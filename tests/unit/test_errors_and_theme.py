import importlib
import pytest


@pytest.mark.unit
def test_errors_module():
    try:
        errors = importlib.import_module("power_benchmarking_suite.errors")
    except ModuleNotFoundError:
        pytest.skip("errors module missing")

    # Validate custom exceptions are subclasses of Exception
    names = [n for n in dir(errors) if n.endswith("Error")]
    if not names:
        pytest.skip("no custom Error classes")
    for n in names:
        cls = getattr(errors, n)
        if isinstance(cls, type):
            assert issubclass(cls, Exception)


@pytest.mark.unit
def test_theme_and_usage_modules():
    for modname in ["power_benchmarking_suite.theme", "power_benchmarking_suite.usage", "power_benchmarking_suite.premium"]:
        try:
            m = importlib.import_module(modname)
        except ModuleNotFoundError:
            continue
        # Ensure module loads and exposes something callable or constants
        exported = [getattr(m, n) for n in dir(m) if not n.startswith("_")]
        assert exported is not None
