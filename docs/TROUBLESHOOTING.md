# Troubleshooting Guide

## Common Issues

### Permission Errors

**Problem**: `powermetrics requires sudo privileges`

**Solution**:
```bash
# Run with sudo
sudo power-benchmark monitor --test 30

# Or configure passwordless sudo (advanced)
sudo visudo
# Add: your_username ALL=(ALL) NOPASSWD: /usr/bin/powermetrics
```

### Syntax Errors

**Problem**: `IndentationError` or `SyntaxError`

**Solution**:
```bash
# Check syntax
python3 -m py_compile scripts/unified_benchmark.py

# Fix formatting
black scripts/unified_benchmark.py
```

### Import Errors

**Problem**: `ModuleNotFoundError`

**Solution**:
```bash
# Reinstall package
pip install -e .

# Check installation
pip show power-benchmarking-suite
```

### Validation Failures

**Problem**: Code quality validations fail

**Solution**:
```bash
# Run validations to see issues
make validate

# Fix SRP violations: Refactor large functions
# Fix logging: Replace print() with logger.info()
# Fix dynamic code: Move hardcoded values to config
```

### Observability Not Working

**Problem**: No traces/logs/metrics

**Solution**:
```bash
# Check environment variables
export LOG_LEVEL=DEBUG
export ENABLE_TRACING=true
export ENABLE_METRICS=true

# Verify dependencies
pip install -r requirements-observability.txt
```

### Docker Issues

**Problem**: Container won't start

**Solution**:
```bash
# Check Docker is running
docker ps

# Rebuild image
docker-compose build

# Check logs
docker-compose logs
```

## Getting Help

1. Check this troubleshooting guide
2. Search existing issues
3. Check documentation
4. Open a new issue with:
   - Error message
   - Steps to reproduce
   - System information
   - Logs (if applicable)


