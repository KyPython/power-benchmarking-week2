# Workflow Guides

## Development Workflow

### Setup
```bash
# Clone repository
git clone <repo-url>
cd power-benchmarking-week2

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-observability.txt

# Install package in development mode
pip install -e .

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Making Changes

1. **Create feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes**
   - Write code
   - Add tests
   - Update documentation

3. **Run validations**
   ```bash
   make validate
   # Or individually:
   ./scripts/validate-all.sh
   ```

4. **Run tests**
   ```bash
   pytest tests/
   ```

5. **Commit**
   ```bash
   git add .
   git commit -m "feat: Add new feature"
   # Pre-commit hooks run automatically
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/my-feature
   ```

## Testing Workflow

### Unit Tests
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_monitor.py

# Run with coverage
pytest --cov=power_benchmarking_suite tests/
```

### Integration Tests
```bash
# Run integration tests (requires macOS with sudo)
pytest tests/integration/ -v
```

### Manual Testing
```bash
# Test monitor command
sudo power-benchmark monitor --test 30

# Test analyze command
sudo power-benchmark analyze app Safari --duration 60

# Test optimize command
power-benchmark optimize thermal --app Safari --ambient-temp 35
```

## Release Workflow

### Pre-Release
1. **Update version**
   - `setup.py`
   - `power_benchmarking_suite/__init__.py`
   - `CHANGELOG.md`

2. **Run all validations**
   ```bash
   make validate
   pytest tests/
   ```

3. **Update documentation**
   - Review all docs
   - Update release notes

### Release
```bash
# Use release script
./scripts/release.sh

# Or manually:
python3 -m build
twine check dist/*
twine upload dist/*
git tag v1.0.0
git push origin v1.0.0
```

## Code Quality Workflow

### Before Committing
```bash
# Run validations
make validate

# Fix formatting
black power_benchmarking_suite/ scripts/

# Check types
mypy power_benchmarking_suite/
```

### CI/CD
- Validations run automatically on push
- Tests run on all PRs
- Release workflow triggers on tag

## Observability Workflow

### Enable Observability
```bash
# Set environment variables
export LOG_LEVEL=DEBUG
export ENABLE_TRACING=true
export ENABLE_METRICS=true

# Run command
sudo power-benchmark monitor --test 30
```

### View Metrics
```bash
# Start metrics server (if enabled)
curl http://localhost:8000/metrics
```

### View Logs
```bash
# Structured JSON logs
cat logs/power_benchmark_*.log | jq
```

## Troubleshooting Workflow

### Syntax Errors
```bash
# Check Python syntax
python3 -m py_compile scripts/unified_benchmark.py
```

### Import Errors
```bash
# Verify package installation
pip show power-benchmarking-suite

# Reinstall
pip install -e .
```

### Permission Errors
```bash
# Check sudo access
sudo -v

# Test powermetrics
sudo powermetrics --help
```

## Contribution Workflow

1. **Fork repository**
2. **Create feature branch**
3. **Make changes**
4. **Run validations and tests**
5. **Submit PR with description**
6. **Address review feedback**
7. **Merge after approval**


