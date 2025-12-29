#!/usr/bin/env python3
"""
Quickstart Command - Interactive onboarding

Usage:
    power-benchmark quickstart
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    """Add quickstart command to argument parser."""
    parser = subparsers.add_parser(
        "quickstart",
        aliases=["qs", "start"],
        help="Interactive onboarding and setup guide",
        description="Step-by-step guide to get started with power benchmarking",
    )
    parser.add_argument(
        "--skip-checks", action="store_true", help="Skip system compatibility checks"
    )
    parser.set_defaults(func=run)
    return parser


def run(args: argparse.Namespace, config: Optional[dict] = None) -> int:
    """Execute quickstart command."""
    try:
        print("=" * 70)
        print("🚀 Power Benchmarking Suite - Quick Start")
        print("=" * 70)
        print()

        # Step 1: System Check
        if not args.skip_checks:
            print("Step 1: System Compatibility Check")
            print("-" * 70)
            from power_benchmarking_suite.commands.validate import check_system_compatibility

            compatibility = check_system_compatibility()

            if not compatibility["compatible"]:
                print("❌ System compatibility check failed:")
                for issue in compatibility.get("issues", []):
                    print(f"   - {issue}")
                print()
                print("Please resolve these issues before continuing.")
                return 1
            else:
                print("✅ System compatibility check passed")
                print()

        # Step 2: Model Check
        print("Step 2: Model Check")
        print("-" * 70)
        model_path = Path("MobileNetV2.mlpackage")
        if model_path.exists():
            print("✅ MobileNetV2.mlpackage found")
        else:
            print("⚠️  MobileNetV2.mlpackage not found")
            print("   Run: python3 scripts/convert_model.py")
            print()
            response = input("Continue anyway? (y/n): ")
            if response.lower() != "y":
                return 1
        print()

        # Step 3: Quick Test
        print("Step 3: Quick Test (30 seconds)")
        print("-" * 70)
        print("This will run a 30-second power benchmark test.")
        print("You'll need sudo privileges for powermetrics.")
        print()
        response = input("Run quick test? (y/n): ")
        if response.lower() == "y":
            print()
            print("Running: sudo power-benchmark monitor --test 30")
            print("(Press Ctrl+C to stop)")
            print()

            import subprocess

            result = subprocess.run(
                ["sudo", "power-benchmark", "monitor", "--test", "30"], check=False
            )

            if result.returncode == 0:
                print()
                print("✅ Quick test completed successfully!")
            else:
                print()
                print("⚠️  Quick test had issues (this is OK for first run)")
        else:
            print("Skipping quick test")
        print()

        # Step 4: Introduction to Mechanical Sympathy (Mission-Driven with Progressive Disclosure)
        print("Step 4: Understanding 'Mechanical Sympathy'")
        print("-" * 70)
        print("🎯 What is Mechanical Sympathy?")
        print()
        print("Think of your code like a race car driver who understands their engine:")
        print("  • A good driver knows when to shift gears (cache levels)")
        print("  • They avoid redlining (thermal throttling)")
        print("  • They optimize for the track (hardware architecture)")
        print()
        print("Mechanical Sympathy = Writing code that works WITH your hardware,")
        print("not against it. This can save 4.5x energy! 💚")
        print()

        # Progressive Disclosure: Start with web developer analogy
        print("🌐 For Web Developers:")
        print("-" * 70)
        print("You know how Big O notation matters? (O(n²) vs O(n log n))")
        print("Cache levels are like that, but for ENERGY:")
        print()
        print("  • L1 Cache = Your browser's memory (instant)")
        print("  • L2 Cache = Your local database (fast)")
        print("  • L3 Cache = Your CDN (pretty fast)")
        print("  • DRAM = Your API call to a remote server (slow & expensive)")
        print()
        print("💡 The 'Energy Gap':")
        print("  • Accessing DRAM is like making 40 API calls")
        print("  • Accessing L2 cache is like reading from local storage")
        print("  • Same data, 40x less energy!")
        print()

        response = input("Want to see the real numbers? (y/n): ")
        if response.lower() == "y":
            print()
            print("📊 Real Example: Cache Optimization")
            print("-" * 70)
            print("In our tests, we achieved:")
            print("  • 78.5% of energy savings from cache optimization")
            print("  • 4.5x improvement in Energy per Unit Work")
            print("  • How? By moving data from DRAM → L2 cache")
            print()
            print("The 'Energy Gap' (Energy per Access):")
            print("  • DRAM: ~200 pJ (like 40 API calls)")
            print("  • L2 cache: ~5 pJ (like 1 local read)")
            print("  • L1 cache: ~1 pJ (like reading from memory)")
            print()
            print("💡 Key Insight: Small code changes → Massive energy savings")
            print()
            print("🎓 Why This Matters for Web Dev:")
            print("  • Your React app's state management? Cache-aware!")
            print("  • Your database queries? Cache-friendly!")
            print("  • Your API responses? Cache-optimized!")
            print()
            print("  Same principles, different hardware layer.")
            print()
            print("Want to learn more? See docs/TECHNICAL_DEEP_DIVE.md")
            print("  (Search for 'Mechanical Sympathy' or 'Energy Gap')")
            print()

        # Step 5: Next Steps
        print("Step 5: Next Steps")
        print("-" * 70)
        print("You're all set! Here are some commands to try:")
        print()
        print("  # Monitor power in real-time")
        print("  sudo power-benchmark monitor --test 30")
        print()
        print("  # Analyze an application")
        print("  sudo power-benchmark analyze app Safari --duration 60")
        print()
        print("  # Optimize for thermal safety")
        print("  power-benchmark optimize thermal --app Safari --ambient-temp 35")
        print("  sudo power-benchmark monitor --test 30  # Applies optimizations!")
        print()
        print("  # Visualize power data")
        print("  power-benchmark analyze csv power_log.csv")
        print()
        print("  # Check configuration")
        print("  power-benchmark config --list")
        print()
        print("For more help:")
        print("  power-benchmark --help")
        print("  See QUICK_START_GUIDE.md for detailed walkthrough")
        print()
        print("🎓 Learning Path:")
        print("  1. Start: Run monitor commands (you are here)")
        print("  2. Next: Read about Energy Gap (docs/TECHNICAL_DEEP_DIVE.md)")
        print("  3. Advanced: Understand Mechanical Sympathy (cache optimization)")
        print("  4. Expert: Apply to your own code (see examples in docs/)")
        print()
        print("=" * 70)

        return 0

    except KeyboardInterrupt:
        print("\n\nQuickstart interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Quickstart failed: {e}", exc_info=True)
        return 1
