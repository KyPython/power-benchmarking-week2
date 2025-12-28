#!/usr/bin/env python3
"""
Unified CLI for Power Benchmarking Suite

Usage:
    power-benchmark --mode unified --duration 60
    power-benchmark --analyze app Safari
    power-benchmark --energy-gap simple.py optimized.py
    power-benchmark --premium-status
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
import json

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR.parent))

# Premium feature configuration
PREMIUM_CONFIG_FILE = Path.home() / ".power_benchmarking" / "premium_config.json"
FREE_TIER_LIMITS = {
    "max_devices": 1,
    "max_duration_hours": 1,  # 1 hour max per session
    "advanced_analytics": False,
    "cloud_sync": False,
    "team_collaboration": False,
    "api_access": False,
    "priority_support": False,
}

PREMIUM_TIER_FEATURES = {
    "max_devices": 10,
    "max_duration_hours": 24,  # 24 hours max per session
    "advanced_analytics": True,
    "cloud_sync": True,
    "team_collaboration": True,
    "api_access": True,
    "priority_support": True,
}


def load_premium_config() -> Dict:
    """Load premium configuration from file."""
    if PREMIUM_CONFIG_FILE.exists():
        try:
            with open(PREMIUM_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {"tier": "free", "features": FREE_TIER_LIMITS.copy()}


def save_premium_config(config: Dict):
    """Save premium configuration to file."""
    PREMIUM_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PREMIUM_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def check_premium_feature(feature: str, config: Optional[Dict] = None) -> bool:
    """Check if a premium feature is available."""
    if config is None:
        config = load_premium_config()
    
    tier = config.get("tier", "free")
    if tier == "premium":
        return PREMIUM_TIER_FEATURES.get(feature, False)
    return FREE_TIER_LIMITS.get(feature, False)


def check_duration_limit(duration_seconds: int, config: Optional[Dict] = None) -> tuple[bool, Optional[str]]:
    """Check if duration exceeds free tier limit."""
    if config is None:
        config = load_premium_config()
    
    tier = config.get("tier", "free")
    max_hours = PREMIUM_TIER_FEATURES["max_duration_hours"] if tier == "premium" else FREE_TIER_LIMITS["max_duration_hours"]
    max_seconds = max_hours * 3600
    
    if duration_seconds > max_seconds and tier == "free":
        return False, f"Duration {duration_seconds/3600:.1f} hours exceeds free tier limit ({max_hours} hour). Upgrade to premium for up to 24 hours."
    return True, None


def run_script(script_name: str, args: List[str], require_sudo: bool = False) -> int:
    """Run a script from the scripts directory."""
    script_path = SCRIPTS_DIR / script_name
    
    if not script_path.exists():
        print(f"❌ Error: Script '{script_name}' not found at {script_path}")
        return 1
    
    # Build command
    cmd = ["python3", str(script_path)] + args
    
    if require_sudo:
        cmd = ["sudo"] + cmd
        print("⚠️  Note: This command requires sudo privileges for powermetrics access.")
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error running script: {e}")
        return 1


def cmd_unified(args):
    """Run unified benchmark."""
    duration = args.duration
    test_mode = args.test
    
    config = load_premium_config()
    
    # Check duration limit
    if duration:
        duration_seconds = duration * 3600 if duration > 10 else duration  # Assume hours if > 10
        allowed, error_msg = check_duration_limit(int(duration_seconds), config)
        if not allowed:
            print(f"❌ {error_msg}")
            print("💡 Upgrade to premium: power-benchmark --upgrade")
            return 1
    
    script_args = []
    if test_mode:
        script_args.extend(["--test", str(test_mode)])
    elif duration:
        script_args.extend(["--duration", str(duration)])
    
    return run_script("unified_benchmark.py", script_args, require_sudo=True)


def cmd_analyze(args):
    """Analyze application power consumption."""
    if not args.app:
        print("❌ Error: --app is required for analysis")
        return 1
    
    config = load_premium_config()
    
    # Advanced analytics is premium-only
    if args.advanced and not check_premium_feature("advanced_analytics", config):
        print("❌ Advanced analytics is a premium feature.")
        print("💡 Upgrade to premium: power-benchmark --upgrade")
        return 1
    
    script_args = [args.app]
    if args.duration:
        script_args.extend(["--duration", str(args.duration)])
    if args.advanced:
        script_args.append("--advanced")
    
    return run_script("app_power_analyzer.py", script_args, require_sudo=True)


def cmd_energy_gap(args):
    """Calculate energy gap between two implementations."""
    if not args.simple or not args.optimized:
        print("❌ Error: Both --simple and --optimized are required")
        return 1
    
    # Import energy gap framework
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from energy_gap_framework import calculate_energy_gap
        
        # This is a simplified version - full implementation would load actual code
        print("📊 Energy Gap Analysis")
        print(f"   Simple: {args.simple}")
        print(f"   Optimized: {args.optimized}")
        print("   (Full analysis requires running energy_gap_framework.py)")
        print("   See docs/TECHNICAL_DEEP_DIVE.md for details")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def cmd_visualize(args):
    """Visualize power data from CSV."""
    if not args.csv:
        print("❌ Error: --csv is required")
        return 1
    
    config = load_premium_config()
    
    # Advanced analytics for visualization is premium-only
    if args.advanced:
        if not check_premium_feature("advanced_analytics", config):
            print("❌ Advanced visualization is a premium feature.")
            print("💡 Upgrade to premium: power-benchmark --upgrade")
            return 1
    
    script_args = [args.csv]
    if args.output:
        script_args.extend(["--output", args.output])
    if args.advanced:
        script_args.append("--advanced")
    
    return run_script("power_visualizer.py", script_args, require_sudo=False)


def cmd_logger(args):
    """Start power logging."""
    config = load_premium_config()
    
    # Check duration limit
    duration_seconds = args.duration * 3600 if args.duration > 10 else args.duration
    allowed, error_msg = check_duration_limit(int(duration_seconds), config)
    if not allowed:
        print(f"❌ {error_msg}")
        print("💡 Upgrade to premium: power-benchmark --upgrade")
        return 1
    
    script_args = []
    if args.duration:
        script_args.extend(["--duration", str(args.duration)])
    if args.output:
        script_args.extend(["--output", args.output])
    
    return run_script("power_logger.py", script_args, require_sudo=True)


def cmd_premium_status(args):
    """Show premium status and features."""
    config = load_premium_config()
    tier = config.get("tier", "free")
    features = config.get("features", FREE_TIER_LIMITS.copy())
    
    print("=" * 70)
    print("💎 PREMIUM STATUS")
    print("=" * 70)
    print(f"Tier: {tier.upper()}")
    print()
    
    if tier == "free":
        print("📋 FREE TIER LIMITS:")
        for key, value in FREE_TIER_LIMITS.items():
            print(f"   {key}: {value}")
        print()
        print("💡 Upgrade to premium for:")
        print("   ✅ Up to 10 devices")
        print("   ✅ Up to 24 hours per session")
        print("   ✅ Advanced analytics")
        print("   ✅ Cloud sync")
        print("   ✅ Team collaboration")
        print("   ✅ API access")
        print("   ✅ Priority support")
        print()
        print("   Run: power-benchmark --upgrade")
    else:
        print("📋 PREMIUM FEATURES:")
        for key, value in PREMIUM_TIER_FEATURES.items():
            status = "✅" if features.get(key, False) else "❌"
            print(f"   {status} {key}: {value}")
    
    print("=" * 70)
    return 0


def cmd_upgrade(args):
    """Upgrade to premium (placeholder for payment integration)."""
    print("=" * 70)
    print("💎 UPGRADE TO PREMIUM")
    print("=" * 70)
    print()
    print("Premium features include:")
    print("   ✅ Up to 10 devices (vs. 1 free)")
    print("   ✅ Up to 24 hours per session (vs. 1 hour free)")
    print("   ✅ Advanced analytics and insights")
    print("   ✅ Cloud sync and backup")
    print("   ✅ Team collaboration")
    print("   ✅ API access for automation")
    print("   ✅ Priority support")
    print()
    print("Pricing:")
    print("   💰 Pro: $99/month")
    print("   💰 Enterprise: $500+/month (custom pricing)")
    print()
    print("To upgrade, visit: https://power-benchmarking-suite.com/upgrade")
    print("Or contact: sales@power-benchmarking-suite.com")
    print()
    print("💡 For now, you can enable premium features locally for testing:")
    print("   power-benchmark --enable-premium-test")
    print("=" * 70)
    return 0


def cmd_enable_premium_test(args):
    """Enable premium features for local testing (development only)."""
    config = {
        "tier": "premium",
        "features": PREMIUM_TIER_FEATURES.copy(),
        "test_mode": True
    }
    save_premium_config(config)
    print("✅ Premium features enabled for local testing (development mode)")
    print("⚠️  This is for testing only. Production use requires paid subscription.")
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Power Benchmarking Suite - Unified CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run unified benchmark (30 second test)
  power-benchmark --mode unified --test 30
  
  # Run full benchmark
  sudo power-benchmark --mode unified
  
  # Analyze Safari power consumption
  sudo power-benchmark --analyze app Safari --duration 60
  
  # Visualize power data
  power-benchmark --visualize power_log.csv
  
  # Start power logging
  sudo power-benchmark --logger --duration 3600 --output power_log.csv
  
  # Check premium status
  power-benchmark --premium-status
  
  # Upgrade to premium
  power-benchmark --upgrade
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Unified benchmark
    parser_unified = subparsers.add_parser("unified", aliases=["u"], help="Run unified benchmark")
    parser_unified.add_argument("--test", type=int, help="Test mode duration (seconds)")
    parser_unified.add_argument("--duration", type=float, help="Benchmark duration (hours)")
    
    # Analyze app
    parser_analyze = subparsers.add_parser("analyze", aliases=["a"], help="Analyze application power")
    parser_analyze.add_argument("--app", type=str, required=True, help="Application name (e.g., Safari)")
    parser_analyze.add_argument("--duration", type=int, default=30, help="Analysis duration (seconds)")
    parser_analyze.add_argument("--advanced", action="store_true", help="Advanced analytics (premium)")
    
    # Energy gap
    parser_energy = subparsers.add_parser("energy-gap", aliases=["eg"], help="Calculate energy gap")
    parser_energy.add_argument("--simple", type=str, help="Simple implementation file")
    parser_energy.add_argument("--optimized", type=str, help="Optimized implementation file")
    
    # Visualize
    parser_viz = subparsers.add_parser("visualize", aliases=["v"], help="Visualize power data")
    parser_viz.add_argument("--csv", type=str, required=True, help="CSV file to visualize")
    parser_viz.add_argument("--output", type=str, help="Output image file")
    parser_viz.add_argument("--advanced", action="store_true", help="Advanced analytics (premium)")
    
    # Logger
    parser_log = subparsers.add_parser("logger", aliases=["l"], help="Start power logging")
    parser_log.add_argument("--duration", type=int, help="Logging duration (seconds)")
    parser_log.add_argument("--output", type=str, default="power_log.csv", help="Output CSV file")
    
    # Premium status
    subparsers.add_parser("premium-status", aliases=["ps"], help="Show premium status")
    
    # Upgrade
    subparsers.add_parser("upgrade", aliases=["up"], help="Upgrade to premium")
    
    # Enable premium test (development)
    subparsers.add_parser("enable-premium-test", aliases=["ept"], help="Enable premium for testing (dev only)")
    
    # Legacy mode support (--mode flag)
    parser.add_argument("--mode", type=str, help="Mode (unified, analyze, visualize, logger)")
    parser.add_argument("--duration", type=float, help="Duration")
    parser.add_argument("--test", type=int, help="Test mode")
    parser.add_argument("--app", type=str, help="Application name")
    parser.add_argument("--csv", type=str, help="CSV file")
    parser.add_argument("--output", type=str, help="Output file")
    parser.add_argument("--advanced", action="store_true", help="Advanced features")
    parser.add_argument("--simple", type=str, help="Simple implementation")
    parser.add_argument("--optimized", type=str, help="Optimized implementation")
    parser.add_argument("--premium-status", action="store_true", help="Show premium status")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade to premium")
    
    args = parser.parse_args()
    
    # Handle legacy --mode flag
    if args.mode:
        if args.mode == "unified":
            return cmd_unified(args)
        elif args.mode == "analyze":
            return cmd_analyze(args)
        elif args.mode == "visualize":
            return cmd_visualize(args)
        elif args.mode == "logger":
            return cmd_logger(args)
    
    # Handle legacy flags
    if args.premium_status:
        return cmd_premium_status(args)
    if args.upgrade:
        return cmd_upgrade(args)
    
    # Handle subcommands
    if args.command == "unified" or args.command == "u":
        return cmd_unified(args)
    elif args.command == "analyze" or args.command == "a":
        return cmd_analyze(args)
    elif args.command == "energy-gap" or args.command == "eg":
        return cmd_energy_gap(args)
    elif args.command == "visualize" or args.command == "v":
        return cmd_visualize(args)
    elif args.command == "logger" or args.command == "l":
        return cmd_logger(args)
    elif args.command == "premium-status" or args.command == "ps":
        return cmd_premium_status(args)
    elif args.command == "upgrade" or args.command == "up":
        return cmd_upgrade(args)
    elif args.command == "enable-premium-test" or args.command == "ept":
        return cmd_enable_premium_test(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

