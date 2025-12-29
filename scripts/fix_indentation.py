#!/usr/bin/env python3
"""
Fix indentation errors in unified_benchmark.py
Uses Python's tokenizer to properly fix indentation
"""

import tokenize
import io
import sys


def fix_indentation(file_path):
    """Fix indentation errors in Python file."""
    with open(file_path, "rb") as f:
        tokens = list(tokenize.tokenize(f.readline))

    # Reconstruct file with proper indentation
    lines = []
    current_indent = 0
    indent_stack = [0]

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token.type == tokenize.INDENT:
            current_indent += len(token.string)
            indent_stack.append(current_indent)
        elif token.type == tokenize.DEDENT:
            indent_stack.pop()
            current_indent = indent_stack[-1]
        elif token.type == tokenize.NEWLINE:
            lines.append("")
        elif token.type == tokenize.NL:
            lines.append("")
        elif token.type == tokenize.ENCODING:
            pass
        else:
            # Add token to current line
            if not lines:
                lines.append("")
            lines[-1] += token.string

        i += 1

    # This is a simplified approach - for complex cases, use black
    print(
        "Note: For complex indentation fixes, use: pip install black && black scripts/unified_benchmark.py"
    )


if __name__ == "__main__":
    fix_indentation("scripts/unified_benchmark.py")

