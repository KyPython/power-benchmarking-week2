# Arduino Setup Guide

## Quick Start

1. **Upload the Sketch**
   - Open `scripts/arduino_power_receiver.ino` in Arduino IDE
   - Select your board (Arduino Uno, Nano, etc.)
   - Select the correct port (usually `/dev/cu.usbmodem*` on macOS)
   - Click "Upload"

2. **Open Serial Monitor**
   - Tools → Serial Monitor (or `Cmd+Shift+M`)
   - Set baud rate to **115200**
   - You should see: "Arduino Power Receiver - Ready"

3. **Run Python Script**
   ```bash
   sudo python3 scripts/unified_benchmark.py
   ```

4. **View Data**
   - **Serial Monitor**: Shows formatted output with packet counts
   - **Serial Plotter**: Tools → Serial Plotter (shows real-time graph)
     - For Serial Plotter, uncomment line 95 in the sketch:
     ```cpp
     // Serial.println(powerValue);
     ```
     And comment out the detailed Serial.print statements

## Features

- ✅ Receives `ANE_PWR:[value]\n` format
- ✅ Validates power values (0-5000 mW range)
- ✅ Error counting and reporting
- ✅ LED blink on activity (if board has built-in LED)
- ✅ Timeout detection (warns if no data for 1+ seconds)
- ✅ Buffer overflow protection

## Troubleshooting

**No data received:**
- Check baud rate matches (115200)
- Verify Arduino port matches what Python detects
- Check USB cable connection

**Garbage characters:**
- Reset Arduino (press reset button)
- Restart Python script
- Check baud rate mismatch

**Python can't find Arduino:**
- Unplug and replug USB cable
- Check `ls /dev/cu.usbmodem*` in terminal
- The script will continue without Arduino (expected behavior)

