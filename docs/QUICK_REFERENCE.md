# Quick Reference Guide

## 🎯 Common Tasks

### Measure Power During Activity

```bash
# Log power for 1 hour during gaming
sudo python3 scripts/power_logger.py --duration 3600 --output gaming.csv

# Log power during video editing (until Ctrl+C)
sudo python3 scripts/power_logger.py --output video_editing.csv
```

### Visualize Power Data

```bash
# Create graph from CSV
python3 scripts/power_visualizer.py gaming.csv

# View graph and save
python3 scripts/power_visualizer.py gaming.csv --show
```

### Compare Apps

```bash
# Quick comparison (10 seconds each)
sudo python3 scripts/app_power_analyzer.py Safari Chrome

# Longer comparison with output
sudo python3 scripts/app_power_analyzer.py Safari Chrome Firefox --duration 30 --output browsers.csv
```

### Analyze Energy Efficiency

```bash
# From measured values
python3 scripts/analyze_power_data.py 800 3000

# From powermetrics file
python3 scripts/analyze_power_data.py --file powermetrics.txt
```

## 📊 Typical Workflows

### Workflow 1: Quick App Comparison
```bash
# 1. Compare two browsers
sudo python3 scripts/app_power_analyzer.py Safari Chrome --duration 15 --output browsers.csv

# 2. View results
cat browsers.csv
```

### Workflow 2: Extended Power Monitoring
```bash
# 1. Start logging (runs in background)
sudo python3 scripts/power_logger.py --duration 7200 --output session.csv &

# 2. Do your work
# ... your activity ...

# 3. Visualize results
python3 scripts/power_visualizer.py session.csv
```

### Workflow 3: Complete Benchmark Session
```bash
# 1. Test components
python3 scripts/test_components.py

# 2. Run benchmark with power monitoring
sudo python3 scripts/unified_benchmark.py --test 30

# 3. Analyze results
python3 scripts/analyze_power_data.py <ane_power> <cpu_power>
```

## 🔍 Power Metrics Explained

- **ANE Power**: Neural Engine power consumption (mW)
- **CPU Power**: CPU package power (mW)
- **GPU Power**: GPU power consumption (mW)
- **Total Power**: Combined package power (mW)
- **Energy (mJ)**: Cumulative energy consumption

## 📈 Interpreting Results

### Good Signs
- ✅ Consistent power readings
- ✅ ANE power increases during ML inference
- ✅ Reasonable power values (ANE: 0-2000 mW typical)

### Warning Signs
- ⚠️ No ANE power values (Neural Engine idle)
- ⚠️ Very high power (>5000 mW sustained)
- ⚠️ Erratic readings (check sampling interval)

## 💡 Tips

1. **Sampling Interval**: Lower = more data but more overhead
   - 500ms: Good balance
   - 1000ms: Lower overhead
   - 100ms: High detail (more CPU usage)

2. **Duration**: Longer = better averages
   - 10s: Quick test
   - 60s: Good average
   - 300s+: Very accurate

3. **CSV Files**: Can get large
   - 1 hour @ 500ms = ~7200 rows
   - Monitor disk space for long sessions

## 🎯 Example Commands

```bash
# Quick power test (10 seconds)
sudo python3 scripts/power_logger.py --duration 10 --output test.csv

# Compare three video players
sudo python3 scripts/app_power_analyzer.py VLC QuickTime --duration 20

# Full benchmark with visualization
sudo python3 scripts/unified_benchmark.py --test 60
python3 scripts/power_visualizer.py power_log.csv
```

