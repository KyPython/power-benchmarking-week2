# Performance Analysis: PyTorch vs CoreML Neural Engine

## Benchmark Results Summary

### Test Configuration
- **Model**: MobileNetV2
- **Input**: (1, 3, 224, 224) random tensor
- **Warmup**: 10 inferences
- **Test**: 100 inferences (PyTorch) / 500 inferences (CoreML)

---

## Latency Comparison

### PyTorch (CPU/GPU) - `scripts/benchmark.py`
```
Total Time:        2.8007 seconds
Inferences:        100
Average Latency:   28.01 ms per inference
Throughput:        35.71 inferences/sec
```

### CoreML (Neural Engine) - `scripts/benchmark_power.py`
```
Total Time:        0.24 seconds
Inferences:        500
Average Latency:   0.49 ms per inference
Throughput:        ~2,040 inferences/sec (estimated)
```

---

## Performance Metrics

### Speedup Factor
```
Latency Improvement:  28.01 ms / 0.49 ms = 57.2x faster
Throughput Improvement: ~2,040 / 35.71 = 57.1x more inferences/sec
```

**The Neural Engine is approximately 57x faster than PyTorch on CPU/GPU!**

### Time Savings
For 100 inferences:
- **PyTorch**: 2.80 seconds
- **CoreML**: 0.049 seconds (estimated)
- **Time saved**: 2.75 seconds (98.2% reduction)

---

## Why the Massive Speedup?

1. **Hardware Acceleration**: Neural Engine is purpose-built for ML inference
2. **Optimized Execution**: CoreML compiles to highly optimized ANE instructions
3. **Lower Overhead**: Direct hardware access vs. framework layers
4. **Parallel Processing**: ANE can process operations in parallel more efficiently

---

## Power Efficiency Analysis

The latency improvements translate directly to energy efficiency. To measure actual power consumption and calculate energy per inference, use the unified benchmark:

### Measuring Power Consumption

**Run unified benchmark with power monitoring:**
```bash
sudo python3 scripts/unified_benchmark.py --test 30
```

**Calculate energy efficiency using analyze_power_data.py:**
```bash
python3 scripts/analyze_power_data.py power_log.csv
```

### Energy per Inference Formula

```
Energy (J) = Power (W) × Time (s)
Energy per Inference = ANE Power (W) × Latency (s)
```

### Expected Energy Efficiency

Based on the 57x latency improvement, even if ANE power is similar to CPU power, the energy per inference is dramatically lower:

- **Faster Execution**: 57x faster = 57x less time
- **Energy Savings**: Lower power × shorter time = significantly more efficient
- **Combined Effect**: The Neural Engine provides both speed and energy efficiency advantages

---

## Preliminary Predictions

Based on typical M2 behavior:

| Metric | PyTorch (CPU) | CoreML (ANE) | Improvement |
|--------|---------------|--------------|-------------|
| Latency | 28.01 ms | 0.49 ms | **57x faster** |
| Power (est.) | ~2000-4000 mW | ~500-1500 mW | **2-4x lower** |
| Energy/inf (est.) | ~56-112 mJ | ~0.25-0.74 mJ | **75-450x more efficient** |

*Note: Actual power values will be measured with powermetrics*

---

## Conclusion

The conversion from PyTorch to CoreML shows a **dramatic 57x latency improvement**. When combined with power measurements, we expect to see even greater energy efficiency gains due to:

1. **Lower power consumption** (ANE vs CPU)
2. **Faster execution** (less time = less total energy)
3. **Optimized hardware** (purpose-built for ML)

**Status**: Ready for power measurements! 🚀

---

## The Performance Evolution: Documented Formulas Change Interpretation

**Question**: Now that you've replaced "Pending" tasks with actual formulas, how does having the math documented right next to the benchmark data change how we interpret a "10% improvement" in the future?

**Answer**: Documented formulas provide **contextual meaning** to improvements, transforming raw numbers into actionable insights about efficiency, energy savings, and user experience impact.

### Before: Raw Numbers Without Context

**Without Formulas**:
```
10% improvement in latency
→ Is this good? Bad? Significant?
→ What does it mean for energy?
→ How does it compare to the 57x improvement?
→ Unclear significance
```

**Problem**: Without formulas, improvements are just numbers. There's no way to understand:
- **Energy impact**: Does 10% latency improvement = 10% energy savings?
- **Statistical significance**: Is 10% within measurement error?
- **Relative performance**: Is 10% good compared to baseline?

### After: Formulas Provide Contextual Meaning

**With Formulas Documented**:

```
Energy per Inference = Power (W) × Latency (s)

10% latency improvement:
- Original: 0.49 ms latency
- Improved: 0.441 ms latency (10% faster)
- If power stays same: 10% less energy per inference
- If power increases: May not save energy (need to calculate)

Energy Impact Calculation:
- Original: 1500 mW × 0.00049s = 0.735 mJ
- Improved: 1500 mW × 0.000441s = 0.662 mJ
- Energy savings: 0.073 mJ (10% reduction) ✅

But if power increases:
- Improved: 1650 mW × 0.000441s = 0.728 mJ
- Energy savings: 0.007 mJ (1% reduction) ⚠️
```

### How Formulas Change Interpretation

#### 1. **Energy-Aware Analysis**

**Formula**: `Energy = Power × Time`

**10% latency improvement** means different things depending on power:
- **Power constant**: 10% latency improvement = 10% energy savings ✅
- **Power increases**: 10% latency improvement may not save energy ⚠️
- **Power decreases**: 10% latency + lower power = even better ✅

**Action**: Use formula to calculate actual energy impact, not just assume latency = energy.

#### 2. **Statistical Significance**

**Formula**: `Speedup Factor = Old_Latency / New_Latency`

**10% improvement** in context of 57x baseline:
- **Baseline**: 57x improvement (PyTorch → CoreML)
- **10% on top**: 57x × 1.1 = 62.7x improvement
- **Significance**: Small relative improvement (10%) but huge absolute impact (62.7x)

**Action**: Compare improvement to baseline magnitude, not just percentage.

#### 3. **Relative Performance Context**

**Formula**: `Efficiency Ratio = PyTorch_Energy / CoreML_Energy`

**10% improvement** on CoreML:
- **Original CoreML**: 75-450x more efficient than PyTorch
- **10% improved CoreML**: 82.5-495x more efficient
- **Context**: Even small improvements are significant on an already efficient system

**Action**: Understand improvement in context of baseline efficiency.

### Example: Interpreting a Future 10% Improvement

**Scenario**: Future optimization reduces ANE latency from 0.49ms to 0.441ms (10% improvement)

**Without Formulas**:
- "10% improvement" → Unclear significance

**With Formulas** (documented in PERFORMANCE.md):
- **Energy Impact**: `Energy = Power × Time`
  - Original: 1500 mW × 0.00049s = 0.735 mJ
  - Improved: 1500 mW × 0.000441s = 0.662 mJ
  - Savings: 0.073 mJ (10% reduction) ✅
  
- **Relative Context**: `Speedup Factor = Old / New`
  - Baseline: 57x vs PyTorch
  - Improved: 62.7x vs PyTorch
  - Significance: Small percentage, but maintains huge absolute advantage
  
- **Efficiency Context**: `Efficiency Ratio = PyTorch_Energy / CoreML_Energy`
  - Original: 75-450x more efficient
  - Improved: 82.5-495x more efficient
  - Impact: Continues to widen efficiency gap

**Result**: Formulas transform "10% improvement" into:
- ✅ **10% energy savings** (if power constant)
- ✅ **62.7x speedup** (absolute improvement)
- ✅ **82.5-495x efficiency** (continues dominance)

### The Value of Documented Formulas

**Before**: Improvements are just numbers
**After**: Improvements have contextual meaning

**Benefits**:
1. **Energy-Aware**: Can calculate actual energy impact
2. **Statistically Significant**: Can compare to baseline magnitude
3. **Contextually Relevant**: Can understand relative performance
4. **Actionable**: Can make informed decisions about optimizations

**Conclusion**: Documented formulas transform performance numbers from raw data into **actionable insights** that guide optimization decisions and provide meaningful context for improvements.

---
