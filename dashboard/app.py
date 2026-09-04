"""
Streamlit Live Monitoring Dashboard — UAV Aero-Piston Engine Digital Twin.

Unified & Synchronized UI Architecture:
--------------------------------------
1. 📊 Engine Telemetry & Parameters (Organized Engine Metrics Grid & Live Charts)
2. 🚨 Anomaly Detection & AI Diagnostics (Dedicated Separated Panel for Anomaly Detection & AI Classifier)
3. 🔧 3D Engine Model (Interactive Three.js 3D Aero-Engine Model with Dynamic Color Sync)
4. ❓ Parameter Guide & Glossary (Complete Reference Table & Normal Ranges)
"""

from pathlib import Path
import json
import queue
import threading
import time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import streamlit as st
import websocket

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="UAV Engine Digital Twin",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

WS_URL = "ws://127.0.0.1:8000/ws/telemetry"
REST_URL = "http://127.0.0.1:8000/telemetry"
HISTORY_URL = "http://127.0.0.1:8000/history?n=200"
MAX_POINTS = 200


# ---------------------------------------------------------------------------
# Session State Initialization & Background WebSocket Worker
# ---------------------------------------------------------------------------

if "data_buffer" not in st.session_state:
    st.session_state.data_buffer = []

if "latest_data" not in st.session_state:
    st.session_state.latest_data = None

if "connection_status" not in st.session_state:
    st.session_state.connection_status = "DISCONNECTED"

if "msg_queue" not in st.session_state:
    st.session_state.msg_queue = queue.Queue()

if "ws_thread_started" not in st.session_state:
    st.session_state.ws_thread_started = False


def websocket_listener_worker(msg_queue: queue.Queue):
    """Background worker thread listening to FastAPI WebSocket."""
    def on_message(ws, message):
        try:
            data = json.loads(message)
            if "pong" not in data:
                msg_queue.put(("DATA", data))
        except Exception:
            pass

    def on_error(ws, error):
        msg_queue.put(("STATUS", "ERROR"))

    def on_close(ws, close_status_code, close_msg):
        msg_queue.put(("STATUS", "DISCONNECTED"))

    def on_open(ws):
        msg_queue.put(("STATUS", "CONNECTED"))

    while True:
        try:
            msg_queue.put(("STATUS", "CONNECTING"))
            ws_app = websocket.WebSocketApp(
                WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            ws_app.run_forever(ping_interval=10, ping_timeout=5)
        except Exception:
            msg_queue.put(("STATUS", "DISCONNECTED"))
        
        time.sleep(2.0)


# Start background thread ONCE per session
if not st.session_state.ws_thread_started:
    st.session_state.ws_thread_started = True
    t = threading.Thread(
        target=websocket_listener_worker,
        args=(st.session_state.msg_queue,),
        daemon=True,
    )
    t.start()


# Drain queue messages into session_state
while not st.session_state.msg_queue.empty():
    try:
        msg_type, payload = st.session_state.msg_queue.get_nowait()
        if msg_type == "STATUS":
            st.session_state.connection_status = payload
        elif msg_type == "DATA":
            st.session_state.connection_status = "CONNECTED"
            st.session_state.latest_data = payload
            st.session_state.data_buffer.append(payload)
            if len(st.session_state.data_buffer) > MAX_POINTS:
                st.session_state.data_buffer.pop(0)
    except queue.Empty:
        break


# Extract latest telemetry packet
latest = st.session_state.latest_data

# ---------------------------------------------------------------------------
# UI Header & Connection Status
# ---------------------------------------------------------------------------

st.title("✈️ UAV Engine Digital Twin Dashboard")
st.caption("Real-Time Telemetry, Physics Digital Twin Health & Synchronized AI Diagnostics")

# Status Banner
status = st.session_state.connection_status

if status == "CONNECTED":
    st.success("🟢 Backend Connected: ws://127.0.0.1:8000/ws/telemetry", icon="✅")
elif status == "CONNECTING":
    st.warning("🟡 Connecting to backend server...", icon="⏳")
elif status == "DISCONNECTED":
    st.error("🔴 Disconnected from backend server — auto-reconnecting...", icon="⚠️")
else:
    st.error(f"🔴 Connection Error ({status})", icon="🚨")


# Sidebar Controls
st.sidebar.header("⚙️ Controls & Options")
auto_refresh = st.sidebar.checkbox("Auto Refresh (1s)", value=True, help="Auto-update dashboard every 1 second.")

if st.sidebar.button("🔄 Clear History Buffer"):
    st.session_state.data_buffer = []
    st.session_state.latest_data = None
    try:
        requests.post("http://127.0.0.1:8000/reset", timeout=2)
    except Exception:
        pass
    st.rerun()

# Interactive Manual Simulator Control & Live Fault Injector Panel
st.sidebar.markdown("---")
st.sidebar.subheader("🎮 Live Manual Control & Fault Injector")

manual_mode = st.sidebar.checkbox(
    "Enable Manual Control",
    value=False,
    help="Override automatic flight profile and manually control throttle & live fault injection."
)

if manual_mode:
    man_throttle = st.sidebar.slider(
        "Manual Throttle Position",
        min_value=0.20,
        max_value=0.95,
        value=0.65,
        step=0.05,
        help="Adjust crankshaft speed & engine power output live."
    )

    man_fault = st.sidebar.selectbox(
        "Inject Live Fault Scenario:",
        [
            "NONE",
            "OVERHEATING",
            "LUBRICATION_ISSUE",
            "EXHAUST_LEAK",
        ],
        format_func=lambda x: {
            "NONE": "🟢 NONE (Healthy Engine)",
            "OVERHEATING": "🔴 OVERHEATING (Thermal Overload)",
            "LUBRICATION_ISSUE": "🟡 LUBRICATION_ISSUE (Oil Breakdown)",
            "EXHAUST_LEAK": "💨 EXHAUST_LEAK (Exhaust Manifold Leak)",
        }.get(x, x),
        help="Inject real-time fault symptoms directly into the running engine simulator."
    )

    curr_ctrl_state = (True, float(man_throttle), str(man_fault))
    if st.session_state.get("prev_ctrl_state") != curr_ctrl_state:
        try:
            requests.post(
                f"http://127.0.0.1:8000/simulator/control?manual_override=true&throttle={man_throttle}&injected_fault={man_fault}",
                timeout=2,
            )
            st.session_state.prev_ctrl_state = curr_ctrl_state
        except Exception:
            pass
else:
    if st.session_state.get("prev_manual_mode", False):
        try:
            requests.post("http://127.0.0.1:8000/simulator/reset_control", timeout=2)
            st.session_state.prev_ctrl_state = (False, 0.6, "NONE")
        except Exception:
            pass
st.session_state.prev_manual_mode = manual_mode


# Mission Control & Replay Panel
st.sidebar.markdown("---")
st.sidebar.subheader("🎬 Mission Profile Replay")

try:
    resp = requests.get("http://127.0.0.1:8000/missions", timeout=2)
    avail_missions = resp.json().get("missions", [])
except Exception:
    avail_missions = []

# Standard fault missions mapping
mission_label_map = {
    "mission_001_nominal_cruise": "🟢 Mission 1: Nominal Cruise Flight",
    "mission_002_thermal_overload": "🔴 Mission 2: Thermal Overload (Overheating)",
    "mission_003_lubrication_issue": "🟡 Mission 3: Oil Lubrication Failure",
    "mission_004_exhaust_leak": "💨 Mission 4: Exhaust Manifold Leak",
}

if not avail_missions:
    avail_missions = list(mission_label_map.keys())

selected_mission = st.sidebar.selectbox(
    "Select Pre-Recorded Mission:",
    avail_missions,
    format_func=lambda m: mission_label_map.get(m, m),
    help="Select a fault-specific flight recording to replay through the Digital Twin."
)

r_col1, r_col2 = st.sidebar.columns(2)
with r_col1:
    if st.sidebar.button("▶️ Start Replay"):
        try:
            requests.post(f"http://127.0.0.1:8000/replay/start?mission={selected_mission}", timeout=3)
            st.session_state.data_buffer = []
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

with r_col2:
    if st.sidebar.button("⏹️ Stop Replay"):
        try:
            requests.post("http://127.0.0.1:8000/replay/stop", timeout=3)
            st.session_state.data_buffer = []
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

if latest is None:
    st.info("Awaiting telemetry stream from Digital Twin backend...")
    if auto_refresh:
        time.sleep(1.0)
        st.rerun()
    st.stop()

# Mode Banner
curr_mode = latest.get("mode", "live")
curr_mission = latest.get("mission", None)

if curr_mode == "replay":
    st.info(f"🎬 **REPLAY MODE ACTIVE** — Replaying mission recording **'{mission_label_map.get(curr_mission, curr_mission)}'**.")


# ---------------------------------------------------------------------------
# Synchronized Common Telemetry State Extraction
# ---------------------------------------------------------------------------
is_anomaly = latest.get("anomaly", False)
health_val = latest.get("health", 100.0)
health_status = latest.get("health_status", "NOMINAL")
fault_class = latest.get("fault_class", "NORMAL")
fault_confidence = latest.get("fault_confidence", 0.0) * 100.0
diag_msg = latest.get("diagnostic", "Engine behavior is within expected operating range.")
exp = latest.get("explanation", {})


# ---------------------------------------------------------------------------
# MAIN TAB NAVIGATION: Organized & Synchronized Layout
# ---------------------------------------------------------------------------

tab_telemetry, tab_anomaly, tab_3d, tab_guide = st.tabs([
    "📊 Engine Telemetry & Parameters",
    "🚨 Anomaly Detection & AI Diagnostics",
    "🔧 3D Engine Model",
    "❓ Parameter Guide & Glossary"
])


# ===========================================================================
# TAB 1: ENGINE TELEMETRY & PARAMETERS
# ===========================================================================
with tab_telemetry:
    st.subheader("⚙️ Real-Time Engine Telemetry Parameters")
    st.caption("All primary physical sensors and thermodynamic digital twin parameters organized in one structured view.")

    # Grid Row 1: Operating Parameters
    st.markdown("##### 1️⃣ Engine Operating & Thermal Parameters")
    p1, p2, p3, p4 = st.columns(4)

    with p1:
        st.metric(
            label="Engine Speed (RPM)",
            value=f"{latest.get('rpm', 0):.0f} RPM",
            help="Crankshaft speed. Normal operating range: 2000 – 4500 RPM."
        )

    with p2:
        st.metric(
            label="Throttle Position (%)",
            value=f"{latest.get('throttle', 0)*100:.1f} %",
            help="Throttle command input. Range: 0% – 100%."
        )

    with p3:
        st.metric(
            label="Exhaust Gas Temp (EGT)",
            value=f"{latest.get('egt', 0):.1f} °C",
            delta=f"Physics Target: {latest.get('egt_expected', 0):.1f} °C",
            delta_color="off",
            help="Measured Exhaust Gas Temp vs Thermodynamic Expected Target."
        )

    with p4:
        st.metric(
            label="Cylinder Head Temp (CHT)",
            value=f"{latest.get('cht', 0):.1f} °C",
            delta=f"Physics Target: {latest.get('cht_expected', 0):.1f} °C",
            delta_color="off",
            help="Measured Cylinder Head Temp vs Thermodynamic Expected Target."
        )

    # Grid Row 2: Health, Wear & Life Parameters
    st.markdown("##### 2️⃣ Engine Health, Wear & Life Parameters")
    h1, h2, h3, h4 = st.columns(4)

    with h1:
        ehi_status_color = "normal" if health_val >= 80 else ("off" if health_val >= 60 else "inverse")
        ehi_label = health_status  # NOMINAL / CAUTION / WARNING / CRITICAL
        st.metric(
            label="Engine Health Index (EHI)",
            value=f"{health_val:.1f}%",
            delta=ehi_label,
            delta_color=ehi_status_color,
            help="Overall health score (100% = Nominal, <60% = Critical)."
        )

    with h2:
        st.metric(
            label="Oil Lubrication Temp",
            value=f"{latest.get('oil_temp', 0):.1f} °C",
            help="Crankcase lubricating oil temperature. Normal range: 70°C – 95°C."
        )

    with h3:
        deg_val = latest.get("degradation", 0.0) * 100.0
        deg_label = "Nominal" if deg_val < 1.0 else f"Accumulating ({deg_val:.1f}%)"
        deg_color = "normal" if deg_val < 1.0 else ("off" if deg_val < 10.0 else "inverse")
        st.metric(
            label="Accumulated Wear & Degradation",
            value=f"{deg_val:.2f}%",
            delta=deg_label,
            delta_color=deg_color,
            help="Physical component wear accumulated over operating hours. Resets to 0% on engine reset."
        )

    with h4:
        rul_val = latest.get("rul_hours", 200.0)
        st.metric(
            label="Remaining Useful Life (RUL)",
            value=f"{rul_val:.1f} Hours",
            help="Estimated flight hours remaining before mandatory overhaul."
        )

    st.markdown("---")

    # Telemetry Visual Gauges & Historical Charts
    st.subheader("📈 Live Telemetry Charts")
    df_buf = pd.DataFrame(st.session_state.data_buffer)

    if not df_buf.empty and "timestamp" in df_buf.columns:
        c1, c2 = st.columns(2)

        with c1:
            fig_rpm = px.line(df_buf, x="timestamp", y="rpm", title="Engine Speed (RPM)", labels={"timestamp": "Time (s)", "rpm": "RPM"})
            fig_rpm.update_traces(line_color="#1f77b4", line_width=2)
            fig_rpm.update_layout(height=260, margin=dict(l=20, r=20, t=35, b=20))
            st.plotly_chart(fig_rpm, use_container_width=True)

            fig_cht = go.Figure()
            fig_cht.add_trace(go.Scatter(x=df_buf["timestamp"], y=df_buf["cht"], mode="lines", name="CHT Measured", line=dict(color="#ff7f0e", width=2)))
            if "cht_expected" in df_buf.columns:
                fig_cht.add_trace(go.Scatter(x=df_buf["timestamp"], y=df_buf["cht_expected"], mode="lines", name="CHT Physics Target", line=dict(color="#2ca02c", dash="dash", width=2)))
            fig_cht.update_layout(title="Cylinder Head Temp (°C)", xaxis_title="Time (s)", yaxis_title="°C", height=260, margin=dict(l=20, r=20, t=35, b=20))
            st.plotly_chart(fig_cht, use_container_width=True)

        with c2:
            fig_egt = go.Figure()
            fig_egt.add_trace(go.Scatter(x=df_buf["timestamp"], y=df_buf["egt"], mode="lines", name="EGT Measured", line=dict(color="#d62728", width=2)))
            if "egt_expected" in df_buf.columns:
                fig_egt.add_trace(go.Scatter(x=df_buf["timestamp"], y=df_buf["egt_expected"], mode="lines", name="EGT Physics Target", line=dict(color="#2ca02c", dash="dash", width=2)))
            fig_egt.update_layout(title="Exhaust Gas Temp (°C)", xaxis_title="Time (s)", yaxis_title="°C", height=260, margin=dict(l=20, r=20, t=35, b=20))
            st.plotly_chart(fig_egt, use_container_width=True)

            if "health" in df_buf.columns:
                fig_health = px.line(df_buf, x="timestamp", y="health", title="Engine Health Index (EHI %)", labels={"timestamp": "Time (s)", "health": "EHI (%)"})
                fig_health.update_traces(line_color="#2ca02c", line_width=2)
                fig_health.update_layout(height=260, margin=dict(l=20, r=20, t=35, b=20), yaxis_range=[0, 105])
                st.plotly_chart(fig_health, use_container_width=True)


# ===========================================================================
# TAB 2: ANOMALY DETECTION & AI DIAGNOSTICS (SEPARATE DEDICATED VIEW)
# ===========================================================================
with tab_anomaly:
    st.subheader("🚨 Anomaly Detection & AI Diagnostics Center")
    st.caption("Dedicated anomaly monitoring panel separating rule-based safety thresholds, unsupervised AI anomaly detection, and supervised fault classification.")

    # Top Anomaly Alert Banner (Synchronized with Tab 1 & Tab 3)
    if is_anomaly:
        st.error(f"🚨 **ANOMALY DETECTED:** {diag_msg}", icon="🔥")
    else:
        st.success(f"🟢 **SYSTEM NOMINAL:** {diag_msg}", icon="✅")

    st.markdown("---")

    # 4 Key AI & Anomaly Cards
    a1, a2, a3, a4 = st.columns(4)

    with a1:
        rule_anom = latest.get("anomaly_rule", False)
        st.markdown("##### 1. Rule Limit Check")
        if rule_anom:
            st.error("🚨 THRESHOLD BREACH")
        else:
            st.success("✅ WITHIN LIMITS")
        st.caption("Checks hard safety limits (e.g. EGT > 850°C).")

    with a2:
        ml_flag = latest.get("anomaly_flag_ml", "NORMAL")
        st.markdown("##### 2. AI Anomaly Detector")
        if ml_flag == "ABNORMAL":
            st.error("🚨 ABNORMAL PATTERN")
        elif ml_flag == "NORMAL":
            st.success("✅ NORMAL PATTERN")
        else:
            st.warning("⚠️ UNAVAILABLE")
        st.caption("Unsupervised Isolation Forest model.")

    with a3:
        ml_score = latest.get("anomaly_score_ml", 0.0)
        st.markdown("##### 3. AI Risk Score")
        st.metric(
            label="Risk Score (0.0 - 1.0)",
            value=f"{ml_score:.4f}",
            help="Values > 0.5 indicate anomalous sensor behavior."
        )
        st.caption("Normalized score from Isolation Forest.")

    with a4:
        st.markdown("##### 4. AI Fault Classifier")
        if fault_class == "OVERHEATING":
            st.error(f"🚨 {fault_class}")
        elif fault_class == "LUBRICATION_ISSUE":
            st.warning(f"⚠️ {fault_class}")
        else:
            st.success(f"✅ {fault_class}")
        st.caption(f"Random Forest confidence: {fault_confidence:.1f}%")

    st.markdown("---")

    # Detailed Explainability Section
    st.subheader("🔍 Physics Deviation & Root Cause Breakdown")

    e1, e2, e3 = st.columns(3)

    with e1:
        st.metric(
            label="Primary Indicator Channel",
            value=exp.get("main_indicator", "Normal behavior"),
            help="Sensor channel contributing most heavily to current anomaly."
        )

    with e2:
        res_egt_val = exp.get("res_egt", latest.get("res_egt", 0.0))
        st.metric(
            label="Exhaust Temp Drift (EGT Residual)",
            value=f"{res_egt_val:+.1f} °C",
            help="Positive value = running hotter than physics target."
        )

    with e3:
        res_cht_val = exp.get("res_cht", latest.get("res_cht", 0.0))
        st.metric(
            label="Cylinder Temp Drift (CHT Residual)",
            value=f"{res_cht_val:+.1f} °C",
            help="Positive value = cylinder head running hotter than physics target."
        )

    # Anomaly Score History Chart
    if not df_buf.empty and "anomaly_score_ml" in df_buf.columns:
        st.markdown("---")
        fig_ai_risk = px.line(
            df_buf, x="timestamp", y="anomaly_score_ml",
            title="AI Anomaly Risk Score History",
            labels={"timestamp": "Time (s)", "anomaly_score_ml": "Risk Score"}
        )
        fig_ai_risk.update_traces(line_color="#d62728" if is_anomaly else "#9467bd", line_width=2)
        fig_ai_risk.update_layout(height=280, margin=dict(l=20, r=20, t=35, b=20), yaxis_range=[0.0, 1.0])
        st.plotly_chart(fig_ai_risk, use_container_width=True)


# ===========================================================================
# TAB 3: 3D ENGINE MODEL (Interactive Model View)
# ===========================================================================
with tab_3d:
    st.subheader("🔧 3D Aero-Piston Engine Model — Telemetry Driven")
    st.caption("Interactive Three.js 3D engine model. Propeller speed, piston stroke, and thermal colors update live from Digital Twin telemetry.")

    _iframe_html = """
    <div style="position:relative; width:100%; height:600px; border-radius:8px; overflow:hidden; border:1px solid #333;">
        <iframe id="engine3d" src="http://127.0.0.1:8000/3d-viewer"
                style="width:100%; height:100%; border:none;"
                allow="autoplay">
        </iframe>
    </div>
    """
    import streamlit.components.v1 as components
    components.html(_iframe_html, height=640)

    # Quick metric bar alongside 3D model (Synchronized with Tab 1 & Tab 2)
    v1, v2, v3, v4, v5 = st.columns(5)
    with v1:
        st.metric("Engine Speed", f"{latest.get('rpm', 0):.0f} RPM")
    with v2:
        st.metric("Exhaust Temp", f"{latest.get('egt', 0):.1f} °C")
    with v3:
        st.metric("Cylinder Temp", f"{latest.get('cht', 0):.1f} °C")
    with v4:
        st.metric("Engine Health", f"{health_val:.1f}%", delta=health_status, delta_color="normal" if health_val > 80 else "inverse")
    with v5:
        st.metric("AI Fault Class", fault_class, delta="ANOMALY" if is_anomaly else "NORMAL", delta_color="inverse" if is_anomaly else "normal")


# ===========================================================================
# TAB 4: PARAMETER GUIDE & GLOSSARY
# ===========================================================================
with tab_guide:
    st.subheader("❓ Parameter Reference Guide & Glossary")
    st.caption("Complete reference explaining all engine telemetry parameters, units, normal ranges, and AI metrics.")

    st.markdown(
        """
        | Parameter / Acronym | Full Name | Normal Range | Plain English Description |
        | :--- | :--- | :--- | :--- |
        | **RPM** | **Engine Speed** | `2000 – 4500 RPM` | Crankshaft rotational speed in revolutions per minute. |
        | **Throttle** | **Throttle Position** | `0% – 100%` | Pilot/autopilot throttle command input percentage. |
        | **EGT** | **Exhaust Gas Temp** | `550°C – 750°C` | Temperature of exhaust gases leaving cylinder. High EGT indicates lean fuel or overload. |
        | **CHT** | **Cylinder Head Temp** | `140°C – 200°C` | Temperature of cylinder head wall. High CHT indicates cooling airflow loss. |
        | **Oil Temp** | **Oil Lubrication Temp** | `70°C – 95°C` | Lubricating oil temperature in crankcase sump. |
        | **EHI** | **Engine Health Index** | `80% – 100%` | Overall health score from 0% (Critical Failure) to 100% (Nominal). |
        | **Residual (Drift)** | **Physics Deviation** | `0 ± 5°C` | **Difference between actual measured sensor value and what physics model expected.** Positive (+15°C) = running hotter than physically normal. |
        | **Degradation** | **Accumulated Wear** | `0% – 100%` | Physical component wear accumulated over operating hours. |
        | **RUL** | **Remaining Useful Life** | `150 – 200+ Hours` | Estimated remaining flight hours before required servicing/overhaul. |
        | **Isolation Forest** | **Unsupervised AI Anomaly Detector** | `Score < 0.3` | Machine learning model evaluating 7 sensor channels to spot unusual behavior combinations. |
        | **Random Forest** | **Supervised AI Fault Classifier** | `NORMAL` | Machine learning model predicting specific root cause (`NORMAL`, `OVERHEATING`, `LUBRICATION_ISSUE`). |
        """
    )

    st.markdown("---")
    st.subheader("📋 Comprehensive Telemetry Parameter Table")

    table_data = [
        {"Parameter Name": "Operating Mode", "Current Value": str(latest.get('mode', 'live')).upper(), "Unit": "mode", "Target / Normal Range": "LIVE / REPLAY", "Description": "System operational mode."},
        {"Parameter Name": "Active Mission", "Current Value": str(latest.get('mission', 'N/A')), "Unit": "profile", "Target / Normal Range": "mission_001", "Description": "Pre-recorded flight profile replayed."},
        {"Parameter Name": "Simulation Time", "Current Value": f"{latest.get('timestamp', 0):.1f}", "Unit": "seconds", "Target / Normal Range": "> 0.0 s", "Description": "Total simulation run time."},
        {"Parameter Name": "Engine Speed (RPM)", "Current Value": f"{latest.get('rpm', 0):.0f}", "Unit": "RPM", "Target / Normal Range": "2000 – 4500 RPM", "Description": "Crankshaft rotational speed."},
        {"Parameter Name": "Throttle Position", "Current Value": f"{latest.get('throttle', 0)*100:.1f}", "Unit": "%", "Target / Normal Range": "20% – 100%", "Description": "Throttle command input percentage."},
        {"Parameter Name": "EGT Measured", "Current Value": f"{latest.get('egt', 0):.1f}", "Unit": "°C", "Target / Normal Range": "550°C – 750°C", "Description": "Measured Exhaust Gas Temperature."},
        {"Parameter Name": "EGT Physics Target", "Current Value": f"{latest.get('egt_expected', 0):.1f}", "Unit": "°C", "Target / Normal Range": "550°C – 750°C", "Description": "Thermodynamic expected EGT."},
        {"Parameter Name": "EGT Temp Drift (Residual)", "Current Value": f"{latest.get('res_egt', 0):+.1f}", "Unit": "°C", "Target / Normal Range": "0.0 ± 5.0 °C", "Description": "Difference (Measured − Expected EGT)."},
        {"Parameter Name": "CHT Measured", "Current Value": f"{latest.get('cht', 0):.1f}", "Unit": "°C", "Target / Normal Range": "140°C – 200°C", "Description": "Measured Cylinder Head Temperature."},
        {"Parameter Name": "CHT Physics Target", "Current Value": f"{latest.get('cht_expected', 0):.1f}", "Unit": "°C", "Target / Normal Range": "140°C – 200°C", "Description": "Thermodynamic expected CHT."},
        {"Parameter Name": "CHT Temp Drift (Residual)", "Current Value": f"{latest.get('res_cht', 0):+.1f}", "Unit": "°C", "Target / Normal Range": "0.0 ± 5.0 °C", "Description": "Difference (Measured − Expected CHT)."},
        {"Parameter Name": "Oil Lubrication Temp", "Current Value": f"{latest.get('oil_temp', 0):.1f}", "Unit": "°C", "Target / Normal Range": "70°C – 95°C", "Description": "Crankcase oil temperature."},
        {"Parameter Name": "Engine Health Index (EHI)", "Current Value": f"{health_val:.1f}", "Unit": "%", "Target / Normal Range": "80% – 100%", "Description": "Overall health score derived from physics residuals."},
        {"Parameter Name": "Accumulated Wear & Degradation", "Current Value": f"{latest.get('degradation', 0)*100:.2f}", "Unit": "%", "Target / Normal Range": "< 5.0 %", "Description": "Accumulated component wear."},
        {"Parameter Name": "Remaining Useful Life (RUL)", "Current Value": f"{latest.get('rul_hours', 200):.1f}", "Unit": "hours", "Target / Normal Range": "150 – 200+ hours", "Description": "Estimated remaining flight hours."},
        {"Parameter Name": "AI Anomaly Risk Score", "Current Value": f"{latest.get('anomaly_score_ml', 0):.4f}", "Unit": "0.0 – 1.0", "Target / Normal Range": "< 0.3000", "Description": "Normalized risk score from Isolation Forest."},
        {"Parameter Name": "Predicted Fault Profile", "Current Value": fault_class, "Unit": "class", "Target / Normal Range": "NORMAL", "Description": "Predicted fault profile from Random Forest."},
        {"Parameter Name": "Fault Model Confidence", "Current Value": f"{fault_confidence:.1f}%", "Unit": "%", "Target / Normal Range": "> 85.0 %", "Description": "Classifier confidence probability."},
        {"Parameter Name": "Automated Diagnostic Message", "Current Value": diag_msg, "Unit": "text", "Target / Normal Range": "Engine behavior is within expected operating range.", "Description": "Diagnostic summary generated by Digital Twin Core."}
    ]

    df_table = pd.DataFrame(table_data)
    st.dataframe(df_table, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Auto Refresh cadence
# ---------------------------------------------------------------------------
if auto_refresh:
    time.sleep(1.0)
    st.rerun()
