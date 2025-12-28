#!/usr/bin/env python3
"""
Power Logger - Automated powermetrics data collection
Runs powermetrics in the background and saves data to CSV for analysis.
"""

import subprocess
import csv
import time
import signal
import sys
import os
from datetime import datetime
from pathlib import Path
import re
from typing import Optional, Dict, List
import threading
from queue import Queue

# Global flag for graceful shutdown
running = True
data_queue = Queue()


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
    print("\n\n🛑 Shutting down power logger...")
    running = False
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def parse_powermetrics_line(line: str) -> Optional[Dict[str, float]]:
    """
    Parse a line from powermetrics output.
    Returns dict with power values or None if no data found.
    """
    data = {}
    timestamp = time.time()
    
    # ANE Power
    ane_match = re.search(r'ANE\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
    if ane_match:
        data['ane_power_mw'] = float(ane_match.group(1))
    
    # CPU Power (package power)
    cpu_match = re.search(r'(?:CPU|Package)\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
    if cpu_match:
        data['cpu_power_mw'] = float(cpu_match.group(1))
    
    # GPU Power
    gpu_match = re.search(r'GPU\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
    if gpu_match:
        data['gpu_power_mw'] = float(gpu_match.group(1))
    
    # Total Package Power
    total_match = re.search(r'Total\s+Package\s+Power[:\s]+([\d.]+)\s*mW', line, re.IGNORECASE)
    if total_match:
        data['total_power_mw'] = float(total_match.group(1))
    
    # CPU Energy (if available)
    cpu_energy_match = re.search(r'CPU\s+Energy[:\s]+([\d.]+)\s*mJ', line, re.IGNORECASE)
    if cpu_energy_match:
        data['cpu_energy_mj'] = float(cpu_energy_match.group(1))
    
    if data:
        data['timestamp'] = timestamp
        data['datetime'] = datetime.now().isoformat()
        return data
    
    return None


def powermetrics_reader(sample_interval: int, data_queue: Queue):
    """
    Run powermetrics in a separate thread with non-blocking I/O.
    Uses select/poll for efficient non-blocking reads to prevent script freezing.
    """
    global running
    
    process = None
    try:
        cmd = ['sudo', 'powermetrics', '--samplers', 'cpu_power', '-i', str(sample_interval)]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,  # Unbuffered for real-time data
            universal_newlines=True
        )
        
        print(f"✅ powermetrics started (sampling every {sample_interval}ms)")
        print(f"   Process PID: {process.pid}")
        
        # Use non-blocking I/O with select for efficient reading
        import select
        buffer = ""
        last_data_time = time.time()
        no_data_warning = False
        
        while running:
            if process.stdout is None:
                break
            
            # Check if process is still alive
            if process.poll() is not None:
                print(f"⚠️  powermetrics process ended (code: {process.returncode})")
                break
            
            # Use select for non-blocking read (works on Unix/macOS)
            try:
                ready, _, _ = select.select([process.stdout], [], [], 0.1)
                
                if ready:
                    # Data available - read in chunks
                    chunk = process.stdout.read(4096)
                    if chunk:
                        buffer += chunk
                        last_data_time = time.time()
                        no_data_warning = False
                        
                        # Process complete lines
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            data = parse_powermetrics_line(line)
                            if data:
                                data_queue.put(data)
                    else:
                        # EOF reached
                        break
                else:
                    # No data available - check for timeout
                    if time.time() - last_data_time > 5.0 and not no_data_warning:
                        print("⚠️  No data from powermetrics for 5+ seconds...")
                        no_data_warning = True
                
                # Prevent buffer overflow
                if len(buffer) > 16384:
                    buffer = buffer[-8192:]
                    
            except (OSError, ValueError) as e:
                # Handle select errors gracefully
                if running:
                    time.sleep(0.1)
                continue
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running powermetrics: {e}")
    except Exception as e:
        print(f"❌ Unexpected error in powermetrics reader: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean shutdown
        if process:
            try:
                process.terminate()
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            except Exception as e:
                print(f"⚠️  Error cleaning up process: {e}")


def csv_writer(csv_path: Path, data_queue: Queue):
    """Write data from queue to CSV file."""
    global running
    
    # Field names for CSV
    fieldnames = ['timestamp', 'datetime', 'ane_power_mw', 'cpu_power_mw', 
                  'gpu_power_mw', 'total_power_mw', 'cpu_energy_mj']
    
    # Check if file exists to determine if we need headers
    file_exists = csv_path.exists()
    
    with open(csv_path, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        
        if not file_exists:
            writer.writeheader()
            print(f"✅ Created CSV file: {csv_path}")
        else:
            print(f"✅ Appending to existing CSV: {csv_path}")
        
        last_write_time = time.time()
        write_interval = 1.0  # Write to disk every second
        
        while running:
            # Collect data from queue
            rows_to_write = []
            while not data_queue.empty():
                rows_to_write.append(data_queue.get())
            
            # Write to CSV periodically
            current_time = time.time()
            if rows_to_write and (current_time - last_write_time) >= write_interval:
                for row in rows_to_write:
                    # Fill missing fields with None
                    complete_row = {field: row.get(field) for field in fieldnames}
                    writer.writerow(complete_row)
                
                csvfile.flush()  # Ensure data is written
                last_write_time = current_time
                print(f"📊 Wrote {len(rows_to_write)} data points to CSV")
            
            time.sleep(0.5)
    
    print(f"✅ CSV file saved: {csv_path}")


def main():
    """Main function."""
    global running
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Automated power logging with powermetrics'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='power_log.csv',
        help='Output CSV file path (default: power_log.csv)'
    )
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=500,
        help='Sampling interval in milliseconds (default: 500)'
    )
    parser.add_argument(
        '--duration', '-d',
        type=float,
        help='Duration to log in seconds (default: run until Ctrl+C)'
    )
    
    args = parser.parse_args()
    
    csv_path = Path(args.output)
    
    print("=" * 70)
    print("🔋 Power Logger - Automated Data Collection")
    print("=" * 70)
    print(f"Output file: {csv_path}")
    print(f"Sampling interval: {args.interval}ms")
    if args.duration:
        print(f"Duration: {args.duration}s")
    else:
        print("Duration: Until Ctrl+C")
    print("=" * 70)
    print()
    
    # Start powermetrics reader thread
    power_thread = threading.Thread(
        target=powermetrics_reader,
        args=(args.interval, data_queue),
        daemon=True
    )
    power_thread.start()
    time.sleep(2)  # Give powermetrics time to start
    
    # Start CSV writer thread
    csv_thread = threading.Thread(
        target=csv_writer,
        args=(csv_path, data_queue),
        daemon=True
    )
    csv_thread.start()
    
    # Main loop - wait for duration or Ctrl+C
    start_time = time.time()
    try:
        while running:
            if args.duration and (time.time() - start_time) >= args.duration:
                print(f"\n⏱️  Duration reached ({args.duration}s)")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        time.sleep(1)  # Give threads time to finish
        print("\n✅ Power logging complete!")
        print(f"📁 Data saved to: {csv_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

