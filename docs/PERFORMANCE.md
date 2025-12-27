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

## Power Efficiency Analysis (Pending)

Once we run `unified_benchmark.py` with powermetrics, we'll be able to calculate:

### Energy per Inference
```
Energy (J) = Power (W) × Time (s)
Energy per Inference = ANE Power (W) × Latency (s)
```

### Power Efficiency Comparison
```
PyTorch Energy per Inference = CPU_Power × 0.02801s
CoreML Energy per Inference = ANE_Power × 0.00049s

Efficiency Ratio = PyTorch_Energy / CoreML_Energy
```

### Expected Findings
- **Lower Power**: ANE typically runs at lower power than CPU/GPU
- **Faster Execution**: Even if power is similar, shorter time = less total energy
- **Combined Effect**: Lower power × shorter time = significantly more efficient

---

## Next Steps

1. **Run Unified Benchmark**: 
   ```bash
   sudo python3 scripts/unified_benchmark.py --test 30
   ```

2. **Collect Power Data**:
   - ANE Power (mW) during CoreML inference
   - Compare to CPU power during PyTorch inference

3. **Calculate Energy Efficiency**:
   - Energy per inference for both
   - Total energy for 100 inferences
   - Efficiency ratio

4. **Generate Report**:
   - Latency comparison ✅ (done)
   - Power comparison (pending)
   - Energy efficiency (pending)

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

