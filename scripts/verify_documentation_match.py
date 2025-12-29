#!/usr/bin/env python3
"""
Documentation Verification Script

Verifies that features documented in MD files are actually implemented in the codebase.
This prevents documentation drift and ensures code matches what's documented.

Usage:
    python scripts/verify_documentation_match.py
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Set
import ast
import importlib.util


class DocumentationVerifier:
    """Verifies codebase matches documentation."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.docs_dir = root_dir / "docs"
        self.code_dir = root_dir / "power_benchmarking_suite"
        self.scripts_dir = root_dir / "scripts"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.verified: List[str] = []
    
    def verify(self) -> bool:
        """Run all verification checks."""
        print("🔍 Verifying codebase matches documentation...\n")
        
        # Check CLI commands
        self._verify_cli_commands()
        
        # Check validate command features
        self._verify_validate_features()
        
        # Check marketing command features
        self._verify_marketing_features()
        
        # Check key functions
        self._verify_key_functions()
        
        # Check stall visualization
        self._verify_stall_visualization()
        
        # Print results
        self._print_results()
        
        return len(self.errors) == 0
    
    def _verify_cli_commands(self):
        """Verify CLI commands mentioned in docs exist."""
        print("📋 Checking CLI commands...")
        
        # Commands documented in various MD files
        documented_commands = {
            "validate", "v", "check",
            "marketing", "mkt",
            "monitor", "m",
            "analyze", "a",
            "optimize", "opt", "o",
            "config", "c",
            "quickstart", "qs", "start",
            "business", "biz",
        }
        
        # Check if commands are registered in CLI
        cli_file = self.root_dir / "power_benchmarking_suite" / "cli.py"
        if not cli_file.exists():
            self.errors.append(f"❌ CLI file not found: {cli_file}")
            return
        
        cli_content = cli_file.read_text()
        
        # Check command imports (handle both import styles)
        commands_to_check = {
            "monitor": "monitor",
            "analyze": "analyze",
            "optimize": "optimize",
            "config_cmd": "config_cmd",
            "quickstart": "quickstart",
            "validate": "validate",
            "business": "business",
            "marketing": "marketing",
        }
        
        for cmd_var, cmd_name in commands_to_check.items():
            # Check if imported (either style)
            imported = (
                f"import {cmd_var}" in cli_content or
                f"from power_benchmarking_suite.commands import" in cli_content and cmd_var in cli_content
            )
            
            # Check if registered
            registered = f"{cmd_var}.add_parser" in cli_content or f"{cmd_name}.add_parser" in cli_content
            
            if not imported:
                self.errors.append(f"❌ Command '{cmd_name}' not imported in cli.py")
            elif not registered:
                self.errors.append(f"❌ Command '{cmd_name}' not registered with add_parser in cli.py")
            else:
                self.verified.append(f"✅ CLI command '{cmd_name}' registered")
    
    def _verify_validate_features(self):
        """Verify validate command features."""
        print("🔍 Checking validate command features...")
        
        validate_file = self.code_dir / "commands" / "validate.py"
        if not validate_file.exists():
            self.errors.append(f"❌ validate.py not found: {validate_file}")
            return
        
        validate_content = validate_file.read_text()
        
        # Check for key flags
        flags_to_check = [
            ("--verbose", "verbose flag"),
            ("--headless", "headless flag"),
            ("--mock", "mock flag"),
            ("--mock-arch", "mock-arch flag"),
        ]
        
        for flag, description in flags_to_check:
            if flag in validate_content:
                self.verified.append(f"✅ Validate {description} implemented")
            else:
                self.errors.append(f"❌ Validate {description} missing (documented but not implemented)")
        
        # Check for key functions
        functions_to_check = [
            ("check_system_compatibility", "System compatibility check"),
            ("_check_thermal_guardian_compatibility", "Thermal Guardian compatibility"),
            ("_mock_architecture_compatibility", "Mock architecture compatibility"),
            ("_check_thermal_guardian_consistency", "Thermal Guardian consistency check"),
            ("_test_thermal_guardian_math_architecture", "Thermal Guardian math tests"),
        ]
        
        for func_name, description in functions_to_check:
            if f"def {func_name}" in validate_content:
                self.verified.append(f"✅ Validate function '{func_name}' ({description}) implemented")
            else:
                self.errors.append(f"❌ Validate function '{func_name}' ({description}) missing")
        
        # Check for key sections mentioned in docs
        sections_to_check = [
            ("Thermal Momentum → Throttling Visualization", "Thermal momentum visualization"),
            ("Ghost Performance → Reliable Speed Comparison", "Ghost performance comparison"),
            ("Executive Pitch (CEO Level)", "Executive pitch section"),
            ("Safety Margin Deep-Dive", "Safety margin explanation"),
            ("Mechanical Sympathy Balance", "Mechanical sympathy balance"),
            ("The Evolution of Sympathy", "Evolution of sympathy explanation"),
            ("The Headcount ROI", "Headcount ROI section"),
            ("The Stall Psychology", "Stall psychology explanation"),
        ]
        
        for section_text, description in sections_to_check:
            if section_text in validate_content:
                self.verified.append(f"✅ Validate section '{description}' implemented")
            else:
                self.errors.append(f"❌ Validate section '{description}' missing (documented but not in code)")
    
    def _verify_marketing_features(self):
        """Verify marketing command features."""
        print("🔍 Checking marketing command features...")
        
        marketing_file = self.code_dir / "commands" / "marketing.py"
        if not marketing_file.exists():
            self.errors.append(f"❌ marketing.py not found: {marketing_file}")
            return
        
        marketing_content = marketing_file.read_text()
        
        # Check for readme subcommand
        if "readme" in marketing_content and "subcommand" in marketing_content.lower():
            self.verified.append("✅ Marketing readme subcommand implemented")
        else:
            self.errors.append("❌ Marketing readme subcommand missing")
        
        # Check for key functions
        functions_to_check = [
            ("_handle_readme", "README generation handler"),
            ("_calculate_carbon_backlog_impact", "Carbon backlog calculation"),
            ("_generate_green_readme", "Green README generation"),
        ]
        
        for func_name, description in functions_to_check:
            if f"def {func_name}" in marketing_content:
                self.verified.append(f"✅ Marketing function '{func_name}' ({description}) implemented")
            else:
                self.errors.append(f"❌ Marketing function '{func_name}' ({description}) missing")
        
        # Check for key sections
        sections_to_check = [
            ("3-Year Refresh Cycle", "3-year refresh cycle argument"),
            ("M3 Payback Strategy", "M3 payback strategy"),
            ("Psychology of the 'No'", "Psychology explanation"),
        ]
        
        for section_text, description in sections_to_check:
            if section_text in marketing_content:
                self.verified.append(f"✅ Marketing section '{description}' implemented")
            else:
                self.warnings.append(f"⚠️  Marketing section '{description}' may be missing")
    
    def _verify_key_functions(self):
        """Verify key functions mentioned in docs exist."""
        print("🔍 Checking key functions...")
        
        # Check for display_live_stats in unified_benchmark.py
        unified_benchmark = self.scripts_dir / "unified_benchmark.py"
        if unified_benchmark.exists():
            content = unified_benchmark.read_text()
            if "def display_live_stats" in content:
                self.verified.append("✅ display_live_stats function exists")
            else:
                self.errors.append("❌ display_live_stats function missing")
            
            # Check for smoothness icons
            if "smoothness_icon" in content and "✨" in content:
                self.verified.append("✅ Stall visualization with smoothness icons implemented")
            else:
                self.errors.append("❌ Stall visualization missing smoothness icons")
        else:
            self.errors.append(f"❌ unified_benchmark.py not found: {unified_benchmark}")
    
    def _verify_stall_visualization(self):
        """Verify stall visualization features."""
        print("🔍 Checking stall visualization...")
        
        unified_benchmark = self.scripts_dir / "unified_benchmark.py"
        if not unified_benchmark.exists():
            return
        
        content = unified_benchmark.read_text()
        
        # Check for smoothness levels
        smoothness_levels = ["✨", "🌟", "💫"]
        for icon in smoothness_levels:
            if icon in content:
                self.verified.append(f"✅ Smoothness icon '{icon}' implemented")
            else:
                self.warnings.append(f"⚠️  Smoothness icon '{icon}' may be missing")
        
        # Check for smoothness level logic
        if "smoothness_level" in content and "Smooth" in content:
            self.verified.append("✅ Smoothness level logic implemented")
        else:
            self.errors.append("❌ Smoothness level logic missing")
    
    def _print_results(self):
        """Print verification results."""
        print("\n" + "=" * 70)
        print("📊 Verification Results")
        print("=" * 70)
        
        if self.verified:
            print(f"\n✅ Verified ({len(self.verified)} items):")
            for item in self.verified[:10]:  # Show first 10
                print(f"  {item}")
            if len(self.verified) > 10:
                print(f"  ... and {len(self.verified) - 10} more")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)} items):")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)} items):")
            for error in self.errors:
                print(f"  {error}")
        
        print("\n" + "=" * 70)
        
        if self.errors:
            print(f"❌ FAILED: {len(self.errors)} error(s) found")
            print("   Documentation does not match codebase implementation")
            return False
        elif self.warnings:
            print(f"⚠️  PASSED with warnings: {len(self.warnings)} warning(s)")
            print("   Documentation mostly matches, but some items need review")
            return True
        else:
            print(f"✅ PASSED: All {len(self.verified)} items verified")
            print("   Documentation matches codebase implementation")
            return True


def main():
    """Main entry point."""
    root_dir = Path(__file__).parent.parent
    verifier = DocumentationVerifier(root_dir)
    
    success = verifier.verify()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

