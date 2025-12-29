# Production Deployment Guide

**Single Responsibility**: Complete guide for deploying Power Benchmarking Suite to production (GitHub releases, PyPI publishing).

---

## Quick Start

### Option 1: Automated Deployment (Recommended)

**Via GitHub Actions:**
1. Go to: https://github.com/KyPython/power-benchmarking-week2/actions/workflows/deploy.yml
2. Click "Run workflow"
3. Fill in:
   - Version: `1.0.0`
   - Deploy to GitHub: ✅
   - Deploy to TestPyPI: ✅ (test first)
   - Deploy to PyPI: ❌ (only after testing)
4. Click "Run workflow"

**Via Git Tag:**
```bash
git tag v1.0.0
git push origin v1.0.0
# Automatically triggers deployment workflow
```

### Option 2: Manual Deployment Script

```bash
# Deploy to GitHub only
DEPLOY_GITHUB=true ./scripts/deploy.sh

# Deploy to TestPyPI (test first!)
DEPLOY_TESTPYPI=true ./scripts/deploy.sh

# Deploy to PyPI (PRODUCTION - be careful!)
DEPLOY_PYPI=true ./scripts/deploy.sh

# Deploy everything
DEPLOY_GITHUB=true DEPLOY_TESTPYPI=true ./scripts/deploy.sh
```

---

## Pre-Deployment Checklist

### ✅ Code Quality
- [ ] All syntax errors fixed
- [ ] Code formatted (Black)
- [ ] Code quality validations pass
- [ ] No uncommitted changes (or intentional)

### ✅ Testing
- [ ] All tests passing
- [ ] Integration tests verified
- [ ] Manual testing completed

### ✅ Documentation
- [ ] README.md updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated

### ✅ Configuration
- [ ] Version set in `setup.py`
- [ ] Dependencies verified
- [ ] GitHub secrets configured (for PyPI)

---

## Deployment Steps

### 1. Pre-flight Checks

The deployment script automatically:
- ✅ Verifies project structure
- ✅ Checks Python version
- ✅ Validates git status
- ✅ Runs syntax checks
- ✅ Runs code quality validations

### 2. Build Package

```bash
# Automatic (via script)
python3 -m build

# Manual
pip install build twine
python -m build
twine check dist/*
```

**Output:**
- `dist/power_benchmarking_suite-X.X.X-py3-none-any.whl` (wheel)
- `dist/power-benchmarking-suite-X.X.X.tar.gz` (source)

### 3. Test Installation

```bash
# Test local installation
pip install -e .

# Test from TestPyPI
pip install --index-url https://test.pypi.org/simple/ power-benchmarking-suite

# Verify
power-benchmark --version
power-benchmark --help
```

### 4. Deploy to GitHub

**Automatic (via script):**
```bash
DEPLOY_GITHUB=true ./scripts/deploy.sh
```

**Manual:**
```bash
git tag v1.0.0
git push origin main
git push origin v1.0.0

# Create release at:
# https://github.com/KyPython/power-benchmarking-week2/releases/new
```

### 5. Deploy to TestPyPI (Recommended First)

**Via Script:**
```bash
DEPLOY_TESTPYPI=true ./scripts/deploy.sh
```

**Manual:**
```bash
twine upload --repository testpypi dist/*
```

**Test Installation:**
```bash
pip install --index-url https://test.pypi.org/simple/ power-benchmarking-suite
```

### 6. Deploy to PyPI (Production)

**⚠️ WARNING: This publishes to PRODUCTION!**

**Via Script:**
```bash
DEPLOY_PYPI=true ./scripts/deploy.sh
# Will ask for confirmation
```

**Manual:**
```bash
twine upload dist/*
```

**Required:**
- PyPI API token in `~/.pypirc` or `TWINE_PASSWORD` env var
- Or GitHub secret: `PYPI_API_TOKEN`

---

## CI/CD Integration

### GitHub Actions Workflow

**Location:** `.github/workflows/deploy.yml`

**Triggers:**
1. **Manual:** Workflow dispatch (with options)
2. **Automatic:** Push tag `v*.*.*`

**Features:**
- ✅ Pre-flight checks
- ✅ Test suite
- ✅ Build package
- ✅ Verify build
- ✅ Deploy to GitHub (create release)
- ✅ Deploy to TestPyPI (optional)
- ✅ Deploy to PyPI (optional, requires confirmation)
- ✅ Upload artifacts

**Usage:**
```bash
# Trigger via tag
git tag v1.0.0
git push origin v1.0.0

# Or manually via GitHub UI
# Actions → Deploy → Run workflow
```

---

## Configuration

### Environment Variables

```bash
# Version
export VERSION="1.0.0"

# Deployment targets
export DEPLOY_GITHUB="true"
export DEPLOY_TESTPYPI="true"
export DEPLOY_PYPI="false"  # Only after testing!
```

### GitHub Secrets

**Required for PyPI:**
- `PYPI_API_TOKEN` - Production PyPI token
- `TESTPYPI_API_TOKEN` - TestPyPI token (optional)

**Get tokens:**
1. Go to: https://pypi.org/manage/account/token/
2. Create API token
3. Add to GitHub Secrets: Settings → Secrets → Actions

---

## Production-Ready Features

### ✅ Core Features (Ready)
- Real-time power monitoring (ANE, CPU, GPU)
- CoreML Neural Engine benchmarking
- Data analysis and visualization
- Energy optimization tools
- Configuration management
- System validation

### ✅ CLI Commands (Ready)
- `power-benchmark monitor` - Real-time monitoring
- `power-benchmark analyze` - Data analysis
- `power-benchmark optimize` - Energy optimization
- `power-benchmark config` - Configuration
- `power-benchmark quickstart` - Onboarding
- `power-benchmark validate` - System check

### ⚠️ Optional Features (Graceful Degradation)
- Business automation (requires ReportLab)
- Marketing automation (requires Resend)
- Arduino integration (optional hardware)

**Note:** Core features work without optional dependencies.

---

## Post-Deployment

### 1. Verify Installation

```bash
pip install power-benchmarking-suite
power-benchmark --version
power-benchmark quickstart
```

### 2. Monitor

- Watch GitHub issues
- Monitor PyPI downloads
- Check CI/CD status
- Review error logs

### 3. Announce

- GitHub release notes
- Social media (Twitter, LinkedIn)
- Developer communities
- Documentation updates

---

## Troubleshooting

### Build Fails

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Install build tools
pip install --upgrade build twine

# Clean and rebuild
rm -rf dist/ build/ *.egg-info
python3 -m build
```

### PyPI Upload Fails

```bash
# Check credentials
twine check dist/*
twine upload --repository testpypi dist/*  # Test first

# Verify token
echo $TWINE_PASSWORD  # Should be set
```

### GitHub Release Fails

```bash
# Check permissions
gh auth status

# Verify tag exists
git tag -l

# Push tag manually
git push origin v1.0.0
```

---

## Repeatable Process

### For Each Release:

1. **Update Version**
   ```bash
   # Edit setup.py
   version="1.0.0"
   ```

2. **Run Deployment**
   ```bash
   # Test first
   DEPLOY_TESTPYPI=true ./scripts/deploy.sh
   
   # Then production
   DEPLOY_GITHUB=true DEPLOY_PYPI=true ./scripts/deploy.sh
   ```

3. **Verify**
   ```bash
   pip install power-benchmarking-suite==1.0.0
   power-benchmark --version
   ```

4. **Document**
   - Update CHANGELOG.md
   - Create GitHub release notes
   - Announce

---

## Quick Reference

```bash
# Full deployment (GitHub + TestPyPI)
DEPLOY_GITHUB=true DEPLOY_TESTPYPI=true ./scripts/deploy.sh

# Production deployment (GitHub + PyPI)
DEPLOY_GITHUB=true DEPLOY_PYPI=true ./scripts/deploy.sh

# GitHub only
DEPLOY_GITHUB=true ./scripts/deploy.sh

# Via CI/CD (push tag)
git tag v1.0.0 && git push origin v1.0.0
```

---

**See Also:**
- `scripts/deploy.sh` - Deployment script
- `.github/workflows/deploy.yml` - CI/CD workflow
- `docs/RELEASE_READY.md` - Release checklist


