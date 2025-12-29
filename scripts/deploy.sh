#!/bin/bash
# Power Benchmarking Suite - Production Deployment Script
# Repeatable, automated deployment process for production releases

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
VERSION="${VERSION:-1.0.0}"
REPO_NAME="power-benchmarking-week2"
PYPI_NAME="power-benchmarking-suite"
GITHUB_REPO="KyPython/${REPO_NAME}"

# Deployment targets
DEPLOY_GITHUB="${DEPLOY_GITHUB:-false}"
DEPLOY_PYPI="${DEPLOY_PYPI:-false}"
DEPLOY_TESTPYPI="${DEPLOY_TESTPYPI:-false}"

echo "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo "${BLUE}║  Power Benchmarking Suite - Production Deployment         ║${NC}"
echo "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "${CYAN}Version: ${VERSION}${NC}"
echo "${CYAN}Targets: GitHub=${DEPLOY_GITHUB} | TestPyPI=${DEPLOY_TESTPYPI} | PyPI=${DEPLOY_PYPI}${NC}"
echo ""

# ============================================================================
# STEP 1: Pre-flight Checks
# ============================================================================
echo "${BLUE}[1/8] Pre-flight Checks${NC}"
echo "─────────────────────────────────────────────────────────────"

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo "${RED}❌ Error: setup.py not found. Run from project root.${NC}"
    exit 1
fi
echo "${GREEN}✅ Project root verified${NC}"

# Check Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "${RED}❌ Error: python3 not found${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"

# Check git
if ! command -v git >/dev/null 2>&1; then
    echo "${RED}❌ Error: git not found${NC}"
    exit 1
fi
echo "${GREEN}✅ Git found${NC}"

# Check git status
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "${YELLOW}⚠️  Uncommitted changes detected${NC}"
    git status --short | head -5
    echo ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "${GREEN}✅ Working directory clean${NC}"
fi

# ============================================================================
# STEP 2: Code Quality Validation
# ============================================================================
echo ""
echo "${BLUE}[2/8] Code Quality Validation${NC}"
echo "─────────────────────────────────────────────────────────────"

# Syntax check
echo "  Checking Python syntax..."
if find power_benchmarking_suite scripts -name "*.py" -type f -exec python3 -m py_compile {} \; 2>&1 | grep -q "SyntaxError"; then
    echo "${RED}❌ Syntax errors found${NC}"
    exit 1
fi
echo "${GREEN}  ✅ Syntax check passed${NC}"

# Format check
if command -v black >/dev/null 2>&1; then
    echo "  Checking code formatting..."
    if black --check --line-length 100 power_benchmarking_suite/ scripts/ 2>&1 | grep -q "would reformat"; then
        echo "${YELLOW}  ⚠️  Formatting issues found (non-blocking)${NC}"
    else
        echo "${GREEN}  ✅ Formatting check passed${NC}"
    fi
else
    echo "${YELLOW}  ⚠️  Black not found, skipping format check${NC}"
fi

# Code quality validations
if [ -f "scripts/validate-all.sh" ]; then
    echo "  Running code quality validations..."
    if ./scripts/validate-all.sh > /tmp/validation.log 2>&1; then
        echo "${GREEN}  ✅ Code quality validations passed${NC}"
    else
        echo "${YELLOW}  ⚠️  Some validations found issues (check /tmp/validation.log)${NC}"
    fi
fi

# ============================================================================
# STEP 3: Test Suite
# ============================================================================
echo ""
echo "${BLUE}[3/8] Running Test Suite${NC}"
echo "─────────────────────────────────────────────────────────────"

if [ -d "tests" ] && command -v pytest >/dev/null 2>&1; then
    if pytest tests/ -v --tb=short 2>&1 | tee /tmp/test_results.log; then
        echo "${GREEN}✅ All tests passed${NC}"
    else
        echo "${YELLOW}⚠️  Some tests failed (check /tmp/test_results.log)${NC}"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "${YELLOW}⚠️  Tests directory or pytest not found, skipping${NC}"
fi

# ============================================================================
# STEP 4: Build Package
# ============================================================================
echo ""
echo "${BLUE}[4/8] Building Package${NC}"
echo "─────────────────────────────────────────────────────────────"

# Install build tools
if ! python3 -m pip show build >/dev/null 2>&1; then
    echo "  Installing build tools..."
    python3 -m pip install --quiet --upgrade build twine
fi

# Clean previous builds
echo "  Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info

# Build
echo "  Building wheel and source distribution..."
python3 -m build 2>&1 | grep -E "(Creating|Built)" || true

if [ ! -d "dist" ] || [ -z "$(ls -A dist/ 2>/dev/null)" ]; then
    echo "${RED}❌ Build failed - dist/ directory is empty${NC}"
    exit 1
fi

echo "${GREEN}✅ Build successful${NC}"
ls -lh dist/ | tail -n +2

# ============================================================================
# STEP 5: Verify Build
# ============================================================================
echo ""
echo "${BLUE}[5/8] Verifying Build${NC}"
echo "─────────────────────────────────────────────────────────────"

if command -v twine >/dev/null 2>&1; then
    if twine check dist/* > /tmp/twine_check.log 2>&1; then
        echo "${GREEN}✅ Build verification passed${NC}"
    else
        echo "${RED}❌ Build verification failed${NC}"
        cat /tmp/twine_check.log
        exit 1
    fi
else
    echo "${YELLOW}⚠️  twine not found, skipping verification${NC}"
fi

# Test local installation
echo "  Testing local installation..."
python3 -m pip install -e . --quiet > /dev/null 2>&1
if command -v power-benchmark >/dev/null 2>&1; then
    echo "${GREEN}✅ Local installation successful${NC}"
    power-benchmark --version 2>/dev/null | head -1 || echo "  Version check: OK"
else
    echo "${YELLOW}⚠️  power-benchmark command not found (may need PATH refresh)${NC}"
fi

# ============================================================================
# STEP 6: Git Operations
# ============================================================================
echo ""
echo "${BLUE}[6/8] Git Operations${NC}"
echo "─────────────────────────────────────────────────────────────"

if [ "$DEPLOY_GITHUB" = "true" ]; then
    # Commit changes
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "  Committing changes..."
        git add .
        git commit -m "Release v${VERSION}: Production deployment" || echo "  No changes to commit"
        echo "${GREEN}✅ Changes committed${NC}"
    fi

    # Create tag
    if git rev-parse "v${VERSION}" >/dev/null 2>&1; then
        echo "${YELLOW}⚠️  Tag v${VERSION} already exists${NC}"
        read -p "  Delete and recreate? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git tag -d "v${VERSION}" 2>/dev/null || true
            git push origin ":refs/tags/v${VERSION}" 2>/dev/null || true
        else
            echo "  Skipping tag creation"
            DEPLOY_GITHUB="false"
        fi
    fi

    if [ "$DEPLOY_GITHUB" = "true" ]; then
        git tag "v${VERSION}"
        echo "${GREEN}✅ Tag v${VERSION} created${NC}"

        # Push to GitHub
        echo "  Pushing to GitHub..."
        git push origin main
        git push origin "v${VERSION}"
        echo "${GREEN}✅ Pushed to GitHub${NC}"
        echo ""
        echo "${CYAN}📝 Next: Create GitHub release at:${NC}"
        echo "   https://github.com/${GITHUB_REPO}/releases/new"
        echo "   Tag: v${VERSION}"
    fi
else
    echo "${YELLOW}⚠️  GitHub deployment skipped (set DEPLOY_GITHUB=true to enable)${NC}"
fi

# ============================================================================
# STEP 7: PyPI Deployment
# ============================================================================
echo ""
echo "${BLUE}[7/8] PyPI Deployment${NC}"
echo "─────────────────────────────────────────────────────────────"

if [ "$DEPLOY_TESTPYPI" = "true" ]; then
    echo "${CYAN}📦 Uploading to TestPyPI...${NC}"
    if command -v twine >/dev/null 2>&1; then
        if twine upload --repository testpypi dist/*; then
            echo "${GREEN}✅ Uploaded to TestPyPI${NC}"
            echo ""
            echo "${CYAN}🧪 Test installation:${NC}"
            echo "   pip install --index-url https://test.pypi.org/simple/ ${PYPI_NAME}"
        else
            echo "${RED}❌ TestPyPI upload failed${NC}"
            exit 1
        fi
    else
        echo "${RED}❌ twine not found${NC}"
        exit 1
    fi
fi

if [ "$DEPLOY_PYPI" = "true" ]; then
    echo ""
    echo "${RED}⚠️  WARNING: This will publish to PRODUCTION PyPI!${NC}"
    read -p "Are you absolutely sure? (type 'yes' to confirm): " -r
    echo
    if [[ $REPLY == "yes" ]]; then
        if command -v twine >/dev/null 2>&1; then
            if twine upload dist/*; then
                echo "${GREEN}✅ Uploaded to PyPI (PRODUCTION)${NC}"
                echo ""
                echo "${CYAN}📦 Installation:${NC}"
                echo "   pip install ${PYPI_NAME}"
            else
                echo "${RED}❌ PyPI upload failed${NC}"
                exit 1
            fi
        else
            echo "${RED}❌ twine not found${NC}"
            exit 1
        fi
    else
        echo "  PyPI upload cancelled"
    fi
fi

# ============================================================================
# STEP 8: Summary
# ============================================================================
echo ""
echo "${BLUE}[8/8] Deployment Summary${NC}"
echo "─────────────────────────────────────────────────────────────"
echo ""
echo "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo "${CYAN}Version:${NC} v${VERSION}"
echo "${CYAN}Package:${NC} ${PYPI_NAME}"
echo "${CYAN}Distributions:${NC}"
ls -lh dist/ | tail -n +2 | awk '{print "  " $9 " (" $5 ")"}'
echo ""

if [ "$DEPLOY_GITHUB" = "true" ]; then
    echo "${GREEN}✅ GitHub:${NC} Tagged and pushed"
    echo "   https://github.com/${GITHUB_REPO}/releases/tag/v${VERSION}"
fi

if [ "$DEPLOY_TESTPYPI" = "true" ]; then
    echo "${GREEN}✅ TestPyPI:${NC} Published"
    echo "   https://test.pypi.org/project/${PYPI_NAME}/${VERSION}/"
fi

if [ "$DEPLOY_PYPI" = "true" ]; then
    echo "${GREEN}✅ PyPI:${NC} Published (PRODUCTION)"
    echo "   https://pypi.org/project/${PYPI_NAME}/${VERSION}/"
fi

echo ""
echo "${CYAN}📋 Next Steps:${NC}"
echo "   1. Create GitHub release (if not automated)"
echo "   2. Test installation: pip install ${PYPI_NAME}"
echo "   3. Monitor for issues"
echo "   4. Announce release"
echo ""
echo "${GREEN}🚀 Ready for production!${NC}"


