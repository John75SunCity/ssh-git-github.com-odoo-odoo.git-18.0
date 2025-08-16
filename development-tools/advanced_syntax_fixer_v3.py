#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Odoo Syntax Fixer - Handles complex syntax errors after mass edits
"""

import os
import re
import ast
import sys
from pathlib import Path

class AdvancedOdooSyntaxFixer:
    def __init__(self, records_dir="records_management"):
        self.records_dir = Path(records_dir)
        self.models_dir = self.records_dir / "models"
        self.fixes_applied = 0
        self.files_processed = 0

    def fix_missing_docstring_quotes(self, content):
        """Fix files where docstring is missing opening/closing quotes"""
        fixes = 0
        lines = content.split('\n')

        # Look for pattern: starts with comment header, then text that should be docstring
        for i, line in enumerate(lines):
            if i < 3:  # Check first few lines
                if (line.strip() and
                    not line.strip().startswith('#') and
                    not line.strip().startswith('"""') and
                    not line.strip().startswith("'''") and
                    not 'import' in line and
                    not 'from' in line and
                    not 'class' in line and
                    not 'def' in line):
                    # This looks like the start of an unquoted docstring
                    # Find the end (usually before imports or class definitions)
                    end_idx = i
                    for j in range(i+1, min(len(lines), i+50)):  # Look ahead max 50 lines
                        if ('import' in lines[j] or 'from' in lines[j] or
                            'class' in lines[j] or lines[j].strip() == ''):
                            end_idx = j - 1
                            break

                    # If we found a reasonable end, wrap in docstring quotes
                    if end_idx > i:
                        lines[i] = '"""' + lines[i]
                        lines[end_idx] = lines[end_idx] + '"""'
                        fixes += 1
                        break

        return '\n'.join(lines), fixes

    def fix_field_definitions(self, content):
        """Fix malformed field definitions"""
        fixes = 0

        # Pattern 1: Fix fields.Type(, → fields.Type(
        pattern1 = r'(= fields\.\w+)\(,'
        content = re.sub(pattern1, r'\1(', content)
        fixes += len(re.findall(pattern1, content))

        # Pattern 2: Fix Selection([ patterns - simple replacement
        content = content.replace('fields.Selection([', 'fields.Selection([')
        content = content.replace('], help=', '], help=')
        fixes += 1

        # Pattern 3: Fix trailing commas and missing parameters
        # name = fields.Char(
        #     string="Name",
        #     help="Help text",  # <-- Missing closing paren
        pattern3 = r'(\w+\s*=\s*fields\.\w+\([^)]+),\s*\n\s*help='
        content = re.sub(pattern3, r'\1,\n        help=', content)
        fixes += len(re.findall(pattern3, content))

        return content, fixes

    def fix_bracket_mismatches(self, content):
        """Fix bracket/parenthesis mismatches"""
        fixes = 0

        # Fix closing bracket mismatches: ],) → ])
        count = content.count('],)')
        content = content.replace('],)', '])')
        fixes += count

        # Fix Selection fields missing commas
        selection_pattern = r'fields\.Selection\(\[([^\]]*)\),'
        count = len(re.findall(selection_pattern, content, re.MULTILINE))
        content = re.sub(selection_pattern, r'fields.Selection([\1]),', content, flags=re.MULTILINE)
        fixes += count

        return content, fixes

    def fix_incomplete_lines(self, content):
        """Fix incomplete lines and hanging syntax"""
        fixes = 0
        lines = content.split('\n')
        fixed_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check for incomplete field definitions
            if ('= fields.' in line and line.strip().endswith(',') and
                i < len(lines) - 1):
                # Look ahead for parameter continuation
                next_line = lines[i + 1].strip()
                if next_line.startswith('string=') or next_line.startswith('help='):
                    # Combine the lines properly
                    line = line.rstrip(',') + '(' + next_line + ')'
                    i += 1  # Skip the next line since we combined it
                    fixes += 1

            # Fix lines ending with colons that shouldn't
            if (line.strip().endswith(':') and
                not any(keyword in line for keyword in ['def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'except:', 'else:', 'elif '])):
                line = line.rstrip(':')
                fixes += 1

            fixed_lines.append(line)
            i += 1

        return '\n'.join(fixed_lines), fixes

    def fix_method_syntax(self, content):
        """Fix method definition syntax issues"""
        fixes = 0

        # Fix create method pattern
        pattern = r'@api\.model_create_multi\s*\ndef create\(self, vals_list\):'
        if re.search(pattern, content):
            # Make sure it's properly indented
            content = re.sub(r'^(\s*)@api\.model_create_multi\s*\n^def create',
                           r'\1@api.model_create_multi\n\1def create',
                           content, flags=re.MULTILINE)
            fixes += 1

        return content, fixes

    def comprehensive_fix(self, content):
        """Apply all fixes"""
        total_fixes = 0

        # Apply fixes in order
        content, fixes = self.fix_missing_docstring_quotes(content)
        total_fixes += fixes

        content, fixes = self.fix_field_definitions(content)
        total_fixes += fixes

        content, fixes = self.fix_bracket_mismatches(content)
        total_fixes += fixes

        content, fixes = self.fix_incomplete_lines(content)
        total_fixes += fixes

        content, fixes = self.fix_method_syntax(content)
        total_fixes += fixes

        return content, total_fixes

    def validate_basic_python_structure(self, content):
        """Do basic validation to avoid corrupting files"""
        # Check for basic Python structure elements
        has_class = 'class ' in content
        has_imports = ('import ' in content or 'from ' in content)

        # Must have these basic elements for a model file
        return has_class and has_imports

    def process_file(self, filepath):
        """Process a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Skip files that don't look like model files
            if not self.validate_basic_python_structure(original_content):
                print(f"⚠️  {filepath.name}: Skipped (not a model file)")
                return True

            # Apply fixes
            fixed_content, fixes_count = self.comprehensive_fix(original_content)

            if fixes_count > 0:
                # Write back
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)

                print(f"✅ {filepath.name}: {fixes_count} fixes")
                self.fixes_applied += fixes_count
            else:
                print(f"✨ {filepath.name}: No fixes needed")

            return True

        except Exception as e:
            print(f"❌ {filepath.name}: Error - {e}")
            return False

    def run(self):
        """Run the advanced fixer"""
        if not self.models_dir.exists():
            print(f"❌ Models directory not found: {self.models_dir}")
            return

        print("🔧 Advanced Odoo Syntax Fixer Started...")
        print(f"📂 Directory: {self.models_dir}")

        # Get all Python files except __init__.py
        python_files = [f for f in self.models_dir.glob("*.py") if f.name != "__init__.py"]

        print(f"📋 Processing {len(python_files)} files...")

        for filepath in sorted(python_files):
            self.files_processed += 1
            self.process_file(filepath)

        print(f"\n🎯 Summary:")
        print(f"   📁 Files: {self.files_processed}")
        print(f"   🔧 Fixes: {self.fixes_applied}")
        print(f"   📊 Avg: {self.fixes_applied/max(1,self.files_processed):.1f} per file")

def main():
    """Main execution"""
    print("=" * 50)
    print("🚀 ADVANCED ODOO SYNTAX FIXER")
    print("=" * 50)

    if not Path("records_management").exists():
        print("❌ Error: records_management directory not found")
        return 1

    fixer = AdvancedOdooSyntaxFixer()
    fixer.run()

    print("\n✅ Advanced fixing completed!")
    print("🔍 Run syntax validation to check results:")
    print("   python development-tools/find_syntax_errors.py")

    return 0

if __name__ == "__main__":
    sys.exit(main())
