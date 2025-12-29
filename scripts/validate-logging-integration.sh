#!/bin/bash
# Power Benchmarking Suite - Logging Integration Validation
# Checks that all logging uses structured logging instead of print()

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "${BLUE}=== Logging Integration Validation ===${NC}\n"

VIOLATIONS=0
FILES_CHECKED=0

# Find all Python files
PYTHON_FILES=$(find power_benchmarking_suite scripts -name "*.py" -type f 2>/dev/null | grep -v __pycache__ | grep -v test | sort)

if [ -z "$PYTHON_FILES" ]; then
    echo "${YELLOW}⚠ No Python files found${NC}"
    exit 0
fi

echo "Checking for print() statements and logging usage...\n"

for file in $PYTHON_FILES; do
    FILES_CHECKED=$((FILES_CHECKED + 1))
    
    # Skip test files and scripts (they may legitimately use print)
    if [[ "$file" == *"test"* ]] || [[ "$file" == *"__pycache__"* ]] || [[ "$file" == "scripts/"* ]]; then
        continue
    fi
    
    # Check for print() statements (excluding test files and scripts)
    PRINT_STATEMENTS=$(grep -n "print(" "$file" 2>/dev/null | grep -v "#" | grep -v "logger.debug\|logger.info\|logger.warning\|logger.error" || true)
    if [ -n "$PRINT_STATEMENTS" ]; then
        echo "${RED}✗${NC} ${file}: print() statements found (should use logging):"
        echo "$PRINT_STATEMENTS" | sed 's/^/  /'
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
    
    # Check if file uses logging but doesn't import it
    HAS_LOGGING_CALLS=$(grep -c "logging\." "$file" 2>/dev/null | tr -d ' ' || echo "0")
    HAS_LOGGER_CALLS=$(grep -c "logger\." "$file" 2>/dev/null | tr -d ' ' || echo "0")
    if [ -n "$HAS_LOGGING_CALLS" ] && [ -n "$HAS_LOGGER_CALLS" ] && ([ "$HAS_LOGGING_CALLS" -gt 0 ] 2>/dev/null || [ "$HAS_LOGGER_CALLS" -gt 0 ] 2>/dev/null); then
        HAS_LOGGING_IMPORT=$(grep -c "import logging\|from logging\|logger\s*=" "$file" 2>/dev/null | tr -d ' ' || echo "0")
        if [ -n "$HAS_LOGGING_IMPORT" ] && [ "$HAS_LOGGING_IMPORT" -eq 0 ] 2>/dev/null; then
            echo "${YELLOW}⚠${NC} ${file}: Uses logging but may not import it properly"
        fi
    fi
done

echo ""
if [ "$VIOLATIONS" -eq 0 ]; then
    echo "${GREEN}✅ Logging integration validation passed${NC}"
    echo "   Checked ${FILES_CHECKED} files"
    exit 0
else
    echo "${RED}✗ Logging integration validation failed: ${VIOLATIONS} violation(s)${NC}"
    echo "   Checked ${FILES_CHECKED} files"
    echo ""
    echo "${YELLOW}💡 Tip: Replace print() with logger.info() or appropriate logging level${NC}"
    exit 1
fi

