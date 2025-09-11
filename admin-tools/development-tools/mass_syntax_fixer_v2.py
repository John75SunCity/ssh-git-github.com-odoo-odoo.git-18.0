#!/usr/bin/env python3
"""
Mass Syntax Fixer V2 - Handle unterminated strings and complex syntax issues
This will fix the remaining patterns after V1
"""

import os
import re
import ast

class MassSyntaxFixerV2:
    def __init__(self, base_dir="/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"):
        self.base_dir = base_dir
        self.models_dir = os.path.join(base_dir, "models")
        self.fixes_applied = 0
        self.files_fixed = 0

    def fix_unterminated_strings_advanced(self, content):
        """Fix complex unterminated string literal issues"""
        fixes = 0
        lines = content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i]

            # Look for unterminated multi-line strings
            if '"""' in line and line.count('"""') % 2 == 1:
                # We have an opening triple quote, find the closing
                quote_start = i
                found_closing = False

                # Look ahead for closing triple quote
                for j in range(i + 1, min(i + 20, len(lines))):  # Look max 20 lines ahead
                    if '"""' in lines[j]:
                        found_closing = True
                        break

                if not found_closing:
                    # Add closing triple quote
                    # Find the right indentation
                    indent = len(line) - len(line.lstrip())
                    lines.insert(i + 1, ' ' * indent + '"""')
                    fixes += 1

            # Look for unterminated single line strings
            elif line.strip().endswith(',') and ('"' in line or "'" in line):
                # Check if quotes are balanced
                if line.count('"') % 2 == 1:
                    # Add missing quote before the comma
                    line = line.replace(',', '",')
                    lines[i] = line
                    fixes += 1
                elif line.count("'") % 2 == 1:
                    # Add missing quote before the comma
                    line = line.replace(',', "',")
                    lines[i] = line
                    fixes += 1

            # Look for string=" patterns without closing
            elif 'string=' in line and '"' in line:
                quote_count = line.count('"')
                if quote_count == 1:  # Only opening quote
                    # Find end of string content
                    if line.rstrip().endswith(','):
                        # Add quote before comma
                        line = line.rstrip()[:-1] + '",'
                    else:
                        # Add quote at end
                        line = line.rstrip() + '"'
                    lines[i] = line
                    fixes += 1

            i += 1

        return '\n'.join(lines), fixes

    def fix_invalid_syntax_patterns(self, content):
        """Fix various invalid syntax patterns"""
        fixes = 0

        # Fix "Perhaps you forgot a comma?" issues
        # Pattern: field)(another_field
        content = re.sub(r'\)\s*\(', ', ', content)
        fixes += 1

        # Fix invalid field syntax - remove stray characters
        content = re.sub(r'fields\.\w+\(\s*,\s*\)', 'fields.Char()', content)
        fixes += 1

        # Fix class definitions with syntax errors
        content = re.sub(r'class\s+(\w+)\s*\(\s*models\.Model\s*\)\s*:', r'class \1(models.Model):', content)
        fixes += 1

        # Fix import statements with syntax errors
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('from odoo import') and line.count('(') != line.count(')'):
                # Fix unbalanced parens in imports
                if '(' in line and ')' not in line:
                    line = line + ')'
                    lines[i] = line
                    fixes += 1

        content = '\n'.join(lines)

        return content, fixes

    def fix_closing_parenthesis_mismatches(self, content):
        """Fix 'closing parenthesis X does not match opening parenthesis Y' errors"""
        fixes = 0
        lines = content.split('\n')

        for i, line in enumerate(lines):
            original_line = line

            # Pattern: domain=[('field', '=', 'value')
            # Missing closing bracket
            if 'domain=' in line and '[' in line and line.count('[') > line.count(']'):
                # Add missing closing bracket
                if line.rstrip().endswith(','):
                    line = line.rstrip()[:-1] + '],'
                else:
                    line = line.rstrip() + ']'
                lines[i] = line
                fixes += 1

            # Pattern: selection=[('key', 'value'),
            # Missing closing bracket
            elif 'selection=' in line and '[' in line and line.count('[') > line.count(']'):
                # Add missing closing bracket
                if line.rstrip().endswith(','):
                    line = line.rstrip()[:-1] + '],'
                else:
                    line = line.rstrip() + ']'
                lines[i] = line
                fixes += 1

            # Pattern: Many2one('model.name'
            # Missing closing parenthesis
            elif 'Many2one(' in line and line.count('(') > line.count(')'):
                # Add missing closing parenthesis
                if line.rstrip().endswith(','):
                    line = line.rstrip()[:-1] + '),'
                else:
                    line = line.rstrip() + ')'
                lines[i] = line
                fixes += 1

            # Pattern: fields.Type(string="Name"
            # Missing closing parenthesis
            elif 'fields.' in line and '(' in line and 'string=' in line:
                if line.count('(') > line.count(')'):
                    # Add missing closing parenthesis
                    if line.rstrip().endswith(','):
                        line = line.rstrip()[:-1] + '),'
                    else:
                        line = line.rstrip() + ')'
                    lines[i] = line
                    fixes += 1

        return '\n'.join(lines), fixes

    def fix_class_structure_issues(self, content):
        """Fix class structure and indentation issues"""
        fixes = 0
        lines = content.split('\n')

        # Find class definition
        class_line = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('class ') and not line.startswith('    '):
                class_line = i
                break

        if class_line >= 0:
            # Ensure proper class structure
            for i in range(class_line + 1, len(lines)):
                line = lines[i]
                if not line.strip():  # Empty line
                    continue

                # Class attributes should be indented 4 spaces
                if line.strip().startswith(('_name', '_description', '_inherit', '_order', '_rec_name')):
                    if not line.startswith('    '):
                        lines[i] = '    ' + line.strip()
                        fixes += 1

                # Field definitions should be indented 4 spaces
                elif '= fields.' in line:
                    if not line.startswith('    ') and not line.startswith('        '):
                        lines[i] = '    ' + line.strip()
                        fixes += 1

                # Method definitions should be indented 4 spaces
                elif line.strip().startswith('def '):
                    if not line.startswith('    '):
                        lines[i] = '    ' + line.strip()
                        fixes += 1

                # If we hit another class or top-level construct, stop
                elif line.strip().startswith(('class ', 'from ', 'import ')) and not line.startswith('    '):
                    break

        return '\n'.join(lines), fixes

    def validate_syntax(self, content):
        """Check if content has valid Python syntax"""
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False

    def fix_file(self, filepath):
        """Fix a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            total_fixes = 0

            # Apply fixes in order
            content, fixes = self.fix_unterminated_strings_advanced(content)
            total_fixes += fixes

            content, fixes = self.fix_closing_parenthesis_mismatches(content)
            total_fixes += fixes

            content, fixes = self.fix_invalid_syntax_patterns(content)
            total_fixes += fixes

            content, fixes = self.fix_class_structure_issues(content)
            total_fixes += fixes

            # Check if we made any changes
            if content != original_content:
                # Write the fixed file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

                # Check if syntax is now valid
                is_valid = self.validate_syntax(content)

                self.files_fixed += 1
                self.fixes_applied += total_fixes

                filename = os.path.basename(filepath)
                if is_valid:
                    print(f"✅ FIXED & VALID: {filename} ({total_fixes} fixes)")
                else:
                    print(f"⚠️ IMPROVED: {filename} ({total_fixes} fixes, still has errors)")

                return True
            else:
                return False

        except Exception as e:
            print(f"❌ ERROR: {os.path.basename(filepath)} - {e}")
            return False

    def fix_all_files(self):
        """Fix all Python files"""
        print("🔧 Mass Syntax Fixer V2 - Fixing unterminated strings and complex syntax...")

        python_files = []
        for file in os.listdir(self.models_dir):
            if file.endswith('.py') and not file.startswith('__'):
                python_files.append(os.path.join(self.models_dir, file))

        for filepath in sorted(python_files):
            self.fix_file(filepath)

        print(f"\n📊 Mass Fix V2 Summary:")
        print(f"   Files processed: {len(python_files)}")
        print(f"   Files modified: {self.files_fixed}")
        print(f"   Total fixes applied: {self.fixes_applied}")

def main():
    fixer = MassSyntaxFixerV2()
    fixer.fix_all_files()

if __name__ == "__main__":
    main()
