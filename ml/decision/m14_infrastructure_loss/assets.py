"""
ml/decision/m14_infrastructure_loss/assets.py
=============================================
Authoritative infrastructure asset register for the Upper Beas corridor (Kullu–Manali).
"""

from __future__ import annotations

from typing import Dict
from ml.decision.m14_infrastructure_loss.schema import AssetCategory, InfrastructureAsset


BEAS_INFRASTRUCTURE_ASSETS: Dict[str, InfrastructureAsset] = {
    # Highway Segments
    "NH3_AUT_GORGE": InfrastructureAsset(
        asset_id="NH3_AUT_GORGE",
        name="NH-3 Aut Gorge Highway Section (Km 210-218)",
        category=AssetCategory.TRANSPORTATION_ROAD,
        replacement_value_lakhs_inr=3500.0,
        critical_elevation_m=915.0,
        soffit_or_deck_height_m=0.5,
        lat=31.7480,
        lon=77.2080,
        reach_name="Aut_Gorge",
        criticality_tier=1,
    ),
    "NH3_THALOUT_PANDOH": InfrastructureAsset(
        asset_id="NH3_THALOUT_PANDOH",
        name="NH-3 Thalout to Pandoh Dam Riverbank Highway",
        category=AssetCategory.TRANSPORTATION_ROAD,
        replacement_value_lakhs_inr=4200.0,
        critical_elevation_m=905.0,
        soffit_or_deck_height_m=0.6,
        lat=31.7100,
        lon=77.1800,
        reach_name="Pandoh_Reservoir",
        criticality_tier=1,
    ),
    "NH3_MANALI_BYPASS": InfrastructureAsset(
        asset_id="NH3_MANALI_BYPASS",
        name="Manali Right Bank Arterial Bypass (Bahang to Aleo)",
        category=AssetCategory.TRANSPORTATION_ROAD,
        replacement_value_lakhs_inr=2200.0,
        critical_elevation_m=2040.0,
        soffit_or_deck_height_m=0.8,
        lat=32.2450,
        lon=77.1880,
        reach_name="Upper_Manali",
        criticality_tier=1,
    ),

    # Bridges
    "BR_AUT_SUSPENSION": InfrastructureAsset(
        asset_id="BR_AUT_SUSPENSION",
        name="Aut Beas Suspension Bridge",
        category=AssetCategory.TRANSPORTATION_BRIDGE,
        replacement_value_lakhs_inr=1800.0,
        critical_elevation_m=916.0,
        soffit_or_deck_height_m=4.5,
        lat=31.7483,
        lon=77.2081,
        reach_name="Aut_Gorge",
        criticality_tier=1,
    ),
    "BR_LARJI_INTAKE": InfrastructureAsset(
        asset_id="BR_LARJI_INTAKE",
        name="Larji Hydel Project Access Bridge",
        category=AssetCategory.TRANSPORTATION_BRIDGE,
        replacement_value_lakhs_inr=1250.0,
        critical_elevation_m=962.0,
        soffit_or_deck_height_m=3.8,
        lat=31.7167,
        lon=77.2167,
        reach_name="Larji_Confluence",
        criticality_tier=2,
    ),
    "BR_BHUNTAR_CONFLUENCE": InfrastructureAsset(
        asset_id="BR_BHUNTAR_CONFLUENCE",
        name="Bhuntar Parbati-Beas Confluence Bridge",
        category=AssetCategory.TRANSPORTATION_BRIDGE,
        replacement_value_lakhs_inr=2600.0,
        critical_elevation_m=1092.0,
        soffit_or_deck_height_m=5.2,
        lat=31.8789,
        lon=77.1554,
        reach_name="Bhuntar_Confluence",
        criticality_tier=1,
    ),
    "BR_AKHARA_KULLU": InfrastructureAsset(
        asset_id="BR_AKHARA_KULLU",
        name="Akhara Bazar Kullu Foot & Vehicle Bridge",
        category=AssetCategory.TRANSPORTATION_BRIDGE,
        replacement_value_lakhs_inr=1400.0,
        critical_elevation_m=1222.0,
        soffit_or_deck_height_m=4.0,
        lat=31.9600,
        lon=77.1120,
        reach_name="Kullu_Urban",
        criticality_tier=1,
    ),
    "BR_PALCHAN_BAILEY": InfrastructureAsset(
        asset_id="BR_PALCHAN_BAILEY",
        name="Palchan Solang-Rohtang Link Bailey Bridge",
        category=AssetCategory.TRANSPORTATION_BRIDGE,
        replacement_value_lakhs_inr=650.0,
        critical_elevation_m=2210.0,
        soffit_or_deck_height_m=3.2,
        lat=32.3080,
        lon=77.1760,
        reach_name="Upper_Manali",
        criticality_tier=1,
    ),

    # Power Sub-stations
    "SUB_LARJI_HYDEL": InfrastructureAsset(
        asset_id="SUB_LARJI_HYDEL",
        name="HPSEB Larji 126MW Hydro Generating Substation",
        category=AssetCategory.POWER_SUBSTATION,
        replacement_value_lakhs_inr=8500.0,
        critical_elevation_m=963.0,
        soffit_or_deck_height_m=1.5,
        lat=31.7150,
        lon=77.2180,
        reach_name="Larji_Confluence",
        criticality_tier=1,
    ),
    "SUB_BHUNTAR_GRID": InfrastructureAsset(
        asset_id="SUB_BHUNTAR_GRID",
        name="Bhuntar 66kV Electrical Distribution Grid",
        category=AssetCategory.POWER_SUBSTATION,
        replacement_value_lakhs_inr=2400.0,
        critical_elevation_m=1093.0,
        soffit_or_deck_height_m=1.2,
        lat=31.8750,
        lon=77.1580,
        reach_name="Bhuntar_Confluence",
        criticality_tier=1,
    ),

    # Healthcare Hospitals
    "HOSP_KULLU_REGIONAL": InfrastructureAsset(
        asset_id="HOSP_KULLU_REGIONAL",
        name="Kullu Regional Civil & Trauma Hospital (Dhalpur)",
        category=AssetCategory.HEALTHCARE_HOSPITAL,
        replacement_value_lakhs_inr=9800.0,
        critical_elevation_m=1225.0,
        soffit_or_deck_height_m=1.8,
        lat=31.9560,
        lon=77.1080,
        reach_name="Kullu_Urban",
        criticality_tier=1,
    ),
    "HOSP_MANALI_CIVIL": InfrastructureAsset(
        asset_id="HOSP_MANALI_CIVIL",
        name="Manali Civil Hospital (Left Bank Link)",
        category=AssetCategory.HEALTHCARE_HOSPITAL,
        replacement_value_lakhs_inr=4500.0,
        critical_elevation_m=2048.0,
        soffit_or_deck_height_m=1.5,
        lat=32.2420,
        lon=77.1850,
        reach_name="Upper_Manali",
        criticality_tier=1,
    ),

    # Water Treatment & Pumping
    "WTR_PATLIKUHAL_INTAKE": InfrastructureAsset(
        asset_id="WTR_PATLIKUHAL_INTAKE",
        name="JSV Beas River Water Intake & Treatment Works",
        category=AssetCategory.WATER_INTAKE,
        replacement_value_lakhs_inr=1100.0,
        critical_elevation_m=1522.0,
        soffit_or_deck_height_m=0.8,
        lat=32.1260,
        lon=77.1490,
        reach_name="Mid_Valley",
        criticality_tier=2,
    ),

    # Agriculture & Commercial Orchards
    "AGR_PATLIKUHAL_ORCHARDS": InfrastructureAsset(
        asset_id="AGR_PATLIKUHAL_ORCHARDS",
        name="Patli Kuhal Floodplain Commercial Apple Orchards",
        category=AssetCategory.AGRICULTURE_ORCHARD,
        replacement_value_lakhs_inr=1500.0,
        critical_elevation_m=1521.0,
        soffit_or_deck_height_m=0.0,
        lat=32.1300,
        lon=77.1450,
        reach_name="Mid_Valley",
        criticality_tier=3,
    ),
}


def get_asset_or_default(asset_id: str) -> InfrastructureAsset:
    norm = asset_id.upper().strip()
    if norm in BEAS_INFRASTRUCTURE_ASSETS:
        return BEAS_INFRASTRUCTURE_ASSETS[norm]
    
    return InfrastructureAsset(
        asset_id=asset_id,
        name=f"Generic_Asset_{asset_id}",
        category=AssetCategory.TRANSPORTATION_ROAD,
        replacement_value_lakhs_inr=1000.0,
        critical_elevation_m=1200.0,
        soffit_or_deck_height_m=1.0,
        lat=32.0,
        lon=77.15,
        reach_name="General_Reach",
        criticality_tier=2,
    )
