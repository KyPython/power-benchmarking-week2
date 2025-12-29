# Codebase Navigation Guide

## Overview

This guide helps you navigate the Power Benchmarking Suite codebase and understand how components connect.

## Directory Structure

```
power-benchmarking-week2/
├── power_benchmarking_suite/     # Main package
│   ├── __init__.py               # Package initialization
│   ├── cli.py                    # CLI entry point
│   ├── commands/                 # Command implementations
│   │   ├── monitor.py           # Real-time power monitoring
│   │   ├── analyze.py           # Power data analysis
│   │   ├── optimize.py          # Energy optimization
│   │   ├── config.py            # Configuration management
│   │   ├── quickstart.py        # Interactive onboarding
│   │   └── validate.py          # System compatibility
│   ├── observability/            # Observability module
│   │   ├── logging.py           # Structured logging
│   │   ├── tracing.py           # OpenTelemetry tracing
│   │   └── metrics.py            # Prometheus metrics
│   ├── utils/                    # Utility functions
│   │   └── error_handler.py     # Error handling
│   ├── config.py                 # Configuration management
│   └── errors.py                 # Custom exceptions
├── scripts/                      # Standalone scripts
│   ├── unified_benchmark.py     # Core benchmarking script
│   ├── energy_gap_framework.py  # Energy analysis
│   └── validate-*.sh            # Quality validation scripts
├── docs/                         # Documentation
├── tests/                        # Test suite
└── requirements.txt              # Dependencies
```

## Entry Points

### CLI Command Flow

1. **User runs**: `power-benchmark monitor --test 30`
2. **Entry**: `power_benchmarking_suite/cli.py::main()`
   - Parses arguments
   - Routes to command handler
3. **Command**: `power_benchmarking_suite/commands/monitor.py::run()`
   - Checks permissions
   - Loads thermal feedback
   - Executes `scripts/unified_benchmark.py`
4. **Script**: `scripts/unified_benchmark.py::main()`
   - Loads CoreML model
   - Starts power monitoring
   - Runs inference loop
   - Collects metrics

### Command-to-Code Mapping

| Command | Entry Point | Main Logic |
|---------|-------------|------------|
| `monitor` | `commands/monitor.py` | `scripts/unified_benchmark.py` |
| `analyze` | `commands/analyze.py` | `scripts/app_power_analyzer.py` |
| `optimize` | `commands/optimize.py` | `scripts/energy_gap_framework.py` |
| `config` | `commands/config.py` | `config.py` |
| `quickstart` | `commands/quickstart.py` | Interactive flow |
| `validate` | `commands/validate.py` | System checks |

## Key Components

### 1. CLI System (`cli.py`)
- Argument parsing
- Command routing
- Error handling
- Configuration loading

### 2. Commands (`commands/`)
Each command module:
- `add_parser()` - Defines CLI arguments
- `run()` - Executes command logic
- Uses observability for logging/tracing

### 3. Observability (`observability/`)
- **Logging**: Structured JSON logs with trace context
- **Tracing**: OpenTelemetry spans for operations
- **Metrics**: Prometheus metrics for power/inference

### 4. Core Scripts (`scripts/`)
- `unified_benchmark.py` - Main benchmarking logic
- `energy_gap_framework.py` - Energy analysis
- Validation scripts - Code quality checks

## Data Flow

### Power Monitoring Flow
```
powermetrics (subprocess)
  ↓
powermetrics_reader() [thread]
  ↓
power_queue (Queue)
  ↓
display_live_stats() [thread]
  ↓
User terminal (rich console)
```

### Inference Flow
```
CoreML Model
  ↓
inference_loop() [main thread]
  ↓
Neural Engine (hardware)
  ↓
Metrics collection
```

## Adding New Features

### New Command
1. Create `power_benchmarking_suite/commands/new_command.py`
2. Implement `add_parser()` and `run()`
3. Register in `cli.py`
4. Add observability (logging, tracing, metrics)

### New Script
1. Create `scripts/new_script.py`
2. Use observability module for logging
3. Add to `setup.py` if needed
4. Document in relevant command

### New Metric
1. Add to `observability/metrics.py`
2. Record in relevant code path
3. Update Grafana dashboard (if applicable)

## Testing

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Run: `pytest tests/`

## Debugging

1. **Enable debug logging**: `LOG_LEVEL=DEBUG power-benchmark ...`
2. **View traces**: Check console output (if enabled)
3. **View metrics**: `curl http://localhost:8000/metrics`
4. **Check logs**: Structured JSON in logs directory


