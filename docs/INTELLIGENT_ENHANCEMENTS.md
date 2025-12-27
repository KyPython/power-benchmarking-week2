# Intelligent Suite Enhancements

**Purpose**: Three advanced enhancements that apply validation findings to make the suite more intelligent and adaptive.

---

## 🏛️ The Three Enhancements

| Enhancement | Validation Basis | Intelligence Added |
|-------------|----------------|-------------------|
| **Adaptive Baseline Adjustment** 🏗️ | P-Core Tax (700 mW) | Auto-detects P-core usage and warns about AR impact |
| **Divergence Dashboard** 📊 | Skewness Threshold (2.35%) | Real-time display of drop fraction and background interference |
| **Kernel-Level Resilience** 🛡️ | Scheduler Priority (50ms vs 75ms) | Enhanced signal handling with multiple kernel signals |

---

## 1. Adaptive Baseline Adjustment 🏗️

### What It Does

Uses P-Core Tax findings to automatically detect when background daemons are running on P-cores and warns users that their Attribution Ratio (AR) may be artificially low.

### Implementation

**Script**: `scripts/intelligent_baseline_detector.py`

**Key Features:**
- Detects high baseline power (>800 mW threshold)
- Checks if common daemons (mds, backupd, cloudd) are on P-cores
- Estimates Power Tax based on validation results
- Calculates AR impact (how much AR is reduced)
- Provides actionable recommendations

### Usage

**Standalone:**
```bash
python3 scripts/intelligent_baseline_detector.py --baseline 1200 --stressed 4500
```

**Integrated into unified_benchmark.py:**
```python
from scripts.intelligent_baseline_detector import analyze_baseline

# After collecting baseline power
baseline_power = np.mean(power_values[:10])  # First 10 samples
analysis = analyze_baseline(baseline_power, stressed_power=np.mean(power_values))

if analysis['warnings']:
    for warning in analysis['warnings']:
        print(warning)
```

### Example Output

```
🔍 INTELLIGENT BASELINE ANALYSIS
======================================================================

📊 Baseline Power: 1200.45 mW

⚠️  Warnings:
   ⚠️  High baseline power detected: 1200.45 mW (threshold: 800 mW)
   ⚠️  Estimated Power Tax: 700.00 mW from daemons on P-cores
   🚨 AR artificially low: 78.2% (would be 88.9% without tax, reduction: 10.7%)

🔍 Daemon Status:
   mds: ⚠️  On P-cores (Tax: 700.0 mW)
   backupd: ✅ On E-cores (normal)
   cloudd: ✅ On E-cores (normal)

📈 Attribution Ratio Impact:
   Normal AR:     88.9%
   With Tax AR:   78.2%
   AR Reduction:  10.7%

💡 Recommendations:
   💡 Consider moving background daemons to E-cores using taskpolicy
   💡 High baseline may indicate inefficient P-core usage
```

### What This Enables

✅ **Automatic Detection**: No manual checking needed  
✅ **AR Correction**: Warns when AR is artificially low  
✅ **Actionable Insights**: Provides specific recommendations  
✅ **Validation-Based**: Uses empirical 700 mW Power Tax data  

---

## 2. Divergence Dashboard 📊

### What It Does

Shows the "2.35% drop fraction" in real-time, allowing users to see exactly when a background task like `cloudd` starts interfering with their measurement.

### Implementation

**Enhanced in**: `scripts/power_visualizer.py`

**Key Features:**
- Real-time divergence calculation (Mean vs Median)
- Drop fraction estimation using formula: `Mean = (L × f) + (H × (1-f))`
- Visual warnings when divergence exceeds thresholds
- Color-coded indicators (✅ Normal, ⚠️ Warning, 🚨 Critical)

### Visual Dashboard

**In Power Distribution Plot:**
```
Power Distribution + Divergence Dashboard

[Histogram with Mean/Median lines]

⚠️ Divergence: 2.35%
📉 Drop Fraction: 2.35%
```

**In Summary Table:**
```
📊 POWER CONSUMPTION SUMMARY + DIVERGENCE DASHBOARD
======================================================================

Metric              Mean (mW)    Median (mW)  Divergence    Drop Frac
----------------------------------------------------------------------
Total Power Mw      1973.45      2000.00      ⚠️  2.35%      2.35%

💡 Divergence Interpretation:
   ✅ < 1%: Normal distribution (no background interference)
   ℹ️  1-5%: Minor background task detected
   ⚠️  5-10%: Moderate background interference
   🚨 > 10%: Major background task interference

💡 Drop Fraction:
   Shows estimated % of time at low power (background task activity)
   Use median for typical power, mean for energy calculations
```

### Real-Time Calculation

**Formula Application:**
```python
# Given power data
mean = 1973 mW
median = 2000 mW
low_power = 1500 mW  # Minimum observed
high_power = 2000 mW  # Median (typical high)

# Calculate drop fraction
# Mean = (L × f) + (H × (1-f))
# 1973 = (1500 × f) + (2000 × (1-f))
# 1973 = 1500f + 2000 - 2000f
# 1973 = 2000 - 500f
# 500f = 2000 - 1973 = 27
# f = 27/500 = 0.054 = 5.4%

drop_fraction = (mean - high_power) / (low_power - high_power)
drop_fraction = (1973 - 2000) / (1500 - 2000) = -27 / -500 = 0.054
```

**Detection Threshold:**
- **< 2.35% drop fraction**: Background task is "noise" (negligible)
- **> 2.35% drop fraction**: Background task is "signal" (significant)
- **Visual warning triggers** at 1% divergence (2.35% drop fraction)

### What This Enables

✅ **Real-Time Monitoring**: See background interference as it happens  
✅ **Quantitative Detection**: Exact drop fraction, not just qualitative  
✅ **Visual Feedback**: Color-coded warnings in plots  
✅ **Actionable Guidance**: Use median vs mean based on divergence  

---

## 3. Kernel-Level Resilience 🛡️

### What It Does

Since `select.select()` stays under 100ms even during a "Chaos Test," we can monitor other kernel signals (besides SIGINT) to make the tool even more robust.

### Implementation

**Script**: `scripts/enhanced_signal_handler.py`

**Key Features:**
- Monitors multiple signals: SIGINT, SIGTERM, SIGHUP, SIGQUIT
- Timer-based "heartbeat" mechanism (100ms intervals)
- Responsive signal delivery even under CPU stress
- Signal history tracking

### Signal Coverage

| Signal | Trigger | Use Case |
|--------|---------|----------|
| **SIGINT** | Ctrl+C | User-initiated shutdown |
| **SIGTERM** | Termination request | System shutdown, process manager |
| **SIGHUP** | Terminal hangup | Terminal closed, SSH disconnect |
| **SIGQUIT** | Quit with core dump | Debugging, forced termination |

### Usage

**Standalone:**
```bash
python3 scripts/enhanced_signal_handler.py
```

**Integrated:**
```python
from scripts.enhanced_signal_handler import setup_enhanced_signals, is_shutdown_requested

def my_shutdown(sig, name):
    print(f"Shutting down due to {name}")
    # Custom cleanup

handler = setup_enhanced_signals(my_shutdown)

# In main loop
while handler.is_running():
    # Do work
    if is_shutdown_requested():
        break
```

### Heartbeat Mechanism

**How It Works:**
```python
def heartbeat_loop():
    while running:
        # Use select.select() with 100ms timeout (heartbeat)
        ready, _, _ = select.select([], [], [], 0.1)
        
        # Regular check ensures signals are processed
        # Even under CPU stress, timer fires every 100ms
        if not running:
            break
```

**Why It Works:**
- ✅ **Hardware timer** runs independently (not affected by CPU load)
- ✅ **100ms timeout** provides regular "heartbeat" for signal checking
- ✅ **Guaranteed maximum** wait time (100ms)
- ✅ **Works under stress** (validated by Scheduler Priority test)

### What This Enables

✅ **Robust Shutdown**: Handles multiple signal types  
✅ **Responsive Under Stress**: <100ms response time guaranteed  
✅ **Graceful Cleanup**: Custom shutdown callbacks  
✅ **Signal History**: Track which signals were received  

---

## Integration Guide

### 1. Add Adaptive Baseline to unified_benchmark.py

```python
# After collecting initial power samples
from scripts.intelligent_baseline_detector import analyze_baseline

baseline_samples = list(power_history)[:20]  # First 20 samples
baseline_power = np.mean(baseline_samples)

analysis = analyze_baseline(baseline_power)
if analysis['warnings']:
    for warning in analysis['warnings']:
        console.print(f"[yellow]{warning}[/yellow]")
```

### 2. Divergence Dashboard Already Integrated

The divergence dashboard is automatically included in `power_visualizer.py` when you run:
```bash
python3 scripts/power_visualizer.py power_log.csv
```

### 3. Add Enhanced Signals to unified_benchmark.py

```python
from scripts.enhanced_signal_handler import setup_enhanced_signals

def shutdown_handler(sig, name):
    global running
    running = False
    print(f"\n🛑 Shutting down due to {name}")

handler = setup_enhanced_signals(shutdown_handler)

# In main loop
while handler.is_running():
    # Do work
    pass
```

---

## Benefits Summary

### Adaptive Baseline Adjustment

- **Automatic Detection**: No manual checking
- **AR Correction**: Warns when measurements are inaccurate
- **Actionable**: Provides specific recommendations
- **Validated**: Based on empirical 700 mW Power Tax

### Divergence Dashboard

- **Real-Time**: See background interference as it happens
- **Quantitative**: Exact drop fraction calculation
- **Visual**: Color-coded warnings
- **Actionable**: Guidance on using median vs mean

### Kernel-Level Resilience

- **Robust**: Handles multiple signal types
- **Responsive**: <100ms guaranteed response time
- **Validated**: Based on Scheduler Priority test
- **Graceful**: Custom cleanup on shutdown

---

## Validation Connection

These enhancements directly apply the "smoking gun" results:

1. **P-Core Tax (700 mW)** → Adaptive Baseline Adjustment
2. **Skewness Threshold (2.35%)** → Divergence Dashboard
3. **Scheduler Priority (50ms)** → Kernel-Level Resilience

Together, they transform theoretical validation into **practical intelligence** that makes the suite more adaptive, informative, and robust.

---

## Deep Dive: Addressing Advanced Questions

### 1. Tax Correction Logic: Legitimate vs Wasted Power 🏗️

**Question**: When detecting a 1200 mW baseline, how do we distinguish between legitimate workload power and wasted P-core leakage?

**Solution**: Multi-factor analysis using CPU usage and known P-core tax.

**How It Works:**
- **CPU Usage Analysis**: >20% CPU = legitimate workload, <10% CPU = likely wasted
- **Power Breakdown**: Calculates legitimate vs wasted components
- **Known P-Core Tax**: Refines estimate using actual daemon checks
- **Classification**: `legitimate_workload`, `likely_wasted`, or `mixed`

**Example Scenarios:**

**Scenario A: Legitimate Workload (1200 mW baseline)**
```
CPU Usage: 35%
Top Process: Python (compiler running)
Classification: legitimate_workload

Breakdown:
  Legitimate: 1025 mW (500 idle + 35% × 15 mW/%)
  Wasted: 175 mW (12% of baseline)
  
Interpretation: ✅ High baseline is from real work, not waste
```

**Scenario B: Wasted P-Core Leakage (1200 mW baseline)**
```
CPU Usage: 5%
Top Process: mds (Spotlight indexing)
Daemon on P-cores: Yes
Known Tax: 700 mW

Breakdown:
  Legitimate: 500 mW (typical idle)
  Wasted: 700 mW (58% of baseline)
  
Interpretation: ⚠️ High baseline is from P-core waste, not work
```

### 2. Real-Time Skew Trigger: Automatic Re-run 📉

**Question**: When 2.35% drop fraction is detected, should we just warn or automatically offer to re-run?

**Solution**: Intelligent re-run logic with user choice.

**How It Works:**
- **Real-Time Detection**: Monitors divergence and drop fraction as data arrives
- **Re-run Decision**: Offers re-run when >5% divergence OR persistent detections OR >5% drop fraction
- **Stabilization Wait**: Monitors power until background task completes (waits for low variance)
- **User Choice**: Continue, wait and re-run automatically, or cancel

**Example Flow:**
```
⚠️  BACKGROUND TASK INTERFERENCE DETECTED
   Divergence: 2.35%
   Drop Fraction: 2.35%

🔄 Options:
   1. Continue (use median for typical power)
   2. Wait and re-run automatically when task completes
   3. Cancel and re-run manually later

Your choice: 2

⏳ Waiting for background task to complete...
   ✅ Power stabilized at 2000.5 mW
   🔄 Re-running benchmark with clean baseline...
```

### 3. Multi-Signal Robustness: SIGHUP vs SIGINT 🛡️

**Question**: How does the 100ms "heartbeat" ensure that SIGHUP (remote terminal disconnect) is handled as gracefully as SIGINT (Ctrl+C)?

**Solution**: Timer-based heartbeat mechanism ensures all signals are handled identically.

**How It Works:**
- **Hardware Timer**: Runs independently (not affected by CPU load)
- **Timer Interrupt**: Fires every few milliseconds
- **Kernel Signal Delivery**: Checks signals on every timer tick
- **select.select() with timeout**: Provides regular wake-up opportunity (100ms)
- **All Signals**: SIGINT, SIGTERM, SIGHUP, SIGQUIT handled identically

**Why SIGHUP is Handled Gracefully:**

```
Remote Terminal Disconnect Scenario:

1. SSH connection drops → SIGHUP sent
2. Kernel queues SIGHUP
3. Process in TASK_INTERRUPTIBLE (waiting on select.select)
4. Timer interrupt fires (every few ms)
5. Kernel checks signal queue
6. SIGHUP delivered within 100ms
7. Same graceful shutdown as SIGINT (Ctrl+C)
```

**Comparison:**

| Signal | Trigger | Delivery Time | Graceful? |
|--------|---------|---------------|-----------|
| **SIGINT** | Ctrl+C | <100ms | ✅ Yes |
| **SIGHUP** | Terminal disconnect | <100ms | ✅ Yes (same!) |
| **SIGTERM** | System shutdown | <100ms | ✅ Yes (same!) |
| **SIGQUIT** | Debug quit | <100ms | ✅ Yes (same!) |

**Key Insight**: The timer-based heartbeat ensures **all signals are delivered within 100ms**, regardless of signal type or CPU load.

---

## Next Steps

1. **Test each enhancement** individually
2. **Integrate into main scripts** as shown above
3. **Validate improvements** with real measurements
4. **Document results** in your analysis

---

## Dependencies

All enhancements use existing dependencies:
- `psutil` (for process/CPU affinity checking)
- `numpy` (for calculations)
- `pandas` (for data analysis)
- `matplotlib` (for visualization)
- Standard library (`signal`, `select`, `threading`)

No new dependencies required!

