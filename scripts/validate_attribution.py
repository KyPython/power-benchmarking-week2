#!/usr/bin/env python3
"""
Attribution Accuracy Check - Power Virus Test
Compares Process-level tracking against a known "power virus" to measure
unattributed system power and validate baseline subtraction logic.
"""

import subprocess
import time
import sys
import argparse
import re
from typing import Dict, List
import psutil


def create_power_virus(duration: int = 30, cores: int = 1):
    """
    Create a "power virus" - a script that maxes out CPU cores.
    
    Args:
        duration: How long to run (seconds)
        cores: Number of cores to stress
    """
    virus_script = f"""
import time
import multiprocessing

def burn_cpu():
    '''Burn CPU cycles continuously'''
    end_time = time.time() + {duration}
    while time.time() < end_time:
        # Intensive computation
        sum(i*i for i in range(100000))

# Start stress processes
processes = []
for _ in range({cores}):
    p = multiprocessing.Process(target=burn_cpu)
    p.start()
    processes.append(p)

# Wait for completion
for p in processes:
    p.join()
"""
    
    return subprocess.Popen(
        ['python3', '-c', virus_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def measure_baseline_power(duration: int = 10) -> Dict[str, float]:
    """Measure system power in idle state (baseline)."""
    print(f"📊 Measuring baseline power (idle system) for {duration}s...")
    
    cmd = ['sudo', 'powermetrics', '--samplers', 'cpu_power', 
           '-i', '500', '-n', str(int(duration * 1000 / 500))]
    
    power_values = {
        'cpu': [],
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
            print(f"⚠️  powermetrics error: {stderr[:200]}")
            return {}
        
        # Parse power values
        for line in stdout.split('\n'):
            cpu_match = re.search(r'(?:CPU|Package)\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
            if cpu_match:
                power_values['cpu'].append(float(cpu_match.group(1)))
            
            total_match = re.search(r'Total\s+Package\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
            if total_match:
                power_values['total'].append(float(total_match.group(1)))
        
        # Calculate averages
        baseline = {}
        if power_values['cpu']:
            baseline['cpu_mean'] = sum(power_values['cpu']) / len(power_values['cpu'])
        if power_values['total']:
            baseline['total_mean'] = sum(power_values['total']) / len(power_values['total'])
        
        return baseline
        
    except Exception as e:
        print(f"❌ Error measuring baseline: {e}")
        return {}


def measure_power_virus_power(virus_process, duration: int = 30) -> Dict[str, float]:
    """Measure system power while power virus is running."""
    print(f"🔥 Measuring power during CPU stress for {duration}s...")
    
    cmd = ['sudo', 'powermetrics', '--samplers', 'cpu_power', 
           '-i', '500', '-n', str(int(duration * 1000 / 500))]
    
    power_values = {
        'cpu': [],
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
            print(f"⚠️  powermetrics error: {stderr[:200]}")
            return {}
        
        # Parse power values
        for line in stdout.split('\n'):
            cpu_match = re.search(r'(?:CPU|Package)\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
            if cpu_match:
                power_values['cpu'].append(float(cpu_match.group(1)))
            
            total_match = re.search(r'Total\s+Package\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
            if total_match:
                power_values['total'].append(float(total_match.group(1)))
        
        # Calculate averages
        virus_power = {}
        if power_values['cpu']:
            virus_power['cpu_mean'] = sum(power_values['cpu']) / len(power_values['cpu'])
        if power_values['total']:
            virus_power['total_mean'] = sum(power_values['total']) / len(power_values['total'])
        
        return virus_power
        
    except Exception as e:
        print(f"❌ Error measuring virus power: {e}")
        return {}


def find_virus_pids() -> List[int]:
    """Find PIDs of power virus processes."""
    pids = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            if 'burn_cpu' in cmdline or 'multiprocessing.Process' in cmdline:
                pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return pids


def calculate_attribution_accuracy(baseline: Dict, virus_power: Dict, virus_pids: List[int]):
    """Calculate how much power is attributed vs unattributed."""
    print("\n" + "=" * 70)
    print("⚖️  ATTRIBUTION ACCURACY ANALYSIS")
    print("=" * 70)
    
    if not baseline or not virus_power:
        print("❌ Missing baseline or virus power data")
        return
    
    # Calculate power delta
    cpu_delta = virus_power.get('cpu_mean', 0) - baseline.get('cpu_mean', 0)
    total_delta = virus_power.get('total_mean', 0) - baseline.get('total_mean', 0)
    
    print(f"\n📊 Power Measurements:")
    print(f"   Baseline (idle):")
    print(f"     CPU:  {baseline.get('cpu_mean', 0):.2f} mW")
    print(f"     Total: {baseline.get('total_mean', 0):.2f} mW")
    
    print(f"\n   During Power Virus:")
    print(f"     CPU:  {virus_power.get('cpu_mean', 0):.2f} mW")
    print(f"     Total: {virus_power.get('total_mean', 0):.2f} mW")
    
    print(f"\n   Power Delta (Virus - Baseline):")
    print(f"     CPU:  {cpu_delta:.2f} mW")
    print(f"     Total: {total_delta:.2f} mW")
    
    print(f"\n🔍 Attribution Analysis:")
    print(f"   Virus PIDs found: {len(virus_pids)}")
    if virus_pids:
        print(f"   PIDs: {virus_pids}")
    
    # Estimate process power (if we could measure it directly)
    # In reality, we can't directly measure process power, so we use delta
    estimated_process_power = total_delta
    
    print(f"\n   Estimated Process Power (delta): {estimated_process_power:.2f} mW")
    print(f"   System Overhead (baseline): {baseline.get('total_mean', 0):.2f} mW")
    
    # Calculate unattributed power
    # This is power that exists but isn't directly from the process
    unattributed = baseline.get('total_mean', 0)
    attribution_ratio = estimated_process_power / (estimated_process_power + unattributed) if (estimated_process_power + unattributed) > 0 else 0
    
    print(f"\n   Attribution Ratio: {attribution_ratio*100:.1f}%")
    print(f"   (Process power / Total power during stress)")
    
    print(f"\n💡 Interpretation:")
    print(f"   - Power delta shows additional power from virus")
    print(f"   - Baseline shows 'unattributed' system power")
    print(f"   - Attribution ratio indicates how much power is 'attributed' to process")
    print(f"   - Lower ratio = more system overhead/unattributed power")
    
    if attribution_ratio < 0.5:
        print(f"\n   ⚠️  Low attribution (<50%) - significant system overhead")
        print(f"   💡 Baseline subtraction would improve accuracy")
    elif attribution_ratio > 0.7:
        print(f"\n   ✅ Good attribution (>70%) - process power is dominant")
    else:
        print(f"\n   ℹ️  Moderate attribution (50-70%) - some system overhead")
    
    print("=" * 70)


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description='Validate power attribution accuracy using power virus'
    )
    parser.add_argument(
        '--baseline-duration',
        type=int,
        default=10,
        help='Baseline measurement duration in seconds (default: 10)'
    )
    parser.add_argument(
        '--virus-duration',
        type=int,
        default=30,
        help='Power virus duration in seconds (default: 30)'
    )
    parser.add_argument(
        '--cores',
        type=int,
        default=1,
        help='Number of CPU cores to stress (default: 1)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("⚖️  Attribution Accuracy Validation")
    print("=" * 70)
    print(f"Baseline duration: {args.baseline_duration}s")
    print(f"Virus duration: {args.virus_duration}s")
    print(f"CPU cores to stress: {args.cores}")
    print("=" * 70)
    print()
    
    # Step 1: Measure baseline
    baseline = measure_baseline_power(args.baseline_duration)
    if not baseline:
        print("❌ Failed to measure baseline power")
        return 1
    
    print(f"✅ Baseline measured: {baseline.get('total_mean', 0):.2f} mW")
    print()
    
    # Step 2: Start power virus
    print("🔥 Starting power virus...")
    virus_process = create_power_virus(args.virus_duration, args.cores)
    time.sleep(1)  # Let it start
    
    # Find virus PIDs
    virus_pids = find_virus_pids()
    if virus_pids:
        print(f"✅ Found {len(virus_pids)} virus process(es)")
    else:
        print("⚠️  Could not find virus PIDs (may still be running)")
    
    # Step 3: Measure power during virus
    virus_power = measure_power_virus_power(virus_process, args.virus_duration)
    
    # Wait for virus to complete
    virus_process.wait()
    
    if not virus_power:
        print("❌ Failed to measure virus power")
        return 1
    
    print(f"✅ Virus power measured: {virus_power.get('total_mean', 0):.2f} mW")
    print()
    
    # Step 4: Analyze attribution
    calculate_attribution_accuracy(baseline, virus_power, virus_pids)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

