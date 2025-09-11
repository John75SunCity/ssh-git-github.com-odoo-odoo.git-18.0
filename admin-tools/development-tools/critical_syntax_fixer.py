#!/usr/bin/env python3
"""
Targeted Syntax Error Fixer for Critical Issues
Fixes the most common critical syntax errors preventing module loading
"""

import os
import re
import sys
from pathlib import Path

class CriticalSyntaxFixer:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.models_path = self.base_path / "records_management" / "models"
        self.fixed_count = 0

    def log(self, message):
        """Log progress messages"""
        print(f"[CriticalFixer] {message}")

    def fix_critical_errors(self, content, filename):
        """Fix the most critical syntax errors"""
        lines = content.split('\n')
        fixed_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Fix 1: Missing docstring quotes at beginning
            if i < 5 and not line.startswith('#') and not line.startswith('from') and not line.startswith('import') and not line.startswith('"""') and not line.startswith("'''") and line.strip() and not line.strip().startswith('class') and not line.strip().startswith('def'):
                # This looks like it should be part of a docstring
                if not any(quote in line for quote in ['"""', "'''"]):
                    # Check if previous line was a comment
                    if i > 0 and lines[i-1].startswith('#'):
                        # Add opening docstring quote
                        fixed_lines.append('"""')
                        fixed_lines.append(line)
                        # Look ahead to close docstring appropriately
                        j = i + 1
                        while j < len(lines) and j < i + 10:  # Look ahead max 10 lines
                            if lines[j].strip() == '' or (not lines[j].startswith('#') and any(keyword in lines[j] for keyword in ['import', 'from', 'class', 'def'])):
                                break
                            j += 1
                        i = j - 1  # Skip to where we found the break
                        fixed_lines.append('"""')
                        fixed_lines.append('')
                        i += 1
                        continue

            # Fix 2: Import syntax errors - missing colon after except
            if 'except ImportError' in line and ':' not in line:
                line = line.rstrip() + ':'

            # Fix 3: Parenthesis mismatches - [ ] ) mismatch
            if 'fields.' in line:
                # Count brackets and parentheses
                open_parens = line.count('(')
                close_parens = line.count(')')
                open_brackets = line.count('[')
                close_brackets = line.count(']')
                open_braces = line.count('{')
                close_braces = line.count('}')

                # Fix closing bracket mismatches
                if close_brackets > 0 and open_brackets == 0 and open_parens > close_parens:
                    line = line.replace(']', ')')
                elif close_braces > 0 and open_braces == 0 and open_parens > close_parens:
                    line = line.replace('}', ')')

            # Fix 4: Unterminated string literals
            single_quotes = line.count("'") - line.count("\\'")
            double_quotes = line.count('"') - line.count('\\"')

            if single_quotes % 2 == 1:  # Odd number = unterminated
                line = line + "'"
            elif double_quotes % 2 == 1:  # Odd number = unterminated
                line = line + '"'

            # Fix 5: Invalid syntax at line 3 - usually missing imports
            if i == 2 and filename in ['invalid syntax at line 3'] and not line.startswith('from') and not line.startswith('import'):
                # Insert basic imports before this line
                fixed_lines.append("from odoo import models, fields, api, _")
                fixed_lines.append("from odoo.exceptions import ValidationError, UserError")
                fixed_lines.append("")

            # Fix 6: Leading zeros (like 0123 -> 123)
            line = re.sub(r'\b0(\d+)\b', r'\1', line)

            # Fix 7: Unexpected indent - normalize indentation
            if line.strip():
                # Count leading spaces and normalize to 4-space increments
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    proper_indent = ((leading_spaces + 3) // 4) * 4  # Round up to nearest 4
                    line = ' ' * proper_indent + line.lstrip()

            fixed_lines.append(line)
            i += 1

        return '\n'.join(fixed_lines)

    def fix_file(self, filepath):
        """Fix critical syntax errors in a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()

            if not original_content.strip():
                return

            fixed_content = self.fix_critical_errors(original_content, str(filepath))

            # Only write if content actually changed
            if fixed_content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                self.fixed_count += 1
                self.log(f"Fixed critical errors in: {filepath.name}")

        except Exception as e:
            self.log(f"Error fixing {filepath.name}: {str(e)}")

    def fix_all_files(self):
        """Fix critical syntax errors in all Python files"""
        self.log("Starting critical syntax error fixing...")

        if not self.models_path.exists():
            self.log(f"Error: Models directory not found: {self.models_path}")
            return

        # Get all Python files
        python_files = list(self.models_path.glob("*.py"))
        self.log(f"Found {len(python_files)} Python files to process")

        for py_file in python_files:
            if py_file.name == "__init__.py":
                continue
            self.fix_file(py_file)

        self.log(f"\nCritical syntax fixing complete. Fixed {self.fixed_count} files.")

if __name__ == "__main__":
    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0"
    fixer = CriticalSyntaxFixer(base_path)
    fixer.fix_all_files()
