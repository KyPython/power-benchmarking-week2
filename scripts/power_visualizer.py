#!/usr/bin/env python3
"""
Power Visualizer - Create graphs and dashboards from power log data
Turns CSV data into visualizations using matplotlib.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
import sys
import argparse
from datetime import datetime


def load_power_data(csv_path: Path) -> pd.DataFrame:
    """Load power data from CSV file."""
    try:
        df = pd.read_csv(csv_path)
        
        # Convert timestamp to datetime if available
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        elif 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Set datetime as index
        if 'datetime' in df.columns:
            df.set_index('datetime', inplace=True)
        
        return df
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        sys.exit(1)


def create_power_graph(df: pd.DataFrame, output_path: Path, title: str = "Power Consumption Over Time"):
    """
    Create a professional-looking power consumption graph with matplotlib.
    Includes styling, multiple subplots, and statistical annotations.
    """
    # Set professional matplotlib style
    plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
    
    # Create figure with subplots for better organization
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # Main power plot
    ax_main = fig.add_subplot(gs[0, :])
    
    # Plot available power metrics with distinct colors and styles
    power_columns = ['ane_power_mw', 'cpu_power_mw', 'gpu_power_mw', 'total_power_mw']
    available_columns = [col for col in power_columns if col in df.columns]
    
    if not available_columns:
        print("⚠️  No power data columns found in CSV")
        return
    
    # Color palette for different power metrics
    colors = {
        'ane_power_mw': '#2E86AB',      # Blue
        'cpu_power_mw': '#A23B72',      # Purple
        'gpu_power_mw': '#F18F01',      # Orange
        'total_power_mw': '#C73E1D'     # Red
    }
    
    # Line styles for clarity
    linestyles = {
        'ane_power_mw': '-',
        'cpu_power_mw': '--',
        'gpu_power_mw': '-.',
        'total_power_mw': ':'
    }
    
    for col in available_columns:
        if df[col].notna().any():
            label = col.replace('_', ' ').replace('mw', 'mW').title()
            color = colors.get(col, None)
            linestyle = linestyles.get(col, '-')
            
            ax_main.plot(
                df.index, df[col],
                label=label,
                linewidth=2.5,
                alpha=0.85,
                color=color,
                linestyle=linestyle,
                marker='o' if len(df) < 100 else None,
                markersize=3 if len(df) < 100 else 0
            )
            
            # Add mean line annotation
            mean_val = df[col].mean()
            ax_main.axhline(y=mean_val, color=color, linestyle='--', alpha=0.5, linewidth=1)
            ax_main.text(
                df.index[-1], mean_val,
                f'  Avg: {mean_val:.0f} mW',
                color=color,
                fontsize=9,
                verticalalignment='center'
            )
    
    ax_main.set_xlabel('Time', fontsize=13, fontweight='bold')
    ax_main.set_ylabel('Power (mW)', fontsize=13, fontweight='bold')
    ax_main.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax_main.legend(loc='upper left', framealpha=0.9, fontsize=10)
    ax_main.grid(True, alpha=0.3, linestyle='--')
    
    # Format x-axis dates
    if isinstance(df.index, pd.DatetimeIndex):
        ax_main.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        interval = max(1, len(df) // 15)
        ax_main.xaxis.set_major_locator(mdates.SecondLocator(interval=interval))
        plt.setp(ax_main.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Statistics subplot (if we have multiple metrics)
    if len(available_columns) > 1:
        ax_stats = fig.add_subplot(gs[1, 0])
        
        # Bar chart of average power
        means = [df[col].mean() for col in available_columns]
        labels = [col.replace('_', ' ').replace('mw', 'mW').title() for col in available_columns]
        bar_colors = [colors.get(col, '#808080') for col in available_columns]
        
        bars = ax_stats.bar(labels, means, color=bar_colors, alpha=0.7, edgecolor='black', linewidth=1.5)
        ax_stats.set_ylabel('Average Power (mW)', fontsize=11, fontweight='bold')
        ax_stats.set_title('Average Power by Component', fontsize=12, fontweight='bold')
        ax_stats.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, mean in zip(bars, means):
            height = bar.get_height()
            ax_stats.text(bar.get_x() + bar.get_width()/2., height,
                         f'{mean:.0f}',
                         ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        plt.setp(ax_stats.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Power distribution subplot
    if 'total_power_mw' in df.columns and df['total_power_mw'].notna().any():
        ax_dist = fig.add_subplot(gs[1, 1])
        
        power_data = df['total_power_mw'].dropna()
        ax_dist.hist(power_data, bins=30, color='#C73E1D', alpha=0.7, edgecolor='black', linewidth=1)
        ax_dist.axvline(power_data.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {power_data.mean():.0f} mW')
        ax_dist.axvline(power_data.median(), color='blue', linestyle='--', linewidth=2, label=f'Median: {power_data.median():.0f} mW')
        ax_dist.set_xlabel('Power (mW)', fontsize=11, fontweight='bold')
        ax_dist.set_ylabel('Frequency', fontsize=11, fontweight='bold')
        ax_dist.set_title('Power Distribution', fontsize=12, fontweight='bold')
        ax_dist.legend(fontsize=9)
        ax_dist.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Professional graph saved: {output_path} (300 DPI)")


def create_summary_stats(df: pd.DataFrame) -> dict:
    """Calculate summary statistics."""
    stats = {}
    
    power_columns = ['ane_power_mw', 'cpu_power_mw', 'gpu_power_mw', 'total_power_mw']
    
    for col in power_columns:
        if col in df.columns and df[col].notna().any():
            stats[col] = {
                'mean': df[col].mean(),
                'min': df[col].min(),
                'max': df[col].max(),
                'std': df[col].std(),
                'count': df[col].notna().sum()
            }
    
    return stats


def print_summary_table(stats: dict):
    """Print summary statistics as a table."""
    print("\n" + "=" * 70)
    print("📊 POWER CONSUMPTION SUMMARY")
    print("=" * 70)
    
    if not stats:
        print("No power data available")
        return
    
    print(f"\n{'Metric':<20} {'Mean (mW)':<12} {'Min (mW)':<12} {'Max (mW)':<12} {'Std Dev':<12}")
    print("-" * 70)
    
    for col, data in stats.items():
        name = col.replace('_', ' ').replace('mw', 'mW').title()
        print(f"{name:<20} {data['mean']:>10.2f} {data['min']:>10.2f} {data['max']:>10.2f} {data['std']:>10.2f}")
    
    print("=" * 70)


def create_dashboard(csv_path: Path, output_dir: Path = None):
    """Create a complete dashboard with multiple visualizations."""
    if output_dir is None:
        output_dir = csv_path.parent
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print(f"📊 Loading data from: {csv_path}")
    df = load_power_data(csv_path)
    
    print(f"✅ Loaded {len(df)} data points")
    print(f"   Time range: {df.index.min()} to {df.index.max()}")
    
    # Create main power graph
    graph_path = output_dir / f"{csv_path.stem}_power_graph.png"
    create_power_graph(df, graph_path, f"Power Consumption - {csv_path.stem}")
    
    # Print summary statistics
    stats = create_summary_stats(df)
    print_summary_table(stats)
    
    # Create energy analysis if CPU energy is available
    if 'cpu_energy_mj' in df.columns and df['cpu_energy_mj'].notna().any():
        total_energy = df['cpu_energy_mj'].sum() / 1000  # Convert to J
        duration = (df.index.max() - df.index.min()).total_seconds()
        avg_power = total_energy / duration if duration > 0 else 0
        
        print(f"\n⚡ Energy Analysis:")
        print(f"   Total Energy: {total_energy:.2f} J")
        print(f"   Duration: {duration:.1f} s")
        print(f"   Average Power: {avg_power*1000:.2f} mW")
    
    return graph_path


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Visualize power consumption data from CSV logs'
    )
    parser.add_argument(
        'csv_file',
        type=str,
        help='Path to CSV file with power data'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output directory for graphs (default: same as CSV)'
    )
    parser.add_argument(
        '--show',
        action='store_true',
        help='Display graph in window (in addition to saving)'
    )
    
    args = parser.parse_args()
    
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return 1
    
    output_dir = Path(args.output) if args.output else None
    graph_path = create_dashboard(csv_path, output_dir)
    
    if args.show:
        plt.show()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

