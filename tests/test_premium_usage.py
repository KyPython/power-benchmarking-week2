#!/usr/bin/env python3
"""
Unit tests for premium gating and usage tracking.
"""
import tempfile
from pathlib import Path
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from power_benchmarking_suite import premium as premium_mod
from power_benchmarking_suite import usage as usage_mod


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def test_premium_is_premium_with_api_key(tmp_path: Path):
    cfg = tmp_path / "premium_config.json"
    write_json(cfg, {"licensing": {"polar_api_key": "polar_oat_test"}})
    with patch.object(premium_mod, "PREMIUM_CONFIG_FILE", cfg):
        pf = premium_mod.get_premium_features()
        assert pf.is_premium() is True


def test_premium_is_premium_with_tier(tmp_path: Path):
    cfg = tmp_path / "premium_config.json"
    write_json(cfg, {"tier": "premium", "features": {"advanced_analytics": True}})
    with patch.object(premium_mod, "PREMIUM_CONFIG_FILE", cfg):
        pf = premium_mod.get_premium_features()
        assert pf.is_premium() is True
        assert pf.advanced_analytics_enabled() is True


def test_usage_record_and_summary(tmp_path: Path):
    usage_file = tmp_path / "usage.json"
    with patch.object(usage_mod, "USAGE_FILE", usage_file):
        usage_mod.record_session("monitor", 30, success=True)
        usage_mod.record_session("analyze", 10, success=False)
        summary = usage_mod.usage_summary()
        assert summary["today_sessions"] == 2
        assert summary["today_seconds"] == 40
        assert summary["total_seconds"] == 40


@patch("power_benchmarking_suite.commands.monitor.check_powermetrics_availability", lambda: (True, None))
@patch("power_benchmarking_suite.commands.monitor.subprocess.run")
def test_monitor_free_tier_blocks_long_duration(mock_run):
    # Stub subprocess to succeed
    mock_run.return_value = SimpleNamespace(returncode=0)
    # Stub premium features: Free tier
    from power_benchmarking_suite.commands import monitor as monitor_cmd
    with patch.object(monitor_cmd, "get_premium_features", lambda: SimpleNamespace(is_premium=lambda: False)):
        args = SimpleNamespace(test=None, duration=2.0, output=None, arduino=False)
        rc = monitor_cmd.run(args, config=None)
        # Should block with exit code 1 due to free-tier duration > 1 hour
        assert rc == 1


@patch("power_benchmarking_suite.commands.monitor.check_powermetrics_availability", lambda: (True, None))
@patch("power_benchmarking_suite.commands.monitor.subprocess.run")
def test_monitor_premium_allows_long_duration(mock_run):
    mock_run.return_value = SimpleNamespace(returncode=0)
    from power_benchmarking_suite.commands import monitor as monitor_cmd
    with patch.object(monitor_cmd, "get_premium_features", lambda: SimpleNamespace(is_premium=lambda: True)):
        args = SimpleNamespace(test=None, duration=2.0, output=None, arduino=False)
        rc = monitor_cmd.run(args, config=None)
        assert rc == 0
        # Ensure subprocess invoked
        mock_run.assert_called()
