#!/usr/bin/env python3
"""
Analyze Command - Analyze power data and applications

Usage:
    power-benchmark analyze app Safari [--duration SECONDS] [--advanced]
    power-benchmark analyze csv power_log.csv [--output FILE]
"""

import argparse
import sys
import subprocess
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Import existing scripts
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add analyze command to argument parser."""
    parser = subparsers.add_parser(
        "analyze",
        aliases=["a"],
        help="Analyze power consumption data or applications",
        description="Analyze power data from CSV files or monitor specific applications",
    )

    subparsers_analyze = parser.add_subparsers(dest="analyze_type", help="Analysis type")

    # App analysis
    parser_app = subparsers_analyze.add_parser(
        "app",
        help="Analyze application power consumption",
        description="Monitor and analyze power consumption of a specific application",
    )
    parser_app.add_argument(
        "app_name", type=str, help="Application name to analyze (e.g., Safari, Chrome)"
    )
    parser_app.add_argument(
        "--duration",
        type=int,
        default=30,
        metavar="SECONDS",
        help="Analysis duration in seconds (default: 30)",
    )
    parser_app.add_argument(
        "--advanced", action="store_true", help="Use advanced analytics (premium feature)"
    )
    parser_app.set_defaults(analyze_subtype="app")

    # CSV analysis
    parser_csv = subparsers_analyze.add_parser(
        "csv",
        help="Analyze power data from CSV file",
        description="Analyze and visualize power consumption data from CSV log file",
    )
    parser_csv.add_argument("csv_file", type=str, help="Path to CSV file containing power data")
    parser_csv.add_argument(
        "--output",
        type=str,
        metavar="FILE",
        help="Output file for visualization (default: auto-generated)",
    )
    parser_csv.add_argument(
        "--advanced", action="store_true", help="Use advanced analytics (premium feature)"
    )
    parser_csv.set_defaults(analyze_subtype="csv")

    parser.set_defaults(func=run)
    return parser


def run(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Execute analyze command."""
    try:
        if not hasattr(args, "analyze_type") or args.analyze_type is None:
            logger.error("Analysis type required. Use 'app' or 'csv'")
            return 1

        if args.analyze_type == "app":
            return _analyze_app(args, config)
        elif args.analyze_type == "csv":
            return _analyze_csv(args, config)
        else:
            logger.error(f"Unknown analysis type: {args.analyze_type}")
            return 1

    except Exception as e:
        logger.error(f"Analyze command failed: {e}", exc_info=True)
        return 1


def _analyze_app(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Analyze application power consumption."""
    # Check permissions before starting
    is_available, error = check_powermetrics_availability()
    if not is_available:
        print(format_error_for_user(error))
        return 1

    # Continue with existing implementation...
    """Analyze application power consumption."""
    try:
        script_path = SCRIPTS_DIR / "app_power_analyzer.py"

        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return 1

        cmd = ["sudo", "python3", str(script_path), args.app_name]
        cmd.extend(["--duration", str(args.duration)])

        # Note: --advanced flag not yet supported by app_power_analyzer.py
        # if args.advanced:
        #     cmd.append("--advanced")

        logger.info(f"Analyzing application: {args.app_name}")
        result = subprocess.run(cmd, check=False)
        return result.returncode

    except Exception as e:
        logger.error(f"App analysis failed: {e}", exc_info=True)
        return 1


def _analyze_csv(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Analyze CSV power data."""
    try:
        csv_path = Path(args.csv_file)
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return 1

        script_path = SCRIPTS_DIR / "power_visualizer.py"

        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return 1

        cmd = ["python3", str(script_path), str(csv_path)]

        if args.output:
            cmd.extend(["--output", args.output])

        # Note: --advanced flag not yet supported by power_visualizer.py
        # if args.advanced:
        #     cmd.append("--advanced")

        logger.info(f"Analyzing CSV file: {csv_path}")
        result = subprocess.run(cmd, check=False)
        return result.returncode

    except Exception as e:
        logger.error(f"CSV analysis failed: {e}", exc_info=True)
        return 1
