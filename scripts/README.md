# Scripts Directory

**Single Responsibility**: Navigation guide for all executable scripts, organized by purpose and workflow stage.

## 📁 Directory Organization

All scripts are organized by their primary responsibility. Each script follows the **Single Responsibility Principle (SRP)** - one clear purpose per script.

---

## 🚀 Core Workflow (Start Here)

**Purpose**: Essential scripts for the main benchmarking workflow.

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `convert_model.py` | Convert PyTorch → CoreML | First step: Prepare model |
| `benchmark.py` | PyTorch baseline benchmark | Compare against CoreML |
| `benchmark_power.py` | CoreML Neural Engine benchmark | Measure ANE performance |
| `unified_benchmark.py` | **Main benchmark** (inference + power + Arduino) | **Primary entry point** |

**Workflow**:
```bash
1. python3 scripts/convert_model.py
2. python3 scripts/benchmark.py              # Optional: baseline
3. python3 scripts/benchmark_power.py        # Optional: CoreML only
4. sudo python3 scripts/unified_benchmark.py # Main benchmark
```

---

## 📊 Power Monitoring & Analysis

**Purpose**: Collect, visualize, and analyze power consumption data.

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `power_logger.py` | Automated CSV logging | Real-time `powermetrics` | CSV file |
| `power_visualizer.py` | Generate graphs from CSV | CSV file | PNG graphs |
| `app_power_analyzer.py` | Compare apps (Safari vs Chrome) | App names | Comparison report |
| `analyze_power_data.py` | Calculate energy efficiency | Power values | Energy metrics |

**Note**: `analyze_power_data.py` could be integrated into `power_visualizer.py` (both analyze data), but kept separate for modularity.

---

## 🧪 Validation Scripts

**Purpose**: Empirically validate technical claims about hardware/kernel behavior.

| Script | Validates | Key Question |
|--------|-----------|--------------|
| `validate_io_performance.py` | Non-blocking I/O performance | Does `select.select()` handle stalls? |
| `validate_attribution.py` | Power attribution accuracy | Can we accurately attribute power to processes? |
| `validate_statistics.py` | Mean/median divergence | Does skewness identify workload type? |
| `validate_pcore_tax.py` | P-core power tax | What's the cost of using P-cores for background tasks? |
| `validate_skewness_threshold.py` | Skewness detection threshold | At what point does background task become significant? |
| `validate_scheduler_priority.py` | Kernel signal handling | Why are timer waits prioritized over pipe I/O? |

**Usage**: Run individually to validate specific technical claims.

---

## 🧠 Intelligent Features

**Purpose**: AI-powered, adaptive features that make the suite "intelligent."

| Script | Purpose | Key Feature |
|--------|---------|-------------|
| `intelligent_baseline_detector.py` | Adaptive baseline adjustment | Auto-detects high baseline, checks P-core usage |
| `auto_rerun_on_skew.py` | Auto re-run on interference | Monitors skewness, offers to re-run when interference subsides |
| `enhanced_signal_handler.py` | Multi-signal handling | Handles SIGINT, SIGTERM, SIGHUP, SIGQUIT gracefully |
| `automated_feedback_loop.py` | Automated optimization | Detects → Fixes → Verifies power issues for daemons |
| `thermal_throttle_controller.py` | Programmatic throttling | Keeps burst fraction under cooling threshold |

**Note**: `enhanced_signal_handler.py` is a utility used by other scripts (could be a module, but kept as script for standalone testing).

---

## 🌟 Advanced Features

**Purpose**: Extended capabilities beyond core benchmarking.

| Script | Purpose | Use Case |
|--------|---------|----------|
| `adversarial_benchmark.py` | Extreme stress test | Test robustness under CPU stress + SSH disconnect |
| `long_term_profiler.py` | Long-term daemon profiling | Identify battery drain offenders over days |
| `ane_gpu_monitor.py` | ANE/GPU statistical analysis | Monitor accelerators with skewness/attribution |
| `user_app_analyzer.py` | User app power analysis | Analyze Safari, Chrome, etc. with WebKit breakdown |

---

## 🔧 Testing & Utilities

**Purpose**: Testing and maintenance scripts.

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `test_components.py` | Component verification | Before running full benchmark |
| `test_full_integration.py` | Comprehensive integration test | Verify entire system works |
| `verify_documentation.py` | Documentation verification | Check docs match implementation |

**Note**: `test_components.py` could be integrated into `test_full_integration.py`, but kept separate for quick component checks.

---

## 🔌 Hardware

**Purpose**: External hardware integration.

| Script | Purpose | Platform |
|--------|---------|-----------|
| `arduino_power_receiver.ino` | Arduino sketch for power display | Arduino IDE |

---

## 📋 Script Count by Category

- **Core Workflow**: 4 scripts
- **Power Monitoring**: 4 scripts
- **Validation**: 6 scripts
- **Intelligent Features**: 5 scripts
- **Advanced Features**: 4 scripts
- **Testing**: 3 scripts
- **Hardware**: 1 script

**Total**: 27 scripts (26 Python + 1 Arduino)

---

## 🎯 Navigation Guide

### For First-Time Users
1. Start with `convert_model.py`
2. Run `test_components.py` to verify setup
3. Run `unified_benchmark.py` for main benchmark

### For Power Analysis
1. Use `power_logger.py` to collect data
2. Use `power_visualizer.py` to visualize
3. Use `app_power_analyzer.py` to compare apps

### For Advanced Research
1. Run validation scripts to understand hardware behavior
2. Use intelligent features for automated optimization
3. Use advanced features for extended analysis

### For Developers
1. Read `ARCHITECTURE.md` for system design
2. Check `test_full_integration.py` for integration tests
3. Review validation scripts for technical claims

---

## 🔄 Potential Integrations (Without Breaking SRP)

### ✅ Safe Integrations
1. **`analyze_power_data.py` → `power_visualizer.py`**
   - Both analyze/visualize power data
   - Could add `--analyze` flag to visualizer
   - **Status**: Kept separate for modularity (can use independently)

2. **`test_components.py` → `test_full_integration.py`
   - Both are testing scripts
   - Could add `--components-only` flag
   - **Status**: Kept separate for quick component checks

### ❌ Should Stay Separate
- **All validation scripts**: Each validates a specific technical claim
- **All intelligent features**: Each serves a distinct purpose
- **Core benchmarking scripts**: Different stages of workflow
- **Advanced features**: Different use cases and audiences

---

## 📚 Related Documentation

- **`docs/ARCHITECTURE.md`**: System design and technical details
- **`docs/QUICK_REFERENCE.md`**: Command cheat sheet
- **`docs/VALIDATION.md`**: Complete validation guide
- **`docs/ADVANCED_FEATURES.md`**: Advanced features documentation

---

## ✅ SRP Compliance

Each script:
- ✅ Has one clear, distinct purpose
- ✅ Can be used independently
- ✅ Follows naming convention (purpose is clear from name)
- ✅ Has comprehensive docstring explaining purpose
- ✅ Is organized by category for easy navigation

**All scripts follow Single Responsibility Principle.**

