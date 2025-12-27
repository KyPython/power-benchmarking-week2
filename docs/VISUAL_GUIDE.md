# Visual Guide: What You'll See

This guide shows you exactly what to expect when running the unified benchmark with all its visual features.

## 🎨 Enhanced Output Features

### 1. Startup Sequence

When you run `sudo python3 scripts/unified_benchmark.py --test 30`, you'll see:

```
======================================================================
🚀 Unified Benchmark: CoreML + Power Monitoring + Arduino
🧪 TEST MODE: Running for 30 seconds
======================================================================

✅ Model loaded successfully
✅ Using input name: 'x_1'
✅ Input tensor prepared: (1, 3, 224, 224)
✅ Warmup complete

🔌 Searching for Arduino...
✅ Found Arduino at: /dev/cu.usbmodem14101

⚡ Starting power monitoring...
✅ powermetrics started (sampling every 500ms)

📡 Starting serial communication...
✅ Serial connection established: /dev/cu.usbmodem14101 @ 115200 baud

======================================================================
🎯 Starting test benchmark (30s) - Press Ctrl+C to stop early
======================================================================
```

### 2. Real-Time Statistics Display

During the benchmark, you'll see a live-updating panel (if `rich` library is installed):

```
┌─────────────────────────────────────────────────────────────┐
│ ⚡ Real-Time Power Monitoring                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ████████████████████████████████░░░░░░░░░░ 1234.5 mW        │
│                                                              │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│ ┃ 📊 Real-Time Statistics                                 ┃  │
│ ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫  │
│ ┃ Metric          │ Value                                 ┃  │
│ ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫  │
│ ┃ Current         │ 1234.5 mW                            ┃  │
│ ┃ Min             │ 856.2 mW                              ┃  │
│ ┃ Max             │ 1456.8 mW                             ┃  │
│ ┃ Mean            │ 1123.4 mW                             ┃  │
│ ┃ Median          │ 1105.6 mW                             ┃  │
│ ┃ Samples         │ 45                                    ┃  │
│ ┃ Inferences      │ 12,345                                ┃  │
│ ┃ Throughput      │ 2057.5 inf/sec                        ┃  │
│ ┃ Elapsed         │ 6.0s                                  ┃  │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
└─────────────────────────────────────────────────────────────┘
```

**Color Coding:**
- 🟢 **Green bar**: Low power (< 50% of range)
- 🟡 **Yellow bar**: Medium power (50-80% of range)
- 🔴 **Red bar**: High power (> 80% of range)

### 3. Arduino Serial Monitor Output

If Arduino is connected, you'll see in the Serial Monitor:

```
==================================================
Arduino Power Receiver - Ready
Waiting for ANE_PWR data from Python...
Format: ANE_PWR:[value]\n
==================================================

ANE Power: 1234.50 mW | Packets: 1 | Errors: 0
ANE Power: 1156.23 mW | Packets: 2 | Errors: 0
ANE Power: 1289.45 mW | Packets: 3 | Errors: 0
...
```

**For Serial Plotter:**
Uncomment line 126 in `arduino_power_receiver.ino` to see a live graph:
```cpp
// Serial.println(powerValue);  // Uncomment this
```

### 4. Final Summary

At the end of the benchmark:

```
======================================================================
📊 FINAL SUMMARY
======================================================================
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric          │ Value                                      ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Total Inferences│ 61,500                                     ┃
┃ Elapsed Time    │ 30.00 seconds                              ┃
┃ Average Throughput│ 2050.0 inf/sec                           ┃
┃                 │                                            ┃
┃ Power Samples   │ 60                                         ┃
┃ Min Power       │ 856.23 mW                                  ┃
┃ Max Power       │ 1456.78 mW                                 ┃
┃ Mean Power      │ 1123.45 mW                                 ┃
┃ Median Power    │ 1105.67 mW                                 ┃
┃ Std Dev         │ 145.23 mW                                  ┃
┃                 │                                            ┃
┃ Arduino Connected│ ✅ Yes                                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
======================================================================

✅ Benchmark complete!
```

## 📊 Understanding the Statistics

### Power Metrics

- **Current**: Latest power reading (updates every 500ms)
- **Min**: Lowest power observed during the run
- **Max**: Highest power observed during the run
- **Mean**: Average power across all samples
- **Median**: Middle value (less affected by outliers)
- **Std Dev**: Standard deviation (shows power variability)

### Performance Metrics

- **Total Inferences**: Number of model predictions completed
- **Elapsed Time**: Total benchmark duration
- **Average Throughput**: Inferences per second
- **Samples**: Number of power readings collected

## 🎯 What to Look For

### Normal Operation

✅ **Power should be:**
- Relatively stable (low std dev)
- Between 500-2000 mW for MobileNetV2 on ANE
- Increasing during inference, decreasing when idle

✅ **Throughput should be:**
- ~2000+ inf/sec for MobileNetV2 on Neural Engine
- Consistent (not dropping over time)

### Potential Issues

⚠️ **If power is:**
- Very high (>3000 mW): System may be throttling
- Very low (<100 mW): ANE may not be active
- Highly variable: Background tasks interfering

⚠️ **If throughput is:**
- Lower than expected: Check if ANE is being used
- Dropping over time: Thermal throttling may be occurring

## 🔧 Troubleshooting

### No Visual Output

If you don't see the rich visual panels:
1. Install rich: `pip install rich`
2. Or use `--no-visual` flag for basic text mode

### Arduino Not Found

If Arduino isn't detected:
1. Check USB connection
2. Verify Arduino IDE Serial Monitor isn't open
3. Check port permissions: `ls -l /dev/cu.usbmodem*`
4. Try different USB port/cable

### No Power Data

If power readings are missing:
1. Verify sudo permissions
2. Check powermetrics is available: `which powermetrics`
3. Try running powermetrics manually: `sudo powermetrics --samplers cpu_power -i 500`

## 📸 Screenshots

For best visualization:
- Use a terminal with good color support (iTerm2, Terminal.app, or VS Code terminal)
- Full-screen terminal recommended for best layout
- Arduino Serial Plotter provides excellent real-time graphs

## 🎓 Next Steps

After running the benchmark:
1. Review the summary statistics
2. Check Arduino Serial Monitor/Plotter for visual graphs
3. Run `power_visualizer.py` on any CSV logs for detailed analysis
4. Compare results across different test durations

