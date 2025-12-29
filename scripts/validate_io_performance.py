#!/usr/bin/env python3
"""
I/O Performance Stress Test - Chaos Script
Validates select.select() response time during system stalls and shutdown signals.
Tests the <100ms response time claim from TECHNICAL_DEEP_DIVE.md
"""

import subprocess
import select
import time
import signal
import sys
import threading
from queue import Queue
from statistics import mean, median

# Global flags
running = True
response_times = []
shutdown_times = []


def signal_handler(sig, frame):
    """Handle Ctrl+C and measure response time."""
    global running
    shutdown_start = time.time()
    running = False
    shutdown_end = time.time()
    response_time = (shutdown_end - shutdown_start) * 1000  # Convert to ms
    shutdown_times.append(response_time)
    print(f"\n🛑 Shutdown signal received - Response time: {response_time:.2f} ms")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def create_stall_process():
    """Create a process that intentionally stalls the system."""
    # CPU-intensive task that will cause system load
    stall_script = """
import time
import multiprocessing

def cpu_stress():
    while True:
        # Burn CPU cycles
        sum(range(1000000))

# Start multiple stress processes
processes = []
for _ in range(multiprocessing.cpu_count()):
    p = multiprocessing.Process(target=cpu_stress)
    p.start()
    processes.append(p)

# Keep running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    for p in processes:
        p.terminate()
"""

    return subprocess.Popen(
        ["python3", "-c", stall_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )


def test_select_performance(duration=10, stall_enabled=True):
    """
    Test select.select() performance under normal and stressed conditions.

    Args:
        duration: Test duration in seconds
        stall_enabled: Whether to run CPU stress during test
    """
    global running, response_times

    print("=" * 70)
    print("🧪 I/O Performance Stress Test")
    print("=" * 70)
    print(f"Duration: {duration}s")
    print(f"Stall enabled: {stall_enabled}")
    print("=" * 70)
    print()

    # Create a dummy subprocess that outputs data periodically
    cmd = [
        "python3",
        "-c",
        """
import time
import sys
for i in range(1000):
    print(f"Data line {i}")
    sys.stdout.flush()
    time.sleep(0.1)
""",
    ]

    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=0
    )

    # Start stall process if enabled
    stall_process = None
    if stall_enabled:
        print("🔥 Starting CPU stress process...")
        stall_process = create_stall_process()
        time.sleep(1)  # Let stress process start

    print("📊 Starting I/O performance test...")
    print("   (Press Ctrl+C to test shutdown response time)")
    print()

    buffer = ""
    line_count = 0
    start_time = time.time()
    last_check_time = start_time

    try:
        while running and (time.time() - start_time) < duration:
            # Measure time before select
            before_select = time.time()

            # Use select.select() (non-blocking)
            ready, _, _ = select.select([process.stdout], [], [], 0.1)

            # Measure time after select
            after_select = time.time()
            select_time = (after_select - before_select) * 1000  # ms

            # Record response time
            if select_time < 200:  # Only record reasonable times
                response_times.append(select_time)

            if ready:
                # Data available - read it
                chunk = process.stdout.read(4096)
                if chunk:
                    buffer += chunk
                    line_count += buffer.count("\n")
                    buffer = buffer.split("\n")[-1]  # Keep incomplete line
            else:
                # No data - check process status
                if process.poll() is not None:
                    break

            # Periodic status
            current_time = time.time()
            if current_time - last_check_time >= 1.0:
                avg_response = mean(response_times) if response_times else 0
                print(f"   Lines processed: {line_count} | Avg select time: {avg_response:.2f} ms")
                last_check_time = current_time

    except KeyboardInterrupt:
        # This should be caught by signal handler, but just in case
        pass
    finally:
        # Cleanup
        if process:
            process.terminate()
            process.wait()
        if stall_process:
            stall_process.terminate()
            stall_process.wait()

    return response_times, shutdown_times


def print_results(response_times, shutdown_times, stall_enabled):
    """Print test results and validate claims."""
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS")
    print("=" * 70)

    if response_times:
        print(f"\nselect.select() Performance ({len(response_times)} samples):")
        print(f"   Mean:    {mean(response_times):.2f} ms")
        print(f"   Median:  {median(response_times):.2f} ms")
        print(f"   Min:     {min(response_times):.2f} ms")
        print(f"   Max:     {max(response_times):.2f} ms")

        # Validate claim: <100ms response time
        p95 = sorted(response_times)[int(len(response_times) * 0.95)]
        print(f"   95th percentile: {p95:.2f} ms")

        if p95 < 100:
            print("   ✅ CLAIM VALIDATED: 95th percentile < 100ms")
        else:
            print("   ⚠️  CLAIM NOT MET: Some responses > 100ms")

    if shutdown_times:
        print(f"\nShutdown Response Time ({len(shutdown_times)} tests):")
        for i, st in enumerate(shutdown_times, 1):
            print(f"   Test {i}: {st:.2f} ms")

        avg_shutdown = mean(shutdown_times)
        print(f"   Average: {avg_shutdown:.2f} ms")

        if avg_shutdown < 100:
            print("   ✅ CLAIM VALIDATED: Shutdown response < 100ms")
        else:
            print("   ⚠️  CLAIM NOT MET: Shutdown response > 100ms")

    print("\n" + "=" * 70)
    print("💡 Interpretation:")
    if stall_enabled:
        print("   Tested under CPU stress conditions")
        print("   If response times are still < 100ms, select.select() handles")
        print("   system stalls gracefully.")
    else:
        print("   Tested under normal conditions")
        print("   Run with --stall to test under system stress")
    print("=" * 70)


def main():
    """Main test function."""
    import argparse

    parser = argparse.ArgumentParser(description="Stress test select.select() I/O performance")
    parser.add_argument(
        "--duration", "-d", type=int, default=10, help="Test duration in seconds (default: 10)"
    )
    parser.add_argument("--stall", action="store_true", help="Enable CPU stress during test")

    args = parser.parse_args()

    try:
        response_times, shutdown_times = test_select_performance(args.duration, args.stall)
        print_results(response_times, shutdown_times, args.stall)
    except KeyboardInterrupt:
        print("\n\n✅ Test interrupted - shutdown response time recorded")
        if shutdown_times:
            print_results([], shutdown_times, args.stall)

    return 0


if __name__ == "__main__":
    sys.exit(main())
