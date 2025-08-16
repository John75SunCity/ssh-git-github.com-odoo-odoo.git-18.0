#!/usr/bin/env python3
"""
Advanced Syntax Error Fixer for Records Management Module
Systematically fixes all remaining syntax errors before GitHub deployment
"""

import os
import re
import sys
import tempfile
import shutil
from pathlib import Path

class AdvancedSyntaxFixer:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.models_path = self.base_path / "records_management" / "models"
        self.fixed_count = 0
        self.error_count = 0

    def log(self, message):
        """Log progress messages"""
        print(f"[SyntaxFixer] {message}")

    def fix_common_syntax_errors(self, content, filename):
        """Fix common syntax error patterns"""
        original_content = content

        # Fix 1: Closing parenthesis ')' does not match opening parenthesis '['
        # Pattern: field_name = fields.Type( ... ]
        content = re.sub(
            r'(\w+\s*=\s*fields\.\w+\([^)]*)\]',
            r'\1)',
            content,
            flags=re.DOTALL
        )

        # Fix 2: Closing parenthesis ')' does not match opening parenthesis '{'
        # Pattern: field_name = fields.Type( ... }
        content = re.sub(
            r'(\w+\s*=\s*fields\.\w+\([^)]*)\}',
            r'\1)',
            content,
            flags=re.DOTALL
        )

        # Fix 3: Closing parenthesis ']' does not match opening parenthesis '('
        # Pattern: field_name = fields.Type( ... ]
        content = re.sub(
            r'(\w+\s*=\s*fields\.\w+\([^]]*)\]',
            r'\1)',
            content,
            flags=re.DOTALL
        )

        # Fix 4: Unterminated triple-quoted string literal
        # Find and fix unterminated docstrings
        lines = content.split('\n')
        fixed_lines = []
        in_docstring = False
        docstring_quote = None

        for i, line in enumerate(lines):
            if '"""' in line or "'''" in line:
                triple_quotes = ['"""', "'''"]
                for quote in triple_quotes:
                    if quote in line:
                        count = line.count(quote)
                        if count % 2 == 1:  # Odd number means opening or closing
                            if not in_docstring:
                                in_docstring = True
                                docstring_quote = quote
                            else:
                                in_docstring = False
                                docstring_quote = None
                        break

            # If we're at the end and still in a docstring, close it
            if i == len(lines) - 1 and in_docstring and docstring_quote:
                line += f'\n    {docstring_quote}'
                in_docstring = False

            fixed_lines.append(line)

        content = '\n'.join(fixed_lines)

        # Fix 5: Invalid syntax at line 3 (common pattern)
        # Usually missing imports or malformed class declaration
        if 'invalid syntax at line 3' in filename:
            lines = content.split('\n')
            if len(lines) > 3:
                line3 = lines[2].strip()
                if line3 and not line3.startswith('#') and not line3.startswith('from') and not line3.startswith('import'):
                    # Likely missing import, add basic Odoo imports
                    lines.insert(0, "from odoo import models, fields, api, _")
                    lines.insert(1, "from odoo.exceptions import ValidationError, UserError")
                    lines.insert(2, "")
                    content = '\n'.join(lines)

        # Fix 6: Unterminated string literal
        # Find lines with unterminated strings and fix them
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Count quotes to detect unterminated strings
            single_quotes = line.count("'") - line.count("\\'")
            double_quotes = line.count('"') - line.count('\\"')

            if single_quotes % 2 == 1:  # Unterminated single quote
                lines[i] = line + "'"
            elif double_quotes % 2 == 1:  # Unterminated double quote
                lines[i] = line + '"'

        content = '\n'.join(lines)

        # Fix 7: Perhaps you forgot a comma?
        # Add missing commas in field definitions
        content = re.sub(
            r'(\w+\s*=\s*fields\.\w+\([^)]*)\s+(\w+\s*=)',
            r'\1,\n    \2',
            content,
            flags=re.MULTILINE
        )

        # Fix 8: Unexpected indent
        # Fix indentation issues
        lines = content.split('\n')
        fixed_lines = []
        for line in lines:
            # Convert tabs to spaces
            line = line.expandtabs(4)
            # Remove leading/trailing whitespace but preserve relative indentation
            if line.strip():
                # Count leading spaces
                leading_spaces = len(line) - len(line.lstrip())
                # Ensure proper 4-space indentation
                if leading_spaces > 0:
                    proper_indent = (leading_spaces // 4) * 4
                    if leading_spaces % 4 != 0:
                        proper_indent += 4
                    line = ' ' * proper_indent + line.lstrip()
            fixed_lines.append(line)

        content = '\n'.join(fixed_lines)

        # Fix 9: Leading zeros in decimal integer literals
        content = re.sub(r'\b0(\d+)\b', r'\1', content)

        # Fix 10: Invalid character (Unicode issues)
        # Remove non-ASCII characters that might cause issues
        content = content.encode('ascii', 'ignore').decode('ascii')

        # Fix 11: '(' was never closed
        # Count parentheses and add missing closing ones
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens > close_parens:
            content += ')' * (open_parens - close_parens)

        return content

    def fix_file(self, filepath):
        """Fix syntax errors in a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                self.log(f"Skipping empty file: {filepath.name}")
                return

            # Apply fixes
            fixed_content = self.fix_common_syntax_errors(content, str(filepath))

            # Only write if content changed
            if fixed_content != content:
                # Create backup
                backup_path = filepath.with_suffix(filepath.suffix + '.backup')
                shutil.copy2(filepath, backup_path)

                # Write fixed content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)

                self.fixed_count += 1
                self.log(f"Fixed syntax errors in: {filepath.name}")
            else:
                self.log(f"No changes needed: {filepath.name}")

        except Exception as e:
            self.error_count += 1
            self.log(f"Error fixing {filepath.name}: {str(e)}")

    def fix_all_files(self):
        """Fix syntax errors in all Python files"""
        self.log("Starting advanced syntax error fixing...")
        self.log(f"Scanning directory: {self.models_path}")

        if not self.models_path.exists():
            self.log(f"Error: Models directory not found: {self.models_path}")
            return

        # Get all Python files
        python_files = list(self.models_path.glob("*.py"))
        self.log(f"Found {len(python_files)} Python files to process")

        for py_file in python_files:
            if py_file.name == "__init__.py":
                continue  # Skip __init__.py

            self.fix_file(py_file)

        self.log("\n" + "="*60)
        self.log("ADVANCED SYNTAX FIXING COMPLETE")
        self.log("="*60)
        self.log(f"Files processed: {len(python_files) - 1}")  # -1 for __init__.py
        self.log(f"Files fixed: {self.fixed_count}")
        self.log(f"Errors encountered: {self.error_count}")
        self.log(f"Success rate: {((len(python_files) - 1 - self.error_count) / (len(python_files) - 1) * 100):.1f}%")

if __name__ == "__main__":
    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0"
    fixer = AdvancedSyntaxFixer(base_path)
    fixer.fix_all_files()
