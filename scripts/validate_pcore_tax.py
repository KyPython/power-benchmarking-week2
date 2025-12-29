#!/usr/bin/env python3
"""
P-Core Tax Calculation Validation
Forces background daemons onto P-cores and measures the "Power Tax" - the specific
increase in baseline power when tasks share high-performance silicon with main workload.
"""

import subprocess
import time
import sys
import argparse
import re
from typing import Dict, List, Optional, Tuple
import psutil
import signal

# Global flag
running = True


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
    print("\n\n🛑 Shutting down...")
    running = False
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def find_daemon_pids(daemon_name: str) -> List[int]:
    """
    Find all PIDs for a macOS daemon.

    Args:
        daemon_name: Daemon name (e.g., 'mds', 'backupd', 'cloudd')

    Returns:
        List of PIDs
    """
    pids = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if daemon_name.lower() in proc.info["name"].lower():
                pids.append(proc.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return pids


def force_to_p_cores(pid: int, p_cores: List[int] = [4, 5, 6, 7]) -> bool:
    """
    Force a process to P-cores using taskpolicy.

    Args:
        pid: Process ID
        p_cores: List of P-core IDs (M2: 4, 5, 6, 7)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create CPU mask for P-cores (binary: 11110000 = 0xF0)
        cpu_mask = 0
        for core in p_cores:
            cpu_mask |= 1 << core

        # Use taskpolicy to set CPU affinity
        cmd = ["sudo", "taskpolicy", "-c", hex(cpu_mask), "-p", str(pid)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            return True
        else:
            print(f"  ⚠️  taskpolicy failed for PID {pid}: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  taskpolicy timeout for PID {pid}")
        return False
    except Exception as e:
        print(f"  ⚠️  Error forcing PID {pid} to P-cores: {e}")
        return False


def measure_baseline_power(duration: int = 10, sample_interval: int = 500) -> Dict[str, float]:
    """
    Measure baseline system power using powermetrics.

    Returns:
        Dictionary with power statistics
    """
    print(f"  📊 Measuring baseline power ({duration}s)...")

    cmd = [
        "sudo",
        "powermetrics",
        "--samplers",
        "cpu_power",
        "-i",
        str(sample_interval),
        "-n",
        str(int(duration * 1000 / sample_interval)),
    ]

    power_values = []

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        output, error = process.communicate(timeout=duration + 5)

        if error:
            print(f"  ⚠️  powermetrics stderr: {error[:200]}")

        # Parse ANE Power values
        pattern = r"ANE\s+Power[:\s]+([\d.]+)\s*mW"
        matches = re.finditer(pattern, output, re.IGNORECASE)

        for match in matches:
            power_mw = float(match.group(1))
            power_values.append(power_mw)

        if not power_values:
            # Try alternative pattern
            pattern2 = r"(?:ANE|Neural\s+Engine)[:\s]+([\d.]+)\s*mW"
            matches = re.finditer(pattern2, output, re.IGNORECASE)
            for match in matches:
                power_mw = float(match.group(1))
                power_values.append(power_mw)

        if power_values:
            return {
                "mean": sum(power_values) / len(power_values),
                "min": min(power_values),
                "max": max(power_values),
                "median": sorted(power_values)[len(power_values) // 2],
                "samples": len(power_values),
            }
        else:
            print("  ⚠️  No power values found in powermetrics output")
            return {}

    except subprocess.TimeoutExpired:
        process.kill()
        print("  ❌ powermetrics timeout")
        return {}
    except Exception as e:
        print(f"  ❌ Error measuring power: {e}")
        return {}


def calculate_power_tax(
    baseline_e: Dict[str, float], baseline_p: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate the "Power Tax" - increase in baseline when daemons use P-cores.

    Args:
        baseline_e: Baseline power with daemons on E-cores (default)
        baseline_p: Baseline power with daemons on P-cores (forced)

    Returns:
        Dictionary with tax calculations
    """
    if not baseline_e or not baseline_p or "mean" not in baseline_e or "mean" not in baseline_p:
        return {}

    tax_absolute = baseline_p["mean"] - baseline_e["mean"]
    tax_percent = (tax_absolute / baseline_e["mean"]) * 100 if baseline_e["mean"] > 0 else 0

    return {
        "baseline_e_mw": baseline_e["mean"],
        "baseline_p_mw": baseline_p["mean"],
        "tax_absolute_mw": tax_absolute,
        "tax_percent": tax_percent,
        "efficiency_loss_mw": tax_absolute,
    }


def run_experiment(daemon_name: str, duration: int = 10, p_cores: List[int] = [4, 5, 6, 7]):
    """
    Run the P-Core Tax experiment.

    Steps:
    1. Measure baseline with daemons on E-cores (default)
    2. Force daemons to P-cores
    3. Measure baseline with daemons on P-cores
    4. Calculate Power Tax
    """
    print("=" * 70)
    print("🔬 P-Core Tax Calculation Experiment")
    print("=" * 70)
    print()

    # Step 1: Find daemon PIDs
    print(f"1️⃣  Finding {daemon_name} processes...")
    pids = find_daemon_pids(daemon_name)

    if not pids:
        print(f"  ⚠️  No {daemon_name} processes found")
        print(f"  💡 Make sure {daemon_name} is running")
        return None

    print(f"  ✅ Found {len(pids)} process(es): PIDs {pids}")
    print()

    # Step 2: Measure baseline (E-cores, default)
    print("2️⃣  Measuring baseline with daemons on E-cores (default)...")
    baseline_e = measure_baseline_power(duration)

    if not baseline_e:
        print("  ❌ Failed to measure baseline")
        return None

    print(f"  ✅ Baseline (E-cores): {baseline_e['mean']:.2f} mW")
    print(f"     Min: {baseline_e['min']:.2f} mW, Max: {baseline_e['max']:.2f} mW")
    print(f"     Samples: {baseline_e['samples']}")
    print()

    # Step 3: Force daemons to P-cores
    print("3️⃣  Forcing daemons to P-cores...")
    forced_count = 0
    for pid in pids:
        if force_to_p_cores(pid, p_cores):
            forced_count += 1
            print(f"  ✅ Forced PID {pid} to P-cores {p_cores}")
        else:
            print(f"  ❌ Failed to force PID {pid}")

    if forced_count == 0:
        print("  ⚠️  Could not force any processes to P-cores")
        print("  💡 May require root privileges or process may not support affinity")
        return None

    print(f"  ✅ Forced {forced_count}/{len(pids)} processes to P-cores")
    print()

    # Wait for scheduler to adjust
    print("  ⏳ Waiting 3 seconds for scheduler to adjust...")
    time.sleep(3)
    print()

    # Step 4: Measure baseline (P-cores, forced)
    print("4️⃣  Measuring baseline with daemons on P-cores (forced)...")
    baseline_p = measure_baseline_power(duration)

    if not baseline_p:
        print("  ❌ Failed to measure baseline")
        return None

    print(f"  ✅ Baseline (P-cores): {baseline_p['mean']:.2f} mW")
    print(f"     Min: {baseline_p['min']:.2f} mW, Max: {baseline_p['max']:.2f} mW")
    print(f"     Samples: {baseline_p['samples']}")
    print()

    # Step 5: Calculate Power Tax
    print("5️⃣  Calculating Power Tax...")
    tax = calculate_power_tax(baseline_e, baseline_p)

    if not tax:
        print("  ❌ Failed to calculate tax")
        return None

    print()
    print("=" * 70)
    print("📊 POWER TAX RESULTS")
    print("=" * 70)
    print()
    print(f"Baseline (E-cores):     {tax['baseline_e_mw']:.2f} mW")
    print(f"Baseline (P-cores):     {tax['baseline_p_mw']:.2f} mW")
    print()
    print(f"💸 Power Tax:           {tax['tax_absolute_mw']:.2f} mW")
    print(f"   Percentage Increase: {tax['tax_percent']:.2f}%")
    print(f"   Efficiency Loss:     {tax['efficiency_loss_mw']:.2f} mW")
    print()

    # Interpretation
    if tax["tax_percent"] > 20:
        print("⚠️  HIGH TAX: Significant power increase (>20%)")
        print("   Background tasks are consuming substantial P-core resources")
    elif tax["tax_percent"] > 10:
        print("⚠️  MODERATE TAX: Noticeable power increase (10-20%)")
        print("   Background tasks are impacting P-core efficiency")
    elif tax["tax_percent"] > 0:
        print("✅ LOW TAX: Minimal power increase (<10%)")
        print("   Background tasks have minimal impact on P-core efficiency")
    else:
        print("ℹ️  NEGATIVE TAX: Power decreased (unexpected)")
        print("   May indicate measurement variance or scheduler behavior")

    print()
    print("=" * 70)

    return tax


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="P-Core Tax Calculation: Measure power increase when daemons use P-cores"
    )
    parser.add_argument(
        "daemon", nargs="?", default="mds", help="Daemon name to test (default: mds)"
    )
    parser.add_argument(
        "--duration", type=int, default=10, help="Measurement duration in seconds (default: 10)"
    )
    parser.add_argument(
        "--p-cores",
        type=int,
        nargs="+",
        default=[4, 5, 6, 7],
        help="P-core IDs (M2 default: 4 5 6 7)",
    )

    args = parser.parse_args()

    # Common macOS daemons to test
    common_daemons = ["mds", "backupd", "cloudd", "kernel_task"]

    if args.daemon not in common_daemons:
        print(f"⚠️  Warning: '{args.daemon}' may not be a standard macOS daemon")
        print(f"   Common daemons: {', '.join(common_daemons)}")
        print()

    result = run_experiment(args.daemon, args.duration, args.p_cores)

    if result:
        print("\n✅ Experiment complete!")
        print("\n💡 Key Insights:")
        print("   • Power Tax quantifies the cost of P-core sharing")
        print("   • High tax (>20%) indicates inefficient scheduling")
        print("   • Low tax (<10%) indicates good E-core isolation")
        print("   • Use this to validate AR calculations")
        return 0
    else:
        print("\n❌ Experiment failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
