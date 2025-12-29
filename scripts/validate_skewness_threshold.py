#!/usr/bin/env python3
"""
Skewness Magnitude Math Validation
Tests the general formula: Mean = (L × f) + (H × (1-f))
By varying drop duration (f), determines the "Detection Threshold" - the exact point
where a background task becomes statistically significant enough to skew results.
"""

import numpy as np
import pandas as pd
import sys
import argparse
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
from pathlib import Path


def calculate_mean_formula(low_power: float, high_power: float, drop_fraction: float) -> float:
    """
    Calculate mean using the formula: Mean = (L × f) + (H × (1-f))

    Args:
        low_power: Power during drops (L)
        high_power: Power during active periods (H)
        drop_fraction: Fraction of time at low power (f)

    Returns:
        Calculated mean
    """
    return (low_power * drop_fraction) + (high_power * (1 - drop_fraction))


def generate_synthetic_workload(
    low_power: float,
    high_power: float,
    drop_fraction: float,
    duration: int = 60,
    sample_rate: float = 0.5,
) -> np.ndarray:
    """
    Generate synthetic power workload with specified drop fraction.

    Args:
        low_power: Power during drops (mW)
        high_power: Power during active periods (mW)
        drop_fraction: Fraction of time at low power (0.0-1.0)
        duration: Duration in seconds
        sample_rate: Sampling rate in seconds

    Returns:
        Array of power values
    """
    num_samples = int(duration / sample_rate)
    num_drops = int(num_samples * drop_fraction)
    num_active = num_samples - num_drops

    # Generate power values
    power_values = np.concatenate([np.full(num_drops, low_power), np.full(num_active, high_power)])

    # Shuffle to randomize order
    np.random.shuffle(power_values)

    return power_values


def calculate_statistics(power_values: np.ndarray) -> Dict[str, float]:
    """
    Calculate statistical metrics for power values.

    Returns:
        Dictionary with mean, median, std dev, divergence
    """
    mean = np.mean(power_values)
    median = np.median(power_values)
    std_dev = np.std(power_values)

    # Divergence: (median - mean) / median
    divergence = (median - mean) / median if median > 0 else 0

    return {
        "mean": mean,
        "median": median,
        "std_dev": std_dev,
        "divergence": divergence,
        "samples": len(power_values),
    }


def find_detection_threshold(
    low_power: float, high_power: float, median_power: float, threshold_divergence: float = 0.01
) -> Tuple[float, Dict[str, float]]:
    """
    Find the drop fraction (f) that produces a specific divergence threshold.

    Uses binary search to find the exact drop fraction where:
    divergence = threshold_divergence

    Args:
        low_power: Power during drops (L)
        high_power: Power during active periods (H)
        median_power: Target median power (typically = high_power for left-skewed)
        threshold_divergence: Target divergence (e.g., 0.01 = 1%)

    Returns:
        Tuple of (drop_fraction, statistics_dict)
    """
    # Binary search for drop fraction
    low_f = 0.0
    high_f = 1.0
    tolerance = 0.001

    best_f = 0.0
    best_stats = None
    min_diff = float("inf")

    for _ in range(50):  # Max iterations
        mid_f = (low_f + high_f) / 2

        # Generate workload
        power_values = generate_synthetic_workload(low_power, high_power, mid_f, duration=60)

        # Calculate statistics
        stats = calculate_statistics(power_values)

        # Check if we're close to target
        diff = abs(stats["divergence"] - threshold_divergence)
        if diff < min_diff:
            min_diff = diff
            best_f = mid_f
            best_stats = stats

        # Adjust search range
        if stats["divergence"] < threshold_divergence:
            low_f = mid_f
        else:
            high_f = mid_f

        if (high_f - low_f) < tolerance:
            break

    return best_f, best_stats


def test_formula_accuracy(
    low_power: float, high_power: float, drop_fractions: List[float]
) -> pd.DataFrame:
    """
    Test the accuracy of the formula across different drop fractions.

    Returns:
        DataFrame with results
    """
    results = []

    for f in drop_fractions:
        # Calculate using formula
        formula_mean = calculate_mean_formula(low_power, high_power, f)

        # Generate synthetic workload
        power_values = generate_synthetic_workload(low_power, high_power, f, duration=60)

        # Calculate actual statistics
        stats = calculate_statistics(power_values)
        actual_mean = stats["mean"]

        # Calculate error
        error = abs(formula_mean - actual_mean)
        error_percent = (error / actual_mean) * 100 if actual_mean > 0 else 0

        results.append(
            {
                "drop_fraction": f,
                "formula_mean": formula_mean,
                "actual_mean": actual_mean,
                "error": error,
                "error_percent": error_percent,
                "divergence": stats["divergence"],
                "median": stats["median"],
            }
        )

    return pd.DataFrame(results)


def plot_threshold_analysis(df: pd.DataFrame, output_path: Path):
    """Create visualization of threshold analysis."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Skewness Detection Threshold Analysis", fontsize=16, fontweight="bold")

    # Plot 1: Formula vs Actual Mean
    ax1 = axes[0, 0]
    ax1.plot(df["drop_fraction"], df["formula_mean"], "b-", label="Formula", linewidth=2)
    ax1.plot(df["drop_fraction"], df["actual_mean"], "r--", label="Actual", linewidth=2)
    ax1.set_xlabel("Drop Fraction (f)")
    ax1.set_ylabel("Mean Power (mW)")
    ax1.set_title("Formula Accuracy: Mean = (L × f) + (H × (1-f))")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Divergence vs Drop Fraction
    ax2 = axes[0, 1]
    ax2.plot(df["drop_fraction"], df["divergence"] * 100, "g-", linewidth=2)
    ax2.axhline(y=1.0, color="r", linestyle="--", label="1% Threshold")
    ax2.axhline(y=5.0, color="orange", linestyle="--", label="5% Threshold")
    ax2.set_xlabel("Drop Fraction (f)")
    ax2.set_ylabel("Divergence (%)")
    ax2.set_title("Mean/Median Divergence vs Drop Fraction")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Error Analysis
    ax3 = axes[1, 0]
    ax3.plot(df["drop_fraction"], df["error_percent"], "purple", linewidth=2)
    ax3.set_xlabel("Drop Fraction (f)")
    ax3.set_ylabel("Formula Error (%)")
    ax3.set_title("Formula Accuracy (Error %)")
    ax3.grid(True, alpha=0.3)

    # Plot 4: Detection Thresholds
    ax4 = axes[1, 1]
    thresholds = [0.01, 0.05, 0.10, 0.20]  # 1%, 5%, 10%, 20%
    threshold_fractions = []

    for threshold in thresholds:
        # Find drop fraction for this threshold
        # Use interpolation from divergence data
        f_interp = np.interp(threshold, df["divergence"], df["drop_fraction"])
        threshold_fractions.append(f_interp)

    ax4.bar(range(len(thresholds)), [f * 100 for f in threshold_fractions], color="teal")
    ax4.set_xticks(range(len(thresholds)))
    ax4.set_xticklabels([f"{t*100:.0f}%" for t in thresholds])
    ax4.set_xlabel("Divergence Threshold")
    ax4.set_ylabel("Required Drop Fraction (%)")
    ax4.set_title("Detection Threshold: Drop Fraction Needed")
    ax4.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"  ✅ Saved plot: {output_path}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Skewness Magnitude Math Validation: Test Mean formula and find detection thresholds"
    )
    parser.add_argument(
        "--low-power", type=float, default=1500.0, help="Low power during drops (mW, default: 1500)"
    )
    parser.add_argument(
        "--high-power",
        type=float,
        default=2100.0,
        help="High power during active periods (mW, default: 2100)",
    )
    parser.add_argument(
        "--median-power", type=float, default=2000.0, help="Target median power (mW, default: 2000)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.01,
        help="Detection threshold divergence (default: 0.01 = 1%%)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="skewness_threshold_analysis.png",
        help="Output plot path (default: skewness_threshold_analysis.png)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("🔬 Skewness Magnitude Math Validation")
    print("=" * 70)
    print()
    print(f"Parameters:")
    print(f"  Low Power (L):  {args.low_power:.1f} mW")
    print(f"  High Power (H): {args.high_power:.1f} mW")
    print(f"  Median Power:   {args.median_power:.1f} mW")
    print(f"  Threshold:     {args.threshold*100:.1f}% divergence")
    print()

    # Test formula across different drop fractions
    print("1️⃣  Testing formula accuracy across drop fractions...")
    drop_fractions = np.linspace(0.0, 0.5, 21)  # 0% to 50% in 2.5% steps
    df = test_formula_accuracy(args.low_power, args.high_power, drop_fractions)

    print(f"  ✅ Tested {len(df)} drop fractions")
    print(f"  ✅ Average formula error: {df['error_percent'].mean():.3f}%")
    print(f"  ✅ Max formula error: {df['error_percent'].max():.3f}%")
    print()

    # Find detection threshold
    print(f"2️⃣  Finding detection threshold ({args.threshold*100:.1f}% divergence)...")
    threshold_f, threshold_stats = find_detection_threshold(
        args.low_power, args.high_power, args.median_power, args.threshold
    )

    print(f"  ✅ Detection Threshold: {threshold_f*100:.2f}% drop fraction")
    print(f"     Mean: {threshold_stats['mean']:.2f} mW")
    print(f"     Median: {threshold_stats['median']:.2f} mW")
    print(f"     Divergence: {threshold_stats['divergence']*100:.2f}%")
    print()

    # Calculate thresholds for multiple levels
    print("3️⃣  Calculating thresholds for multiple detection levels...")
    detection_levels = [0.01, 0.05, 0.10, 0.20]  # 1%, 5%, 10%, 20%
    threshold_results = []

    for level in detection_levels:
        f, stats = find_detection_threshold(
            args.low_power, args.high_power, args.median_power, level
        )
        threshold_results.append(
            {
                "divergence_threshold": level * 100,
                "drop_fraction": f * 100,
                "mean": stats["mean"],
                "median": stats["median"],
            }
        )

    print()
    print("=" * 70)
    print("📊 DETECTION THRESHOLD RESULTS")
    print("=" * 70)
    print()
    print(f"{'Divergence':<15} {'Drop Fraction':<15} {'Mean':<12} {'Median':<12}")
    print("-" * 70)
    for result in threshold_results:
        print(
            f"{result['divergence_threshold']:>6.1f}%       "
            f"{result['drop_fraction']:>8.2f}%       "
            f"{result['mean']:>8.2f} mW  {result['median']:>8.2f} mW"
        )
    print()

    # Interpretation
    print("💡 Interpretation:")
    print()
    if threshold_f < 0.05:
        print("  ✅ LOW THRESHOLD: Background tasks become significant with <5% drop time")
        print("     Very sensitive detection - catches small background interference")
    elif threshold_f < 0.15:
        print("  ⚠️  MODERATE THRESHOLD: Background tasks need 5-15% drop time to be detected")
        print("     Moderate sensitivity - catches typical background tasks")
    else:
        print("  ⚠️  HIGH THRESHOLD: Background tasks need >15% drop time to be detected")
        print("     Less sensitive - may miss subtle background interference")
    print()

    # Create visualization
    print("4️⃣  Creating visualization...")
    output_path = Path(args.output)
    plot_threshold_analysis(df, output_path)
    print()

    # Formula validation
    print("5️⃣  Formula Validation:")
    print()
    print(f"  Formula: Mean = (L × f) + (H × (1-f))")
    print(f"  Where:")
    print(f"    L = Low power = {args.low_power:.1f} mW")
    print(f"    H = High power = {args.high_power:.1f} mW")
    print(f"    f = Drop fraction")
    print()
    print(f"  Example (f = {threshold_f:.3f}):")
    calculated = calculate_mean_formula(args.low_power, args.high_power, threshold_f)
    print(
        f"    Mean = ({args.low_power:.1f} × {threshold_f:.3f}) + ({args.high_power:.1f} × {1-threshold_f:.3f})"
    )
    print(f"    Mean = {calculated:.2f} mW")
    print(f"    Actual: {threshold_stats['mean']:.2f} mW")
    print(f"    Error: {abs(calculated - threshold_stats['mean']):.2f} mW")
    print()

    print("=" * 70)
    print("✅ Validation complete!")
    print()
    print("📈 Key Findings:")
    print(f"  • Detection threshold: {threshold_f*100:.2f}% drop fraction")
    print(f"  • Formula accuracy: {df['error_percent'].mean():.3f}% average error")
    print(f"  • Use this threshold to identify significant background tasks")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
