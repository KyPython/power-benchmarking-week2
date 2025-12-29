# Release Command Reference

Quick reference for releasing the Power Benchmarking Suite.

## Prerequisites

```bash
# Install build tools
pip install build twine

# Verify you're logged into PyPI (if needed)
# twine login  # For first-time setup
```

## Automated Release (Recommended)

```bash
# Run the release script
./scripts/release.sh
```

The script will guide you through:
1. Pre-release checks
2. Building distributions
3. Git operations (commit, tag, push)
4. PyPI upload (TestPyPI first, then production)

## Manual Release Steps

### 1. Pre-Release Checks

```bash
# Run validations
make validate

# Run tests
pytest tests/ -v

# Check installation
pip install -e .
power-benchmark --version
```

### 2. Update Version (if needed)

```bash
# Update in setup.py
# Update in power_benchmarking_suite/__init__.py
# Update CHANGELOG.md
```

### 3. Build Distributions

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build
python -m build

# Verify
twine check dist/*
```

### 4. Test Installation Locally

```bash
# Install from local build
pip install dist/power_benchmarking_suite-*.whl

# Test
power-benchmark --version
power-benchmark --help
```

### 5. Test on TestPyPI

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ power-benchmarking-suite
```

### 6. Git Operations

```bash
# Commit all changes
git add .
git commit -m "Release v1.0.0: Initial public release"

# Create tag
git tag v1.0.0

# Push to GitHub
git push origin main
git push origin v1.0.0
```

### 7. Publish to PyPI

```bash
# Upload to production PyPI
twine upload dist/*
```

### 8. Create GitHub Release

1. Go to: https://github.com/KyPython/power-benchmarking-week2/releases/new
2. Tag: `v1.0.0`
3. Title: `v1.0.0 - Initial Public Release`
4. Description: Copy from `RELEASE_NOTES.md`
5. Publish release

## Post-Release

### Verify Installation

```bash
# Uninstall local version
pip uninstall power-benchmarking-suite -y

# Install from PyPI
pip install power-benchmarking-suite

# Test
power-benchmark --version
power-benchmark --help
```

### Monitor

- Check PyPI: https://pypi.org/project/power-benchmarking-suite/
- Check GitHub: https://github.com/KyPython/power-benchmarking-week2/releases
- Monitor issues and feedback

## Troubleshooting

### Build Fails

```bash
# Check Python version
python --version  # Should be 3.8+

# Check setuptools
pip install --upgrade setuptools wheel

# Clean and rebuild
rm -rf dist/ build/ *.egg-info
python -m build
```

### Upload Fails

```bash
# Check PyPI credentials
# Ensure PYPI_API_TOKEN is set (for GitHub Actions)
# Or use: twine login

# Check package name availability
# Visit: https://pypi.org/project/power-benchmarking-suite/
```

### Installation Issues

```bash
# Clear pip cache
pip cache purge

# Install with verbose output
pip install -v power-benchmarking-suite

# Check dependencies
pip check
```

## Version Bumping

For future releases:

```bash
# Update version in:
# 1. setup.py
# 2. power_benchmarking_suite/__init__.py
# 3. CHANGELOG.md
# 4. RELEASE_NOTES.md (create new)
```

## Rollback

If a release has issues:

```bash
# Delete PyPI release (if possible)
# Note: PyPI doesn't allow deletion, but you can yank it:
twine upload --skip-existing dist/*  # Won't work for deletion

# Create a new patch release
# Update version to 1.0.1
# Fix issues
# Release again
```


