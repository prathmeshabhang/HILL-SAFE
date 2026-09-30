"""
ml/anomaly/m9_sensor/model.py
=============================
Production Model M9: Dual-Stage Hybrid IoT Sensor Anomaly Detector.
Integrates Deterministic Physics, Rolling Statistics, and Multivariate Isolation Forest.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from ml.anomaly.m9_sensor.rules import DeterministicRulesEngine
from ml.anomaly.m9_sensor.schema import (
    M9InputFeatures,
    M9PredictionOutput,
    SensorAnomalyType,
    SensorStatus,
)
from ml.anomaly.m9_sensor.statistical import StatisticalFilterEngine

MODEL_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = MODEL_DIR / "m9_isolation_forest.joblib"


class M9SensorAnomalyModel:
    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self.rules_engine = DeterministicRulesEngine()
        self.stat_engine = StatisticalFilterEngine()
        self.feature_names = [
            "rainfall_rate_mmh",
            "water_level_m",
            "soil_moisture_pct",
            "tilt_deg",
            "pore_pressure_kpa",
        ]
        self.iso_forest: Optional[IsolationForest] = None
        self._load_model()

    def _load_model(self) -> None:
        if self.model_path.exists():
            try:
                self.iso_forest = joblib.load(self.model_path)
            except Exception as e:
                print(f"[M9Model] Warning loading model: {e}")
                self.iso_forest = None

    def fit(self, X_nominal: np.ndarray, save: bool = True) -> None:
        """Fits unsupervised Isolation Forest on nominal catchment telemetry."""
        self.iso_forest = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
        )
        self.iso_forest.fit(X_nominal)
        if save:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.iso_forest, self.model_path)

    def predict(
        self,
        features: Dict[str, Any],
        recent_history: Optional[Sequence[Dict[str, float]]] = None,
    ) -> Dict[str, Any]:
        """
        Universal FLOODY SHIELD prediction interface.
        Evaluates Stage 1 (Rules), Stage 2 (Stats), and Stage 3 (Isolation Forest).
        """
        flags: List[str] = []

        # 1. Stage 1: Deterministic Physics Check
        is_rule_anom, rule_type, rule_flags, rec_action = self.rules_engine.evaluate(features, recent_history)
        if is_rule_anom:
            out = M9PredictionOutput(
                sensor_status=SensorStatus.FAULTY,
                anomaly_score=1.0,
                anomaly_type=rule_type,
                is_valid_reading=False,
                recommended_action=rec_action,
                confidence=0.99,
                uncertainty={"interval": [0.95, 1.0], "method": "deterministic_bounds"},
                data_quality=0.0,
                model_version="M9-hybrid-v1.0",
                applicability="IN_AOI",
                flags=rule_flags,
            )
            return out.to_dict()

        # 2. Stage 2: Cross-Sensor Physical Consistency
        is_inconsistent, inc_msg = self.stat_engine.check_cross_sensor_consistency(features, recent_history)
        if is_inconsistent and inc_msg:
            flags.append(inc_msg)
            out = M9PredictionOutput(
                sensor_status=SensorStatus.ANOMALOUS,
                anomaly_score=0.85,
                anomaly_type=SensorAnomalyType.CROSS_SENSOR_INCONSISTENCY,
                is_valid_reading=False,
                recommended_action="CROSS_VERIFY_ADJACENT_STATIONS",
                confidence=0.85,
                uncertainty={"interval": [0.75, 0.95], "method": "heuristic_consistency"},
                data_quality=0.30,
                model_version="M9-hybrid-v1.0",
                applicability="IN_AOI",
                flags=flags,
            )
            return out.to_dict()

        # 2b. Safeguard: Authentic Multi-Hazard Storm Surge Check
        if self.stat_engine.is_authentic_storm_surge(features):
            out = M9PredictionOutput(
                sensor_status=SensorStatus.NORMAL,
                anomaly_score=0.05,
                anomaly_type=SensorAnomalyType.NONE,
                is_valid_reading=True,
                recommended_action="AUTHENTIC_STORM_SURGE_PRESERVED",
                confidence=0.96,
                uncertainty={"interval": [0.0, 0.10], "method": "multi_hazard_consistency"},
                data_quality=0.95,
                model_version="M9-hybrid-v1.0",
                applicability="IN_AOI",
                flags=["AUTHENTIC_SEVERE_STORM_CORRELATION"],
            )
            return out.to_dict()

        # 3. Stage 3: Multivariate Isolation Forest
        vec = [float(features.get(f, 0.0)) for f in self.feature_names]
        iso_score = 0.0
        is_ml_anom = False
        if self.iso_forest is not None:
            decision = float(self.iso_forest.decision_function([vec])[0])
            is_ml_anom = bool(self.iso_forest.predict([vec])[0] == -1)
            if is_ml_anom:
                iso_score = float(np.clip(0.55 + abs(decision) * 2.0, 0.55, 0.98))
            else:
                iso_score = float(np.clip(0.15 - (decision * 1.5), 0.02, 0.25))
        else:
            # Baseline heuristic score
            iso_score = 0.05
            is_ml_anom = False

        status = SensorStatus.ANOMALOUS if is_ml_anom else SensorStatus.NORMAL
        anom_type = SensorAnomalyType.MULTIVARIATE_DRIFT if is_ml_anom else SensorAnomalyType.NONE
        action = "INVESTIGATE_MULTIVARIATE_DRIFT" if is_ml_anom else "MAINTAIN_NORMAL_STREAM"

        out = M9PredictionOutput(
            sensor_status=status,
            anomaly_score=iso_score,
            anomaly_type=anom_type,
            is_valid_reading=not is_ml_anom,
            recommended_action=action,
            confidence=round(1.0 - iso_score * 0.4, 4) if not is_ml_anom else round(iso_score, 4),
            uncertainty={"interval": [max(0.0, iso_score - 0.1), min(1.0, iso_score + 0.1)], "method": "isolation_distance"},
            data_quality=round(1.0 - iso_score, 4),
            model_version="M9-hybrid-v1.0",
            applicability="IN_AOI",
            flags=flags,
        )
        return out.to_dict()
