# 🚀 Release Guide - v1.0.0

## Quick Start (Fastest Path to Release)

### Option 1: Automated Script (Recommended)

```bash
cd /Users/ky/power-benchmarking-week2
./scripts/release.sh
```

The script will guide you through everything interactively.

### Option 2: Manual Steps

Follow the steps below in order.

---

## Step-by-Step Release Process

### 1️⃣ Pre-Release Verification (5 min)

```bash
# Run validations
make validate

# Run tests  
pytest tests/ -v

# Test CLI
power-benchmark --version
power-benchmark --help
```

### 2️⃣ Set Up PyPI (One-time, 5 min)

**Create PyPI Account:**
- Visit: https://pypi.org/account/register/
- Verify email

**Create API Token:**
- Visit: https://pypi.org/manage/account/token/
- Click "Add API token"
- Name: `power-benchmarking-suite`
- Copy token (starts with `pypi-`)

**Add to GitHub Secrets:**
- Visit: https://github.com/KyPython/power-benchmarking-week2/settings/secrets/actions
- New secret: `PYPI_API_TOKEN`
- Paste token
- Save

### 3️⃣ Build Package (2 min)

```bash
# Install build tools
pip install build twine

# Build
python3 -m build

# Verify
twine check dist/*
ls -lh dist/
```

### 4️⃣ Test on TestPyPI (5 min)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ power-benchmarking-suite
power-benchmark --version
```

### 5️⃣ Commit & Tag (2 min)

```bash
# Review changes
git status

# Commit
git add .
git commit -m "Release v1.0.0: Initial public release

Features:
- Unified CLI with 6 subcommands
- Real-time CoreML power monitoring
- Energy Gap Framework
- Thermal throttling prediction
- Sustainability ROI calculations
- Statistical attribution engine
- Comprehensive documentation"

# Tag
git tag v1.0.0

# Push
git push origin main
git push origin v1.0.0
```

### 6️⃣ Publish to PyPI (2 min)

```bash
# Upload to production PyPI
twine upload dist/*
```

### 7️⃣ Create GitHub Release (5 min)

1. Visit: https://github.com/KyPython/power-benchmarking-week2/releases/new
2. **Tag**: `v1.0.0`
3. **Title**: `v1.0.0 - Initial Public Release`
4. **Description**: Copy from `RELEASE_NOTES.md`
5. Click **"Publish release"**

### 8️⃣ Verify (2 min)

```bash
# Uninstall local
pip uninstall power-benchmarking-suite -y

# Install from PyPI
pip install power-benchmarking-suite

# Test
power-benchmark --version
power-benchmark --help
```

### 9️⃣ Announce (15 min)

**Twitter/X:**
```
🚀 Just released Power Benchmarking Suite v1.0.0!

The first tool to combine CoreML inference with real-time power monitoring on Apple Silicon.

✨ 57x speedup
⚡ 4.5x energy improvement  
🌱 Sustainability ROI

pip install power-benchmarking-suite

#AppleSilicon #CoreML #EnergyEfficiency
```

**Hacker News:**
- Submit as "Show HN"
- Title: "Show HN: Power Benchmarking Suite - Real-time CoreML power monitoring for Apple Silicon"

**Reddit:**
- r/apple: "Power Benchmarking Suite - Monitor CoreML power consumption in real-time"
- r/MachineLearning: "New tool for optimizing CoreML models on Apple Silicon"
- r/Python: "Power Benchmarking Suite v1.0.0 - Python CLI for Apple Silicon power monitoring"

---

## Files Ready for Release

✅ **Documentation:**
- `README.md` - Complete
- `CHANGELOG.md` - v1.0.0 documented
- `RELEASE_NOTES.md` - Public announcement
- `QUICK_START_GUIDE.md` - User onboarding

✅ **Configuration:**
- `setup.py` - Complete with metadata
- `requirements.txt` - All dependencies
- `LICENSE` - MIT License
- `.code-quality-config.json` - Quality rules

✅ **Automation:**
- `scripts/release.sh` - Automated release
- `.github/workflows/publish.yml` - PyPI publishing
- `Makefile` - Development commands

✅ **Code:**
- All features implemented
- Tests passing
- Quality validations in place

---

## Checklist

- [ ] Pre-release verification passes
- [ ] PyPI account created
- [ ] PyPI API token created
- [ ] GitHub secret `PYPI_API_TOKEN` added
- [ ] Build successful (`python3 -m build`)
- [ ] Tested on TestPyPI
- [ ] All changes committed
- [ ] Git tag `v1.0.0` created
- [ ] Pushed to GitHub
- [ ] Published to PyPI
- [ ] GitHub release created
- [ ] Installation verified from PyPI
- [ ] Announcement posted

---

## Troubleshooting

### Build Fails
```bash
pip install --upgrade setuptools wheel build
python3 -m build
```

### Upload Fails
- Check PyPI token is correct
- Ensure package name is available
- Check network connection

### Installation Fails
```bash
pip cache purge
pip install -v power-benchmarking-suite
```

---

## Post-Release

### Monitor
- PyPI download stats: https://pypi.org/project/power-benchmarking-suite/
- GitHub issues: Monitor for user feedback
- Installation problems: Check error reports

### Next Steps
- Address any critical bugs
- Plan v1.1.0 features
- Update roadmap based on feedback

---

## 🎉 You're Ready!

**Total Time**: ~45 minutes

**Recommended**: Use `./scripts/release.sh` for automated release.

Good luck! 🚀
