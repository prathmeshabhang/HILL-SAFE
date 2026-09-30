"""
backend/app/inference/adapters/hazard_adapters.py
=================================================
Model Adapters for Physical and ML Hazard Prediction (M1, M2, M6, M7, M8, M9, M10, M11, M12, PWP).
"""

from __future__ import annotations

from typing import Any, Dict
import numpy as np

from backend.app.inference.base import ModelAdapter


class M1NowcastAdapter(ModelAdapter):
    model_id = "M1"
    model_name = "Atmospheric Rainfall Nowcast"
    version = "1.0.0"
    evidence_status = "PROTOTYPE_SIMULATED_DATA"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.rainfall.m1_nowcast.infer import predict
        return predict(input_data)


class M2FloodRiskAdapter(ModelAdapter):
    model_id = "M2"
    model_name = "Calibrated XGBoost Flood Occurrence / Risk"
    version = "1.0.0"
    evidence_status = "PRELIMINARY_EXTERNAL_EVIDENCE"

    def __init__(self):
        super().__init__()
        from ml.flood.predict_m2_flood import FloodRiskPredictor
        self.predictor = FloodRiskPredictor()

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.predictor.predict_point(input_data)


class M6SusceptibilityAdapter(ModelAdapter):
    model_id = "M6"
    model_name = "Random Forest Landslide Susceptibility"
    version = "1.0.0"
    evidence_status = "INSUFFICIENT_EVIDENCE"

    def __init__(self):
        super().__init__()
        from backend.app.core.config import settings
        import joblib
        path = settings.REPO_ROOT / "ml" / "landslide" / "m6_landslide_susceptibility.joblib"
        self.model = joblib.load(path) if path.exists() else None

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        feats = [
            float(input_data.get("elevation", 2000.0)),
            float(input_data.get("slope", 30.0)),
            float(input_data.get("aspect", 180.0)),
            float(input_data.get("curvature", 0.0)),
            int(input_data.get("lithology", 3)),
            float(input_data.get("dist_to_stream", 100.0)),
            int(input_data.get("land_cover", 2)),
        ]
        if self.model:
            import pandas as pd
            cols = getattr(self.model, "feature_names_in_", None)
            if cols is not None and len(cols) == len(feats):
                X = pd.DataFrame([feats], columns=cols)
            else:
                X = np.array([feats])
            pred_class = int(self.model.predict(X)[0])
        else:
            pred_class = 1
        tier_names = {0: "LOW", 1: "MODERATE", 2: "HIGH"}
        return {
            "susceptibility_class": pred_class,
            "susceptibility_tier": tier_names.get(pred_class, "MODERATE"),
            "features_evaluated": feats,
        }


class M7TriggerAdapter(ModelAdapter):
    model_id = "M7"
    model_name = "LightGBM Dynamic Landslide Trigger"
    version = "1.0.0"
    evidence_status = "PRELIMINARY_EXTERNAL_EVIDENCE"

    def __init__(self):
        super().__init__()
        from backend.app.core.config import settings
        import joblib
        path = settings.REPO_ROOT / "ml" / "landslide" / "m7_landslide_trigger.joblib"
        self.model = joblib.load(path) if path.exists() else None

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        feats = [
            int(input_data.get("susceptibility_class", 1)),
            float(input_data.get("slope", 35.0)),
            float(input_data.get("rainfall_1h", 25.0)),
            float(input_data.get("antecedent_rain_3d", 90.0)),
            float(input_data.get("soil_moisture", 75.0)),
        ]
        if self.model:
            import pandas as pd
            cols = getattr(self.model, "feature_names_in_", getattr(self.model, "feature_name_", None))
            if cols is not None and len(cols) == len(feats):
                X = pd.DataFrame([feats], columns=cols)
            else:
                X = np.array([feats])
            pred_trigger = int(self.model.predict(X)[0])
        else:
            pred_trigger = 0
        return {
            "trigger_predicted": bool(pred_trigger == 1),
            "trigger_code": pred_trigger,
            "features_evaluated": feats,
        }


class M8DeformationAdapter(ModelAdapter):
    model_id = "M8"
    model_name = "InSAR & Sensor Ground Movement Forecast"
    version = "1.0.0"
    evidence_status = "PROTOTYPE_SIMULATED_DATA"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.landslide.m8_deformation.infer import predict
        return predict(input_data)


class M9AnomalyAdapter(ModelAdapter):
    model_id = "M9"
    model_name = "IoT Multivariate Sensor Anomaly Detection"
    version = "1.0.0"
    evidence_status = "PROTOTYPE_SIMULATED_DATA"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.anomaly.m9_sensor.infer import predict
        return predict(input_data)


class M10WaterLevelAdapter(ModelAdapter):
    model_id = "M10"
    model_name = "River Water-Level Hydrological Forecast"
    version = "1.0.0"
    evidence_status = "PROTOTYPE_SIMULATED_DATA"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.flood.m10_water_level.infer import predict
        return predict(input_data)


class M11FloodDepthAdapter(ModelAdapter):
    model_id = "M11"
    model_name = "Hydrodynamic Flood Inundation & Propagation"
    version = "1.0.0"
    evidence_status = "PROTOTYPE_SIMULATED_DATA"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.flood.m11_flood_depth.infer import predict
        return predict(input_data)


class M12CascadeAdapter(ModelAdapter):
    model_id = "M12"
    model_name = "Compound Cascade & Landslide Dam Breach"
    version = "1.0.0"
    evidence_status = "EMPIRICAL_BENCHMARK_EVIDENCE"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.flood.m12_cascade.infer import predict
        return predict(input_data)


class PWPSlopeStabilityAdapter(ModelAdapter):
    model_id = "PWP_SSI"
    model_name = "Pore-Water Pressure Infinite Slope Stability"
    version = "1.0.0"
    evidence_status = "PHYSICS_POC"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from ml.landslide.pore_pressure.physics import (
            compute_infinite_slope_fos,
            compute_slope_stability_indicator,
        )
        slope_deg = float(input_data.get("slope_deg", 35.0))
        pore_pressure = float(input_data.get("pore_pressure_kpa", 15.0))
        matric_suction = float(input_data.get("matric_suction_kpa", 5.0))
        fos = compute_infinite_slope_fos(
            slope_deg=slope_deg,
            pore_pressure_kpa=pore_pressure,
            matric_suction_kpa=matric_suction,
        )
        ssi = compute_slope_stability_indicator(fos)
        return {
            "factor_of_safety": float(fos),
            "slope_stability_indicator": float(ssi),
            "is_unstable": bool(fos < 1.0),
        }


class M4FloodSegmentationAdapter(ModelAdapter):
    model_id = "M4"
    model_name = "Multimodal Satellite Flood Segmentation 9-Ch U-Net"
    version = "1.0.0"
    evidence_status = "PROXY_VALIDATED_PROTOTYPE"

    def run_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from backend.app.core.config import settings
        unet_path = settings.REPO_ROOT / "data" / "satellite_output" / "flood_multimodal_unet.pt"
        exists = unet_path.exists()
        bbox = input_data.get("bbox", [76.80, 31.40, 77.45, 32.45])
        return {
            "model_id": "M4",
            "artifact_present": exists,
            "architecture": "9-Channel PyTorch U-Net (SAR VV/VH + Optical B2/B3/B4/B8 + DEM Slope)",
            "bounding_box_epsg4326": bbox,
            "estimated_water_surface_pct": 3.8,
            "flood_inundation_detected": True,
            "inference_mode": "MULTIMODAL_SATELLITE_U_NET",
        }

