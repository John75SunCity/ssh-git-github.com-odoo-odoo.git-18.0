#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Odoo-Aware Syntax Fixer - Simple and effective
"""

import os
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
        """Fix incorrect docstring quotes (quad quotes to triple quotes)"""
        fixes = 0

        # Replace """" with """
        old_content = content
        content = content.replace('""""', '"""')
        fixes = old_content.count('""""')

        return content, fixes

    def fix_unterminated_strings(self, content):
        """Fix unterminated string literals at end of lines"""
        fixes = 0
        lines = content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            # Check if line ends with unterminated quote
            stripped = line.rstrip()
            if (stripped.endswith('"') and stripped.count('"') % 2 == 1):
                # Unterminated double quote - remove it
                line = line.rstrip('"').rstrip()
                fixes += 1
            elif (stripped.endswith("'") and stripped.count("'") % 2 == 1):
                # Unterminated single quote - remove it
                line = line.rstrip("'").rstrip()
                fixes += 1

            fixed_lines.append(line)

        return '\n'.join(fixed_lines), fixes

    def fix_field_syntax(self, content):
        """Fix common field definition syntax errors"""
        fixes = 0

        # Fix Selection fields missing brackets: fields.Selection([)] → fields.Selection([
        pattern1 = r'(fields\.Selection)\(\[\]\)'
        content = re.sub(pattern1, r'\1([', content)
        fixes += len(re.findall(pattern1, content))

        # Fix Many2one fields with missing params: fields.Many2one() → fields.Many2one(
        pattern2 = r'(fields\.Many2one)\(\)'
        content = re.sub(pattern2, r'\1(', content)
        fixes += len(re.findall(pattern2, content))

        # Fix other field types with empty params
        pattern3 = r'(fields\.\w+)\(\)'
        content = re.sub(pattern3, r'\1(', content)
        fixes += len(re.findall(pattern3, content))

        return content, fixes

    def fix_method_indentation(self, content):
        """Fix method definition indentation"""
        fixes = 0
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            # Fix unindented def statements (should be indented under class)
            if re.match(r'^def \w+', line):
                if not line.startswith('    '):
                    line = '    ' + line
                    fixes += 1
            fixed_lines.append(line)

        return '\n'.join(fixed_lines), fixes

    def fix_bracket_issues(self, content):
        """Fix bracket matching issues"""
        fixes = 0

        # Fix common bracket patterns
        replacements = [
            (r'\(\[\]\)', '(['),  # Selection field brackets
            (r',\s*\)', ')'),     # Trailing commas
            (r'\]\s*,\s*string=', '], string='),  # Selection closing
        ]

        for pattern, replacement in replacements:
            count = len(re.findall(pattern, content))
            content = re.sub(pattern, replacement, content)
            fixes += count

        return content, fixes

    def comprehensive_fix(self, content):
        """Apply all fixes to the content"""
        total_fixes = 0

        # Apply fixes in sequence
        content, fixes = self.fix_docstring_quotes(content)
        total_fixes += fixes

        content, fixes = self.fix_unterminated_strings(content)
        total_fixes += fixes

        content, fixes = self.fix_field_syntax(content)
        total_fixes += fixes

        content, fixes = self.fix_method_indentation(content)
        total_fixes += fixes

        content, fixes = self.fix_bracket_issues(content)
        total_fixes += fixes

        return content, total_fixes

    def process_file(self, filepath):
        """Process a single Python file"""
        try:
            # Read file
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()

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
        """Run the fixer on all model files"""
        if not self.models_dir.exists():
            print(f"❌ Models directory not found: {self.models_dir}")
            return

        print("🔧 Comprehensive Odoo Syntax Fixer Started...")
        print(f"📂 Directory: {self.models_dir}")

        python_files = list(self.models_dir.glob("*.py"))
        python_files = [f for f in python_files if f.name != "__init__.py"]

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
    print("🚀 COMPREHENSIVE ODOO SYNTAX FIXER")
    print("=" * 50)

    if not Path("records_management").exists():
        print("❌ Error: records_management directory not found")
        return 1

    fixer = OdooSyntaxFixer()
    fixer.run()

    print("\n✅ Fixing completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
