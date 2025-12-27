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

## Notes

- Attribution test requires `sudo` (powermetrics access)
- I/O and statistics tests run without `sudo`
- Generated CSV files can be analyzed with `power_visualizer.py`
- Results may vary based on system load and hardware

