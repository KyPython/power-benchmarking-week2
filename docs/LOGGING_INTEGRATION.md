# Logging Integration Guide

## Overview

The Power Benchmarking Suite now uses structured logging via the observability module, replacing `print()` statements with proper logging while keeping `console.print()` for user-facing output.

## Architecture

### Logging Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages
- **WARNING**: Warning messages (non-critical issues)
- **ERROR**: Error messages (failures that don't stop execution)
- **CRITICAL**: Critical errors (failures that stop execution)

### Output Channels

1. **User-Facing Output**: `console.print()` (Rich library) - for real-time display
2. **Backend Logging**: `logger.info()`, `logger.warning()`, `logger.error()` - for structured logs

## Implementation

### Setup

```python
# In unified_benchmark.py
import logging

try:
    from power_benchmarking_suite.observability.logging import get_logger
    logger = get_logger('unified_benchmark')
except ImportError:
    # Fallback to standard logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('unified_benchmark')
```

### Usage Patterns

#### Before (print statements)
```python
print("✅ powermetrics started")
print(f"❌ Error: {e}")
```

#### After (logging + console)
```python
# User-facing (keep console.print)
if console:
    console.print("[green]✅ powermetrics started[/green]")
else:
    print("✅ powermetrics started")

# Backend logging (add logger)
logger.info("powermetrics started", extra={'sample_interval': sample_interval})
logger.error(f"Error running powermetrics: {e}", exc_info=True)
```

## Migration Checklist

- [x] Add logging import and setup
- [ ] Replace backend `print()` with `logger.info/warning/error`
- [ ] Keep `console.print()` for user-facing output
- [ ] Add structured context to log messages
- [ ] Integrate with observability tracing

## Next Steps

1. Complete migration of all `print()` statements
2. Add trace context to log messages
3. Integrate with metrics collection
4. Set up log aggregation (Loki/Promtail)


