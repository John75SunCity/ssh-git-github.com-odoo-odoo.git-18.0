#!/usr/bin/env python3
"""
Mass Syntax Fixer V1 - Handle the most common syntax errors
This will fix bracket mismatches, basic indentation, and common patterns
"""

import os
import re
import ast

class MassSyntaxFixerV1:
    def __init__(self, base_dir="/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"):
        self.base_dir = base_dir
        self.models_dir = os.path.join(base_dir, "models")
        self.fixes_applied = 0
        self.files_fixed = 0

    def fix_bracket_mismatches(self, content):
        """Fix common bracket mismatch patterns"""
        fixes = 0

        # Pattern 1: Fix ") does not match opening parenthesis '['"
        # This means we have something like: field = fields.Type([...)
        # Should be: field = fields.Type([...])

        # Find patterns like: field = fields.Type([...])
        # But where the closing is ) instead of ]

        lines = content.split('\n')
        for i, line in enumerate(lines):
            original_line = line

            # Look for field definitions with bracket mismatches
            if 'fields.' in line and '[' in line and '])' in line:
                # This is likely a bracket mismatch
                # Replace ]) with ]]
                line = line.replace('])', ']]')
                fixes += 1

            # Look for selection fields with wrong closing
            if 'selection=' in line and '[' in line and ')' in line and ']' not in line:
                # Add missing bracket before the closing paren
                line = re.sub(r'\)(\s*,?\s*)$', r']\1', line)
                fixes += 1

            # Look for domain fields with wrong closing
            if 'domain=' in line and '[' in line and ')' in line and ']' not in line:
                # Add missing bracket before the closing paren
                line = re.sub(r'\)(\s*,?\s*)$', r']\1', line)
                fixes += 1

            lines[i] = line

        return '\n'.join(lines), fixes

    def fix_unexpected_indents(self, content):
        """Fix unexpected indentation errors"""
        fixes = 0
        lines = content.split('\n')

        # Check if file starts with proper imports and structure
        if len(lines) > 5 and lines[0].strip().startswith('#') and 'coding' in lines[0]:
            # File looks like it starts correctly, check for class structure
            found_class = False
            for i, line in enumerate(lines):
                if line.strip().startswith('class ') and not line.startswith('    '):
                    found_class = True
                    break
                elif line.strip().startswith('class ') and line.startswith('    '):
                    # Class is indented when it shouldn't be
                    lines[i] = line[4:]  # Remove 4 spaces
                    fixes += 1
                    found_class = True
                    break

            # If no class found, but we have indented lines at the top level
            if not found_class:
                for i, line in enumerate(lines[1:], 1):  # Skip first line (encoding)
                    if line.strip() and line.startswith('    ') and not line.strip().startswith('#'):
                        # Check if this should be a top-level statement
                        stripped = line.strip()
                        if (stripped.startswith('from ') or stripped.startswith('import ') or
                            stripped.startswith('class ') or stripped.startswith('def ')):
                            lines[i] = stripped
                            fixes += 1

        return '\n'.join(lines), fixes

    def fix_unterminated_strings(self, content):
        """Fix basic unterminated string issues"""
        fixes = 0
        lines = content.split('\n')

        for i, line in enumerate(lines):
            original_line = line

            # Look for lines that have unterminated quotes
            # Simple case: line ends with quote count mismatch
            single_quotes = line.count("'")
            double_quotes = line.count('"')

            # If we have an odd number of quotes, likely unterminated
            if single_quotes % 2 == 1 and "string=" in line:
                # Add closing quote at end of line
                line = line.rstrip() + "'"
                fixes += 1
            elif double_quotes % 2 == 1 and "string=" in line:
                # Add closing quote at end of line
                line = line.rstrip() + '"'
                fixes += 1

            lines[i] = line

        return '\n'.join(lines), fixes

    def fix_basic_syntax_issues(self, content):
        """Fix basic syntax issues"""
        fixes = 0

        # Fix common field definition issues
        # Pattern: field = fields.Type(,  -> field = fields.Type()
        content = re.sub(r'fields\.\w+\(\s*,', lambda m: m.group(0)[:-1], content)
        if content != content:
            fixes += 1

        # Fix trailing commas before closing parens
        content = re.sub(r',\s*\)', ')', content)
        fixes += 1

        # Fix double commas
        content = re.sub(r',,+', ',', content)
        fixes += 1

        return content, fixes

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
            content, fixes = self.fix_bracket_mismatches(content)
            total_fixes += fixes

            content, fixes = self.fix_unexpected_indents(content)
            total_fixes += fixes

            content, fixes = self.fix_unterminated_strings(content)
            total_fixes += fixes

            content, fixes = self.fix_basic_syntax_issues(content)
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
        print("🔧 Mass Syntax Fixer V1 - Fixing bracket mismatches and basic issues...")

        python_files = []
        for file in os.listdir(self.models_dir):
            if file.endswith('.py') and not file.startswith('__'):
                python_files.append(os.path.join(self.models_dir, file))

        for filepath in sorted(python_files):
            self.fix_file(filepath)

        print(f"\n📊 Mass Fix V1 Summary:")
        print(f"   Files processed: {len(python_files)}")
        print(f"   Files modified: {self.files_fixed}")
        print(f"   Total fixes applied: {self.fixes_applied}")

def main():
    fixer = MassSyntaxFixerV1()
    fixer.fix_all_files()

if __name__ == "__main__":
    main()
