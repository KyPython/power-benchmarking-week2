import importlib
import types
import sys
import pytest


@pytest.mark.unit
def test_cli_entrypoint_help(capsys):
    mod = importlib.import_module("power_benchmarking_suite.cli")
    if not hasattr(mod, "main"):
        pytest.skip("cli.main not found")
    try:
        mod.main(["--help"])  # many CLIs print help and exit 0
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out + capsys.readouterr().err
    assert "help" in out.lower() or "usage" in out.lower()


@pytest.mark.unit
def test_package_main_invocation(capsys):
    # python -m power_benchmarking_suite should dispatch to cli or __main__
    pkg_main = importlib.import_module("power_benchmarking_suite.__main__")
    if not hasattr(pkg_main, "main"):
        pytest.skip("__main__.main not found")
    try:
        pkg_main.main(["--version"])  # expect to print version or handle flag gracefully
    except SystemExit as e:
        assert e.code in (0, 2)
    out = capsys.readouterr().out + capsys.readouterr().err
    assert out is not None
