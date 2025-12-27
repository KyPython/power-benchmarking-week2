#!/usr/bin/env python3
"""
Component Test Script - Verifies all parts of unified_benchmark.py
Run this before the full benchmark to ensure everything is ready.
"""

import sys
import coremltools as ct
import numpy as np
import serial.tools.list_ports
import re

def test_model_loading():
    """Test 1: Model loads correctly"""
    print("=" * 60)
    print("TEST 1: Model Loading")
    print("=" * 60)
    try:
        model = ct.models.MLModel(
            "MobileNetV2.mlpackage",
            compute_units=ct.ComputeUnit.ALL
        )
        print("✅ Model loaded successfully")
        
        # Get input name
        spec = model.get_spec()
        if spec.description.input:
            input_name = spec.description.input[0].name
            print(f"✅ Input name detected: '{input_name}'")
        else:
            print("⚠️  Warning: No input found in spec")
            return False
        
        # Test inference
        input_data = np.random.rand(1, 3, 224, 224).astype(np.float32)
        result = model.predict({input_name: input_data})
        print(f"✅ Inference successful (output keys: {list(result.keys())})")
        return True
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False


def test_ane_parsing():
    """Test 2: ANE Power parsing logic"""
    print("\n" + "=" * 60)
    print("TEST 2: ANE Power Parsing")
    print("=" * 60)
    
    def parse_ane_power(powermetrics_output):
        pattern1 = r'ANE\s+Power[:\s]+([\d.]+)\s*mW'
        match = re.search(pattern1, powermetrics_output, re.IGNORECASE)
        if match:
            return float(match.group(1))
        
        pattern2 = r'(?:ANE|Neural\s+Engine)[:\s]+([\d.]+)\s*mW'
        match = re.search(pattern2, powermetrics_output, re.IGNORECASE)
        if match:
            return float(match.group(1))
        
        lines = powermetrics_output.split('\n')
        for line in lines:
            if 'ane' in line.lower() and 'power' in line.lower():
                numbers = re.findall(r'[\d.]+', line)
                if numbers:
                    return float(numbers[0])
        
        return None
    
    test_cases = [
        ("ANE Power: 123.45 mW", 123.45),
        ("ANE: 456.78 mW", 456.78),
        ("Neural Engine: 789.01 mW", 789.01),
        ("Processor Energy:\n  ANE Power: 234.56 mW", 234.56),
        ("No power data", None),
    ]
    
    all_passed = True
    for test_input, expected in test_cases:
        result = parse_ane_power(test_input)
        if result == expected:
            print(f"✅ '{test_input[:30]}...' → {result} mW")
        else:
            print(f"❌ '{test_input[:30]}...' → Expected {expected}, got {result}")
            all_passed = False
    
    return all_passed


def test_serial_detection():
    """Test 3: Serial port detection"""
    print("\n" + "=" * 60)
    print("TEST 3: Serial Port Detection")
    print("=" * 60)
    
    try:
        ports = serial.tools.list_ports.comports()
        if ports:
            print(f"✅ Found {len(ports)} serial port(s):")
            arduino_found = False
            for port in ports:
                is_arduino = 'usbmodem' in port.device.lower()
                marker = "🔌" if is_arduino else "  "
                print(f"   {marker} {port.device}: {port.description}")
                if is_arduino:
                    arduino_found = True
            
            if not arduino_found:
                print("⚠️  No Arduino detected (this is OK - script will continue without it)")
            else:
                print("✅ Arduino detected!")
        else:
            print("⚠️  No serial ports found (this is OK)")
        
        return True
    except Exception as e:
        print(f"❌ Serial detection failed: {e}")
        return False


def test_powermetrics_availability():
    """Test 4: powermetrics availability"""
    print("\n" + "=" * 60)
    print("TEST 4: powermetrics Availability")
    print("=" * 60)
    
    import subprocess
    import shutil
    
    # Check if powermetrics exists
    powermetrics_path = shutil.which('powermetrics')
    if powermetrics_path:
        print(f"✅ powermetrics found at: {powermetrics_path}")
    else:
        print("❌ powermetrics not found in PATH")
        return False
    
    # Check if we can run it (will fail without sudo, but that's expected)
    try:
        result = subprocess.run(
            ['powermetrics', '--help'],
            capture_output=True,
            text=True,
            timeout=2
        )
        print("✅ powermetrics is executable")
        return True
    except subprocess.TimeoutExpired:
        print("⚠️  powermetrics help command timed out")
        return True  # Still OK
    except PermissionError:
        print("⚠️  powermetrics requires sudo (expected)")
        print("   You'll need to run: sudo python3 unified_benchmark.py")
        return True  # This is expected
    except Exception as e:
        print(f"⚠️  Could not test powermetrics: {e}")
        return True  # Don't fail on this


def main():
    """Run all component tests"""
    print("\n" + "🧪 COMPONENT VERIFICATION TEST SUITE" + "\n")
    
    results = []
    results.append(("Model Loading", test_model_loading()))
    results.append(("ANE Parsing", test_ane_parsing()))
    results.append(("Serial Detection", test_serial_detection()))
    results.append(("powermetrics", test_powermetrics_availability()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 All component tests passed!")
        print("\nNext step: Run the full benchmark with:")
        print("   sudo python3 unified_benchmark.py --test 10")
        print("\nOr run indefinitely:")
        print("   sudo python3 unified_benchmark.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix issues before running benchmark.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

