# Project Structure

## Organization Summary

This project has been organized for clarity and portfolio presentation:

```
power-benchmarking-week2/
├── README.md                    # Main portfolio README (public)
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
│
├── scripts/                     # All executable code
│   ├── convert_model.py        # PyTorch → CoreML conversion
│   ├── benchmark.py            # PyTorch baseline benchmark
│   ├── benchmark_power.py      # CoreML Neural Engine benchmark
│   ├── unified_benchmark.py     # Main integrated benchmark
│   ├── power_logger.py         # Automated CSV logging
│   ├── power_visualizer.py     # Data visualization
│   ├── app_power_analyzer.py   # App comparison tool
│   ├── analyze_power_data.py   # Energy efficiency analysis
│   ├── test_components.py      # Component verification
│   └── arduino_power_receiver.ino  # Arduino sketch
│
├── docs/                        # Documentation
│   ├── README.md               # Documentation index
│   │
│   ├── [PUBLIC]                # Portfolio/public docs
│   ├── PERFORMANCE.md           # Performance analysis
│   ├── ARDUINO.md              # Arduino setup guide
│   └── QUICK_REFERENCE.md      # Command reference
│   │
│   └── [TECHNICAL]             # Technical documentation
│   ├── ARCHITECTURE.md         # System architecture & design decisions
│   ├── TECHNICAL_DEEP_DIVE.md  # Advanced concepts
│   ├── ENHANCEMENTS.md         # Script enhancements
│   └── PROJECT_STRUCTURE.md    # This file
│
└── MobileNetV2.mlpackage/       # CoreML model (generated)
```

## File Categories

### Core Scripts (All Used)
- **Model Conversion**: `convert_model.py`
- **Benchmarking**: `benchmark.py`, `benchmark_power.py`, `unified_benchmark.py`
- **Power Tools**: `power_logger.py`, `power_visualizer.py`, `app_power_analyzer.py`, `analyze_power_data.py`
- **Testing**: `test_components.py`
- **Hardware**: `arduino_power_receiver.ino`

### Documentation
- **Public/Portfolio**: PERFORMANCE.md, ARDUINO.md, QUICK_REFERENCE.md
- **Technical**: ARCHITECTURE.md, TECHNICAL_DEEP_DIVE.md, ENHANCEMENTS.md, PROJECT_STRUCTURE.md

## Usage

All scripts are in the `scripts/` directory. Use them with:
```bash
python3 scripts/script_name.py
```

All documentation is in the `docs/` directory, organized by audience.

