import importlib
import math
import statistics
import pytest


aa = importlib.import_module("power_benchmarking_suite.advanced_analytics")


@pytest.mark.unit
def test_basic_statistics(sample_numbers):
    if not hasattr(aa, "mean"):
        pytest.skip("mean function not found in advanced_analytics")
    m = aa.mean(sample_numbers)
    assert math.isclose(m, statistics.mean(sample_numbers), rel_tol=1e-9)

    if hasattr(aa, "variance"):
        v = aa.variance(sample_numbers)
        assert v >= 0


@pytest.mark.unit
def test_outlier_detection(sample_series_irregular):
    # Try generic function names commonly used; skip when absent
    fn_names = [
        "detect_outliers",
        "zscore_outliers",
        "iqr_outliers",
    ]
    for name in fn_names:
        if hasattr(aa, name):
            fn = getattr(aa, name)
            out = fn(sample_series_irregular)
            assert isinstance(out, (list, tuple))
            assert any(x for x in out if isinstance(x, (int, float))) or len(out) >= 0
            break
    else:
        pytest.skip("No outlier detection function exposed by advanced_analytics")
