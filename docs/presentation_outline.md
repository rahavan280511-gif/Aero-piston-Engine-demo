# Presentation Outline — AI-Enabled Digital Twin for MALE UAV Aero-Piston Engine

---

## SLIDE 1 — PROBLEM & VISION

### Title
**AI-Enabled Digital Twin for MALE UAV Aero-Piston Engine**

### Problem
Medium-Altitude Long-Endurance (MALE) UAVs operate for long durations (up to 24+ hours) in critical operational missions:
- Intelligence, Surveillance, and Reconnaissance (ISR)
- Maritime surveillance and border patrol
- Aerial communication relay
- Strategic environmental and perimeter monitoring

Engine reliability is critical during these missions. An undetected propulsion degradation or thermal anomaly can lead to:
- Incomplete missions and loss of aerial coverage
- Reduced UAV availability and high operational downtime
- Unplanned, reactive maintenance costs
- Risk of forced emergency landings or airframe loss

Traditional engine monitoring relies on simple raw threshold alerts. It observes sensor values in isolation without continuously comparing actual engine thermal/power response against physics-based expected healthy behavior under dynamic flight loads.

### Vision
Create a continuously synchronized virtual representation (Digital Twin) of the UAV engine that combines first-principles physics models with machine learning anomaly detection.

```text
Real/Simulated Engine Data
        ↓
   Digital Twin
        ↓
   Physics + AI
        ↓
 Health Assessment
        ↓
Fault/Anomaly Detection
        ↓
RUL & Maintenance Insight
```

> **Key idea:** *"Don't just monitor the engine — understand how it is behaving."*

---

## SLIDE 2 — ARCHITECTURE OVERVIEW

### Title
**Digital Twin Architecture**

```text
┌──────────────────────────┐
│ Engine / Sensor Data     │
│ RPM                      │
│ Throttle                 │
│ EGT                      │
│ CHT                      │
│ Oil Temperature          │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Data Synchronization     │
│ FastAPI + WebSocket      │
└────────────┬─────────────┘
             ↓
┌─────────────────────────────────────┐
│       DIGITAL TWIN CORE             │
│                                     │
│  Physics Model                      │
│  Residual Calculation               │
│  ML Anomaly Detection               │
│  Health Assessment                  │
│  Degradation Tracking               │
│  RUL Estimation                     │
│  Explainable Diagnostics            │
└────────────┬────────────────────────┘
             ↓
┌──────────────────────────┐
│ Health & Diagnostics     │
│ Health Score             │
│ Anomaly Status           │
│ Fault Suggestion         │
│ RUL                      │
│ Diagnostic Explanation   │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ Streamlit Dashboard      │
│ Real-Time Visualization  │
└──────────────────────────┘
```

### Modes Supported
```text
LIVE SIMULATION  +  MISSION REPLAY
```

### Component Roles
1. **Engine Simulator (`app/simulator.py`)**: Generates real-time sensor streams with mission profile loads and controlled fault injection capability.
2. **Physics Model (`app/physics_model.py`)**: Predicts expected healthy EGT, CHT, and oil temperature from RPM, throttle, and ambient air conditions.
3. **Digital Twin Core (`app/twin_core.py`)**: Computes smoothed residuals, calculates Engine Health Index (EHI), tracks health trends, and generates explainable diagnostics.
4. **ML Anomaly Detector (`models/isolation_forest_anomaly.pkl`)**: Isolation Forest model trained on 7 feature channels to flag multi-dimensional statistical deviations.
5. **Replay Engine (`app/replay.py`)**: Streams recorded CSV flight telemetry through the identical Digital Twin Core logic for mission verification.
6. **FastAPI & WebSocket (`app/main.py`)**: Provides asynchronous state control, REST telemetry endpoints, and high-frequency live push streaming.
7. **Streamlit Dashboard (`dashboard/app.py`)**: Renders real-time Plotly charts, EHI gauges, hybrid decision statuses, and maintenance diagnostic cards.

---

## SLIDE 3 — LIVE DEMO

### Title
**Live Digital Twin Demonstration**

### Dashboard Output Surface

#### Real-Time Engine Parameters
- Engine Speed (RPM)
- Throttle Position (%)
- Exhaust Gas Temp (EGT)
- Cylinder Head Temp (CHT)
- Oil Temperature (°C)

#### Twin Intelligence & Health
- Expected EGT & CHT (Physics Model)
- EGT & CHT Residuals ($\text{Measured} - \text{Expected}$)
- Engine Health Index (EHI 0–100%)
- ML Anomaly Score (0.0–1.0)
- Anomaly Status (Rule / ML / Hybrid)
- Accumulated Degradation (%)
- Estimated Remaining Useful Life (RUL hours)

#### Explainable Diagnostics
```text
Main Indicator:
EGT residual

Health Trend:
Degrading

Diagnostic:
EGT is 38.2°C above expected and CHT is 12.0°C above expected.
Suggests possible overheating.
```

### Demonstration Sequence
```text
 1. Start FastAPI Backend (http://127.0.0.1:8000)
 2. Launch Streamlit Dashboard (http://localhost:8501)
 3. Observe normal engine operating baseline
 4. Observe physics model expected predictions tracking throttle inputs
 5. Observe ML Isolation Forest distribution status (NORMAL)
 6. Introduce / encounter simulated thermal fault (EGT bias)
 7. Observe physical residual divergence (Measured > Expected)
 8. Observe rule-based threshold & ML anomaly detection flags
 9. Observe Engine Health Index (EHI) drop & health trend change to DEGRADING
10. Observe degradation accumulation and conceptual RUL hours decrease
11. Observe engineer-oriented explainable diagnostic message update live
```

> **Complete Intelligence Chain:**
> $\text{Telemetry} \longrightarrow \text{Prediction} \longrightarrow \text{Residual} \longrightarrow \text{Anomaly} \longrightarrow \text{Health} \longrightarrow \text{Degradation} \longrightarrow \text{RUL} \longrightarrow \text{Explanation}$

---

## SLIDE 4 — HOW THIS SCALES

### Title
**From Prototype to Full Engine Digital Twin**

### Current Prototype Scope
Focuses on thermal dynamics and baseline power delivery using 5 core telemetry channels (`rpm`, `throttle`, `egt`, `cht`, `oil_temp`) coupled with an empirical physics model and an Isolation Forest anomaly detector.

### Multi-Subsystem Scaling Architecture
```text
                    ENGINE DIGITAL TWIN
                           │
        ┌──────────────────┼──────────────────┐
        ↓                  ↓                  ↓
   Propulsion         Thermal System     Lubrication
        │                  │                  │
   RPM/Power          EGT/CHT            Oil Pressure
   Torque             Cylinder Temp      Oil Temp
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ↓
                  Twin Synchronization
                           ↓
                  AI + Physics Engine
                           ↓
             Health / Fault / RUL System
```

### Planned Extensions
- **FADEC / ECU & CAN Bus Integration**: Ingest real engine control unit data streams.
- **Subsystem Physics Models**:
  - Lubrication Subsystem (oil pressure vs. oil temperature vs. pump speed)
  - Fuel & Mixture Subsystem (fuel flow rate, air-fuel ratio, injector dynamics)
  - Ignition Subsystem (spark timing, cylinder pressure traces)
  - Cooling Subsystem (ambient airspeed, radiator inlet pressure, coolant flow)
  - Exhaust & Induction Subsystem (manifold absolute pressure, boost pressure)
- **Advanced AI / Prognostics**: Supervised fault classifiers, physics-informed neural networks (PINNs), and probabilistic RUL distributions.

---

## SLIDE 5 — TEAM PLAN & ROLES

### Title
**Team Structure & Responsibilities**

```text
┌─────────────────────────┐     ┌─────────────────────────┐
│ Physics / Engine Model  │     │       AI / ML           │
│ - Thermodynamic equations│     │ - Anomaly models        │
│ - Subsystem maps        │     │ - Fault classification  │
└────────────┬────────────┘     └────────────┬────────────┘
             │                               │
             └──────────────┬────────────────┘
                            ↓
             ┌──────────────────────────────┐
             │ Integration & Architecture   │
             │ - Digital Twin Core          │
             │ - Real-time synchronization  │
             └──────────────┬───────────────┘
                            │
             ┌──────────────┴────────────────┐
             ↓                               ↓
┌─────────────────────────┐     ┌─────────────────────────┐
│ Backend & Data Pipeline │     │ Dashboard & UX          │
│ - FastAPI / WebSockets  │     │ - Streamlit UI          │
│ - Sensor & CAN interfaces│    │ - Diagnostic displays   │
└─────────────────────────┘     └─────────────────────────┘
```

### Technical Layer Owners
1. **Physics / Engine Modeling Lead**: Develops expected baseline models, thermodynamic maps, and subsystem physics.
2. **AI / ML Specialist**: Trains anomaly detection algorithms, fault classifiers, degradation metrics, and RUL models.
3. **Backend & Digital Twin Engineer**: Manages state estimation, FastAPI middleware, WebSocket synchronization, and data pipelines.
4. **Dashboard & Visualization Engineer**: Designs intuitive Streamlit operator panels, Plotly charts, and diagnostic cards.
5. **Hardware & Systems Integration Engineer**: Manages ECU/FADEC CAN interfaces, hardware-in-the-loop (HIL) testing, and sensor validation.

> **Team principle:** *"Each member owns a technical layer, while integration connects the complete Digital Twin."*

---

## SLIDE 6 — RISKS & MITIGATION

### Title
**Technical Risks & Mitigation**

| Technical Risk | Mitigation Strategy |
| :--- | :--- |
| **Limited real engine dataset** | High-fidelity synthetic simulator + controlled physical fault injection framework. |
| **Rare fault occurrence in flight** | Automated scenario generation for rare faults (overheating, mixture lean-out, sensor drift). |
| **Lack of trust in pure black-box AI** | Hybrid architecture pairing deterministic physics residuals with ML anomaly detection. |
| **False positive anomaly alarms** | Exponential moving average (EMA) noise damping + sustained threshold verification. |
| **RUL estimation uncertainty** | Frame current RUL as a conceptual prototype metric and validate against benchmark degradation datasets. |
| **Sensor noise and transients** | Filtering pipelines and robust feature normalization. |
| **Model generalization across flight profiles** | Evaluation and tuning across diverse mission profiles (`endurance`, `high_altitude`, `cruise`). |
| **Hardware integration complexity** | Standardized FastAPI/REST/WebSocket contracts for staged ECU/CAN integration. |
| **Real-time processing latency** | Lightweight, asynchronous single-pass twin updates ($dt = 0.5\text{ s}$). |

---

## SLIDE 7 — ASK / NEXT STEPS

### Title
**Next Steps & What We Need**

### Immediate Technical Goals
- Validate physics model curves against physical aero-piston test-bench data.
- Expand fault injection scenarios (oil pressure drop, spark degradation, fuel restriction).
- Train multi-class fault classifiers to complement the Isolation Forest anomaly detector.
- Develop subsystem-level physics models (lubrication and fuel systems).
- Test backend performance under multi-client WebSocket streaming.

### Hardware & Lab Requirements
- Access to aero-piston engine test-cell telemetry logs.
- FADEC / ECU CAN bus protocol documentation and sample capture files.
- Sensor hardware specs (thermocouples, pressure transducers, hall-effect RPM sensors).
- Domain expertise for model validation.

### Team / Mentor Support Requested
- Guidance from propulsion and thermal management faculty/mentors.
- Review of physics model assumption parameters.
- Access to benchmark engine degradation datasets.

> **Goal:** *"Move from a simulation-driven prototype to a validated, multi-subsystem engine Digital Twin."*
