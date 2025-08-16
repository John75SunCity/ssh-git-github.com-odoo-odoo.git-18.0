#!/usr/bin/env python3
"""
Comprehensive Odoo-Aware Syntax Fixer
=====================================

This tool fixes common syntax errors found in Odoo model files after mass edits:
- Incorrect docstring quotes
- Malformed field definitions
- Missing commas and parentheses
- String literal termination issues
- Indentation problems
- Bracket matching issues

The fixer preserves Odoo-specific patterns and business logic while correcting syntax.
"""import os
import re
import ast
import sys
from pathlib import Path

class OdooSyntaxFixer:
    def __init__(self, records_dir="records_management"):
        self.records_dir = Path(records_dir)
        self.models_dir = self.records_dir / "models"
        self.fixes_applied = 0
        self.files_processed = 0

    def fix_docstring_quotes(self, content):
        """Fix incorrect docstring quotes ("""" → """)"""
        fixes = 0

        # Pattern 1: Fix quad quotes at start of docstrings
        pattern1 = r'^(\s*)("""")([^"]*?)(\"\"\"\")$'
        def repl1(match):
            nonlocal fixes
            fixes += 1
            indent, _, docstring, _ = match.groups()
            return f'{indent}"""{docstring}"""'
        content = re.sub(pattern1, repl1, content, flags=re.MULTILINE | re.DOTALL)

        # Pattern 2: Fix quad quotes in middle of files
        pattern2 = r'(\n\s*)("""")([^"]*?)(\"\"\"\")(\s*\n)'
        def repl2(match):
            nonlocal fixes
            fixes += 1
            pre, _, docstring, _, post = match.groups()
            return f'{pre}"""{docstring}"""{post}'
        content = re.sub(pattern2, repl2, content, flags=re.DOTALL)

        # Pattern 3: Fix single line quad quotes
        content = re.sub(r'(^\s*)("""")([^"]*?)("""")(\s*$)', r'\1"""\3"""\5', content, flags=re.MULTILINE)
        fixes += len(re.findall(r'(^\s*)("""")([^"]*?)("""")(\s*$)', content, flags=re.MULTILINE))

        return content, fixes

    def fix_field_definitions(self, content):
        """Fix malformed Odoo field definitions"""
        fixes = 0

        # Pattern 1: Fix fields with missing opening parenthesis
        # Example: field = fields.Type() → field = fields.Type(
        pattern1 = r'(\w+\s*=\s*fields\.\w+)\(\)\s*\n\s*(["\'][^"\']*["\'])'
        def repl1(match):
            nonlocal fixes
            fixes += 1
            field_def, param = match.groups()
            return f'{field_def}({param})'
        content = re.sub(pattern1, repl1, content)

        # Pattern 2: Fix fields with parameters on wrong lines
        # Example: field = fields.Type(
        #              "parameter"
        pattern2 = r'(\w+\s*=\s*fields\.\w+)\(\)\s*\n\s*(["\'][^"\']*["\'],?\s*\n)'
        def repl2(match):
            nonlocal fixes
            fixes += 1
            field_def, param = match.groups()
            return f'{field_def}({param.strip()})'
        content = re.sub(pattern2, repl2, content, flags=re.MULTILINE)

        # Pattern 3: Fix Selection fields with missing brackets
        # action_type = fields.Selection([)]
        pattern3 = r'(\w+\s*=\s*fields\.Selection)\(\[\]\)(\s*\n\s*\([^)]+\),?\s*\n)'
        def repl3(match):
            nonlocal fixes
            fixes += 1
            field_def, selections = match.groups()
            # Extract the selection options and clean them up
            clean_selections = re.sub(r'^\s*\(', '[', selections.strip())
            clean_selections = re.sub(r'\),?\s*$', ']', clean_selections)
            return f'{field_def}({clean_selections})'
        content = re.sub(pattern3, repl3, content, flags=re.MULTILINE | re.DOTALL)

        # Pattern 4: Fix Many2one fields with missing opening parenthesis
        # partner_id = fields.Many2one()
        #     "res.partner",
        pattern4 = r'(\w+\s*=\s*fields\.Many2one)\(\)\s*\n\s*(["\'][^"\']*["\'],?\s*\n)'
        def repl4(match):
            nonlocal fixes
            fixes += 1
            field_def, param = match.groups()
            return f'{field_def}({param.strip()})'
        content = re.sub(pattern4, repl4, content, flags=re.MULTILINE)

        return content, fixes

    def fix_string_literals(self, content):
        """Fix unterminated string literals"""
        fixes = 0
        lines = content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            original_line = line

            # Check for unterminated strings at end of line
            if re.search(r'["\']$', line.strip()) and not re.search(r'["\'][^"\']*["\']', line):
                # Line ends with quote but doesn't have matching quote
                if line.strip().endswith('"'):
                    line = line.rstrip('"') + ')'
                elif line.strip().endswith("'"):
                    line = line.rstrip("'") + ')'
                fixes += 1

            # Fix lines that start with quoted string but are not parameters
            if re.match(r'^\s*["\']', line) and i > 0:
                prev_line = lines[i-1].strip()
                if ('=' in prev_line and 'fields.' in prev_line and
                    not prev_line.endswith(',') and not prev_line.endswith('(')):
                    # Previous line is field definition missing opening paren
                    lines[i-1] = prev_line + '('
                    line = '    ' + line.strip() + ')'
                    fixes += 1

            fixed_lines.append(line)

        return '\n'.join(fixed_lines), fixes

    def fix_indentation(self, content):
        """Fix indentation issues"""
        fixes = 0
        lines = content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            original_line = line

            # Fix unexpected indents after comments
            if (i > 0 and lines[i-1].strip().startswith('#') and
                line.strip() and not line.startswith(' ' * 4)):
                if line.strip():
                    line = '    ' + line.strip()
                    fixes += 1

            # Fix unindent issues in method definitions
            if (line.strip().startswith('def ') and i > 0 and
                lines[i-1].strip() and not lines[i-1].strip().startswith('#')):
                # Should be indented under class
                if not line.startswith('    '):
                    line = '    ' + line.strip()
                    fixes += 1

            fixed_lines.append(line)

        return '\n'.join(fixed_lines), fixes

    def fix_bracket_matching(self, content):
        """Fix bracket and parenthesis matching issues"""
        fixes = 0

        # Fix common bracket mismatches
        patterns = [
            # Fix "] → )"
            (r'(\w+\s*=\s*fields\.\w+)\(\[\]\)', r'\1([])', 'Selection field brackets'),
            # Fix missing closing parentheses on field definitions
            (r'(\w+\s*=\s*fields\.\w+\([^)]+),\s*$', r'\1)', 'Missing closing paren'),
            # Fix trailing commas before closing parens
            (r',(\s*\))', r'\1', 'Trailing comma'),
        ]

        for pattern, replacement, desc in patterns:
            matches = len(re.findall(pattern, content, re.MULTILINE))
            if matches > 0:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                fixes += matches

        return content, fixes

    def fix_method_definitions(self, content):
        """Fix method definition syntax issues"""
        fixes = 0

        # Fix method definitions with wrong indentation
        pattern = r'^(def \w+\([^)]*\):)$'
        def repl(match):
            nonlocal fixes
            fixes += 1
            return '    ' + match.group(1)

        content = re.sub(pattern, repl, content, flags=re.MULTILINE)

        # Fix create method specifically
        create_pattern = r'^(\s*)@api\.model_create_multi\s*\n^def create\(self, vals_list\):'
        def create_repl(match):
            nonlocal fixes
            fixes += 1
            indent = match.group(1)
            return f'{indent}@api.model_create_multi\n{indent}def create(self, vals_list):'

        content = re.sub(create_pattern, create_repl, content, flags=re.MULTILINE)

        return content, fixes

    def apply_comprehensive_fixes(self, content):
        """Apply all syntax fixes to content"""
        total_fixes = 0

        # Apply fixes in order of importance
        content, fixes = self.fix_docstring_quotes(content)
        total_fixes += fixes

        content, fixes = self.fix_field_definitions(content)
        total_fixes += fixes

        content, fixes = self.fix_string_literals(content)
        total_fixes += fixes

        content, fixes = self.fix_bracket_matching(content)
        total_fixes += fixes

        content, fixes = self.fix_indentation(content)
        total_fixes += fixes

        content, fixes = self.fix_method_definitions(content)
        total_fixes += fixes

        return content, total_fixes

    def validate_syntax(self, content):
        """Validate Python syntax"""
        try:
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, str(e)

    def process_file(self, filepath):
        """Process a single Python file"""
        try:
            # Read file
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Apply fixes
            fixed_content, fixes_count = self.apply_comprehensive_fixes(original_content)

            # Validate syntax
            is_valid, error = self.validate_syntax(fixed_content)

            if fixes_count > 0:
                # Write back fixed content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)

                print(f"✅ {filepath.name}: Applied {fixes_count} fixes")
                self.fixes_applied += fixes_count
                return True
            else:
                print(f"✨ {filepath.name}: No fixes needed")
                return True

        except Exception as e:
            print(f"❌ {filepath.name}: Error - {e}")
            return False

    def process_all_files(self):
        """Process all Python files in models directory"""
        if not self.models_dir.exists():
            print(f"❌ Models directory not found: {self.models_dir}")
            return

        print("🔧 Starting Comprehensive Odoo Syntax Fixing...")
        print(f"📂 Processing directory: {self.models_dir}")

        python_files = list(self.models_dir.glob("*.py"))
        print(f"📋 Found {len(python_files)} Python files")

        for filepath in sorted(python_files):
            if filepath.name == "__init__.py":
                continue  # Skip __init__.py

            self.files_processed += 1
            self.process_file(filepath)

        print(f"\n🎯 Summary:")
        print(f"   📁 Files processed: {self.files_processed}")
        print(f"   🔧 Total fixes applied: {self.fixes_applied}")
        print(f"   📊 Average fixes per file: {self.fixes_applied / max(1, self.files_processed):.1f}")

def main():
    """Main execution function"""
    print("=" * 50)
    print("🚀 COMPREHENSIVE ODOO SYNTAX FIXER")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("records_management").exists():
        print("❌ Error: records_management directory not found")
        print("   Please run this script from the project root directory")
        return 1

    # Create and run fixer
    fixer = OdooSyntaxFixer()
    fixer.process_all_files()

    print("\n✅ Syntax fixing completed!")
    print("🔍 Run syntax validation to check results:")
    print("   python development-tools/find_syntax_errors.py")

    return 0

if __name__ == "__main__":
    sys.exit(main())
