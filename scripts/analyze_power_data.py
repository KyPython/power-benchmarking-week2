#!/usr/bin/env python3
"""
Power Data Analysis Script
Analyzes powermetrics output to calculate energy efficiency.
"""

import sys
import re
from typing import List, Tuple, Optional

# Benchmark results from our tests
PYTORCH_LATENCY_MS = 28.01  # ms per inference
COREML_LATENCY_MS = 0.49  # ms per inference


def parse_powermetrics_file(filepath: str) -> List[Tuple[float, float]]:
    """
    Parse powermetrics output file.
    Returns list of (timestamp, power_mw) tuples.
    """
    power_readings = []

    try:
        with open(filepath, "r") as f:
            content = f.read()

        # Pattern to match ANE Power values
        pattern = r"ANE\s+Power[:\s]+([\d.]+)\s*mW"
        matches = re.finditer(pattern, content, re.IGNORECASE)

        for i, match in enumerate(matches):
            power_mw = float(match.group(1))
            # Use line number as proxy for timestamp
            power_readings.append((i * 0.5, power_mw))  # Assuming 500ms intervals

        return power_readings

    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return []
    except Exception as e:
        print(f"❌ Error parsing file: {e}")
        return []


def calculate_energy_efficiency(
    ane_power_mw: float, pytorch_power_mw: Optional[float] = None
) -> dict:
    """
    Calculate energy efficiency metrics.

    Args:
        ane_power_mw: Average ANE power in mW
        pytorch_power_mw: Average CPU power in mW (optional)

    Returns:
        Dictionary with efficiency metrics
    """
    # Convert latencies to seconds
    pytorch_latency_s = PYTORCH_LATENCY_MS / 1000.0
    coreml_latency_s = COREML_LATENCY_MS / 1000.0

    # Calculate energy per inference (mJ = mW × ms)
    pytorch_energy_mj = (pytorch_power_mw * pytorch_latency_s * 1000) if pytorch_power_mw else None
    coreml_energy_mj = ane_power_mw * coreml_latency_s * 1000

    # Calculate energy for 100 inferences
    pytorch_energy_100_mj = pytorch_energy_mj * 100 if pytorch_energy_mj else None
    coreml_energy_100_mj = coreml_energy_mj * 100

    results = {
        "ane_power_mw": ane_power_mw,
        "pytorch_power_mw": pytorch_power_mw,
        "coreml_energy_per_inf_mj": coreml_energy_mj,
        "pytorch_energy_per_inf_mj": pytorch_energy_mj,
        "coreml_energy_100_inf_mj": coreml_energy_100_mj,
        "pytorch_energy_100_inf_mj": pytorch_energy_100_mj,
    }

    if pytorch_energy_mj:
        results["efficiency_ratio"] = pytorch_energy_mj / coreml_energy_mj
        results["energy_savings_percent"] = (1 - (coreml_energy_mj / pytorch_energy_mj)) * 100

    return results


def print_analysis(results: dict):
    """Print formatted analysis results."""
    print("\n" + "=" * 70)
    print("ENERGY EFFICIENCY ANALYSIS")
    print("=" * 70)

    print(f"\n📊 Power Consumption:")
    print(f"   ANE Power:        {results['ane_power_mw']:.2f} mW")
    if results["pytorch_power_mw"]:
        print(f"   CPU Power:         {results['pytorch_power_mw']:.2f} mW")
        print(f"   Power Ratio:       {results['pytorch_power_mw'] / results['ane_power_mw']:.2f}x")

    print(f"\n⚡ Energy per Inference:")
    print(f"   CoreML (ANE):       {results['coreml_energy_per_inf_mj']:.4f} mJ")
    if results["pytorch_energy_per_inf_mj"]:
        print(f"   PyTorch (CPU):      {results['pytorch_energy_per_inf_mj']:.4f} mJ")
        print(f"   Efficiency Ratio:   {results['efficiency_ratio']:.1f}x more efficient")
        print(f"   Energy Savings:     {results['energy_savings_percent']:.1f}%")

    print(f"\n🔋 Energy for 100 Inferences:")
    print(f"   CoreML (ANE):       {results['coreml_energy_100_inf_mj']:.2f} mJ")
    if results["pytorch_energy_100_inf_mj"]:
        print(f"   PyTorch (CPU):      {results['pytorch_energy_100_inf_mj']:.2f} mJ")
        savings = results["pytorch_energy_100_inf_mj"] - results["coreml_energy_100_inf_mj"]
        print(f"   Energy Saved:       {savings:.2f} mJ ({savings/1000:.4f} J)")

    print("\n" + "=" * 70)

    # Summary
    print("\n📈 Summary:")
    speedup = PYTORCH_LATENCY_MS / COREML_LATENCY_MS
    print(f"   • Neural Engine is {speedup:.1f}x faster")
    if results.get("efficiency_ratio"):
        print(f"   • Neural Engine is {results['efficiency_ratio']:.1f}x more energy efficient")
        print(f"   • Combined: {results['efficiency_ratio'] * speedup:.1f}x better overall")
    print()


def main():
    """Main analysis function."""
    print("=" * 70)
    print("POWER EFFICIENCY ANALYSIS")
    print("=" * 70)

    if len(sys.argv) < 2:
        print("\nUsage: python3 analyze_power_data.py <ane_power_mw> [cpu_power_mw]")
        print("\nExample:")
        print("  python3 analyze_power_data.py 800")
        print("  python3 analyze_power_data.py 800 3000")
        print("\nOr provide a powermetrics output file:")
        print("  python3 analyze_power_data.py --file powermetrics_output.txt")
        return 1

    if sys.argv[1] == "--file":
        if len(sys.argv) < 3:
            print("❌ Please provide a file path")
            return 1

        power_readings = parse_powermetrics_file(sys.argv[2])
        if not power_readings:
            return 1

        # Calculate average power
        avg_power = sum(p[1] for p in power_readings) / len(power_readings)
        print(f"\n📊 Parsed {len(power_readings)} power readings")
        print(f"   Average ANE Power: {avg_power:.2f} mW")

        results = calculate_energy_efficiency(avg_power)
        print_analysis(results)

    else:
        # Direct power values
        try:
            ane_power = float(sys.argv[1])
            cpu_power = float(sys.argv[2]) if len(sys.argv) > 2 else None

            results = calculate_energy_efficiency(ane_power, cpu_power)
            print_analysis(results)

        except ValueError:
            print("❌ Invalid power values. Please provide numbers in mW.")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
