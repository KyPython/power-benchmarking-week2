# Validation & Testing

**Single Responsibility: Validation scripts and test procedures for verifying documented claims.**

## Overview

This document describes validation scripts that test the technical claims made in `TECHNICAL_DEEP_DIVE.md` and `ARCHITECTURE.md`. These scripts provide empirical evidence for:

1. Non-blocking I/O performance claims
2. Power attribution accuracy
3. Statistical interpretation correctness

## Validation Scripts

### 1. I/O Performance Stress Test

**Script**: `scripts/validate_io_performance.py`

**Purpose**: Validates the <100ms response time claim for `select.select()` during system stalls and shutdown signals.

**What it tests**:
- `select.select()` response time under normal conditions
- Response time during CPU stress (system stall)
- Shutdown signal response time (Ctrl+C handling)

**Usage**:
```bash
# Normal conditions
python3 scripts/validate_io_performance.py --duration 10

# With CPU stress (chaos test)
python3 scripts/validate_io_performance.py --duration 10 --stall
```

**Expected Results**:
- 95th percentile response time < 100ms
- Shutdown response time < 100ms
- Performance maintained even under CPU stress

**Validation Criteria**:
- ✅ 95th percentile < 100ms: Claim validated
- ⚠️ 95th percentile > 100ms: Claim not met

---

### 2. Attribution Accuracy Check

**Script**: `scripts/validate_attribution.py`

**Purpose**: Compares Process-level tracking against a known "power virus" to measure unattributed system power.

**What it tests**:
- Baseline power measurement (idle system)
- Power during CPU stress (power virus)
- Attribution ratio (process power vs total power)
- Effectiveness of baseline subtraction

**Usage**:
```bash
# Single core stress
sudo python3 scripts/validate_attribution.py --cores 1

# Multi-core stress
sudo python3 scripts/validate_attribution.py --cores 4 --virus-duration 60
```

**Expected Results**:
- Attribution ratio > 50% indicates good process tracking
- Lower ratios indicate significant system overhead
- Baseline subtraction improves accuracy

**Validation Criteria**:
- ✅ Attribution > 70%: Good process tracking
- ℹ️ Attribution 50-70%: Moderate, some overhead
- ⚠️ Attribution < 50%: Significant system overhead

**Interpretation**:
- **High attribution**: Process power is dominant, tracking is accurate
- **Low attribution**: System overhead is significant, baseline subtraction recommended

---

### 3. Statistical Interpretation Validation

**Script**: `scripts/validate_statistics.py`

**Purpose**: Tests mean/median divergence with different workload patterns to validate statistical interpretation.

**What it tests**:
- Constant workload (Normal distribution) - Video rendering simulation
- Burst workload (Right-skewed) - Web browsing simulation
- Mean/Median divergence calculation
- Workload type identification

**Usage**:
```bash
# Generate and analyze both workloads
python3 scripts/validate_statistics.py --duration 60

# Analyze existing CSV files
python3 scripts/validate_statistics.py --analyze-only
```

**Expected Results**:

**Constant Workload (Video Render)**:
- Mean ≈ Median (divergence < 5%)
- Normal distribution
- Predictable power consumption

**Burst Workload (Web Browsing)**:
- Mean >> Median (divergence > 20%)
- Right-skewed distribution
- High-power spikes identified

**Validation Criteria**:
- ✅ Constant: Divergence < 5% = Normal distribution
- ✅ Burst: Divergence > 20% and Mean > Median = Right-skewed
- ⚠️ If criteria not met: Statistical interpretation needs review

---

## Running All Validations

### Quick Validation Suite

```bash
# 1. I/O Performance (no sudo needed)
python3 scripts/validate_io_performance.py --duration 10 --stall

# 2. Attribution Accuracy (requires sudo)
sudo python3 scripts/validate_attribution.py --cores 2

# 3. Statistical Interpretation (no sudo needed)
python3 scripts/validate_statistics.py --duration 60
```

### Full Validation Suite

```bash
# Comprehensive testing
python3 scripts/validate_io_performance.py --duration 30 --stall
sudo python3 scripts/validate_attribution.py --cores 4 --virus-duration 60
python3 scripts/validate_statistics.py --duration 120
```

## Interpreting Results

### I/O Performance

**Good Results**:
- Response times consistently < 100ms
- No degradation under CPU stress
- Immediate shutdown response

**Issues**:
- Response times > 100ms indicate blocking behavior
- Degradation under stress suggests resource contention

### Attribution Accuracy

**Good Results**:
- High attribution ratio (>70%)
- Clear power delta during stress
- Baseline subtraction reduces unattributed power

**Issues**:
- Low attribution (<50%) indicates significant system overhead
- May need improved process tracking or baseline subtraction

### Statistical Interpretation

**Good Results**:
- Constant workload: Low divergence (<5%)
- Burst workload: High divergence (>20%) with Mean > Median
- Correct workload type identification

**Issues**:
- Incorrect distribution identification
- Divergence doesn't match expected pattern

## Integration with Documentation

These validation scripts directly test claims made in:

- **TECHNICAL_DEEP_DIVE.md**: Non-blocking I/O, power attribution, statistics
- **ARCHITECTURE.md**: Design decisions and implementation details

## Dependencies

Validation scripts require:
- `numpy` (for statistical distributions)
- `pandas` (for CSV analysis)
- `psutil` (for process tracking)
- `sudo` access (for attribution test)

All dependencies are in `requirements.txt`.

## Continuous Validation

These scripts can be integrated into:
- Pre-commit hooks
- CI/CD pipelines
- Regular testing schedules
- Documentation updates

---

### 4. P-Core Tax Calculation

**Script**: `scripts/validate_pcore_tax.py`

**Purpose**: Measures the "Power Tax" - the specific increase in baseline power when background daemons are forced to share P-cores with the main workload.

**What it tests**:
- Baseline power with daemons on E-cores (default)
- Forcing daemons to P-cores using `taskpolicy`
- Baseline power with daemons on P-cores (forced)
- Power Tax calculation (absolute and percentage)

**Usage**:
```bash
# Test with mds daemon (default)
sudo python3 scripts/validate_pcore_tax.py mds --duration 10

# Test with different daemon
sudo python3 scripts/validate_pcore_tax.py backupd --duration 15

# Custom P-core IDs
sudo python3 scripts/validate_pcore_tax.py cloudd --p-cores 4 5 6 7
```

**Expected Results**:
- Power Tax: 200-700 mW typical (10-30% increase)
- Higher tax indicates inefficient P-core sharing
- Validates AR reduction when baseline uses P-cores

**Validation Criteria**:
- ✅ Tax < 10%: Good E-core isolation, minimal impact
- ⚠️ Tax 10-20%: Moderate impact, some P-core contention
- ⚠️ Tax > 20%: High impact, significant P-core waste

**Interpretation**:
- **Low tax**: E-cores are effectively handling baseline
- **High tax**: P-core sharing is inefficient, validates AR reduction
- **Use this**: To experimentally verify P-core contention effects

---

### 5. Skewness Magnitude Math Validation

**Script**: `scripts/validate_skewness_threshold.py`

**Purpose**: Tests the formula `Mean = (L × f) + (H × (1-f))` and determines the "Detection Threshold" - the exact drop fraction where background tasks become statistically significant.

**What it tests**:
- Formula accuracy across different drop fractions (f)
- Detection threshold for various divergence levels (1%, 5%, 10%, 20%)
- Mean/median divergence vs drop fraction relationship
- Formula error analysis

**Usage**:
```bash
# Default test (1500 mW low, 2100 mW high, 2000 mW median)
python3 scripts/validate_skewness_threshold.py

# Custom power values
python3 scripts/validate_skewness_threshold.py --low-power 1400 --high-power 2200 --median-power 2000

# Custom detection threshold
python3 scripts/validate_skewness_threshold.py --threshold 0.05  # 5% divergence
```

**Expected Results**:
- Formula accuracy: <0.1% error typically
- Detection threshold: 2-10% drop fraction for 1% divergence
- Visual plot showing threshold analysis

**Validation Criteria**:
- ✅ Formula error < 1%: Formula is accurate
- ✅ Threshold found: Detection point identified
- ⚠️ High error: Formula may need adjustment

**Interpretation**:
- **Low threshold (<5%)**: Very sensitive, catches small background tasks
- **Moderate threshold (5-15%)**: Typical sensitivity for background detection
- **High threshold (>15%)**: Less sensitive, may miss subtle interference

---

### 6. Scheduler Priority Deep Dive

**Script**: `scripts/validate_scheduler_priority.py`

**Purpose**: Examines why processes waiting on Hardware Timers get priority for SIGINT delivery over processes waiting on Pipe I/O under CPU stress.

**What it tests**:
- Signal response time for timer-based waits (select.select with timeout)
- Signal response time for pipe-based waits (select.select on pipe)
- Performance comparison under normal and CPU stress conditions
- 95th/99th percentile analysis

**Usage**:
```bash
# Normal conditions
python3 scripts/validate_scheduler_priority.py --tests 100

# Under CPU stress (chaos test)
python3 scripts/validate_scheduler_priority.py --tests 100 --stress
```

**Expected Results**:
- Timer waits: <100ms response time (meets guarantee)
- Pipe waits: Variable response time (no guarantee)
- Timer waits faster on average, especially under stress

**Validation Criteria**:
- ✅ Timer P95 < 100ms: Timer priority confirmed
- ✅ Timer faster than pipe: Scheduler prioritization validated
- ⚠️ No difference: May need longer test or different conditions

**Interpretation**:
- **Timer priority**: Hardware timer provides predictable, fast signal delivery
- **Pipe dependency**: Pipe waits depend on external events (less predictable)
- **Use timer-based**: For responsive signal handling in production code

---

## Running All Validations

### Quick Validation Suite

```bash
# 1. I/O Performance (no sudo needed)
python3 scripts/validate_io_performance.py --duration 10 --stall

# 2. Attribution Accuracy (requires sudo)
sudo python3 scripts/validate_attribution.py --cores 2

# 3. Statistical Interpretation (no sudo needed)
python3 scripts/validate_statistics.py --duration 60

# 4. P-Core Tax (requires sudo)
sudo python3 scripts/validate_pcore_tax.py mds --duration 10

# 5. Skewness Threshold (no sudo needed)
python3 scripts/validate_skewness_threshold.py

# 6. Scheduler Priority (no sudo needed)
python3 scripts/validate_scheduler_priority.py --tests 100
```

### Full Validation Suite

```bash
# Comprehensive testing
python3 scripts/validate_io_performance.py --duration 30 --stall
sudo python3 scripts/validate_attribution.py --cores 4 --virus-duration 60
python3 scripts/validate_statistics.py --duration 120
sudo python3 scripts/validate_pcore_tax.py mds --duration 15
python3 scripts/validate_skewness_threshold.py --threshold 0.01
python3 scripts/validate_scheduler_priority.py --tests 200 --stress
```

## Interpreting Results

### I/O Performance

**Good Results**:
- Response times consistently < 100ms
- No degradation under CPU stress
- Immediate shutdown response

**Issues**:
- Response times > 100ms indicate blocking behavior
- Degradation under stress suggests resource contention

### Attribution Accuracy

**Good Results**:
- High attribution ratio (>70%)
- Clear power delta during stress
- Baseline subtraction reduces unattributed power

**Issues**:
- Low attribution (<50%) indicates significant system overhead
- May need improved process tracking or baseline subtraction

### Statistical Interpretation

**Good Results**:
- Constant workload: Low divergence (<5%)
- Burst workload: High divergence (>20%) with Mean > Median
- Correct workload type identification

**Issues**:
- Incorrect distribution identification
- Divergence doesn't match expected pattern

### P-Core Tax

**Good Results**:
- Low tax (<10%): Good E-core isolation
- Validates AR reduction when forcing to P-cores
- Confirms efficiency gap calculations

**Issues**:
- High tax (>20%): Significant P-core waste
- May indicate inefficient scheduling

### Skewness Threshold

**Good Results**:
- Formula accuracy <1% error
- Detection threshold identified
- Clear relationship between drop fraction and divergence

**Issues**:
- High formula error: May need adjustment
- Threshold not found: Check parameters

### Scheduler Priority

**Good Results**:
- Timer waits faster than pipe waits
- Timer P95 < 100ms (meets guarantee)
- Performance maintained under stress

**Issues**:
- No difference: May need longer test
- Timer > 100ms: Unexpected behavior

## Integration with Documentation

These validation scripts directly test claims made in:

- **TECHNICAL_DEEP_DIVE.md**: 
  - P-Core Contention Test (Section: Architecture Efficiency Test)
  - Skewness Magnitude Math (Section: Skewness Diagnostic)
  - Scheduler Priority (Section: Kernel Wake-up Logic)
  - Non-blocking I/O, power attribution, statistics
- **ARCHITECTURE.md**: Design decisions and implementation details

## Dependencies

Validation scripts require:
- `numpy` (for statistical distributions and calculations)
- `pandas` (for CSV analysis)
- `psutil` (for process tracking)
- `matplotlib` (for visualization)
- `sudo` access (for attribution and P-core tax tests)

All dependencies are in `requirements.txt`.

## Continuous Validation

These scripts can be integrated into:
- Pre-commit hooks
- CI/CD pipelines
- Regular testing schedules
- Documentation updates

## Notes

- Attribution and P-Core Tax tests require `sudo` (powermetrics access)
- I/O, statistics, skewness, and scheduler tests run without `sudo`
- Generated CSV files can be analyzed with `power_visualizer.py`
- Results may vary based on system load and hardware
- P-Core Tax test may require root privileges for `taskpolicy`

