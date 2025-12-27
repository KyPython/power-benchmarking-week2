# Advanced Features: Extending the Suite

**Single Responsibility**: Documents three advanced features that extend the power benchmarking suite to handle extreme scenarios, long-term profiling, and ANE/GPU monitoring.

---

## Overview

Three advanced features extend the suite's capabilities:

1. **Adversarial Benchmark**: Tests suite resilience under extreme stress
2. **Long-Term Efficiency Profiling**: Identifies worst battery drain offenders over days
3. **ANE/GPU Monitoring**: Applies statistical analysis to Neural Engine and GPU power

---

## 1. Adversarial Benchmark 🌪️

### Purpose

Tests the suite's response prioritization when multiple extreme events occur simultaneously:
- Heavy compile job on P-cores (CPU stress)
- SSH disconnect (SIGHUP signal)
- Multiple concurrent signals

### How It Works

**Script**: `scripts/adversarial_benchmark.py`

**Priority Rules:**
1. **SIGHUP (SSH disconnect)** - Highest priority (data integrity)
2. **SIGINT (Ctrl+C)** - High priority (user intent)
3. **SIGTERM (system shutdown)** - Medium priority
4. **SIGQUIT (debug)** - Low priority

**Response Time Guarantee:**
- All signals handled within 100ms (validated by heartbeat mechanism)
- SIGHUP prioritized for data integrity

### Usage

```bash
# Basic adversarial test (4 P-cores, 60s, SSH disconnect after 5s)
python3 scripts/adversarial_benchmark.py

# Custom stress test
python3 scripts/adversarial_benchmark.py \
  --stress-cores 6 \
  --stress-duration 120 \
  --ssh-delay 10.0
```

### Example Output

```
🌪️  ADVERSARIAL BENCHMARK: Extreme Stress Test
======================================================================

🔥 Creating CPU stress on 4 P-cores...
🔌 [5.0s] Simulating SSH disconnect (SIGHUP)...

🛑 [5.2ms] Received SIGHUP (SSH disconnect)
   Priority: CRITICAL (SSH disconnect, <100ms)

📊 ADVERSARIAL BENCHMARK REPORT
======================================================================

🎯 First Signal (Highest Priority Response):
   Signal: SIGHUP (SSH disconnect)
   Response Time: 5.2 ms
   Priority: CRITICAL (SSH disconnect, <100ms)

✅ Validation:
   ✅ Mean response time < 100ms (meets guarantee)
   ✅ First signal response < 100ms (meets guarantee)
   ✅ SIGHUP handled as highest priority (data integrity)
```

### Key Insights

- **SIGHUP is prioritized** even under extreme CPU stress
- **100ms guarantee holds** even with heavy compile job running
- **Data integrity protected** - SSH disconnect handled gracefully
- **Priority system works** - Critical signals processed first

---

## 2. Long-Term Efficiency Profiling 📈

### Purpose

Tracks daemon power consumption over days to identify which macOS background daemons are the "worst offenders" for battery drain on your specific machine.

### How It Works

**Script**: `scripts/long_term_profiler.py`

**Monitored Daemons:**
- `mds` - Spotlight indexing
- `backupd` - Time Machine
- `cloudd` - iCloud sync
- `bird` - iCloud Documents
- `photolibraryd` - Photos sync
- `mdworker` - Spotlight workers
- `kernel_task` - System kernel
- `WindowServer` - Graphics server
- And more...

**Power Tax Calculation:**
- Detects when daemons run on P-cores (inefficient)
- Estimates power tax based on validation data
- Tracks over time to identify patterns

### Usage

```bash
# Take a single snapshot
python3 scripts/long_term_profiler.py --snapshot

# Analyze last 7 days
python3 scripts/long_term_profiler.py --analyze 7

# Continuous profiling (every 60 minutes)
python3 scripts/long_term_profiler.py --continuous 60
```

### Example Output

```
📊 LONG-TERM EFFICIENCY PROFILE: Worst Battery Drain Offenders
======================================================================

📈 Analysis Period: 168 snapshots (7 days)
📊 Average Baseline: 850.3 mW

🏆 Top Battery Drain Offenders (by average power tax):

 1. mds
     Avg Tax: 650.2 mW
     Max Tax: 700.0 mW
     On P-Cores: 45.2% of time
     Snapshots: 168

 2. backupd
     Avg Tax: 420.5 mW
     Max Tax: 500.0 mW
     On P-Cores: 12.3% of time
     Snapshots: 168

 3. cloudd
     Avg Tax: 380.1 mW
     Max Tax: 400.0 mW
     On P-Cores: 8.7% of time
     Snapshots: 168

💡 Total Average Tax: 1450.8 mW
💡 Baseline Efficiency: 850.3 mW

💡 Recommendations:
   🎯 Focus on: mds, backupd, cloudd
   💡 Consider moving these to E-cores using taskpolicy
   💡 Estimated savings: 1450.8 mW
```

### Key Insights

- **Identifies worst offenders** - Which daemons waste the most power
- **Time-based patterns** - When daemons run on P-cores
- **Actionable recommendations** - Specific daemons to optimize
- **Quantified savings** - Exact mW savings potential

---

## 3. ANE/GPU Monitoring with Skewness & Attribution 🧠

### Purpose

Extends power monitoring to Apple Neural Engine (ANE) and GPU, applying the same statistical analysis (skewness, attribution) used for CPU.

### How It Works

**Script**: `scripts/ane_gpu_monitor.py`

**Statistical Analysis:**
- **Skewness Detection**: Mean/median divergence for ANE/GPU
- **Attribution Ratio**: Component contribution to total package power
- **Background Interference**: Detects when ANE/GPU idle periods affect measurements

**Power Metrics:**
- ANE Power (Neural Engine)
- GPU Power (Graphics)
- CPU Power (for comparison)
- Total Package Power

### Usage

```bash
# Monitor for 60 seconds
sudo python3 scripts/ane_gpu_monitor.py --duration 60

# Custom sampling interval
sudo python3 scripts/ane_gpu_monitor.py --duration 120 --interval 250
```

### Example Output

```
📊 ANE/GPU POWER ANALYSIS: Skewness & Attribution
======================================================================

📈 SKEWNESS ANALYSIS
----------------------------------------------------------------------

ANE Power:
  Mean:       1234.5 mW
  Median:     1200.0 mW
  Divergence:  2.88%
  Skew:       right-skewed
  Interpretation: Burst workloads increasing power (e.g., inference spikes)
  Range:    800.0 - 1800.0 mW
  Std Dev:   150.2 mW
  Samples:   120

GPU Power:
  Mean:       890.3 mW
  Median:     900.0 mW
  Divergence:  1.08%
  Skew:       left-skewed
  Interpretation: Background tasks reducing power (e.g., GPU idle periods)
  Drop Fraction: 1.08%
  Range:    600.0 - 1200.0 mW
  Std Dev:   120.5 mW
  Samples:   120

🎯 ATTRIBUTION ANALYSIS
----------------------------------------------------------------------

ANE Attribution:
  Component Power:  1234.5 mW
  Total Power:     4500.0 mW
  Attribution:      27.4% of total
  Delta Attribution: 35.2% of delta
  Samples:         120

GPU Attribution:
  Component Power:   890.3 mW
  Total Power:     4500.0 mW
  Attribution:      19.8% of total
  Delta Attribution: 25.1% of delta
  Samples:         120

💡 INTERPRETATION
----------------------------------------------------------------------

✅ ANE shows stable power consumption
⚠️  GPU shows significant divergence - background interference detected
📊 ANE contributes 27.4% of total package power
📊 GPU contributes 19.8% of total package power
```

### Key Insights

- **ANE power patterns** - How Neural Engine power consumption behaves
- **GPU power patterns** - Graphics power consumption analysis
- **Attribution breakdown** - What percentage of total power is ANE/GPU
- **Background detection** - When idle periods affect measurements
- **Same statistical rigor** - Skewness and attribution rules apply to all components

---

## Integration with Existing Suite

### Adversarial Benchmark

**Connection to Enhanced Signal Handler:**
- Tests the multi-signal handling under extreme conditions
- Validates 100ms response time guarantee
- Proves SIGHUP prioritization works in practice

**Use Cases:**
- Stress testing before deployment
- Validating robustness claims
- Demonstrating graceful shutdown under stress

### Long-Term Profiling

**Connection to Tax Correction:**
- Uses Tax Correction data to estimate daemon power
- Builds profile over time to identify patterns
- Provides actionable recommendations based on empirical data

**Use Cases:**
- Battery life optimization
- System tuning for efficiency
- Identifying problematic daemons

### ANE/GPU Monitoring

**Connection to Statistical Analysis:**
- Applies same skewness detection to ANE/GPU
- Uses same attribution ratio calculations
- Extends validation framework to accelerators

**Use Cases:**
- AI inference power analysis
- Graphics workload profiling
- Accelerator efficiency studies

---

## Technical Details

### Adversarial Benchmark

**Stress Creation:**
- Uses `taskpolicy` to force processes to P-cores
- Creates CPU stress with `yes` command
- Simulates SSH disconnect with `os.kill(SIGHUP)`

**Priority Calculation:**
- Signal type determines priority
- Response time affects priority level
- Critical signals (SIGHUP) always highest

### Long-Term Profiling

**Data Collection:**
- Snapshots stored as JSON files
- Timestamped for time-series analysis
- Includes baseline, daemon tax, and metadata

**Analysis:**
- Aggregates snapshots over time period
- Calculates average, max, and frequency
- Ranks daemons by average power tax

### ANE/GPU Monitoring

**Power Parsing:**
- Extends existing powermetrics parsing
- Handles ANE, GPU, CPU, and Total power
- Aligns arrays for attribution calculation

**Statistical Methods:**
- Same skewness formula: `Mean = (L × f) + (H × (1-f))`
- Same attribution ratio: `AR = (Component / Total) × 100`
- Same divergence thresholds: 1%, 5%, 10%

---

## Dependencies

All scripts use existing dependencies:
- `psutil` (for process management)
- `numpy` (for calculations)
- `statistics` (standard library)
- `subprocess` (standard library)
- `sudo` access (for powermetrics)

No new dependencies required!

---

## Next Steps

1. **Run adversarial benchmark** to validate robustness
2. **Start long-term profiling** to identify battery drain offenders
3. **Monitor ANE/GPU** during AI inference workloads
4. **Analyze results** to optimize system efficiency

---

## Advanced Technical Concepts

For deep technical explanations of:
- **Universality of the Math**: Why the skewness formula works across all accelerators
- **Signal Lifecycle**: How SIGHUP ensures data integrity before termination
- **Data to Decisions**: How profiling recommendations translate to actionable fixes

See **[ADVANCED_CONCEPTS.md](ADVANCED_CONCEPTS.md)**.

## Conclusion

These three advanced features extend the power benchmarking suite to handle:
- **Extreme stress scenarios** (adversarial benchmark)
- **Long-term efficiency analysis** (profiling)
- **Accelerator power monitoring** (ANE/GPU)

Together, they provide a complete framework for power analysis on Apple Silicon, from real-time monitoring to long-term optimization.

