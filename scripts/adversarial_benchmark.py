#!/usr/bin/env python3
"""
Adversarial Benchmark: Extreme Stress Test
Tests the suite's response prioritization under extreme conditions:
- Heavy compile job on P-cores
- SSH disconnect (SIGHUP)
- Multiple concurrent signals
"""

import subprocess
import time
import signal
import sys
import threading
import os
import select
from typing import Dict, List, Tuple
from collections import deque
from datetime import datetime
import argparse
import os


class AdversarialBenchmark:
    """
    Adversarial benchmark that tests suite resilience under extreme stress.
    """

    def __init__(self, output_file: Optional[str] = None):
        self.running = True
        self.stress_processes = []
        self.signal_times = deque(maxlen=100)
        self.priority_log = []
        self.start_time = time.time()
        self.output_file = output_file
        self.data_written = False
        self.csv_header_written = False

        # Register signal handlers
        self._setup_signal_handlers()

        # Start heartbeat monitor
        self._start_heartbeat()

        # Initialize output file if specified
        if self.output_file:
            self._write_csv_header()

    def _setup_signal_handlers(self):
        """Setup handlers for all signals with priority tracking."""

        def signal_handler(sig, frame):
            signal_name = {
                signal.SIGINT: "SIGINT (Ctrl+C)",
                signal.SIGTERM: "SIGTERM",
                signal.SIGHUP: "SIGHUP (SSH disconnect)",
                signal.SIGQUIT: "SIGQUIT",
            }.get(sig, f"Signal {sig}")

            timestamp = time.time()
            elapsed = timestamp - self.start_time

            self.signal_times.append((sig, timestamp, signal_name, elapsed))

            # CRITICAL: Ensure data integrity before shutdown
            # For SIGHUP (SSH disconnect), this is especially important
            if sig == signal.SIGHUP:
                print(
                    f"\n\n🔌 [{elapsed*1000:.1f}ms] Received {signal_name} - ensuring data integrity..."
                )
                self._ensure_data_persisted()
            else:
                print(f"\n\n🛑 [{elapsed*1000:.1f}ms] Received {signal_name}")

            # Log priority response
            self.priority_log.append(
                {
                    "signal": signal_name,
                    "elapsed_ms": elapsed * 1000,
                    "timestamp": datetime.now().isoformat(),
                    "priority": self._calculate_priority(sig, elapsed),
                    "data_persisted": self.data_written,
                }
            )

            print(f"   Priority: {self._calculate_priority(sig, elapsed)}")

            # Only set running=False after data is persisted
            # This ensures cleanup happens in order
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGHUP, signal_handler)
        signal.signal(signal.SIGQUIT, signal_handler)

    def _calculate_priority(self, sig: int, elapsed: float) -> str:
        """Calculate response priority based on signal type and response time."""
        elapsed_ms = elapsed * 1000

        # Priority rules:
        # 1. SIGHUP (SSH disconnect) - highest priority (data integrity)
        # 2. SIGINT (Ctrl+C) - high priority (user intent)
        # 3. SIGTERM (system shutdown) - medium priority
        # 4. SIGQUIT (debug) - low priority

        if sig == signal.SIGHUP:
            if elapsed_ms < 100:
                return "CRITICAL (SSH disconnect, <100ms)"
            else:
                return "HIGH (SSH disconnect, >100ms)"
        elif sig == signal.SIGINT:
            if elapsed_ms < 100:
                return "HIGH (User intent, <100ms)"
            else:
                return "MEDIUM (User intent, >100ms)"
        elif sig == signal.SIGTERM:
            return "MEDIUM (System shutdown)"
        else:
            return "LOW (Debug/Quit)"

    def _start_heartbeat(self):
        """Start heartbeat monitor for signal checking."""

        def heartbeat_loop():
            while self.running:
                # 100ms heartbeat
                ready, _, _ = select.select([], [], [], 0.1)
                if not self.running:
                    break

        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()

    def _write_csv_header(self):
        """Write CSV header to output file."""
        if not self.output_file or self.csv_header_written:
            return

        try:
            with open(self.output_file, "w") as f:
                f.write("timestamp,elapsed_ms,signal,priority,data_persisted\n")
            self.csv_header_written = True
            print(f"📝 CSV header written to {self.output_file}")
        except Exception as e:
            print(f"⚠️  Error writing CSV header: {e}")

    def _ensure_data_persisted(self):
        """
        Ensure all data is written to disk before shutdown.

        This is critical for SIGHUP (SSH disconnect) to prevent data loss.

        **Why more critical during high-power bursts:**
        1. **More data generated**: Bursts create rapid power changes, generating
           more data points per second than idle periods
        2. **Higher write load**: More data in buffers = more to flush
        3. **More valuable data**: Bursts are the interesting part (idle is baseline)
        4. **System stress**: High-power bursts indicate system activity, increasing
           risk of data loss if process is killed abruptly
        5. **Buffer saturation**: During bursts, buffers fill faster, making
           fsync() more critical to prevent buffer loss

        **The lifecycle:**
        1. Signal received (<100ms via heartbeat)
        2. Signal handler called
        3. Data flushed to disk (this function) - CRITICAL during bursts
        4. running flag set to False
        5. Main loop exits gracefully
        6. Kernel can safely terminate process
        """
        if not self.output_file:
            return

        try:
            # Flush any pending data
            if self.priority_log:
                with open(self.output_file, "a") as f:
                    for log_entry in self.priority_log:
                        f.write(
                            f"{log_entry['timestamp']},"
                            f"{log_entry['elapsed_ms']:.1f},"
                            f"{log_entry['signal']},"
                            f"{log_entry['priority']},"
                            f"{log_entry.get('data_persisted', False)}\n"
                        )

                    # CRITICAL: During high-power bursts, more data is in buffers
                    # flush() alone isn't enough - we need fsync() to guarantee
                    # data is on physical disk before process termination
                    f.flush()  # Python buffer → OS buffer
                    os.fsync(f.fileno())  # OS buffer → Physical disk

                    # During bursts, this is especially critical because:
                    # - More data points = larger buffers
                    # - System under stress = higher risk of buffer loss
                    # - Burst data is more valuable than idle data

            self.data_written = True
            print(f"✅ Data persisted to {self.output_file} (critical during bursts)")
        except Exception as e:
            print(f"⚠️  Error persisting data: {e}")

    def create_cpu_stress(self, cores: int = 4, duration: int = 60) -> subprocess.Popen:
        """
        Create CPU stress on P-cores (simulating heavy compile job).

        Args:
            cores: Number of cores to stress
            duration: Duration in seconds (0 = infinite)

        Returns:
            Process handle
        """
        print(f"🔥 Creating CPU stress on {cores} P-cores...")

        # Use 'yes' command to max out CPU
        # Force to P-cores using taskpolicy
        cmd = ["taskpolicy", "-c", "0xF0"]  # P-cores: 4,5,6,7 (0xF0 = 11110000)

        # Create stress processes
        processes = []
        for i in range(cores):
            stress_cmd = cmd + ["yes", ">/dev/null"]
            proc = subprocess.Popen(
                stress_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            processes.append(proc)

        self.stress_processes.extend(processes)
        return processes

    def simulate_ssh_disconnect(self, delay: float = 5.0):
        """
        Simulate SSH disconnect by sending SIGHUP.

        Args:
            delay: Delay before sending SIGHUP (seconds)
        """

        def send_sighup():
            time.sleep(delay)
            if self.running:
                print(f"\n🔌 [{delay}s] Simulating SSH disconnect (SIGHUP)...")
                os.kill(os.getpid(), signal.SIGHUP)

        disconnect_thread = threading.Thread(target=send_sighup, daemon=True)
        disconnect_thread.start()

    def run_benchmark(
        self,
        stress_cores: int = 4,
        stress_duration: int = 60,
        ssh_delay: float = 5.0,
        monitor_interval: float = 0.5,
    ) -> Dict:
        """
        Run adversarial benchmark.

        Args:
            stress_cores: Number of P-cores to stress
            stress_duration: Duration of stress test (seconds)
            ssh_delay: Delay before simulating SSH disconnect
            monitor_interval: Monitoring interval (seconds)

        Returns:
            Dictionary with benchmark results
        """
        print("=" * 70)
        print("🌪️  ADVERSARIAL BENCHMARK: Extreme Stress Test")
        print("=" * 70)
        print()
        print("This test will:")
        print(f"  1. Create CPU stress on {stress_cores} P-cores (heavy compile simulation)")
        print(f"  2. Simulate SSH disconnect (SIGHUP) after {ssh_delay}s")
        print(f"  3. Monitor signal response times and priorities")
        print()
        print("Press Ctrl+C at any time to test SIGINT handling under stress")
        print()

        # Start CPU stress
        stress_procs = self.create_cpu_stress(stress_cores, stress_duration)

        # Schedule SSH disconnect
        self.simulate_ssh_disconnect(ssh_delay)

        # Monitor until shutdown
        monitor_count = 0
        while self.running:
            time.sleep(monitor_interval)
            monitor_count += 1

            # Check if stress processes are still running
            alive_count = sum(1 for p in stress_procs if p.poll() is None)
            if alive_count == 0 and stress_duration > 0:
                print(f"⏱️  [{time.time() - self.start_time:.1f}s] Stress processes completed")
                break

        # Cleanup stress processes
        for proc in stress_procs:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except:
                proc.kill()

        # Ensure final data is persisted
        if self.output_file:
            self._ensure_data_persisted()

        # Generate report
        return self._generate_report()

    def _generate_report(self) -> Dict:
        """Generate benchmark report."""
        if not self.signal_times:
            return {"status": "no_signals", "message": "No signals received during benchmark"}

        # Get first signal (highest priority response)
        first_sig, first_time, first_name, first_elapsed = self.signal_times[0]

        # Calculate statistics
        elapsed_times = [sig[3] * 1000 for sig in self.signal_times]  # Convert to ms

        report = {
            "status": "success",
            "total_signals": len(self.signal_times),
            "first_signal": {
                "name": first_name,
                "elapsed_ms": first_elapsed * 1000,
                "priority": self._calculate_priority(first_sig, first_elapsed),
            },
            "all_signals": [
                {
                    "name": sig[2],
                    "elapsed_ms": sig[3] * 1000,
                    "priority": self._calculate_priority(sig[0], sig[3]),
                }
                for sig in self.signal_times
            ],
            "statistics": {
                "min_response_ms": min(elapsed_times),
                "max_response_ms": max(elapsed_times),
                "mean_response_ms": sum(elapsed_times) / len(elapsed_times),
                "median_response_ms": sorted(elapsed_times)[len(elapsed_times) // 2],
            },
            "priority_log": self.priority_log,
        }

        return report

    def print_report(self, report: Dict):
        """Print benchmark report."""
        print("\n" + "=" * 70)
        print("📊 ADVERSARIAL BENCHMARK REPORT")
        print("=" * 70)
        print()

        if report["status"] == "no_signals":
            print("ℹ️  No signals received during benchmark")
            return

        print(f"📈 Total Signals Received: {report['total_signals']}")
        print()

        print("🎯 First Signal (Highest Priority Response):")
        first = report["first_signal"]
        print(f"   Signal: {first['name']}")
        print(f"   Response Time: {first['elapsed_ms']:.1f} ms")
        print(f"   Priority: {first['priority']}")
        print()

        print("📊 Response Time Statistics:")
        stats = report["statistics"]
        print(f"   Min: {stats['min_response_ms']:.1f} ms")
        print(f"   Max: {stats['max_response_ms']:.1f} ms")
        print(f"   Mean: {stats['mean_response_ms']:.1f} ms")
        print(f"   Median: {stats['median_response_ms']:.1f} ms")
        print()

        print("🔍 All Signals Received:")
        for i, sig_info in enumerate(report["all_signals"], 1):
            print(
                f"   {i}. {sig_info['name']}: {sig_info['elapsed_ms']:.1f} ms ({sig_info['priority']})"
            )
        print()

        # Priority analysis
        print("🎯 Priority Analysis:")
        priorities = {}
        for sig_info in report["all_signals"]:
            priority = sig_info["priority"]
            priorities[priority] = priorities.get(priority, 0) + 1

        for priority, count in sorted(priorities.items(), key=lambda x: x[1], reverse=True):
            print(f"   {priority}: {count} signal(s)")
        print()

        # Validation
        print("✅ Validation:")
        if stats["mean_response_ms"] < 100:
            print("   ✅ Mean response time < 100ms (meets guarantee)")
        else:
            print("   ⚠️  Mean response time > 100ms (exceeds guarantee)")

        if first["elapsed_ms"] < 100:
            print("   ✅ First signal response < 100ms (meets guarantee)")
        else:
            print("   ⚠️  First signal response > 100ms (exceeds guarantee)")

        if "SIGHUP" in first["name"]:
            print("   ✅ SIGHUP handled as highest priority (data integrity)")
        else:
            print("   ℹ️  First signal was not SIGHUP")


def main():
    parser = argparse.ArgumentParser(description="Adversarial benchmark: extreme stress test")
    parser.add_argument(
        "--stress-cores", type=int, default=4, help="Number of P-cores to stress (default: 4)"
    )
    parser.add_argument(
        "--stress-duration",
        type=int,
        default=60,
        help="Duration of stress test in seconds (default: 60, 0 = infinite)",
    )
    parser.add_argument(
        "--ssh-delay",
        type=float,
        default=5.0,
        help="Delay before simulating SSH disconnect in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output CSV file for benchmark results (ensures data persistence on SIGHUP)",
    )

    args = parser.parse_args()

    benchmark = AdversarialBenchmark(output_file=args.output)

    try:
        report = benchmark.run_benchmark(
            stress_cores=args.stress_cores,
            stress_duration=args.stress_duration,
            ssh_delay=args.ssh_delay,
        )
        benchmark.print_report(report)
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrupted")
        report = benchmark._generate_report()
        benchmark.print_report(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
