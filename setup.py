#!/usr/bin/env python3
"""
Power Benchmarking Suite - Installation Package
Apple Silicon M2 Power Benchmarking Suite
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="power-benchmarking-suite",
    version="1.0.0",
    description="Comprehensive toolkit for monitoring, analyzing, and visualizing power consumption on Apple Silicon Macs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/KyPython/power-benchmarking-week2",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    py_modules=[
        # Core scripts as modules
        "scripts.convert_model",
        "scripts.benchmark",
        "scripts.benchmark_power",
        "scripts.unified_benchmark",
        "scripts.power_logger",
        "scripts.power_visualizer",
        "scripts.app_power_analyzer",
        "scripts.analyze_power_data",
        "scripts.energy_gap_framework",
    ],
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "power-benchmark=power_benchmarking_suite.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: MacOS",
    ],
    keywords="apple silicon, power monitoring, coreml, neural engine, benchmarking, energy efficiency",
    project_urls={
        "Documentation": "https://github.com/KyPython/power-benchmarking-week2#readme",
        "Source": "https://github.com/KyPython/power-benchmarking-week2",
        "Tracker": "https://github.com/KyPython/power-benchmarking-week2/issues",
    },
)

