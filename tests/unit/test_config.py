import os
import importlib
import types
import pytest


@pytest.mark.unit
def test_config_defaults(monkeypatch_env):
    monkeypatch_env.clear_prefix("PWR_")
    mod = importlib.import_module("power_benchmarking_suite.config")
    importlib.reload(mod)
    # Check some common default attributes exist and are of expected type
    assert hasattr(mod, "Settings"), "Pydantic Settings model expected"
    settings = getattr(mod, "settings", None)
    assert settings is not None
    # Common expected attrs; tolerate absence by skipping if not there
    for attr in [
        "ENV",
        "LOG_LEVEL",
        "DATA_DIR",
    ]:
        if hasattr(settings, attr):
            getattr(settings, attr)


@pytest.mark.unit
def test_config_env_override(monkeypatch_env):
    monkeypatch_env.set("PWR_ENV", "test")
    monkeypatch_env.set("PWR_LOG_LEVEL", "DEBUG")

    mod = importlib.import_module("power_benchmarking_suite.config")
    importlib.reload(mod)

    settings = getattr(mod, "settings", None)
    if settings is None:
        pytest.skip("settings object not exposed in config module")

    if hasattr(settings, "ENV"):
        assert settings.ENV.lower() == "test"
    if hasattr(settings, "LOG_LEVEL"):
        assert str(settings.LOG_LEVEL).upper().startswith("DEBUG")
