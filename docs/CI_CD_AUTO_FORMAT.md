# CI/CD Auto-Formatting Setup

## ✅ Auto-Formatting Configured

The CI/CD pipeline now automatically formats code using Black when formatting issues are detected.

## How It Works

### 1. Format Check
- CI checks if code is properly formatted using `black --check`
- If formatting issues are found, sets `needs_format=true`

### 2. Auto-Format
- If formatting issues detected, runs `black` to auto-format code
- Formats all Python files in `power_benchmarking_suite/`, `scripts/`, and `tests/`

### 3. Auto-Commit (PRs Only)
- For pull requests, automatically commits formatting fixes
- Commit message: `🔧 Auto-format code with Black [skip ci]`
- Pushes changes back to the PR branch
- Creates a PR comment confirming the formatting

## Workflows

### Main CI Workflow (`.github/workflows/ci.yml`)
- **Format Check**: Checks formatting in test and lint jobs
- **Auto-Format**: Formats code if issues found (in lint job)
- **Auto-Commit**: Commits fixes for PRs only

### Dedicated Auto-Format Workflow (`.github/workflows/auto-format.yml`)
- **Trigger**: On pull requests or manual dispatch
- **Purpose**: Dedicated job for auto-formatting
- **Features**:
  - Checks formatting
  - Auto-formats if needed
  - Commits and pushes fixes
  - Creates PR comment

## Local Development

### Make Commands

```bash
# Auto-format code
make format

# Check formatting (no changes)
make format-check
```

### Pre-commit Hooks

Pre-commit hooks automatically format code before commit:
- Installed via `.pre-commit-config.yaml`
- Runs Black on staged files
- Auto-fixes formatting issues

## Configuration

### Black Settings
- **Line Length**: 100 characters
- **Config File**: `.black.toml`
- **Target Python**: 3.11

### CI/CD Settings
- **Format Check**: Non-blocking (continues on error)
- **Auto-Commit**: Only for pull requests
- **Skip CI**: Format commits use `[skip ci]` to avoid loops

## Benefits

1. **Consistency**: All code follows the same style
2. **Automation**: No manual formatting needed
3. **Self-Healing**: CI/CD fixes issues automatically
4. **Developer Experience**: Less friction in development workflow

## Example Flow

1. Developer pushes code with formatting issues
2. CI detects formatting problems
3. Auto-format job runs Black
4. Changes are committed to PR
5. PR is updated with formatted code
6. Developer can continue without manual fixes

## Troubleshooting

### Format commits not appearing
- Check if workflow has `contents: write` permission
- Verify PR is from a branch (not fork)
- Check workflow logs for errors

### Infinite loop prevention
- Format commits use `[skip ci]` tag
- Prevents re-triggering CI on format commits

### Manual formatting
```bash
# Format all code
black --line-length 100 power_benchmarking_suite/ scripts/ tests/

# Or use make
make format
```
