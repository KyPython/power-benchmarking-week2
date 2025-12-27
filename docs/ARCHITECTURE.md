# Architecture & Design Decisions

**Single Responsibility: System architecture, design decisions, and implementation details.**

## System Architecture

### Multi-Threaded Design

The unified benchmark uses a three-thread architecture:

- **Main Thread**: Runs CoreML inference loop
- **Power Thread**: Runs powermetrics subprocess and parses output
- **Serial Thread**: Reads from power queue and sends to Arduino

**Communication**: Thread-safe `Queue` for data exchange between threads.

**Benefits**:
- Non-blocking operations
- Real-time data processing
- Graceful shutdown handling
- Isolated error handling per component

### Threading Implementation

```python
# Power monitoring thread (daemon)
power_thread = threading.Thread(
    target=powermetrics_reader,
    args=(sample_interval, data_queue),
    daemon=True  # Automatically terminates with main thread
)
```

**Key Design Decisions**:
- Daemon threads for automatic cleanup
- Queue-based communication (thread-safe)
- Global `running` flag for coordinated shutdown
- Signal handlers for graceful Ctrl+C handling

## Design Decisions & Solutions

### 1. powermetrics Output Format Parsing

**Challenge**: powermetrics output format varies across macOS versions.

**Solution**: Multi-pattern regex parsing with fallback strategies:
- Primary patterns: `ANE Power: X mW`, `ANE: X mW`, `Neural Engine: X mW`
- Fallback: Line-by-line search for ANE-related power values
- Buffer management: Prevents memory overflow, handles partial reads
- Accumulates output in buffer, processes complete lines, keeps last 8KB for overlap

### 2. Model Input Tensor Detection

**Challenge**: Input tensor names vary between models (e.g., `'x_1'` may not match actual spec).

**Solution**: Auto-detection with fallback:
1. Read from model specification
2. Test common names (`x_1`, `input`, `image`, `data`)
3. Use first successful match

### 3. Timing and Synchronization

**Challenge**: "Infinite loop" + "every 500ms" is ambiguous - continuous inference or periodic?

**Solution**: Continuous inference loop with independent power monitoring:
- Inference runs as fast as possible (with small 1ms sleep to prevent overwhelming)
- Power data is collected every 500ms via powermetrics
- Serial data is sent every 500ms when new power data is available
- Uses threading to decouple these operations

### 4. Serial Port Detection

**Challenge**: Multiple USB devices, Arduino may not be connected.

**Solution**: 
- Enumerate all serial ports using `pyserial.tools.list_ports`
- Match `usbmodem` pattern
- Return first matching port
- Return `None` if not found (graceful degradation)
- Script continues without Arduino (expected "Edge Case" behavior)

### 5. Error Handling Strategy

**Philosophy**: Fail gracefully, continue when possible.

**Implementation**:
- **Arduino not found**: Prints warning, continues benchmark, drains power queue
- **Serial errors**: Catches `SerialException`, prints warning, continues
- **powermetrics errors**: Catches subprocess errors, prints error message, attempts to continue
- **Inference errors**: Catches exceptions, prints error, exits gracefully
- All errors are logged but don't crash the entire benchmark

### 6. Data Synchronization

**Challenge**: Align power readings with inference timing.

**Solution**: 
- Power readings are timestamped when added to queue
- Serial thread always sends the latest available power value
- Queue-based approach (FIFO) ensures no blocking between threads
- Latest value is used if multiple values accumulate

### 7. powermetrics Permissions

**Challenge**: powermetrics requires `sudo` - what if user doesn't have permissions?

**Solution**: 
- Error handling catches `CalledProcessError` and prints helpful message
- Script continues to attempt other operations
- User is informed they need sudo permissions

### 8. Graceful Shutdown

**Challenge**: How to stop the infinite loop cleanly?

**Solution**: 
- Implements `SIGINT` signal handler (Ctrl+C)
- Global `running` flag for coordinated shutdown
- All threads check `running` flag and exit gracefully
- Serial port is properly closed on exit
- Process cleanup with timeout handling

### 9. Buffer Management

**Challenge**: powermetrics output can be large - how to handle memory?

**Solution**:
- Accumulates output in buffer (max 16KB)
- Processes line-by-line
- Clears buffer after successful parse (keeps last 8KB for overlap)
- Prevents buffer from growing beyond limits
- Handles partial reads gracefully

## Performance Optimizations

### Non-Blocking I/O

**Power Logger Enhancement**: Uses `select.select()` for non-blocking subprocess reads.

```python
ready, _, _ = select.select([process.stdout], [], [], 0.1)
if ready:
    chunk = process.stdout.read(4096)  # Non-blocking
```

**Benefits**:
- Script remains responsive
- No freezing during long sessions
- Better resource utilization
- Immediate response to Ctrl+C

### Process Filtering

**App Analyzer Enhancement**: PID-based filtering for accurate app measurements.

- Finds all PIDs for application using `psutil`
- Filters powermetrics output by process name
- Uses `--show-process-coalition` for better accuracy
- Falls back to system-wide if needed

## Known Limitations

1. **powermetrics requires sudo**: macOS security requirement
2. **ANE power may be 0**: Neural Engine idle state
3. **Serial port detection**: First matching port only
4. **Process filtering**: Approximate (powermetrics limitations)
5. **Power attribution**: System-wide measurements include background processes

## Testing Strategy

### Component Verification

Run `scripts/test_components.py` to verify:
- Model loading
- ANE parsing logic
- Serial detection
- powermetrics availability

### Integration Testing

```bash
# Quick test (10 seconds)
sudo python3 scripts/unified_benchmark.py --test 10

# Full test
sudo python3 scripts/unified_benchmark.py
```

## Future Enhancements

Potential improvements:
- Real-time PID tracking during measurements
- More granular power attribution
- Web dashboard for live monitoring
- Historical data analysis
- Baseline subtraction for app attribution
