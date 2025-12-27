# Script Enhancements

## Overview

Three key scripts have been enhanced with advanced features for better performance, visualization, and accuracy.

## 1. Power Logger (`power_logger.py`)

### Enhancement: Non-Blocking Subprocess with Threading

**Problem Solved**: The original implementation could freeze the script while waiting for powermetrics output.

**Solution**: Implemented non-blocking I/O using `select` for efficient subprocess communication.

### Key Improvements:

- **Non-Blocking Reads**: Uses `select.select()` to check for data availability without blocking
- **Process Monitoring**: Tracks powermetrics process health and handles crashes gracefully
- **Timeout Detection**: Warns if no data is received for 5+ seconds
- **Better Error Handling**: Graceful cleanup of subprocess on exit
- **Unbuffered I/O**: Real-time data processing with `bufsize=0`

### Technical Details:

```python
# Uses select for non-blocking read (works on Unix/macOS)
ready, _, _ = select.select([process.stdout], [], [], 0.1)

if ready:
    chunk = process.stdout.read(4096)  # Read available data
    # Process immediately without blocking
```

### Benefits:

- ✅ Script remains responsive during logging
- ✅ Can handle long-duration logging without freezing
- ✅ Better resource management
- ✅ Graceful shutdown handling

---

## 2. Power Visualizer (`power_visualizer.py`)

### Enhancement: Professional Matplotlib Visualizations

**Problem Solved**: Basic graphs lacked professional styling and comprehensive analysis.

**Solution**: Enhanced with multi-panel dashboards, statistical annotations, and professional styling.

### Key Improvements:

- **Multi-Panel Layout**: 
  - Main time-series plot (full width)
  - Average power bar chart
  - Power distribution histogram

- **Professional Styling**:
  - Seaborn-style grid (if available)
  - Distinct color palette for each metric
  - Different line styles for clarity
  - Mean value annotations on plots

- **Statistical Features**:
  - Mean lines on time-series
  - Bar chart with value labels
  - Histogram with mean/median markers
  - High-resolution output (300 DPI)

- **Enhanced Formatting**:
  - Better date/time formatting
  - Rotated labels for readability
  - Professional font sizing and weights
  - Clean, publication-ready output

### Visual Features:

```
┌─────────────────────────────────────────┐
│  Power Consumption Over Time            │
│  [Time-series with multiple metrics]    │
└─────────────────────────────────────────┘
┌──────────────────┬──────────────────────┐
│ Average Power    │ Power Distribution    │
│ [Bar Chart]      │ [Histogram]          │
└──────────────────┴──────────────────────┘
```

### Benefits:

- ✅ Publication-ready graphs
- ✅ Multiple analysis views in one figure
- ✅ Better data interpretation
- ✅ Professional appearance for portfolios

---

## 3. App Power Analyzer (`app_power_analyzer.py`)

### Enhancement: PID-Based Process Filtering

**Problem Solved**: Original implementation measured system-wide power, not app-specific consumption.

**Solution**: Added PID (Process ID) detection and filtering to track specific applications.

### Key Improvements:

- **PID Detection**: 
  - Finds all PIDs for a given application name
  - Searches by process name and command line
  - Handles multiple instances of the same app

- **Process Filtering**:
  - Filters powermetrics output by detected PIDs
  - Uses `--show-process-coalition` for better accuracy
  - Falls back to system-wide if no PIDs found

- **Enhanced Reporting**:
  - Shows detected PIDs in output
  - Reports process-specific power when available
  - Better accuracy for app comparisons

### Technical Implementation:

```python
def find_app_pids(app_name: str) -> Set[int]:
    """Find all PIDs for an application"""
    pids = set()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if app_name.lower() in proc.info['name'].lower():
            pids.add(proc.info['pid'])
    return pids
```

### Usage:

```bash
# With PID filtering (default)
sudo python3 scripts/app_power_analyzer.py Safari Chrome

# Without PID filtering (system-wide)
sudo python3 scripts/app_power_analyzer.py Safari Chrome --no-pid-filter
```

### Benefits:

- ✅ Accurate app-specific power measurements
- ✅ Can compare multiple instances
- ✅ Better isolation of app power consumption
- ✅ More meaningful comparisons

---

## Dependencies Added

- **psutil**: For process management and PID detection
  ```bash
  pip install psutil>=5.8.0
  ```

## Testing Recommendations

### Power Logger
```bash
# Test non-blocking behavior
sudo python3 scripts/power_logger.py --duration 30 --output test.csv
# Script should remain responsive, can Ctrl+C cleanly
```

### Power Visualizer
```bash
# Generate enhanced graphs
python3 scripts/power_visualizer.py test.csv --show
# Should see multi-panel professional graph
```

### App Power Analyzer
```bash
# Test PID detection
sudo python3 scripts/app_power_analyzer.py Safari --duration 10
# Should show detected PIDs and app-specific power
```

## Performance Impact

- **Power Logger**: Minimal overhead, better responsiveness
- **Power Visualizer**: Slightly longer generation time for better quality
- **App Power Analyzer**: Small overhead for PID detection, more accurate results

## Backward Compatibility

All enhancements maintain backward compatibility:
- Default behavior unchanged
- New features are opt-in or improve existing functionality
- No breaking changes to command-line interfaces

