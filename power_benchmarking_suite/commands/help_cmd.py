#!/usr/bin/env python3
"""
Help Command - Show commands reference guide

Usage:
    power-benchmark help
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add help command to argument parser."""
    parser = subparsers.add_parser(
        "help",
        aliases=["commands", "ref", "reference"],
        help="Show commands reference guide",
        description="Display comprehensive commands reference guide",
    )
    parser.add_argument(
        "--command",
        type=str,
        help="Show help for specific command (e.g., 'validate', 'optimize')",
    )
    parser.set_defaults(func=run)
    return parser


def _show_commands_reference():
    """Display the commands reference guide."""
    print("=" * 70)
    print("📚 Power Benchmarking Suite - Commands Reference")
    print("=" * 70)
    print()
    print("Quick Command Overview:")
    print("-" * 70)
    print()
    
    commands = [
        ("validate", "System compatibility checks", "No (for basic)"),
        ("optimize", "Energy gap and thermal optimization", "No"),
        ("marketing", "Lead capture, email, README generation", "No"),
        ("monitor", "Real-time power monitoring", "Yes"),
        ("analyze", "Power consumption analysis", "Yes (for apps)"),
        ("config", "Configuration management", "No"),
        ("quickstart", "Interactive onboarding", "No"),
        ("business", "Business automation", "No"),
        ("help", "Show this reference guide", "No"),
    ]
    
    print(f"{'Command':<20} {'Purpose':<40} {'Sudo Required?':<15}")
    print("-" * 70)
    for cmd, purpose, sudo in commands:
        print(f"{cmd:<20} {purpose:<40} {sudo:<15}")
    
    print()
    print("=" * 70)
    print("📖 Detailed Command Examples")
    print("=" * 70)
    print()
    
    print("1. System Validation:")
    print("   power-benchmark validate                    # Quick check")
    print("   power-benchmark validate --verbose          # Detailed with explanations")
    print("   power-benchmark validate --mock --verbose   # CI/CD testing")
    print()
    
    print("2. Energy & Thermal Optimization:")
    print("   power-benchmark optimize energy-gap --simple simple.py --optimized optimized.py")
    print("   power-benchmark optimize thermal --app Safari --ambient-temp 35")
    print()
    
    print("3. Marketing & Documentation:")
    print("   power-benchmark marketing readme            # Generate Green README")
    print()
    
    print("4. Real-Time Power Monitoring:")
    print("   sudo power-benchmark monitor --test 30     # 30-second test")
    print("   sudo power-benchmark monitor --duration 300 --output session.csv")
    print()
    
    print("5. Power Analysis:")
    print("   sudo power-benchmark analyze app Safari --duration 60")
    print("   power-benchmark analyze csv power_log.csv --output report.png")
    print()
    
    print("6. Configuration:")
    print("   power-benchmark config --list              # List all settings")
    print("   power-benchmark config --set powermetrics.sample_interval 1000")
    print()
    
    print("7. Interactive Onboarding:")
    print("   power-benchmark quickstart                 # Step-by-step guide")
    print("   power-benchmark qs                         # Alias")
    print()
    
    print("8. Business Automation:")
    print("   power-benchmark business clients --list")
    print("   power-benchmark business invoice --generate")
    print()
    
    print("=" * 70)
    print("🔄 Common Workflows")
    print("=" * 70)
    print()
    
    print("First-Time Setup:")
    print("  1. power-benchmark quickstart")
    print("  2. power-benchmark validate --verbose")
    print("  3. sudo power-benchmark monitor --test 30")
    print()
    
    print("Daily Power Monitoring:")
    print("  1. sudo power-benchmark monitor --duration 300 --output daily_log.csv")
    print("  2. power-benchmark analyze csv daily_log.csv --output daily_report.png")
    print()
    
    print("Code Optimization:")
    print("  1. power-benchmark optimize energy-gap --simple simple.py --optimized optimized.py")
    print("  2. power-benchmark optimize thermal --app MyApp --ambient-temp 35")
    print("  3. sudo power-benchmark monitor --test 60")
    print()
    
    print("=" * 70)
    print("📊 System Status")
    print("=" * 70)
    print()
    
    # Try to detect system
    try:
        from power_benchmarking_suite.commands.validate import check_system_compatibility
        compatibility = check_system_compatibility()
        if compatibility.get("compatible"):
            chip = compatibility.get("chip", "Unknown")
            print(f"✅ Detected: Apple {chip} chip")
            print("✅ Thermal Guardian: Fully compatible")
            print("✅ All Thermal Guardian features supported")
            print("✅ Mock mode working for CI/CD testing")
        else:
            print("⚠️  System compatibility check failed")
            print("   Run 'power-benchmark validate' for details")
    except Exception:
        print("ℹ️  Run 'power-benchmark validate' to check system status")
    
    print()
    print("=" * 70)
    print("🆘 Getting Help")
    print("=" * 70)
    print()
    
    print("Quick Help:")
    print("  power-benchmark --help                      # Show all commands")
    print("  power-benchmark validate --help            # Command-specific help")
    print("  power-benchmark optimize --help")
    print()
    
    print("Documentation:")
    print("  • Quick Start Guide: QUICK_START_GUIDE.md")
    print("  • Commands Reference: COMMANDS_REFERENCE.md")
    print("  • Product Study Guide: docs/PRODUCT_STUDY_GUIDE.md")
    print("  • Technical Deep Dive: docs/TECHNICAL_DEEP_DIVE.md")
    print()
    
    print("=" * 70)
    print("💡 Tips")
    print("=" * 70)
    print()
    print("1. Always run 'validate' first to ensure system compatibility")
    print("2. Use '--verbose' for detailed explanations and frameworks")
    print("3. Use '--mock' for CI/CD testing without hardware")
    print("4. Save outputs with '--output' flag for later analysis")
    print("5. Run 'quickstart' if you're new to the suite")
    print()
    print("=" * 70)
    print()
    print("📚 Full Reference: See COMMANDS_REFERENCE.md for complete details")
    print()


def _show_command_help(command_name: str):
    """Show help for a specific command."""
    print(f"Help for '{command_name}' command:")
    print("=" * 70)
    print()
    
    # Try to get help from the command
    import subprocess
    try:
        result = subprocess.run(
            ["power-benchmark", command_name, "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"Command '{command_name}' not found or has no help available.")
            print()
            print("Available commands:")
            print("  validate, optimize, marketing, monitor, analyze, config,")
            print("  quickstart, business, help")
    except Exception as e:
        logger.error(f"Failed to get help for command '{command_name}': {e}")
        print(f"Could not retrieve help for '{command_name}'.")
        print("Try: power-benchmark {command_name} --help".format(command_name=command_name))


def run(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Execute help command."""
    try:
        if args.command:
            _show_command_help(args.command)
        else:
            _show_commands_reference()
        return 0
    except Exception as e:
        logger.error(f"Help command failed: {e}", exc_info=True)
        return 1

