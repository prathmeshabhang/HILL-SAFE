"""
tests/test_stations_management.py
=================================
Automated verification tests for adding, listing, and deleting physical
telemetry stations in HILL-SAFE (Upper Beas Catchment).
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_station_lifecycle_add_list_delete():
    # 1. Register a new station in Upper Beas Basin
    station_payload = {
        "station_id": "STN_TEST_MANALI_VALLEY_01",
        "name": "Manali Valley Hydrology Test Rig",
        "station_type": "MET_HYDRO_IOT",
        "latitude": 32.2450,
        "longitude": 77.1890,
        "elevation_m": 2048.5,
        "river_basin": "Upper Beas Basin (Manali)",
        "status": "ACTIVE",
    }
    create_res = client.post("/api/v1/stations", json=station_payload)
    assert create_res.status_code == 200, f"Expected 200, got {create_res.status_code}: {create_res.text}"
    created_data = create_res.json()
    assert created_data["status"] == "REGISTERED"
    assert created_data["station"]["id"] == "STN_TEST_MANALI_VALLEY_01"

    # 2. Verify that station is present in listing
    list_res = client.get("/api/v1/stations")
    assert list_res.status_code == 200
    stations = list_res.json().get("stations", [])
    matched = [s for s in stations if s["id"] == "STN_TEST_MANALI_VALLEY_01"]
    assert len(matched) == 1
    assert matched[0]["name"] == "Manali Valley Hydrology Test Rig"
    assert matched[0]["latitude"] == 32.2450

    # 3. Delete the station
    del_res = client.delete("/api/v1/stations/STN_TEST_MANALI_VALLEY_01")
    assert del_res.status_code == 200, f"Expected 200 on delete, got {del_res.status_code}: {del_res.text}"
    assert del_res.json()["status"] == "DELETED"

    # 4. Verify station is no longer in listing
    list_res_after = client.get("/api/v1/stations")
    stations_after = list_res_after.json().get("stations", [])
    matched_after = [s for s in stations_after if s["id"] == "STN_TEST_MANALI_VALLEY_01"]
    assert len(matched_after) == 0
