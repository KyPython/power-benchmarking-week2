#!/usr/bin/env python3
"""
ANE/GPU Monitor with Skewness and Attribution Analysis
Extends power monitoring to Apple Neural Engine (ANE) and GPU,
applying the same statistical analysis (skewness, attribution) used for CPU.
"""

import subprocess
import time
import sys
import re
import argparse
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime
import numpy as np
import statistics


class ANEGPUMonitor:
    """
    Monitors ANE and GPU power with statistical analysis.
    """
    
    def __init__(self, sample_interval: int = 500):
        self.sample_interval = sample_interval
        self.ane_power_history = deque(maxlen=10000)
        self.gpu_power_history = deque(maxlen=10000)
        self.cpu_power_history = deque(maxlen=10000)
        self.total_power_history = deque(maxlen=10000)
        self.running = True
    
    def parse_powermetrics_line(self, line: str) -> Optional[Dict[str, float]]:
        """Parse power values from powermetrics output line."""
        data = {}
        
        # ANE Power
        ane_match = re.search(r'ANE\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
        if ane_match:
            data['ane_power_mw'] = float(ane_match.group(1))
        
        # GPU Power
        gpu_match = re.search(r'GPU\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
        if gpu_match:
            data['gpu_power_mw'] = float(gpu_match.group(1))
        
        # CPU Power
        cpu_match = re.search(r'(?:CPU|Package)\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
        if cpu_match:
            data['cpu_power_mw'] = float(cpu_match.group(1))
        
        # Total Package Power
        total_match = re.search(r'Total\s+Package\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
        if total_match:
            data['total_power_mw'] = float(total_match.group(1))
        
        return data if data else None
    
    def collect_power_data(self, duration: int = 60) -> Dict[str, List[float]]:
        """
        Collect power data from powermetrics.
        
        Args:
            duration: Collection duration in seconds
        
        Returns:
            Dictionary with power arrays
        """
        print(f"📊 Collecting power data for {duration} seconds...")
        print("   Monitoring: ANE, GPU, CPU, Total Package")
        print()
        
        cmd = [
            'sudo', 'powermetrics',
            '--samplers', 'cpu_power,gpu_power',
            '-i', str(self.sample_interval),
            '-n', str(int(duration * 1000 / self.sample_interval))
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            output, error = process.communicate(timeout=duration + 10)
            
            if error:
                print(f"⚠️  powermetrics stderr: {error[:200]}")
            
            # Parse all power values
            ane_values = []
            gpu_values = []
            cpu_values = []
            total_values = []
            
            for line in output.split('\n'):
                data = self.parse_powermetrics_line(line)
                if data:
                    if 'ane_power_mw' in data:
                        ane_values.append(data['ane_power_mw'])
                    if 'gpu_power_mw' in data:
                        gpu_values.append(data['gpu_power_mw'])
                    if 'cpu_power_mw' in data:
                        cpu_values.append(data['cpu_power_mw'])
                    if 'total_power_mw' in data:
                        total_values.append(data['total_power_mw'])
            
            return {
                'ane': ane_values,
                'gpu': gpu_values,
                'cpu': cpu_values,
                'total': total_values
            }
            
        except Exception as e:
            print(f"❌ Error collecting power data: {e}")
            return {}
    
    def calculate_skewness(self, values: List[float], component: str = "unknown") -> Dict[str, float]:
        """
        Calculate skewness statistics (mean, median, divergence).
        
        The formula Mean = (L × f) + (H × (1-f)) works universally across
        all Apple Silicon accelerators (CPU, ANE, GPU) because:
        
        1. **Unified Power Management**: Apple uses the same power management
           architecture across all accelerators - they all have idle states (L)
           and active states (H), with transitions between them.
        
        2. **Statistical Universality**: The formula is a mathematical property
           of bimodal distributions, independent of the underlying hardware. Whether
           it's CPU cores, Neural Engine, or GPU, if there are two power states
           (low and high), the mean will be a weighted average.
        
        3. **Apple's Design Philosophy**: All accelerators follow the same
           efficiency pattern - they idle when not in use (low power) and ramp up
           when active (high power). The "drop fraction" (f) represents the
           percentage of time spent in idle state.
        
        Args:
            values: Power values to analyze
            component: Component name (for interpretation)
        
        Returns:
            Dictionary with skewness metrics
        """
        if not values or len(values) < 10:
            return {}
        
        mean = statistics.mean(values)
        median = statistics.median(values)
        
        if median == 0:
            divergence_pct = 0.0
        else:
            divergence_pct = abs(mean - median) / median * 100
        
        # Determine skew direction
        if mean < median:
            skew_direction = "left-skewed"
            if component.lower() == "ane":
                skew_interpretation = "ANE idle periods between inference batches (Apple's unified power management)"
            elif component.lower() == "gpu":
                skew_interpretation = "GPU idle periods between render frames (Apple's unified power management)"
            else:
                skew_interpretation = "Background tasks reducing power (e.g., idle periods)"
        elif mean > median:
            skew_direction = "right-skewed"
            if component.lower() == "ane":
                skew_interpretation = "ANE inference spikes (burst workloads, Apple's unified power management)"
            elif component.lower() == "gpu":
                skew_interpretation = "GPU render spikes (burst workloads, Apple's unified power management)"
            else:
                skew_interpretation = "Burst workloads increasing power (e.g., inference spikes)"
        else:
            skew_direction = "normal"
            skew_interpretation = "Stable workload (consistent power consumption)"
        
        # Estimate drop fraction (for left-skewed)
        if mean < median and len(values) > 0:
            low_power = min(values)
            high_power = median
            if high_power > low_power:
                drop_fraction = (mean - high_power) / (low_power - high_power)
                drop_fraction = max(0, min(1, abs(drop_fraction)))
            else:
                drop_fraction = 0.0
        else:
            drop_fraction = 0.0
        
        return {
            'mean': mean,
            'median': median,
            'divergence_pct': divergence_pct,
            'skew_direction': skew_direction,
            'skew_interpretation': skew_interpretation,
            'drop_fraction': drop_fraction,
            'min': min(values),
            'max': max(values),
            'std': statistics.stdev(values) if len(values) > 1 else 0.0,
            'samples': len(values),
            'universality_note': (
                "Formula Mean = (L × f) + (H × (1-f)) works universally because "
                "Apple uses unified power management across all accelerators. "
                "All components (CPU, ANE, GPU) follow the same idle/active pattern."
            )
        }
    
    def calculate_attribution_ratio(
        self,
        component_values: List[float],
        total_values: List[float],
        baseline: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate attribution ratio for a component (ANE/GPU).
        
        Args:
            component_values: Component power values
            total_values: Total package power values
            baseline: Baseline power (optional, for delta calculation)
        
        Returns:
            Dictionary with attribution metrics
        """
        if not component_values or not total_values:
            return {}
        
        # Align arrays (take minimum length)
        min_len = min(len(component_values), len(total_values))
        component_aligned = component_values[:min_len]
        total_aligned = total_values[:min_len]
        
        # Calculate component contribution
        component_mean = statistics.mean(component_aligned)
        total_mean = statistics.mean(total_aligned)
        
        # Attribution ratio (component / total)
        if total_mean > 0:
            attribution_ratio = (component_mean / total_mean) * 100
        else:
            attribution_ratio = 0.0
        
        # Delta attribution (if baseline provided)
        if baseline is not None:
            component_delta = component_mean - baseline
            total_delta = total_mean - baseline
            if total_delta > 0:
                delta_attribution = (component_delta / total_delta) * 100
            else:
                delta_attribution = 0.0
        else:
            delta_attribution = None
        
        return {
            'component_mean_mw': component_mean,
            'total_mean_mw': total_mean,
            'attribution_ratio_pct': attribution_ratio,
            'delta_attribution_pct': delta_attribution,
            'samples': min_len
        }
    
    def analyze_power_data(self, power_data: Dict[str, List[float]]) -> Dict:
        """
        Analyze power data with skewness and attribution.
        
        Returns:
            Complete analysis dictionary
        """
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'ane': {},
            'gpu': {},
            'cpu': {},
            'total': {},
            'attribution': {}
        }
        
        # Skewness analysis for each component
        for component in ['ane', 'gpu', 'cpu', 'total']:
            if component in power_data and power_data[component]:
                analysis[component] = self.calculate_skewness(power_data[component], component=component)
        
        # Attribution analysis
        if 'total' in power_data and power_data['total']:
            total_values = power_data['total']
            
            # ANE attribution
            if 'ane' in power_data and power_data['ane']:
                ane_baseline = min(power_data['ane']) if power_data['ane'] else 0.0
                analysis['attribution']['ane'] = self.calculate_attribution_ratio(
                    power_data['ane'],
                    total_values,
                    baseline=ane_baseline
                )
            
            # GPU attribution
            if 'gpu' in power_data and power_data['gpu']:
                gpu_baseline = min(power_data['gpu']) if power_data['gpu'] else 0.0
                analysis['attribution']['gpu'] = self.calculate_attribution_ratio(
                    power_data['gpu'],
                    total_values,
                    baseline=gpu_baseline
                )
        
        return analysis
    
    def print_analysis(self, analysis: Dict):
        """Print analysis results."""
        print("\n" + "=" * 70)
        print("📊 ANE/GPU POWER ANALYSIS: Skewness & Attribution")
        print("=" * 70)
        print()
        
        # Skewness Analysis
        print("📈 SKEWNESS ANALYSIS")
        print("-" * 70)
        print()
        
        for component in ['ane', 'gpu', 'cpu', 'total']:
            if component in analysis and analysis[component]:
                stats = analysis[component]
                component_name = component.upper()
                
                print(f"{component_name} Power:")
                print(f"  Mean:     {stats['mean']:8.1f} mW")
                print(f"  Median:   {stats['median']:8.1f} mW")
                print(f"  Divergence: {stats['divergence_pct']:5.2f}%")
                print(f"  Skew:     {stats['skew_direction']}")
                print(f"  Interpretation: {stats['skew_interpretation']}")
                
                if stats['drop_fraction'] > 0:
                    print(f"  Drop Fraction: {stats['drop_fraction']*100:.2f}%")
                
                print(f"  Range:    {stats['min']:.1f} - {stats['max']:.1f} mW")
                print(f"  Std Dev:  {stats['std']:.1f} mW")
                print(f"  Samples:  {stats['samples']}")
                print()
        
        # Attribution Analysis
        if 'attribution' in analysis and analysis['attribution']:
            print("🎯 ATTRIBUTION ANALYSIS")
            print("-" * 70)
            print()
            
            for component in ['ane', 'gpu']:
                if component in analysis['attribution']:
                    attr = analysis['attribution'][component]
                    component_name = component.upper()
                    
                    print(f"{component_name} Attribution:")
                    print(f"  Component Power: {attr['component_mean_mw']:8.1f} mW")
                    print(f"  Total Power:     {attr['total_mean_mw']:8.1f} mW")
                    print(f"  Attribution:     {attr['attribution_ratio_pct']:5.1f}% of total")
                    
                    if attr['delta_attribution_pct'] is not None:
                        print(f"  Delta Attribution: {attr['delta_attribution_pct']:5.1f}% of delta")
                    
                    print(f"  Samples:          {attr['samples']}")
                    print()
        
        # Summary
        print("💡 INTERPRETATION")
        print("-" * 70)
        print()
        
        if 'ane' in analysis and analysis['ane']:
            ane_stats = analysis['ane']
            if ane_stats['divergence_pct'] > 5.0:
                print("⚠️  ANE shows significant divergence - background interference detected")
            else:
                print("✅ ANE shows stable power consumption")
        
        if 'gpu' in analysis and analysis['gpu']:
            gpu_stats = analysis['gpu']
            if gpu_stats['divergence_pct'] > 5.0:
                print("⚠️  GPU shows significant divergence - background interference detected")
            else:
                print("✅ GPU shows stable power consumption")
        
        if 'attribution' in analysis:
            if 'ane' in analysis['attribution']:
                ane_attr = analysis['attribution']['ane']
                print(f"📊 ANE contributes {ane_attr['attribution_ratio_pct']:.1f}% of total package power")
            
            if 'gpu' in analysis['attribution']:
                gpu_attr = analysis['attribution']['gpu']
                print(f"📊 GPU contributes {gpu_attr['attribution_ratio_pct']:.1f}% of total package power")


def main():
    parser = argparse.ArgumentParser(
        description='Monitor ANE/GPU power with skewness and attribution analysis'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Monitoring duration in seconds (default: 60)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=500,
        help='Sampling interval in milliseconds (default: 500)'
    )
    
    args = parser.parse_args()
    
    monitor = ANEGPUMonitor(sample_interval=args.interval)
    
    print("=" * 70)
    print("🧠 ANE/GPU MONITOR: Skewness & Attribution Analysis")
    print("=" * 70)
    print()
    print("This monitor applies the same statistical analysis used for CPU:")
    print("  • Skewness detection (mean/median divergence)")
    print("  • Attribution ratio (component vs total power)")
    print("  • Background interference detection")
    print()
    
    # Collect data
    power_data = monitor.collect_power_data(duration=args.duration)
    
    if not power_data:
        print("❌ Failed to collect power data")
        return 1
    
    # Analyze
    analysis = monitor.analyze_power_data(power_data)
    
    # Print results
    monitor.print_analysis(analysis)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

