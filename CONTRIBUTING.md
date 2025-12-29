# Contributing to Power Benchmarking Suite

Thank you for your interest in contributing! This document provides guidelines for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/power-benchmarking-week2.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Install dependencies: `pip install -r requirements.txt`
5. Install in development mode: `pip install -e .`

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_business.py -v

# Run with coverage
pytest tests/ --cov=power_benchmarking_suite --cov-report=html
```

### Code Style

```bash
# Format code
make format

# Check formatting
make lint
```

### Making Changes

1. Make your changes
2. Write/update tests
3. Ensure all tests pass
4. Format code
5. Update documentation if needed

## Pull Request Process

1. Update CHANGELOG.md with your changes
2. Ensure all tests pass
3. Update documentation if needed
4. Submit pull request with clear description
5. Link to related issues

## Code Standards

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for all functions/classes
- Keep functions focused and small
- Write tests for new features

## Commit Messages

Use clear, descriptive commit messages:
- `feat: Add email sequence support`
- `fix: Resolve client lookup issue`
- `docs: Update installation guide`

## Questions?

Open an issue or start a discussion!


