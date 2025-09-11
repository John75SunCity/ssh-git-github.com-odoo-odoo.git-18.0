#!/usr/bin/env python3
"""
Critical Dependency Error Detector

Focuses on finding only the most critical dependency issues that would
cause actual runtime errors during module loading or field computation.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import os
import re
from pathlib import Path


def check_critical_dependencies():
    """Check for critical @api.depends dependency errors"""

    print("🔍 Checking for CRITICAL dependency field errors...")

    models_path = Path('records_management/models')
    critical_issues = []

    # Known problematic patterns that cause runtime errors
    problematic_patterns = [
        # Pattern: dependency on non-existent field in related model
        r"@api\.depends\(['\"]([^'\"]*\.[^'\"]*)['\"]",
        # Pattern: mapped calls on possibly non-existent fields
        r"\.mapped\(['\"]([^'\"]*)['\"]",
    ]

    for py_file in models_path.glob('*.py'):
        if py_file.name.startswith('__'):
            continue

        print(f"   📄 Checking: {py_file.name}")

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # Check @api.depends with relationship navigation
            for i, line in enumerate(lines):
                if '@api.depends(' in line and '.' in line:
                    # Extract the dependency
                    match = re.search(r"@api\.depends\(['\"]([^'\"]+)['\"]", line)
                    if match:
                        dependency = match.group(1)
                        if '.' in dependency:
                            parts = dependency.split('.')
                            base_field = parts[0]
                            related_field = parts[1]

                            # This is a potential issue - needs manual verification
                            critical_issues.append({
                                'file': py_file.name,
                                'line': i + 1,
                                'dependency': dependency,
                                'base_field': base_field,
                                'related_field': related_field,
                                'type': 'dependency_navigation',
                                'code_line': line.strip()
                            })

        except Exception as e:
            print(f"   ❌ Error reading {py_file.name}: {e}")

    return critical_issues


def print_critical_issues(issues):
    """Print only the most critical issues that need immediate attention"""

    print(f"\n🚨 Found {len(issues)} potential critical dependency issues:")
    print("="*80)

    # Group by file for better readability
    by_file = {}
    for issue in issues:
        if issue['file'] not in by_file:
            by_file[issue['file']] = []
        by_file[issue['file']].append(issue)

    for file_name, file_issues in by_file.items():
        print(f"\n📄 {file_name}:")
        for issue in file_issues:
            print(f"   Line {issue['line']}: {issue['dependency']}")
            print(f"   Code: {issue['code_line']}")
            print(f"   ⚠️  Verify that '{issue['related_field']}' exists in the related model")
            print()

    print("="*80)
    print("🔧 ACTION REQUIRED:")
    print("1. Check each dependency to ensure the related field exists")
    print("2. Fix field names that don't match the actual model fields")
    print("3. Test each fix by running the syntax validator")
    print("4. Deploy and check for runtime errors")


def main():
    """Main execution"""
    print("🚀 Starting Critical Dependency Error Detection...")

    if not Path('records_management').exists():
        print("❌ records_management directory not found!")
        return 1

    critical_issues = check_critical_dependencies()

    if critical_issues:
        print_critical_issues(critical_issues)
        return 1
    else:
        print("✅ No critical dependency issues found!")
        return 0


if __name__ == '__main__':
    exit(main())
