# Installation Guide

## Quick Install

```bash
# Install from local directory
pip install -e .

# Or install from PyPI (once published)
pip install power-benchmarking-suite
```

## Prerequisites

- macOS with Apple Silicon (M1/M2/M3)
- Python 3.8+
- `sudo` access (required for powermetrics)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/KyPython/power-benchmarking-week2.git
cd power-benchmarking-week2
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install the Package

```bash
# Development install (editable)
pip install -e .

# Or production install
pip install .
```

### 4. Verify Installation

```bash
# Check if command is available
power-benchmark --help

# Check premium status
power-benchmark --premium-status
```

## Usage

### Basic Commands

```bash
# Run unified benchmark (30 second test)
sudo power-benchmark unified --test 30

# Run full benchmark
sudo power-benchmark unified

# Analyze Safari power consumption
sudo power-benchmark analyze --app Safari --duration 60

# Visualize power data
power-benchmark visualize --csv power_log.csv

# Start power logging
sudo power-benchmark logger --duration 3600 --output power_log.csv
```

### Configuration

Configuration is stored in `~/.power_benchmarking/config.yaml`:

```yaml
powermetrics:
  sample_interval: 500  # milliseconds
  samplers:
    - cpu_power
    - ane_power
    - gpu_power

arduino:
  enabled: false
  port: /dev/cu.usbmodem*
  baud_rate: 115200

default_profile: default
```

### Profiles

Create and use profiles for different scenarios:

```bash
# Create a profile
power-benchmark --profile my_profile --mode unified --test 30

# List profiles
ls ~/.power_benchmarking/profiles/
```

## Premium Features

### Free Tier

- ✅ Single device monitoring
- ✅ Up to 1 hour per session
- ✅ Basic power monitoring
- ✅ Standard visualizations

### Premium Tier ($99/month)

- ✅ Up to 10 devices
- ✅ Up to 24 hours per session
- ✅ Advanced analytics
- ✅ Cloud sync
- ✅ Team collaboration
- ✅ API access
- ✅ Priority support

### Enable Premium (Testing)

For local testing/development:

```bash
power-benchmark enable-premium-test
```

**Note**: This is for development only. Production use requires paid subscription.

## Troubleshooting

### Permission Errors

If you see permission errors with `powermetrics`:

```bash
# Ensure you're using sudo
sudo power-benchmark unified --test 30
```

### Module Not Found

If you see "Module not found" errors:

```bash
# Reinstall the package
pip install -e . --force-reinstall
```

### Configuration Issues

Reset configuration:

```bash
rm ~/.power_benchmarking/config.yaml
power-benchmark --premium-status  # Will create default config
```

## Next Steps

- Read `README.md` for overview
- Read `docs/QUICK_REFERENCE.md` for command reference
- Read `docs/ARCHITECTURE.md` for technical details

