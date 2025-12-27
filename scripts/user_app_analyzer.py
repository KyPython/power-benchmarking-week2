#!/usr/bin/env python3
"""
User-Facing App Analyzer: Attribution and Skewness for Applications

**Single Responsibility**: Applies the same Attribution and Skewness rules used for
system daemons to user-facing applications (web browsers, video editors, etc.) to find
"hidden" energy waste.

**Beyond the Daemon**: 
- System daemons (cloudd, mds) run in background
- User apps (Safari, Chrome, Final Cut Pro) run in foreground
- Same statistical analysis applies: attribution ratio, skewness, burst fraction
- Can identify inefficient rendering, background tabs, or hidden processes
"""

import subprocess
import time
import sys
import os
import re
import psutil
import argparse
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import statistics
import json


class UserAppAnalyzer:
    """
    Analyzes user-facing applications using attribution and skewness analysis.
    """
    
    def __init__(self, app_name: str, data_dir: Path = Path("app_analysis_data")):
        self.app_name = app_name
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
    
    def find_app_processes(self) -> List[Dict]:
        """
        Find all processes belonging to the application.
        
        Returns:
            List of process dictionaries with PID, name, and CPU usage
        """
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                proc_info = proc.info
                proc_name = proc_info['name'].lower()
                
                # Match app name (flexible matching)
                if self.app_name.lower() in proc_name or proc_name in self.app_name.lower():
                    processes.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'cpu_percent': proc_info.get('cpu_percent', 0.0),
                        'memory_mb': proc_info.get('memory_info', {}).get('rss', 0) / 1024 / 1024
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return processes
    
    def measure_app_power(
        self,
        duration: int = 30,
        sample_interval: int = 500
    ) -> Dict[str, List[float]]:
        """
        Measure power consumption for the application.
        
        Returns:
            Dictionary with power time series for CPU, ANE, GPU, Total
        """
        print(f"\n📊 Measuring power for {self.app_name} ({duration}s)...")
        
        processes = self.find_app_processes()
        if not processes:
            print(f"  ⚠️  No processes found for {self.app_name}")
            return {}
        
        print(f"  Found {len(processes)} process(es):")
        for proc in processes:
            print(f"    - {proc['name']} (PID: {proc['pid']})")
        
        # Get PIDs for filtering
        pids = [p['pid'] for p in processes]
        
        # Run powermetrics
        cmd = [
            'sudo', 'powermetrics',
            '--samplers', 'cpu_power,gpu_power',
            '-i', str(sample_interval),
            '-n', str(int(duration * 1000 / sample_interval)),
            '--show-process-coalition'
        ]
        
        cpu_power = []
        ane_power = []
        gpu_power = []
        total_power = []
        timestamps = []
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            start_time = time.time()
            
            for line in process.stdout:
                current_time = time.time() - start_time
                timestamps.append(current_time)
                
                # Check if line contains app process
                line_lower = line.lower()
                app_in_line = any(
                    self.app_name.lower() in line_lower or
                    str(pid) in line
                    for pid in pids
                )
                
                if app_in_line or 'package' in line_lower or 'total' in line_lower:
                    # Parse CPU power
                    cpu_match = re.search(r'CPU\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
                    if cpu_match:
                        cpu_power.append(float(cpu_match.group(1)))
                    
                    # Parse ANE power
                    ane_match = re.search(r'ANE\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
                    if ane_match:
                        ane_power.append(float(ane_match.group(1)))
                    
                    # Parse GPU power
                    gpu_match = re.search(r'GPU\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
                    if gpu_match:
                        gpu_power.append(float(gpu_match.group(1)))
                    
                    # Parse Total/Package power
                    total_match = re.search(
                        r'(?:Package|Total)\s+Power[:\s]+([\d.]+)\s*mW',
                        line,
                        re.IGNORECASE
                    )
                    if total_match:
                        total_power.append(float(total_match.group(1)))
            
            process.wait(timeout=duration + 5)
            
        except Exception as e:
            print(f"  ⚠️  Error measuring power: {e}")
            return {}
        
        # Align arrays (use shortest length)
        min_len = min(
            len(cpu_power) if cpu_power else 0,
            len(ane_power) if ane_power else 0,
            len(gpu_power) if gpu_power else 0,
            len(total_power) if total_power else 0
        )
        
        return {
            'cpu_power': cpu_power[:min_len] if cpu_power else [],
            'ane_power': ane_power[:min_len] if ane_power else [],
            'gpu_power': gpu_power[:min_len] if gpu_power else [],
            'total_power': total_power[:min_len] if total_power else [],
            'timestamps': timestamps[:min_len] if timestamps else [],
            'processes': processes,
            'duration': duration,
            'samples': min_len
        }
    
    def calculate_attribution_ratio(
        self,
        app_power: List[float],
        total_power: List[float],
        baseline_power: float
    ) -> Dict[str, float]:
        """
        Calculate attribution ratio for the application.
        
        Formula: AR = (App_Power - Baseline) / (Total_Power - Baseline)
        
        Returns:
            Dictionary with attribution metrics
        """
        if not app_power or not total_power or len(app_power) != len(total_power):
            return {}
        
        # Calculate deltas
        app_delta = [p - baseline_power for p in app_power]
        total_delta = [p - baseline_power for p in total_power]
        
        # Filter out negative values (power below baseline)
        app_delta = [d for d in app_delta if d > 0]
        total_delta = [d for d in total_delta if d > 0]
        
        if not app_delta or not total_delta:
            return {}
        
        mean_app_delta = statistics.mean(app_delta)
        mean_total_delta = statistics.mean(total_delta)
        
        if mean_total_delta == 0:
            attribution_ratio = 0.0
        else:
            attribution_ratio = mean_app_delta / mean_total_delta
        
        return {
            'attribution_ratio': attribution_ratio,
            'attribution_percent': attribution_ratio * 100,
            'mean_app_delta_mw': mean_app_delta,
            'mean_total_delta_mw': mean_total_delta,
            'baseline_power_mw': baseline_power,
            'mean_app_power_mw': statistics.mean(app_power),
            'mean_total_power_mw': statistics.mean(total_power)
        }
    
    def calculate_skewness(self, power_values: List[float]) -> Dict[str, any]:
        """
        Calculate skewness statistics for power consumption.
        
        Returns:
            Dictionary with skewness metrics and burst fraction
        """
        if not power_values or len(power_values) < 10:
            return {}
        
        mean = statistics.mean(power_values)
        median = statistics.median(power_values)
        
        if median == 0:
            divergence_pct = 0.0
        else:
            divergence_pct = abs(mean - median) / median * 100
        
        # Determine skew direction
        if mean < median:
            skew_direction = "left-skewed"
            skew_interpretation = "Power drops (idle periods, background tabs, paused rendering)"
        elif mean > median:
            skew_direction = "right-skewed"
            skew_interpretation = "Power spikes (active rendering, video playback, heavy computation)"
        else:
            skew_direction = "normal"
            skew_interpretation = "Stable power consumption"
        
        # Calculate burst fraction for right-skewed
        burst_fraction = None
        if mean > median:
            low_power = min(power_values)
            high_power = max(power_values)
            if high_power > low_power:
                # Mean = (L × f) + (H × (1-f))
                idle_fraction = (mean - high_power) / (low_power - high_power)
                idle_fraction = max(0.0, min(1.0, idle_fraction))
                burst_fraction = 1.0 - idle_fraction
        
        return {
            'mean': mean,
            'median': median,
            'divergence_pct': divergence_pct,
            'skew_direction': skew_direction,
            'skew_interpretation': skew_interpretation,
            'burst_fraction': burst_fraction,
            'min': min(power_values),
            'max': max(power_values),
            'std': statistics.stdev(power_values) if len(power_values) > 1 else 0.0,
            'samples': len(power_values)
        }
    
    def identify_hidden_waste(self, analysis: Dict) -> List[str]:
        """
        Identify hidden energy waste based on analysis.
        
        Returns:
            List of waste indicators and recommendations
        """
        waste_indicators = []
        
        # Low attribution ratio = hidden processes
        if 'attribution_ratio' in analysis:
            ar = analysis['attribution_ratio']
            if ar < 0.3:  # Less than 30% attribution
                waste_indicators.append(
                    f"⚠️  Low Attribution Ratio ({ar*100:.1f}%): "
                    f"App power is not well-attributed. Possible hidden processes or "
                    f"system overhead consuming power."
                )
        
        # High burst fraction = inefficient rendering
        if 'skewness' in analysis and 'burst_fraction' in analysis['skewness']:
            bf = analysis['skewness']['burst_fraction']
            if bf and bf > 0.5:  # More than 50% bursting
                waste_indicators.append(
                    f"⚠️  High Burst Fraction ({bf*100:.1f}%): "
                    f"Frequent power spikes indicate inefficient rendering or "
                    f"background activity. Consider reducing workload or closing background tabs."
                )
        
        # Right-skewed with high divergence = inconsistent power
        if 'skewness' in analysis:
            skew = analysis['skewness']
            if (skew['skew_direction'] == 'right-skewed' and 
                skew['divergence_pct'] > 20):
                waste_indicators.append(
                    f"⚠️  High Divergence ({skew['divergence_pct']:.1f}%): "
                    f"Mean and median diverge significantly, indicating inconsistent "
                    f"power consumption. May indicate background tabs or hidden processes."
                )
        
        return waste_indicators
    
    def analyze_app(self, duration: int = 30, baseline_power: Optional[float] = None) -> Dict:
        """
        Complete analysis of the application.
        
        Args:
            duration: Measurement duration (seconds)
            baseline_power: Baseline system power (if None, will measure)
        
        Returns:
            Complete analysis dictionary
        """
        print("=" * 70)
        print(f"🔍 USER APP ANALYSIS: {self.app_name}")
        print("=" * 70)
        print()
        
        # Measure baseline if not provided
        if baseline_power is None:
            print("📊 Measuring baseline power (10s)...")
            baseline_power = self._measure_baseline(duration=10)
            print(f"  Baseline: {baseline_power:.1f} mW")
        
        # Measure app power
        power_data = self.measure_app_power(duration=duration)
        if not power_data or not power_data.get('total_power'):
            print("  ⚠️  Could not collect power data")
            return {}
        
        # Calculate attribution
        attribution = self.calculate_attribution_ratio(
            power_data['total_power'],
            power_data['total_power'],  # For app, total = app (we're measuring app-specific)
            baseline_power
        )
        
        # Calculate skewness
        skewness = self.calculate_skewness(power_data['total_power'])
        
        # Identify waste
        waste_indicators = self.identify_hidden_waste({
            'attribution_ratio': attribution.get('attribution_ratio', 0),
            'skewness': skewness
        })
        
        # Build analysis result
        analysis = {
            'app_name': self.app_name,
            'timestamp': datetime.now().isoformat(),
            'baseline_power_mw': baseline_power,
            'power_data': power_data,
            'attribution': attribution,
            'skewness': skewness,
            'waste_indicators': waste_indicators,
            'processes': power_data.get('processes', [])
        }
        
        # Print results
        self._print_results(analysis)
        
        # Save results
        self._save_results(analysis)
        
        return analysis
    
    def _print_results(self, analysis: Dict):
        """Print analysis results."""
        print("\n" + "=" * 70)
        print("📊 ANALYSIS RESULTS")
        print("=" * 70)
        print()
        
        # Attribution
        if 'attribution' in analysis and analysis['attribution']:
            attr = analysis['attribution']
            print(f"Attribution Ratio: {attr['attribution_percent']:.1f}%")
            print(f"  Mean App Power: {attr['mean_app_power_mw']:.1f} mW")
            print(f"  Baseline: {attr['baseline_power_mw']:.1f} mW")
            print()
        
        # Skewness
        if 'skewness' in analysis and analysis['skewness']:
            skew = analysis['skewness']
            print(f"Power Distribution: {skew['skew_direction']}")
            print(f"  Mean: {skew['mean']:.1f} mW")
            print(f"  Median: {skew['median']:.1f} mW")
            print(f"  Divergence: {skew['divergence_pct']:.1f}%")
            if skew['burst_fraction']:
                print(f"  Burst Fraction: {skew['burst_fraction']*100:.1f}%")
            print(f"  Interpretation: {skew['skew_interpretation']}")
            print()
        
        # Waste indicators
        if analysis.get('waste_indicators'):
            print("Hidden Energy Waste:")
            for indicator in analysis['waste_indicators']:
                print(f"  {indicator}")
            print()
    
    def _save_results(self, analysis: Dict):
        """Save analysis results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_dir / f"app_analysis_{self.app_name}_{timestamp}.json"
        
        # Remove power_data from saved file (too large)
        save_data = analysis.copy()
        save_data.pop('power_data', None)
        
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        print(f"💾 Results saved: {filename}")
    
    def _measure_baseline(self, duration: int = 10) -> float:
        """Measure baseline system power."""
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
            
            pattern = r'(?:CPU|Package|Total)\s+Power[:\s]+([\d.]+)\s*mW'
            matches = re.finditer(pattern, output, re.IGNORECASE)
            
            for match in matches:
                power_mw = float(match.group(1))
                power_values.append(power_mw)
            
            if power_values:
                return statistics.mean(power_values)
        except Exception:
            pass
        
        return 0.0


def main():
    parser = argparse.ArgumentParser(
        description="Analyze user-facing applications for hidden energy waste"
    )
    parser.add_argument(
        'app',
        help='Application name to analyze (e.g., Safari, Chrome, "Final Cut Pro")'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=30,
        help='Measurement duration in seconds (default: 30)'
    )
    parser.add_argument(
        '--baseline',
        type=float,
        help='Baseline system power in mW (if not provided, will measure)'
    )
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path("app_analysis_data"),
        help='Directory to save results (default: app_analysis_data)'
    )
    
    args = parser.parse_args()
    
    analyzer = UserAppAnalyzer(args.app, args.data_dir)
    results = analyzer.analyze_app(
        duration=args.duration,
        baseline_power=args.baseline
    )
    
    if results:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())

