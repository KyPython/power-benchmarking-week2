#!/bin/bash
# Power Benchmarking Suite - Dynamic Code Validation
# Checks for hardcoded values that should be configurable

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "${BLUE}=== Dynamic Code Validation ===${NC}\n"

VIOLATIONS=0
FILES_CHECKED=0

# Find all Python files
PYTHON_FILES=$(find power_benchmarking_suite scripts -name "*.py" -type f 2>/dev/null | grep -v __pycache__ | grep -v test | sort)

if [ -z "$PYTHON_FILES" ]; then
    echo "${YELLOW}⚠ No Python files found${NC}"
    exit 0
fi

echo "Checking for hardcoded values...\n"

for file in $PYTHON_FILES; do
    FILES_CHECKED=$((FILES_CHECKED + 1))
    
    # Skip test files
    if [[ "$file" == *"test"* ]] || [[ "$file" == *"__pycache__"* ]]; then
        continue
    fi
    
    # Check for hardcoded URLs (http:// or https://)
    HARDCODED_URLS=$(grep -n "https\?://[^\"' ]*" "$file" 2>/dev/null | grep -v "localhost" | grep -v "127.0.0.1" | grep -v "example.com" | grep -v "test" || true)
    if [ -n "$HARDCODED_URLS" ]; then
        echo "${RED}✗${NC} ${file}: Hardcoded URLs found:"
        echo "$HARDCODED_URLS" | sed 's/^/  /'
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
    
    # Check for hardcoded API keys (patterns like sk_, pk_, key=, api_key=)
    HARDCODED_KEYS=$(grep -n -i "\(sk_\|pk_\|api_key\s*=\s*['\"][^'\"]*['\"]\|secret\s*=\s*['\"][^'\"]*['\"]\)" "$file" 2>/dev/null | grep -v "os.getenv\|os.environ\|process.env\|config.get" || true)
    if [ -n "$HARDCODED_KEYS" ]; then
        echo "${RED}✗${NC} ${file}: Potential hardcoded API keys found:"
        echo "$HARDCODED_KEYS" | sed 's/^/  /'
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
    
    # Check for magic numbers (numbers > 10 that aren't in obvious contexts)
    # This is a simplified check - focuses on suspicious patterns
    MAGIC_NUMBERS=$(grep -n -E "=\s*[0-9]{2,}|\([0-9]{2,}\)" "$file" 2>/dev/null | grep -v "os.getenv\|os.environ\|process.env\|config.get\|#\|test\|__" | grep -v "\.py:" || true)
    if [ -n "$MAGIC_NUMBERS" ]; then
        # Filter out common exceptions (ports, common timeouts, etc.)
        FILTERED=$(echo "$MAGIC_NUMBERS" | grep -v -E "(3000|3030|5000|8000|8080|9000|115200|500|1000|2000|3000|5000|10000)" || true)
        if [ -n "$FILTERED" ]; then
            echo "${YELLOW}⚠${NC} ${file}: Potential magic numbers (review recommended):"
            echo "$FILTERED" | head -5 | sed 's/^/  /'
        fi
    fi
    
    # Check for hardcoded file paths (absolute paths starting with /)
    HARDCODED_PATHS=$(grep -n "['\"]/[^'\"]*['\"]" "$file" 2>/dev/null | grep -v "os.getenv\|os.environ\|process.env\|config.get\|__file__\|__name__\|#\|test" | grep -v "localhost\|127.0.0.1" || true)
    if [ -n "$HARDCODED_PATHS" ]; then
        # Filter out common exceptions (system paths, etc.)
        FILTERED=$(echo "$HARDCODED_PATHS" | grep -v -E "(/usr/|/etc/|/var/|/tmp/|/dev/|/sys/|/proc/)" || true)
        if [ -n "$FILTERED" ]; then
            echo "${YELLOW}⚠${NC} ${file}: Potential hardcoded file paths (review recommended):"
            echo "$FILTERED" | head -5 | sed 's/^/  /'
        fi
    fi
done

echo ""
if [ "$VIOLATIONS" -eq 0 ]; then
    echo "${GREEN}✅ Dynamic code validation passed${NC}"
    echo "   Checked ${FILES_CHECKED} files"
    exit 0
else
    echo "${RED}✗ Dynamic code validation failed: ${VIOLATIONS} violation(s)${NC}"
    echo "   Checked ${FILES_CHECKED} files"
    exit 1
fi


