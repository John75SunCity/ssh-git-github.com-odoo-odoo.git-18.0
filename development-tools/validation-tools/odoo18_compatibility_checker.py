#!/usr/bin/env python3
"""
Odoo 18.0 Compatibility Checker
===============================

Comprehensive checker for Odoo 18.0 compatibility issues in XML view files.
This script identifies and can optionally fix common compatibility problems.

Author: Development Tools Suite
Date: September 14, 2025
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse

class Odoo18CompatibilityChecker:
    """Check and fix Odoo 18.0 compatibility issues"""

    def __init__(self, module_path):
        self.module_path = Path(module_path)
        self.issues_found = []
        self.fixes_applied = []

    def check_view_files(self):
        """Check all XML view files for compatibility issues"""
        print("🔍 Checking Odoo 18.0 compatibility...")

        views_path = self.module_path / 'views'
        if not views_path.exists():
            print(f"❌ Views directory not found: {views_path}")
            return False

        xml_files = list(views_path.glob('*.xml'))
        print(f"📁 Found {len(xml_files)} XML files to check")

        for xml_file in xml_files:
            self._check_file(xml_file)

        return True

    def _check_file(self, file_path):
        """Check individual XML file for issues"""
        print(f"📄 Checking: {file_path.name}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for deprecated tree tags
            self._check_tree_tags(file_path, content)

            # Check for deprecated view_mode values
            self._check_view_modes(file_path, content)

            # Check for other Odoo 18.0 issues
            self._check_other_issues(file_path, content)

        except Exception as e:
            issue = f"❌ Error reading {file_path.name}: {e}"
            print(issue)
            self.issues_found.append(issue)

    def _check_tree_tags(self, file_path, content):
        """Check for deprecated <tree> tags"""
        tree_pattern = r'<tree[^>]*>'
        matches = re.finditer(tree_pattern, content)

        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            issue = f"🌳 {file_path.name}:{line_num} - Deprecated <tree> tag (should be <list>)"
            print(f"  {issue}")
            self.issues_found.append(issue)

    def _check_view_modes(self, file_path, content):
        """Check for deprecated view_mode values"""
        # Look for view_mode with tree
        tree_mode_pattern = r'view_mode["\']>\s*[^<]*tree'
        matches = re.finditer(tree_mode_pattern, content)

        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            issue = f"📋 {file_path.name}:{line_num} - view_mode contains 'tree' (should be 'list')"
            print(f"  {issue}")
            self.issues_found.append(issue)

    def _check_other_issues(self, file_path, content):
        """Check for other potential Odoo 18.0 compatibility issues"""

        # Check for deprecated attributes
        deprecated_attrs = [
            (r'editable=["\']top["\']', 'editable="top" may cause issues'),
            (r'editable=["\']bottom["\']', 'editable="bottom" may cause issues'),
            # Add more patterns as needed
        ]

        for pattern, description in deprecated_attrs:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                issue = f"⚠️  {file_path.name}:{line_num} - {description}"
                print(f"  {issue}")
                self.issues_found.append(issue)

    def fix_issues(self, auto_fix=False):
        """Fix compatibility issues automatically"""
        if not auto_fix:
            print("❓ Auto-fix not enabled. Use --fix to apply automatic fixes.")
            return False

        print("🔧 Applying automatic fixes...")

        views_path = self.module_path / 'views'
        xml_files = list(views_path.glob('*.xml'))

        for xml_file in xml_files:
            self._fix_file(xml_file)

        return True

    def _fix_file(self, file_path):
        """Apply fixes to individual file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix tree tags
            content = re.sub(r'<tree([^>]*)>', r'<list\1>', content)
            content = re.sub(r'</tree>', '</list>', content)

            # Fix view_mode
            content = re.sub(r'(view_mode[^>]*>)([^<]*?)tree([^<]*)', r'\1\2list\3', content)

            if content != original_content:
                # Create backup
                backup_path = file_path.with_suffix('.xml.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)

                # Write fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                fix = f"✅ Fixed: {file_path.name} (backup: {backup_path.name})"
                print(f"  {fix}")
                self.fixes_applied.append(fix)

        except Exception as e:
            error = f"❌ Error fixing {file_path.name}: {e}"
            print(error)
            self.issues_found.append(error)

    def generate_report(self):
        """Generate summary report"""
        print("\n" + "="*60)
        print("📊 ODOO 18.0 COMPATIBILITY REPORT")
        print("="*60)

        if not self.issues_found and not self.fixes_applied:
            print("✅ No compatibility issues found! Module is Odoo 18.0 ready.")
            return

        if self.issues_found:
            print(f"\n❌ Issues Found: {len(self.issues_found)}")
            for issue in self.issues_found:
                print(f"  • {issue}")

        if self.fixes_applied:
            print(f"\n✅ Fixes Applied: {len(self.fixes_applied)}")
            for fix in self.fixes_applied:
                print(f"  • {fix}")

        print(f"\n📋 Summary:")
        print(f"  • Issues: {len(self.issues_found)}")
        print(f"  • Fixes: {len(self.fixes_applied)}")

        if self.issues_found and not self.fixes_applied:
            print("\n💡 Tip: Use --fix to automatically apply fixes")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Check Odoo 18.0 compatibility')
    parser.add_argument('module_path', nargs='?', default='records_management',
                       help='Path to Odoo module (default: records_management)')
    parser.add_argument('--fix', action='store_true',
                       help='Automatically fix compatibility issues')

    args = parser.parse_args()

    # Determine module path
    if os.path.exists(args.module_path):
        module_path = args.module_path
    else:
        # Try relative to current directory
        current_dir = Path.cwd()
        module_path = current_dir / args.module_path
        if not module_path.exists():
            print(f"❌ Module path not found: {args.module_path}")
            return 1

    print(f"🔍 Checking module: {module_path}")

    checker = Odoo18CompatibilityChecker(module_path)

    # Check for issues
    if not checker.check_view_files():
        return 1

    # Apply fixes if requested
    if args.fix:
        checker.fix_issues(auto_fix=True)

    # Generate report
    checker.generate_report()

    # Return appropriate exit code
    return 1 if checker.issues_found else 0

if __name__ == '__main__':
    exit(main())
