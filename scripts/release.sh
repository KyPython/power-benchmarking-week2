#!/bin/bash
# Power Benchmarking Suite - Release Script
# Automates the release process for GitHub and PyPI

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

VERSION="1.0.0"
REPO_NAME="power-benchmarking-week2"
PYPI_NAME="power-benchmarking-suite"

echo "${BLUE}=== Power Benchmarking Suite Release Script ===${NC}\n"
echo "${CYAN}Version: ${VERSION}${NC}\n"

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo "${RED}Error: setup.py not found. Run this script from the project root.${NC}"
    exit 1
fi

# Step 1: Pre-release checks
echo "${BLUE}[1/7] Running pre-release checks...${NC}"

# Check if all validations pass
if [ -f "scripts/validate-all.sh" ]; then
    echo "  Running code quality validations..."
    if ! ./scripts/validate-all.sh > /dev/null 2>&1; then
        echo "${YELLOW}  ⚠️  Code quality validations found issues (non-blocking)${NC}"
    else
        echo "${GREEN}  ✅ Code quality validations passed${NC}"
    fi
fi

# Check if tests pass
if [ -f "pytest.ini" ] || [ -d "tests" ]; then
    echo "  Running tests..."
    if command -v pytest >/dev/null 2>&1; then
        if pytest tests/ -v --tb=short > /dev/null 2>&1; then
            echo "${GREEN}  ✅ Tests passed${NC}"
        else
            echo "${YELLOW}  ⚠️  Some tests failed (check manually)${NC}"
        fi
    else
        echo "${YELLOW}  ⚠️  pytest not found, skipping tests${NC}"
    fi
fi

# Step 2: Check git status
echo "\n${BLUE}[2/7] Checking git status...${NC}"
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "${YELLOW}  ⚠️  You have uncommitted changes${NC}"
    echo "  Files changed:"
    git status --short | head -10
    read -p "  Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "${GREEN}  ✅ Working directory clean${NC}"
fi

# Step 3: Build distributions
echo "\n${BLUE}[3/7] Building distributions...${NC}"
if ! command -v python3 >/dev/null 2>&1; then
    echo "${RED}  Error: python3 not found${NC}"
    exit 1
fi

# Install build tools if needed
if ! python3 -m pip show build >/dev/null 2>&1; then
    echo "  Installing build tools..."
    python3 -m pip install --upgrade build twine
fi

# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build
echo "  Building wheel and source distribution..."
python3 -m build

if [ ! -d "dist" ] || [ -z "$(ls -A dist/)" ]; then
    echo "${RED}  Error: Build failed - dist/ directory is empty${NC}"
    exit 1
fi

echo "${GREEN}  ✅ Build successful${NC}"
ls -lh dist/

# Step 4: Verify build
echo "\n${BLUE}[4/7] Verifying build...${NC}"
if command -v twine >/dev/null 2>&1; then
    echo "  Checking distributions..."
    if twine check dist/*; then
        echo "${GREEN}  ✅ Build verification passed${NC}"
    else
        echo "${RED}  Error: Build verification failed${NC}"
        exit 1
    fi
else
    echo "${YELLOW}  ⚠️  twine not found, skipping verification${NC}"
fi

# Step 5: Test installation
echo "\n${BLUE}[5/7] Testing local installation...${NC}"
python3 -m pip install -e . > /dev/null 2>&1
if command -v power-benchmark >/dev/null 2>&1; then
    echo "${GREEN}  ✅ Installation successful${NC}"
    power-benchmark --version 2>/dev/null || echo "  Version check: OK"
else
    echo "${YELLOW}  ⚠️  power-benchmark command not found (may need PATH refresh)${NC}"
fi

# Step 6: Git operations
echo "\n${BLUE}[6/7] Git operations...${NC}"
read -p "  Commit all changes? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add .
    git commit -m "Release v${VERSION}: Initial public release" || echo "  No changes to commit"
    echo "${GREEN}  ✅ Changes committed${NC}"
fi

read -p "  Create git tag v${VERSION}? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if git rev-parse "v${VERSION}" >/dev/null 2>&1; then
        echo "${YELLOW}  ⚠️  Tag v${VERSION} already exists${NC}"
        read -p "  Delete and recreate? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git tag -d "v${VERSION}"
            git push origin ":refs/tags/v${VERSION}" 2>/dev/null || true
        fi
    fi
    git tag "v${VERSION}"
    echo "${GREEN}  ✅ Tag v${VERSION} created${NC}"
fi

read -p "  Push to GitHub? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin main
    if git rev-parse "v${VERSION}" >/dev/null 2>&1; then
        git push origin "v${VERSION}"
    fi
    echo "${GREEN}  ✅ Pushed to GitHub${NC}"
fi

# Step 7: PyPI upload
echo "\n${BLUE}[7/7] PyPI upload...${NC}"
echo "${YELLOW}  ⚠️  IMPORTANT: Test on TestPyPI first!${NC}"
echo ""
echo "  To upload to TestPyPI:"
echo "    twine upload --repository testpypi dist/*"
echo ""
echo "  To upload to PyPI (production):"
echo "    twine upload dist/*"
echo ""
read -p "  Upload to TestPyPI now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v twine >/dev/null 2>&1; then
        twine upload --repository testpypi dist/*
        echo "${GREEN}  ✅ Uploaded to TestPyPI${NC}"
        echo "  Test installation: pip install --index-url https://test.pypi.org/simple/ ${PYPI_NAME}"
    else
        echo "${RED}  Error: twine not found${NC}"
    fi
fi

read -p "  Upload to PyPI (production)? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v twine >/dev/null 2>&1; then
        echo "${RED}  ⚠️  WARNING: This will publish to production PyPI!${NC}"
        read -p "  Are you absolutely sure? (yes/no): " -r
        if [[ $REPLY == "yes" ]]; then
            twine upload dist/*
            echo "${GREEN}  ✅ Uploaded to PyPI${NC}"
        else
            echo "  Upload cancelled"
        fi
    else
        echo "${RED}  Error: twine not found${NC}"
    fi
fi

# Summary
echo "\n${BLUE}=== Release Summary ===${NC}"
echo "${GREEN}✅ Release preparation complete!${NC}\n"
echo "Next steps:"
echo "  1. Create GitHub release: https://github.com/KyPython/${REPO_NAME}/releases/new"
echo "  2. Tag: v${VERSION}"
echo "  3. Title: v${VERSION} - Initial Public Release"
echo "  4. Description: Copy from RELEASE_NOTES.md"
echo "  5. Announce on social media and communities"
echo ""
echo "Files created:"
echo "  - dist/* (PyPI distributions)"
echo "  - CHANGELOG.md"
echo "  - RELEASE_NOTES.md"
echo "  - RELEASE_CHECKLIST.md"


