"""
FastAPI Application — UAV Aero-Piston Engine Digital Twin.

Architecture
------------
A background asyncio task drives the simulation loop at real-time speed
(one step every ``dt`` seconds).  On each tick the simulator produces
telemetry that is immediately fed to the Digital Twin Core.  The resulting
:class:`TwinState` is kept in a module-level shared-state object and
broadcast to every active WebSocket client.

Exposed surface
---------------
  GET  /                  → system info card
  GET  /health            → liveness probe (for monitoring)
  GET  /status            → simulation run metadata
  GET  /telemetry         → latest combined twin state (JSON)
  GET  /history?n=<int>   → last *n* twin states (JSON array, max 500)
  POST /reset             → restart the simulation from t = 0
  WS   /ws/telemetry      → push latest twin state on every tick
       /ws/telemetry?interval=<float>  override push interval (seconds)

Design constraints
------------------
- No database, no external broker.
- Simulator + twin are synchronous; they run inside a dedicated asyncio
  task via a thin ``await asyncio.sleep()`` cadence.
- All shared state is protected with asyncio.Lock to be safe with future
  concurrent endpoint calls.
- CORS is fully open for local dashboard development.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.simulator import EngineSimulator
from app.twin_core import DigitalTwinCore, TwinState
from app.replay import MissionReplayEngine, list_available_missions

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("twin.api")

# ---------------------------------------------------------------------------
# Simulation configuration
# ---------------------------------------------------------------------------
_SIM_DT: float = 0.5          # seconds between simulation steps
_AMBIENT_TEMP: float = 25.0   # °C — ISA standard day
_HISTORY_MAXLEN: int = 500    # maximum states kept in ring buffer

# ---------------------------------------------------------------------------
# Shared runtime state  (module-level singletons, guarded by lock)
# ---------------------------------------------------------------------------
_sim_lock = asyncio.Lock()
_simulator: EngineSimulator | None = None
_twin: DigitalTwinCore | None = None
_latest_state: dict | None = None

# Mode Control (live vs replay)
_current_mode: str = "live"
_current_mission_name: str | None = None
_replay_engine: MissionReplayEngine | None = None

# Simulation metadata
_sim_meta: dict[str, Any] = {
    "started_at": None,
    "step_count": 0,
    "simulation_time": 0.0,
    "running": False,
    "mode": "live",
    "mission": None,
    "replay_progress_pct": 0.0,
}

# Background task handle
_sim_task: asyncio.Task | None = None


# ---------------------------------------------------------------------------
# WebSocket connection manager
# ---------------------------------------------------------------------------

class _ConnectionManager:
    """Tracks active WebSocket clients and delivers broadcast messages."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        log.info("WebSocket connected — %d active client(s)", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._connections:
            self._connections.remove(ws)
        log.info("WebSocket disconnected — %d active client(s)", len(self._connections))

    async def broadcast(self, payload: dict) -> None:
        """Send *payload* to all connected clients; drop stale connections."""
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    @property
    def client_count(self) -> int:
        return len(self._connections)


manager = _ConnectionManager()


# ---------------------------------------------------------------------------
# API response normalisation
# ---------------------------------------------------------------------------

def _to_api_format(state_dict: dict) -> dict:
    """
    Translate a raw ``TwinState.to_dict()`` payload into the stable public
    API contract consumed by the Streamlit dashboard and any external client.

    Mapping rationale
    -----------------
    - Internal names (``egt_measured``, ``health_index``, ``anomaly_detected``)
      reflect the Twin Core's internal data model.
    - Public API names (``egt``, ``health``, ``anomaly``) are shorter, cleaner,
      and more meaningful to consumers.
    - A concise ``fault_suggestion`` code is derived from ``anomaly_channels``
      so the dashboard can display a short label without parsing the full
      diagnostic message.
    """
    channels: list = state_dict.get("anomaly_channels", [])
    anomaly: bool  = state_dict.get("anomaly_detected", False)
    egt_smooth: float = state_dict.get("egt_residual_smooth", 0.0)
    cht_smooth: float = state_dict.get("cht_residual_smooth", 0.0)

    # Derive short fault code
    if not anomaly:
        fault_suggestion = "NOMINAL"
    elif "EGT" in channels and egt_smooth > 0:
        fault_suggestion = "POSSIBLE_OVERHEATING"
    elif "EGT" in channels and egt_smooth < 0:
        fault_suggestion = "EGT_SENSOR_LOW"
    elif "CHT" in channels and cht_smooth > 0:
        fault_suggestion = "THERMAL_DEGRADATION"
    elif "OIL_TEMP" in channels:
        fault_suggestion = "OIL_SYSTEM_CONCERN"
    else:
        fault_suggestion = "MULTI_CHANNEL_ANOMALY"

    return {
        # ── Core telemetry ────────────────────────────────────────────────
        "timestamp":     state_dict["timestamp"],
        "rpm":           state_dict["rpm"],
        "throttle":      state_dict["throttle"],
        "egt":           state_dict["egt_measured"],
        "cht":           state_dict["cht_measured"],
        "oil_temp":      state_dict["oil_temp_measured"],
        "fault_active":  state_dict["fault_active_gt"],
        # ── Physics-model expected values ─────────────────────────────────
        "egt_expected":      state_dict["egt_expected"],
        "cht_expected":      state_dict["cht_expected"],
        "oil_temp_expected": state_dict["oil_temp_expected"],
        # ── Smoothed residuals (primary Digital Twin signal) ──────────────
        "res_egt":  state_dict["egt_residual_smooth"],
        "res_cht":  state_dict["cht_residual_smooth"],
        "res_oil":  state_dict["oil_temp_residual_smooth"],
        # ── Raw single-step residuals (for reference) ─────────────────────
        "egt_residual": state_dict["egt_residual"],
        "cht_residual": state_dict["cht_residual"],
        # ── Engine Health Index ───────────────────────────────────────────
        "health":        state_dict["health_index"],
        "health_status": state_dict["health_status"],
        # ── Anomaly detection (Hybrid: Rule + ML) ─────────────────────────
        "anomaly_rule":     state_dict.get("anomaly_rule", False),
        "anomaly_score_ml": state_dict.get("anomaly_score_ml", 0.0),
        "anomaly_flag_ml":  state_dict.get("anomaly_flag_ml", "UNAVAILABLE"),
        "anomaly":          anomaly,
        "anomaly_channels": channels,
        "fault_suggestion": fault_suggestion,
        # ── Degradation & Conceptual RUL ─────────────────────────────────────
        "degradation": state_dict.get("degradation", 0.0),
        "rul_hours":   state_dict.get("rul_hours", 200.0),
        # ── Fault Classification (Step 12) ──────────────────────────────
        "fault_class":      state_dict.get("fault_class", "UNAVAILABLE"),
        "fault_confidence": state_dict.get("fault_confidence", 0.0),
        # ── Full diagnostic message & Explainability (Step 10) ──────────
        "diagnostic":  state_dict["diagnostic"],
        "explanation": state_dict.get("explanation", {
            "main_indicator": "Normal operating behavior" if not anomaly else "EGT residual",
            "res_egt": state_dict.get("egt_residual_smooth", 0.0),
            "res_cht": state_dict.get("cht_residual_smooth", 0.0),
            "health_trend": "stable",
            "diagnostic_message": state_dict.get("diagnostic", "Engine behavior is within the expected operating range."),
            "severity": "NORMAL" if not anomaly else "WARNING",
        }),
    }


# ---------------------------------------------------------------------------
# Simulation loop  (runs as a background asyncio task)
# ---------------------------------------------------------------------------

async def _simulation_loop() -> None:
    """
    Continuously step the simulator and twin core at real-time speed.

    Each iteration:
      1. Calls ``simulator.step()`` to produce one telemetry packet.
      2. Passes it to ``twin.update()`` to obtain a full :class:`TwinState`.
      3. Serialises the state and stores it as the globally latest value.
      4. Broadcasts the state to all connected WebSocket clients.
      5. Sleeps for ``_SIM_DT`` seconds before the next iteration.
    """
    global _latest_state

    log.info("Simulation loop starting (dt=%.2f s, ambient=%.1f °C)", _SIM_DT, _AMBIENT_TEMP)
    _sim_meta["running"] = True
    _sim_meta["started_at"] = datetime.now(timezone.utc).isoformat()

    try:
        while True:
            async with _sim_lock:
                if _current_mode == "replay" and _replay_engine is not None:
                    telem, is_finished = _replay_engine.get_step()
                    _sim_meta["replay_progress_pct"] = _replay_engine.progress_pct
                    if is_finished:
                        log.info("Mission replay completed for '%s'.", _current_mission_name)
                        _sim_meta["running"] = False
                else:
                    telem = _simulator.step()                      # type: ignore[union-attr]

                state: TwinState = _twin.update(telem)         # type: ignore[union-attr]
                # Normalise to stable public API format before storing/broadcasting
                payload = _to_api_format(state.to_dict())
                payload["mode"] = _current_mode
                payload["mission"] = _current_mission_name
                _latest_state = payload
                _sim_meta["step_count"] = _twin.step_count     # type: ignore[union-attr]
                _sim_meta["simulation_time"] = round(state.timestamp, 2)
                _sim_meta["mode"] = _current_mode
                _sim_meta["mission"] = _current_mission_name

            # Broadcast outside the lock so slow clients don't delay simulation
            await manager.broadcast(payload)

            # Log anomaly transitions to the server console
            if state.anomaly_detected:
                log.warning(
                    "ANOMALY t=%.1f s | channels=%s | EHI=%.1f | %s",
                    state.timestamp,
                    state.anomaly_channels,
                    state.health_index,
                    state.diagnostic[:80],
                )

            await asyncio.sleep(_SIM_DT)

    except asyncio.CancelledError:
        log.info("Simulation loop cancelled — shutting down cleanly.")
        _sim_meta["running"] = False
        raise


# ---------------------------------------------------------------------------
# FastAPI lifespan  (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Initialise singletons and start the simulation loop on startup."""
    global _simulator, _twin, _sim_task

    log.info("Starting UAV Engine Digital Twin API...")
    _simulator = EngineSimulator(dt=_SIM_DT, seed=None)   # non-deterministic
    _twin = DigitalTwinCore(ambient_temp=_AMBIENT_TEMP, history_maxlen=_HISTORY_MAXLEN)

    _sim_task = asyncio.create_task(_simulation_loop(), name="simulation_loop")

    yield   # ── application is running ──────────────────────────────────────

    log.info("Shutting down UAV Engine Digital Twin API...")
    _sim_task.cancel()
    try:
        await _sim_task
    except asyncio.CancelledError:
        pass
    log.info("Shutdown complete.")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="UAV Aero-Piston Engine Digital Twin API",
    description=(
        "Real-time engine telemetry stream, first-principles thermodynamic Digital Twin, "
        "hybrid rule + Isolation Forest anomaly detection, Random Forest fault classification, "
        "degradation tracking, conceptual RUL estimation, explainable diagnostics, and mission replay API."
    ),
    version="0.3.0",
    lifespan=_lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow local Streamlit dashboard (any origin, port 8501 by default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# 3D Engine Viewer Mounting & Route
# ---------------------------------------------------------------------------
app.mount(
    "/3d",
    StaticFiles(directory="dashboard/3d_viewer"),
    name="3d_viewer"
)

@app.get("/3d-viewer", tags=["Viewer"], summary="3D Engine Viewer HTML")
async def get_3d_viewer():
    """Serves the 3D Engine Viewer HTML page."""
    return FileResponse("dashboard/3d_viewer/index.html")


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["System"], summary="System info card")
async def root() -> dict:
    """
    Returns a static description card.
    Useful as a quick liveness check from a browser.
    """
    return {
        "system": "UAV Aero-Piston Engine Digital Twin",
        "version": "0.2.0",
        "description": "Physics-based digital twin with real-time EHI and anomaly detection.",
        "endpoints": {
            "latest_telemetry": "GET /telemetry",
            "history":          "GET /history?n=<int>",
            "status":           "GET /status",
            "reset":            "POST /reset",
            "websocket":        "WS /ws/telemetry",
            "docs":             "GET /docs",
        },
    }


@app.get("/health", tags=["System"], summary="Liveness probe")
async def health_check() -> dict:
    """Minimal liveness endpoint for load-balancer / container health probes."""
    return {
        "status": "healthy",
        "simulation_running": _sim_meta.get("running", False),
    }


@app.get("/status", tags=["System"], summary="Simulation run metadata")
async def simulation_status() -> dict:
    """
    Returns metadata about the current simulation session:
    step count, wall-clock start time, simulated time elapsed,
    and number of active WebSocket clients.
    """
    return {
        **_sim_meta,
        "websocket_clients": manager.client_count,
        "history_length": len(_twin.history) if _twin else 0,  # type: ignore[arg-type]
    }


@app.get("/telemetry", tags=["Data"], summary="Latest twin state")
async def get_telemetry() -> dict:
    """
    Returns the most recent combined telemetry + Digital Twin state snapshot.

    The response contains:
    - Raw sensor readings (rpm, egt, cht, oil_temp, throttle)
    - Physics-model expected values
    - Per-channel residuals (raw and EMA-smoothed)
    - Engine Health Index (0–100) and status label
    - Anomaly detection results and diagnostic message
    - Ground-truth fault flag (for dashboard validation display)
    """
    if _latest_state is None:
        raise HTTPException(
            status_code=503,
            detail="Simulation has not produced any data yet. Please retry shortly."
        )
    return _latest_state


@app.get("/history", tags=["Data"], summary="Recent twin state history")
async def get_history(
    n: int = Query(default=100, ge=1, le=500, description="Number of recent states to return"),
) -> list[dict]:
    """
    Returns the last *n* Digital Twin state snapshots (most recent last).

    Useful for the dashboard to initialise time-series charts without
    waiting for enough WebSocket frames to accumulate.

    - Maximum 500 entries (the internal ring buffer capacity).
    - States are ordered oldest → newest.
    """
    if _twin is None or len(_twin.history) == 0:
        return []

    async with _sim_lock:
        # Snapshot history under lock to avoid mid-append iteration
        all_states = list(_twin.history)

    # Slice to requested window (most recent n); normalise each state
    selected = all_states[-n:]
    return [_to_api_format(s.to_dict()) for s in selected]


@app.post("/reset", tags=["Control"], summary="Reset simulation to t = 0")
async def reset_simulation() -> dict:
    """
    Restarts both the engine simulator and the digital twin from initial
    conditions (t = 0, all state variables zeroed, EHI = 100).

    WebSocket stream continues without interruption — clients will simply
    see a discontinuity in the timestamp as it jumps back to 0.5 s.
    """
    async with _sim_lock:
        if _simulator is None or _twin is None:
            raise HTTPException(status_code=503, detail="Simulation not yet initialised.")
        _simulator.reset()
        _twin.reset()
        _sim_meta["step_count"] = 0
        _sim_meta["simulation_time"] = 0.0
        _sim_meta["started_at"] = datetime.now(timezone.utc).isoformat()

    log.info("Simulation reset requested via POST /reset")
    return {"status": "reset", "message": "Simulation restarted from t = 0."}


@app.post("/simulator/control", tags=["Control"], summary="Set manual simulator controls & fault injection")
async def simulator_control(
    manual_override: bool = Query(default=True, description="Enable or disable manual control mode"),
    throttle: float = Query(default=0.6, ge=0.2, le=0.95, description="Manual throttle position (0.2 - 0.95)"),
    injected_fault: str = Query(default="NONE", description="Fault injection mode (NONE, OVERHEATING, LUBRICATION_ISSUE, EXHAUST_LEAK)"),
) -> dict:
    """
    Manually override simulator throttle and dynamically inject specific live fault symptoms.
    """
    async with _sim_lock:
        if _simulator is None:
            raise HTTPException(status_code=503, detail="Simulator not initialised.")
        
        if manual_override:
            _simulator.set_manual_control(throttle=throttle, injected_fault=injected_fault)
            log.info("Manual simulator control set: throttle=%.2f, fault=%s", throttle, injected_fault)
        else:
            _simulator.clear_manual_control()
            log.info("Manual simulator control cleared.")

    return {
        "status": "success",
        "manual_override": _simulator.manual_override,
        "throttle": _simulator.manual_throttle,
        "injected_fault": _simulator.injected_fault,
    }


@app.post("/simulator/reset_control", tags=["Control"], summary="Clear manual simulator controls")
async def reset_simulator_control() -> dict:
    """Clear manual simulator controls and return to automatic flight simulation."""
    async with _sim_lock:
        if _simulator is None:
            raise HTTPException(status_code=503, detail="Simulator not initialised.")
        _simulator.clear_manual_control()

    log.info("Manual simulator control reset.")
    return {"status": "success", "message": "Manual controls cleared. Automatic simulation restored."}


# ---------------------------------------------------------------------------
# Replay Endpoints
# ---------------------------------------------------------------------------

@app.get("/missions", tags=["Replay"], summary="List available mission recordings")
async def get_missions() -> dict:
    """Returns a list of all recorded mission CSV files available in data/missions/."""
    return {"missions": list_available_missions()}


@app.get("/replay/status", tags=["Replay"], summary="Get current replay status")
async def replay_status() -> dict:
    """Returns current system mode (live or replay) and mission progress."""
    return {
        "mode": _current_mode,
        "mission": _current_mission_name,
        "running": _sim_meta.get("running", False),
        "progress_pct": _sim_meta.get("replay_progress_pct", 0.0),
    }


@app.post("/replay/start", tags=["Replay"], summary="Start mission replay")
async def start_replay(
    mission: str = Query(default="mission_001", description="Mission recording name (e.g. mission_001)"),
) -> dict:
    """
    Start replaying a recorded mission CSV through the Digital Twin Core.
    """
    global _current_mode, _current_mission_name, _replay_engine, _twin
    async with _sim_lock:
        try:
            _replay_engine = MissionReplayEngine(mission)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to load mission: {e}")

        # Re-initialize twin core for clean mission evaluation baseline
        _twin = DigitalTwinCore(ambient_temp=_AMBIENT_TEMP, history_maxlen=_HISTORY_MAXLEN)
        _current_mode = "replay"
        _current_mission_name = mission
        _sim_meta["mode"] = "replay"
        _sim_meta["mission"] = mission
        _sim_meta["running"] = True
        _sim_meta["replay_progress_pct"] = 0.0
        log.info("Started mission replay for '%s'", mission)

    return {"status": "started", "mode": "replay", "mission": mission}


@app.post("/replay/stop", tags=["Replay"], summary="Stop mission replay")
async def stop_replay() -> dict:
    """
    Stop active mission replay and return the Digital Twin to live simulation mode.
    """
    global _current_mode, _current_mission_name, _replay_engine, _simulator, _twin
    async with _sim_lock:
        _current_mode = "live"
        _current_mission_name = None
        _replay_engine = None
        _simulator.reset()
        _twin.reset()
        _sim_meta["mode"] = "live"
        _sim_meta["mission"] = None
        _sim_meta["running"] = True
        _sim_meta["replay_progress_pct"] = 0.0
        log.info("Stopped mission replay. Switched to live simulation mode.")

    return {"status": "stopped", "mode": "live"}


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws/telemetry")
async def websocket_telemetry(
    ws: WebSocket,
    interval: float = Query(default=0.0, ge=0.0, le=10.0,
                            description="Optional additional delay between frames (seconds)"),
):
    """
    WebSocket push stream — delivers one :class:`TwinState` JSON frame per
    simulation tick (every ``dt`` seconds ≈ 0.5 s by default).

    Query parameters
    ----------------
    interval : float
        Extra sleep added between frames on the *client* side of this
        handler.  Set to 0 (default) for maximum update rate.
        Useful for lower-bandwidth connections or slow dashboards.

    Protocol
    --------
    - Client connects.
    - Server immediately sends the latest state (if available) so the
      client can initialise its display without waiting for the next tick.
    - Server then pushes new states on every simulation tick via
      :meth:`_ConnectionManager.broadcast`.
    - Client can send any text frame as a ping; server echoes ``{"pong": true}``.
    - Connection closes normally when the client disconnects.
    """
    await manager.connect(ws)

    try:
        # ── Prime the client with the latest known state ──────────────────
        if _latest_state is not None:
            await ws.send_json(_latest_state)

        # ── Keep alive: echo any client pings, wait for disconnect ────────
        while True:
            try:
                text = await asyncio.wait_for(ws.receive_text(), timeout=_SIM_DT + interval + 1.0)
                # Client sent a message — treat as a ping
                await ws.send_json({"pong": True, "received": text[:64]})
            except asyncio.TimeoutError:
                # No client message this cycle — that's fine, keep waiting
                pass

    except WebSocketDisconnect:
        log.info("WebSocket client disconnected cleanly.")
    except Exception as exc:
        log.warning("WebSocket error: %s", exc)
    finally:
        manager.disconnect(ws)
