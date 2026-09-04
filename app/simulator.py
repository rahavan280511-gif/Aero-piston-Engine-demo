"""
UAV Aero-Piston Engine & Sensor Telemetry Simulator.

Provides a continuous time-series simulation of engine operating parameters
with realistic physics-inspired state equations, Gaussian sensor noise, and
a configurable EGT sensor fault injection profile.
"""

import numpy as np


# ---------------------------------------------------------------------------
# Constants / Defaults
# ---------------------------------------------------------------------------

# Throttle profile
_THROTTLE_CENTRE = 0.4
_THROTTLE_AMPLITUDE = 0.3
_THROTTLE_FREQ = 0.05          # rad/s  (slow mission-profile sweep)
_THROTTLE_NOISE_STD = 0.01     # small operational variation
_THROTTLE_MIN = 0.2
_THROTTLE_MAX = 0.9

# RPM model
_RPM_IDLE = 2000               # RPM at zero throttle reference
_RPM_GAIN = 2500               # RPM increase per unit throttle
_RPM_NOISE_STD = 20.0          # sensor / shaft variation (RPM)

# EGT model — first-order linear function of throttle and RPM
_EGT_OFFSET = 400.0            # base EGT at idle (°C)
_EGT_THROTTLE_GAIN = 600.0     # °C per throttle unit
_EGT_RPM_GAIN = 0.05           # °C per excess RPM above 2000
_EGT_NOISE_STD = 5.0           # sensor noise (°C)

# CHT model — driven by EGT thermal coupling
_CHT_OFFSET = 120.0            # base CHT (°C)
_CHT_EGT_COUPLING = 0.6        # °C CHT per °C EGT above 400
_CHT_NOISE_STD = 3.0           # sensor noise (°C)

# Oil temperature model
_OIL_TEMP_OFFSET = 80.0        # base oil temp (°C)
_OIL_TEMP_EGT_COUPLING = 0.2   # °C oil per °C EGT above 400
_OIL_TEMP_NOISE_STD = 2.0      # sensor noise (°C)

# Fault injection
_FAULT_TRIGGER_TIME = 60.0     # seconds — EGT bias activates after this time
_EGT_FAULT_BIAS = 40.0         # °C positive bias introduced by sensor fault


class EngineSimulator:
    """
    Simulates a UAV aero-piston engine telemetry stream.

    The simulation advances in fixed time-steps (dt).  On each call to
    :meth:`step` the internal state is updated and a snapshot of all
    measured parameters is returned as a dictionary.

    Parameters
    ----------
    dt : float
        Simulation time-step in seconds (default 0.5 s).
    seed : int | None
        Random seed for reproducible noise sequences.  Pass ``None`` for
        non-deterministic operation (default).
    """

    def __init__(
        self,
        dt: float = 0.5,
        seed: int | None = None,
        enable_fault: bool = False,
        mission_profile: Any = None,
    ) -> None:
        self._rng = np.random.default_rng(seed)

        # ── Time ──────────────────────────────────────────────────────────
        self.dt: float = dt
        self.t: float = 0.0
        self.enable_fault: bool = enable_fault

        # ── Mission profile ───────────────────────────────────────────────
        self._mission_profile_fn = None
        if mission_profile is not None:
            if callable(mission_profile):
                self._mission_profile_fn = mission_profile
            elif isinstance(mission_profile, str):
                from app.mission_profiles import get_mission_profile
                self._mission_profile_fn = get_mission_profile(mission_profile)

        # ── Engine state (initialised at plausible idle values) ───────────
        self.throttle: float = _THROTTLE_CENTRE
        self.rpm: float = _RPM_IDLE + _RPM_GAIN * _THROTTLE_CENTRE
        self.egt: float = _EGT_OFFSET                # measured EGT (°C)
        self.cht: float = _CHT_OFFSET                # measured CHT (°C)
        self.oil_temp: float = _OIL_TEMP_OFFSET      # measured oil temp (°C)

        # ── Fault & Manual Control State ──────────────────────────────
        self.fault_active: bool = False
        self._egt_bias: float = 0.0
        self._cht_bias: float = 0.0
        self._oil_bias: float = 0.0
        
        self.manual_override: bool = False
        self.manual_throttle: float = 0.6
        self.injected_fault: str = "NONE"

    # ------------------------------------------------------------------
    # Public Control API
    # ------------------------------------------------------------------

    def set_manual_control(self, throttle: float = 0.6, injected_fault: str = "NONE") -> None:
        """Enable manual simulator control and set live fault mode."""
        self.manual_override = True
        self.manual_throttle = float(np.clip(throttle, _THROTTLE_MIN, _THROTTLE_MAX))
        self.injected_fault = injected_fault.upper().strip()

    def clear_manual_control(self) -> None:
        """Clear manual control override and return to auto simulation."""
        self.manual_override = False
        self.injected_fault = "NONE"

    def step(self) -> dict:
        """
        Advance the simulation by one time-step and return current telemetry.
        """
        # 1. Advance simulation clock
        self.t += self.dt

        # 2. Determine throttle and RPM baseline
        mp_fault_mode = "NONE"
        if self.manual_override:
            self.throttle = float(np.clip(self.manual_throttle, _THROTTLE_MIN, _THROTTLE_MAX))
            rpm_true = _RPM_IDLE + _RPM_GAIN * self.throttle
        elif self._mission_profile_fn is not None:
            mp = self._mission_profile_fn(self.t)
            self.throttle = float(mp.get("throttle", _THROTTLE_CENTRE))
            rpm_true = float(mp.get("rpm_base", _RPM_IDLE + _RPM_GAIN * self.throttle))
            mp_fault_mode = mp.get("fault_mode", "NONE")
        else:
            self.throttle = self._compute_throttle(self.t)
            rpm_true = _RPM_IDLE + _RPM_GAIN * self.throttle

        # Determine effective active fault mode
        active_fault_mode = self.injected_fault if self.manual_override else mp_fault_mode

        # 3. RPM — baseline + Gaussian noise
        self.rpm = rpm_true + self._noise(_RPM_NOISE_STD)

        # 4. True (noiseless) engine states
        egt_true = (
            _EGT_OFFSET
            + _EGT_THROTTLE_GAIN * self.throttle
            + _EGT_RPM_GAIN * (rpm_true - _RPM_IDLE)
        )
        cht_true = _CHT_OFFSET + _CHT_EGT_COUPLING * (egt_true - _EGT_OFFSET)
        oil_temp_true = _OIL_TEMP_OFFSET + _OIL_TEMP_EGT_COUPLING * (egt_true - _EGT_OFFSET)

        # 5. Fault Injection Biases
        egt_bias = 0.0
        cht_bias = 0.0
        oil_bias = 0.0
        rpm_drag = 0.0

        if active_fault_mode == "OVERHEATING":
            egt_bias = 120.0
            cht_bias = 45.0
            self.fault_active = True
        elif active_fault_mode == "LUBRICATION_ISSUE":
            oil_bias = 35.0
            rpm_drag = 150.0   # mechanical friction drag
            self.fault_active = True
        elif active_fault_mode == "EXHAUST_LEAK":
            egt_bias = -60.0
            self.fault_active = True
        elif self.enable_fault and not self.manual_override and self.t > _FAULT_TRIGGER_TIME:
            egt_bias = _EGT_FAULT_BIAS
            self.fault_active = True
        else:
            self.fault_active = False

        # Apply friction drag to RPM
        self.rpm = max(1000.0, rpm_true - rpm_drag) + self._noise(_RPM_NOISE_STD)

        # 6. Add noise + fault bias to measured values
        self.egt = egt_true + egt_bias + self._noise(_EGT_NOISE_STD)
        self.cht = cht_true + cht_bias + self._noise(_CHT_NOISE_STD)
        self.oil_temp = oil_temp_true + oil_bias + self._noise(_OIL_TEMP_NOISE_STD)

        return self._build_telemetry()

    def reset(self) -> None:
        """Reset simulation time and fault state to initial conditions."""
        self.t = 0.0
        self.throttle = _THROTTLE_CENTRE
        self.rpm = _RPM_IDLE + _RPM_GAIN * _THROTTLE_CENTRE
        self.egt = _EGT_OFFSET
        self.cht = _CHT_OFFSET
        self.oil_temp = _OIL_TEMP_OFFSET
        self.fault_active = False
        self._egt_bias = 0.0
        self.clear_manual_control()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_throttle(self, t: float) -> float:
        """Return throttle position at time *t* (clamped to valid range)."""
        raw = (
            _THROTTLE_CENTRE
            + _THROTTLE_AMPLITUDE * np.sin(_THROTTLE_FREQ * t)
            + self._noise(_THROTTLE_NOISE_STD)
        )
        return float(np.clip(raw, _THROTTLE_MIN, _THROTTLE_MAX))

    def _noise(self, std: float) -> float:
        """Return a single Gaussian noise sample with zero mean and given std."""
        return float(self._rng.normal(loc=0.0, scale=std))

    def _build_telemetry(self) -> dict:
        """Package current state into the standard telemetry dictionary."""
        return {
            "timestamp": round(self.t, 4),
            "throttle": round(self.throttle, 4),
            "rpm": round(self.rpm, 2),
            "egt": round(self.egt, 2),       # Exhaust Gas Temperature (°C)
            "cht": round(self.cht, 2),       # Cylinder Head Temperature (°C)
            "oil_temp": round(self.oil_temp, 2),
            "fault_active": self.fault_active,
        }


# ---------------------------------------------------------------------------
# Quick self-test  (run: python -m app.simulator)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    sim = EngineSimulator(dt=0.5, seed=42)
    print(f"{'t':>8} {'throttle':>9} {'rpm':>8} {'egt':>8} {'cht':>8} {'oil':>8} {'fault':>6}")
    print("-" * 62)

    for _ in range(160):   # 80 seconds of simulated time
        telem = sim.step()
        if telem["timestamp"] % 5.0 < sim.dt:   # print every ~5 s
            print(
                f"{telem['timestamp']:>8.1f} "
                f"{telem['throttle']:>9.3f} "
                f"{telem['rpm']:>8.1f} "
                f"{telem['egt']:>8.1f} "
                f"{telem['cht']:>8.1f} "
                f"{telem['oil_temp']:>8.1f} "
                f"{'YES' if telem['fault_active'] else 'no':>6}"
            )
