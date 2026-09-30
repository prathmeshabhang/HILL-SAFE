"""
tools/verify_model_hashes.py
============================
Automated SHA-256 Immutability Verification for Frozen Scientific ML Models.
Verifies M2, M4, M6, and M7 binary artifacts bit-for-bit.
Exits with 0 if all hashes match exactly, or 1 if any hash has changed.
"""

import hashlib
import sys
from pathlib import Path

FROZEN_MODELS = {
    "M2": {
        "path": "ml/flood/m2_upper_beas_flood_model.joblib",
        "expected_sha256": "a3f349f6d10547ed1f378bf44f8240e840029f011c6afa0855f91fc7d7d9100b",
        "description": "Upper Beas Catchment Hydrological Runoff Model",
    },
    "M4": {
        "path": "data/satellite_output/flood_multimodal_unet.pt",
        "expected_sha256": "45aa1823c395e14ff99612019c728732f776c9c0a5f6f4f92e0ec25076ee7e07",
        "description": "Satellite Multi-Modal U-Net Flood Inundation Model",
    },
    "M6": {
        "path": "ml/landslide/m6_beas_susceptibility_rf.joblib",
        "expected_sha256": "e4f5f933668373cbedaa4968faeddc89822af123bc574fbca42817c02a4e627c",
        "description": "Beas Basin Landslide Susceptibility Random Forest",
    },
    "M7": {
        "path": "ml/landslide/m7_beas_trigger_lgbm.joblib",
        "expected_sha256": "f3b8e88d37013747d72a5ddb80bf230cf0e41d5f028944f1f127c981256c1b8a",
        "description": "Beas Basin Rainfall-Induced Landslide Trigger LightGBM",
    },
}

REPO_ROOT = Path(__file__).resolve().parent.parent


def verify_models() -> bool:
    all_passed = True
    print("=" * 70)
    print("FLOODY SHIELD — FROZEN MODEL SHA-256 IMMUTABILITY VERIFICATION")
    print("=" * 70)

    for model_id, spec in FROZEN_MODELS.items():
        file_path = REPO_ROOT / spec["path"]
        if not file_path.exists():
            print(f"[-] {model_id} FAIL: Artifact not found at {file_path}")
            all_passed = False
            continue

        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        actual_hash = hasher.hexdigest()

        if actual_hash == spec["expected_sha256"]:
            print(f"[+] {model_id} PASS: {spec['description']}")
            print(f"    SHA-256: {actual_hash}")
        else:
            print(f"[-] {model_id} FAIL: SHA-256 MISMATCH!")
            print(f"    Expected: {spec['expected_sha256']}")
            print(f"    Actual:   {actual_hash}")
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("ALL FROZEN ARTIFACTS BIT-IDENTICAL")
        return True
    else:
        print("CRITICAL ERROR: ONE OR MORE FROZEN ARTIFACTS HAVE CHANGED!")
        return False


if __name__ == "__main__":
    success = verify_models()
    sys.exit(0 if success else 1)
