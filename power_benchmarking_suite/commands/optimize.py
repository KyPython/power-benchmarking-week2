#!/usr/bin/env python3
"""
Optimize Command - Energy Gap analysis and optimization recommendations

Usage:
    power-benchmark optimize energy-gap --simple FILE1 --optimized FILE2
    power-benchmark optimize thermal --app Safari --ambient-temp 35
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Import energy gap framework
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR.parent))


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add optimize command to argument parser."""
    parser = subparsers.add_parser(
        "optimize",
        aliases=["opt", "o"],
        help="Energy optimization analysis and recommendations",
        description="Analyze energy efficiency and provide optimization recommendations",
    )

    subparsers_opt = parser.add_subparsers(dest="optimize_type", help="Optimization type")

    # Energy gap analysis
    parser_energy = subparsers_opt.add_parser(
        "energy-gap",
        aliases=["eg"],
        help="Calculate energy gap between implementations",
        description="Compare energy consumption between simple and optimized implementations",
    )
    parser_energy.add_argument(
        "--simple",
        type=str,
        required=True,
        metavar="FILE",
        help="Simple implementation file or description",
    )
    parser_energy.add_argument(
        "--optimized",
        type=str,
        required=True,
        metavar="FILE",
        help="Optimized implementation file or description",
    )
    parser_energy.set_defaults(optimize_subtype="energy-gap")

    # Thermal optimization
    parser_thermal = subparsers_opt.add_parser(
        "thermal",
        help="Thermal optimization recommendations",
        description="Get thermal optimization recommendations for applications",
    )
    parser_thermal.add_argument(
        "--app", type=str, required=True, help="Application name to optimize"
    )
    parser_thermal.add_argument(
        "--ambient-temp",
        type=float,
        default=25.0,
        metavar="CELSIUS",
        help="Ambient temperature in Celsius (default: 25.0)",
    )
    parser_thermal.set_defaults(optimize_subtype="thermal")

    parser.set_defaults(func=run)
    return parser


def run(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Execute optimize command."""
    try:
        if not hasattr(args, "optimize_type") or args.optimize_type is None:
            logger.error("Optimization type required. Use 'energy-gap' or 'thermal'")
            return 1

        if args.optimize_type == "energy-gap":
            return _optimize_energy_gap(args, config)
        elif args.optimize_type == "thermal":
            return _optimize_thermal(args, config)
        else:
            logger.error(f"Unknown optimization type: {args.optimize_type}")
            return 1

    except Exception as e:
        logger.error(f"Optimize command failed: {e}", exc_info=True)
        return 1


def _optimize_energy_gap(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Calculate energy gap between implementations."""
    try:
        # Import energy gap framework
        try:
            from scripts.energy_gap_framework import calculate_energy_gap
        except ImportError:
            logger.error(
                "Energy gap framework not available. Ensure scripts/energy_gap_framework.py exists."
            )
            return 1

        logger.info("Energy Gap Analysis")
        logger.info(f"  Simple: {args.simple}")
        logger.info(f"  Optimized: {args.optimized}")
        logger.info("")
        logger.info("Note: Full energy gap analysis requires actual power measurements.")
        logger.info("See docs/TECHNICAL_DEEP_DIVE.md for detailed usage examples.")
        logger.info("")
        logger.info("To perform full analysis:")
        logger.info("  1. Run benchmarks for both implementations")
        logger.info("  2. Collect power data (CSV files)")
        logger.info("  3. Use energy_gap_framework.py directly with measured data")

        return 0

    except Exception as e:
        logger.error(f"Energy gap analysis failed: {e}", exc_info=True)
        return 1


def _optimize_thermal(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Get thermal optimization recommendations."""
    try:
        # Import thermal functions
        try:
            # Import from scripts directory
            scripts_dir = Path(__file__).parent.parent.parent / "scripts"
            sys.path.insert(0, str(scripts_dir))
            from energy_gap_framework import calculate_safety_ceiling
        except ImportError:
            logger.error("Thermal optimization framework not available.")
            logger.error("Ensure scripts/energy_gap_framework.py exists and is importable.")
            calculate_safety_ceiling = None

        print(f"Thermal Optimization Analysis for: {args.app}")
        print(f"Ambient Temperature: {args.ambient_temp}°C")
        print()

        # Calculate safety ceiling
        try:
            if calculate_safety_ceiling is not None:
                safety = calculate_safety_ceiling(
                    ambient_temp_c=args.ambient_temp, max_device_temp_c=95.0
                )
            else:
                raise ImportError("calculate_safety_ceiling not available")

            print("Thermal Safety Analysis:")
            print(f"  Safety Ceiling: {safety['safety_ceiling_mw']:.0f} mW")
            print(f"  Burst Ceiling: {safety['burst_ceiling_mw']:.0f} mW")
            print(f"  Sustained Ceiling: {safety['sustained_ceiling_mw']:.0f} mW")
            print(f"  Thermal Risk: {safety['thermal_risk_level']}")
            print()
            print("Recommendation: Use Thermal Guardian to optimize power profile.")
            print("See docs/TECHNICAL_DEEP_DIVE.md for Thermal Guardian details.")
        except Exception as e:
            logger.warning(f"Could not calculate safety ceiling: {e}")
            print("Note: Full thermal analysis requires energy_gap_framework functions.")
            print("See scripts/thermal_throttle_controller.py for thermal control.")

        return 0

    except Exception as e:
        logger.error(f"Thermal optimization failed: {e}", exc_info=True)
        return 1
