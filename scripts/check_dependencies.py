#!/usr/bin/env python3
"""
Check that production requirements.txt doesn't contain dev dependencies.

This script ensures that development-only tools (pytest, black, flake8, etc.)
are not accidentally added to requirements.txt, which would bloat production installs.
"""

import sys
from pathlib import Path

# Dev-only dependencies that should NEVER be in requirements.txt
DEV_DEPENDENCIES = {
    "pytest",
    "pytest-cov",
    "pytest-",
    "black",
    "flake8",
    "mypy",
    "bandit",
    "safety",
    "pre-commit",
    "types-",
    "coverage",
    "pylint",
    "ruff",
    "isort",
}

# Optional: Some packages might be in both (e.g., if they're used at runtime)
# But these should be rare and explicitly justified
ALLOWED_IN_BOTH = set()  # Add exceptions here if needed


def check_requirements_txt():
    """Check requirements.txt for dev dependencies."""
    repo_root = Path(__file__).parent.parent
    requirements_file = repo_root / "requirements.txt"
    requirements_dev_file = repo_root / "requirements-dev.txt"
    
    if not requirements_file.exists():
        print(f"❌ requirements.txt not found at {requirements_file}")
        return 1
    
    violations = []
    with open(requirements_file, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            
            # Extract package name (before >=, ==, etc.)
            package_name = line.split(">=")[0].split("==")[0].split("<")[0].split(";")[0].strip()
            package_name_lower = package_name.lower()
            
            # Check if it's a dev dependency
            for dev_dep in DEV_DEPENDENCIES:
                if dev_dep.lower() in package_name_lower:
                    if package_name not in ALLOWED_IN_BOTH:
                        violations.append((line_num, line, package_name))
    
    if violations:
        print("❌ DEV DEPENDENCY LEAK DETECTED!")
        print("=" * 70)
        print("The following development-only dependencies were found in requirements.txt:")
        print("(They should be in requirements-dev.txt instead)\n")
        
        for line_num, line, package in violations:
            print(f"  Line {line_num}: {line}")
            print(f"    → Package '{package}' is a dev dependency")
            print()
        
        print("=" * 70)
        print("💡 Fix:")
        print("  1. Move these packages to requirements-dev.txt")
        print("  2. Remove them from requirements.txt")
        print("  3. Commit the changes")
        print()
        print("📚 Why this matters:")
        print("  • Production installs should only include runtime dependencies")
        print("  • Dev dependencies bloat production installs (~70% larger)")
        print("  • Slower install times for end users")
        print("  • Larger attack surface (more dependencies = more vulnerabilities)")
        print()
        
        return 1
    
    print("✅ requirements.txt is clean - no dev dependencies found")
    
    # Optional: Verify requirements-dev.txt exists and has dev deps
    if requirements_dev_file.exists():
        with open(requirements_dev_file, "r") as f:
            dev_content = f.read().lower()
            has_dev_deps = any(dep.lower() in dev_content for dep in DEV_DEPENDENCIES)
            if has_dev_deps:
                print("✅ requirements-dev.txt contains dev dependencies (as expected)")
            else:
                print("⚠️  requirements-dev.txt exists but contains no known dev dependencies")
    
    return 0


if __name__ == "__main__":
    sys.exit(check_requirements_txt())

