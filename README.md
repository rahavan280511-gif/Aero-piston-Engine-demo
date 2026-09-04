# AI-Enabled Digital Twin for MALE UAV Aero-Piston Engine

A real-time **AI-Enabled Digital Twin demonstration package** for a Medium-Altitude Long-Endurance (MALE) UAV aero-piston engine. The system combines first-principles thermodynamic physics models, real-time telemetry simulation, residual analysis, hybrid rule + ML anomaly detection (Isolation Forest), health degradation tracking, conceptual Remaining Useful Life (RUL) estimation, mission recording & replay, and engineer-friendly explainable diagnostics.

---

## 1. Overview

Medium-Altitude Long-Endurance (MALE) UAVs perform long-duration missions such as Intelligence, Surveillance, and Reconnaissance (ISR), maritime patrol, and communication relay. Propulsion reliability is mission-critical. Traditional monitoring observes raw sensor values against static thresholds without understanding whether the engine is behaving as expected under dynamic flight loads.

This project delivers a continuously synchronized Digital Twin core that pairs live telemetry with expected physical behavior, detecting subtle thermal and power anomalies early before catastrophic engine failure occurs.

---

## 2. Project Objective

- **Continuous Synchronization**: Pair raw engine telemetry streams with a thermodynamic physics model in real-time ($dt = 0.5\text{ s}$).
- **Hybrid Intelligence**: Combine deterministic physical residual thresholding with an offline-trained Isolation Forest machine learning model.
- **Prognostics & Health**: Quantify engine degradation accumulation ($d \in [0, 1]$) and map life consumption to conceptual Remaining Useful Life ($\text{RUL} = 200 \times (1 - d)\text{ hours}$).
- **Explainable Diagnostics**: Translate physical residual deviations and ML flags into engineer-oriented actionable maintenance messages.
- **Mission Intelligence**: Replay recorded CSV mission logs through the identical Digital Twin core for post-flight safety audits.

---

## 3. What This Demo Shows

- **Real-Time Telemetry Simulation**: Simulates dynamic UAV aero-piston engine speed, throttle dynamics, EGT, CHT, and oil temperature under realistic sensor noise and load profiles.
- **Physics Expected Behavior Model**: Computes first-principles expected EGT, CHT, and oil temperatures based on engine RPM, throttle setting, and ambient conditions.
- **Hybrid Anomaly Detection**: Integrates rule-based residual thresholds with an `IsolationForest` ML model trained on 7 feature channels (`rpm`, `throttle`, `egt`, `cht`, `oil_temp`, `res_egt`, `res_cht`).
- **Engine Health Index (EHI) & Prognostics**: Calculates scalar health index ($0\text{--}100\%$), tracks cumulative degradation, and estimates conceptual RUL hours.
- **Explainable Diagnostics & Mission Replay**: Explains *why* an anomaly was flagged and allows replaying flight CSV logs row-by-row through the twin backend.

> **Note**: This system is a **demonstrative research prototype**, not a certified aviation maintenance system.

---

## 4. System Architecture

```text
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                        LAYER 1 — TELEMETRY SOURCE                         │
 │   EngineSimulator (app/simulator.py)  OR  MissionReplayEngine (app/replay.py) │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                     LAYER 2 — SYNCHRONIZATION & API                       │
 │   FastAPI Backend Service (app/main.py) — REST & WebSocket (/ws/telemetry)│
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                      LAYER 3 — DIGITAL TWIN CORE                          │
 │   EnginePhysicsModel (app/physics_model.py) ──> Residuals & EHI Calculation  │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                         LAYER 4 — AI & ANOMALY                            │
 │   Rule-Based Thresholds  +  Isolation Forest ML Model (7 Feature Channels)│
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                      LAYER 5 — PROGNOSTICS (RUL)                          │
 │   Degradation Accumulation (d ∈ [0, 1]) ──> Conceptual RUL Estimation (hours)│
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                    LAYER 6 — EXPLAINABILITY ENGINE                        │
 │   Main Indicator Isolation + Trend Buffer + Human-Readable Diagnostic Text│
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                     LAYER 7 — VISUALIZATION & UI                          │
 │   Streamlit Interactive Live Monitoring Dashboard (dashboard/app.py)     │
 └───────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Key Features

- **Dynamic Engine Simulator**: Ingests mission flight profiles (`endurance`, `high_altitude`, `cruise`) and executes controlled fault injection ($+40\text{ °C}$ EGT bias for $t > 60\text{ s}$).
- **Thermodynamic Physics Model**: Calculates healthy reference baseline values for EGT, CHT, and oil temperature.
- **EMA Residual Smoothing**: Dampens raw single-step sensor noise using Exponential Moving Average ($\alpha = 0.2$).
- **Isolation Forest ML Model**: Detects multi-dimensional statistical anomalies across sensor telemetry and physical residual signals.
- **Explainability Engine**: Translates residual deviations into maintenance diagnostic messages (e.g. *"EGT is 39.5°C above expected. Suggests possible overheating."*).
- **Asynchronous API & WebSocket Stream**: Built on FastAPI with real-time push streams for minimal dashboard latency.
- **Interactive Streamlit Dashboard**: Renders gauges, Plotly charts, hybrid decision banners, diagnostic cards, and state telemetry tables.

---

## 6. Project Structure

```text
uav_engine_twin_demo/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & WebSocket server
│   ├── simulator.py         # Aero-piston engine telemetry simulator
│   ├── physics_model.py     # Thermodynamic expected behavior physics model
│   ├── twin_core.py        # Central state estimation & Digital Twin Core
│   ├── anomaly.py          # Legacy rule anomaly detector helpers
│   ├── mission_profiles.py # UAV flight profile definitions (endurance, etc.)
│   └── replay.py           # Mission CSV replay engine
├── dashboard/
│   └── app.py               # Streamlit live monitoring user interface
├── data/
│   ├── normal_telemetry.csv # Generated normal telemetry dataset
│   └── missions/
│       ├── mission_001.csv  # Endurance mission recording
│       └── mission_002.csv  # High altitude mission recording
├── docs/
│   ├── presentation_outline.md # 7-slide pitch deck presentation outline
│   ├── demo_script.md          # Complete presentation script & 3-min flow
│   └── architecture.md         # Full technical architecture specification
├── models/
│   └── isolation_forest_anomaly.pkl # Trained Isolation Forest model bundle
├── train_anomaly_model.py   # Offline ML training script
├── generate_mission.py      # Mission recording CLI generator
├── requirements.txt         # Project dependencies
└── README.md                # Main documentation
```

---

## 7. Requirements

- **Python**: `3.9` or higher recommended
- **Core Dependencies**:
  - `fastapi` & `uvicorn` (Backend web service & WebSocket)
  - `streamlit` & `websocket-client` (Frontend dashboard UI)
  - `scikit-learn` & `joblib` (Isolation Forest ML model)
  - `numpy`, `pandas`, `plotly` (Data processing & visualization)
  - `requests` (REST API client)

---

## 8. How to Run the Demo

### Option A — One-Click Automated Launcher (Recommended)
```bash
python run_demo.py
```
*This launches both the FastAPI backend and Streamlit dashboard automatically and opens `http://localhost:8501` in your default browser.*

### Option B — Manual Terminal Execution

**1. Install Dependencies**
```bash
pip install -r requirements.txt
```

**2. Start FastAPI Backend Service**
```bash
python -m uvicorn app.main:app --reload --port 8000
```
*Backend runs at `http://127.0.0.1:8000` with OpenAPI Swagger UI at `http://127.0.0.1:8000/docs`.*

**3. Launch Streamlit Dashboard (in a second terminal)**
```bash
python -m streamlit run dashboard/app.py
```
*Dashboard opens automatically in your browser at `http://localhost:8501`.*

---

## 9. Live Demo Flow

```text
START
  ↓
FastAPI Backend (http://127.0.0.1:8000)
  ↓
Engine Simulator / Replay Engine
  ↓
Telemetry Packets (RPM, Throttle, EGT, CHT, Oil Temp)
  ↓
Digital Twin Core Processing
  ↓
Physics Model Expected Predictions
  ↓
EMA Residual Calculation (Measured − Expected)
  ↓
Hybrid Anomaly Detection (Rule Thresholds + Isolation Forest ML)
  ↓
Engine Health Index (EHI) Assessment
  ↓
Degradation Accumulation & RUL Estimation
  ↓
Explainable Diagnostics Generation
  ↓
WebSocket Broadcast Stream
  ↓
Streamlit Dashboard Real-Time Display (http://localhost:8501)
```

---

## 10. Mission Replay

To replay a previously recorded mission:
1. Ensure the backend is running (`http://127.0.0.1:8000`).
2. Open the Streamlit dashboard (`http://localhost:8501`).
3. Locate **🎬 Mission Control & Replay** in the left sidebar.
4. Select `mission_001` or `mission_002` from the dropdown.
5. Click **▶️ Start Replay**.
6. The Digital Twin backend re-streams recorded CSV telemetry packet-by-packet through the **exact same physics and ML Digital Twin Core**, displaying live diagnostics.
7. Click **⏹️ Stop Replay** to return to live simulation mode.

Alternatively, trigger replay via REST API:
```bash
curl -X POST "http://127.0.0.1:8000/replay/start?mission=mission_001"
```

---

## 11. Example Diagnostic Output

### 1. Normal Operation
```json
{
  "main_indicator": "Normal operating behavior",
  "res_egt": -0.98,
  "res_cht": 0.24,
  "health_trend": "stable",
  "diagnostic_message": "Engine behavior is within the expected operating range.",
  "severity": "NORMAL"
}
```

### 2. Thermal Fault Operation (EGT Spike)
```json
{
  "main_indicator": "EGT residual",
  "res_egt": 39.46,
  "res_cht": -3.09,
  "health_trend": "degrading",
  "diagnostic_message": "EGT is 39.5°C above expected. This indicates elevated exhaust temperature and suggests possible overheating.",
  "severity": "CRITICAL"
}
```

### 3. ML-Only Anomaly
```json
{
  "main_indicator": "ML anomaly",
  "res_egt": 4.10,
  "res_cht": 2.30,
  "health_trend": "stable",
  "diagnostic_message": "ML anomaly detected: current telemetry differs from the learned normal operating pattern, although rule-based residuals remain within limits.",
  "severity": "WARNING"
}
```

---

## 12. Optional Add-ons & Extended Features

### Supervised ML Fault Classification (Random Forest)
A Random Forest classifier is trained on synthetic fault scenarios (`data/fault_classification.csv`) to classify patterns into:
- `NORMAL`
- `OVERHEATING`
- `LUBRICATION_ISSUE`

> **Disclaimer**: The lubrication fault class is currently represented using synthetic telemetry patterns because detailed lubrication sensors and validated lubrication-system models are not yet implemented. This classifier is intended strictly for prototype demonstration.

### Engine Health Trend Plot
The Streamlit dashboard tracks the Engine Health Index (%) over time in an interactive line chart, operating across both live simulation and mission replay modes.

### Interactive API Documentation
FastAPI automatically generates interactive Swagger documentation and OpenAPI specifications:
- **Interactive Swagger UI**: `http://127.0.0.1:8000/docs`
- **OpenAPI JSON Schema**: `http://127.0.0.1:8000/openapi.json`

### Docker Deployment
The project includes a `Dockerfile` and `docker-compose.yml` for multi-container deployment:
```bash
docker compose up --build
```
- FastAPI Backend: `http://localhost:8000`
- Streamlit Dashboard: `http://localhost:8501`

---

## 13. Current Prototype Scope

The current implementation includes:

- [x] Simulated aero-piston engine telemetry stream ($dt = 0.5\text{ s}$)
- [x] Physics-based expected EGT, CHT, and oil temperature model
- [x] Residual calculation ($\text{Measured} - \text{Expected}$) & EMA smoothing
- [x] Rule-based anomaly threshold detection
- [x] Isolation Forest ML anomaly detection (7 feature channels)
- [x] Random Forest supervised fault classification (`NORMAL`, `OVERHEATING`, `LUBRICATION_ISSUE`)
- [x] Hybrid rule + ML decision fusion
- [x] Engine Health Index (EHI 0–100%) & Live Health Trend chart
- [x] Degradation tracking ($d \in [0, 1]$)
- [x] Prototype Remaining Useful Life (RUL hours) estimation
- [x] Mission flight profiles (`endurance`, `high_altitude`, `cruise`)
- [x] Mission CSV recording & replay engine
- [x] Explainable diagnostics & human-readable maintenance wording
- [x] FastAPI REST & WebSocket synchronization backend with `/docs` Swagger UI
- [x] Streamlit interactive live monitoring dashboard UI
- [x] Dockerfile & Docker Compose deployment configuration

---

## 14. Planned Extensions

> **PLANNED / FUTURE DEVELOPMENT** (Not currently implemented):

### Engine Modeling & Subsystems
- **Propulsion Subsystem**: Torque measurement, propeller speed ratio, shaft power modeling.
- **Lubrication Subsystem**: Physical oil pressure & valve dynamics model.
- **Fuel & Mixture Subsystem**: Fuel flow rate, air-fuel ratio, injector pulse dynamics.
- **Ignition & Combustion**: Spark timing, cylinder pressure trace integration.
- **Cooling Subsystem**: Radiator pressure drop, ram air flow, coolant temperature loops.

### Hardware & Sensor Integration
- **ECU / FADEC Integration**: Direct ingestion of engine control unit data streams.
- **CAN Bus Interface**: Hardware-in-the-loop (HIL) CAN telemetry parsing.
- **Multi-Sensor Expansion**: Vibration sensors (accelerometers), manifold pressure transducers.

### Advanced AI & Prognostics
- **Deep Learning Classifiers**: Multi-class neural networks for component-level diagnosis.
- **Physics-Informed Neural Networks (PINNs)**: Hybrid physics-deep learning models.
- **Probabilistic RUL Estimation**: Weibull failure distributions and Bayesian RUL confidence bounds.

---

## 14. Limitations

- **Simplified Physics**: The thermodynamic physics equations are empirical approximations suitable for real-time twin demonstration, not 3D CFD combustion solvers.
- **Synthetic Simulator Baseline**: Telemetry is generated via an engine simulator with mathematical noise profiles; real aero-piston dynamics may introduce unmodeled harmonics.
- **Isolation Forest Scope**: The ML model detects statistical pattern anomalies but does not independently deduce physical root causes without rule residual context.
- **Prototype RUL Estimator**: Conceptual life-consumption estimator for demonstration purposes; requires fleet degradation datasets for physical certification.
- **Non-Certified**: This prototype is designed for research and demonstration, not flight-critical avionics deployment.

---

## 15. Future Validation

To transition from prototype to validated engineering system, planned validation milestones include:
1. Benchmarking physics model outputs against aero-piston engine test-cell dynamometer data.
2. Training ML classifiers on real engine fault run-to-failure telemetry datasets.
3. Conducting hardware-in-the-loop (HIL) testing via ECU CAN bus interfaces.
4. Tuning anomaly thresholds using historical UAV flight logs.

---

## 16. Team / Project Development

For complete presentation and architectural documentation, refer to:
- **Presentation Slide Deck Outline**: [docs/presentation_outline.md](file:///d:/uav_engine_twin_demo/docs/presentation_outline.md)
- **Live Demonstration Script & 3-Min Flow**: [docs/demo_script.md](file:///d:/uav_engine_twin_demo/docs/demo_script.md)
- **Technical Architecture Specification**: [docs/architecture.md](file:///d:/uav_engine_twin_demo/docs/architecture.md)

### Technical Layer Ownership Model
- **Physics / Engine Modeling Lead**: Thermodynamic curves, expected values, subsystem physics.
- **AI / ML Lead**: Model training, feature engineering, anomaly detection, prognosis.
- **Backend / Digital Twin Lead**: FastAPI, WebSockets, state estimation, replay engine.
- **Dashboard Lead**: Streamlit UI, Plotly charts, diagnostic cards, UX polish.
- **Integration / Hardware Lead**: ECU/FADEC interfaces, CAN integration, HIL testing.
