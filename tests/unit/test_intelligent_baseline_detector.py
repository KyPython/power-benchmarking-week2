import importlib
import types
import pytest

ibd = importlib.import_module("scripts.intelligent_baseline_detector")


@pytest.mark.unit
def test_is_on_p_cores():
    assert ibd.is_on_p_cores([4, 5, 6, 7]) is True
    assert ibd.is_on_p_cores([0, 1, 4]) is False
    assert ibd.is_on_p_cores([]) is False


@pytest.mark.unit
def test_detect_high_baseline():
    assert ibd.detect_high_baseline(900) is True
    assert ibd.detect_high_baseline(799.9) is False


@pytest.mark.unit
def test_calculate_ar_impact():
    res = ibd.calculate_ar_impact(baseline_power=800.0, stressed_power=2000.0, power_tax=500.0)
    assert res["ar_normal_pct"] > res["ar_with_tax_pct"]
    assert res["ar_reduction_pct"] >= 0


@pytest.mark.unit
def test_distinguish_legitimate_vs_wasted_monkeypatched(monkeypatch):
    # Force deterministic inputs for workload and daemons
    monkeypatch.setattr(ibd, "check_active_workload", lambda: {"cpu_percent": 5.0, "has_active_workload": False, "workload_cpu_percent": 0.5})
    monkeypatch.setattr(ibd, "check_daemons_on_p_cores", lambda: {"mds": {"on_p_cores": True, "estimated_tax_mw": 700.0, "pids": [123]}})

    out = ibd.distinguish_legitimate_vs_wasted(1200.0, ibd.check_active_workload())
    assert out["classification"] in ("likely_wasted", "mixed", "legitimate_workload")
    # With known tax, wasted should be at least a large portion of tax
    assert out["estimated_wasted_mw"] >= 0.8 * 700.0


@pytest.mark.unit
def test_analyze_baseline_paths(monkeypatch):
    # Low CPU, high baseline, mock known tax
    monkeypatch.setattr(ibd, "check_active_workload", lambda: {"cpu_percent": 3.0, "has_active_workload": False, "workload_cpu_percent": 0.2})
    monkeypatch.setattr(ibd, "check_daemons_on_p_cores", lambda: {"backupd": {"on_p_cores": True, "estimated_tax_mw": 600.0, "pids": [42]}})

    analysis = ibd.analyze_baseline(1000.0, stressed_power=3000.0)
    assert analysis["high_baseline"] is True
    assert analysis["total_estimated_tax_mw"] >= 600.0
    assert any("Power Breakdown" in w or "Estimated Power Tax" in w for w in analysis["warnings"])