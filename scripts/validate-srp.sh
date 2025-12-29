#!/bin/bash
# Power Benchmarking Suite - SRP (Single Responsibility Principle) Validation
# Checks that files, functions, and classes follow SRP

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "${BLUE}=== SRP Validation ===${NC}\n"

# Thresholds (from .code-quality-config.json)
MAX_FUNCTIONS_PER_FILE=20
MAX_METHODS_PER_CLASS=15
MAX_LINES_PER_FUNCTION=50
MAX_LINES_PER_FILE=500

VIOLATIONS=0
FILES_CHECKED=0

# Find all Python files
PYTHON_FILES=$(find power_benchmarking_suite scripts -name "*.py" -type f 2>/dev/null | grep -v __pycache__ | grep -v test | sort)

if [ -z "$PYTHON_FILES" ]; then
    echo "${YELLOW}⚠ No Python files found${NC}"
    exit 0
fi

echo "Checking ${#PYTHON_FILES[@]} Python files...\n"

for file in $PYTHON_FILES; do
    FILES_CHECKED=$((FILES_CHECKED + 1))
    
    # Skip test files
    if [[ "$file" == *"test"* ]] || [[ "$file" == *"__pycache__"* ]]; then
        continue
    fi
    
    # Check file length
    LINES=$(wc -l < "$file" 2>/dev/null | tr -d ' ' || echo "0")
    if [ -n "$LINES" ] && [ "$LINES" -gt "$MAX_LINES_PER_FILE" ] 2>/dev/null; then
        echo "${RED}✗${NC} ${file}: ${LINES} lines (max: ${MAX_LINES_PER_FILE})"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
    
    # Count functions in file
    FUNCTION_COUNT=$(grep -c "^def " "$file" 2>/dev/null | tr -d ' ' || echo "0")
    if [ -n "$FUNCTION_COUNT" ] && [ "$FUNCTION_COUNT" -gt "$MAX_FUNCTIONS_PER_FILE" ] 2>/dev/null; then
        echo "${RED}✗${NC} ${file}: ${FUNCTION_COUNT} functions (max: ${MAX_FUNCTIONS_PER_FILE})"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
    
    # Check function lengths (using awk to parse Python)
    # This is a simplified check - counts lines between function definitions
    awk '
    /^def / {
        if (func_start > 0) {
            func_lines = NR - func_start
            if (func_lines > '"$MAX_LINES_PER_FUNCTION"') {
                print "'"${RED}✗${NC}"' '"$file"': Function at line " func_start " has " func_lines " lines (max: '"$MAX_LINES_PER_FUNCTION"')"
                violations++
            }
        }
        func_start = NR
    }
    END {
        if (func_start > 0) {
            func_lines = NR - func_start + 1
            if (func_lines > '"$MAX_LINES_PER_FUNCTION"') {
                print "'"${RED}✗${NC}"' '"$file"': Function at line " func_start " has " func_lines " lines (max: '"$MAX_LINES_PER_FUNCTION"')"
                violations++
            }
        }
    }
    ' "$file" 2>/dev/null || true
    
    # Count methods in classes (simplified check)
    CLASS_COUNT=$(grep -c "^class " "$file" 2>/dev/null | tr -d ' ' || echo "0")
    if [ -n "$CLASS_COUNT" ] && [ "$CLASS_COUNT" -gt 0 ] 2>/dev/null; then
        # Note: Detailed method counting per class is complex in bash
        # This is a simplified check - manual review recommended for classes
        echo "${BLUE}ℹ${NC} ${file}: ${CLASS_COUNT} class(es) found (manual review for method count recommended)"
    fi
done

echo ""
if [ "$VIOLATIONS" -eq 0 ]; then
    echo "${GREEN}✅ SRP validation passed${NC}"
    echo "   Checked ${FILES_CHECKED} files"
    exit 0
else
    echo "${RED}✗ SRP validation failed: ${VIOLATIONS} violation(s)${NC}"
    echo "   Checked ${FILES_CHECKED} files"
    exit 1
fi

