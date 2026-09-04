"""
Synthetic Fault Classification Dataset Generator.

Generates data/fault_classification.csv containing 3,000 synthetic samples
across three fault classes:
  - NORMAL (1000 samples)
  - OVERHEATING (1000 samples)
  - LUBRICATION_ISSUE (1000 samples)

Physics-consistent features:
  [rpm, throttle, egt, cht, oil_temp, egt_residual, cht_residual, label]
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.physics_model import EnginePhysicsModel


def generate_fault_dataset(
    n_samples_per_class: int = 1000,
    seed: int = 42,
    output_csv: Path | str = PROJECT_ROOT / "data" / "fault_classification.csv",
) -> pd.DataFrame:
    """Generate synthetic telemetry dataset for fault classification."""
    np.random.seed(seed)
    physics = EnginePhysicsModel(ambient_temp=25.0)

    records = []

    # ── 1. NORMAL (1000 samples) ─────────────────────────────────────────
    for _ in range(n_samples_per_class):
        throttle = float(np.random.uniform(0.3, 0.95))
        rpm = float(2000.0 + throttle * 2500.0 + np.random.normal(0, 30.0))
        rpm = float(np.clip(rpm, 2000.0, 6200.0))

        expected = physics.predict(rpm=rpm, throttle=throttle, ambient_temp=25.0)

        # Measured telemetry near expected
        egt_meas = expected.egt_expected + float(np.random.normal(0.0, 3.0))
        cht_meas = expected.cht_expected + float(np.random.normal(0.0, 2.0))
        oil_meas = expected.oil_temp_expected + float(np.random.normal(0.0, 1.5))

        egt_res = egt_meas - expected.egt_expected
        cht_res = cht_meas - expected.cht_expected

        records.append({
            "rpm": round(rpm, 2),
            "throttle": round(throttle, 4),
            "egt": round(egt_meas, 2),
            "cht": round(cht_meas, 2),
            "oil_temp": round(oil_meas, 2),
            "egt_residual": round(egt_res, 2),
            "cht_residual": round(cht_res, 2),
            "label": "NORMAL",
        })

    # ── 2. OVERHEATING (1000 samples) ────────────────────────────────────
    for _ in range(n_samples_per_class):
        throttle = float(np.random.uniform(0.4, 0.95))
        rpm = float(2000.0 + throttle * 2500.0 + np.random.normal(0, 30.0))
        rpm = float(np.clip(rpm, 2000.0, 6200.0))

        expected = physics.predict(rpm=rpm, throttle=throttle, ambient_temp=25.0)

        # Severe EGT & CHT thermal bias
        egt_bias = float(np.random.uniform(22.0, 48.0))
        cht_bias = float(np.random.uniform(12.0, 28.0))

        egt_meas = expected.egt_expected + egt_bias + float(np.random.normal(0.0, 3.0))
        cht_meas = expected.cht_expected + cht_bias + float(np.random.normal(0.0, 2.0))
        oil_meas = expected.oil_temp_expected + float(np.random.normal(3.0, 2.0))

        egt_res = egt_meas - expected.egt_expected
        cht_res = cht_meas - expected.cht_expected

        records.append({
            "rpm": round(rpm, 2),
            "throttle": round(throttle, 4),
            "egt": round(egt_meas, 2),
            "cht": round(cht_meas, 2),
            "oil_temp": round(oil_meas, 2),
            "egt_residual": round(egt_res, 2),
            "cht_residual": round(cht_res, 2),
            "label": "OVERHEATING",
        })

    # ── 3. LUBRICATION_ISSUE (1000 samples) ──────────────────────────────
    for _ in range(n_samples_per_class):
        throttle = float(np.random.uniform(0.35, 0.9))
        rpm = float(2000.0 + throttle * 2500.0 + np.random.normal(0, 30.0))
        rpm = float(np.clip(rpm, 2000.0, 6200.0))

        expected = physics.predict(rpm=rpm, throttle=throttle, ambient_temp=25.0)

        # Primary oil temperature bias + mild CHT thermal friction
        oil_bias = float(np.random.uniform(15.0, 32.0))
        cht_bias = float(np.random.uniform(4.0, 10.0))

        egt_meas = expected.egt_expected + float(np.random.normal(2.0, 3.0))
        cht_meas = expected.cht_expected + cht_bias + float(np.random.normal(0.0, 2.0))
        oil_meas = expected.oil_temp_expected + oil_bias + float(np.random.normal(0.0, 1.5))

        egt_res = egt_meas - expected.egt_expected
        cht_res = cht_meas - expected.cht_expected

        records.append({
            "rpm": round(rpm, 2),
            "throttle": round(throttle, 4),
            "egt": round(egt_meas, 2),
            "cht": round(cht_meas, 2),
            "oil_temp": round(oil_meas, 2),
            "egt_residual": round(egt_res, 2),
            "cht_residual": round(cht_res, 2),
            "label": "LUBRICATION_ISSUE",
        })

    df = pd.DataFrame(records)
    # Shuffle dataset
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    out_path = Path(output_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"[OK] Generated {len(df)} samples into {out_path}")
    print("Class distribution:\n", df["label"].value_counts())
    return df


if __name__ == "__main__":
    generate_fault_dataset()
