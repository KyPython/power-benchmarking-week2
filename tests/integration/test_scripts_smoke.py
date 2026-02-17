import importlib
import runpy
import sys
import types
import pytest
from pathlib import Path

scripts = [
    "benchmark.py",
    "unified_benchmark.py",
    "analyze_power_data.py",
]


@pytest.mark.integration
@pytest.mark.parametrize("script", scripts)
def test_scripts_import_and_main_guard(script, monkeypatch):
    p = Path(__file__).resolve().parents[2] / "scripts" / script
    if not p.exists():
        pytest.skip(f"{script} not present")

    # Ensure scripts can be imported as modules without executing heavy logic
    mod_name = f"scripts.{p.stem}"
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        pytest.fail(f"Failed to import {mod_name}: {e}")

    # If the script defines main(args), call with --help and expect clean exit
    if hasattr(mod, "main") and callable(getattr(mod, "main")):
        try:
            mod.main(["--help"])  # should not run heavy work
        except SystemExit as e:
            assert e.code in (0, 2)
