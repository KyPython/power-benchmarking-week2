# Git Commit Guide

## Pre-Commit Checklist

Before committing, ensure:

1. **Tests Pass**
   ```bash
   make test
   # or
   pytest tests/ -v
   ```

2. **Code Formatted**
   ```bash
   make format
   # or
   black power_benchmarking_suite/ scripts/ tests/
   ```

3. **Linting Clean**
   ```bash
   make lint
   # or
   flake8 power_benchmarking_suite/ scripts/ tests/
   ```

## Commit Message Format

Use conventional commits format:

```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

### Examples

```bash
# Feature
git commit -m "feat: Add email sequence support"

# Bug fix
git commit -m "fix: Resolve client lookup by email"

# Documentation
git commit -m "docs: Update installation guide with PyPI instructions"

# Test
git commit -m "test: Add unit tests for invoice generation"

# Multiple changes
git commit -m "feat: Add business automation CLI

- Client management commands
- Invoice generation
- Check-in tracking
- Workflow automation"
```

## Release Commit

For v1.0.0 release:

```bash
git commit -m "release: v1.0.0 - Power Benchmarking Suite with DevOps Integration

- Complete power benchmarking CLI (8 commands)
- Business automation (clients, invoices, check-ins)
- Marketing automation (lead capture, email)
- CI/CD pipeline with GitHub Actions
- Comprehensive test suite
- Full documentation"
```

## Branch Strategy

- `main`: Production-ready code
- `develop`: Development branch
- `feature/*`: Feature branches
- `release/*`: Release preparation
- `hotfix/*`: Critical bug fixes

## Pre-Push Checklist

Before pushing:

1. All tests pass
2. Code formatted
3. Linting clean
4. Commit messages follow format
5. Branch is up to date with main/develop

```bash
# Pull latest changes
git pull origin main

# Run tests
make test

# Push
git push origin your-branch
```


