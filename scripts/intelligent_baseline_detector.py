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
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if daemon_name.lower() in proc.info['name'].lower():
                pids.append(proc.info['pid'])
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
        'mds': 700.0,
        'backupd': 600.0,
        'cloudd': 500.0,
        'kernel_task': 400.0,
    }
    
    return tax_estimates.get(daemon_name.lower(), 500.0)  # Default estimate


def detect_high_baseline(baseline_power: float, threshold: float = 800.0) -> bool:
    """
    Detect if baseline power is suspiciously high.
    Returns True if baseline exceeds threshold.
    """
    return baseline_power > threshold


def check_daemons_on_p_cores(common_daemons: List[str] = ['mds', 'backupd', 'cloudd']) -> Dict[str, Dict]:
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
            'pids': pids,
            'on_p_cores': on_p_cores,
            'estimated_tax_mw': estimated_tax
        }
    
    return results


def calculate_ar_impact(baseline_power: float, stressed_power: float, power_tax: float) -> Dict[str, float]:
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
        'baseline_normal_mw': baseline_power,
        'baseline_with_tax_mw': baseline_with_tax,
        'stressed_power_mw': stressed_power,
        'ar_normal_pct': ar_normal,
        'ar_with_tax_pct': ar_with_tax,
        'ar_reduction_pct': ar_reduction,
        'power_tax_mw': power_tax
    }


def analyze_baseline(baseline_power: float, stressed_power: Optional[float] = None) -> Dict:
    """
    Analyze baseline power and provide intelligent warnings.
    
    Returns:
        Dictionary with analysis results and warnings
    """
    analysis = {
        'baseline_power_mw': baseline_power,
        'high_baseline': detect_high_baseline(baseline_power),
        'daemons_on_p_cores': {},
        'total_estimated_tax_mw': 0.0,
        'warnings': [],
        'recommendations': []
    }
    
    # Check if baseline is high
    if analysis['high_baseline']:
        analysis['warnings'].append(
            f"⚠️  High baseline power detected: {baseline_power:.1f} mW "
            f"(threshold: 800 mW)"
        )
        
        # Check daemons
        daemon_status = check_daemons_on_p_cores()
        analysis['daemons_on_p_cores'] = daemon_status
        
        # Calculate total estimated tax
        total_tax = sum(
            status['estimated_tax_mw'] 
            for status in daemon_status.values() 
            if status['on_p_cores']
        )
        analysis['total_estimated_tax_mw'] = total_tax
        
        if total_tax > 0:
            analysis['warnings'].append(
                f"⚠️  Estimated Power Tax: {total_tax:.1f} mW "
                f"from daemons on P-cores"
            )
            
            # Calculate AR impact if stressed power available
            if stressed_power:
                ar_impact = calculate_ar_impact(baseline_power, stressed_power, total_tax)
                analysis['ar_impact'] = ar_impact
                
                if ar_impact['ar_reduction_pct'] > 5:
                    analysis['warnings'].append(
                        f"🚨 AR artificially low: {ar_impact['ar_with_tax_pct']:.1f}% "
                        f"(would be {ar_impact['ar_normal_pct']:.1f}% without tax, "
                        f"reduction: {ar_impact['ar_reduction_pct']:.1f}%)"
                    )
        
        # Recommendations
        if total_tax > 500:
            analysis['recommendations'].append(
                "💡 Consider moving background daemons to E-cores using taskpolicy"
            )
            analysis['recommendations'].append(
                "💡 High baseline may indicate inefficient P-core usage"
            )
        else:
            analysis['recommendations'].append(
                "💡 Baseline is high but may be normal for your system"
            )
    else:
        analysis['warnings'].append(
            f"✅ Baseline power is normal: {baseline_power:.1f} mW"
        )
    
    return analysis


def print_analysis_report(analysis: Dict):
    """Print a formatted analysis report."""
    print("\n" + "=" * 70)
    print("🔍 INTELLIGENT BASELINE ANALYSIS")
    print("=" * 70)
    print()
    
    print(f"📊 Baseline Power: {analysis['baseline_power_mw']:.1f} mW")
    print()
    
    if analysis['warnings']:
        print("⚠️  Warnings:")
        for warning in analysis['warnings']:
            print(f"   {warning}")
        print()
    
    if analysis['daemons_on_p_cores']:
        print("🔍 Daemon Status:")
        for daemon, status in analysis['daemons_on_p_cores'].items():
            if status['on_p_cores']:
                print(f"   {daemon}: ⚠️  On P-cores (Tax: {status['estimated_tax_mw']:.1f} mW)")
            else:
                print(f"   {daemon}: ✅ On E-cores (normal)")
        print()
    
    if analysis.get('ar_impact'):
        ar = analysis['ar_impact']
        print("📈 Attribution Ratio Impact:")
        print(f"   Normal AR:     {ar['ar_normal_pct']:.1f}%")
        print(f"   With Tax AR:   {ar['ar_with_tax_pct']:.1f}%")
        print(f"   AR Reduction:  {ar['ar_reduction_pct']:.1f}%")
        print()
    
    if analysis['recommendations']:
        print("💡 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"   {rec}")
        print()
    
    print("=" * 70)


def main():
    """CLI interface for baseline analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Intelligent Baseline Detector - Auto-detect P-core usage and AR impact'
    )
    parser.add_argument(
        '--baseline',
        type=float,
        required=True,
        help='Baseline power in mW'
    )
    parser.add_argument(
        '--stressed',
        type=float,
        help='Stressed power in mW (for AR calculation)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=800.0,
        help='High baseline threshold in mW (default: 800)'
    )
    
    args = parser.parse_args()
    
    analysis = analyze_baseline(args.baseline, args.stressed)
    print_analysis_report(analysis)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

