# Demonstration Script — UAV Aero-Piston Engine Digital Twin

This script guides the presenter through demonstrating the **UAV Aero-Piston Engine Digital Twin Demo** to evaluators, faculty review panels, or project team selection committees.

---

## Pre-Demo Checklist

Run through this checklist prior to starting the presentation:

- [ ] Python virtual environment activated (`venv` or `conda`).
- [ ] Required dependencies installed (`pip install -r requirements.txt`).
- [ ] Isolation Forest model exists (`models/isolation_forest_anomaly.pkl`).
- [ ] Mission recordings exist (`data/missions/mission_001.csv` and `data/missions/mission_002.csv`).
- [ ] FastAPI backend starts cleanly (`python -m uvicorn app.main:app --port 8000`).
- [ ] Streamlit dashboard starts cleanly (`streamlit run dashboard/app.py`).
- [ ] Streamlit connects to WebSocket (`🟢 Backend: CONNECTED`).
- [ ] Expected physics values visible on telemetry charts.
- [ ] ML anomaly score gauge and score line chart visible.
- [ ] Health score index gauge displaying baseline 100%.
- [ ] Degradation tracking metric showing 0.00%.
- [ ] Estimated RUL displaying baseline 200.0 hours.
- [ ] ENGINE DIAGNOSTICS panel visible with NORMAL status.
- [ ] Mission control replay dropdown and start/stop buttons operational.
- [ ] Terminal windows clear of error stack traces.

---

## Script Walkthrough

### Opening — 30 seconds (Problem & Vision)

> *"Good morning / afternoon. An aero-piston engine on a Medium-Altitude Long-Endurance UAV produces thousands of sensor telemetry frames during a 24-hour mission. The fundamental challenge in health monitoring is not simply collecting raw data — it is determining whether the engine is behaving as expected under dynamic flight loads."*
>
> *"Our project implements an AI-Enabled Digital Twin. It continuously synchronizes incoming telemetry with a first-principles physics model to compute real-time residuals, feeds those signals into a hybrid rule and ML anomaly detector, tracks health degradation over time, estimates remaining useful life, and generates engineer-friendly explainable diagnostics."*

---

### Demo Part 1 — Normal Operation (Engine Baseline)

> *"Here on the Streamlit live dashboard, we see the real-time telemetry stream coming from our FastAPI backend via WebSocket."*
>
> *"Notice the primary telemetry channels: Engine Speed at ~5000 RPM, Exhaust Gas Temperature at ~650°C, Cylinder Head Temperature at ~180°C, and Oil Temperature at ~80°C. The Engine Health Index (EHI) displays a healthy 100%, accumulated degradation is at 0%, and estimated RUL is 200 hours."*

---

### Demo Part 2 — Physics Residuals (Measured vs. Expected)

> *"In the middle section, notice the dashed green lines on our Plotly charts. Those represent the thermodynamic expected values computed live by our Engine Physics Model based on throttle, RPM, and ambient air conditions."*
>
> *"The Digital Twin continuously subtracts expected values from measured values to compute smoothed residuals ($\text{Measured} - \text{Expected}$). Under normal operating conditions, these residuals stay near zero ($+2.4\text{ °C}$ EGT residual), indicating the engine is behaving exactly as physics predicts."*

---

### Demo Part 3 — AI Anomaly Detection (Isolation Forest)

> *"In the Hybrid Anomaly Detection System panel, we combine two complementary detection layers: rule-based threshold monitoring and machine learning distribution monitoring."*
>
> *"Our Isolation Forest ML model is trained offline on 7 feature channels. The normalized ML Anomaly Score gauge reads near zero ($0.12$), indicating the multi-dimensional sensor telemetry conforms to learned healthy flight patterns."*

---

### Demo Part 3.5 — Supervised ML Fault Classification (Random Forest)

> *"In the Supervised ML Fault Classification panel, we run a Random Forest classifier in parallel with the Isolation Forest anomaly detector."*
>
> *"The anomaly detector tells us that engine behavior has become unusual. The fault classifier then provides a prototype classification of the observed pattern, while the physics residuals provide an interpretable reason for the abnormal behavior."*
>
> *"Here, the Random Forest model predicts `OVERHEATING` with a model confidence of 99.2%, demonstrating how AI classification complements physics-based explainability."*

---

### Demo Part 4 — Simulated Fault Scenario (EGT Bias)

> *"Now let's observe what happens when a thermal fault occurs. At $t = 60\text{ s}$, an EGT thermal anomaly is injected into the simulator."*
>
> *(Point to the dashboard as the fault activates)*
>
> *"Notice the sequence of events:"*
> 1. *"Measured EGT diverges rapidly above the physics model line."*
> 2. *"The smoothed EGT residual jumps past the $+15\text{ °C}$ threshold to $+39.5\text{ °C}$."*
> 3. *"The Rule-Based Detector flags an anomaly, while the Isolation Forest ML Anomaly Score spikes above $0.60$."*
> 4. *"The Random Forest fault classifier identifies the pattern as `OVERHEATING` with high probability."*
> 5. *"The Engine Health Index drops from $100\%$ to ~ $54\%$, visible in real-time on our Live Health Trend chart."*
> 6. *"Accumulated degradation begins accumulating, causing the estimated RUL to decrease below $200\text{ hours}$."*

---

### Demo Part 5 — Explainability & Diagnostics

> *"Instead of simply flashing a generic 'ANOMALY DETECTED' warning, look at our dedicated **ENGINE DIAGNOSTICS** panel."*
>
> *"The Digital Twin isolates the main indicator as **EGT residual**, identifies the health trend as **DEGRADING**, and produces a maintenance-oriented diagnostic message:"*
>
> `Diagnostic: EGT is 39.5°C above expected. This indicates elevated exhaust temperature and suggests possible overheating.`
>
> *"This lightweight explainability layer allows ground station operators and field engineers to immediately understand the physical cause and thermal severity of the anomaly."*

---

### Demo Part 6 — Mission Replay Mode

> *"Now let's demonstrate our Mission Replay capability."*
>
> *(Select `mission_001` from the sidebar and click **▶️ Start Replay**)*
>
> *"The system switches from live simulation mode to replay mode. It reads recorded CSV flight data and streams each raw telemetry packet through the exact same Digital Twin Core. This allows flight safety officers to perform post-flight health audits and replay critical flight segments under identical physics and AI diagnostic logic."*

---

### Closing — 30 seconds

> *"In summary, this prototype demonstrates a complete end-to-end Digital Twin intelligence pipeline: from raw telemetry ingestion to physics residual calculation, ML anomaly detection, degradation tracking, conceptual RUL estimation, and explainable diagnostics."*
>
> *"Our modular architecture is designed so that synthetic simulation streams can progressively be replaced by real ECU, FADEC, and CAN bus telemetry as hardware integration proceeds. Thank you, and we welcome your questions."*

---

## 3-Minute Speed Demo Flow

For rapid team-selection interviews or high-speed pitch presentations, use this condensed timeline:

| Time | Section | Key Visuals / Actions | Core Narrative |
| :--- | :--- | :--- | :--- |
| **0:00–0:30** | **Problem & Vision** | Slide 1 or Title | MALE UAV long-endurance reliability challenge; moving from raw threshold alerts to physics + AI virtual synchronization. |
| **0:30–1:00** | **Architecture** | Slide 2 or Dashboard Header | Core flow: Telemetry $\rightarrow$ Physics Model $\rightarrow$ Residuals $\rightarrow$ Hybrid AI $\rightarrow$ Health/RUL $\rightarrow$ Diagnostics. |
| **1:00–1:45** | **Normal Operation** | Gauges & Telemetry Charts | Show 100% EHI, near-zero residuals, physics expected curves tracking measured inputs cleanly. |
| **1:45–2:15** | **Fault Scenario** | Thermal charts divergence | Observe EGT fault injection: residual spikes $+39.5\text{ °C}$, ML score spikes, EHI drops to ~ $54\%$, RUL decreases. |
| **2:15–2:40** | **Explainable Diagnostics** | ENGINE DIAGNOSTICS panel | Highlight Main Indicator (`EGT residual`), Trend (`DEGRADING`), and readable diagnostic message. |
| **2:40–3:00** | **Replay & Next Steps** | Replay button / Slide 7 | Demonstrate mission CSV replay; wrap up with planned FADEC/CAN subsystem extensions. |
