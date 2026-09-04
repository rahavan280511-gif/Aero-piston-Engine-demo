# Comprehensive Technical Documentation & Architecture Manual
## UAV Aero-Piston Engine Digital Twin & 3D Supercharged V8 System

---

## 1. Executive Summary

This project presents a real-time, physics-informed **Digital Twin** and **3D Interactive Health Monitoring System** for a Medium-Altitude Long-Endurance (MALE) UAV aero-piston engine. 

The application pairs first-principles thermodynamic state estimation equations with live sensor telemetry streams, residual analysis, hybrid machine learning anomaly detection (Isolation Forest), supervised fault classification (Random Forest), health degradation accumulation tracking, conceptual Remaining Useful Life (RUL) estimation, and an interactive **3D Supercharged V8 Aero-Engine model** inspired by Dominic Toretto's 1969 Dodge Charger from *The Fast & The Furious*.

---

## 2. Technology Stack

### Backend & API Framework
- **Python 3.11+**: Primary programming language for physics calculations, ML inference, and API server.
- **FastAPI (v0.110+)**: High-performance asynchronous web server framework handling REST endpoints and real-time WebSocket streams.
- **Uvicorn (v0.28+)**: ASGI server implementation for async I/O.
- **Pydantic (v2.6+)**: Data validation and strict typing contracts.

### Physics & Data Science Pipeline
- **NumPy (v1.26+)**: Fast numerical vector computing and matrix math.
- **Pandas (v2.2+)**: Structured time-series telemetry data manipulation and CSV processing.
- **Scikit-Learn (v1.4+)**: 
  - `IsolationForest`: Unsupervised anomaly detection model trained on multi-dimensional telemetry & residual features.
  - `RandomForestClassifier`: Supervised multi-class fault classifier (`NORMAL`, `OVERHEATING`, `LUBRICATION_ISSUE`).
- **Joblib (v1.3+)**: Efficient model serialization and artifact persistence.

### User Interface & Live Dashboard
- **Streamlit (v1.32+)**: Web dashboard framework rendering telemetry metrics, Plotly interactive charts, live diagnostic cards, and embedded 3D viewer.
- **Plotly (v5.19+)**: High-precision interactive time-series plots for real-time EGT, CHT, Oil Temperature, and Health Index monitoring.

### 3D Graphics Engine & Visualization
- **Three.js (v0.160.0 ES Modules)**: WebGL-based 3D scene rendering, studio lighting, materials, OrbitControls, and custom mesh animations.
- **HTML5 / ES6 JavaScript**: Modern web browser client hosting the 3D canvas and iframe postMessage / WebSocket integration.

### Deployment & Containerization
- **Docker & Docker-Compose**: Multi-stage container builds exposing port `8000` (FastAPI API) and port `8501` (Streamlit Dashboard).
- **Git**: Distributed source control.

---

## 3. System Architecture & End-to-End Pipeline

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
 │   EnginePhysicsModel (app/physics_model.py) ──> Residuals & EHI Calculation │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                    LAYER 4 — AI & HYBRID ANOMALY                          │
 │   Rule-Based Thresholds  +  Isolation Forest ML Model (7 Feature Channels)│
 │   + Supervised Random Forest Fault Classifier                              │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                    LAYER 5 — EXPLAINABILITY & RUL                         │
 │   Diagnostic Engine  +  Degradation Accumulation (RUL Hours Estimation)   │
 └─────────────────────────────────────┬─────────────────────────────────────┘
                                       │
                                       ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │                     LAYER 6 — VISUALIZATION & UI                          │
 │   Streamlit Dashboard (dashboard/app.py) + 3D Supercharged V8 (Three.js)  │
 └───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Implementation Details by Component

### 4.1 Engine Telemetry Simulator (`app/simulator.py`)
Generates realistic time-series telemetry snapshots at a cadence of $dt = 0.5\text{ s}$.
- **Parameters Simulated**: Engine RPM, Throttle Position ($0.20 - 0.95$), Exhaust Gas Temperature (EGT in °C), Cylinder Head Temperature (CHT in °C), and Oil Temperature (in °C).
- **Noise Model**: Additive Gaussian sensor noise ($\sigma_{\text{RPM}}=20$, $\sigma_{\text{EGT}}=5$, $\sigma_{\text{CHT}}=3$, $\sigma_{\text{OIL}}=2$).
- **Live Manual Control & Fault Injection**: Allows manual throttle override and instant fault injection (`NONE`, `OVERHEATING`, `LUBRICATION_ISSUE`, `EXHAUST_LEAK`).

### 4.2 Thermodynamic Physics Model (`app/physics_model.py`)
Computes expected healthy parameter baselines given current operational inputs:
$$\text{EGT}_{\text{expected}} = \text{EGT}_{\text{base}} + G_{\text{thr}} \cdot \text{Throttle} + G_{\text{rpm}} \cdot (\text{RPM} - \text{RPM}_{\text{idle}}) + G_{\text{amb}} \cdot \Delta T_{\text{ambient}}$$
$$\text{CHT}_{\text{expected}} = \text{CHT}_{\text{base}} + K_{\text{CHT}} \cdot (\text{EGT}_{\text{base}} - \text{EGT}_{\text{ref}}) + G_{\text{amb,cht}} \cdot \Delta T_{\text{ambient}}$$
$$\text{OIL}_{\text{expected}} = \text{OIL}_{\text{base}} + K_{\text{OIL}} \cdot (\text{EGT}_{\text{base}} - \text{EGT}_{\text{ref}}) + G_{\text{amb,oil}} \cdot \Delta T_{\text{ambient}}$$

### 4.3 Digital Twin Core (`app/twin_core.py`)
- **Residual Smoothing**: Applies Exponential Moving Average (EMA, $\alpha = 0.2$) on raw residuals:
  $$R_{\text{smooth}}(t) = \alpha \cdot (y_{\text{measured}} - y_{\text{expected}}) + (1 - \alpha) \cdot R_{\text{smooth}}(t-1)$$
- **Engine Health Index (EHI)**: Scalar health score normalized between $0$ (Critical) and $100$ (Nominal):
  $$\text{EHI} = \max\left(0, 100 \cdot \left(1 - \sum w_i \cdot P_i\right)\right)$$
- **Prognostics & RUL**: Accumulates health degradation ($d \in [0, 1]$) to calculate Remaining Useful Life hours ($\text{RUL} = 200 \times (1 - d)$).

### 4.4 Machine Learning Models (`models/`)
- **Unsupervised Anomaly Detection (`isolation_forest_anomaly.pkl`)**:
  - Trained on 3,000 samples covering dynamic flight mission profiles and manual throttle sweeps across $[0.20, 0.95]$.
  - Evaluates 7 core features: `[rpm, throttle, egt, cht, oil_temp, res_egt, res_cht]`.
  - Incorporates 3-step majority-vote hysteresis buffer to eliminate single-tick false alarm flickering.
- **Supervised Fault Classifier (`fault_classifier.pkl`)**:
  - Random Forest classifier trained on 3,000 fault-injected samples.
  - Classifies operational status into `NORMAL`, `OVERHEATING`, or `LUBRICATION_ISSUE` with $>99\%$ accuracy.

---

## 5. Iconic 3D Supercharged V8 Aero-Engine (`dashboard/3d_viewer/`)

Inspired by **Dominic Toretto's 1969 Dodge Charger R/T** from *The Fast & The Furious*, the 3D visualization renders an authentic 90° V8 engine with an exposed Roots Supercharger:

### Mechanical & Visual Design
1. **Enderle / BDS "Shotgun" Air Scoop**:
   - Stadium/capsule chrome housing with smooth rounded side walls.
   - Chrome front faceplate with **3 distinct circular bore holes**.
   - **3 Red Anodized Circular Butterfly Valves** inside the bores that **dynamically tilt open and close** in real-time response to throttle telemetry.
   - Stainless steel side throttle linkage rod and bracket on the right side.
2. **Dual Carburetors & Red Fuel Lines**:
   - Twin 4-barrel carburetors with chrome fuel pressure regulators, brass fittings, and red ignition wires along dark ribbed valve covers.
3. **6-71 Roots Supercharger (Blower)**:
   - Polished chrome blower housing with double rotor humps, side cooling ribs, and extended blower drive snout.
4. **Connected Blower Drive Belt & Pulley System**:
   - **Top Blower Snout Pulley**: Cogged aluminum pulley mounted at `Z = 1.08`.
   - **Bottom Crankshaft Blower Pulley**: Cogged aluminum pulley mounted at `Z = 1.08`.
   - **Side Tensioner Idler Pulley**: Mounted on a spring-loaded arm at `X = -0.32`.
   - **Continuous Wide Black Cogged Belt**: Looping around all three pulleys.
   - **Synchronized Z-Axis Rotation**: Pre-rotated Z-geometry ensures pure 360° wheel rotation around pulley shafts with zero wobble.
5. **Aero Propeller Assembly**:
   - Extended drive spindle (`Z = 1.45`) with polished spinner cone and 3 carbon fiber blades with yellow safety tips, rotating in sync with engine RPM.
6. **Telemetry Color Mapping**:
   - **CHT**: Dynamic Green → Yellow → Red color & emissive glow on cylinder heads and cooling fins.
   - **EGT**: Dynamic Green → Yellow → Red color & emissive glow on 8 exhaust primary headers and H-pipe crossover.
   - **Oil Temp**: Dynamic thermal color mapping on oil pan sump.
   - **Engine Health Index**: Engine block transforms from Silver (Nominal) → Anodized Amber (Caution) → Crimson Red (Critical/Overheating).
   - **Anomaly Alarm**: Pulsing background warning flash on active anomaly.

---

## 6. Project Directory Structure

```text
uav_engine_twin_demo/
├── app/
│   ├── __init__.py
│   ├── anomaly.py            # Rule-based thresholding module
│   ├── main.py               # FastAPI application, REST & WebSocket routes
│   ├── mission_profiles.py   # Pre-defined flight mission profile generators
│   ├── physics_model.py      # Thermodynamic expected state predictor
│   ├── replay.py             # CSV mission log replay engine
│   ├── simulator.py          # Real-time engine telemetry simulator
│   └── twin_core.py          # Central Digital Twin state & intelligence engine
├── dashboard/
│   ├── app.py                # Streamlit live monitoring dashboard
│   └── 3d_viewer/
│       ├── index.html        # 3D viewer HTML host
│       └── viewer.js         # Three.js 3D Supercharged V8 engine model
├── data/                     # Normal telemetry & CSV flight mission logs
├── models/
│   ├── isolation_forest_anomaly.pkl  # Trained Isolation Forest model
│   └── fault_classifier.pkl         # Trained Random Forest fault classifier
├── docs/                     # Architecture & presentation docs
├── Dockerfile                # Docker container build script
├── docker-compose.yml        # Docker Compose configuration
├── generate_fault_dataset.py # Fault dataset generator
├── generate_mission.py       # Mission recorder script
├── requirements.txt          # Python dependencies
├── run_demo.py               # One-click launcher script
├── train_anomaly_model.py    # Isolation Forest training pipeline
└── train_fault_classifier.py # Random Forest training pipeline
```

---

## 7. How to Run the Application

### Option A: Local Python Environment (Recommended for Development)

1. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

2. **Start the FastAPI Backend**:
   ```powershell
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Start the Streamlit Dashboard** (in a new terminal):
   ```powershell
   streamlit run dashboard/app.py
   ```

4. **Access Interfaces**:
   - **Streamlit Dashboard**: `http://localhost:8501`
   - **FastAPI Swagger API Docs**: `http://localhost:8000/docs`
   - **3D Supercharged V8 Model**: `http://localhost:8000/3d/`

---

### Option B: Containerized Execution with Docker

```powershell
docker-compose up --build
```

---

## 8. Summary of REST & WebSocket Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | System info and available endpoints |
| `/health` | GET | Container liveness check |
| `/status` | GET | Simulation state, step count, active WS clients |
| `/telemetry` | GET | Latest synchronized Digital Twin state snapshot |
| `/history?n=100` | GET | Recent history ring-buffer snapshots |
| `/reset` | POST | Reset simulation clock to $t = 0$ |
| `/simulator/control` | POST | Manual throttle override & live fault injection |
| `/simulator/reset_control`| POST | Reset to automatic flight profile simulation |
| `/replay/start?mission=x` | POST | Start replaying recorded flight CSV log |
| `/replay/stop` | POST | Stop replay and return to live telemetry mode |
| `/ws/telemetry` | WS | Real-time WebSocket telemetry push stream |
