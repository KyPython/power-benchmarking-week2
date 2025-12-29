#!/usr/bin/env python3
"""
Integration test: Verify all CLI commands work.

Usage:
    python tests/integration_test.py
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list) -> tuple[int, str, str]:
    """Run a command and capture output."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def test_cli():
    """Test all CLI commands."""
    tests = [
        (["power-benchmark", "--help"], 0, "usage:"),
        (["power-benchmark", "--version"], 0, "1.0.0"),
        (["power-benchmark", "monitor", "--help"], 0, "monitor"),
        (["power-benchmark", "analyze", "--help"], 0, "analyze"),
        (["power-benchmark", "optimize", "--help"], 0, "optimize"),
        (["power-benchmark", "config", "--help"], 0, "config"),
        (["power-benchmark", "quickstart", "--help"], 0, "quickstart"),
        (["power-benchmark", "validate", "--help"], 0, "validate"),
        # Test subcommands
        (["power-benchmark", "analyze", "app", "--help"], 0, "app_name"),
        (["power-benchmark", "analyze", "csv", "--help"], 0, "csv_file"),
        (["power-benchmark", "optimize", "energy-gap", "--help"], 0, "energy-gap"),
        (["power-benchmark", "optimize", "thermal", "--help"], 0, "thermal"),
        # Test config commands (non-destructive)
        (["power-benchmark", "config", "--show-path"], 0, "Configuration file"),
        (["power-benchmark", "config", "--list-profiles"], 0, None),  # May be empty, that's OK
    ]

    passed = 0
    failed = 0

    for cmd, expected_code, expected_output in tests:
        code, stdout, stderr = run_command(cmd)
        output = stdout + stderr

        if code != expected_code:
            print(f"❌ FAILED: {' '.join(cmd)}")
            print(f"   Expected exit code {expected_code}, got {code}")
            print(f"   Output: {output[:200]}")
            failed += 1
            continue

        if expected_output and expected_output.lower() not in output.lower():
            print(f"❌ FAILED: {' '.join(cmd)}")
            print(f"   Expected '{expected_output}' in output")
            print(f"   Output: {output[:200]}")
            failed += 1
            continue

        print(f"✅ PASSED: {' '.join(cmd)}")
        passed += 1

    print()
    print("=" * 70)
    print(f"Integration Test Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(test_cli())
