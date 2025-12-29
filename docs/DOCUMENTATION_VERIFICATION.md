# Documentation Verification System

This document explains the automated verification system that ensures the codebase matches what's documented in the MD files.

---

## Overview

The documentation verification system prevents **documentation drift** - the problem where documentation describes features that don't exist in code, or code implements features that aren't documented.

---

## How It Works

### Verification Script

**Location**: `scripts/verify_documentation_match.py`

**What It Checks**:

1. **CLI Commands**: Verifies all documented CLI commands are registered in `cli.py`
   - `monitor`, `analyze`, `optimize`, `config`, `quickstart`, `validate`, `business`, `marketing`

2. **Validate Command Features**: Checks for documented features in `validate.py`
   - Flags: `--verbose`, `--headless`, `--mock`, `--mock-arch`
   - Functions: `check_system_compatibility`, `_check_thermal_guardian_compatibility`, etc.
   - Sections: "Thermal Momentum → Throttling Visualization", "Ghost Performance", etc.

3. **Marketing Command Features**: Checks for documented features in `marketing.py`
   - README subcommand
   - Carbon backlog calculations
   - Key sections like "3-Year Refresh Cycle", "M3 Payback Strategy"

4. **Stall Visualization**: Verifies smoothness icons (✨, 🌟, 💫) are implemented

5. **Key Functions**: Checks that critical functions like `display_live_stats` exist

---

## CI/CD Integration

### 1. Standalone Workflow

**File**: `.github/workflows/docs-verification.yml`

**Triggers**:
- Push to `main` or `develop` (when docs or code change)
- Pull requests (when docs or code change)
- Weekly schedule (Monday at 3 AM UTC)

**What It Does**:
- Runs on `ubuntu-latest` (fast, cost-effective)
- Installs dependencies
- Runs verification script
- Fails CI if documentation doesn't match code

### 2. Compatibility Check Integration

**File**: `.github/workflows/compatibility-check.yml`

**What It Does**:
- Runs verification as part of compatibility checks
- Ensures documentation is verified alongside hardware compatibility
- Runs on `macos-latest` (for Apple Silicon testing)

---

## Pre-Commit Hooks

**File**: `.pre-commit-config.yaml`

**What It Does**:
- Runs verification before each commit
- Only checks when relevant files change (docs, code)
- Prevents committing code that doesn't match documentation

**To Install**:
```bash
pip install pre-commit
pre-commit install
```

---

## Running Manually

You can run the verification script manually:

```bash
python scripts/verify_documentation_match.py
```

**Output**:
- ✅ **Verified**: Features that match documentation
- ⚠️ **Warnings**: Features that may need review
- ❌ **Errors**: Features documented but not implemented

**Exit Code**:
- `0`: All checks passed
- `1`: Errors found (documentation doesn't match code)

---

## What Gets Verified

### CLI Commands
- All 8 commands registered in `cli.py`
- Command aliases (e.g., `v` for `validate`)

### Validate Command
- All flags (`--verbose`, `--headless`, `--mock`, `--mock-arch`)
- All key functions
- All documented sections:
  - Thermal Momentum Visualization
  - Ghost Performance Comparison
  - Executive Pitch
  - Safety Margin Deep-Dive
  - Mechanical Sympathy Balance
  - Evolution of Sympathy
  - Headcount ROI
  - Stall Psychology

### Marketing Command
- README subcommand
- Carbon backlog calculations
- Key sections and templates

### Stall Visualization
- Smoothness icons (✨, 🌟, 💫)
- Smoothness level logic
- Real-time feedback

---

## Adding New Checks

To add verification for new features:

1. **Add Check to Script**: Edit `scripts/verify_documentation_match.py`
2. **Add Verification Method**: Create a new `_verify_*` method
3. **Call in `verify()`**: Add the method call to the main `verify()` function
4. **Test**: Run the script to ensure it works

**Example**:
```python
def _verify_new_feature(self):
    """Verify new feature is implemented."""
    feature_file = self.code_dir / "commands" / "new_feature.py"
    if not feature_file.exists():
        self.errors.append("❌ new_feature.py not found")
        return
    
    content = feature_file.read_text()
    if "def new_function" in content:
        self.verified.append("✅ new_function implemented")
    else:
        self.errors.append("❌ new_function missing")
```

---

## Benefits

1. **Prevents Documentation Drift**: Catches when docs describe features that don't exist
2. **Ensures Completeness**: Verifies all documented features are implemented
3. **CI/CD Integration**: Automatically checks on every push/PR
4. **Pre-Commit Protection**: Catches issues before they're committed
5. **Weekly Audits**: Scheduled checks catch gradual drift

---

## Troubleshooting

### Verification Fails

**Error**: "Command 'X' not imported in cli.py"
- **Fix**: Ensure the command is imported in `power_benchmarking_suite/cli.py`

**Error**: "Function 'Y' missing"
- **Fix**: Implement the function in the appropriate command file

**Error**: "Section 'Z' missing"
- **Fix**: Add the documented section to the command's verbose output

### False Positives

If the script reports an error but the feature is actually implemented:
1. Check the exact string match (case-sensitive)
2. Verify the feature is in the expected file
3. Update the verification script to match the actual implementation

---

## Future Enhancements

Potential improvements:
- Parse MD files to extract documented features automatically
- Check for code that's implemented but not documented
- Generate a report of all verified features
- Add more granular checks (e.g., function signatures, parameters)

---

## Summary

The documentation verification system ensures that:
- ✅ All documented features are implemented
- ✅ All CLI commands are registered
- ✅ All key functions exist
- ✅ Documentation stays in sync with code

This prevents the common problem of documentation describing features that don't exist, ensuring users can trust what they read in the docs.

