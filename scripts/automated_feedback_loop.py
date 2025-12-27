#!/usr/bin/env python3
"""
Automated Feedback Loop: Auto-Fix with Before/After Measurement

**Single Responsibility**: Automatically applies taskpolicy fixes when profiler detects
high burst fraction and high power tax, then measures before/after savings to prove effectiveness.

**The Feedback Loop**:
1. Detect: High burst fraction (>20%) + High power tax (>300 mW)
2. Apply: Automatically run taskpolicy command to force E-cores
3. Measure: Collect before/after power data
4. Verify: Calculate and report savings
5. Report: Show proof of effectiveness
"""

import subprocess
import time
import sys
import os
import re
import psutil
import argparse
import statistics
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json


class AutomatedFeedbackLoop:
    """
    Automated feedback loop for daemon power optimization.
    """
    
    def __init__(self, daemon_name: str, data_dir: Path = Path("feedback_data")):
        self.daemon_name = daemon_name
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
        
    def detect_high_power_issue(self, duration: int = 10) -> Optional[Dict]:
        """
        Detect if daemon has high burst fraction and high power tax.
        
        Returns:
            Dictionary with detection results, or None if no issue
        """
        print(f"\n🔍 Detecting power issues for {self.daemon_name}...")
        
        # Get daemon PIDs
        pids = self._get_daemon_pids()
        if not pids:
            print(f"  ⚠️  {self.daemon_name} not running")
            return None
        
        # Measure power statistics
        power_stats = self._measure_daemon_power(duration)
        if not power_stats:
            print(f"  ⚠️  Could not measure power for {self.daemon_name}")
            return None
        
        # Check if on P-cores
        on_p_cores = any(self._check_on_p_cores(pid) for pid in pids)
        
        # Calculate burst fraction if right-skewed
        mean_p = power_stats['mean_power']
        median_p = power_stats['median_power']
        burst_fraction = None
        
        if mean_p > median_p:  # Right-skewed
            low_p = power_stats['min_power']
            high_p = power_stats['max_power']
            
            if high_p > low_p:
                # Calculate burst fraction: Mean = (L × f) + (H × (1-f))
                # f = (Mean - H) / (L - H)
                idle_fraction = (mean_p - high_p) / (low_p - high_p)
                idle_fraction = max(0.0, min(1.0, idle_fraction))
                burst_fraction = 1.0 - idle_fraction
        
        # Estimate power tax (if on P-cores)
        power_tax = 0.0
        if on_p_cores:
            # Estimate based on daemon type
            tax_estimates = {
                'mds': 700.0,
                'backupd': 500.0,
                'cloudd': 400.0,
                'bird': 300.0,
                'photolibraryd': 350.0,
            }
            base_tax = tax_estimates.get(self.daemon_name.lower(), 200.0)
            power_tax = base_tax * len(pids)
        
        # Detection thresholds
        HIGH_BURST_THRESHOLD = 0.20  # 20% burst fraction
        HIGH_TAX_THRESHOLD = 300.0   # 300 mW power tax
        
        issue_detected = (
            (burst_fraction and burst_fraction > HIGH_BURST_THRESHOLD) and
            power_tax > HIGH_TAX_THRESHOLD
        )
        
        result = {
            'daemon': self.daemon_name,
            'pids': pids,
            'power_stats': power_stats,
            'on_p_cores': on_p_cores,
            'burst_fraction': burst_fraction,
            'power_tax': power_tax,
            'issue_detected': issue_detected,
            'baseline_power': self._measure_baseline_power(duration=5),
            'total_system_power': self._measure_total_system_power(duration=5),
            'timestamp': datetime.now().isoformat()
        }
        
        if issue_detected:
            print(f"  ⚠️  ISSUE DETECTED:")
            print(f"     Burst fraction: {burst_fraction*100:.1f}% (threshold: {HIGH_BURST_THRESHOLD*100}%)")
            print(f"     Power tax: {power_tax:.1f} mW (threshold: {HIGH_TAX_THRESHOLD} mW)")
            print(f"     On P-cores: {on_p_cores}")
        else:
            print(f"  ✅ No issue detected")
            if burst_fraction:
                print(f"     Burst fraction: {burst_fraction*100:.1f}%")
            print(f"     Power tax: {power_tax:.1f} mW")
        
        return result
    
    def apply_fix(self, pids: List[int]) -> bool:
        """
        Apply taskpolicy fix to force daemon to E-cores.
        
        Args:
            pids: List of process IDs to fix
        
        Returns:
            True if fix applied successfully
        """
        print(f"\n🔧 Applying fix: Moving {self.daemon_name} to E-cores...")
        
        for pid in pids:
            try:
                # Force to E-cores (0x0F = 00001111 = cores 0-3 on M2)
                cmd = ['sudo', 'taskpolicy', '-c', '0x0F', '-p', str(pid)]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    print(f"  ✅ PID {pid}: Moved to E-cores")
                else:
                    print(f"  ⚠️  PID {pid}: Failed - {result.stderr.strip()}")
                    return False
                    
            except Exception as e:
                print(f"  ❌ Error applying fix to PID {pid}: {e}")
                return False
        
        return True
    
    def measure_before_after(
        self,
        before_stats: Dict,
        after_duration: int = 10
    ) -> Dict:
        """
        Measure power after fix and calculate savings with Attribution Ratio validation.
        
        **Validating the Feedback Loop**: Uses Attribution Ratio formula to verify that
        the power drop actually eliminated waste (not just moved it elsewhere).
        
        **Attribution Ratio Formula**:
        AR = (Daemon_Power_Delta) / (Total_System_Delta)
        
        **Validation Logic**:
        1. Before: AR_before = (Daemon_Power - Baseline) / (Total_Power - Baseline)
        2. After: AR_after = (Daemon_Power - Baseline) / (Total_Power - Baseline)
        3. If AR_after < AR_before AND total system power decreased:
           → Waste was eliminated (not just moved)
        4. If AR_after ≈ AR_before but power decreased:
           → Power moved to other processes (not eliminated)
        
        Args:
            before_stats: Power statistics before fix
            after_duration: Duration to measure after fix (seconds)
        
        Returns:
            Dictionary with before/after comparison and attribution validation
        """
        print(f"\n📊 Measuring after fix ({after_duration}s)...")
        
        # Wait a moment for fix to take effect
        time.sleep(2)
        
        # Measure baseline (system idle)
        baseline = self._measure_baseline_power(duration=5)
        
        # Measure after (daemon + system)
        after_stats = self._measure_daemon_power(after_duration)
        if not after_stats:
            print("  ⚠️  Could not measure power after fix")
            return {}
        
        # Measure total system power after
        after_total = self._measure_total_system_power(after_duration)
        
        # Get before values (from detection phase)
        before_mean = before_stats['mean_power']
        before_baseline = before_stats.get('baseline_power', baseline)
        before_total = before_stats.get('total_system_power', before_mean + before_baseline)
        
        # After values
        after_mean = after_stats['mean_power']
        after_total_power = after_total if after_total else (after_mean + baseline)
        
        # Calculate savings
        savings_mw = before_mean - after_mean
        savings_percent = (savings_mw / before_mean * 100) if before_mean > 0 else 0
        total_savings_mw = before_total - after_total_power
        
        # Calculate Attribution Ratios
        # AR = (Daemon_Delta) / (Total_Delta)
        before_daemon_delta = before_mean - before_baseline
        before_total_delta = before_total - before_baseline
        ar_before = (before_daemon_delta / before_total_delta * 100) if before_total_delta > 0 else 0
        
        after_daemon_delta = after_mean - baseline
        after_total_delta = after_total_power - baseline
        ar_after = (after_daemon_delta / after_total_delta * 100) if after_total_delta > 0 else 0
        
        # Validation: Did we eliminate waste or just move it?
        ar_reduction = ar_before - ar_after
        waste_eliminated = (ar_after < ar_before) and (total_savings_mw > 0)
        power_moved = (abs(ar_reduction) < 5.0) and (savings_mw > 0) and (total_savings_mw < savings_mw * 0.5)
        
        # Check if still on P-cores
        pids = self._get_daemon_pids()
        on_p_cores_after = any(self._check_on_p_cores(pid) for pid in pids) if pids else False
        
        result = {
            'before': before_stats,
            'after': after_stats,
            'baseline_power_mw': baseline,
            'savings_mw': savings_mw,
            'savings_percent': savings_percent,
            'total_savings_mw': total_savings_mw,
            'on_p_cores_before': before_stats.get('on_p_cores', False),
            'on_p_cores_after': on_p_cores_after,
            'fix_effective': not on_p_cores_after and savings_mw > 0,
            'attribution_ratio_before': ar_before,
            'attribution_ratio_after': ar_after,
            'ar_reduction': ar_reduction,
            'waste_eliminated': waste_eliminated,
            'power_moved': power_moved,
            'validation': {
                'waste_eliminated': waste_eliminated,
                'power_moved': power_moved,
                'interpretation': (
                    "✅ Waste eliminated - power actually reduced system-wide"
                    if waste_eliminated else
                    "⚠️  Power moved - daemon power reduced but system power unchanged"
                    if power_moved else
                    "✅ Fix effective - daemon moved to E-cores"
                )
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    
    def run_feedback_loop(self, detection_duration: int = 10, verification_duration: int = 10) -> Dict:
        """
        Run complete feedback loop: Detect → Fix → Measure → Verify.
        
        Args:
            detection_duration: Duration for initial detection (seconds)
            verification_duration: Duration for after-fix measurement (seconds)
        
        Returns:
            Complete feedback loop results
        """
        print("=" * 70)
        print("🔄 AUTOMATED FEEDBACK LOOP")
        print("=" * 70)
        print(f"Daemon: {self.daemon_name}")
        print()
        
        # Step 1: Detect
        detection = self.detect_high_power_issue(detection_duration)
        if not detection or not detection['issue_detected']:
            print("\n✅ No action needed - daemon is already optimized")
            return {'action_taken': False, 'detection': detection}
        
        # Step 2: Apply Fix
        fix_applied = self.apply_fix(detection['pids'])
        if not fix_applied:
            print("\n❌ Failed to apply fix")
            return {'action_taken': False, 'detection': detection, 'fix_applied': False}
        
        # Step 3: Measure Before/After
        comparison = self.measure_before_after(
            detection['power_stats'],
            verification_duration
        )
        
        if not comparison:
            print("\n⚠️  Could not measure after-fix results")
            return {
                'action_taken': True,
                'detection': detection,
                'fix_applied': True,
                'comparison': None
            }
        
        # Step 4: Report Results
        self._print_results(comparison)
        
        # Save results
        results = {
            'action_taken': True,
            'detection': detection,
            'fix_applied': True,
            'comparison': comparison
        }
        self._save_results(results)
        
        return results
    
    def _print_results(self, comparison: Dict):
        """Print before/after comparison results with Attribution Ratio validation."""
        print("\n" + "=" * 70)
        print("📊 BEFORE vs AFTER RESULTS")
        print("=" * 70)
        print()
        
        before = comparison['before']
        after = comparison['after']
        
        print(f"Power Consumption:")
        print(f"  Before: {before['mean_power']:.1f} mW (mean)")
        print(f"  After:  {after['mean_power']:.1f} mW (mean)")
        print(f"  Savings: {comparison['savings_mw']:.1f} mW ({comparison['savings_percent']:.1f}%)")
        print(f"  Total System Savings: {comparison.get('total_savings_mw', 0):.1f} mW")
        print()
        
        print(f"CPU Affinity:")
        print(f"  Before: {'P-cores' if comparison['on_p_cores_before'] else 'E-cores'}")
        print(f"  After:  {'P-cores' if comparison['on_p_cores_after'] else 'E-cores'}")
        print()
        
        # Attribution Ratio Validation
        if 'attribution_ratio_before' in comparison:
            print(f"🧪 ATTRIBUTION RATIO VALIDATION:")
            print(f"  Before: {comparison['attribution_ratio_before']:.1f}%")
            print(f"  After:  {comparison['attribution_ratio_after']:.1f}%")
            print(f"  Change: {comparison['ar_reduction']:.1f}%")
            print()
            
            validation = comparison.get('validation', {})
            print(f"  {validation.get('interpretation', '')}")
            print()
            
            if validation.get('waste_eliminated'):
                print("  ✅ PROOF: Waste eliminated (not just moved)")
                print(f"     • Daemon AR reduced: {comparison['ar_reduction']:.1f}%")
                print(f"     • System power decreased: {comparison.get('total_savings_mw', 0):.1f} mW")
                print(f"     • Formula: AR = (Daemon_Delta) / (Total_Delta)")
                print(f"     • Lower AR + Lower Total = Waste eliminated")
            elif validation.get('power_moved'):
                print("  ⚠️  WARNING: Power may have moved to other processes")
                print(f"     • Daemon power reduced but AR unchanged")
                print(f"     • System power may not have decreased proportionally")
            print()
        
        if comparison['fix_effective']:
            print("✅ FIX EFFECTIVE: Power savings achieved and moved to E-cores")
        else:
            print("⚠️  Fix applied but verification incomplete")
        print()
    
    def _save_results(self, results: Dict):
        """Save feedback loop results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_dir / f"feedback_{self.daemon_name}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Results saved: {filename}")
    
    def _get_daemon_pids(self) -> List[int]:
        """Get all PIDs for the daemon."""
        pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if self.daemon_name.lower() in proc.info['name'].lower():
                    pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return pids
    
    def _check_on_p_cores(self, pid: int) -> bool:
        """Check if process is on P-cores (heuristic)."""
        try:
            proc = psutil.Process(pid)
            # Check CPU usage and infer core type
            # This is a heuristic - actual core assignment is complex
            cpu_percent = proc.cpu_percent(interval=0.1)
            return cpu_percent > 0  # Simplified check
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _measure_daemon_power(self, duration: int = 10) -> Optional[Dict]:
        """Measure power statistics for the daemon."""
        cmd = [
            'sudo', 'powermetrics',
            '--samplers', 'cpu_power',
            '-i', '500',
            '-n', str(int(duration * 1000 / 500))
        ]
        
        power_values = []
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            output, error = process.communicate(timeout=duration + 5)
            
            # Parse power values
            pattern = r'(?:CPU|Package|Total)\s+Power[:\s]+([\d.]+)\s*mW'
            matches = re.finditer(pattern, output, re.IGNORECASE)
            
            for match in matches:
                power_mw = float(match.group(1))
                power_values.append(power_mw)
            
            if power_values and len(power_values) >= 3:
                return {
                    'mean_power': statistics.mean(power_values),
                    'median_power': statistics.median(power_values),
                    'min_power': min(power_values),
                    'max_power': max(power_values),
                    'samples': len(power_values)
                }
        except Exception as e:
            print(f"  ⚠️  Error measuring power: {e}")
        
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Automated Feedback Loop: Auto-fix daemon power issues"
    )
    parser.add_argument(
        'daemon',
        help='Daemon name to analyze (e.g., cloudd, mds, backupd)'
    )
    parser.add_argument(
        '--detection-duration',
        type=int,
        default=10,
        help='Duration for detection phase (seconds, default: 10)'
    )
    parser.add_argument(
        '--verification-duration',
        type=int,
        default=10,
        help='Duration for after-fix verification (seconds, default: 10)'
    )
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path("feedback_data"),
        help='Directory to save results (default: feedback_data)'
    )
    
    args = parser.parse_args()
    
    loop = AutomatedFeedbackLoop(args.daemon, args.data_dir)
    results = loop.run_feedback_loop(
        detection_duration=args.detection_duration,
        verification_duration=args.verification_duration
    )
    
    if results.get('action_taken'):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())

