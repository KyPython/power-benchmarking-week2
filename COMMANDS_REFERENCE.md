# Power Benchmarking Suite - Commands Reference

**Quick Access**: Run `power-benchmark help` or `power-benchmark --help` anytime to see all available commands.

---

## 📋 Table of Contents

- [Quick Command Overview](#quick-command-overview)
- [Detailed Command Reference](#detailed-command-reference)
- [Common Workflows](#common-workflows)
- [System Status](#system-status)
- [Getting Help](#getting-help)

---

## 🚀 Quick Command Overview

| Command | Purpose | Sudo Required? |
|---------|---------|----------------|
| `power-benchmark validate` | System compatibility checks | No (for basic) |
| `power-benchmark optimize` | Energy gap and thermal optimization | No |
| `power-benchmark marketing` | Lead capture, email, README generation | No |
| `power-benchmark monitor` | Real-time power monitoring | Yes |
| `power-benchmark analyze` | Power consumption analysis | Yes (for apps) |
| `power-benchmark config` | Configuration management | No |
| `power-benchmark quickstart` | Interactive onboarding | No |
| `power-benchmark business` | Business automation | No |
| `power-benchmark help` | Show this reference guide | No |

---

## 📖 Detailed Command Reference

### 1. `power-benchmark validate` - System Compatibility Checks

**Purpose**: Verify your system is compatible with all Power Benchmarking Suite features.

**Basic Usage**:
```bash
# Quick compatibility check
power-benchmark validate

# Detailed validation with explanations
power-benchmark validate --verbose

# Mock mode (for CI/CD or testing without hardware)
power-benchmark validate --mock --verbose
```

**What It Checks**:
- ✅ Apple Silicon chip detection (M1/M2/M3)
- ✅ Thermal Guardian compatibility
- ✅ Hardware feature support
- ✅ System configuration

**Key Features**:
- **159+ numbered sections** in `--verbose` mode covering:
  - The Psychology of Priority
  - The Shield of Accountability
  - The Negotiation Logic
  - The Commitment Anchor
  - The Durability of Analogy
  - The Cost of Inaction (4,368% APR)
  - The Math of Inaction
  - And many more...

**Examples**:
```bash
# Quick check (no sudo needed)
power-benchmark validate

# Full validation with all explanations
power-benchmark validate --verbose

# Test mock mode for CI/CD
power-benchmark validate --mock --verbose
```

---

### 2. `power-benchmark optimize` - Energy Gap & Thermal Optimization

**Purpose**: Optimize code for energy efficiency and thermal management.

**Subcommands**:
```bash
# Energy gap analysis
power-benchmark optimize energy-gap --simple simple.py --optimized optimized.py

# Thermal optimization
power-benchmark optimize thermal --app Safari --ambient-temp 35
```

**Examples**:
```bash
# Compare two code versions for energy efficiency
power-benchmark optimize energy-gap \
  --simple examples/simple.py \
  --optimized examples/optimized.py

# Optimize for thermal safety
power-benchmark optimize thermal \
  --app Safari \
  --ambient-temp 35
```

---

### 3. `power-benchmark marketing` - Lead Capture & README Generation

**Purpose**: Generate marketing materials, capture leads, and create README files.

**Subcommands**:
```bash
# Generate a "Green" README with sustainability metrics
power-benchmark marketing readme

# Lead capture (if configured)
power-benchmark marketing capture --email user@example.com

# Email automation (if configured)
power-benchmark marketing email --template welcome
```

**Examples**:
```bash
# Generate GitHub README with sustainability credentials
power-benchmark marketing readme

# The generated README includes:
# - 4.5× energy efficiency improvement
# - Carbon payback period (4.7 days)
# - Operational vs. Embodied carbon breakdown
# - Manager communication templates
```

---

### 4. `power-benchmark monitor` - Real-Time Power Monitoring

**Purpose**: Monitor power consumption in real-time with live statistics.

**Basic Usage**:
```bash
# 30-second test run
sudo power-benchmark monitor --test 30

# Monitor for specific duration
sudo power-benchmark monitor --duration 60

# Monitor with output file
sudo power-benchmark monitor --duration 300 --output power_log.csv
```

**Features**:
- Real-time power bars (visual feedback)
- Smoothness level indicators (✨ Smooth, 🌟 Very Smooth, 💫 Buttery Smooth)
- Live statistics display
- CSV logging for analysis

**Examples**:
```bash
# Quick 30-second test
sudo power-benchmark monitor --test 30

# Monitor for 5 minutes and save to CSV
sudo power-benchmark monitor --duration 300 --output session.csv

# Monitor with verbose output
sudo power-benchmark monitor --duration 60 --verbose
```

---

### 5. `power-benchmark analyze` - Power Consumption Analysis

**Purpose**: Analyze power consumption data from apps or CSV files.

**Subcommands**:
```bash
# Analyze an application
sudo power-benchmark analyze app Safari --duration 60

# Analyze CSV data
power-benchmark analyze csv power_log.csv

# Analyze with visualization
power-benchmark analyze csv power_log.csv --output report.png
```

**Examples**:
```bash
# Analyze Safari power consumption for 1 minute
sudo power-benchmark analyze app Safari --duration 60

# Analyze CSV file and generate report
power-benchmark analyze csv power_log.csv --output report.png

# Compare multiple apps
sudo power-benchmark analyze app Safari Chrome --duration 30
```

---

### 6. `power-benchmark config` - Configuration Management

**Purpose**: View and modify Power Benchmarking Suite configuration.

**Basic Usage**:
```bash
# List all configuration settings
power-benchmark config --list

# Get a specific setting
power-benchmark config --get powermetrics.sample_interval

# Set a configuration value
power-benchmark config --set powermetrics.sample_interval 1000

# Reset to defaults
power-benchmark config --reset
```

**Examples**:
```bash
# View all settings
power-benchmark config --list

# Change sampling interval to 1 second
power-benchmark config --set powermetrics.sample_interval 1000

# View current sampling interval
power-benchmark config --get powermetrics.sample_interval
```

---

### 7. `power-benchmark quickstart` - Interactive Onboarding

**Purpose**: Step-by-step guide to get started with the Power Benchmarking Suite.

**Aliases**: `qs`, `start`

**Usage**:
```bash
# Run interactive quickstart
power-benchmark quickstart

# Skip system checks
power-benchmark quickstart --skip-checks
```

**What It Does**:
1. ✅ System compatibility check
2. ✅ Model verification
3. ✅ Quick test run (optional)
4. ✅ Command reference display
5. ✅ Learning path guidance

**Examples**:
```bash
# Full interactive onboarding
power-benchmark quickstart

# Or use alias
power-benchmark qs

# Skip compatibility checks
power-benchmark quickstart --skip-checks
```

---

### 8. `power-benchmark business` - Business Automation

**Purpose**: Client management, invoicing, check-ins, and workflow automation.

**Subcommands**:
```bash
# Client management
power-benchmark business clients --list
power-benchmark business clients --add "Client Name"

# Invoicing
power-benchmark business invoice --generate

# Check-ins
power-benchmark business checkin --create
```

**Examples**:
```bash
# List all clients
power-benchmark business clients --list

# Add a new client
power-benchmark business clients --add "Acme Corp"

# Generate invoice
power-benchmark business invoice --generate
```

---

### 9. `power-benchmark help` - Show Commands Reference

**Purpose**: Display this commands reference guide.

**Usage**:
```bash
# Show commands reference
power-benchmark help

# Show help for specific command
power-benchmark validate --help
power-benchmark optimize --help
```

**Examples**:
```bash
# Show all commands
power-benchmark help

# Show help for validate command
power-benchmark validate --help

# Show help for optimize command
power-benchmark optimize --help
```

---

## 🔄 Common Workflows

### Workflow 1: First-Time Setup
```bash
# 1. Run quickstart for interactive setup
power-benchmark quickstart

# 2. Validate system compatibility
power-benchmark validate --verbose

# 3. Run a quick test
sudo power-benchmark monitor --test 30
```

### Workflow 2: Daily Power Monitoring
```bash
# 1. Monitor power for 5 minutes
sudo power-benchmark monitor --duration 300 --output daily_log.csv

# 2. Analyze the results
power-benchmark analyze csv daily_log.csv --output daily_report.png
```

### Workflow 3: Code Optimization
```bash
# 1. Compare two code versions
power-benchmark optimize energy-gap \
  --simple examples/simple.py \
  --optimized examples/optimized.py

# 2. Optimize for thermal safety
power-benchmark optimize thermal --app MyApp --ambient-temp 35

# 3. Monitor optimized code
sudo power-benchmark monitor --test 60
```

### Workflow 4: Marketing & Documentation
```bash
# 1. Generate Green README
power-benchmark marketing readme

# 2. Validate system (for README stats)
power-benchmark validate --verbose
```

### Workflow 5: CI/CD Integration
```bash
# 1. Run mock validation (no hardware needed)
power-benchmark validate --mock --verbose

# 2. Check for consistency issues
power-benchmark validate --mock --verbose | grep "Consistency Check"
```

---

## 📊 System Status

### Current System Detection

**Detected**: Apple M2 chip (or your chip)
- ✅ Thermal Guardian: Fully compatible
- ✅ All Thermal Guardian features supported
- ✅ Mock mode working for CI/CD testing

### What You Can Do Next

1. **Run full validation**: `power-benchmark validate --verbose` (requires sudo for hardware checks)
2. **Test mock mode**: `power-benchmark validate --mock --verbose` (works without sudo)
3. **Generate marketing README**: `power-benchmark marketing readme`
4. **Run quickstart**: `power-benchmark quickstart`

---

## 🆘 Getting Help

### Quick Help
```bash
# Show all commands
power-benchmark --help

# Show help for specific command
power-benchmark validate --help
power-benchmark optimize --help
power-benchmark marketing --help
```

### Documentation
- **Quick Start Guide**: `QUICK_START_GUIDE.md`
- **Product Study Guide**: `docs/PRODUCT_STUDY_GUIDE.md`
- **Technical Deep Dive**: `docs/TECHNICAL_DEEP_DIVE.md`
- **Architecture Guide**: `docs/ARCHITECTURE.md`

### Command Aliases

Some commands have aliases for faster typing:
- `power-benchmark quickstart` → `power-benchmark qs` or `power-benchmark start`
- `power-benchmark validate` → `power-benchmark validate` (no alias, but `--verbose` is common)

---

## 💡 Tips

1. **Always run `validate` first** to ensure system compatibility
2. **Use `--verbose`** for detailed explanations and frameworks
3. **Use `--mock`** for CI/CD testing without hardware
4. **Save outputs** with `--output` flag for later analysis
5. **Run `quickstart`** if you're new to the suite

---

## 🔗 Related Documentation

- [Quick Start Guide](QUICK_START_GUIDE.md) - Get started in 1-2 hours
- [Product Study Guide](docs/PRODUCT_STUDY_GUIDE.md) - Complete product knowledge
- [Technical Deep Dive](docs/TECHNICAL_DEEP_DIVE.md) - Whitepaper audit and proof points
- [Architecture Guide](docs/ARCHITECTURE.md) - System design and implementation
- [Mechanical Sympathy Analogies](docs/MECHANICAL_SYMPATHY_ANALOGIES.md) - Web developer-friendly explanations

---

**Last Updated**: This reference is always available via `power-benchmark help`

