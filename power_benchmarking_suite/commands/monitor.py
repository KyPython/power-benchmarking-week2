#!/usr/bin/env python3
"""
Monitor Command - Real-time power monitoring

Usage:
    power-benchmark monitor [--duration SECONDS] [--output FILE] [--test SECONDS]
"""

import argparse
import sys
import subprocess
import os
from pathlib import Path
from typing import Optional
import logging
import json
import time

# Setup observability
try:
    from power_benchmarking_suite.observability.logging import get_logger
    from power_benchmarking_suite.observability.tracing import get_tracer, trace_span

    logger = get_logger("monitor")
    tracer = get_tracer("monitor")
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    tracer = None
    trace_span = lambda t, n, a=None: __import__("contextlib").nullcontext()

# Import error handling
from ..errors import PowerMetricsPermissionError
from ..utils.error_handler import check_powermetrics_availability, format_error_for_user

# Import existing scripts
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add monitor command to argument parser."""
    parser = subparsers.add_parser(
        "monitor",
        aliases=["m"],
        help="Real-time power monitoring with CoreML inference",
        description="Monitor ANE, CPU, and GPU power consumption in real-time",
    )
    parser.add_argument(
        "--test",
        type=int,
        metavar="SECONDS",
        help="Test mode: run for specified seconds (default: run until Ctrl+C)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        metavar="HOURS",
        help="Run benchmark for specified hours (default: run until Ctrl+C)",
    )
    parser.add_argument("--output", type=str, metavar="FILE", help="Save power data to CSV file")
    parser.add_argument(
        "--arduino", action="store_true", help="Enable Arduino serial communication"
    )
    parser.set_defaults(func=run)
    return parser


def run(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Execute monitor command."""
    with trace_span(
        tracer, "monitor.run", {"test_mode": bool(args.test), "duration": args.duration}
    ):
        try:
            logger.info(
                "Starting power monitoring",
                extra={
                    "test_mode": bool(args.test),
                    "duration": args.duration,
                    "arduino_enabled": args.arduino,
                },
            )

            # Check permissions before starting
            is_available, error = check_powermetrics_availability()
            if not is_available:
                logger.error("powermetrics not available", extra={"error": str(error)})
                print(format_error_for_user(error))
                return 1

            # Check for thermal feedback file (from optimize command)
            thermal_feedback_path = Path.home() / ".power_benchmarking" / "thermal_feedback.json"
            thermal_adjustments = None
            if thermal_feedback_path.exists():
                try:
                    with open(thermal_feedback_path, "r") as f:
                        thermal_adjustments = json.load(f)
                    logger.info("Thermal Guardian adjustments detected - applying optimizations")
                except Exception as e:
                    logger.warning(f"Could not load thermal feedback: {e}")

            # Build command for unified_benchmark.py
            script_path = SCRIPTS_DIR / "unified_benchmark.py"

            if not script_path.exists():
                logger.error(f"Script not found: {script_path}")
                return 1

            cmd = ["sudo", "python3", str(script_path)]

            if args.test:
                cmd.extend(["--test", str(args.test)])
            elif args.duration:
                cmd.extend(["--duration", str(args.duration)])

            if args.output:
                cmd.extend(["--output", args.output])

            if args.arduino:
                # Arduino is auto-detected by unified_benchmark.py
                pass

            # Pass thermal adjustments if available
            if thermal_adjustments:
                # Create environment variable for thermal feedback
                env = os.environ.copy()
                env["THERMAL_FEEDBACK"] = json.dumps(thermal_adjustments)
                logger.info(
                    "Thermal feedback applied",
                    extra={"strategy": thermal_adjustments.get("recommended_strategy")},
                )
            else:
                env = None

            # Display thermal feedback info if available
            if thermal_adjustments:
                print("\n🌡️  Thermal Guardian Active")
                print("-" * 70)
                strategy = thermal_adjustments.get("recommended_strategy", "UNKNOWN")
                if strategy == "BURST_OPTIMIZED":
                    print("✅ Using optimized burst strategy (Thermal Paradox)")
                    profile = thermal_adjustments.get("optimized_profile", {})
                    if profile:
                        burst_duration = profile.get("burst_duration_s", "N/A")
                        idle_duration = profile.get("idle_duration_s", "N/A")
                        print(f"   Burst: {burst_duration}s, Idle: {idle_duration}s")
                print()

            # Run the script
            logger.info("Executing unified_benchmark.py", extra={"command": " ".join(cmd)})
            result = subprocess.run(cmd, check=False, env=env)

            if result.returncode != 0:
                logger.error("Monitor command failed", extra={"exit_code": result.returncode})
                return result.returncode

            logger.info("Power monitoring completed successfully")
            return 0

        except PermissionError as e:
            error = PowerMetricsPermissionError("powermetrics")
            print(format_error_for_user(error))
            return 1
        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
            return 130
        except Exception as e:
            print(format_error_for_user(e))
            logger.error(f"Monitor command failed: {e}", exc_info=True)
            return 1
