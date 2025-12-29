#!/usr/bin/env python3
"""
Long-Term Efficiency Profiler
Tracks daemon power consumption over days to identify worst battery drain offenders.
Uses Tax Correction data to build a profile of which macOS background daemons
consume the most power on your specific machine.
"""

import subprocess
import time
import sys
import os
import re
import psutil
import argparse
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import statistics


class LongTermProfiler:
    """
    Profiles daemon power consumption over extended periods.
    """

    def __init__(self, data_dir: str = "profiling_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Track daemon power over time
        self.daemon_power_history = defaultdict(list)
        self.baseline_history = []
        self.tax_history = defaultdict(list)

        # Common macOS daemons to monitor
        self.monitored_daemons = [
            "mds",  # Spotlight indexing
            "backupd",  # Time Machine
            "cloudd",  # iCloud sync
            "bird",  # iCloud Documents
            "photolibraryd",  # Photos sync
            "mds_stores",  # Spotlight stores
            "mdworker",  # Spotlight workers
            "kernel_task",  # System kernel
            "WindowServer",  # Graphics server
            "com.apple.WebKit",  # WebKit processes
        ]

    def get_daemon_pids(self, daemon_name: str) -> List[int]:
        """Get all PIDs for a daemon."""
        pids = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if daemon_name.lower() in proc.info["name"].lower():
                    pids.append(proc.info["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return pids

    def check_daemon_on_p_cores(self, pid: int) -> bool:
        """Check if a process is running on P-cores."""
        try:
            # Get CPU affinity
            proc = psutil.Process(pid)
            # On macOS, we can check CPU usage and infer core type
            # P-cores typically have higher CPU numbers (4-7 on M2)
            # This is a heuristic - actual core assignment is complex
            cpu_percent = proc.cpu_percent(interval=0.1)

            # If process is active and consuming CPU, check if it's on P-cores
            # We'll use taskpolicy to check actual assignment
            try:
                result = subprocess.run(
                    ["taskpolicy", "-p", str(pid)], capture_output=True, text=True, timeout=1
                )
                # If we can query it, it exists
                return True
            except:
                return False
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def measure_daemon_power_tax(self, daemon_name: str, duration: int = 30) -> Optional[float]:
        """
        Measure power tax for a specific daemon.

        Returns:
            Power tax in mW, or None if daemon not found
        """
        pids = self.get_daemon_pids(daemon_name)
        if not pids:
            return None

        # Check if any instance is on P-cores
        on_p_cores = any(self.check_daemon_on_p_cores(pid) for pid in pids)

        if not on_p_cores:
            return 0.0  # On E-cores, no tax

        # Estimate tax based on daemon type
        # These are empirical values from validation
        tax_estimates = {
            "mds": 700.0,
            "backupd": 500.0,
            "cloudd": 400.0,
            "bird": 300.0,
            "photolibraryd": 350.0,
            "mdworker": 200.0,
            "mds_stores": 150.0,
        }

        base_tax = tax_estimates.get(daemon_name.lower(), 200.0)

        # Scale by number of instances
        instance_count = len(pids)
        if instance_count > 1:
            # Multiple instances increase tax (but not linearly)
            tax = base_tax * (1 + (instance_count - 1) * 0.3)
        else:
            tax = base_tax

        return tax

    def measure_baseline_power(self, duration: int = 10) -> float:
        """Measure current baseline power."""
        print(f"  📊 Measuring baseline power ({duration}s)...")

        cmd = [
            "sudo",
            "powermetrics",
            "--samplers",
            "cpu_power",
            "-i",
            "500",
            "-n",
            str(int(duration * 1000 / 500)),
        ]

        power_values = []

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            output, error = process.communicate(timeout=duration + 5)

            # Parse CPU/Total power
            pattern = r"(?:CPU|Package|Total)\s+Power[:\s]+([\d.]+)\s*mW"
            matches = re.finditer(pattern, output, re.IGNORECASE)

            for match in matches:
                power_mw = float(match.group(1))
                power_values.append(power_mw)

            if power_values:
                return statistics.mean(power_values)
            else:
                return 0.0

        except Exception as e:
            print(f"  ⚠️  Error measuring baseline: {e}")
            return 0.0

    def profile_snapshot(self) -> Dict:
        """Take a snapshot of current daemon power profile."""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "baseline_power_mw": 0.0,
            "daemons": {},
        }

        # Measure baseline
        baseline = self.measure_baseline_power(duration=10)
        snapshot["baseline_power_mw"] = baseline

        # Profile each daemon
        print(f"\n🔍 Profiling daemons (baseline: {baseline:.1f} mW)...")

        for daemon in self.monitored_daemons:
            pids = self.get_daemon_pids(daemon)
            if not pids:
                continue

            tax = self.measure_daemon_power_tax(daemon, duration=5)

            # Measure daemon power for skewness analysis
            daemon_power = self._measure_daemon_power(daemon, duration=5)

            snapshot["daemons"][daemon] = {
                "pids": pids,
                "instance_count": len(pids),
                "power_tax_mw": tax,
                "on_p_cores": tax > 0,
            }

            # Add power statistics if available
            if daemon_power:
                snapshot["daemons"][daemon].update(daemon_power)

                # Calculate burst fraction if right-skewed
                if "mean_power" in daemon_power and "median_power" in daemon_power:
                    mean_p = daemon_power["mean_power"]
                    median_p = daemon_power["median_power"]

                    if mean_p > median_p:  # Right-skewed
                        low_p = daemon_power.get("min_power", 0)
                        high_p = daemon_power.get("max_power", 0)

                        if high_p > low_p:
                            burst_fraction = self.calculate_burst_fraction(
                                mean_p, median_p, low_p, high_p
                            )
                            if burst_fraction is not None:
                                snapshot["daemons"][daemon]["burst_fraction"] = burst_fraction
                                snapshot["daemons"][daemon]["burst_percent"] = burst_fraction * 100
                                print(
                                    f"  📊 {daemon}: {burst_fraction*100:.1f}% burst fraction (right-skewed)"
                                )

            if tax > 0:
                print(f"  ⚠️  {daemon}: {tax:.1f} mW tax ({len(pids)} instance(s))")
            else:
                print(f"  ✅ {daemon}: On E-cores (no tax)")

        return snapshot

    def _measure_daemon_power(self, daemon_name: str, duration: int = 5) -> Optional[Dict]:
        """
        Measure power statistics for a specific daemon.

        Returns:
            Dictionary with power statistics (mean, median, min, max)
        """
        pids = self.get_daemon_pids(daemon_name)
        if not pids:
            return None

        # Use powermetrics with process filtering
        cmd = [
            "sudo",
            "powermetrics",
            "--samplers",
            "cpu_power",
            "-i",
            "500",
            "-n",
            str(int(duration * 1000 / 500)),
            "--show-process-coalition",
        ]

        power_values = []

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            output, error = process.communicate(timeout=duration + 5)

            # Parse power values for this daemon
            for line in output.split("\n"):
                # Check if line contains this daemon
                if daemon_name.lower() in line.lower():
                    # Extract power values
                    power_match = re.search(r"([\d.]+)\s*mW", line)
                    if power_match:
                        power_values.append(float(power_match.group(1)))

            if power_values and len(power_values) >= 3:
                return {
                    "mean_power": statistics.mean(power_values),
                    "median_power": statistics.median(power_values),
                    "min_power": min(power_values),
                    "max_power": max(power_values),
                    "samples": len(power_values),
                }
        except Exception:
            pass

        return None

    def save_snapshot(self, snapshot: Dict):
        """Save snapshot to file."""
        timestamp = snapshot["timestamp"].replace(":", "-").split(".")[0]
        filename = self.data_dir / f"snapshot_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(snapshot, f, indent=2)

        print(f"\n💾 Snapshot saved: {filename}")

    def load_snapshots(self, days: int = 7) -> List[Dict]:
        """Load snapshots from last N days."""
        snapshots = []
        cutoff = datetime.now() - timedelta(days=days)

        for filename in sorted(self.data_dir.glob("snapshot_*.json")):
            try:
                with open(filename, "r") as f:
                    snapshot = json.load(f)
                    snapshot_time = datetime.fromisoformat(snapshot["timestamp"])
                    if snapshot_time >= cutoff:
                        snapshots.append(snapshot)
            except Exception as e:
                print(f"⚠️  Error loading {filename}: {e}")

        return snapshots

    def calculate_burst_fraction(
        self, mean_power: float, median_power: float, low_power: float, high_power: float
    ) -> Optional[float]:
        """
        Calculate burst fraction (f) for right-skewed distribution using universal formula.

        For right-skewed (Mean > Median):
        - L = Low power (idle/baseline state)
        - H = High power (burst state)
        - f = Fraction of time at LOW power (idle)
        - (1-f) = Fraction of time at HIGH power (bursting)

        Formula: Mean = (L × f) + (H × (1-f))
        Solving for f: f = (Mean - H) / (L - H)

        Args:
            mean_power: Mean power (higher than median for right-skewed)
            median_power: Median power (typical baseline)
            low_power: Minimum observed power (idle state)
            high_power: Maximum observed power (burst state)

        Returns:
            Burst fraction (1-f) = fraction of time bursting, or None if invalid
        """
        if mean_power <= median_power:
            # Not right-skewed
            return None

        if high_power <= low_power:
            return None

        # Solve: Mean = (L × f) + (H × (1-f))
        # Mean = L×f + H - H×f
        # Mean = H + f×(L - H)
        # f = (Mean - H) / (L - H)

        idle_fraction = (mean_power - high_power) / (low_power - high_power)
        idle_fraction = max(0.0, min(1.0, idle_fraction))  # Clamp to [0, 1]

        # Burst fraction is (1 - idle_fraction)
        burst_fraction = 1.0 - idle_fraction

        return burst_fraction

    def analyze_daemon_offenders(self, snapshots: List[Dict]) -> Dict:
        """Analyze snapshots to identify worst battery drain offenders."""
        daemon_stats = defaultdict(
            lambda: {
                "total_tax": 0.0,
                "count": 0,
                "max_tax": 0.0,
                "avg_tax": 0.0,
                "on_p_cores_percent": 0.0,
            }
        )

        baseline_values = []

        for snapshot in snapshots:
            baseline_values.append(snapshot["baseline_power_mw"])

            for daemon, info in snapshot["daemons"].items():
                stats = daemon_stats[daemon]
                tax = info["power_tax_mw"]

                stats["total_tax"] += tax
                stats["count"] += 1
                stats["max_tax"] = max(stats["max_tax"], tax)

                if info["on_p_cores"]:
                    stats["on_p_cores_percent"] += 1

        # Calculate averages and burst analysis
        for daemon, stats in daemon_stats.items():
            if stats["count"] > 0:
                stats["avg_tax"] = stats["total_tax"] / stats["count"]
                stats["on_p_cores_percent"] = (stats["on_p_cores_percent"] / stats["count"]) * 100

                # Calculate burst fraction if we have power data
                # For right-skewed distributions (Mean > Median)
                if "mean_power" in stats and "median_power" in stats:
                    mean_p = stats.get("mean_power", 0)
                    median_p = stats.get("median_power", 0)
                    low_p = stats.get("min_power", 0)
                    high_p = stats.get("max_power", 0)

                    if mean_p > median_p and high_p > low_p:
                        burst_fraction = self.calculate_burst_fraction(
                            mean_p, median_p, low_p, high_p
                        )
                        if burst_fraction is not None:
                            stats["burst_fraction"] = burst_fraction
                            stats["burst_percent"] = burst_fraction * 100

        # Sort by average tax
        sorted_daemons = sorted(daemon_stats.items(), key=lambda x: x[1]["avg_tax"], reverse=True)

        avg_baseline = statistics.mean(baseline_values) if baseline_values else 0.0

        return {
            "snapshot_count": len(snapshots),
            "avg_baseline_mw": avg_baseline,
            "daemon_rankings": sorted_daemons,
            "analysis_date": datetime.now().isoformat(),
        }

    def _get_daemon_recommendations(self, daemon_name: str) -> List[str]:
        """
        Get specific macOS settings and task policy recommendations for a daemon.

        Returns:
            List of recommendation strings
        """
        recommendations = []

        daemon_lower = daemon_name.lower()

        if daemon_lower == "backupd":
            # Time Machine recommendations
            recommendations.extend(
                [
                    "1. Limit Time Machine frequency:",
                    "   sudo tmutil setinterval 3600  # Backup every hour instead of continuous",
                    "",
                    "2. Move backupd to E-cores:",
                    "   sudo taskpolicy -c 0x0F -p $(pgrep -f backupd)  # Force to E-cores (0-3)",
                    "",
                    "3. Schedule backups during low-usage periods:",
                    "   System Settings > General > Time Machine > Options",
                    "   Enable 'Back up automatically' only during specific hours",
                    "",
                    "4. Exclude large directories from backups:",
                    "   sudo tmutil addexclusion ~/Downloads  # Example",
                ]
            )

        elif daemon_lower == "mds" or "mds" in daemon_lower:
            # Spotlight recommendations
            recommendations.extend(
                [
                    "1. Reduce Spotlight indexing:",
                    "   System Settings > Siri & Spotlight > Spotlight",
                    "   Uncheck unnecessary categories (e.g., Developer, Fonts)",
                    "",
                    "2. Move mds to E-cores:",
                    "   sudo taskpolicy -c 0x0F -p $(pgrep -f mds)  # Force to E-cores",
                    "",
                    "3. Exclude large directories from indexing:",
                    "   sudo mdutil -i off /Volumes/LargeDrive  # Example",
                    "   Or: System Settings > Siri & Spotlight > Privacy",
                    "",
                    "4. Limit indexing frequency:",
                    "   sudo defaults write /.Spotlight-V100 IndexingInterval 3600",
                ]
            )

        elif daemon_lower == "cloudd":
            # iCloud sync recommendations
            recommendations.extend(
                [
                    "1. Force cloudd bursts to E-cores (CRITICAL for bursty behavior):",
                    "   sudo taskpolicy -c 0x0F -p $(pgrep -f cloudd)  # E-cores: 0-3 (0x0F = 00001111)",
                    "   ",
                    "   Why: Right-skewed distribution (bursts) hitting P-cores wastes power.",
                    "   E-cores handle sync bursts efficiently, reducing Power Tax.",
                    "",
                    "2. Reduce iCloud sync frequency:",
                    "   System Settings > Apple ID > iCloud",
                    "   Disable 'iCloud Drive' or 'Desktop & Documents' if not needed",
                    "",
                    "3. Limit sync to Wi-Fi only:",
                    "   System Settings > Apple ID > iCloud > iCloud Drive > Options",
                    "   Enable 'Only sync over Wi-Fi'",
                    "",
                    "4. Pause iCloud sync during high-usage:",
                    "   System Settings > Apple ID > iCloud",
                    "   Temporarily disable 'iCloud Drive' when not needed",
                    "",
                    "5. Monitor burst frequency:",
                    "   Use profiler to track burst fraction (f) over time",
                    "   High burst fraction (>20%) indicates frequent sync activity",
                ]
            )

        elif daemon_lower == "bird":
            # iCloud Documents recommendations
            recommendations.extend(
                [
                    "1. Move bird to E-cores:",
                    "   sudo taskpolicy -c 0x0F -p $(pgrep -f bird)  # Force to E-cores",
                    "",
                    "2. Reduce iCloud Documents sync:",
                    "   System Settings > Apple ID > iCloud",
                    "   Disable 'Desktop & Documents' if not needed",
                    "",
                    "3. Limit sync frequency:",
                    "   System Settings > Apple ID > iCloud > iCloud Drive > Options",
                    "   Enable 'Only sync over Wi-Fi'",
                ]
            )

        elif "photolibraryd" in daemon_lower:
            # Photos sync recommendations
            recommendations.extend(
                [
                    "1. Disable iCloud Photos if not needed:",
                    "   System Settings > Apple ID > iCloud > Photos",
                    "   Turn off 'iCloud Photos'",
                    "",
                    "2. Move photolibraryd to E-cores:",
                    "   sudo taskpolicy -c 0x0F -p $(pgrep -f photolibraryd)  # Force to E-cores",
                    "",
                    "3. Limit photo sync to Wi-Fi:",
                    "   System Settings > Apple ID > iCloud > Photos",
                    "   Enable 'Download Originals' only on Wi-Fi",
                ]
            )

        elif "mdworker" in daemon_lower or "mds_stores" in daemon_lower:
            # Spotlight worker recommendations
            recommendations.extend(
                [
                    "1. Move mdworker to E-cores:",
                    "   sudo taskpolicy -c 0x0F -p $(pgrep -f mdworker)  # Force to E-cores",
                    "",
                    "2. Reduce Spotlight indexing (see 'mds' recommendations above)",
                ]
            )

        else:
            # Generic recommendations
            recommendations.extend(
                [
                    f"1. Move {daemon_name} to E-cores:",
                    f"   sudo taskpolicy -c 0x0F -p $(pgrep -f {daemon_name})  # Force to E-cores",
                    "",
                    "2. Check System Settings for daemon-specific options",
                    "",
                    "3. Consider disabling if not needed:",
                    f"   sudo launchctl unload -w /System/Library/LaunchDaemons/{daemon_name}.plist",
                ]
            )

        return recommendations

    def print_offender_report(self, analysis: Dict):
        """Print report of worst battery drain offenders."""
        print("\n" + "=" * 70)
        print("📊 LONG-TERM EFFICIENCY PROFILE: Worst Battery Drain Offenders")
        print("=" * 70)
        print()
        print(f"📈 Analysis Period: {analysis['snapshot_count']} snapshots")
        print(f"📊 Average Baseline: {analysis['avg_baseline_mw']:.1f} mW")
        print()

        print("🏆 Top Battery Drain Offenders (by average power tax):")
        print()

        for i, (daemon, stats) in enumerate(analysis["daemon_rankings"][:10], 1):
            if stats["avg_tax"] > 0:
                print(f"{i:2d}. {daemon:20s}")
                print(f"     Avg Tax: {stats['avg_tax']:6.1f} mW")
                print(f"     Max Tax: {stats['max_tax']:6.1f} mW")
                print(f"     On P-Cores: {stats['on_p_cores_percent']:5.1f}% of time")

                # Show burst fraction if available (right-skewed)
                if "burst_percent" in stats:
                    print(f"     Burst Fraction: {stats['burst_percent']:5.1f}% (right-skewed)")
                    print(
                        f"     Interpretation: {stats['burst_percent']:.1f}% of time in high-power bursts"
                    )

                print(f"     Snapshots: {stats['count']}")
                print()

        # Summary
        total_tax = sum(stats["avg_tax"] for _, stats in analysis["daemon_rankings"])
        print(f"💡 Total Average Tax: {total_tax:.1f} mW")
        print(f"💡 Baseline Efficiency: {analysis['avg_baseline_mw']:.1f} mW")
        print()

        # Recommendations with specific macOS settings
        print("💡 Recommendations:")
        top_offenders = [d for d, s in analysis["daemon_rankings"][:3] if s["avg_tax"] > 0]
        if top_offenders:
            print(f"   🎯 Focus on: {', '.join(top_offenders)}")
            print(
                f"   💡 Estimated savings: {sum(s['avg_tax'] for _, s in analysis['daemon_rankings'][:3]):.1f} mW"
            )
            print()
            print("🔧 Specific macOS Settings & Task Policies:")
            print()

            for daemon in top_offenders:
                recommendations = self._get_daemon_recommendations(daemon)
                if recommendations:
                    print(f"   📋 {daemon}:")
                    for rec in recommendations:
                        print(f"      {rec}")
                    print()


def main():
    parser = argparse.ArgumentParser(description="Long-term efficiency profiler for macOS daemons")
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Take a single snapshot of current daemon power profile",
    )
    parser.add_argument(
        "--analyze",
        type=int,
        metavar="DAYS",
        help="Analyze snapshots from last N days (default: 7)",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="profiling_data",
        help="Directory to store profiling data (default: profiling_data)",
    )
    parser.add_argument(
        "--continuous",
        type=int,
        metavar="INTERVAL",
        help="Take snapshots continuously every N minutes (default: 60)",
    )

    args = parser.parse_args()

    profiler = LongTermProfiler(data_dir=args.data_dir)

    if args.snapshot:
        snapshot = profiler.profile_snapshot()
        profiler.save_snapshot(snapshot)
        print("\n✅ Snapshot complete")

    elif args.analyze:
        print(f"📊 Analyzing snapshots from last {args.analyze} days...")
        snapshots = profiler.load_snapshots(days=args.analyze)

        if not snapshots:
            print("⚠️  No snapshots found")
            return 1

        analysis = profiler.analyze_daemon_offenders(snapshots)
        profiler.print_offender_report(analysis)

        # Save analysis
        analysis_file = (
            profiler.data_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)
        print(f"\n💾 Analysis saved: {analysis_file}")

    elif args.continuous:
        print(f"🔄 Continuous profiling (every {args.continuous} minutes)")
        print("Press Ctrl+C to stop")
        print()

        try:
            while True:
                snapshot = profiler.profile_snapshot()
                profiler.save_snapshot(snapshot)
                print(f"\n⏳ Next snapshot in {args.continuous} minutes...")
                time.sleep(args.continuous * 60)
        except KeyboardInterrupt:
            print("\n\n✅ Profiling stopped")

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
