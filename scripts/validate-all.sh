#!/bin/bash
# Power Benchmarking Suite - Run All Validations
# Runs all code quality validations and reports results

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo "${BLUE}=== Power Benchmarking Suite - Code Quality Validation ===${NC}\n"
echo "${CYAN}Running all validations...${NC}\n"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

FAILED=0
PASSED=0

# Run SRP validation
echo "${BLUE}[1/3] SRP Validation${NC}"
if "$SCRIPT_DIR/validate-srp.sh"; then
    echo "${GREEN}✅ SRP validation passed${NC}\n"
    PASSED=$((PASSED + 1))
else
    echo "${RED}✗ SRP validation failed${NC}\n"
    FAILED=$((FAILED + 1))
fi

# Run dynamic code validation
echo "${BLUE}[2/3] Dynamic Code Validation${NC}"
if "$SCRIPT_DIR/validate-dynamic-code.sh"; then
    echo "${GREEN}✅ Dynamic code validation passed${NC}\n"
    PASSED=$((PASSED + 1))
else
    echo "${RED}✗ Dynamic code validation failed${NC}\n"
    FAILED=$((FAILED + 1))
fi

# Run logging integration validation
echo "${BLUE}[3/3] Logging Integration Validation${NC}"
if "$SCRIPT_DIR/validate-logging-integration.sh"; then
    echo "${GREEN}✅ Logging integration validation passed${NC}\n"
    PASSED=$((PASSED + 1))
else
    echo "${RED}✗ Logging integration validation failed${NC}\n"
    FAILED=$((FAILED + 1))
fi

# Summary
echo "${BLUE}=== Validation Summary ===${NC}"
echo "${GREEN}Passed: ${PASSED}/3${NC}"
if [ "$FAILED" -gt 0 ]; then
    echo "${RED}Failed: ${FAILED}/3${NC}"
    echo ""
    echo "${RED}✗ Code quality validation failed${NC}"
    echo "${YELLOW}💡 Fix violations before committing${NC}"
    exit 1
else
    echo "${GREEN}✅ All validations passed!${NC}"
    exit 0
fi


