#!/usr/bin/env python3
"""
Fix syntax errors in unified_benchmark.py
Removes duplicate else: statements and fixes indentation
"""

import re

file_path = "scripts/unified_benchmark.py"

with open(file_path, "r") as f:
    lines = f.readlines()

fixed_lines = []
i = 0

while i < len(lines):
    line = lines[i]

    # Fix duplicate else: statements
    if re.match(r"^\s+else:\s*$", line):
        # Check if next line is also else:
        if i + 1 < len(lines) and re.match(r"^\s+else:\s*$", lines[i + 1]):
            # Skip the duplicate
            i += 1
            continue
        # Check if next line needs indentation
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            # If next line is not indented and not empty, it needs fixing
            if (
                next_line.strip()
                and not next_line.startswith("        ")
                and not next_line.startswith("    #")
            ):
                # Check if it should be indented (not a comment, not a blank line)
                if not next_line.strip().startswith("#"):
                    fixed_lines.append(line)
                    # Add proper indentation
                    indent_level = len(line) - len(line.lstrip())
                    next_indent = " " * (indent_level + 4)
                    fixed_lines.append(next_indent + next_line.lstrip())
                    i += 2
                    continue

    fixed_lines.append(line)
    i += 1

with open(file_path, "w") as f:
    f.writelines(fixed_lines)

print("Fixed syntax errors in unified_benchmark.py")

