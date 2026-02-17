import importlib
import argparse
import pytest

cli = importlib.import_module("power_benchmarking_suite.cli")
validate_cmd = importlib.import_module("power_benchmarking_suite.commands.validate")


@pytest.mark.unit
@pytest.mark.parametrize(
    "argv, expected_exit",
    [
        (["validate", "--headless", "--mock"], 0),
        (["validate", "--headless", "--mock", "--mock-arch", "apple-silicon"], 0),
    ],
)
def test_cli_validate_subcommand(monkeypatch, capsys, argv, expected_exit):
    # Avoid making subprocess calls in validate by mocking compatibility functions
    monkeypatch.setattr(validate_cmd, "check_system_compatibility", lambda verbose=False: {"compatible": True, "checks": {}, "issues": [], "warnings": []})
    monkeypatch.setattr(validate_cmd, "_mock_architecture_compatibility", lambda architecture, verbose=False: {"compatible": True, "checks": {}, "issues": [], "warnings": []})

    def fake_get_config_manager():
        class M:
            config = {}
        return M()

    monkeypatch.setattr("power_benchmarking_suite.cli.get_config_manager", fake_get_config_manager)

    # Build parser and run main-like flow by invoking via argparse through main
    def run_and_capture(args_list):
        # Patch sys.argv by delegating through argparse within main
        import sys as _sys
        old = _sys.argv
        try:
            _sys.argv = ["power-benchmark"] + args_list
            return cli.main()
        finally:
            _sys.argv = old

    code = run_and_capture(argv)
    assert code in (0, expected_exit)
    out = capsys.readouterr().out + capsys.readouterr().err
    assert isinstance(out, str)
