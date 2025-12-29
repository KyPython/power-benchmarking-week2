# Release Checklist - v1.0.0

## Pre-Release Checklist

### ✅ Code Quality
- [x] All code quality validations pass (`make validate`)
- [x] No critical security issues (bandit scan)
- [x] All tests pass (`pytest`)
- [x] Code formatted (black)
- [x] Linting passes (flake8)

### ✅ Documentation
- [x] README.md is complete and accurate
- [x] All features documented
- [x] Installation instructions clear
- [x] Quick start guide available
- [x] API documentation complete

### ✅ Configuration
- [x] Version number updated (1.0.0)
- [x] setup.py configured correctly
- [x] requirements.txt complete
- [x] LICENSE file present (MIT)
- [x] .gitignore excludes sensitive files

### ✅ PyPI Preparation
- [x] Package name available on PyPI
- [x] setup.py includes all metadata
- [x] Long description (README) formatted for PyPI
- [x] Classifiers are correct
- [x] Entry points configured

### ✅ GitHub Preparation
- [x] All changes committed
- [x] CHANGELOG.md created
- [x] Release notes prepared
- [x] GitHub Actions workflows configured
- [x] No sensitive data in repository

### ✅ Testing
- [x] Local installation works (`pip install -e .`)
- [x] CLI commands work (`power-benchmark --help`)
- [x] All subcommands functional
- [x] Integration tests pass

## Release Steps

### Step 1: Final Verification
```bash
# Run all validations
make validate

# Run tests
pytest tests/ -v

# Check installation
pip install -e .
power-benchmark --version
power-benchmark --help
```

### Step 2: Update Version (if needed)
- Update `setup.py` version
- Update `power_benchmarking_suite/__init__.py` version
- Update `CHANGELOG.md`

### Step 3: Commit to GitHub
```bash
git add .
git commit -m "Release v1.0.0: Initial public release"
git tag v1.0.0
git push origin main
git push origin v1.0.0
```

### Step 4: Build for PyPI
```bash
# Install build tools
pip install build twine

# Build distributions
python -m build

# Verify build
twine check dist/*
```

### Step 5: Test PyPI Upload (TestPyPI first)
```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ power-benchmarking-suite
```

### Step 6: Publish to PyPI
```bash
# Upload to PyPI (production)
twine upload dist/*
```

### Step 7: Create GitHub Release
1. Go to GitHub repository
2. Click "Releases" → "Create a new release"
3. Tag: `v1.0.0`
4. Title: `v1.0.0 - Initial Public Release`
5. Description: Copy from `RELEASE_NOTES.md`
6. Publish release

### Step 8: Announcement
- [ ] Update project website (if applicable)
- [ ] Post on social media
- [ ] Share in relevant communities
- [ ] Update documentation links

## Post-Release

### Monitor
- [ ] Check PyPI download stats
- [ ] Monitor GitHub issues
- [ ] Check for installation problems
- [ ] Review user feedback

### Next Steps
- [ ] Plan v1.1.0 features
- [ ] Address any critical bugs
- [ ] Update roadmap


