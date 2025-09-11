#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Odoo Syntax Error Fixer - Second Pass
==============================================

This tool specifically targets the remaining syntax errors after the first pass:
- Unterminated string literals
- Bracket mismatches
- Indentation issues
- Invalid characters
"""

import os
import re
from pathlib import Path

class AdvancedSyntaxFixer:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.fixes_applied = 0

    def fix_all_remaining_errors(self):
        """Fix remaining syntax errors"""
        print("🔧 Advanced Syntax Fixer - Second Pass")

        models_dir = self.base_path / "records_management" / "models"
        python_files = list(models_dir.glob("*.py"))

        for file_path in python_files:
            try:
                self.fix_file_advanced(file_path)
            except Exception as e:
                print(f"❌ Error in {file_path.name}: {e}")

        print(f"✅ Advanced fixing complete! Applied {self.fixes_applied} fixes")

    def fix_file_advanced(self, file_path):
        """Advanced file fixing"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return

        original_content = content

        # Fix specific patterns causing issues
        content = self.fix_unterminated_strings_advanced(content)
        content = self.fix_bracket_mismatches_advanced(content)
        content = self.fix_indentation_advanced(content)
        content = self.fix_invalid_syntax_patterns(content)
        content = self.fix_field_definition_issues(content)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"🔧 Advanced fix: {file_path.name}")
            self.fixes_applied += 1

    def fix_unterminated_strings_advanced(self, content):
        """Advanced string termination fixing"""
        lines = content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            original_line = line

            # Handle common unterminated string patterns
            if ('_description = "' in line and
                line.count('"') == 1 and
                not line.strip().endswith('"')):
                line = line + '"'

            elif ('_name = "' in line and
                  line.count('"') == 1 and
                  not line.strip().endswith('"')):
                line = line + '"'

            elif ('string="' in line and
                  line.count('"') % 2 == 1):
                line = line + '"'

            elif ("string='" in line and
                  line.count("'") % 2 == 1):
                line = line + "'"

            # Fix lines ending with just a quote
            elif line.strip() == '"':
                # This is likely a stray quote, comment it out
                line = '# ' + line

            elif line.strip() == "'":
                line = '# ' + line

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def fix_bracket_mismatches_advanced(self, content):
        """Advanced bracket fixing"""
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            # Fix common bracket patterns
            if ('closing parenthesis' in line or
                'does not match opening parenthesis' in line):
                # This is an error message, skip it
                continue

            # Count brackets and fix simple cases
            open_parens = line.count('(')
            close_parens = line.count(')')
            open_brackets = line.count('[')
            close_brackets = line.count(']')

            # Fix simple parentheses issues
            if (open_parens == close_parens + 1 and
                line.strip().endswith(',') and
                'fields.' in line):
                line = line.rstrip(',') + '),'

            # Fix bracket issues in selection fields
            if (open_brackets == close_brackets + 1 and
                'Selection([' in line and
                not line.strip().endswith(']')):
                if line.strip().endswith(','):
                    line = line.rstrip(',') + '],'
                else:
                    line = line + ']'

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def fix_indentation_advanced(self, content):
        """Fix complex indentation issues"""
        lines = content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            # Fix unexpected indents in specific contexts
            stripped = line.strip()

            if stripped.startswith('class ') and line.startswith('    '):
                # Class definitions should not be indented
                line = stripped

            elif stripped.startswith('_name = ') and line.startswith('        '):
                # Fix over-indented _name
                line = '    ' + stripped

            elif stripped.startswith('_description = ') and line.startswith('        '):
                # Fix over-indented _description
                line = '    ' + stripped

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def fix_invalid_syntax_patterns(self, content):
        """Fix invalid syntax patterns"""
        # Fix invalid decimal literals (common OCR/copy errors)
        content = re.sub(r'([0-9]+)O([0-9]+)', r'\1\2', content)  # Replace O with nothing in numbers

        # Fix invalid characters in variable names
        content = content.replace('→', '->')
        content = content.replace('←', '<-')

        # Fix some common copy-paste errors
        content = re.sub(r'(\w+) = fields\.(\w+)\(\s*$', r'\1 = fields.\2()', content)

        return content

    def fix_field_definition_issues(self, content):
        """Fix common field definition syntax issues"""
        lines = content.split('\n')
        fixed_lines = []

        in_field_def = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Detect field definitions
            if ('= fields.' in line and
                '(' in line and
                line.count('(') > line.count(')')):
                in_field_def = True

            # If we're in a field definition and this line doesn't close it
            if (in_field_def and
                ')' not in line and
                not stripped.endswith(',') and
                stripped and
                not stripped.startswith('#')):
                # Add comma if this looks like a parameter
                if ('=' in stripped or
                    stripped.startswith('"') or
                    stripped.startswith("'") or
                    stripped in ['True', 'False']):
                    line = line + ','

            # Close field definition
            if in_field_def and ')' in line:
                in_field_def = False

            # Fix common field syntax issues
            if 'Many2one(' in line and line.count('"') == 1:
                # Likely unterminated string in Many2one
                if not line.strip().endswith('"'):
                    line = line + '"'

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

def main():
    """Run the advanced syntax fixer"""
    base_path = Path.cwd()

    if not (base_path / "records_management").exists():
        print("❌ records_management directory not found!")
        return 1

    fixer = AdvancedSyntaxFixer(base_path)
    fixer.fix_all_remaining_errors()

    # Run validation
    print("\n🔍 Running syntax validation...")
    syntax_checker = base_path / "development-tools" / "syntax-tools" / "find_syntax_errors.py"
    if syntax_checker.exists():
        os.system(f"python {syntax_checker}")

    return 0

if __name__ == "__main__":
    main()
