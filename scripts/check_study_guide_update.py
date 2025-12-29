#!/usr/bin/env python3
"""
Check if the Product Study Guide has been updated recently.

This script ensures that the study guide (docs/PRODUCT_STUDY_GUIDE.md) is kept
up to date with the latest product features, technical concepts, and sales/marketing
information.

Usage:
    python scripts/check_study_guide_update.py [--warn-days DAYS] [--strict]

Options:
    --warn-days DAYS: Warn if study guide hasn't been updated in DAYS days (default: 30)
    --strict: Fail if study guide hasn't been updated in the current commit/PR
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import argparse


def get_git_root():
    """Get the root directory of the git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Not in a git repo or git not available
        return Path.cwd()


def get_file_last_modified(file_path):
    """Get the last modification time of a file."""
    if not file_path.exists():
        return None
    return datetime.fromtimestamp(file_path.stat().st_mtime)


def get_file_last_commit_date(file_path, repo_root):
    """Get the date of the last commit that modified a file."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", str(file_path.relative_to(repo_root))],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            return datetime.fromtimestamp(int(result.stdout.strip()))
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def is_file_modified_in_current_commit(file_path, repo_root):
    """Check if a file was modified in the current commit or PR."""
    try:
        # Check if file is in the current commit
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD", "--", str(file_path.relative_to(repo_root))],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            return True
        
        # Check if file is in staged changes
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached", "--", str(file_path.relative_to(repo_root))],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            return True
        
        # Check if file is in unstaged changes
        result = subprocess.run(
            ["git", "diff", "--name-only", "--", str(file_path.relative_to(repo_root))],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip():
            return True
        
        # For PRs, check if file is in the diff between base and head
        # This is a simplified check - in CI/CD, GitHub Actions provides better context
        if os.getenv("GITHUB_BASE_REF") and os.getenv("GITHUB_HEAD_REF"):
            base_ref = os.getenv("GITHUB_BASE_REF")
            head_ref = os.getenv("GITHUB_HEAD_REF")
            try:
                result = subprocess.run(
                    ["git", "diff", "--name-only", f"{base_ref}...{head_ref}", "--", str(file_path.relative_to(repo_root))],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
                if result.stdout.strip():
                    return True
            except subprocess.CalledProcessError:
                pass
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return False


def check_study_guide(warn_days=30, strict=False):
    """Check if the study guide has been updated recently."""
    repo_root = get_git_root()
    study_guide_path = repo_root / "docs" / "PRODUCT_STUDY_GUIDE.md"
    
    print("📚 Checking Product Study Guide update status...")
    print(f"   Study Guide: {study_guide_path}")
    print()
    
    # Check if file exists
    if not study_guide_path.exists():
        print("❌ ERROR: Study guide not found!")
        print(f"   Expected location: {study_guide_path}")
        print("   Please create the study guide at docs/PRODUCT_STUDY_GUIDE.md")
        return False
    
    # Get file modification dates
    file_mtime = get_file_last_modified(study_guide_path)
    commit_date = get_file_last_commit_date(study_guide_path, repo_root)
    modified_in_commit = is_file_modified_in_current_commit(study_guide_path, repo_root)
    
    # Use commit date if available (more accurate for git history)
    last_update = commit_date if commit_date else file_mtime
    
    if not last_update:
        print("⚠️  WARNING: Could not determine last update date")
        print("   The study guide exists but git history may be unavailable")
        return not strict
    
    # Calculate days since last update
    days_since_update = (datetime.now() - last_update).days
    
    print(f"   Last updated: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Days since update: {days_since_update}")
    print(f"   Modified in current commit/PR: {'Yes' if modified_in_commit else 'No'}")
    print()
    
    # Check if updated in current commit/PR
    if strict and not modified_in_commit:
        print("❌ FAILURE: Study guide not updated in current commit/PR")
        print("   The study guide should be updated when adding new features,")
        print("   technical concepts, or sales/marketing information.")
        print()
        print("   To fix this:")
        print("   1. Review docs/PRODUCT_STUDY_GUIDE.md")
        print("   2. Update it with any new information")
        print("   3. Commit the changes")
        return False
    
    # Check if updated recently (within warn_days)
    if days_since_update > warn_days:
        print(f"⚠️  WARNING: Study guide hasn't been updated in {days_since_update} days")
        print(f"   Recommended: Update within {warn_days} days to keep it current")
        print()
        print("   The study guide should be updated when:")
        print("   • Adding new features or capabilities")
        print("   • Introducing new technical concepts")
        print("   • Updating sales/marketing messaging")
        print("   • Changing competitive positioning")
        print("   • Adding new customer use cases")
        print()
        print("   This is a warning, not an error. Consider updating the study guide.")
        return True  # Warning, not failure
    
    # All checks passed
    print("✅ Study guide is up to date")
    if modified_in_commit:
        print("   Study guide was updated in this commit/PR - excellent!")
    else:
        print(f"   Study guide was last updated {days_since_update} days ago")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check if the Product Study Guide has been updated recently"
    )
    parser.add_argument(
        "--warn-days",
        type=int,
        default=30,
        help="Warn if study guide hasn't been updated in DAYS days (default: 30)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if study guide hasn't been updated in the current commit/PR"
    )
    
    args = parser.parse_args()
    
    success = check_study_guide(warn_days=args.warn_days, strict=args.strict)
    
    if not success:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()

