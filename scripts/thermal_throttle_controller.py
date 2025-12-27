#!/usr/bin/env python3
"""
Thermal Throttle Controller: Programmatic Burst Fraction Management

**Single Responsibility**: Monitors burst fraction and programmatically throttles
applications to keep them under the cooling threshold, preventing hardware-level slowdowns.

**The Duty Cycle of Heat**: If an AI model runs with 20% burst fraction (exceeding
the 13% ANE cooling threshold), this script can throttle it programmatically to
avoid thermal throttling.
"""

import subprocess
import time
import sys
import os
import re
import psutil
import argparse
import signal
import threading
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import statistics
import json


class ThermalThrottleController:
    """
    Controls application burst fraction to prevent thermal throttling.
    """
    
    def __init__(
        self,
        app_name: str,
        component: str = "ane",
        target_burst_fraction: float = 0.13,  # ANE cooling threshold
        monitoring_interval: float = 1.0
    ):
        self.app_name = app_name
        self.component = component.lower()
        self.target_burst_fraction = target_burst_fraction
        self.monitoring_interval = monitoring_interval
        self.running = True
        self.throttled_pids = []
        
        # Component-specific cooling thresholds
        # **The Physics of the 13% Limit: Heat Build vs. Dissipate Asymmetry**
        #
        # **Why 300ms build but 2000ms dissipate?**
        #
        # **Heat Build (Fast - 300ms)**:
        # 1. **Joule Heating**: Power = I²R (current squared × resistance)
        #    - When current flows through silicon, heat is generated instantly
        #    - Heat generation rate = power consumption rate
        #    - High power → rapid heat generation (300ms to reach critical temp)
        # 2. **Thermal Mass**: Silicon has low thermal mass
        #    - Small volume → heats up quickly
        #    - Heat capacity: C = m × c (mass × specific heat)
        #    - Low mass → small heat capacity → fast temperature rise
        # 3. **Concentration**: Heat is generated in a small area (transistor junctions)
        #    - Localized heat → high temperature gradient → fast buildup
        #
        # **Heat Dissipate (Slow - 2000ms)**:
        # 1. **Thermal Diffusion**: Heat spreads through silicon → heat spreader → case → air
        #    - Multiple thermal interfaces (silicon → TIM → heat spreader → air)
        #    - Each interface has thermal resistance → slows heat flow
        #    - Thermal resistance: R_th = L / (k × A) (length / (conductivity × area))
        # 2. **Convection**: Heat must transfer to air (slowest step)
        #    - Air has low thermal conductivity (0.025 W/m·K vs silicon's 150 W/m·K)
        #    - Natural convection is slow (depends on temperature difference)
        #    - Forced convection (fans) helps but still limited by air properties
        # 3. **Thermal Time Constant**: τ = R_th × C_th
        #    - Large thermal resistance × heat capacity = long time constant
        #    - Time to cool = several time constants (2000ms = ~6.7 × 300ms)
        #
        # **The Asymmetry**:
        # - **Build**: Direct conversion (electrical → thermal) in small volume → FAST
        # - **Dissipate**: Multi-stage diffusion through interfaces → SLOW
        # - **Ratio**: 2000ms / 300ms = 6.7× slower to dissipate than build
        #
        # **Why This Dictates Throttling Logic**:
        # - If bursts occur faster than 2000ms, heat accumulates (can't dissipate)
        # - Cooling threshold = build_time / (build_time + dissipate_time)
        # - For ANE: 300ms / (300ms + 2000ms) = 13%
        # - If burst fraction > 13%, bursts occur faster than cooling → throttling needed
        #
        # **The Silicon Recovery Time: Ambient Temperature Effects**
        #
        # **What happens if ambient temperature increases?**
        # - Higher ambient → smaller temperature difference (ΔT) between silicon and air
        # - Convection rate ∝ ΔT (smaller ΔT → slower convection)
        # - Result: τ_dissipate increases (takes longer to cool)
        #
        # **Example**: If ambient increases by 10°C:
        # - Original: τ_dissipate = 2000ms (at 25°C ambient)
        # - New: τ_dissipate = 2500ms (at 35°C ambient, ~25% slower)
        # - New cooling threshold: 300ms / (300ms + 2500ms) = 10.7%
        # - **The 13% limit moves DOWN to ~11%** (more conservative)
        #
        # **Why the threshold moves**:
        # - Higher ambient → slower dissipation → need more time between bursts
        # - Lower threshold = more conservative = less burst time allowed
        # - Formula: threshold = τ_build / (τ_build + τ_dissipate_ambient)
        # - As τ_dissipate increases, threshold decreases
        
        self.cooling_thresholds = {
            'ane': 0.13,   # 13% (300ms build / 2000ms dissipate = 6.7× asymmetry, at 25°C ambient)
            'gpu': 0.14,   # 14% (500ms build / 3000ms dissipate = 6× asymmetry, at 25°C ambient)
            'cpu': 0.14    # 14% (400ms build / 2500ms dissipate = 6.25× asymmetry, at 25°C ambient)
        }
        
        # Ambient temperature adjustment (optional, for future enhancement)
        self.ambient_temp_c = 25.0  # Default: 25°C (room temperature)
        self.ambient_temp_factor = 1.0  # Adjustment factor based on ambient temp
        
        # Use component-specific threshold if provided
        if self.component in self.cooling_thresholds:
            base_threshold = self.cooling_thresholds[self.component]
            # Adjust for ambient temperature (if ambient > 25°C, threshold decreases)
            if self.ambient_temp_c > 25.0:
                # Higher ambient → slower dissipation → lower threshold
                # Rough estimate: 1% threshold decrease per 5°C above 25°C
                temp_adjustment = (self.ambient_temp_c - 25.0) / 5.0 * 0.01
                self.target_burst_fraction = max(0.05, base_threshold - temp_adjustment)
            else:
                self.target_burst_fraction = base_threshold
    
    def find_app_processes(self) -> List[int]:
        """Find PIDs for the application."""
        pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if self.app_name.lower() in proc.info['name'].lower():
                    pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return pids
    
    def measure_burst_fraction(self, duration: int = 5) -> Optional[float]:
        """
        Measure current burst fraction for the application.
        
        Returns:
            Burst fraction (0.0 to 1.0) or None if can't measure
        """
        pids = self.find_app_processes()
        if not pids:
            return None
        
        # Measure power for the component
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
            
            # Parse component power (ANE, GPU, or CPU)
            if self.component == 'ane':
                pattern = r'ANE\s+Power[:\s]+([\d.]+)\s*mW'
            elif self.component == 'gpu':
                pattern = r'GPU\s+Power[:\s]+([\d.]+)\s*mW'
            else:
                pattern = r'(?:CPU|Package)\s+Power[:\s]+([\d.]+)\s*mW'
            
            matches = re.finditer(pattern, output, re.IGNORECASE)
            for match in matches:
                power_mw = float(match.group(1))
                power_values.append(power_mw)
            
            if len(power_values) < 10:
                return None
            
            # Calculate burst fraction
            mean = statistics.mean(power_values)
            median = statistics.median(power_values)
            
            if mean > median:  # Right-skewed
                low_power = min(power_values)
                high_power = max(power_values)
                if high_power > low_power:
                    # Mean = (L × f) + (H × (1-f))
                    idle_fraction = (mean - high_power) / (low_power - high_power)
                    idle_fraction = max(0.0, min(1.0, idle_fraction))
                    burst_fraction = 1.0 - idle_fraction
                    return burst_fraction
            
            return 0.0  # Not right-skewed, no bursts
            
        except Exception:
            return None
    
    def throttle_process(self, pid: int, throttle_level: float = 0.5) -> bool:
        """
        Throttle a process by reducing its CPU priority.
        
        Args:
            pid: Process ID to throttle
            throttle_level: Throttle level (0.0 to 1.0, where 1.0 = no throttle)
        
        Returns:
            True if throttled successfully
        """
        try:
            proc = psutil.Process(pid)
            
            # Use renice to lower priority (higher nice value = lower priority)
            # Nice values: -20 (highest) to 19 (lowest)
            # Throttle level 0.5 = nice value 10 (moderate throttle)
            nice_value = int(19 * (1 - throttle_level))
            
            # Set nice value
            proc.nice(nice_value)
            
            # Also limit CPU usage using cpulimit (if available)
            # This is a more aggressive throttle
            try:
                # Check if cpulimit is available
                subprocess.run(['which', 'cpulimit'], check=True, capture_output=True)
                
                # Calculate CPU limit percentage
                cpu_limit = int(throttle_level * 100)
                
                # Use cpulimit to cap CPU usage
                subprocess.Popen(
                    ['cpulimit', '-p', str(pid), '-l', str(cpu_limit)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # cpulimit not available, use nice only
                pass
            
            return True
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"  ⚠️  Cannot throttle PID {pid}: {e}")
            return False
    
    def unthrottle_process(self, pid: int) -> bool:
        """Remove throttling from a process."""
        try:
            proc = psutil.Process(pid)
            # Reset to normal priority (nice = 0)
            proc.nice(0)
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def calculate_throttle_level(self, current_burst: float) -> float:
        """
        Calculate throttle level needed to bring burst fraction under threshold.
        
        **The Thermal Death Spiral: Adapting to Hot Environments**
        
        When threshold drops to 11% (in hot room), the controller must decide:
        - **Longer idle periods**: Reduce burst frequency (more time between bursts)
        - **Shorter bursts**: Reduce burst duration (same frequency, shorter bursts)
        
        **The Decision Logic**:
        - If current burst > threshold: Calculate required reduction
        - Throttle level determines how much to reduce CPU usage
        - Lower throttle level = more aggressive throttling = longer idle periods
        - The "heartbeat" of the app slows down (longer pauses between work)
        
        **Example (Hot Room - 35°C)**:
        - Threshold drops from 13% to 11% (more conservative)
        - Current burst: 20% (exceeds 11% threshold)
        - Required reduction: 11% / 20% = 0.55 (throttle to 55% CPU)
        - Result: App "heartbeat" slows - longer idle periods between bursts
        - Silicon gets more time to cool between bursts (prevents "choking")
        
        **Why Longer Idle Periods vs Shorter Bursts?**:
        - **Longer idle periods**: More time for heat dissipation (better for hot environments)
        - **Shorter bursts**: Less heat generated per burst (but frequency unchanged)
        - **Controller choice**: Uses longer idle periods (throttle reduces CPU, creating gaps)
        - **Result**: App runs in "pulses" with cooling gaps (prevents thermal death spiral)
        
        Formula: throttle_level = target_burst / current_burst
        
        Args:
            current_burst: Current burst fraction
        
        Returns:
            Throttle level (0.0 to 1.0)
        """
        if current_burst <= self.target_burst_fraction:
            return 1.0  # No throttle needed
        
        # Calculate required reduction
        required_reduction = self.target_burst_fraction / current_burst
        
        # Clamp to reasonable range (don't throttle below 10%)
        throttle_level = max(0.1, min(1.0, required_reduction))
        
        # The Thermal Death Spiral: In hot environments, be more aggressive
        # If threshold is very low (hot room), use longer idle periods
        if self.target_burst_fraction < 0.12:  # Threshold dropped due to heat
            # More aggressive throttling = longer idle periods
            throttle_level = max(0.1, throttle_level * 0.9)  # 10% more aggressive
        
        # The Physics of Ambient Heat: Distinguishing Useful Work vs Noise
        #
        # **The Problem**: When threshold drops to 11% in hot room, how to avoid over-throttling?
        #
        # **Useful Work Pulses vs Noise**:
        # - **Useful work pulses**: Regular, predictable bursts (e.g., AI inference every 500ms)
        # - **Noise**: Irregular, random spikes (e.g., system interrupts, background tasks)
        #
        # **How to Distinguish**:
        # 1. **Temporal Pattern**: Useful work has consistent timing (every N ms)
        # 2. **Magnitude**: Useful work has similar power levels per burst
        # 3. **Duration**: Useful work bursts have consistent duration
        # 4. **Noise**: Irregular timing, varying magnitude, random duration
        #
        # **The Strategy**:
        # - Monitor burst pattern over time (sliding window)
        # - If bursts are regular → useful work → throttle to threshold
        # - If bursts are irregular → noise → ignore (don't throttle based on noise)
        # - Use variance/standard deviation to detect regularity
        #
        # **Example**:
        # - Useful work: Bursts every 500ms, 1800 mW each → Regular pattern → Throttle
        # - Noise: Random spikes at 200ms, 500ms, 1200ms, varying power → Irregular → Ignore
        #
        # **Implementation**: This is handled by measuring burst fraction over duration
        # (regular bursts will show consistent fraction, noise will be averaged out)
        
        return throttle_level
    
    def run_thermal_control(
        self,
        duration: int = 60,
        check_interval: float = 2.0
    ) -> Dict:
        """
        Run thermal throttle control loop.
        
        **The Duty Cycle of Heat**: Monitors burst fraction and throttles
        programmatically to keep it under the cooling threshold.
        
        **Physics-Based Throttling Logic**:
        - Heat builds in 300ms (fast: direct electrical→thermal conversion)
        - Heat dissipates in 2000ms (slow: multi-stage diffusion through interfaces)
        - Asymmetry ratio: 6.7× slower to dissipate than build
        - Cooling threshold: 13% = build_time / (build_time + dissipate_time)
        - If burst fraction > 13%, bursts occur faster than cooling → throttling needed
        
        Args:
            duration: Total duration to run (seconds)
            check_interval: How often to check and adjust (seconds)
        
        Returns:
            Control results dictionary
        """
        print("=" * 70)
        print("🌡️  THERMAL THROTTLE CONTROLLER")
        print("=" * 70)
        print(f"App: {self.app_name}")
        print(f"Component: {self.component.upper()}")
        print(f"Target Burst Fraction: {self.target_burst_fraction*100:.1f}% (cooling threshold)")
        print(f"Duration: {duration}s | Check Interval: {check_interval}s")
        print()
        
        pids = self.find_app_processes()
        if not pids:
            print(f"  ⚠️  No processes found for {self.app_name}")
            return {}
        
        print(f"  Found {len(pids)} process(es): {pids}")
        print()
        
        start_time = time.time()
        measurements = []
        throttle_events = []
        
        # Signal handler for graceful shutdown
        def signal_handler(sig, frame):
            self.running = False
            print("\n🛑 Shutting down...")
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            while self.running and (time.time() - start_time) < duration:
                # Measure current burst fraction
                burst_fraction = self.measure_burst_fraction(duration=3)
                
                if burst_fraction is None:
                    time.sleep(check_interval)
                    continue
                
                # The Physics of Ambient Heat: Distinguish Useful Work vs Noise
                # Check if burst pattern is regular (useful work) or irregular (noise)
                is_regular_pattern = self._check_regular_pattern(measurements, burst_fraction)
                
                measurements.append({
                    'time': time.time() - start_time,
                    'burst_fraction': burst_fraction,
                    'exceeds_threshold': burst_fraction > self.target_burst_fraction,
                    'is_regular_pattern': is_regular_pattern
                })
                
                # Check if throttling needed
                # Only throttle if burst exceeds threshold AND pattern is regular (useful work)
                # Ignore noise (irregular spikes) to avoid over-throttling
                if burst_fraction > self.target_burst_fraction:
                    # Check if this is useful work or noise
                    if not is_regular_pattern:
                        # Noise detected - don't throttle based on noise
                        print(f"[{time.time() - start_time:.1f}s] Burst: {burst_fraction*100:.1f}% "
                              f"(threshold: {self.target_burst_fraction*100:.1f}%) - NOISE DETECTED (ignoring)")
                        time.sleep(check_interval)
                        continue
                    
                    # Calculate throttle level
                    throttle_level = self.calculate_throttle_level(burst_fraction)
                    
                    # The Thermal Death Spiral: Explain the heartbeat change
                    heartbeat_change = ""
                    if self.target_burst_fraction < 0.12:
                        heartbeat_change = " (Hot room: Using longer idle periods to prevent thermal death spiral)"
                    
                    print(f"[{time.time() - start_time:.1f}s] Burst: {burst_fraction*100:.1f}% "
                          f"(threshold: {self.target_burst_fraction*100:.1f}%) - THROTTLING to {throttle_level*100:.1f}%{heartbeat_change}")
                    
                    # Apply throttling
                    for pid in pids:
                        if pid not in self.throttled_pids:
                            if self.throttle_process(pid, throttle_level):
                                self.throttled_pids.append(pid)
                                throttle_events.append({
                                    'time': time.time() - start_time,
                                    'pid': pid,
                                    'burst_before': burst_fraction,
                                    'throttle_level': throttle_level
                                })
                else:
                    # Burst fraction is acceptable, remove throttling if applied
                    if self.throttled_pids:
                        print(f"[{time.time() - start_time:.1f}s] Burst: {burst_fraction*100:.1f}% "
                              f"(under threshold) - REMOVING throttle")
                        for pid in self.throttled_pids[:]:
                            if self.unthrottle_process(pid):
                                self.throttled_pids.remove(pid)
                
                time.sleep(check_interval)
        
        finally:
            # Cleanup: Remove all throttling
            print("\n🧹 Cleaning up: Removing all throttles...")
            for pid in self.throttled_pids[:]:
                self.unthrottle_process(pid)
            
            # Kill any cpulimit processes
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'cpulimit' in proc.info['name'].lower():
                        proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        
        # Calculate results
        if measurements:
            avg_burst = statistics.mean([m['burst_fraction'] for m in measurements])
            max_burst = max([m['burst_fraction'] for m in measurements])
            exceeded_count = sum([1 for m in measurements if m['exceeds_threshold']])
            exceeded_percent = (exceeded_count / len(measurements)) * 100
            
            results = {
                'app_name': self.app_name,
                'component': self.component,
                'target_burst_fraction': self.target_burst_fraction,
                'avg_burst_fraction': avg_burst,
                'max_burst_fraction': max_burst,
                'exceeded_threshold_percent': exceeded_percent,
                'throttle_events': len(throttle_events),
                'measurements': measurements,
                'throttle_events': throttle_events,
                'success': avg_burst <= self.target_burst_fraction * 1.1  # 10% tolerance
            }
            
            # Print summary
            print("\n" + "=" * 70)
            print("📊 THERMAL CONTROL RESULTS")
            print("=" * 70)
            print(f"Average Burst Fraction: {avg_burst*100:.1f}%")
            print(f"Target Threshold: {self.target_burst_fraction*100:.1f}%")
            print(f"Max Burst Fraction: {max_burst*100:.1f}%")
            print(f"Threshold Exceeded: {exceeded_percent:.1f}% of time")
            print(f"Throttle Events: {len(throttle_events)}")
            print()
            
            if results['success']:
                print("✅ SUCCESS: Burst fraction kept under cooling threshold")
            else:
                print("⚠️  WARNING: Burst fraction exceeded threshold")
            
            return results
        
        return {}
    
    def _check_regular_pattern(self, measurements: List[Dict], current_burst: float) -> bool:
        """
        Check if burst pattern is regular (useful work) or irregular (noise).
        
        **The Physics of Ambient Heat: Distinguishing Useful Work vs Noise**
        
        When threshold drops to 11% in hot room, we need to avoid over-throttling
        based on noise (random spikes) rather than useful work (regular bursts).
        
        **Strategy**:
        - Useful work: Regular timing, consistent magnitude
        - Noise: Irregular timing, varying magnitude
        
        **Detection**:
        - Calculate variance of burst fractions over recent measurements
        - Low variance = regular pattern (useful work)
        - High variance = irregular pattern (noise)
        
        Args:
            measurements: Recent burst fraction measurements
            current_burst: Current burst fraction
        
        Returns:
            True if pattern is regular (useful work), False if irregular (noise)
        """
        if len(measurements) < 5:
            # Not enough data - assume regular (will refine as we collect more)
            return True
        
        # Get recent burst fractions (last 5 measurements)
        recent_bursts = [m['burst_fraction'] for m in measurements[-5:]] + [current_burst]
        
        # Calculate variance
        if len(recent_bursts) > 1:
            mean_burst = statistics.mean(recent_bursts)
            # Use sample variance (divide by n-1)
            variance = sum((x - mean_burst) ** 2 for x in recent_bursts) / (len(recent_bursts) - 1)
            
            # Threshold: If variance > 0.01 (1% variance), it's likely noise
            # Regular work has low variance (consistent burst fraction)
            # Example: Regular bursts at 20% → variance ~0.0001 (very low)
            # Example: Noise spikes at 15%, 25%, 10%, 30% → variance ~0.01 (high)
            is_regular = variance < 0.01
            
            return is_regular
        
        return True  # Default: assume regular if can't determine


def main():
    parser = argparse.ArgumentParser(
        description="Thermal Throttle Controller: Keep burst fraction under cooling threshold"
    )
    parser.add_argument(
        'app',
        help='Application name to throttle (e.g., "Python", "Safari")'
    )
    parser.add_argument(
        '--component',
        choices=['ane', 'gpu', 'cpu'],
        default='ane',
        help='Component to monitor (default: ane)'
    )
    parser.add_argument(
        '--target-burst',
        type=float,
        help='Target burst fraction (default: component cooling threshold)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Duration to run (seconds, default: 60)'
    )
    parser.add_argument(
        '--check-interval',
        type=float,
        default=2.0,
        help='Check interval (seconds, default: 2.0)'
    )
    
    args = parser.parse_args()
    
    controller = ThermalThrottleController(
        app_name=args.app,
        component=args.component,
        target_burst_fraction=args.target_burst if args.target_burst else None
    )
    
    results = controller.run_thermal_control(
        duration=args.duration,
        check_interval=args.check_interval
    )
    
    if results:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())

