#!/usr/bin/env python3
"""
Unified Benchmark Script for Apple Silicon M2
Integrates CoreML inference with real-time power monitoring and Arduino serial communication.
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
from typing import Optional, Tuple

# Global flags for graceful shutdown
running = True
serial_connected = False


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global running
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
        
        print(f"✅ powermetrics started (sampling every {sample_interval}ms)")
        
        if process.stdout is None:
            print("❌ Error: powermetrics stdout is not available")
            return
        
        buffer = ""
        
        while running:
            chunk = process.stdout.read(1024)
            if not chunk:
                if process.poll() is not None:
                    break
                time.sleep(0.1)
                continue
            
            buffer += chunk
            
            # Try to parse ANE power from accumulated buffer
            # powermetrics outputs data in chunks, so we accumulate until we have a complete sample
            ane_power = parse_ane_power(buffer)
            
            if ane_power is not None:
                power_queue.put((time.time(), ane_power))
                # Clear buffer after successful parse (keep last 2KB for overlap)
                buffer = buffer[-2048:] if len(buffer) > 2048 else ""
            
            # Prevent buffer from growing too large
            if len(buffer) > 8192:
                buffer = buffer[-4096:]
        
        process.terminate()
        process.wait()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running powermetrics: {e}")
        print("   Make sure you have sudo permissions and powermetrics is available.")
    except Exception as e:
        print(f"❌ Unexpected error in powermetrics reader: {e}")


def serial_writer(power_queue: Queue, port: Optional[str], baudrate: int = 115200):
    """
    Read power values from queue and send them to Arduino via serial.
    Sends data every 500ms in format: ANE_PWR:[value]\n
    """
    global running, serial_connected
    
    if port is None:
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
        print(f"✅ Serial connection established: {port} @ {baudrate} baud")
        
        last_send_time = 0
        send_interval = 0.5  # 500ms
        
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
                print(f"📤 Sent: {message.strip()} (at {time.strftime('%H:%M:%S')})")
                last_send_time = current_time
            
            time.sleep(0.1)  # Small sleep to prevent busy-waiting
        
    except serial.SerialException as e:
        print(f"⚠️  Warning: Serial communication error: {e}")
        print("   Continuing benchmark without serial output.")
        serial_connected = False
    except Exception as e:
        print(f"⚠️  Warning: Unexpected serial error: {e}")
        serial_connected = False
    finally:
        if ser and ser.is_open:
            ser.close()
            print("🔌 Serial port closed")


def inference_loop(model: ct.models.MLModel, input_name: str, input_data: np.ndarray, timeout_seconds: Optional[float] = None):
    """
    Run CoreML inference in an infinite loop on the Neural Engine.
    
    Args:
        model: CoreML model
        input_name: Input tensor name
        input_data: Input data array
        timeout_seconds: Optional timeout in seconds (for test mode)
    """
    global running
    
    print("🔄 Starting inference loop on Neural Engine...")
    if timeout_seconds:
        print(f"   Test mode: Will run for {timeout_seconds} seconds")
    
    inference_count = 0
    start_time = time.time()
    
    try:
        while running:
            # Check timeout if in test mode
            if timeout_seconds and (time.time() - start_time) >= timeout_seconds:
                print(f"\n⏱️  Test timeout reached ({timeout_seconds}s)")
                break
            
            # Run inference
            _ = model.predict({input_name: input_data})
            inference_count += 1
            
            # Print progress every 100 inferences
            if inference_count % 100 == 0:
                elapsed = time.time() - start_time
                throughput = inference_count / elapsed if elapsed > 0 else 0
                print(f"   Inference count: {inference_count} | Throughput: {throughput:.1f} inf/sec")
            
            # Small sleep to prevent overwhelming the system
            time.sleep(0.001)
    
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ Error in inference loop: {e}")
    
    elapsed = time.time() - start_time
    avg_throughput = inference_count / elapsed if elapsed > 0 else 0
    print(f"✅ Inference loop completed. Total inferences: {inference_count} | Avg throughput: {avg_throughput:.1f} inf/sec")


def main():
    """Main function to orchestrate the unified benchmark."""
    global running
    
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
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Unified Benchmark: CoreML + Power Monitoring + Arduino")
    if args.test:
        print(f"🧪 TEST MODE: Running for {args.test} seconds")
    print("=" * 60)
    print()
    
    # 1. Load CoreML model
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
    print("🔍 Detecting model input name...")
    input_name = get_model_input_name(model)
    print(f"✅ Using input name: '{input_name}'")
    
    # 3. Prepare input data
    input_data = np.random.rand(1, 3, 224, 224).astype(np.float32)
    print("✅ Input tensor prepared: (1, 3, 224, 224)")
    
    # 4. Warmup
    print("\n🔥 Warming up model...")
    try:
        for _ in range(10):
            _ = model.predict({input_name: input_data})
        print("✅ Warmup complete")
    except Exception as e:
        print(f"❌ Warmup failed: {e}")
        return 1
    
    # 5. Find Arduino port
    print("\n🔌 Searching for Arduino...")
    arduino_port = find_arduino_port()
    
    # 6. Create power queue for thread communication
    power_queue = Queue()
    
    # 7. Start powermetrics reader thread
    print("\n⚡ Starting power monitoring...")
    power_thread = threading.Thread(
        target=powermetrics_reader,
        args=(power_queue, 500),
        daemon=True
    )
    power_thread.start()
    time.sleep(2)  # Give powermetrics time to start
    
    # 8. Start serial writer thread
    print("\n📡 Starting serial communication...")
    serial_thread = threading.Thread(
        target=serial_writer,
        args=(power_queue, arduino_port, 115200),
        daemon=True
    )
    serial_thread.start()
    time.sleep(0.5)
    
    # 9. Run inference loop in main thread
    print("\n" + "=" * 60)
    if args.test:
        print(f"🎯 Starting test benchmark ({args.test}s) - Press Ctrl+C to stop early")
    else:
        print("🎯 Starting benchmark (Press Ctrl+C to stop)")
    print("=" * 60)
    print()
    
    try:
        inference_loop(model, input_name, input_data, timeout_seconds=args.test)
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        # Give threads a moment to finish
        time.sleep(0.5)
        print("\n" + "=" * 60)
        print("✅ Benchmark complete!")
        print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

