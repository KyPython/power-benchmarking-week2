#!/usr/bin/env python3
"""
Intelligent Baseline Detector
Uses P-Core Tax findings to auto-detect and warn about high baseline power
that may indicate P-core usage by background daemons.
"""

import psutil
import subprocess
import re
from typing import Dict, List, Optional, Tuple
import sys


def find_daemon_pids(daemon_name: str) -> List[int]:
    """Find all PIDs for a macOS daemon."""
    pids = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if daemon_name.lower() in proc.info["name"].lower():
                pids.append(proc.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return pids


def check_cpu_affinity(pid: int) -> Optional[List[int]]:
    """
    Check which CPU cores a process is allowed to use.
    Returns list of core IDs or None if can't determine.
    """
    try:
        proc = psutil.Process(pid)
        # Get CPU affinity (cores this process can run on)
        affinity = proc.cpu_affinity()
        return affinity
    except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
        # cpu_affinity() may not be available on macOS
        return None


def is_on_p_cores(affinity: List[int], p_cores: List[int] = [4, 5, 6, 7]) -> bool:
    """
    Check if process is restricted to P-cores only.
    Returns True if affinity contains only P-cores.
    """
    if not affinity:
        return False

    # Check if all allowed cores are P-cores
    e_cores = [0, 1, 2, 3]
    has_e_core = any(core in e_cores for core in affinity)
    has_p_core = any(core in p_cores for core in affinity)

    # If has P-cores but no E-cores, likely forced to P-cores
    if has_p_core and not has_e_core:
        return True

    return False


def estimate_power_tax(daemon_name: str, p_cores: List[int] = [4, 5, 6, 7]) -> Optional[float]:
    """
    Estimate power tax if daemon is on P-cores.
    Returns estimated tax in mW or None if can't determine.
    """
    pids = find_daemon_pids(daemon_name)
    if not pids:
        return None

    # Check if any instance is on P-cores
    on_p_cores = False
    for pid in pids:
        affinity = check_cpu_affinity(pid)
        if affinity and is_on_p_cores(affinity, p_cores):
            on_p_cores = True
            break

    if not on_p_cores:
        return 0.0  # No tax if on E-cores

    # Estimated tax based on validation results
    # Typical values: mds=700mW, backupd=600mW, cloudd=500mW
    tax_estimates = {
        "mds": 700.0,
        "backupd": 600.0,
        "cloudd": 500.0,
        "kernel_task": 400.0,
    }

    return tax_estimates.get(daemon_name.lower(), 500.0)  # Default estimate


def detect_high_baseline(baseline_power: float, threshold: float = 800.0) -> bool:
    """
    Detect if baseline power is suspiciously high.
    Returns True if baseline exceeds threshold.
    """
    return baseline_power > threshold


def check_daemons_on_p_cores(
    common_daemons: List[str] = ["mds", "backupd", "cloudd"]
) -> Dict[str, Dict]:
    """
    Check which daemons are running on P-cores.
    Returns dictionary with daemon status.
    """
    results = {}

    for daemon in common_daemons:
        pids = find_daemon_pids(daemon)
        if not pids:
            continue

        on_p_cores = False
        for pid in pids:
            affinity = check_cpu_affinity(pid)
            if affinity and is_on_p_cores(affinity):
                on_p_cores = True
                break

        estimated_tax = estimate_power_tax(daemon) if on_p_cores else 0.0

        results[daemon] = {
            "pids": pids,
            "on_p_cores": on_p_cores,
            "estimated_tax_mw": estimated_tax,
        }

    return results


def calculate_ar_impact(
    baseline_power: float, stressed_power: float, power_tax: float
) -> Dict[str, float]:
    """
    Calculate how Power Tax affects Attribution Ratio.

    Returns:
        Dictionary with AR calculations
    """
    # Normal AR (without tax)
    delta_normal = stressed_power - baseline_power
    ar_normal = (delta_normal / stressed_power) * 100 if stressed_power > 0 else 0

    # AR with tax (baseline increased by tax)
    baseline_with_tax = baseline_power + power_tax
    delta_with_tax = stressed_power - baseline_with_tax
    ar_with_tax = (delta_with_tax / stressed_power) * 100 if stressed_power > 0 else 0

    # AR reduction
    ar_reduction = ar_normal - ar_with_tax

    return {
        "baseline_normal_mw": baseline_power,
        "baseline_with_tax_mw": baseline_with_tax,
        "stressed_power_mw": stressed_power,
        "ar_normal_pct": ar_normal,
        "ar_with_tax_pct": ar_with_tax,
        "ar_reduction_pct": ar_reduction,
        "power_tax_mw": power_tax,
    }


def check_active_workload() -> Dict[str, float]:
    """
    Check if there's an active workload (legitimate power usage) vs just background.

    Returns:
        Dictionary with CPU usage, process activity, etc.
    """
    try:
        # Get overall CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Get top processes by CPU
        processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent"]):
            try:
                proc.info["cpu_percent"] = proc.cpu_percent(interval=0.0)
                if proc.info["cpu_percent"] > 1.0:  # Only significant processes
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by CPU usage
        processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
        top_processes = processes[:5]  # Top 5

        # Check for common workload indicators
        workload_indicators = [
            "python",
            "node",
            "chrome",
            "safari",
            "xcode",
            "ffmpeg",
            "docker",
            "java",
            "go",
            "rust",
            "cargo",
        ]
        has_workload = any(
            any(indicator in proc.get("name", "").lower() for indicator in workload_indicators)
            for proc in top_processes
        )

        return {
            "cpu_percent": cpu_percent,
            "top_processes": top_processes,
            "has_active_workload": has_workload,
            "workload_cpu_percent": sum(p.get("cpu_percent", 0) for p in top_processes[:3]),
        }
    except Exception as e:
        return {
            "cpu_percent": 0.0,
            "top_processes": [],
            "has_active_workload": False,
            "workload_cpu_percent": 0.0,
            "error": str(e),
        }


def distinguish_legitimate_vs_wasted(baseline_power: float, workload_info: Dict) -> Dict[str, any]:
    """
    Distinguish between legitimate workload power and wasted P-core leakage.

    Logic:
    - If CPU usage > 20%: Likely legitimate workload
    - If CPU usage < 10% but baseline > 800 mW: Likely wasted (P-core leakage)
    - If daemons on P-cores: Calculate wasted portion
    - If active workload: Calculate legitimate portion

    Returns:
        Dictionary with breakdown of legitimate vs wasted power
    """
    cpu_percent = workload_info.get("cpu_percent", 0.0)
    has_workload = workload_info.get("has_active_workload", False)
    workload_cpu = workload_info.get("workload_cpu_percent", 0.0)

    # Typical idle power (E-cores only)
    typical_idle = 500.0  # mW

    # Estimate legitimate power based on CPU usage
    # Rule of thumb: 1% CPU ≈ 10-20 mW on Apple Silicon
    # High CPU (>20%) suggests legitimate workload
    if cpu_percent > 20.0:
        # Significant CPU usage - likely legitimate
        estimated_legitimate = typical_idle + (cpu_percent * 15.0)  # 15 mW per % CPU
        estimated_legitimate = min(estimated_legitimate, baseline_power * 0.9)  # Cap at 90%
        estimated_wasted = baseline_power - estimated_legitimate
        classification = "legitimate_workload"
    elif cpu_percent > 10.0:
        # Moderate CPU - mixed
        estimated_legitimate = typical_idle + (cpu_percent * 10.0)
        estimated_legitimate = min(estimated_legitimate, baseline_power * 0.7)
        estimated_wasted = baseline_power - estimated_legitimate
        classification = "mixed"
    else:
        # Low CPU but high baseline - likely wasted
        estimated_legitimate = typical_idle
        estimated_wasted = baseline_power - estimated_legitimate
        classification = "likely_wasted"

    # Check daemons on P-cores to refine estimate
    daemon_status = check_daemons_on_p_cores()
    total_tax = sum(
        status["estimated_tax_mw"] for status in daemon_status.values() if status["on_p_cores"]
    )

    # Refine wasted estimate based on actual P-core tax
    if total_tax > 0:
        # We know some power is wasted (P-core tax)
        # Adjust wasted estimate to account for known tax
        estimated_wasted = max(estimated_wasted, total_tax * 0.8)  # At least 80% of tax is wasted
        estimated_legitimate = baseline_power - estimated_wasted

    return {
        "baseline_power_mw": baseline_power,
        "cpu_percent": cpu_percent,
        "has_active_workload": has_workload,
        "classification": classification,
        "estimated_legitimate_mw": estimated_legitimate,
        "estimated_wasted_mw": estimated_wasted,
        "wasted_percent": (estimated_wasted / baseline_power * 100) if baseline_power > 0 else 0,
        "known_pcore_tax_mw": total_tax,
        "typical_idle_mw": typical_idle,
    }


def analyze_baseline(baseline_power: float, stressed_power: Optional[float] = None) -> Dict:
    """
    Analyze baseline power and provide intelligent warnings.
    Now distinguishes between legitimate workload and wasted P-core leakage.

    Returns:
        Dictionary with analysis results and warnings
    """
    analysis = {
        "baseline_power_mw": baseline_power,
        "high_baseline": detect_high_baseline(baseline_power),
        "daemons_on_p_cores": {},
        "total_estimated_tax_mw": 0.0,
        "warnings": [],
        "recommendations": [],
        "workload_info": {},
        "power_breakdown": {},
    }

    # Check for active workload to distinguish legitimate vs wasted
    workload_info = check_active_workload()
    analysis["workload_info"] = workload_info

    # Distinguish legitimate workload vs wasted P-core leakage
    power_breakdown = distinguish_legitimate_vs_wasted(baseline_power, workload_info)
    analysis["power_breakdown"] = power_breakdown

    # Check if baseline is high
    if analysis["high_baseline"]:
        analysis["warnings"].append(
            f"⚠️  High baseline power detected: {baseline_power:.1f} mW " f"(threshold: 800 mW)"
        )

        # Add workload classification
        classification = power_breakdown["classification"]
        if classification == "legitimate_workload":
            analysis["warnings"].append(
                f"✅ Active workload detected (CPU: {workload_info['cpu_percent']:.1f}%) - "
                f"baseline likely legitimate"
            )
        elif classification == "likely_wasted":
            analysis["warnings"].append(
                f"⚠️  Low CPU usage ({workload_info['cpu_percent']:.1f}%) but high baseline - "
                f"likely wasted P-core leakage"
            )
        else:
            analysis["warnings"].append(
                f"ℹ️  Mixed workload (CPU: {workload_info['cpu_percent']:.1f}%) - "
                f"both legitimate and wasted components"
            )

        # Add power breakdown
        analysis["warnings"].append(
            f"📊 Power Breakdown: "
            f"Legitimate: {power_breakdown['estimated_legitimate_mw']:.1f} mW, "
            f"Wasted: {power_breakdown['estimated_wasted_mw']:.1f} mW "
            f"({power_breakdown['wasted_percent']:.1f}%)"
        )

        # Check daemons
        daemon_status = check_daemons_on_p_cores()
        analysis["daemons_on_p_cores"] = daemon_status

        # Calculate total estimated tax
        total_tax = sum(
            status["estimated_tax_mw"] for status in daemon_status.values() if status["on_p_cores"]
        )
        analysis["total_estimated_tax_mw"] = total_tax

        if total_tax > 0:
            analysis["warnings"].append(
                f"⚠️  Estimated Power Tax: {total_tax:.1f} mW " f"from daemons on P-cores"
            )

            # Calculate AR impact if stressed power available
            if stressed_power:
                ar_impact = calculate_ar_impact(baseline_power, stressed_power, total_tax)
                analysis["ar_impact"] = ar_impact

                if ar_impact["ar_reduction_pct"] > 5:
                    analysis["warnings"].append(
                        f"🚨 AR artificially low: {ar_impact['ar_with_tax_pct']:.1f}% "
                        f"(would be {ar_impact['ar_normal_pct']:.1f}% without tax, "
                        f"reduction: {ar_impact['ar_reduction_pct']:.1f}%)"
                    )

        # Recommendations
        if total_tax > 500:
            analysis["recommendations"].append(
                "💡 Consider moving background daemons to E-cores using taskpolicy"
            )
            analysis["recommendations"].append(
                "💡 High baseline may indicate inefficient P-core usage"
            )
        else:
            analysis["recommendations"].append(
                "💡 Baseline is high but may be normal for your system"
            )
    else:
        analysis["warnings"].append(f"✅ Baseline power is normal: {baseline_power:.1f} mW")

    return analysis


def print_analysis_report(analysis: Dict):
    """Print a formatted analysis report."""
    print("\n" + "=" * 70)
    print("🔍 INTELLIGENT BASELINE ANALYSIS")
    print("=" * 70)
    print()

    print(f"📊 Baseline Power: {analysis['baseline_power_mw']:.1f} mW")
    print()

    if analysis["warnings"]:
        print("⚠️  Warnings:")
        for warning in analysis["warnings"]:
            print(f"   {warning}")
        print()

    if analysis["daemons_on_p_cores"]:
        print("🔍 Daemon Status:")
        for daemon, status in analysis["daemons_on_p_cores"].items():
            if status["on_p_cores"]:
                print(f"   {daemon}: ⚠️  On P-cores (Tax: {status['estimated_tax_mw']:.1f} mW)")
            else:
                print(f"   {daemon}: ✅ On E-cores (normal)")
        print()

    if analysis.get("ar_impact"):
        ar = analysis["ar_impact"]
        print("📈 Attribution Ratio Impact:")
        print(f"   Normal AR:     {ar['ar_normal_pct']:.1f}%")
        print(f"   With Tax AR:   {ar['ar_with_tax_pct']:.1f}%")
        print(f"   AR Reduction:  {ar['ar_reduction_pct']:.1f}%")
        print()

    if analysis["recommendations"]:
        print("💡 Recommendations:")
        for rec in analysis["recommendations"]:
            print(f"   {rec}")
        print()

    print("=" * 70)


def main():
    """CLI interface for baseline analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Intelligent Baseline Detector - Auto-detect P-core usage and AR impact"
    )
    parser.add_argument("--baseline", type=float, required=True, help="Baseline power in mW")
    parser.add_argument("--stressed", type=float, help="Stressed power in mW (for AR calculation)")
    parser.add_argument(
        "--threshold",
        type=float,
        default=800.0,
        help="High baseline threshold in mW (default: 800)",
    )

    args = parser.parse_args()

    analysis = analyze_baseline(args.baseline, args.stressed)
    print_analysis_report(analysis)

    return 0


if __name__ == "__main__":
    sys.exit(main())
