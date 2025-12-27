# Apple Silicon M2 Power Benchmarking Suite

A comprehensive toolkit for monitoring, analyzing, and visualizing power consumption on Apple Silicon Macs, with special focus on Neural Engine (ANE) performance and CoreML optimization.

## 🎯 Overview

This project demonstrates the performance and energy efficiency advantages of Apple's Neural Engine compared to traditional CPU/GPU inference. It includes tools for:

- **Performance Benchmarking**: Compare PyTorch vs CoreML Neural Engine latency
- **Real-time Power Monitoring**: Capture ANE, CPU, and GPU power consumption
- **Automated Data Collection**: Background CSV logging for extended analysis
- **Data Visualization**: Generate graphs and dashboards from power logs
- **Application Comparison**: Compare power efficiency between different applications
- **Hardware Integration**: Stream power data to Arduino for external monitoring

## 🚀 Quick Start

### Prerequisites

```bash
pip install -r requirements.txt
```

### Basic Usage

1. **Convert PyTorch model to CoreML:**
   ```bash
   python3 scripts/convert_model.py
   ```

2. **Run performance benchmarks:**
   ```bash
   # PyTorch baseline (CPU/GPU)
   python3 scripts/benchmark.py
   
   # CoreML Neural Engine
   python3 scripts/benchmark_power.py
   ```

3. **Run unified benchmark with power monitoring:**
   ```bash
   # Test mode (30 seconds) - recommended for first run
   sudo python3 scripts/unified_benchmark.py --test 30
   
   # Full benchmark (runs until Ctrl+C)
   sudo python3 scripts/unified_benchmark.py
   ```

4. **Test all components:**
   ```bash
   python3 scripts/test_full_integration.py
   ```

## 📊 Key Results

### Performance Comparison (MobileNetV2)

| Metric | PyTorch (CPU/GPU) | CoreML (Neural Engine) | Improvement |
|--------|-------------------|------------------------|-------------|
| **Latency** | 28.01 ms | 0.49 ms | **57.2x faster** |
| **Throughput** | 35.71 inf/sec | ~2,040 inf/sec | **57.1x faster** |

The Neural Engine provides a **57x speedup** for MobileNetV2 inference, demonstrating the power of hardware-accelerated ML on Apple Silicon.

## 🛠️ Tools

### Core Benchmarking
- `convert_model.py` - Convert PyTorch models to CoreML format
- `benchmark.py` - PyTorch baseline performance test
- `benchmark_power.py` - CoreML Neural Engine performance test
- `unified_benchmark.py` - Integrated benchmark with real-time power monitoring

### Power Monitoring
- `power_logger.py` - Automated CSV logging of power consumption
- `power_visualizer.py` - Generate graphs from power logs
- `app_power_analyzer.py` - Compare power consumption between applications
- `analyze_power_data.py` - Calculate energy efficiency metrics

### Utilities
- `test_components.py` - Verify individual components
- `test_full_integration.py` - Comprehensive integration test suite

### Advanced Features
- `adversarial_benchmark.py` - Extreme stress test (CPU + SSH disconnect)
- `long_term_profiler.py` - Long-term daemon power profiling
- `ane_gpu_monitor.py` - ANE/GPU monitoring with statistical analysis

## 📈 Example Workflows

### Extended Power Monitoring
```bash
# Log power for 1 hour during a task
sudo python3 scripts/power_logger.py --duration 3600 --output power_log.csv

# Visualize the results
python3 scripts/power_visualizer.py power_log.csv
```

### Application Comparison
```bash
# Compare power consumption between browsers
sudo python3 scripts/app_power_analyzer.py Safari Chrome --duration 30
```

### Energy Efficiency Analysis
```bash
# Analyze power data
python3 scripts/analyze_power_data.py 800 3000
```

## 🔌 Arduino Integration

The suite includes Arduino support for external power monitoring. See `docs/ARDUINO.md` for setup instructions.

**Quick Arduino Setup:**
1. Upload `scripts/arduino_power_receiver.ino` to your Arduino
2. Connect Arduino via USB
3. Open Arduino Serial Monitor (115200 baud)
4. Run the benchmark - power data will stream automatically

## 🎨 Real-Time Visualization

The enhanced `unified_benchmark.py` now includes:
- **Live Statistics Display**: Real-time power metrics, inference throughput, and statistics
- **Visual Power Bar**: Color-coded power level indicator
- **Rich Terminal UI**: Beautiful, human-readable output (requires `rich` library)
- **Summary Report**: Comprehensive statistics at the end of each run

**Features:**
- Current, Min, Max, Mean, Median power values
- Inference count and throughput
- Sample count and elapsed time
- Arduino connection status
- Automatic fallback to basic mode if `rich` is not installed

## 📁 Project Structure

```
power-benchmarking-week2/
├── README.md                 # Main project overview (you are here)
├── requirements.txt          # Python dependencies
│
├── scripts/                  # All executable code (27 scripts)
│   ├── README.md             # Scripts navigation guide ⭐ START HERE
│   │
│   ├── 🚀 Core Workflow (4 scripts)
│   │   ├── convert_model.py      # PyTorch → CoreML conversion
│   │   ├── benchmark.py          # PyTorch baseline
│   │   ├── benchmark_power.py    # CoreML Neural Engine
│   │   └── unified_benchmark.py  # ⭐ Main benchmark (start here)
│   │
│   ├── 📊 Power Monitoring (4 scripts)
│   │   ├── power_logger.py       # Automated CSV logging
│   │   ├── power_visualizer.py   # Data visualization
│   │   ├── app_power_analyzer.py # App comparison
│   │   └── analyze_power_data.py # Energy analysis
│   │
│   ├── 🧪 Validation (6 scripts)
│   │   ├── validate_io_performance.py
│   │   ├── validate_attribution.py
│   │   ├── validate_statistics.py
│   │   ├── validate_pcore_tax.py
│   │   ├── validate_skewness_threshold.py
│   │   └── validate_scheduler_priority.py
│   │
│   ├── 🧠 Intelligent Features (5 scripts)
│   │   ├── intelligent_baseline_detector.py
│   │   ├── auto_rerun_on_skew.py
│   │   ├── enhanced_signal_handler.py
│   │   ├── automated_feedback_loop.py
│   │   └── thermal_throttle_controller.py
│   │
│   ├── 🌟 Advanced Features (4 scripts)
│   │   ├── adversarial_benchmark.py
│   │   ├── long_term_profiler.py
│   │   ├── ane_gpu_monitor.py
│   │   └── user_app_analyzer.py
│   │
│   ├── 🔧 Testing (3 scripts)
│   │   ├── test_components.py
│   │   ├── test_full_integration.py
│   │   └── verify_documentation.py
│   │
│   └── 🔌 Hardware (1 script)
│       └── arduino_power_receiver.ino
│
├── docs/                     # Documentation (13 files)
│   ├── README.md             # Documentation index ⭐ START HERE
│   │
│   ├── 📖 Public Docs (4 files)
│   │   ├── PERFORMANCE.md        # Performance analysis
│   │   ├── ARDUINO.md            # Arduino setup
│   │   ├── QUICK_REFERENCE.md    # Command reference
│   │   └── VISUAL_GUIDE.md       # Visual output guide
│   │
│   └── 🔬 Technical Docs (9 files)
│       ├── ARCHITECTURE.md       # System architecture
│       ├── TECHNICAL_DEEP_DIVE.md # Advanced concepts
│       ├── VALIDATION.md         # Validation guide
│       ├── INTELLIGENT_ENHANCEMENTS.md
│       ├── ENHANCEMENTS.md
│       ├── ADVANCED_FEATURES.md
│       ├── ADVANCED_CONCEPTS.md
│       └── CLOUDD_ANALYSIS.md
│
└── MobileNetV2.mlpackage/    # CoreML model (generated)
```

### 🧭 Navigation Guide

**New to the project?**
1. Read this `README.md` (overview)
2. Read `scripts/README.md` (script navigation)
3. Read `docs/README.md` (documentation index)

**Want to run benchmarks?**
→ Start with `scripts/unified_benchmark.py`

**Want to understand the code?**
→ Read `docs/ARCHITECTURE.md`

**Want to validate technical claims?**
→ Read `docs/VALIDATION.md`

## 🔬 Technical Details

### Architecture
- **Multi-threaded design**: Separate threads for inference, power monitoring, and serial communication
- **Thread-safe queues**: Ensures data integrity across concurrent operations
- **Robust error handling**: Gracefully handles missing hardware, permission issues, and edge cases

### Power Monitoring
- Uses macOS `powermetrics` for hardware-level power measurements
- Parses ANE (Neural Engine), CPU, and GPU power consumption
- Supports configurable sampling intervals (default: 500ms)

### Performance Optimization
- Automatic input tensor name detection
- Model warmup to ensure optimal performance
- Continuous inference loop for sustained load testing

## 📚 Documentation

- `docs/PERFORMANCE.md` - Detailed performance analysis and results
- `docs/ARDUINO.md` - Arduino integration guide
- `docs/QUICK_REFERENCE.md` - Quick command reference
- `docs/ADVANCED_FEATURES.md` - Advanced features: adversarial benchmark, long-term profiling, ANE/GPU monitoring

## 🎓 Use Cases

1. **ML Model Optimization**: Compare different model formats and compute units
2. **Energy Efficiency Research**: Understand power consumption patterns
3. **Hardware Benchmarking**: Test Neural Engine capabilities
4. **Application Analysis**: Find power-efficient alternatives
5. **Battery Life Studies**: Analyze power consumption for mobile development

## ⚠️ Requirements

- macOS with Apple Silicon (M1/M2/M3)
- Python 3.8+
- `sudo` access (required for powermetrics)
- Optional: Arduino for external monitoring

## 📝 License

This project is provided as-is for educational and research purposes.

## 🙏 Acknowledgments

Built to demonstrate the performance advantages of Apple's Neural Engine and CoreML framework on Apple Silicon hardware.
