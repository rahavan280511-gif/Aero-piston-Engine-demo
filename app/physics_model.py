"""
Physics / Expected-Behaviour Model for UAV Aero-Piston Engine.

This module provides a lightweight empirical model that predicts what the
engine's key thermal and mechanical parameters *should* be under normal,
healthy operating conditions given the current throttle setting, shaft
speed (RPM), and ambient temperature.

Design notes
------------
The equations are intentionally aligned with the simulator's true-state
equations (before noise and fault injection), so that residuals produced
by the Digital Twin Core are near-zero when the engine is healthy and
deviate measurably when a sensor fault or physical degradation is present.

An ambient-temperature correction is applied on top of the base equations
to account for the effect of intake air density on combustion temperature
and heat-transfer rates — a real (though simplified) physical effect.

This is a demonstration model; it is NOT a certified aero-engine model.
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Model coefficients  (kept in one place so they are easy to calibrate)
# ---------------------------------------------------------------------------

# --- Base engine map (must match simulator true-state equations) ---
_EGT_BASE = 400.0           # °C — EGT at idle / zero throttle reference
_EGT_THROTTLE_GAIN = 600.0  # °C per unit throttle
_EGT_RPM_GAIN = 0.05        # °C per RPM above idle reference
_RPM_IDLE_REF = 2000.0      # RPM idle reference (matching simulator)

_CHT_BASE = 120.0           # °C — CHT at idle
_CHT_EGT_COUPLING = 0.6     # °C CHT per °C EGT above base

_OIL_BASE = 80.0            # °C — oil temperature at idle
_OIL_EGT_COUPLING = 0.2     # °C oil per °C EGT above base

# --- Ambient-temperature correction ---
# Real piston engines run hotter in warm/high-density conditions because
# the fuel/air mixture is richer in oxygen, increasing combustion intensity.
# Correction is linear around a 25 °C ISA standard-day reference.
_AMBIENT_REF = 25.0         # °C — ISA standard-day reference temperature
_EGT_AMBIENT_GAIN = 0.8     # additional °C EGT per °C above ambient ref
_CHT_AMBIENT_GAIN = 0.5     # additional °C CHT per °C above ambient ref
_OIL_AMBIENT_GAIN = 0.15    # additional °C oil  per °C above ambient ref

# --- Physical sanity limits (output is clipped to these) ---
# Upper limits reflect realistic air-cooled UAV piston engine operating envelopes.
_EGT_MIN, _EGT_MAX = 350.0, 1200.0   # °C (max EGT before detonation risk)
_CHT_MIN, _CHT_MAX =  80.0,  600.0   # °C (max CHT for air-cooled cylinders)
_OIL_MIN, _OIL_MAX =  40.0,  200.0   # °C (max oil before viscosity breakdown)


# ---------------------------------------------------------------------------
# Output container
# ---------------------------------------------------------------------------

@dataclass
class ExpectedEngineState:
    """
    Predicted (expected) engine parameter values under healthy operation.

    Attributes
    ----------
    egt_expected : float
        Expected Exhaust Gas Temperature (°C).
    cht_expected : float
        Expected Cylinder Head Temperature (°C).
    oil_temp_expected : float
        Expected oil temperature (°C).
    rpm_input : float
        RPM value that was used as a model input (echoed for convenience).
    throttle_input : float
        Throttle value used as a model input (echoed for convenience).
    ambient_temp_input : float
        Ambient temperature used as a model input (echoed for convenience).
    """
    egt_expected: float
    cht_expected: float
    oil_temp_expected: float
    # ── inputs echoed for traceability ────────────────────────────────────
    rpm_input: float
    throttle_input: float
    ambient_temp_input: float

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation."""
        return {
            "egt_expected": round(self.egt_expected, 4),
            "cht_expected": round(self.cht_expected, 4),
            "oil_temp_expected": round(self.oil_temp_expected, 4),
            "rpm_input": round(self.rpm_input, 2),
            "throttle_input": round(self.throttle_input, 4),
            "ambient_temp_input": round(self.ambient_temp_input, 2),
        }


# ---------------------------------------------------------------------------
# Core prediction function
# ---------------------------------------------------------------------------

def predict_expected(
    rpm: float,
    throttle: float,
    ambient_temp: float = 25.0,
) -> ExpectedEngineState:
    """
    Predict expected engine parameter values under healthy, nominal operation.

    The model consists of two additive terms:

    1. **Base engine map** — linear functions of throttle and RPM, calibrated
       to match the simulator's true-state equations so that residuals in the
       Digital Twin Core are near-zero for a healthy, noise-free engine.

    2. **Ambient temperature correction** — small linear adjustment centred on
       the ISA standard-day reference (25 °C) to capture the effect of air
       density on combustion intensity and heat dissipation.

    Parameters
    ----------
    rpm : float
        Current measured (or estimated) engine speed in RPM.
    throttle : float
        Throttle position in the range [0.0, 1.0].
    ambient_temp : float, optional
        Ambient / outside air temperature in °C.  Defaults to 25 °C (ISA
        standard day).

    Returns
    -------
    ExpectedEngineState
        Dataclass holding predicted EGT, CHT, and oil temperature values,
        together with the echoed input values for full traceability.

    Notes
    -----
    Inputs are clamped before use so that out-of-range sensor readings do
    not produce nonsensical physics output.  The returned values are
    additionally clipped to physically plausible limits.

    Examples
    --------
    >>> state = predict_expected(rpm=3200, throttle=0.55)
    >>> state.egt_expected
    750.0  # approximate
    """
    # ── Input sanitisation ────────────────────────────────────────────────
    rpm = max(0.0, float(rpm))
    throttle = float(max(0.0, min(1.0, throttle)))
    ambient_temp = float(ambient_temp)

    # ── Ambient-temperature correction (delta from standard day) ──────────
    d_ambient = ambient_temp - _AMBIENT_REF   # negative means cooler than std

    # ── EGT prediction ────────────────────────────────────────────────────
    egt_base = (
        _EGT_BASE
        + _EGT_THROTTLE_GAIN * throttle
        + _EGT_RPM_GAIN * (rpm - _RPM_IDLE_REF)
    )
    egt_expected = egt_base + _EGT_AMBIENT_GAIN * d_ambient
    egt_expected = float(max(_EGT_MIN, min(_EGT_MAX, egt_expected)))

    # ── CHT prediction ────────────────────────────────────────────────────
    # Derived from EGT via thermal coupling; ambient separately adjusts
    # the cylinder cooling efficiency.
    cht_base = _CHT_BASE + _CHT_EGT_COUPLING * (egt_base - _EGT_BASE)
    cht_expected = cht_base + _CHT_AMBIENT_GAIN * d_ambient
    cht_expected = float(max(_CHT_MIN, min(_CHT_MAX, cht_expected)))

    # ── Oil temperature prediction ────────────────────────────────────────
    oil_base = _OIL_BASE + _OIL_EGT_COUPLING * (egt_base - _EGT_BASE)
    oil_temp_expected = oil_base + _OIL_AMBIENT_GAIN * d_ambient
    oil_temp_expected = float(max(_OIL_MIN, min(_OIL_MAX, oil_temp_expected)))

    return ExpectedEngineState(
        egt_expected=egt_expected,
        cht_expected=cht_expected,
        oil_temp_expected=oil_temp_expected,
        rpm_input=rpm,
        throttle_input=throttle,
        ambient_temp_input=ambient_temp,
    )


# ---------------------------------------------------------------------------
# EnginePhysicsModel — thin OOP wrapper (for DI / future extension)
# ---------------------------------------------------------------------------

class EnginePhysicsModel:
    """
    Object-oriented wrapper around :func:`predict_expected`.

    Provides a stable interface for the Digital Twin Core to call, and a
    natural extension point for future model updates (e.g. degradation
    maps, altitude corrections, fuel-type variants).

    Parameters
    ----------
    ambient_temp : float
        Default ambient temperature in °C used when no override is supplied.
    """

    def __init__(self, ambient_temp: float = 25.0) -> None:
        self.ambient_temp = ambient_temp

    def predict(
        self,
        rpm: float,
        throttle: float,
        ambient_temp: float | None = None,
    ) -> ExpectedEngineState:
        """
        Return expected engine state for the given operating point.

        Parameters
        ----------
        rpm : float
            Engine speed (RPM).
        throttle : float
            Throttle position [0.0 – 1.0].
        ambient_temp : float | None
            Ambient temperature override (°C).  Uses instance default when
            ``None``.
        """
        t_amb = self.ambient_temp if ambient_temp is None else float(ambient_temp)
        return predict_expected(rpm=rpm, throttle=throttle, ambient_temp=t_amb)


# ---------------------------------------------------------------------------
# Quick self-test  (run: python -m app.physics_model)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("EnginePhysicsModel — sweep over throttle at ISA standard day\n")
    model = EnginePhysicsModel(ambient_temp=25.0)

    print(f"{'throttle':>10} {'rpm':>8} {'EGT_exp':>10} {'CHT_exp':>10} {'OIL_exp':>10}")
    print("-" * 52)

    for thr in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        rpm_nominal = 2000 + 2500 * thr
        s = model.predict(rpm=rpm_nominal, throttle=thr)
        print(
            f"{thr:>10.2f} {rpm_nominal:>8.0f} "
            f"{s.egt_expected:>10.1f} {s.cht_expected:>10.1f} {s.oil_temp_expected:>10.1f}"
        )

    print("\nAmbient-temperature effect on EGT (throttle=0.6, rpm=3500)\n")
    print(f"{'ambient °C':>12} {'EGT_exp':>10} {'CHT_exp':>10}")
    print("-" * 36)
    for t_amb in [0, 10, 20, 25, 30, 40, 50]:
        s = predict_expected(rpm=3500, throttle=0.6, ambient_temp=t_amb)
        print(f"{t_amb:>12.0f} {s.egt_expected:>10.1f} {s.cht_expected:>10.1f}")
