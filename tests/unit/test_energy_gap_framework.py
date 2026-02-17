import importlib
import math
import pytest

egf = importlib.import_module("scripts.energy_gap_framework")


@pytest.mark.unit
def test_calculate_energy_gap():
    out = egf.calculate_energy_gap(10.0, 6.0, {}, {})
    assert math.isclose(out["energy_gap_mj"], 4.0)
    assert out["energy_gap_percent"] == pytest.approx(40.0)
    assert out["improvement_ratio"] == pytest.approx(10.0/6.0)


@pytest.mark.unit
def test_calculate_thermal_throttle_risk_boundaries():
    out = egf.calculate_thermal_throttle_risk(
        instruction_count=1_000_000,
        execution_time=2.0,
        total_energy_mj=20.0,
    )
    assert out["power_metrics"]["average_power_mw"] > 0
    assert out["thermal_risk"]["overall_risk"] in ("LOW", "MEDIUM", "HIGH")


@pytest.mark.unit
def test_calculate_environmental_roi_and_prioritization():
    roi = egf.calculate_environmental_roi(energy_saved_per_task_mj=1000, tasks_per_day=100)
    assert roi["annual_co2_saved_kg"] >= 0
    ranked = egf.prioritize_backlog_by_sustainability([
        {"name": "A", "energy_saved_per_task_mj": 1000, "tasks_per_day": 100},
        {"name": "B", "energy_saved_per_task_mj": 200, "tasks_per_day": 20},
    ])
    assert len(ranked["prioritized_tasks"]) == 2
    assert ranked["prioritized_tasks"][0]["priority_score"] >= ranked["prioritized_tasks"][1]["priority_score"]


@pytest.mark.unit
def test_calculate_battery_life_advantage_and_marketing():
    bl = egf.calculate_battery_life_advantage(10.0, tasks_per_hour=100)
    assert bl["battery_life"]["new_hours"] >= bl["battery_life"]["current_hours"]
    vp = egf.build_marketing_value_proposition(
        battery_life_extension_hours=2.0,
        current_battery_life_hours=10.0,
        industry_benchmark_hours=23.0,
        user_value_metrics={"net_time_saved_hours": 0.5, "charging_sessions_saved_per_month": 3},
        competitive_advantage={"advantage_percent": 10.0, "advantage_hours": 1.0},
    )
    assert "headline" in vp and isinstance(vp["headline"], str)
