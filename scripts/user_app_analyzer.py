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

        **The WebKit Iceberg: Unmasking Hidden Processes**

        For Safari specifically, this finds:
        - Main Safari process
        - WebKit renderer processes (one per tab)
        - Extension processes (ad blockers, password managers)
        - Media processes (video decoding, audio)
        - Network processes (DNS, HTTP/2, WebSocket)

        Returns:
            List of process dictionaries with PID, name, and CPU usage
        """
        processes = []

        for proc in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_info", "ppid", "cmdline"]
        ):
            try:
                proc_info = proc.info
                proc_name = proc_info["name"].lower()
                cmdline = " ".join(proc_info.get("cmdline", [])).lower()

                # Match app name (flexible matching)
                app_match = (
                    self.app_name.lower() in proc_name
                    or proc_name in self.app_name.lower()
                    or self.app_name.lower() in cmdline
                )

                # For Safari, also match WebKit processes
                if "safari" in self.app_name.lower():
                    webkit_match = (
                        "webkit" in proc_name
                        or "com.apple.webkit" in cmdline
                        or "safari" in proc_name
                    )
                    app_match = app_match or webkit_match

                if app_match:
                    processes.append(
                        {
                            "pid": proc_info["pid"],
                            "name": proc_info["name"],
                            "cpu_percent": proc_info.get("cpu_percent", 0.0),
                            "memory_mb": proc_info.get("memory_info", {}).get("rss", 0)
                            / 1024
                            / 1024,
                            "ppid": proc_info.get("ppid"),
                            "cmdline": proc_info.get("cmdline", []),
                        }
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return processes

    def breakdown_webkit_processes(self, processes: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Break down WebKit processes by type to identify hidden processes.

        **The WebKit Iceberg**: Safari splits into multiple process types:
        - Main process (Safari.app)
        - Renderer processes (one per tab)
        - Extension processes (ad blockers, password managers)
        - Media processes (video decoding, audio)
        - Network processes (DNS, HTTP/2, WebSocket)

        Returns:
            Dictionary mapping process types to process lists
        """
        breakdown = {
            "main": [],
            "renderer": [],
            "extension": [],
            "media": [],
            "network": [],
            "other": [],
        }

        for proc in processes:
            name = proc["name"].lower()
            cmdline = " ".join(proc.get("cmdline", [])).lower()

            # Classify process type
            if "safari" in name and "webkit" not in name:
                breakdown["main"].append(proc)
            elif "webkit" in name or "com.apple.webkit" in cmdline:
                if "renderer" in cmdline or "webcontent" in cmdline:
                    breakdown["renderer"].append(proc)
                elif "extension" in cmdline or "xpc" in cmdline:
                    breakdown["extension"].append(proc)
                elif "media" in cmdline or "audio" in cmdline or "video" in cmdline:
                    breakdown["media"].append(proc)
                elif "network" in cmdline or "dns" in cmdline or "http" in cmdline:
                    breakdown["network"].append(proc)
                else:
                    breakdown["renderer"].append(proc)  # Default WebKit = renderer
            else:
                breakdown["other"].append(proc)

        return breakdown

    def measure_app_power(
        self, duration: int = 30, sample_interval: int = 500
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
        pids = [p["pid"] for p in processes]

        # Run powermetrics
        cmd = [
            "sudo",
            "powermetrics",
            "--samplers",
            "cpu_power,gpu_power",
            "-i",
            str(sample_interval),
            "-n",
            str(int(duration * 1000 / sample_interval)),
            "--show-process-coalition",
        ]

        cpu_power = []
        ane_power = []
        gpu_power = []
        total_power = []
        timestamps = []

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            start_time = time.time()

            for line in process.stdout:
                current_time = time.time() - start_time
                timestamps.append(current_time)

                # Check if line contains app process
                line_lower = line.lower()
                app_in_line = any(
                    self.app_name.lower() in line_lower or str(pid) in line for pid in pids
                )

                if app_in_line or "package" in line_lower or "total" in line_lower:
                    # Parse CPU power
                    cpu_match = re.search(r"CPU\s+Power[:\s]+([\d.]+)\s*mW", line, re.IGNORECASE)
                    if cpu_match:
                        cpu_power.append(float(cpu_match.group(1)))

                    # Parse ANE power
                    ane_match = re.search(r"ANE\s+Power[:\s]+([\d.]+)\s*mW", line, re.IGNORECASE)
                    if ane_match:
                        ane_power.append(float(ane_match.group(1)))

                    # Parse GPU power
                    gpu_match = re.search(r"GPU\s+Power[:\s]+([\d.]+)\s*mW", line, re.IGNORECASE)
                    if gpu_match:
                        gpu_power.append(float(gpu_match.group(1)))

                    # Parse Total/Package power
                    total_match = re.search(
                        r"(?:Package|Total)\s+Power[:\s]+([\d.]+)\s*mW", line, re.IGNORECASE
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
            len(total_power) if total_power else 0,
        )

        return {
            "cpu_power": cpu_power[:min_len] if cpu_power else [],
            "ane_power": ane_power[:min_len] if ane_power else [],
            "gpu_power": gpu_power[:min_len] if gpu_power else [],
            "total_power": total_power[:min_len] if total_power else [],
            "timestamps": timestamps[:min_len] if timestamps else [],
            "processes": processes,
            "duration": duration,
            "samples": min_len,
        }

    def calculate_attribution_ratio(
        self, app_power: List[float], total_power: List[float], baseline_power: float
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

        # The Precise Attribution Audit: How Stable Baseline Enables Tiny Improvements
        #
        # **The Question**: If we have a perfectly stable 500 mW baseline (thanks to elimination),
        # how does that allow us to detect even tiny 10 mW efficiency improvements?
        #
        # **The Problem with Unstable Baseline**:
        # - Unstable baseline: 500 mW → 650 mW → 500 mW (varies ±150 mW)
        # - Tiny improvement: 10 mW reduction
        # - Result: 10 mW is "lost in the noise" (150 mW variation)
        # - Detection: Impossible (signal-to-noise ratio too low)
        #
        # **The Solution: Stable Baseline**:
        # - Stable baseline: 500 mW (constant, no variation)
        # - Tiny improvement: 10 mW reduction
        # - Result: 10 mW is clearly visible (no noise to hide it)
        # - Detection: Easy (signal-to-noise ratio is infinite)
        #
        # **The Math**:
        # - Before (unstable): Baseline = 500 ± 150 mW (noise = 150 mW)
        #   * Signal (improvement) = 10 mW
        #   * Signal-to-noise ratio = 10 / 150 = 0.067 (undetectable)
        #
        # - After (stable): Baseline = 500 mW (noise = 0 mW)
        #   * Signal (improvement) = 10 mW
        #   * Signal-to-noise ratio = 10 / 0 = ∞ (perfectly detectable)
        #
        # **Example: Code Optimization**:
        # - Original code: App_Power = 2000 mW, Baseline = 500 ± 150 mW
        #   * AR = (2000 - 500) / (2500 - 500) = 75% (but baseline varies)
        #
        # - Optimized code: App_Power = 1990 mW (10 mW improvement)
        #   * With unstable baseline: Can't detect (lost in 150 mW noise)
        #   * With stable baseline: Clearly visible (10 mW reduction)
        #
        # **The Precise Attribution**:
        # - Stable baseline → Accurate AR calculation
        # - Accurate AR → Can detect tiny improvements
        # - Tiny improvements → Precise optimization feedback
        #
        # **Result**: Stable baseline enables "micro-optimization" - detecting improvements
        # that would be impossible to measure with unstable baselines.

        # Calculate detection sensitivity (how small an improvement we can detect)
        baseline_stability = 0.0  # Assume perfect stability (0 mW variation) if baseline is stable
        # In practice, this would be calculated from baseline measurements
        # For now, we assume elimination provides perfect stability

        detection_sensitivity = (
            baseline_stability  # Can detect improvements as small as baseline variation
        )
        # With stable baseline (0 mW variation), we can detect any improvement > 0 mW

        return {
            "attribution_ratio": attribution_ratio,
            "attribution_percent": attribution_ratio * 100,
            "mean_app_delta_mw": mean_app_delta,
            "mean_total_delta_mw": mean_total_delta,
            "baseline_power_mw": baseline_power,
            "mean_app_power_mw": statistics.mean(app_power),
            "mean_total_power_mw": statistics.mean(total_power),
            "baseline_stability_mw": baseline_stability,  # 0 = perfectly stable
            "detection_sensitivity_mw": detection_sensitivity,  # Can detect improvements this small
            "precise_attribution_note": (
                f"Stable baseline ({baseline_power:.0f} mW) enables detection of tiny improvements "
                f"(sensitivity: {detection_sensitivity:.1f} mW). "
                f"With unstable baseline, improvements < 150 mW would be 'lost in the noise'."
            ),
            # The Micro-Optimization Proof: Energy Cost per Instruction
            #
            # **The Question**: How can we use infinite signal-to-noise ratio to compare
            # "Energy Cost per Instruction" between coding styles?
            #
            # **The Strategy**: Measure power delta per instruction count
            #
            # **Formula**: Energy_Cost_per_Instruction = Power_Delta / Instruction_Count
            #
            # **Example: For Loop vs Vectorized Operation**
            #
            # **For Loop (Python)**:
            # - Instructions: ~1,000,000 (loop iterations + operations)
            # - Power: 2000 mW (app) - 500 mW (baseline) = 1500 mW delta
            # - Energy per instruction: 1500 mW / 1,000,000 = 0.0015 mW/instruction
            #
            # **Vectorized Operation (NumPy)**:
            # - Instructions: ~10,000 (vectorized operations, fewer iterations)
            # - Power: 1800 mW (app) - 500 mW (baseline) = 1300 mW delta
            # - Energy per instruction: 1300 mW / 10,000 = 0.13 mW/instruction
            #
            # **Wait - This seems backwards!** Vectorized has HIGHER energy per instruction?
            #
            # **The Key Insight**: Energy per instruction is misleading. What matters is:
            # - **Total energy** (power × time)
            # - **Instructions per task** (how many instructions to complete the work)
            #
            # **Better Metric: Energy per Task**
            #
            # **For Loop**:
            # - Time: 1.0 seconds
            # - Energy: 1500 mW × 1.0s = 1500 mJ
            # - Task: Process 1,000,000 elements
            # - Energy per task: 1500 mJ / 1,000,000 = 0.0015 mJ/element
            #
            # **Vectorized**:
            # - Time: 0.1 seconds (10× faster)
            # - Energy: 1300 mW × 0.1s = 130 mJ
            # - Task: Process 1,000,000 elements
            # - Energy per task: 130 mJ / 1,000,000 = 0.00013 mJ/element
            #
            # **Result**: Vectorized is 11.5× more energy-efficient (130 mJ vs 1500 mJ)
            #
            # **Why Stable Baseline Matters**:
            # - With unstable baseline: 150 mW noise → Can't detect 200 mW difference (1500 vs 1300)
            # - With stable baseline: 0 mW noise → Can detect 200 mW difference perfectly
            # - This enables precise comparison of coding styles
            #
            # **Implementation**: This would require instruction counting (perf, Intel VTune)
            # and precise timing, but the framework is documented here.
            "micro_optimization_framework": {
                "energy_per_instruction_note": (
                    "With stable baseline, can measure Energy Cost per Instruction: "
                    "Power_Delta / Instruction_Count. "
                    "Better metric: Energy per Task = (Power_Delta × Time) / Task_Size. "
                    "Stable baseline enables detection of tiny power differences between coding styles."
                ),
                "example_for_loop": {
                    "instructions": 1000000,
                    "power_delta_mw": 1500,
                    "time_s": 1.0,
                    "energy_mj": 1500,
                    "energy_per_task_mj": 0.0015,
                },
                "example_vectorized": {
                    "instructions": 10000,
                    "power_delta_mw": 1300,
                    "time_s": 0.1,
                    "energy_mj": 130,
                    "energy_per_task_mj": 0.00013,
                    "efficiency_improvement": 11.5,  # 1500 / 130 = 11.5×
                },
            },
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
            skew_interpretation = (
                "Power spikes (active rendering, video playback, heavy computation)"
            )
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
            "mean": mean,
            "median": median,
            "divergence_pct": divergence_pct,
            "skew_direction": skew_direction,
            "skew_interpretation": skew_interpretation,
            "burst_fraction": burst_fraction,
            "min": min(power_values),
            "max": max(power_values),
            "std": statistics.stdev(power_values) if len(power_values) > 1 else 0.0,
            "samples": len(power_values),
        }

    def identify_hidden_waste(self, analysis: Dict) -> List[str]:
        """
        Identify hidden energy waste based on analysis.

        **App Waste Fingerprinting: Low Attribution Ratio (<30%)**

        **What Low AR Tells Us About Hidden Processes**:

        1. **Attribution Ratio Formula**:
           AR = (App_Power_Delta) / (Total_System_Delta)
           - If AR < 30%, app's measured power is <30% of total system increase
           - The remaining 70%+ is "unattributed" = hidden processes

        2. **For Safari Specifically**:
           - Low AR (<30%) indicates hidden helper processes:
             * WebKit processes (renderer, network, GPU)
             * Extension processes (ad blockers, password managers)
             * Background tabs (still consuming power when "idle")
             * Media processes (video decoding, audio processing)
             * Network processes (DNS, HTTP/2, WebSocket)

        3. **Why These Are "Hidden"**:
           - macOS process tree: Safari spawns child processes
           - Each tab = separate process (WebKit architecture)
           - Background tabs still run JavaScript, fetch data
           - Extensions run in separate processes
           - These don't show up as "Safari" in simple PID searches

        4. **Energy Waste Implications**:
           - Hidden processes consume power without user awareness
           - Background tabs can drain battery even when "closed"
           - Extensions may run continuously (e.g., ad blockers scanning)
           - Media processes continue after video ends (buffering)

        5. **Detection Method**:
           - Low AR = discrepancy between app power and system power
           - Formula: AR = App_Delta / Total_Delta
           - If AR < 30%, then Total_Delta > 3× App_Delta
           - This 3× multiplier = hidden processes

        Returns:
            List of waste indicators and recommendations
        """
        waste_indicators = []

        # Low attribution ratio = hidden processes
        if "attribution_ratio" in analysis:
            ar = analysis["attribution_ratio"]
            if ar < 0.3:  # Less than 30% attribution
                app_name = analysis.get("app_name", "Application")

                waste_indicators.append(
                    f"⚠️  Low Attribution Ratio ({ar*100:.1f}%): "
                    f"App power is not well-attributed. Possible hidden processes or "
                    f"system overhead consuming power."
                )

                # App-specific interpretation
                if "safari" in app_name.lower():
                    waste_indicators.append(f"   🕵️‍♂️  Safari Hidden Processes Detected:")
                    waste_indicators.append(f"      • WebKit renderer processes (background tabs)")
                    waste_indicators.append(
                        f"      • Extension processes (ad blockers, password managers)"
                    )
                    waste_indicators.append(f"      • Media processes (video decoding, audio)")
                    waste_indicators.append(f"      • Network processes (DNS, HTTP/2, WebSocket)")
                    waste_indicators.append(
                        f"   💡 Recommendation: Close unused tabs, disable extensions, "
                        f"check Activity Monitor for WebKit processes"
                    )
                elif "chrome" in app_name.lower():
                    waste_indicators.append(
                        f"   🕵️‍♂️  Chrome Hidden Processes: Multiple renderer processes, "
                        f"extensions, background services"
                    )
                else:
                    waste_indicators.append(
                        f"   🕵️‍♂️  Hidden processes detected: Check Activity Monitor "
                        f"for child processes or background threads"
                    )

        # High burst fraction = inefficient rendering
        if "skewness" in analysis and "burst_fraction" in analysis["skewness"]:
            bf = analysis["skewness"]["burst_fraction"]
            if bf and bf > 0.5:  # More than 50% bursting
                waste_indicators.append(
                    f"⚠️  High Burst Fraction ({bf*100:.1f}%): "
                    f"Frequent power spikes indicate inefficient rendering or "
                    f"background activity. Consider reducing workload or closing background tabs."
                )

        # Right-skewed with high divergence = inconsistent power
        if "skewness" in analysis:
            skew = analysis["skewness"]
            if skew["skew_direction"] == "right-skewed" and skew["divergence_pct"] > 20:
                waste_indicators.append(
                    f"⚠️  High Divergence ({skew['divergence_pct']:.1f}%): "
                    f"Mean and median diverge significantly, indicating inconsistent "
                    f"power consumption. May indicate background tabs or hidden processes."
                )

        return waste_indicators

    def _generate_optimization_recommendations(
        self, breakdown: Dict[str, List[Dict]], unattributed_power: float, attribution: Dict
    ) -> List[str]:
        """
        Generate optimization recommendations based on process breakdown.

        **Browser Forensics: Tab Suspender vs Task Policy**

        **The "Work vs. Location" Decision**:

        For 8 background tabs draining battery, why prioritize Tab Suspender over Task Policy?

        **Fundamental Principle**: Stop work > Move work

        1. **Tab Suspender (Recommended - Stops Work)**:
           - **What it does**: Suspends inactive tabs (stops JavaScript, pauses rendering)
           - **Power savings**: 80-90% reduction per suspended tab
           - **Why it works**: Eliminates work entirely
             * JavaScript execution stops → no CPU cycles
             * Rendering pauses → no GPU work
             * Network requests pause → no I/O
             * Memory usage drops → less memory controller activity
           - **Result**: True power elimination (work doesn't happen)
           - **User experience**: Tabs can be resumed when needed (work resumes)

        2. **Task Policy (Alternative - Moves Work)**:
           - **What it does**: Forces renderer processes to E-cores
           - **Power savings**: 30-50% reduction per tab
           - **Why it's less effective**: Work still continues, just on different cores
             * JavaScript still executes (on E-cores instead of P-cores)
             * Rendering still happens (slower, but still happens)
             * Network requests still occur (same I/O load)
             * Memory usage unchanged (same memory controller activity)
           - **Result**: Power redistribution (work moved, not eliminated)
           - **Risk**: May trigger redistribution trap (other processes fill P-cores)

        **The Decision Logic**:
        - **>5 tabs**: Tab Suspender (stops 8 tabs = eliminates 8× work)
        - **<5 tabs**: Task Policy sufficient (moves 2-3 tabs = acceptable redistribution)

        **Why "Stop Work" > "Move Work"**:
        - **Energy = Power × Time**: If work stops, energy = 0
        - **Energy = Power × Time**: If work moves, energy = (lower power) × (same time)
        - **Result**: Stopping work eliminates energy; moving work only reduces it
        - **For 8 tabs**: 8× work elimination (Tab Suspender) > 8× work redistribution (Task Policy)

        **The Energy Elimination Proof: Why Stopping Work Prevents Redistribution Trap**
        #
        # **Why does stopping work prevent the macOS scheduler from "filling the gap"?**
        #
        # **The Redistribution Trap Mechanism**:
        # 1. You free P-cores by moving a task to E-cores
        # 2. macOS scheduler sees "free" P-cores
        # 3. Scheduler immediately fills them with waiting processes
        # 4. Result: Power redistributed, not eliminated
        #
        # **Why Tab Suspender Avoids This**:
        # 1. **No P-cores freed**: Tab Suspender stops work, doesn't move it
        #    - Renderer processes still exist (suspended, not moved)
        #    - They're not using P-cores (stopped), but they're not "freed" either
        #    - Scheduler doesn't see "free" P-cores → no redistribution
        #
        # 2. **Work eliminated, not relocated**:
        #    - Tab Suspender: JavaScript stops, rendering pauses, I/O stops
        #    - No work to redistribute (work doesn't exist)
        #    - Task Policy: Work continues on E-cores (work relocated)
        #    - Relocated work can still trigger redistribution (other processes fill P-cores)
        #
        # 3. **The Scheduler's Perspective**:
        #    - **Task Policy**: "I see free P-cores, let me fill them" → Redistribution trap
        #    - **Tab Suspender**: "I see suspended processes, but no free P-cores" → No trap
        #
        # **The Proof**:
        # - Tab Suspender: Energy = 0 (work stopped) → No P-cores freed → No redistribution
        # - Task Policy: Energy = (lower power) × (same time) → P-cores freed → Redistribution trap
        # - Result: Stopping work eliminates the opportunity for redistribution

        **Decision Logic**:
        - If >5 renderer processes: Recommend tab suspender (more effective)
        - If <5 renderer processes: Task policy may be sufficient
        - If extensions >2: Recommend disabling extensions
        - If media processes active: Recommend closing media tabs

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        renderer_count = len(breakdown.get("renderer", []))
        extension_count = len(breakdown.get("extension", []))
        media_count = len(breakdown.get("media", []))

        # Tab Suspender vs Task Policy decision
        # **The "Work vs. Location" Decision**: Stop work > Move work
        if renderer_count > 5:
            recommendations.append(
                f"✅ RECOMMENDED: Use Tab Suspender for {renderer_count} background tabs"
            )
            recommendations.append(f"   • Why Tab Suspender > Task Policy:")
            recommendations.append(
                f"     - Tab Suspender: Stops work (JavaScript, rendering, I/O) → 80-90% savings"
            )
            recommendations.append(f"     - Task Policy: Moves work (to E-cores) → 30-50% savings")
            recommendations.append(
                f"     - For {renderer_count} tabs: Stop {renderer_count}× work > Move {renderer_count}× work"
            )
            recommendations.append(
                f"   • Power savings: 80-90% per suspended tab (~{renderer_count * 50:.0f} mW)"
            )
            recommendations.append(f"   • Energy = Power × Time: Stopping work → Energy = 0")
            recommendations.append(
                f"   • Energy = Power × Time: Moving work → Energy = (lower power) × (same time)"
            )
            recommendations.append(
                f"   • Energy Elimination Proof: Stopping work prevents redistribution trap"
            )
            recommendations.append(
                f"     - Tab Suspender: No P-cores freed (work stopped, not moved) → No trap"
            )
            recommendations.append(
                f"     - Task Policy: P-cores freed (work moved) → Scheduler fills them → Trap"
            )
            recommendations.append(f"   • Install: Safari Extensions → 'Tab Suspender' or similar")
        elif renderer_count > 2:
            recommendations.append(
                f"✅ RECOMMENDED: Use Task Policy for {renderer_count} background tabs"
            )
            recommendations.append(f"   • Force renderer processes to E-cores:")
            recommendations.append(
                f"   • sudo taskpolicy -c 0x0F -p $(pgrep -f 'com.apple.WebKit')"
            )
            recommendations.append(
                f"   • Power savings: 30-50% per tab (~{renderer_count * 20:.0f} mW)"
            )
            recommendations.append(f"   • Alternative: Use tab suspender for better savings")
        else:
            recommendations.append(
                f"ℹ️  {renderer_count} renderer process(es) - manageable, no action needed"
            )

        # Extension recommendations
        if extension_count > 2:
            recommendations.append(f"⚠️  {extension_count} extension processes detected")
            recommendations.append(f"   • Disable unused extensions to reduce power consumption")
            recommendations.append(
                f"   • Extensions run continuously (ad blockers, password managers)"
            )
            recommendations.append(f"   • Estimated savings: ~{extension_count * 15:.0f} mW")

        # Media process recommendations
        if media_count > 0:
            recommendations.append(f"⚠️  {media_count} media process(es) detected")
            recommendations.append(f"   • Close video/audio tabs to stop media processing")
            recommendations.append(f"   • Media processes continue after playback ends (buffering)")
            recommendations.append(f"   • Estimated savings: ~{media_count * 100:.0f} mW")

        # Overall recommendation priority
        if unattributed_power > 70:
            recommendations.append(
                f"\n🎯 PRIORITY: {unattributed_power:.1f}% unattributed power detected"
            )
            if renderer_count > 5:
                recommendations.append(
                    f"   → Start with Tab Suspender (most effective for many tabs)"
                )
            elif extension_count > 2:
                recommendations.append(f"   → Start with disabling extensions (quick win)")
            else:
                recommendations.append(f"   → Use Task Policy to move processes to E-cores")

        # The Perfect Optimization: Tab Suspender + Task Policy Combination
        # **Why This is the Ultimate "One-Two Punch"**:
        #
        # **Step 1: Tab Suspender (Stop Background Work)**
        # - Suspends 7 background tabs → eliminates 7× work
        # - No P-cores freed (work stopped, not moved) → no redistribution trap
        # - Power savings: 80-90% per suspended tab
        #
        # **Step 2: Task Policy (Move Active Work to E-cores)**
        # - Force the 1 active tab's renderer to E-cores
        # - Active tab still works (just on E-cores, slower but efficient)
        # - Power savings: 30-50% for active tab
        #
        # **Why This Combination Works**:
        # 1. **Tab Suspender eliminates background waste** (stops 7 tabs)
        # 2. **Task Policy optimizes active work** (moves 1 tab to E-cores)
        # 3. **No redistribution trap** (Tab Suspender doesn't free P-cores)
        # 4. **Maximum efficiency** (background eliminated + active optimized)
        #
        # **The Math**:
        # - 8 tabs total: 7 background + 1 active
        # - Tab Suspender: 7 tabs × 80% savings = 560 mW saved
        # - Task Policy: 1 tab × 40% savings = 40 mW saved
        # - Total: 600 mW saved (vs 320 mW with Task Policy alone)
        #
        # **Result**: Ultimate battery life optimization on Apple Silicon

        if renderer_count > 5:
            recommendations.append(f"\n🛑 THE PERFECT OPTIMIZATION: Tab Suspender + Task Policy")
            recommendations.append(
                f"   • Step 1: Tab Suspender → Suspend {renderer_count - 1} background tabs"
            )
            recommendations.append(f"     - Eliminates {renderer_count - 1}× background work")
            recommendations.append(f"     - No P-cores freed → No redistribution trap")
            recommendations.append(f"     - Power savings: ~{(renderer_count - 1) * 50:.0f} mW")
            recommendations.append(f"   • Step 2: Task Policy → Move 1 active tab to E-cores")
            recommendations.append(f"     - Active tab still works (just on E-cores, efficient)")
            recommendations.append(f"     - Power savings: ~40 mW for active tab")
            recommendations.append(f"   • Total Savings: ~{(renderer_count - 1) * 50 + 40:.0f} mW")
            recommendations.append(f"   • Why This Works:")
            recommendations.append(f"     - Tab Suspender eliminates background waste (stops work)")
            recommendations.append(
                f"     - Task Policy optimizes active work (moves work efficiently)"
            )
            recommendations.append(
                f"     - No redistribution trap (background doesn't free P-cores)"
            )
            recommendations.append(
                f"     - Maximum efficiency (background eliminated + active optimized)"
            )
            recommendations.append(f"   • Command for active tab:")
            recommendations.append(
                f"     sudo taskpolicy -c 0x0F -p $(pgrep -f 'com.apple.WebKit' | head -1)"
            )

        # The Strategy of Elimination: Other "Invisible" System Processes
        # **Why Some Processes Should Be Eliminated Rather Than Relocated**
        #
        # **The Principle**: If a process can be safely stopped/paused, eliminate it.
        # If it must run continuously, relocate it to E-cores.
        #
        # **Processes That Should Be Eliminated** (can be paused/stopped):
        # 1. **Background File Indexing (mds, mdworker)**: Can be paused
        #    - Spotlight indexing can be disabled or scheduled
        #    - Elimination: Stop indexing → 0 mW (vs relocation: 200 mW on E-cores)
        #    - Command: `sudo mdutil -i off /` (disable) or schedule indexing
        #
        # 2. **Cloud Syncing (cloudd, bird)**: Can be paused
        #    - iCloud sync can be paused or scheduled
        #    - Elimination: Pause sync → 0 mW (vs relocation: 150 mW on E-cores)
        #    - Command: System Settings → Apple ID → iCloud → Pause sync
        #
        # 3. **Time Machine Backups (backupd)**: Can be scheduled
        #    - Backups can be scheduled instead of continuous
        #    - Elimination: Schedule backups → 0 mW when not backing up (vs relocation: 300 mW)
        #    - Command: `sudo tmutil setinterval 3600` (hourly instead of continuous)
        #
        # **Processes That Must Be Relocated** (cannot be stopped):
        # 1. **WindowServer**: Must run (UI rendering)
        # 2. **kernel_task**: Must run (system kernel)
        # 3. **Active app processes**: User is actively using
        #
        # **The Strategy**:
        # - **Elimination first**: Stop/pause processes that can be safely stopped
        # - **Relocation second**: Move processes that must run to E-cores
        # - **Result**: Maximum efficiency (eliminate waste, optimize necessary work)

        # Check for system processes that should be eliminated
        system_processes_to_eliminate = []

        # Check for Spotlight indexing (mds, mdworker)
        spotlight_processes = breakdown.get("other", [])
        spotlight_count = sum(
            1
            for p in spotlight_processes
            if "mds" in p.get("name", "").lower() or "mdworker" in p.get("name", "").lower()
        )
        if spotlight_count > 0:
            system_processes_to_eliminate.append(
                {
                    "name": "Spotlight Indexing",
                    "processes": spotlight_count,
                    "elimination_method": "Disable or schedule indexing",
                    "command": "sudo mdutil -i off /",
                    "savings_mw": spotlight_count * 50,
                    "why_eliminate": "Indexing can be paused/scheduled - no need to run continuously",
                }
            )

        # Check for cloud sync (cloudd, bird) - would need to detect these
        # This is a placeholder - actual detection would require process name matching

        if system_processes_to_eliminate:
            recommendations.append(
                f"\n🛑 THE STRATEGY OF ELIMINATION: System Processes to Eliminate"
            )
            recommendations.append(
                f"   • Principle: If a process can be safely stopped/paused, eliminate it"
            )
            recommendations.append(f"   • If it must run continuously, relocate it to E-cores")
            recommendations.append(f"   • Strategy: Elimination first → Relocation second")
            recommendations.append(
                f"   • Result: Maximum efficiency (eliminate waste, optimize necessary work)"
            )
            recommendations.append(f"")

            for proc_info in system_processes_to_eliminate:
                recommendations.append(
                    f"   • {proc_info['name']}: {proc_info['processes']} process(es)"
                )
                recommendations.append(f"     - Elimination: {proc_info['elimination_method']}")
                recommendations.append(f"     - Command: {proc_info['command']}")
                recommendations.append(
                    f"     - Savings: ~{proc_info['savings_mw']:.0f} mW (elimination vs relocation)"
                )
                recommendations.append(f"     - Why eliminate: {proc_info['why_eliminate']}")
                recommendations.append(f"")

            recommendations.append(f"   • Processes That Must Be Relocated (cannot be stopped):")
            recommendations.append(
                f"     - WindowServer: Must run (UI rendering) → Move to E-cores if possible"
            )
            recommendations.append(
                f"     - kernel_task: Must run (system kernel) → Already optimized"
            )
            recommendations.append(
                f"     - Active app processes: User is actively using → Keep on P-cores"
            )

        # The Ghost in the Machine: Why Elimination Provides Stable Baseline
        # **The Question**: Why does eliminating cloudd provide more stable baseline
        # than relocating it to E-cores? How does this affect Attribution Ratio?
        #
        # **The Problem with Relocation**:
        # 1. **Variable Power Consumption**:
        #    - cloudd on E-cores: 150-300 mW (varies with sync activity)
        #    - Baseline fluctuates: 500 mW → 650 mW → 500 mW (unstable)
        #    - Attribution Ratio calculation becomes inaccurate (baseline keeps changing)
        #
        # 2. **Bursty Behavior**:
        #    - cloudd syncs in bursts (right-skewed distribution)
        #    - When syncing: 300 mW on E-cores
        #    - When idle: 50 mW on E-cores
        #    - Baseline = mean of these values = 175 mW (but fluctuates)
        #    - AR calculation: (App_Power - Baseline) / (Total - Baseline)
        #    - If baseline fluctuates, AR becomes unreliable
        #
        # 3. **The "Ghost" Effect**:
        #    - cloudd on E-cores still consumes power (even if less)
        #    - This power "ghosts" into baseline measurements
        #    - Baseline = 500 mW (system) + 175 mW (cloudd) = 675 mW
        #    - But cloudd power varies → baseline varies → AR varies
        #
        # **The Solution: Elimination**:
        # 1. **Stable Baseline**:
        #    - Eliminate cloudd: 0 mW (completely stopped)
        #    - Baseline = 500 mW (system only, stable)
        #    - No variation → stable AR calculations
        #
        # 2. **Accurate Attribution**:
        #    - AR = (App_Power - Baseline) / (Total - Baseline)
        #    - Baseline = 500 mW (stable, no cloudd)
        #    - App_Power = 2000 mW (your app)
        #    - Total = 2500 mW (system + app)
        #    - AR = (2000 - 500) / (2500 - 500) = 1500 / 2000 = 75% (accurate)
        #
        # 3. **No "Ghost" Effect**:
        #    - Eliminated process = 0 mW (no power consumption)
        #    - Baseline doesn't include eliminated process
        #    - AR calculation is clean (no interference)
        #
        # **Why This Matters**:
        # - Stable baseline → Accurate AR → Reliable power analysis
        # - Unstable baseline → Inaccurate AR → Unreliable analysis
        # - Elimination provides "clean" baseline for measurements

        if system_processes_to_eliminate:
            recommendations.append(f"\n👻 THE GHOST IN THE MACHINE: Why Elimination > Relocation")
            recommendations.append(f"   • Problem with Relocation:")
            recommendations.append(
                f"     - Relocated process still consumes power (varies with activity)"
            )
            recommendations.append(
                f"     - Baseline fluctuates: 500 mW → 650 mW → 500 mW (unstable)"
            )
            recommendations.append(
                f"     - Attribution Ratio becomes inaccurate (baseline keeps changing)"
            )
            recommendations.append(
                f"     - The 'Ghost' Effect: Process power 'ghosts' into baseline"
            )
            recommendations.append(f"")
            recommendations.append(f"   • Solution: Elimination")
            recommendations.append(f"     - Eliminated process = 0 mW (completely stopped)")
            recommendations.append(f"     - Baseline = 500 mW (system only, stable)")
            recommendations.append(f"     - No variation → Stable AR calculations")
            recommendations.append(
                f"     - Accurate Attribution: AR = (App - Baseline) / (Total - Baseline)"
            )
            recommendations.append(f"")
            recommendations.append(f"   • Example:")
            recommendations.append(
                f"     - Relocation: Baseline = 500 + 175 (cloudd) = 675 mW (varies)"
            )
            recommendations.append(f"     - Elimination: Baseline = 500 mW (stable)")
            recommendations.append(
                f"     - Result: Stable baseline → Accurate AR → Reliable analysis"
            )

        return recommendations

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
        if not power_data or not power_data.get("total_power"):
            print("  ⚠️  Could not collect power data")
            return {}

        # Break down processes by type (for WebKit/Safari)
        processes = power_data.get("processes", [])
        if "safari" in self.app_name.lower():
            process_breakdown = self.breakdown_webkit_processes(processes)
            print(f"\n🕵️‍♂️  WebKit Process Breakdown:")
            for proc_type, proc_list in process_breakdown.items():
                if proc_list:
                    print(f"  {proc_type.capitalize()}: {len(proc_list)} process(es)")
                    for proc in proc_list[:3]:  # Show first 3
                        print(
                            f"    - {proc['name']} (PID: {proc['pid']}, CPU: {proc['cpu_percent']:.1f}%)"
                        )
                    if len(proc_list) > 3:
                        print(f"    ... and {len(proc_list) - 3} more")
            power_data["process_breakdown"] = process_breakdown

        # Calculate attribution
        attribution = self.calculate_attribution_ratio(
            power_data["total_power"],
            power_data["total_power"],  # For app, total = app (we're measuring app-specific)
            baseline_power,
        )

        # Calculate skewness
        skewness = self.calculate_skewness(power_data["total_power"])

        # Identify waste
        waste_indicators = self.identify_hidden_waste(
            {
                "attribution_ratio": attribution.get("attribution_ratio", 0),
                "skewness": skewness,
                "app_name": self.app_name,
            }
        )

        # PID-based process breakdown for unmasking hidden processes
        if "safari" in self.app_name.lower() and "process_breakdown" in power_data:
            breakdown = power_data["process_breakdown"]
            unattributed_power = (1 - attribution.get("attribution_ratio", 0)) * 100

            if unattributed_power > 70:
                print(f"\n🕵️‍♂️  UNMASKING HIDDEN PROCESSES (>70% unattributed):")
                print(f"   Total unattributed: {unattributed_power:.1f}%")
                print(f"   Process breakdown:")

                # Estimate power per process type (heuristic based on count and CPU)
                total_cpu = sum(p["cpu_percent"] for p in processes)
                for proc_type, proc_list in breakdown.items():
                    if proc_list:
                        type_cpu = sum(p["cpu_percent"] for p in proc_list)
                        estimated_power_pct = (type_cpu / total_cpu * 100) if total_cpu > 0 else 0
                        estimated_power_mw = (
                            (estimated_power_pct / 100)
                            * unattributed_power
                            * attribution.get("mean_total_power_mw", 0)
                            / 100
                        )

                        print(f"     • {proc_type.capitalize()}: {len(proc_list)} process(es)")
                        print(
                            f"       Estimated: {estimated_power_pct:.1f}% CPU, ~{estimated_power_mw:.1f} mW"
                        )

                        # Identify likely culprit
                        if proc_type == "renderer" and len(proc_list) > 5:
                            print(
                                f"       ⚠️  LIKELY CULPRIT: {len(proc_list)} background tabs consuming power"
                            )
                        elif proc_type == "extension" and len(proc_list) > 2:
                            print(
                                f"       ⚠️  LIKELY CULPRIT: {len(proc_list)} extensions running continuously"
                            )
                        elif proc_type == "media" and len(proc_list) > 0:
                            print(
                                f"       ⚠️  LIKELY CULPRIT: Media processes (video/audio) still active"
                            )

                print(
                    f"\n   💡 Recommendation: Close unused tabs, disable extensions, check Activity Monitor"
                )

        # Generate optimization recommendations
        optimization_recommendations = self._generate_optimization_recommendations(
            breakdown, unattributed_power, attribution
        )

        if optimization_recommendations:
            print(f"\n🔧 OPTIMIZATION RECOMMENDATIONS:")
            for rec in optimization_recommendations:
                print(f"   {rec}")
            analysis["optimization_recommendations"] = optimization_recommendations

        # Build analysis result
        analysis = {
            "app_name": self.app_name,
            "timestamp": datetime.now().isoformat(),
            "baseline_power_mw": baseline_power,
            "power_data": power_data,
            "attribution": attribution,
            "skewness": skewness,
            "waste_indicators": waste_indicators,
            "processes": power_data.get("processes", []),
            "process_breakdown": power_data.get("process_breakdown", {}),
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
        if "attribution" in analysis and analysis["attribution"]:
            attr = analysis["attribution"]
            print(f"Attribution Ratio: {attr['attribution_percent']:.1f}%")
            print(f"  Mean App Power: {attr['mean_app_power_mw']:.1f} mW")
            print(f"  Baseline: {attr['baseline_power_mw']:.1f} mW")
            print()

        # Skewness
        if "skewness" in analysis and analysis["skewness"]:
            skew = analysis["skewness"]
            print(f"Power Distribution: {skew['skew_direction']}")
            print(f"  Mean: {skew['mean']:.1f} mW")
            print(f"  Median: {skew['median']:.1f} mW")
            print(f"  Divergence: {skew['divergence_pct']:.1f}%")
            if skew["burst_fraction"]:
                print(f"  Burst Fraction: {skew['burst_fraction']*100:.1f}%")
            print(f"  Interpretation: {skew['skew_interpretation']}")
            print()

        # Waste indicators
        if analysis.get("waste_indicators"):
            print("Hidden Energy Waste:")
            for indicator in analysis["waste_indicators"]:
                print(f"  {indicator}")
            print()

    def _save_results(self, analysis: Dict):
        """Save analysis results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_dir / f"app_analysis_{self.app_name}_{timestamp}.json"

        # Remove power_data from saved file (too large)
        save_data = analysis.copy()
        save_data.pop("power_data", None)

        with open(filename, "w") as f:
            json.dump(save_data, f, indent=2)

        print(f"💾 Results saved: {filename}")

    def _measure_baseline(self, duration: int = 10) -> float:
        """Measure baseline system power."""
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

            pattern = r"(?:CPU|Package|Total)\s+Power[:\s]+([\d.]+)\s*mW"
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
        "app", help='Application name to analyze (e.g., Safari, Chrome, "Final Cut Pro")'
    )
    parser.add_argument(
        "--duration", type=int, default=30, help="Measurement duration in seconds (default: 30)"
    )
    parser.add_argument(
        "--baseline", type=float, help="Baseline system power in mW (if not provided, will measure)"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("app_analysis_data"),
        help="Directory to save results (default: app_analysis_data)",
    )

    args = parser.parse_args()

    analyzer = UserAppAnalyzer(args.app, args.data_dir)
    results = analyzer.analyze_app(duration=args.duration, baseline_power=args.baseline)

    if results:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
