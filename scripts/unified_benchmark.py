#!/usr/bin/env python3
"""
Unified Benchmark Script for Apple Silicon M2
Integrates CoreML inference with real-time power monitoring and Arduino serial communication.
Enhanced with real-time visualization and human-readable statistics.
"""

import coremltools as ct
import numpy as np
import subprocess
import serial
import serial.tools.list_ports
import threading
import time
import re
import sys
import signal
import argparse
from queue import Queue
from typing import Optional, Tuple, List
from collections import deque
from datetime import datetime
import select

try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Rich library not available. Install with: pip install rich")
    print("   Falling back to basic output mode.")

# Global flags for graceful shutdown
running = True
serial_connected = False

# Statistics tracking
power_history = deque(maxlen=1000)  # Store last 1000 power readings
inference_count = 0
start_time = None

console = Console() if RICH_AVAILABLE else None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
    if console:
        console.print("\n\n[bold red]🛑 Shutting down gracefully...[/bold red]")
    else:
        print("\n\n🛑 Shutting down gracefully...")
    running = False
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def find_arduino_port() -> Optional[str]:
    """
    Find Arduino serial port by searching for /dev/cu.usbmodem* devices.
    Returns the first matching port or None if not found.
    """
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'usbmodem' in port.device.lower():
            if console:
                console.print(f"[green]✅ Found Arduino at:[/green] {port.device}")
            else:
                print(f"✅ Found Arduino at: {port.device}")
            return port.device
    return None


def get_model_input_name(model: ct.models.MLModel) -> str:
    """
    Extract the input name from the CoreML model specification.
    Falls back to common names if detection fails.
    """
    try:
        spec = model.get_spec()
        if spec.description.input:
            return spec.description.input[0].name
    except Exception as e:
        if console:
            console.print(f"[yellow]⚠️  Warning: Could not detect input name:[/yellow] {e}")
        else:
            print(f"⚠️  Warning: Could not detect input name: {e}")
    
    # Try common input names
    for common_name in ['x_1', 'input', 'image', 'data']:
        try:
            # Quick test to see if this input name works
            dummy = np.random.rand(1, 3, 224, 224).astype(np.float32)
            model.predict({common_name: dummy})
            return common_name
        except:
            continue
    
    # Default fallback
    return 'x_1'


def parse_ane_power(powermetrics_output: str) -> Optional[float]:
    """
    Parse ANE Power value from powermetrics output.
    Handles various output formats that powermetrics might produce.
    
    Returns power in mW, or None if not found.
    """
    # Pattern 1: "ANE Power: 123.45 mW"
    pattern1 = r'ANE\s+Power[:\s]+([\d.]+)\s*mW'
    match = re.search(pattern1, powermetrics_output, re.IGNORECASE)
    if match:
        return float(match.group(1))
    
    # Pattern 2: "ANE: 123.45 mW" or "Neural Engine: 123.45 mW"
    pattern2 = r'(?:ANE|Neural\s+Engine)[:\s]+([\d.]+)\s*mW'
    match = re.search(pattern2, powermetrics_output, re.IGNORECASE)
    if match:
        return float(match.group(1))
    
    # Pattern 3: Look for lines containing "ANE" and power values
    lines = powermetrics_output.split('\n')
    for line in lines:
        if 'ane' in line.lower() and 'power' in line.lower():
            numbers = re.findall(r'[\d.]+', line)
            if numbers:
                return float(numbers[0])
    
    return None


def powermetrics_reader(power_queue: Queue, sample_interval: int = 500):
    """
    Run powermetrics as a subprocess and parse ANE Power values.
    Uses select.select() for non-blocking I/O to ensure responsive shutdown.
    Puts (timestamp, power_mw) tuples into the queue.
    """
    global running
    
    try:
        # Start powermetrics subprocess
        cmd = ['sudo', 'powermetrics', '--samplers', 'cpu_power', '-i', str(sample_interval)]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        if console:
            console.print(f"[green]✅ powermetrics started[/green] (sampling every {sample_interval}ms)")
        else:
            print(f"✅ powermetrics started (sampling every {sample_interval}ms)")
        
        if process.stdout is None:
            if console:
                console.print("[bold red]❌ Error: powermetrics stdout is not available[/bold red]")
            else:
                print("❌ Error: powermetrics stdout is not available")
            return
        
        buffer = ""
        timeout = 0.1  # 100ms timeout for select.select()
        
        while running:
            # Use select.select() for non-blocking I/O
            ready, _, _ = select.select([process.stdout], [], [], timeout)
            
            if ready:
                chunk = process.stdout.read(1024)
                if not chunk:
                    if process.poll() is not None:
                        break
                    continue
                
                buffer += chunk
                
                # Try to parse ANE power from accumulated buffer
                ane_power = parse_ane_power(buffer)
                
                if ane_power is not None:
                    timestamp = time.time()
                    power_queue.put((timestamp, ane_power))
                    # Clear buffer after successful parse (keep last 2KB for overlap)
                    buffer = buffer[-2048:] if len(buffer) > 2048 else ""
                
                # Prevent buffer from growing too large
                if len(buffer) > 8192:
                    buffer = buffer[-4096:]
            else:
                # Timeout - check if we should continue
                if not running:
                    break
        
        process.terminate()
        process.wait()
        
    except subprocess.CalledProcessError as e:
        if console:
            console.print(f"[bold red]❌ Error running powermetrics:[/bold red] {e}")
            console.print("   Make sure you have sudo permissions and powermetrics is available.")
        else:
            print(f"❌ Error running powermetrics: {e}")
            print("   Make sure you have sudo permissions and powermetrics is available.")
    except Exception as e:
        if console:
            console.print(f"[bold red]❌ Unexpected error in powermetrics reader:[/bold red] {e}")
        else:
            print(f"❌ Unexpected error in powermetrics reader: {e}")


def serial_writer(power_queue: Queue, port: Optional[str], baudrate: int = 115200):
    """
    Read power values from queue and send them to Arduino via serial.
    Sends data every 500ms in format: ANE_PWR:[value]\n
    """
    global running, serial_connected
    
    if port is None:
        if console:
            console.print("[yellow]⚠️  Warning: Arduino not found. Continuing benchmark without serial output.[/yellow]")
            console.print("   (This is the expected 'Edge Case' behavior)")
        else:
            print("⚠️  Warning: Arduino not found. Continuing benchmark without serial output.")
            print("   (This is the expected 'Edge Case' behavior)")
        # Drain the queue to prevent it from filling up
        while running:
            try:
                power_queue.get(timeout=0.1)
            except:
                pass
        return
    
    ser = None
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        serial_connected = True
        if console:
            console.print(f"[green]✅ Serial connection established:[/green] {port} @ {baudrate} baud")
        else:
            print(f"✅ Serial connection established: {port} @ {baudrate} baud")
        
        last_send_time = 0
        send_interval = 0.5  # 500ms
        packets_sent = 0
        
        while running:
            current_time = time.time()
            
            # Get latest power value from queue (non-blocking)
            latest_power = None
            while not power_queue.empty():
                latest_power = power_queue.get()
            
            # Send data every 500ms if we have a power value
            if latest_power is not None and (current_time - last_send_time) >= send_interval:
                _, power_mw = latest_power
                message = f"ANE_PWR:{power_mw:.2f}\n"
                ser.write(message.encode('utf-8'))
                packets_sent += 1
                last_send_time = current_time
            
            time.sleep(0.1)  # Small sleep to prevent busy-waiting
        
        if console:
            console.print(f"[green]📤 Total packets sent to Arduino:[/green] {packets_sent}")
        else:
            print(f"📤 Total packets sent to Arduino: {packets_sent}")
        
    except serial.SerialException as e:
        if console:
            console.print(f"[yellow]⚠️  Warning: Serial communication error:[/yellow] {e}")
            console.print("   Continuing benchmark without serial output.")
        else:
            print(f"⚠️  Warning: Serial communication error: {e}")
            print("   Continuing benchmark without serial output.")
        serial_connected = False
    except Exception as e:
        if console:
            console.print(f"[yellow]⚠️  Warning: Unexpected serial error:[/yellow] {e}")
        else:
            print(f"⚠️  Warning: Unexpected serial error: {e}")
        serial_connected = False
    finally:
        if ser and ser.is_open:
            ser.close()
            if console:
                console.print("[dim]🔌 Serial port closed[/dim]")
            else:
                print("🔌 Serial port closed")


def create_stats_table(power_values: List[float], inference_count: int, elapsed_time: float) -> Table:
    """Create a rich table with current statistics."""
    if not power_values:
        return Table(title="📊 Statistics", show_header=True, header_style="bold magenta")
    
    stats = {
        'Current': f"{power_values[-1]:.1f} mW" if power_values else "N/A",
        'Min': f"{min(power_values):.1f} mW",
        'Max': f"{max(power_values):.1f} mW",
        'Mean': f"{np.mean(power_values):.1f} mW",
        'Median': f"{np.median(power_values):.1f} mW",
        'Samples': len(power_values),
        'Inferences': f"{inference_count:,}",
        'Throughput': f"{inference_count / elapsed_time:.1f} inf/sec" if elapsed_time > 0 else "N/A",
        'Elapsed': f"{elapsed_time:.1f}s"
    }
    
    table = Table(title="📊 Real-Time Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    for key, value in stats.items():
        table.add_row(key, value)
    
    return table


def create_power_bar(current_power: float, min_power: float, max_power: float) -> Text:
    """Create a visual power bar using rich."""
    if max_power == min_power:
        return Text("No data", style="dim")
    
    # Normalize power to 0-100
    normalized = ((current_power - min_power) / (max_power - min_power)) * 100
    normalized = max(0, min(100, normalized))
    
    bar_length = 40
    filled = int((normalized / 100) * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    # Color based on power level
    if normalized > 80:
        style = "bold red"
    elif normalized > 50:
        style = "yellow"
    else:
        style = "green"
    
    return Text(f"[{style}]{bar}[/{style}] {current_power:.1f} mW")


def display_live_stats(power_queue: Queue, inference_count_ref: list, start_time_ref: list):
    """Display live statistics using rich."""
    global running
    
    power_values = []
    last_update = time.time()
    
    while running:
        # Collect power values from queue
        while not power_queue.empty():
            try:
                _, power_mw = power_queue.get_nowait()
                power_history.append(power_mw)
                power_values.append(power_mw)
            except:
                pass
        
        # Update display every 0.5 seconds
        if time.time() - last_update >= 0.5:
            if power_values:
                current_power = power_values[-1]
                elapsed = time.time() - start_time_ref[0] if start_time_ref else 0
                inf_count = inference_count_ref[0] if inference_count_ref else 0
                
                # Create layout
                layout = Layout()
                
                # Statistics table
                stats_table = create_stats_table(power_values[-100:], inf_count, elapsed)
                
                # Power bar
                if len(power_values) > 1:
                    power_bar = create_power_bar(
                        current_power,
                        min(power_values),
                        max(power_values)
                    )
                else:
                    power_bar = Text(f"Current: {current_power:.1f} mW", style="green")
                
                # Create panel
                content = f"\n{power_bar}\n\n{stats_table}"
                panel = Panel(
                    content,
                    title="⚡ Real-Time Power Monitoring",
                    border_style="blue",
                    padding=(1, 2)
                )
                
                console.print(panel)
                console.print()  # Blank line
                
                last_update = time.time()
        
        time.sleep(0.1)


def inference_loop(model: ct.models.MLModel, input_name: str, input_data: np.ndarray, 
                   timeout_seconds: Optional[float] = None, inference_count_ref: list = None):
    """
    Run CoreML inference in an infinite loop on the Neural Engine.
    
    Args:
        model: CoreML model
        input_name: Input tensor name
        input_data: Input data array
        timeout_seconds: Optional timeout in seconds (for test mode)
        inference_count_ref: List to store inference count (for threading)
    """
    global running, inference_count, start_time
    
    if console:
        console.print("[cyan]🔄 Starting inference loop on Neural Engine...[/cyan]")
        if timeout_seconds:
            console.print(f"   [dim]Test mode: Will run for {timeout_seconds} seconds[/dim]")
    else:
        print("🔄 Starting inference loop on Neural Engine...")
        if timeout_seconds:
            print(f"   Test mode: Will run for {timeout_seconds} seconds")
    
    inference_count = 0
    start_time = time.time()
    if inference_count_ref is not None:
        inference_count_ref.append(0)
    
    try:
        while running:
            # Check timeout if in test mode
            if timeout_seconds and (time.time() - start_time) >= timeout_seconds:
                if console:
                    console.print(f"\n[cyan]⏱️  Test timeout reached ({timeout_seconds}s)[/cyan]")
                else:
                    print(f"\n⏱️  Test timeout reached ({timeout_seconds}s)")
                break
            
            # Run inference
            _ = model.predict({input_name: input_data})
            inference_count += 1
            if inference_count_ref is not None:
                inference_count_ref[0] = inference_count
            
            # Small sleep to prevent overwhelming the system
            time.sleep(0.001)
    
    except KeyboardInterrupt:
        pass
    except Exception as e:
        if console:
            console.print(f"[bold red]❌ Error in inference loop:[/bold red] {e}")
        else:
            print(f"❌ Error in inference loop: {e}")
    
    elapsed = time.time() - start_time
    avg_throughput = inference_count / elapsed if elapsed > 0 else 0
    
    if console:
        console.print(f"\n[green]✅ Inference loop completed.[/green]")
        console.print(f"   Total inferences: [cyan]{inference_count:,}[/cyan]")
        console.print(f"   Avg throughput: [cyan]{avg_throughput:.1f} inf/sec[/cyan]")
    else:
        print(f"✅ Inference loop completed. Total inferences: {inference_count} | Avg throughput: {avg_throughput:.1f} inf/sec")


def print_summary(power_values: List[float], inference_count: int, elapsed_time: float, serial_connected: bool):
    """Print final summary statistics."""
    if not power_values:
        if console:
            console.print("[yellow]⚠️  No power data collected[/yellow]")
        else:
            print("⚠️  No power data collected")
        return
    
    if console:
        console.print("\n" + "=" * 70)
        console.print("[bold cyan]📊 FINAL SUMMARY[/bold cyan]")
        console.print("=" * 70)
        
        summary_table = Table(show_header=True, header_style="bold magenta")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Total Inferences", f"{inference_count:,}")
        summary_table.add_row("Elapsed Time", f"{elapsed_time:.2f} seconds")
        summary_table.add_row("Average Throughput", f"{inference_count / elapsed_time:.1f} inf/sec")
        summary_table.add_row("", "")
        summary_table.add_row("Power Samples", f"{len(power_values)}")
        summary_table.add_row("Min Power", f"{min(power_values):.2f} mW")
        summary_table.add_row("Max Power", f"{max(power_values):.2f} mW")
        summary_table.add_row("Mean Power", f"{np.mean(power_values):.2f} mW")
        summary_table.add_row("Median Power", f"{np.median(power_values):.2f} mW")
        summary_table.add_row("Std Dev", f"{np.std(power_values):.2f} mW")
        summary_table.add_row("", "")
        summary_table.add_row("Arduino Connected", "✅ Yes" if serial_connected else "❌ No")
        
        console.print(summary_table)
        console.print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("📊 FINAL SUMMARY")
        print("=" * 70)
        print(f"Total Inferences: {inference_count:,}")
        print(f"Elapsed Time: {elapsed_time:.2f} seconds")
        print(f"Average Throughput: {inference_count / elapsed_time:.1f} inf/sec")
        print()
        print(f"Power Samples: {len(power_values)}")
        print(f"Min Power: {min(power_values):.2f} mW")
        print(f"Max Power: {max(power_values):.2f} mW")
        print(f"Mean Power: {np.mean(power_values):.2f} mW")
        print(f"Median Power: {np.median(power_values):.2f} mW")
        print(f"Std Dev: {np.std(power_values):.2f} mW")
        print()
        print(f"Arduino Connected: {'✅ Yes' if serial_connected else '❌ No'}")
        print("=" * 70)


def main():
    """Main function to orchestrate the unified benchmark."""
    global running, serial_connected
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Unified Benchmark: CoreML inference with power monitoring and Arduino serial output'
    )
    parser.add_argument(
        '--test',
        type=float,
        metavar='SECONDS',
        help='Run in test mode for specified number of seconds (useful for verification)'
    )
    parser.add_argument(
        '--no-visual',
        action='store_true',
        help='Disable rich visual output (use basic text mode)'
    )
    args = parser.parse_args()
    
    use_rich = RICH_AVAILABLE and not args.no_visual
    
    if use_rich:
        console.print("=" * 70)
        console.print("[bold cyan]🚀 Unified Benchmark: CoreML + Power Monitoring + Arduino[/bold cyan]")
        if args.test:
            console.print(f"[yellow]🧪 TEST MODE: Running for {args.test} seconds[/yellow]")
        console.print("=" * 70)
        console.print()
    else:
        print("=" * 70)
        print("🚀 Unified Benchmark: CoreML + Power Monitoring + Arduino")
        if args.test:
            print(f"🧪 TEST MODE: Running for {args.test} seconds")
        print("=" * 70)
        print()
    
    # 1. Load CoreML model
    if use_rich:
        with console.status("[bold green]Loading MobileNetV2.mlpackage...") as status:
            try:
                model = ct.models.MLModel(
                    "MobileNetV2.mlpackage",
                    compute_units=ct.ComputeUnit.ALL  # Use Neural Engine
                )
                console.print("[green]✅ Model loaded successfully[/green]")
            except Exception as e:
                console.print(f"[bold red]❌ Failed to load model:[/bold red] {e}")
                return 1
    else:
        print("📦 Loading MobileNetV2.mlpackage...")
        try:
            model = ct.models.MLModel(
                "MobileNetV2.mlpackage",
                compute_units=ct.ComputeUnit.ALL  # Use Neural Engine
            )
            print("✅ Model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            return 1
    
    # 2. Detect input name
    if use_rich:
        console.print("[cyan]🔍 Detecting model input name...[/cyan]")
    else:
        print("🔍 Detecting model input name...")
    input_name = get_model_input_name(model)
    if use_rich:
        console.print(f"[green]✅ Using input name:[/green] '{input_name}'")
    else:
        print(f"✅ Using input name: '{input_name}'")
    
    # 3. Prepare input data
    input_data = np.random.rand(1, 3, 224, 224).astype(np.float32)
    if use_rich:
        console.print("[green]✅ Input tensor prepared:[/green] (1, 3, 224, 224)")
    else:
        print("✅ Input tensor prepared: (1, 3, 224, 224)")
    
    # 4. Warmup
    if use_rich:
        with console.status("[bold yellow]🔥 Warming up model...") as status:
            try:
                for _ in range(10):
                    _ = model.predict({input_name: input_data})
                console.print("[green]✅ Warmup complete[/green]")
            except Exception as e:
                console.print(f"[bold red]❌ Warmup failed:[/bold red] {e}")
                return 1
    else:
        print("\n🔥 Warming up model...")
        try:
            for _ in range(10):
                _ = model.predict({input_name: input_data})
            print("✅ Warmup complete")
        except Exception as e:
            print(f"❌ Warmup failed: {e}")
            return 1
    
    # 5. Find Arduino port
    if use_rich:
        console.print("\n[cyan]🔌 Searching for Arduino...[/cyan]")
    else:
        print("\n🔌 Searching for Arduino...")
    arduino_port = find_arduino_port()
    
    # 6. Create power queue for thread communication
    power_queue = Queue()
    
    # 7. Start powermetrics reader thread
    if use_rich:
        console.print("\n[cyan]⚡ Starting power monitoring...[/cyan]")
    else:
        print("\n⚡ Starting power monitoring...")
    power_thread = threading.Thread(
        target=powermetrics_reader,
        args=(power_queue, 500),
        daemon=True
    )
    power_thread.start()
    time.sleep(2)  # Give powermetrics time to start
    
    # 8. Start serial writer thread
    if use_rich:
        console.print("[cyan]📡 Starting serial communication...[/cyan]")
    else:
        print("\n📡 Starting serial communication...")
    serial_thread = threading.Thread(
        target=serial_writer,
        args=(power_queue, arduino_port, 115200),
        daemon=True
    )
    serial_thread.start()
    time.sleep(0.5)
    
    # 9. Start statistics display thread (if using rich)
    inference_count_ref = [0]
    start_time_ref = [time.time()]
    display_thread = None
    
    if use_rich:
        display_thread = threading.Thread(
            target=display_live_stats,
            args=(power_queue, inference_count_ref, start_time_ref),
            daemon=True
        )
        display_thread.start()
    
    # 10. Run inference loop in main thread
    if use_rich:
        console.print("\n" + "=" * 70)
        if args.test:
            console.print(f"[bold cyan]🎯 Starting test benchmark ({args.test}s) - Press Ctrl+C to stop early[/bold cyan]")
        else:
            console.print("[bold cyan]🎯 Starting benchmark (Press Ctrl+C to stop)[/bold cyan]")
        console.print("=" * 70)
        console.print()
    else:
        print("\n" + "=" * 70)
        if args.test:
            print(f"🎯 Starting test benchmark ({args.test}s) - Press Ctrl+C to stop early")
        else:
            print("🎯 Starting benchmark (Press Ctrl+C to stop)")
        print("=" * 70)
        print()
    
    try:
        inference_loop(model, input_name, input_data, timeout_seconds=args.test, 
                      inference_count_ref=inference_count_ref)
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        # Give threads a moment to finish
        time.sleep(1)
        
        # Collect final power values
        final_power_values = list(power_history)
        elapsed_time = time.time() - start_time_ref[0] if start_time_ref else 0
        
        # Print summary
        print_summary(final_power_values, inference_count_ref[0], elapsed_time, serial_connected)
        
        if use_rich:
            console.print("\n[bold green]✅ Benchmark complete![/bold green]")
        else:
            print("\n✅ Benchmark complete!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
