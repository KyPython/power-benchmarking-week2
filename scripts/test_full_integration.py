#!/usr/bin/env python3
"""
Full Integration Test Script
Tests all components of the unified benchmark system.
"""

import sys
import subprocess
import time
from pathlib import Path

def test_imports():
    """Test that all required packages are installed."""
    print("🔍 Testing imports...")
    try:
        import coremltools as ct
        import numpy as np
        import serial
        import pandas as pd
        import matplotlib.pyplot as plt
        import psutil
        try:
            from rich.console import Console
            print("  ✅ Rich library available (enhanced visualization enabled)")
        except ImportError:
            print("  ⚠️  Rich library not available (will use basic output)")
        print("  ✅ All core imports successful")
        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        print("  💡 Run: pip install -r requirements.txt")
        return False

def test_model():
    """Test that the CoreML model exists and can be loaded."""
    print("\n🔍 Testing CoreML model...")
    model_path = Path("MobileNetV2.mlpackage")
    if not model_path.exists():
        print(f"  ❌ Model not found: {model_path}")
        print("  💡 Run: python3 scripts/convert_model.py")
        return False
    
    try:
        import coremltools as ct
        model = ct.models.MLModel(str(model_path), compute_units=ct.ComputeUnit.ALL)
        print("  ✅ Model loaded successfully")
        
        # Test inference
        import numpy as np
        input_data = np.random.rand(1, 3, 224, 224).astype(np.float32)
        spec = model.get_spec()
        input_name = spec.description.input[0].name
        _ = model.predict({input_name: input_data})
        print("  ✅ Model inference test successful")
        return True
    except Exception as e:
        print(f"  ❌ Model test failed: {e}")
        return False

def test_powermetrics():
    """Test that powermetrics is available and can be run."""
    print("\n🔍 Testing powermetrics...")
    try:
        result = subprocess.run(
            ['which', 'powermetrics'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  ✅ powermetrics found: {result.stdout.strip()}")
            
            # Test sudo access (non-interactive)
            result = subprocess.run(
                ['sudo', '-n', 'powermetrics', '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print("  ✅ sudo access confirmed")
            else:
                print("  ⚠️  sudo access may require password (this is normal)")
            return True
        else:
            print("  ❌ powermetrics not found")
            print("  💡 powermetrics should be available on macOS")
            return False
    except Exception as e:
        print(f"  ⚠️  Could not test powermetrics: {e}")
        return False

def test_arduino():
    """Test Arduino connection (optional)."""
    print("\n🔍 Testing Arduino connection...")
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        arduino_ports = [p for p in ports if 'usbmodem' in p.device.lower()]
        
        if arduino_ports:
            print(f"  ✅ Found {len(arduino_ports)} Arduino device(s):")
            for port in arduino_ports:
                print(f"     - {port.device}")
            return True
        else:
            print("  ⚠️  No Arduino found (this is optional)")
            print("  💡 Connect Arduino and upload arduino_power_receiver.ino")
            return True  # Not a failure, just optional
    except Exception as e:
        print(f"  ⚠️  Could not test Arduino: {e}")
        return True  # Not critical

def test_scripts():
    """Test that all scripts are executable."""
    print("\n🔍 Testing scripts...")
    scripts_dir = Path("scripts")
    required_scripts = [
        "unified_benchmark.py",
        "benchmark.py",
        "benchmark_power.py",
        "power_logger.py",
        "power_visualizer.py"
    ]
    
    all_exist = True
    for script in required_scripts:
        script_path = scripts_dir / script
        if script_path.exists():
            print(f"  ✅ {script}")
        else:
            print(f"  ❌ {script} not found")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests."""
    print("=" * 70)
    print("🧪 Full Integration Test Suite")
    print("=" * 70)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("CoreML Model", test_model),
        ("powermetrics", test_powermetrics),
        ("Arduino", test_arduino),
        ("Scripts", test_scripts),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready.")
        print("\n💡 Next steps:")
        print("   1. Run: sudo python3 scripts/unified_benchmark.py --test 30")
        print("   2. Check Arduino Serial Monitor if connected")
        print("   3. Review the real-time statistics display")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

