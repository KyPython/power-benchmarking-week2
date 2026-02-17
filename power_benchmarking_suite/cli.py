#!/usr/bin/env python3
"""
Unified CLI for Power Benchmarking Suite

Refactored to use command modules for better organization.
"""

import sys
import argparse
import logging
from typing import Optional

# Setup observability (structured logging + tracing)
try:
    from power_benchmarking_suite.observability.logging import setup_logging
    from power_benchmarking_suite.observability.tracing import setup_tracing

    logger = setup_logging(level="INFO", format_type="json")
    setup_tracing()  # Initialize OpenTelemetry tracing
except ImportError:
    # Fallback to standard logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

# Import command modules
from power_benchmarking_suite.commands import (
    monitor,
    analyze,
    optimize,
    config_cmd,
    quickstart,
    validate,
    business,
    marketing,
    schedule,
)
from power_benchmarking_suite.commands import help_cmd
from power_benchmarking_suite.commands import premium_cmd
from power_benchmarking_suite.commands import usage_cmd

# Import config manager
from power_benchmarking_suite.config import get_config_manager


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="power-benchmark",
        description="Power Benchmarking Suite - Comprehensive toolkit for monitoring, analyzing, and visualizing power consumption on Apple Silicon Macs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick start guide
  power-benchmark quickstart
  
  # Monitor power in real-time (30 second test)
  sudo power-benchmark monitor --test 30
  
  # Analyze application power consumption
  sudo power-benchmark analyze app Safari --duration 60
  
  # Analyze CSV power data
  power-benchmark analyze csv power_log.csv --output report.png
  
  # Energy optimization analysis
  power-benchmark optimize energy-gap --simple simple.py --optimized optimized.py
  
  # Thermal optimization
  power-benchmark optimize thermal --app Safari --ambient-temp 35
  
  # Configuration management
  power-benchmark config --list
  power-benchmark config --set powermetrics.sample_interval 1000
  
  # System validation
  power-benchmark validate

For more information, see QUICK_START_GUIDE.md
        """,
    )

    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    # Premium flags (top-level shortcuts)
    parser.add_argument("--premium-status", action="store_true", help="Show premium status")
    parser.add_argument("--upgrade", action="store_true", help="Show upgrade instructions")
    parser.add_argument("--enable-premium-test", action="store_true", help="Enable local premium test mode")

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute", metavar="COMMAND")

    # Register all commands
    monitor.add_parser(subparsers)
    analyze.add_parser(subparsers)
    optimize.add_parser(subparsers)
    config_cmd.add_parser(subparsers)
    quickstart.add_parser(subparsers)
    validate.add_parser(subparsers)
    business.add_parser(subparsers)
    marketing.add_parser(subparsers)
    schedule.add_parser(subparsers)
    help_cmd.add_parser(subparsers)
    premium_cmd.add_parser(subparsers)
    usage_cmd.add_parser(subparsers)

    # Parse arguments
    args = parser.parse_args()

    # Handle premium flags early
    if getattr(args, "premium_status", False) or getattr(args, "upgrade", False) or getattr(args, "enable_premium_test", False):
        try:
            # Reuse premium command handlers
            class A: pass
            a = A()
            if getattr(args, "premium_status", False):
                a.premium_action = "status"
            elif getattr(args, "enable_premium_test", False):
                a.premium_action = "enable-test"
            else:
                a.premium_action = "upgrade"
            return premium_cmd.run(a, None)
        except Exception as e:
            logger.error(f"Premium flag handling failed: {e}")

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    try:
        config_manager = get_config_manager()
        config = config_manager.config
    except Exception as e:
        logger.warning(f"Failed to load configuration: {e}. Using defaults.")
        config = None

    # Handle no command (show help)
    if args.command is None:
        parser.print_help()
        print()
        print("💡 Quick Start: Run 'power-benchmark quickstart' for interactive setup")
        print("📚 Commands Reference: Run 'power-benchmark help' for complete command guide")
        return 0

    # Execute command
    try:
        if hasattr(args, "func"):
            return args.func(args, config)
        else:
            logger.error(f"Command '{args.command}' has no handler function")
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        logger.info("Command interrupted by user")
        return 130
    except Exception as e:
        # Try to use structured error handling if available
        try:
            from power_benchmarking_suite.errors import PowerBenchmarkError

            if isinstance(e, PowerBenchmarkError):
                # Print error with actionable help if available
                print(f"Error: {e}", file=sys.stderr)
                if args.verbose and hasattr(e, 'actionable_help') and e.actionable_help:
                    print(f"\n{e.actionable_help}", file=sys.stderr)
                return 1
        except ImportError:
            pass

        logger.error(f"Command failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
