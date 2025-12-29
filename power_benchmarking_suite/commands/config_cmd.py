#!/usr/bin/env python3
"""
Config Command - Configuration management

Usage:
    power-benchmark config --list
    power-benchmark config --get KEY
    power-benchmark config --set KEY VALUE
    power-benchmark config --profile NAME
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

# Import config manager
from power_benchmarking_suite.config import get_config_manager


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add config command to argument parser."""
    parser = subparsers.add_parser(
        "config",
        aliases=["c"],
        help="Manage configuration and profiles",
        description="View, modify, and manage power benchmarking configuration",
    )

    parser.add_argument("--list", action="store_true", help="List all configuration values")
    parser.add_argument(
        "--get",
        type=str,
        metavar="KEY",
        help="Get configuration value (e.g., powermetrics.sample_interval)",
    )
    parser.add_argument(
        "--set",
        nargs=2,
        metavar=("KEY", "VALUE"),
        help="Set configuration value (e.g., --set powermetrics.sample_interval 1000)",
    )
    parser.add_argument("--profile", type=str, metavar="NAME", help="Use or create a profile")
    parser.add_argument("--list-profiles", action="store_true", help="List all available profiles")
    parser.add_argument("--show-path", action="store_true", help="Show configuration file path")

    parser.set_defaults(func=run)
    return parser


def run(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Execute config command."""
    try:
        config_manager = get_config_manager()

        if args.show_path:
            print(f"Configuration file: {config_manager.config_file}")
            return 0

        if args.list:
            _list_config(config_manager)
            return 0

        if args.get:
            _get_config(config_manager, args.get)
            return 0

        if args.set:
            _set_config(config_manager, args.set[0], args.set[1])
            return 0

        if args.profile:
            _use_profile(config_manager, args.profile)
            return 0

        if args.list_profiles:
            _list_profiles(config_manager)
            return 0

        # No action specified, show help
        import sys

        parser = sys.modules[__name__].parser if "parser" in dir(sys.modules[__name__]) else None
        if parser:
            parser.print_help()
        else:
            print(
                "No action specified. Use --list, --get, --set, --profile, --list-profiles, or --show-path"
            )
        return 1

    except Exception as e:
        logger.error(f"Config command failed: {e}", exc_info=True)
        return 1


def _list_config(config_manager):
    """List all configuration values."""
    import json

    config = config_manager.config

    # Try to print as YAML if available, otherwise JSON
    try:
        import yaml

        print(yaml.dump(config, default_flow_style=False, sort_keys=False))
    except ImportError:
        print(json.dumps(config, indent=2))


def _get_config(config_manager, key: str):
    """Get a configuration value."""
    value = config_manager.get(key)
    if value is None:
        print(f"Configuration key '{key}' not found")
        return 1
    print(f"{key} = {value}")
    return 0


def _set_config(config_manager, key: str, value: str):
    """Set a configuration value."""
    # Try to convert value to appropriate type
    converted_value: Any = value
    try:
        # Try int
        if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
            converted_value = int(value)
        # Try float
        elif "." in value:
            try:
                converted_value = float(value)
            except ValueError:
                pass
        # Try bool
        elif value.lower() in ("true", "false"):
            converted_value = value.lower() == "true"
    except (ValueError, AttributeError):
        pass  # Keep as string

    config_manager.set(key, converted_value)
    print(f"Set {key} = {converted_value}")
    return 0


def _use_profile(config_manager, profile_name: str):
    """Load and use a profile."""
    profile = config_manager.load_profile(profile_name)
    if not profile:
        print(f"Profile '{profile_name}' not found. Creating new profile...")
        # Create empty profile
        config_manager.save_profile(profile_name, {})
        print(f"Created profile '{profile_name}'")
    else:
        print(f"Loaded profile '{profile_name}'")
        # Merge profile into current config
        config_manager.config.update(profile)
        config_manager.save_config()
        print("Profile applied to current configuration")


def _list_profiles(config_manager):
    """List all available profiles."""
    profiles = config_manager.list_profiles()
    if not profiles:
        print("No profiles found")
        return

    print("Available profiles:")
    for profile in profiles:
        print(f"  - {profile}")
