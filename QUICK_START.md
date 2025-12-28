# Quick Start Guide

**5-minute setup to get started with Power Benchmarking Suite**

## Step 1: Install (2 minutes)

```bash
# Clone and install
git clone https://github.com/KyPython/power-benchmarking-week2.git
cd power-benchmarking-week2
pip install -e .
```

## Step 2: Verify Installation (30 seconds)

```bash
# Check installation
power-benchmark --help

# Check premium status
power-benchmark --premium-status
```

## Step 3: Run Your First Benchmark (2 minutes)

```bash
# Convert model (if needed)
python3 scripts/convert_model.py

# Run 30-second test benchmark
sudo power-benchmark unified --test 30
```

## Step 4: Analyze Results (30 seconds)

```bash
# If you generated a CSV file
power-benchmark visualize --csv power_log.csv
```

## Common Workflows

### Workflow 1: Quick Power Check

```bash
sudo power-benchmark unified --test 30
```

### Workflow 2: Analyze an App

```bash
sudo power-benchmark analyze --app Safari --duration 60
```

### Workflow 3: Long-Term Monitoring

```bash
# Start logging (1 hour)
sudo power-benchmark logger --duration 3600 --output power_log.csv

# Visualize results
power-benchmark visualize --csv power_log.csv
```

## Premium Features

### Enable Premium (Testing)

```bash
power-benchmark enable-premium-test
```

### Upgrade to Premium

```bash
power-benchmark --upgrade
```

## Next Steps

- Read `README.md` for full documentation
- Read `docs/QUICK_REFERENCE.md` for all commands
- Read `docs/ARCHITECTURE.md` for technical details

## Troubleshooting

**Permission errors?**
```bash
# Use sudo for powermetrics
sudo power-benchmark unified --test 30
```

**Module not found?**
```bash
pip install -e . --force-reinstall
```

**Need help?**
```bash
power-benchmark --help
```

