# Contributing Guide

## Getting Started

1. Fork the repository
2. Clone your fork
3. Install dependencies
4. Create a feature branch
5. Make your changes
6. Run validations and tests
7. Submit a pull request

## Code Standards

### Style
- Follow PEP 8
- Use Black for formatting (line length: 100)
- Type hints for all functions
- Docstrings for all public functions

### Quality
- All functions < 50 lines (SRP)
- All files < 500 lines
- No hardcoded values (use config/env)
- Use structured logging (no print())
- Write tests for new features

### Validation
```bash
# Run all validations
make validate

# Individual checks
./scripts/validate-srp.sh
./scripts/validate-logging-integration.sh
./scripts/validate-dynamic-code.sh
```

## Testing

### Write Tests
- Unit tests for all new functions
- Integration tests for commands
- Test edge cases and error handling

### Run Tests
```bash
# All tests
pytest tests/

# With coverage
pytest --cov=power_benchmarking_suite tests/
```

## Documentation

### Code Documentation
- Docstrings for all public functions
- Type hints for clarity
- Comments for complex logic

### User Documentation
- Update relevant docs in `docs/`
- Add examples for new features
- Update `CHANGELOG.md` for user-facing changes

## Pull Request Process

1. **Update CHANGELOG.md** with your changes
2. **Ensure all validations pass**
3. **Write clear PR description**
4. **Link related issues**
5. **Request review**

## Questions?

- Open an issue for bugs
- Start a discussion for features
- Check existing documentation


