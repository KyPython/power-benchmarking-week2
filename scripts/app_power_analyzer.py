#!/usr/bin/env python3
"""
App Power Analyzer - Compare power consumption between different apps
Uses powermetrics to measure power usage of specific applications.
"""

import subprocess
import time
import sys
import argparse
import re
from typing import Dict, List, Optional, Set
from pathlib import Path
import csv
from datetime import datetime
import psutil


def find_app_pids(app_name: str) -> Set[int]:
    """
    Find all Process IDs (PIDs) for a given application name.
    
    Args:
        app_name: Application name (e.g., 'Safari', 'Google Chrome')
    
    Returns:
        Set of PIDs for the application
    """
    pids = set()
    
    # Try exact match first
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if app_name.lower() in proc.info['name'].lower():
                pids.add(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Also check command line for better matching
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            if app_name.lower() in cmdline.lower() or app_name.lower() in proc.info['name'].lower():
                pids.add(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return pids


def get_process_power(app_name: str, duration: int = 10, sample_interval: int = 500, 
                     use_pid_filter: bool = True) -> Dict[str, float]:
    """
    Measure power consumption for a specific app using PID filtering.
    
    Args:
        app_name: Name of the application (e.g., 'Safari', 'Chrome')
        duration: Duration to measure in seconds
        sample_interval: Sampling interval in milliseconds
        use_pid_filter: If True, filter powermetrics by process PIDs
    
    Returns:
        Dictionary with power statistics
    """
    print(f"\n🔍 Measuring power for: {app_name}")
    print(f"   Duration: {duration}s | Interval: {sample_interval}ms")
    
    # Find PIDs for the application
    pids = set()
    if use_pid_filter:
        pids = find_app_pids(app_name)
        if pids:
            print(f"   Found {len(pids)} process(es): PIDs {sorted(pids)}")
        else:
            print(f"   ⚠️  No processes found for '{app_name}' - measuring system-wide power")
            print(f"   💡 Tip: Make sure the app is running")
    
    # Build powermetrics command
    cmd = ['sudo', 'powermetrics', '--samplers', 'cpu_power', '-i', str(sample_interval), '-n', str(int(duration * 1000 / sample_interval))]
    
    # Add PID filter if we found processes
    if pids and use_pid_filter:
        # Note: powermetrics doesn't directly support PID filtering in all versions
        # We'll filter in post-processing, but we can use --show-process-coalition for better data
        cmd.extend(['--show-process-coalition'])
        print(f"   Using process coalition tracking for better accuracy")
    
    power_values = {
        'ane': [],
        'cpu': [],
        'gpu': [],
        'total': []
    }
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=duration + 5)
        
        if process.returncode != 0:
            print(f"⚠️  powermetrics returned error: {stderr[:200]}")
            return {}
        
        # Parse power values with PID-aware filtering
        process_power_data = []  # Store per-process data if available
        
        for line in stdout.split('\n'):
            # Check if this line contains process/coalition info
            process_match = None
            if pids and use_pid_filter:
                # Look for process names or PIDs in the line
                for pid in pids:
                    if f'pid {pid}' in line.lower() or app_name.lower() in line.lower():
                        process_match = True
                        break
            
            # ANE Power (system-wide or process-specific)
            ane_match = re.search(r'ANE\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
            if ane_match:
                power_val = float(ane_match.group(1))
                # If we have PID filter and this line matches, prioritize it
                if process_match or not pids:
                    power_values['ane'].append(power_val)
            
            # CPU Power
            cpu_match = re.search(r'(?:CPU|Package)\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
            if cpu_match:
                power_val = float(cpu_match.group(1))
                if process_match or not pids:
                    power_values['cpu'].append(power_val)
            
            # GPU Power
            gpu_match = re.search(r'GPU\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
            if gpu_match:
                power_val = float(gpu_match.group(1))
                if process_match or not pids:
                    power_values['gpu'].append(power_val)
            
            # Total Power
            total_match = re.search(r'Total\s+Package\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
            if total_match:
                power_val = float(total_match.group(1))
                if process_match or not pids:
                    power_values['total'].append(power_val)
            
            # Process-specific power (if available in coalition output)
            if process_match and 'power' in line.lower():
                proc_power_match = re.search(r'(\d+\.?\d*)\s*mW', line)
                if proc_power_match:
                    process_power_data.append(float(proc_power_match.group(1)))
        
        # Calculate statistics
        stats = {}
        for key, values in power_values.items():
            if values:
                stats[f'{key}_mean_mw'] = sum(values) / len(values)
                stats[f'{key}_min_mw'] = min(values)
                stats[f'{key}_max_mw'] = max(values)
                stats[f'{key}_samples'] = len(values)
        
        # Add PID info if available
        if pids:
            stats['pids_tracked'] = sorted(pids)
            stats['pid_count'] = len(pids)
        
        # Add process-specific power if we found it
        if process_power_data:
            stats['process_power_mean_mw'] = sum(process_power_data) / len(process_power_data)
            stats['process_power_samples'] = len(process_power_data)
        
        return stats
        
    except subprocess.TimeoutExpired:
        process.kill()
        print("❌ powermetrics timed out")
        return {}
    except Exception as e:
        print(f"❌ Error measuring power: {e}")
        return {}


def compare_apps(apps: List[str], duration: int = 10, output_csv: Optional[str] = None, 
                use_pid_filter: bool = True):
    """
    Compare power consumption between multiple apps.
    
    Args:
        apps: List of app names to compare
        duration: Duration to measure each app (seconds)
        output_csv: Optional CSV file to save results
    """
    print("=" * 70)
    print("📊 App Power Comparison")
    print("=" * 70)
    print(f"Apps to compare: {', '.join(apps)}")
    print(f"Measurement duration per app: {duration}s")
    print("=" * 70)
    
    results = {}
    
    for app in apps:
        print(f"\n⏳ Starting measurement for {app}...")
        print("   (Please start/switch to the app now)")
        time.sleep(2)  # Give user time to switch apps
        
        stats = get_process_power(app, duration, use_pid_filter=use_pid_filter)
        if stats:
            results[app] = stats
            print(f"✅ Completed measurement for {app}")
        else:
            print(f"⚠️  No data collected for {app}")
    
    # Print comparison table
    print("\n" + "=" * 70)
    print("📊 COMPARISON RESULTS")
    print("=" * 70)
    
    if not results:
        print("❌ No data collected")
        return
    
    # Find all available metrics
    all_metrics = set()
    for app_stats in results.values():
        all_metrics.update(app_stats.keys())
    
    # Group metrics by type
    metric_groups = {}
    for metric in all_metrics:
        if '_mean_mw' in metric:
            base = metric.replace('_mean_mw', '')
            if base not in metric_groups:
                metric_groups[base] = []
            metric_groups[base].append(metric)
    
    # Print comparison for each metric group
    for group, metrics in metric_groups.items():
        print(f"\n{group.upper()} Power (mW):")
        print(f"{'App':<20} {'Mean':<12} {'Min':<12} {'Max':<12} {'Samples':<10}")
        print("-" * 70)
        
        for app in apps:
            if app in results:
                stats = results[app]
                mean_key = f'{group}_mean_mw'
                min_key = f'{group}_min_mw'
                max_key = f'{group}_max_mw'
                samples_key = f'{group}_samples'
                
                if mean_key in stats:
                    print(f"{app:<20} {stats[mean_key]:>10.2f} {stats.get(min_key, 0):>10.2f} "
                          f"{stats.get(max_key, 0):>10.2f} {stats.get(samples_key, 0):>10}")
    
    # Calculate efficiency comparison
    if len(results) >= 2:
        print("\n" + "=" * 70)
        print("⚡ EFFICIENCY COMPARISON")
        print("=" * 70)
        
        apps_list = list(results.keys())
        if 'total_mean_mw' in results[apps_list[0]]:
            base_power = results[apps_list[0]]['total_mean_mw']
            print(f"\nRelative to {apps_list[0]}:")
            for app in apps_list[1:]:
                if 'total_mean_mw' in results[app]:
                    ratio = results[app]['total_mean_mw'] / base_power
                    savings = (1 - ratio) * 100
                    print(f"  {app}: {ratio:.2f}x power ({savings:+.1f}% efficiency)")
    
    # Save to CSV if requested
    if output_csv:
        save_comparison_csv(results, output_csv)
        print(f"\n✅ Results saved to: {output_csv}")


def save_comparison_csv(results: Dict[str, Dict], csv_path: str):
    """Save comparison results to CSV."""
    fieldnames = ['app', 'ane_mean_mw', 'cpu_mean_mw', 'gpu_mean_mw', 'total_mean_mw',
                  'ane_min_mw', 'cpu_min_mw', 'gpu_min_mw', 'total_min_mw',
                  'ane_max_mw', 'cpu_max_mw', 'gpu_max_mw', 'total_max_mw',
                  'ane_samples', 'cpu_samples', 'gpu_samples', 'total_samples']
    
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for app, stats in results.items():
            row = {'app': app}
            row.update(stats)
            writer.writerow(row)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Compare power consumption between different applications'
    )
    parser.add_argument(
        'apps',
        nargs='+',
        help='Application names to compare (e.g., Safari Chrome)'
    )
    parser.add_argument(
        '--duration', '-d',
        type=int,
        default=10,
        help='Duration to measure each app in seconds (default: 10)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output CSV file to save results'
    )
    parser.add_argument(
        '--no-pid-filter',
        action='store_true',
        help='Disable PID filtering (measure system-wide power instead)'
    )
    
    args = parser.parse_args()
    
    if len(args.apps) < 2:
        print("❌ Please provide at least 2 apps to compare")
        return 1
    
    compare_apps(args.apps, args.duration, args.output, use_pid_filter=not args.no_pid_filter)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

