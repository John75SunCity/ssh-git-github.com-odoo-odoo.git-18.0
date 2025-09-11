#!/usr/bin/env python3
"""
Emergency Syntax Fixer for Records Management Module
Fixes common syntax errors before GitHub push
"""

import os
import re
import ast
import tempfile
import shutil

class EmergencySyntaxFixer:
    def __init__(self, base_dir="/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"):
        self.base_dir = base_dir
        self.models_dir = os.path.join(base_dir, "models")
        self.fixes_applied = []
        self.files_fixed = 0

    def fix_missing_comma_errors(self, content):
        """Fix 'Perhaps you forgot a comma?' syntax errors"""
        fixes = []

        # Fix missing commas in field definitions
        # Pattern: field_name = fields.Type(...options...)
        # Look for patterns like ) tracking=True where comma is missing
        patterns = [
            (r'(\)\s+)(tracking=True)', r'\1, \2'),
            (r'(\)\s+)(required=True)', r'\1, \2'),
            (r'(\)\s+)(readonly=True)', r'\1, \2'),
            (r'(\)\s+)(index=True)', r'\1, \2'),
            (r'(\)\s+)(store=True)', r'\1, \2'),
            (r'(\)\s+)(default=)', r'\1, \2'),
            (r'(\)\s+)(string=)', r'\1, \2'),
            (r'(\)\s+)(help=)', r'\1, \2'),
            (r'(\)\s+)(compute=)', r'\1, \2'),
            (r'(\)\s+)(related=)', r'\1, \2'),
            (r'(\)\s+)(inverse=)', r'\1, \2'),
            (r'(\)\s+)(currency_field=)', r'\1, \2'),
            (r'(\)\s+)(copy=)', r'\1, \2'),
            (r'(\)\s+)(ondelete=)', r'\1, \2'),
            (r'(\)\s+)(domain=)', r'\1, \2'),
            (r'(\)\s+)(context=)', r'\1, \2'),
        ]

        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                fixes.append(f"Fixed missing comma: {pattern}")
                content = new_content

        return content, fixes

    def fix_unterminated_strings(self, content):
        """Fix unterminated string literals"""
        fixes = []
        lines = content.split('\n')

        for i, line in enumerate(lines):
            # Look for lines with unterminated strings
            if line.strip().startswith('string=') and line.count('"') % 2 != 0:
                # Find the opening quote and ensure it's properly closed
                if '"' in line and not line.strip().endswith('"'):
                    lines[i] = line + '"'
                    fixes.append(f"Fixed unterminated string at line {i+1}")

            # Look for triple quotes that might be incomplete
            if '"""' in line and line.count('"""') == 1:
                if not line.strip().endswith('"""'):
                    lines[i] = line + '"""'
                    fixes.append(f"Fixed incomplete triple quote at line {i+1}")

        return '\n'.join(lines), fixes

    def fix_unmatched_brackets(self, content):
        """Fix unmatched brackets and parentheses"""
        fixes = []
        lines = content.split('\n')

        for i, line in enumerate(lines):
            # Look for common bracket mismatches
            if '])' in line and '[' not in line:
                # This might be a closing parenthesis that should be a bracket
                lines[i] = line.replace('])', ']')
                fixes.append(f"Fixed bracket mismatch at line {i+1}")

            # Look for lists that end with ) instead of ]
            if re.search(r'\[.*\)', line) and not re.search(r'\[.*\]', line):
                # Replace the last ) with ]
                lines[i] = re.sub(r'\)(\s*,?\s*)$', r']\1', line)
                fixes.append(f"Fixed list bracket at line {i+1}")

        return '\n'.join(lines), fixes

    def fix_unexpected_indent(self, content):
        """Fix unexpected indentation errors"""
        fixes = []
        lines = content.split('\n')

        in_class = False
        expected_indent = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith('class '):
                in_class = True
                expected_indent = 4
                continue

            if not stripped:  # Empty line
                continue

            if in_class and stripped and not line.startswith(' '):
                # This line should be indented
                if not stripped.startswith(('class ', 'def ', '#', 'from ', 'import ')):
                    lines[i] = ' ' * expected_indent + stripped
                    fixes.append(f"Fixed indentation at line {i+1}")

        return '\n'.join(lines), fixes

    def fix_return_outside_function(self, content):
        """Fix 'return' outside function errors"""
        fixes = []
        lines = content.split('\n')

        in_function = False
        function_indent = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith('def '):
                in_function = True
                function_indent = len(line) - len(line.lstrip())
                continue

            if stripped.startswith('class ') or (line and not line.startswith(' ')):
                in_function = False
                continue

            if stripped == 'return' and not in_function:
                # Remove standalone return statements outside functions
                lines[i] = ''
                fixes.append(f"Removed return outside function at line {i+1}")

        return '\n'.join(lines), fixes

    def validate_syntax(self, content):
        """Validate Python syntax"""
        try:
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, str(e)

    def fix_file(self, filepath):
        """Fix a single Python file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            all_fixes = []

            # Apply all fixes
            content, fixes = self.fix_missing_comma_errors(content)
            all_fixes.extend(fixes)

            content, fixes = self.fix_unterminated_strings(content)
            all_fixes.extend(fixes)

            content, fixes = self.fix_unmatched_brackets(content)
            all_fixes.extend(fixes)

            content, fixes = self.fix_unexpected_indent(content)
            all_fixes.extend(fixes)

            content, fixes = self.fix_return_outside_function(content)
            all_fixes.extend(fixes)

            # Validate syntax after fixes
            is_valid, error = self.validate_syntax(content)

            if all_fixes and is_valid:
                # Write the fixed content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

                self.files_fixed += 1
                self.fixes_applied.extend([f"{os.path.basename(filepath)}: {fix}" for fix in all_fixes])
                print(f"✅ Fixed {filepath}: {len(all_fixes)} fixes applied")
                return True
            elif all_fixes and not is_valid:
                print(f"⚠️ {filepath}: Fixes applied but syntax still invalid: {error}")
                return False
            elif not all_fixes:
                print(f"ℹ️ {filepath}: No fixes needed")
                return True

        except Exception as e:
            print(f"❌ Error fixing {filepath}: {e}")
            return False

    def fix_all_files(self):
        """Fix all Python files in the models directory"""
        print("🔧 Emergency Syntax Fixer - Fixing all Python files...")

        if not os.path.exists(self.models_dir):
            print(f"❌ Models directory not found: {self.models_dir}")
            return False

        python_files = []
        for file in os.listdir(self.models_dir):
            if file.endswith('.py') and not file.startswith('__'):
                python_files.append(os.path.join(self.models_dir, file))

        total_files = len(python_files)
        print(f"📂 Found {total_files} Python files to check")

        for filepath in sorted(python_files):
            self.fix_file(filepath)

        print(f"\n📊 Summary:")
        print(f"   Files processed: {total_files}")
        print(f"   Files fixed: {self.files_fixed}")
        print(f"   Total fixes applied: {len(self.fixes_applied)}")

        if self.fixes_applied:
            print(f"\n🔧 Fixes applied:")
            for fix in self.fixes_applied[:20]:  # Show first 20 fixes
                print(f"   - {fix}")
            if len(self.fixes_applied) > 20:
                print(f"   ... and {len(self.fixes_applied) - 20} more fixes")

        return self.files_fixed > 0

def main():
    fixer = EmergencySyntaxFixer()
    fixer.fix_all_files()

if __name__ == "__main__":
    main()
