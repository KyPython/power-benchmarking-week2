#!/usr/bin/env python3
"""
Auto Re-run on Skew Detection
Automatically offers to re-run benchmark when significant divergence is detected.
"""

import sys
import time
import numpy as np
from typing import List, Optional, Callable, Dict
from collections import deque


class SkewDetector:
    """
    Detects skew in real-time and offers automatic re-run.
    """
    
    def __init__(
        self,
        detection_threshold: float = 0.01,  # 1% divergence
        drop_fraction_threshold: float = 0.0235,  # 2.35% drop fraction
        min_samples: int = 20,
        rerun_callback: Optional[Callable] = None
    ):
        """
        Initialize skew detector.
        
        Args:
            detection_threshold: Divergence threshold (0.01 = 1%)
            drop_fraction_threshold: Drop fraction threshold (0.0235 = 2.35%)
            min_samples: Minimum samples before detection
            rerun_callback: Function to call for re-run
        """
        self.detection_threshold = detection_threshold
        self.drop_fraction_threshold = drop_fraction_threshold
        self.min_samples = min_samples
        self.rerun_callback = rerun_callback
        
        self.power_history = deque(maxlen=1000)
        self.detection_count = 0
        self.last_detection_time = None
        self.auto_rerun_enabled = False
    
    def add_sample(self, power_mw: float):
        """Add a power sample and check for skew."""
        self.power_history.append(power_mw)
        
        if len(self.power_history) < self.min_samples:
            return None
        
        # Calculate divergence
        power_array = np.array(self.power_history)
        mean_power = np.mean(power_array)
        median_power = np.median(power_array)
        
        if median_power == 0:
            return None
        
        divergence = abs(mean_power - median_power) / median_power
        
        # Estimate drop fraction
        low_power = np.min(power_array)
        high_power = median_power
        
        if high_power > low_power:
            drop_fraction = (mean_power - high_power) / (low_power - high_power)
            drop_fraction = max(0, min(1, drop_fraction))
        else:
            drop_fraction = 0.0
        
        # Check if threshold exceeded
        if divergence >= self.detection_threshold or drop_fraction >= self.drop_fraction_threshold:
            self.detection_count += 1
            self.last_detection_time = time.time()
            
            return {
                'divergence': divergence,
                'divergence_pct': divergence * 100,
                'drop_fraction': drop_fraction,
                'drop_fraction_pct': drop_fraction * 100,
                'mean': mean_power,
                'median': median_power,
                'samples': len(self.power_history),
                'detection_count': self.detection_count
            }
        
        return None
    
    def should_offer_rerun(self, detection: Dict) -> bool:
        """
        Determine if we should offer automatic re-run.
        
        Criteria:
        - Divergence > 1% OR drop fraction > 2.35%
        - Multiple detections (persistent background task)
        - Not too frequent (avoid spam)
        """
        if not detection:
            return False
        
        # Check if thresholds exceeded
        if (detection['divergence_pct'] > 1.0 or 
            detection['drop_fraction_pct'] > 2.35):
            
            # Offer re-run if:
            # 1. Significant divergence (>5%) OR
            # 2. Multiple detections (persistent task) OR
            # 3. Drop fraction > 5% (substantial background interference)
            if (detection['divergence_pct'] > 5.0 or
                detection['detection_count'] >= 3 or
                detection['drop_fraction_pct'] > 5.0):
                return True
        
        return False
    
    def offer_rerun(self, detection: Dict) -> bool:
        """
        Offer automatic re-run to user.
        
        Returns:
            True if user accepts, False otherwise
        """
        print("\n" + "=" * 70)
        print("⚠️  BACKGROUND TASK INTERFERENCE DETECTED")
        print("=" * 70)
        print()
        print(f"📊 Detection Results:")
        print(f"   Divergence: {detection['divergence_pct']:.2f}%")
        print(f"   Drop Fraction: {detection['drop_fraction_pct']:.2f}%")
        print(f"   Mean: {detection['mean']:.1f} mW")
        print(f"   Median: {detection['median']:.1f} mW")
        print(f"   Detections: {detection['detection_count']}")
        print()
        print("💡 Background task detected (e.g., Spotlight, Time Machine, iCloud)")
        print("   This may affect measurement accuracy.")
        print()
        print("🔄 Options:")
        print("   1. Continue current benchmark (use median for typical power)")
        print("   2. Wait and re-run automatically when background task completes")
        print("   3. Cancel and re-run manually later")
        print()
        
        if self.auto_rerun_enabled:
            print("✅ Auto re-run enabled - will wait for background task to complete")
            return True
        
        try:
            response = input("   Your choice (1/2/3) [default: 1]: ").strip()
            
            if response == "2":
                print("\n⏳ Waiting for background task to complete...")
                print("   Monitoring power for stabilization...")
                return True
            elif response == "3":
                print("\n❌ Cancelling benchmark. Please re-run manually when ready.")
                return False
            else:
                print("\n✅ Continuing benchmark. Use median for typical power.")
                return False
        except (EOFError, KeyboardInterrupt):
            print("\n✅ Continuing benchmark (default).")
            return False
    
    def wait_for_stabilization(
        self,
        power_queue,
        max_wait: float = 60.0,
        stability_threshold: float = 0.005  # 0.5% stability
    ) -> bool:
        """
        Wait for power to stabilize (background task completes).
        
        Returns:
            True if stabilized, False if timeout
        """
        start_time = time.time()
        recent_samples = deque(maxlen=20)
        
        print(f"   Waiting up to {max_wait:.0f} seconds for stabilization...")
        
        while (time.time() - start_time) < max_wait:
            # Collect samples
            while not power_queue.empty():
                try:
                    _, power_mw = power_queue.get_nowait()
                    recent_samples.append(power_mw)
                except:
                    pass
            
            if len(recent_samples) >= 10:
                # Check stability (low variance)
                samples_array = np.array(recent_samples)
                mean = np.mean(samples_array)
                std = np.std(samples_array)
                cv = std / mean if mean > 0 else 0  # Coefficient of variation
                
                if cv < stability_threshold:
                    print(f"   ✅ Power stabilized at {mean:.1f} mW (CV: {cv*100:.2f}%)")
                    return True
            
            time.sleep(0.5)
            print(".", end="", flush=True)
        
        print(f"\n   ⚠️  Timeout after {max_wait:.0f} seconds")
        return False


def create_skew_detector(
    detection_threshold: float = 0.01,
    auto_rerun: bool = False,
    rerun_callback: Optional[Callable] = None
) -> SkewDetector:
    """
    Create a skew detector instance.
    
    Args:
        detection_threshold: Divergence threshold (0.01 = 1%)
        auto_rerun: Enable automatic re-run without prompting
        rerun_callback: Function to call for re-run
    
    Returns:
        SkewDetector instance
    """
    detector = SkewDetector(
        detection_threshold=detection_threshold,
        rerun_callback=rerun_callback
    )
    detector.auto_rerun_enabled = auto_rerun
    return detector


# Example usage
if __name__ == "__main__":
    detector = create_skew_detector()
    
    # Simulate power samples with background task
    print("Testing skew detection...")
    
    # Normal samples
    for i in range(20):
        detector.add_sample(2000.0 + np.random.normal(0, 50))
    
    # Background task starts (drops to 1500 mW for 20% of time)
    for i in range(30):
        if i % 5 == 0:  # 20% drop
            detector.add_sample(1500.0)
        else:
            detector.add_sample(2000.0 + np.random.normal(0, 50))
        
        detection = detector.add_sample(2000.0)
        if detection:
            print(f"\n⚠️  Detection: {detection['divergence_pct']:.2f}% divergence")
            
            if detector.should_offer_rerun(detection):
                if detector.offer_rerun(detection):
                    print("✅ Re-run accepted")
                else:
                    print("ℹ️  Re-run declined, continuing")
                break

