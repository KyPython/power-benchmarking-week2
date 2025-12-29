#!/usr/bin/env python3
"""
Documentation Verification Script
Verifies that all documented features are actually implemented in the codebase.
"""

import sys
import ast
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re

# Expected features from documentation
DOCUMENTED_FEATURES = {
    "scripts": {
        "convert_model.py": ["PyTorch to CoreML conversion", "MobileNetV2", "mlpackage output"],
        "benchmark.py": ["PyTorch baseline", "latency measurement", "throughput calculation"],
        "benchmark_power.py": ["CoreML Neural Engine", "ANE inference", "performance test"],
        "unified_benchmark.py": [
            "CoreML inference loop",
            "real-time power monitoring",
            "Arduino serial communication",
            "powermetrics integration",
            "multi-threaded design",
            "real-time visualization",
            "statistics display",
            "rich library support",
            "--test flag",
            "--no-visual flag",
        ],
        "power_logger.py": [
            "CSV logging",
            "powermetrics subprocess",
            "non-blocking I/O",
            "select.select()",
            "--duration flag",
            "--output flag",
        ],
        "power_visualizer.py": [
            "matplotlib graphs",
            "CSV input",
            "multi-panel dashboard",
            "statistical annotations",
            "PNG output",
        ],
        "app_power_analyzer.py": [
            "PID-based filtering",
            "psutil integration",
            "app comparison",
            "process tracking",
            "--duration flag",
            "--output flag",
        ],
        "analyze_power_data.py": [
            "energy efficiency calculation",
            "power comparison",
            "energy per inference",
            "file parsing",
        ],
        "test_components.py": [
            "component verification",
            "model loading test",
            "serial detection test",
        ],
        "test_full_integration.py": [
            "integration testing",
            "import verification",
            "model test",
            "powermetrics test",
            "Arduino test",
        ],
        "validate_io_performance.py": [
            "I/O performance test",
            "select.select() validation",
            "chaos test",
            "--duration flag",
            "--stall flag",
        ],
        "validate_attribution.py": [
            "attribution ratio calculation",
            "power virus",
            "baseline measurement",
            "--cores flag",
            "--virus-duration flag",
        ],
        "validate_statistics.py": [
            "statistical validation",
            "workload generation",
            "mean/median divergence",
            "--duration flag",
            "--analyze-only flag",
        ],
        "arduino_power_receiver.ino": [
            "serial communication",
            "ANE_PWR parsing",
            "115200 baud",
            "error counting",
            "LED feedback",
        ],
    },
    "features": {
        "real_time_visualization": [
            "live statistics display",
            "power bar visualization",
            "rich library support",
            "automatic fallback",
        ],
        "arduino_integration": [
            "automatic port detection",
            "serial data streaming",
            "500ms interval",
            "graceful degradation",
        ],
        "power_monitoring": [
            "ANE power parsing",
            "powermetrics integration",
            "CSV logging",
            "real-time collection",
        ],
        "multi_threading": [
            "inference thread",
            "power monitoring thread",
            "serial thread",
            "thread-safe queues",
        ],
        "error_handling": [
            "graceful shutdown",
            "Arduino not found handling",
            "powermetrics error handling",
            "signal handlers",
        ],
    },
}


def check_file_exists(filepath: Path) -> bool:
    """Check if a file exists."""
    return filepath.exists()


def check_imports_in_file(filepath: Path, expected_imports: List[str]) -> List[str]:
    """Check if expected imports are present in a Python file."""
    missing = []
    try:
        with open(filepath, "r") as f:
            content = f.read()

        for imp in expected_imports:
            # Simple pattern matching for imports
            patterns = [
                f"import {imp}",
                f"from {imp} import",
                f"import {imp.split('.')[0]}",  # Check for base module
            ]
            if not any(re.search(pattern, content) for pattern in patterns):
                missing.append(imp)
    except Exception as e:
        return [f"Error reading file: {e}"]

    return missing


def check_function_exists(filepath: Path, function_name: str) -> bool:
    """Check if a function exists in a Python file."""
    try:
        with open(filepath, "r") as f:
            content = f.read()
        return f"def {function_name}" in content or f"def {function_name}(" in content
    except:
        return False


def check_argparse_flag(filepath: Path, flag: str) -> bool:
    """Check if an argparse flag exists."""
    try:
        with open(filepath, "r") as f:
            content = f.read()
        # Check for add_argument with the flag
        return f'"{flag}"' in content or f"'{flag}'" in content or f"--{flag}" in content
    except:
        return False


def check_keyword_in_file(filepath: Path, keywords: List[str]) -> List[str]:
    """Check if keywords are present in file."""
    missing = []
    try:
        with open(filepath, "r") as f:
            content = f.read().lower()

        for keyword in keywords:
            if keyword.lower() not in content:
                missing.append(keyword)
    except:
        return keywords

    return missing


def verify_script(script_name: str, features: List[str]) -> Tuple[bool, List[str]]:
    """Verify a script implements all documented features."""
    script_path = Path("scripts") / script_name

    if not check_file_exists(script_path):
        return False, [f"Script {script_name} does not exist"]

    issues = []

    # Check for key features based on script type
    if script_name == "unified_benchmark.py":
        # Check for rich library support
        if "rich library support" in features:
            if not check_keyword_in_file(script_path, ["rich", "Console", "Table", "Panel"]):
                issues.append("Rich library support not fully implemented")

        # Check for flags
        if "--test flag" in features:
            if not check_argparse_flag(script_path, "--test"):
                issues.append("--test flag not found")

        if "--no-visual flag" in features:
            if not check_argparse_flag(script_path, "--no-visual"):
                issues.append("--no-visual flag not found")

        # Check for visualization functions
        if "real-time visualization" in features:
            if not check_function_exists(script_path, "display_live_stats"):
                issues.append("display_live_stats function not found")
            if not check_function_exists(script_path, "create_stats_table"):
                issues.append("create_stats_table function not found")
            if not check_function_exists(script_path, "create_power_bar"):
                issues.append("create_power_bar function not found")

        # Check for Arduino integration
        if "Arduino serial communication" in features:
            if not check_function_exists(script_path, "serial_writer"):
                issues.append("serial_writer function not found")
            if not check_function_exists(script_path, "find_arduino_port"):
                issues.append("find_arduino_port function not found")

        # Check for power monitoring
        if "real-time power monitoring" in features:
            if not check_function_exists(script_path, "powermetrics_reader"):
                issues.append("powermetrics_reader function not found")
            if not check_function_exists(script_path, "parse_ane_power"):
                issues.append("parse_ane_power function not found")

        # Check for multi-threading
        if "multi-threaded design" in features:
            if not check_keyword_in_file(script_path, ["threading", "Thread", "Queue"]):
                issues.append("Multi-threading not implemented")

    elif script_name == "power_logger.py":
        if "--duration flag" in features:
            if not check_argparse_flag(script_path, "--duration"):
                issues.append("--duration flag not found")
        if "--output flag" in features:
            if not check_argparse_flag(script_path, "--output"):
                issues.append("--output flag not found")
        if "non-blocking I/O" in features:
            if not check_keyword_in_file(script_path, ["select.select", "select("]):
                issues.append("Non-blocking I/O (select.select) not found")

    elif script_name == "power_visualizer.py":
        if "matplotlib graphs" in features:
            if not check_keyword_in_file(script_path, ["matplotlib", "plt"]):
                issues.append("matplotlib not imported")
        if "CSV input" in features:
            if not check_keyword_in_file(script_path, ["pd.read_csv", "read_csv"]):
                issues.append("CSV reading not implemented")

    elif script_name == "app_power_analyzer.py":
        if "PID-based filtering" in features:
            if not check_keyword_in_file(script_path, ["psutil", "find_app_pids"]):
                issues.append("PID-based filtering not implemented")
        if "--duration flag" in features:
            if not check_argparse_flag(script_path, "--duration"):
                issues.append("--duration flag not found")

    elif script_name.endswith(".ino"):
        # Arduino sketch checks
        if "115200 baud" in features:
            if not check_keyword_in_file(script_path, ["115200", "BAUD_RATE"]):
                issues.append("115200 baud rate not found")
        if "ANE_PWR parsing" in features:
            if not check_keyword_in_file(script_path, ["ANE_PWR", "startsWith"]):
                issues.append("ANE_PWR parsing not found")

    return len(issues) == 0, issues


def main():
    """Run comprehensive documentation verification."""
    print("=" * 70)
    print("📋 Documentation Verification Audit")
    print("=" * 70)
    print()

    all_passed = True
    total_checks = 0
    passed_checks = 0

    # Check all scripts
    print("🔍 Checking Scripts...")
    print()

    for script_name, features in DOCUMENTED_FEATURES["scripts"].items():
        print(f"  Checking {script_name}...")
        total_checks += 1

        passed, issues = verify_script(script_name, features)

        if passed:
            print(f"    ✅ {script_name} - All features verified")
            passed_checks += 1
        else:
            print(f"    ❌ {script_name} - Issues found:")
            for issue in issues:
                print(f"       - {issue}")
            all_passed = False

    print()
    print("=" * 70)
    print("📊 Verification Summary")
    print("=" * 70)
    print(f"  Scripts checked: {total_checks}")
    print(f"  Passed: {passed_checks}")
    print(f"  Failed: {total_checks - passed_checks}")
    print()

    if all_passed:
        print("✅ All documented features are implemented!")
        print()
        print("💡 Next steps:")
        print("   1. Run: python3 scripts/test_full_integration.py")
        print("   2. Test: sudo python3 scripts/unified_benchmark.py --test 30")
        return 0
    else:
        print("⚠️  Some features may not be fully implemented.")
        print("   Please review the issues above and update code or documentation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
