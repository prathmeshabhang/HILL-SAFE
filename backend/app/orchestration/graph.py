"""
backend/app/orchestration/graph.py
==================================
Multi-hazard dependency graph topology for FLOODY SHIELD v3.3.
Defines explicit dependency relations, hard vs soft constraints, and scientific evidence status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from backend.app.orchestration.state import DependencyType


@dataclass
class ModelNodeDef:
    model_id: str
    model_name: str
    adapter_key: str
    evidence_status: str
    dependencies: Dict[str, DependencyType] = field(default_factory=dict)
    is_root: bool = False


# True scientific dependency graph of FLOODY SHIELD
MODEL_GRAPH: Dict[str, ModelNodeDef] = {
    # --- Atmospheric Nowcasting Branch ---
    "M1": ModelNodeDef(
        model_id="M1",
        model_name="Atmospheric Nowcasting Trajectory Engine",
        adapter_key="M1",
        evidence_status="FUNCTIONAL_PROTOTYPE",
        dependencies={},
        is_root=True,
    ),

    # --- Flash Flood Branch ---
    "M2": ModelNodeDef(
        model_id="M2",
        model_name="Upper Beas Flash Flood Risk XGBoost",
        adapter_key="M2",
        evidence_status="VALIDATED_ARTIFACT",
        dependencies={"M1": DependencyType.SOFT},
    ),
    "M4": ModelNodeDef(
        model_id="M4",
        model_name="Multimodal Flood Segmentation 9-Ch U-Net",
        adapter_key="M4",
        evidence_status="PROXY_VALIDATED_PROTOTYPE",
        dependencies={"M2": DependencyType.OPTIONAL},
    ),

    # --- Landslide Branch ---
    "M6": ModelNodeDef(
        model_id="M6",
        model_name="Landslide Susceptibility Random Forest",
        adapter_key="M6",
        evidence_status="VALIDATED_ARTIFACT",
        dependencies={},
        is_root=True,
    ),
    "PWP_SSI": ModelNodeDef(
        model_id="PWP_SSI",
        model_name="Transient Pore-Water Pressure & Infinite Slope Stability",
        adapter_key="PWP_SSI",
        evidence_status="PHYSICS_PROOF_OF_CONCEPT",
        dependencies={},
        is_root=True,
    ),
    "M7": ModelNodeDef(
        model_id="M7",
        model_name="Dynamic Landslide Rainfall Trigger LightGBM",
        adapter_key="M7",
        evidence_status="VALIDATED_ARTIFACT",
        dependencies={"M6": DependencyType.HARD, "PWP_SSI": DependencyType.SOFT},
    ),
    "M8": ModelNodeDef(
        model_id="M8",
        model_name="InSAR/GNSS Ground Deformation Kinematics",
        adapter_key="M8",
        evidence_status="SIMULATION_PROTOTYPE",
        dependencies={"M7": DependencyType.SOFT},
    ),

    # --- River Hydrology Branch ---
    "M10": ModelNodeDef(
        model_id="M10",
        model_name="River Water-Level 1-6h Forecast",
        adapter_key="M10",
        evidence_status="FUNCTIONAL_PROTOTYPE",
        dependencies={"M1": DependencyType.SOFT},
        is_root=True,
    ),
    "M11": ModelNodeDef(
        model_id="M11",
        model_name="Hydrodynamic Inundation & Wave Propagation",
        adapter_key="M11",
        evidence_status="PHYSICS_ENGINE",
        dependencies={"M10": DependencyType.HARD},
    ),
    "M19": ModelNodeDef(
        model_id="M19",
        model_name="Hydrodynamic Time-to-Impact Wave Celerity",
        adapter_key="M19",
        evidence_status="HYDRODYNAMIC_KINEMATICS",
        dependencies={"M11": DependencyType.SOFT},
    ),

    # --- Multi-Hazard Cascade ---
    "M12": ModelNodeDef(
        model_id="M12",
        model_name="Compound Landslide Dam Breach & Outburst Cascade",
        adapter_key="M12",
        evidence_status="EMPIRICALLY_BENCHMARKED",
        dependencies={"M2": DependencyType.SOFT, "M7": DependencyType.SOFT},
    ),

    # --- Impact Assessment ---
    "M13": ModelNodeDef(
        model_id="M13",
        model_name="Settlement Population Social Vulnerability",
        adapter_key="M13",
        evidence_status="EMPIRICAL_GIS_ENGINE",
        dependencies={"M2": DependencyType.SOFT, "M12": DependencyType.SOFT},
    ),
    "M14": ModelNodeDef(
        model_id="M14",
        model_name="Critical Infrastructure Hazus Damage Loss",
        adapter_key="M14",
        evidence_status="EMPIRICAL_VULNERABILITY_ENGINE",
        dependencies={"M2": DependencyType.SOFT, "M12": DependencyType.SOFT},
    ),

    # --- Safe-Zone & Evacuation Routing ---
    "M15": ModelNodeDef(
        model_id="M15",
        model_name="Safe-Zone Multi-Criteria Shelter Selection",
        adapter_key="M15",
        evidence_status="SPATIAL_RULE_ENGINE",
        dependencies={"M2": DependencyType.SOFT, "M13": DependencyType.SOFT},
    ),
    "M16": ModelNodeDef(
        model_id="M16",
        model_name="Hazard-Weighted Evacuation Routing Network",
        adapter_key="M16",
        evidence_status="GRAPH_OPTIMIZATION_ENGINE",
        dependencies={"M15": DependencyType.HARD, "M14": DependencyType.SOFT},
    ),

    # --- Warning Gating & Calibration ---
    "M17": ModelNodeDef(
        model_id="M17",
        model_name="Cost-Sensitive Life-Safety Warning Gating",
        adapter_key="M17",
        evidence_status="COST_SENSITIVE_DECISION_GATE",
        dependencies={"M12": DependencyType.SOFT, "M13": DependencyType.SOFT, "M16": DependencyType.SOFT},
    ),
    "M18": ModelNodeDef(
        model_id="M18",
        model_name="Isotonic Risk Probability Calibration",
        adapter_key="M18",
        evidence_status="STATISTICAL_CALIBRATION",
        dependencies={"M17": DependencyType.HARD},
    ),
}
