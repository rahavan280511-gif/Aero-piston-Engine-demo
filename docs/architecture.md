# Technical Architecture — UAV Aero-Piston Engine Digital Twin

This document provides a comprehensive technical overview of the **UAV Aero-Piston Engine Digital Twin** system architecture, detailing data flows, component specifications, mathematical models, and software interfaces across all system layers.

---

## System Architecture Diagram

```text
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                        LAYER 1 — TELEMETRY SOURCE                         │
 │                                                                           │
 │   EngineSimulator (app/simulator.py)  OR  MissionReplayEngine (app/replay.py) │
 │   [RPM, Throttle, EGT Measured, CHT Measured, Oil Temp Measured]          │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                     LAYER 2 — SYNCHRONIZATION & API                       │
 │                                                                           │
 │   FastAPI Backend Service (app/main.py)                                   │
 │   - Background Asyncio Event Loop (dt = 0.5 s)                            │
 │   - Single-source Mode Controller (Live vs. Replay)                       │
 │   - REST Endpoints (/telemetry, /missions, /replay/start, /replay/stop)   │
 │   - WebSocket Push Stream (/ws/telemetry)                                 │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                      LAYER 3 — DIGITAL TWIN CORE                          │
 │                                                                           │
 │   DigitalTwinCore (app/twin_core.py)                                      │
 │   ├─ EnginePhysicsModel (app/physics_model.py) ──> Expected EGT/CHT/Oil    │
 │   ├─ Residual Engine ──> Raw & EMA-Smoothed Residuals (r = Measured - Exp)│
 │   └─ Health Engine ──> Engine Health Index (EHI ∈ [0, 100])                │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                         LAYER 4 — AI & ANOMALY                            │
 │                                                                           │
 │   Hybrid Anomaly Detection System                                         │
 │   ├─ Rule-Based Detector ──> Sustained Residual Threshold Check           │
 │   ├─ Isolation Forest ML (models/isolation_forest_anomaly.pkl) ──> Score  │
 │   └─ Hybrid Decision ──> Rule Flag OR ML Abnormal                         │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                      LAYER 5 — PROGNOSTICS (RUL)                          │
 │                                                                           │
 │   Degradation & Life Consumption Tracking                                 │
 │   ├─ Degradation Accumulation: d_t = clip(d_{t-1} + Δd · severity, 0, 1)  │
 │   └─ Conceptual RUL Estimate: RUL_hours = 200 · (1 - d_t)                │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                    LAYER 6 — EXPLAINABILITY ENGINE                        │
 │                                                                           │
 │   Lightweight Diagnostic Explainability Layer                             │
 │   ├─ Main Indicator Logic ──> Dominant Channel Isolation                 │
 │   ├─ Health Trend Logic ──> Bounded History Ring Buffer (deque maxlen=10) │
 │   └─ Diagnostic Wording Generator ──> Maintenance Actionable Text         │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                     LAYER 7 — VISUALIZATION & UI                          │
 │                                                                           │
 │   Streamlit Dashboard (dashboard/app.py)                                  │
 │   - Background WebSocket Receiver Thread + Queue                           │
 │   - Real-Time Plotly Time-Series & Gauges                                 │
 │   - Engine Diagnostics Panel & State Table                                │
 └───────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed System Layer Specifications

### Layer 1 — Telemetry Source
- **`app/simulator.py` (`EngineSimulator`)**:
  - Simulates dynamic aero-piston engine speed, manifold dynamics, exhaust gas heat transfer, cylinder head thermal dynamics, and oil temp dissipation.
  - Supports configurable mission profiles (`endurance`, `high_altitude`, `cruise`) with dynamic throttle waveforms.
  - Injects continuous sensor noise ($\sigma_{\text{EGT}} = 5\text{ °C}$, $\sigma_{\text{CHT}} = 3\text{ °C}$, $\sigma_{\text{Oil}} = 2\text{ °C}$).
  - Injects a severe EGT thermal bias fault ($+40\text{ °C}$) for $t > 60\text{ s}$.
- **`app/replay.py` (`MissionReplayEngine`)**:
  - Ingests recorded CSV telemetry files from `data/missions/`.
  - Validates required CSV headers (`timestamp`, `rpm`, `throttle`, `egt`, `cht`, `oil_temp`).
  - Streams frames sequentially through the Digital Twin Core logic.

### Layer 2 — Data Synchronization & API Pipeline
- **`app/main.py` (FastAPI Application)**:
  - Runs a background `asyncio` task stepping simulation or mission replay at real-time rate ($dt = 0.5\text{ s}$).
  - Uses `asyncio.Lock` to guarantee thread-safe state access across concurrent endpoints.
  - Exposes REST endpoints:
    - `GET /telemetry`: Returns latest normalized twin state payload.
    - `GET /missions`: Returns list of available mission CSV recordings.
    - `POST /replay/start?mission={name}`: Switches mode to `replay` and resets twin state.
    - `POST /replay/stop`: Reverts mode to `live` simulation.
    - `POST /reset`: Resets simulator and twin core to initial state.
  - Pushes live JSON snapshots to connected clients via WebSocket (`/ws/telemetry`).

### Layer 3 — Digital Twin Core & Physics Model
- **`app/physics_model.py` (`EnginePhysicsModel`)**:
  - Computes thermodynamic expected healthy states:
    $$\text{EGT}_{\text{expected}} = T_{\text{amb}} + 400 + 0.05 \cdot \text{RPM} + 120 \cdot \text{throttle}$$
    $$\text{CHT}_{\text{expected}} = T_{\text{amb}} + 80 + 0.015 \cdot \text{RPM} + 45 \cdot \text{throttle}$$
    $$\text{Oil}_{\text{expected}} = T_{\text{amb}} + 40 + 0.006 \cdot \text{RPM} + 20 \cdot \text{throttle}$$
- **`app/twin_core.py` (`DigitalTwinCore`)**:
  - Computes raw residuals: $r_i = y_i - \hat{y}_i$.
  - Applies Exponential Moving Average (EMA) smoothing:
    $$\bar{r}_{i, t} = \alpha r_{i, t} + (1 - \alpha) \bar{r}_{i, t-1} \quad (\alpha = 0.2)$$
  - Calculates scalar Engine Health Index (EHI ∈ [0, 100]):
    $$\text{EHI} = \max\left(0, 100 \cdot (1 - \sum w_i \cdot P_i)\right)$$
    where $w_{\text{EGT}} = 0.60, w_{\text{CHT}} = 0.30, w_{\text{Oil}} = 0.10$.

### Layer 4 — AI & Anomaly Detection
- **Rule-Based Detector**: Flags sustained anomalies when $|\bar{r}_{\text{EGT}}| > 15\text{ °C}$, $|\bar{r}_{\text{CHT}}| > 8\text{ °C}$, or $|\bar{r}_{\text{Oil}}| > 5\text{ °C}$.
- **Isolation Forest ML Model (`models/isolation_forest_anomaly.pkl`)**:
  - Trained offline on 7 feature vectors: $[\text{rpm}, \text{throttle}, \text{egt}, \text{cht}, \text{oil\_temp}, \bar{r}_{\text{EGT}}, \bar{r}_{\text{CHT}}]$.
  - Normalizes raw decision function score into a $[0.0, 1.0]$ score.
- **Hybrid Decision**: Flags anomaly if Rule Anomaly == True OR ML Status == `ABNORMAL`.

### Layer 5 — Prognostics & Conceptual RUL
- **Degradation Tracking**:
  - Accumulates degradation when an anomaly is active:
    $$d_t = \text{clip}\left(d_{t-1} + 0.001 \cdot (1 + \text{score}_{\text{ML}}), 0.0, 1.0\right)$$
  - Slow recovery when nominal ($d_t = \max(0, d_{t-1} - 0.0001)$).
- **Conceptual RUL Estimate**:
  $$\text{RUL}_{\text{hours}} = \text{clip}\left(200.0 \cdot (1.0 - d_t), 0.0, 200.0\right)$$

### Layer 6 — Explainability Engine
- **Main Indicator Logic**: Isolates primary contributor (`EGT residual`, `CHT residual`, `EGT and CHT residuals`, `ML anomaly`, `Normal operating behavior`).
- **Health Trend Logic**: Uses a bounded history buffer (`deque(maxlen=10)`) to evaluate whether health score is `stable`, `degrading`, or `improving`.
- **Diagnostic Wording Generator**: Formats human-readable maintenance text with directional residual context (+/- values).

### Layer 7 — Visualization & UI Dashboard
- **`dashboard/app.py` (Streamlit Application)**:
  - Runs a background WebSocket worker thread pushing JSON payloads into a thread-safe Queue.
  - Maintains a bounded session-state buffer (max 200 points).
  - Renders metrics, Plotly time-series charts, health gauges, ML anomaly gauges, **ENGINE DIAGNOSTICS** panel, and telemetry tables.
