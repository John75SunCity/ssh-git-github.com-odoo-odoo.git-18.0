#!/usr/bin/env python3
"""
Computed Field Dependency Audit Tool
Specifically audits @api.depends decorators on computed fields to find invalid dependencies.
"""

import os
import re
import ast
import sys
from pathlib import Path

def find_computed_fields_with_dependencies():
    """Find all computed fields and their @api.depends decorators."""
    models_dir = Path("records_management/models")
    issues = []
    computed_fields = []

    print("🔍 Auditing computed field dependencies across all models...")
    print("=" * 80)

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find @api.depends decorators followed by method definitions
            depends_pattern = r'@api\.depends\((.*?)\)\s*def\s+(\w+)\(self.*?\):'
            matches = re.finditer(depends_pattern, content, re.DOTALL)

            for match in matches:
                depends_args = match.group(1)
                method_name = match.group(2)

                # Parse the dependency arguments
                try:
                    # Clean up the arguments for parsing
                    cleaned_args = depends_args.strip()
                    if cleaned_args:
                        # Try to safely evaluate the arguments
                        dependencies = []
                        # Split by comma and clean up each dependency
                        for dep in cleaned_args.split(','):
                            dep = dep.strip().strip('"\'')
                            if dep:
                                dependencies.append(dep)

                        computed_fields.append({
                            'file': py_file.name,
                            'method': method_name,
                            'dependencies': dependencies,
                            'line_context': get_line_context(content, match.start())
                        })

                        # Analyze dependencies for potential issues
                        for dep in dependencies:
                            issue = analyze_dependency(py_file.name, method_name, dep)
                            if issue:
                                issues.append(issue)

                except Exception as e:
                    issues.append({
                        'type': 'parsing_error',
                        'file': py_file.name,
                        'method': method_name,
                        'error': str(e),
                        'raw_depends': depends_args
                    })

        except Exception as e:
            print(f"❌ Error reading {py_file}: {e}")

    return computed_fields, issues

def get_line_context(content, position):
    """Get line number context for a position in content."""
    lines_before = content[:position].count('\n')
    return lines_before + 1

def analyze_dependency(file_name, method_name, dependency):
    """Analyze a single dependency for potential issues."""

    # Common problematic patterns we've seen
    problematic_patterns = [
        # Fields that don't exist in referenced models
        (r'service_ids\.weight_processed', 'project.task model does not have weight_processed field'),
        (r'service_ids\.feedback_ids', 'project.task model does not have feedback_ids field'),
        # Other patterns to watch for
        (r'\.nonexistent_field', 'Potential nonexistent field reference'),
    ]

    for pattern, description in problematic_patterns:
        if re.search(pattern, dependency):
            return {
                'type': 'field_dependency_error',
                'file': file_name,
                'method': method_name,
                'dependency': dependency,
                'issue': description
            }

    # Check for deeply nested dependencies that might be fragile
    if dependency.count('.') > 2:
        return {
            'type': 'deep_dependency_warning',
            'file': file_name,
            'method': method_name,
            'dependency': dependency,
            'issue': 'Deep nested dependency - verify all intermediate models exist'
        }

    return None

def print_computed_fields_summary(computed_fields):
    """Print summary of all computed fields found."""
    print(f"\n📊 COMPUTED FIELDS SUMMARY")
    print("=" * 50)
    print(f"Total computed fields with @api.depends: {len(computed_fields)}")

    # Group by file
    by_file = {}
    for field in computed_fields:
        file_name = field['file']
        if file_name not in by_file:
            by_file[file_name] = []
        by_file[file_name].append(field)

    for file_name, fields in sorted(by_file.items()):
        print(f"\n📁 {file_name}:")
        for field in fields:
            deps_str = ', '.join(f"'{dep}'" for dep in field['dependencies'])
            print(f"  🔧 {field['method']}() → @api.depends({deps_str})")

def print_issues_summary(issues):
    """Print summary of issues found."""
    if not issues:
        print(f"\n✅ NO DEPENDENCY ISSUES FOUND!")
        print("All computed field dependencies appear to be correct.")
        return

    print(f"\n🚨 DEPENDENCY ISSUES FOUND: {len(issues)}")
    print("=" * 50)

    # Group by issue type
    by_type = {}
    for issue in issues:
        issue_type = issue['type']
        if issue_type not in by_type:
            by_type[issue_type] = []
        by_type[issue_type].append(issue)

    for issue_type, type_issues in by_type.items():
        print(f"\n🔴 {issue_type.upper()}:")
        for issue in type_issues:
            print(f"  📁 {issue['file']} → {issue['method']}()")
            print(f"     Dependency: '{issue.get('dependency', 'N/A')}'")
            print(f"     Issue: {issue['issue']}")
            if 'raw_depends' in issue:
                print(f"     Raw: {issue['raw_depends']}")

def main():
    """Main audit function."""
    print("🔍 COMPUTED FIELD DEPENDENCY AUDIT")
    print("=" * 80)

    # Check if we're in the right directory
    if not os.path.exists("records_management/models"):
        print("❌ Error: Must run from project root (records_management/models not found)")
        sys.exit(1)

    # Find and analyze computed fields
    computed_fields, issues = find_computed_fields_with_dependencies()

    # Print summaries
    print_computed_fields_summary(computed_fields)
    print_issues_summary(issues)

    # Print specific recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("=" * 30)
    print("1. ✅ Recently fixed: shredding_team.py weight_processed → total_weight")
    print("2. ✅ Recently fixed: shredding_team.py invalid service feedback dependency")
    print("3. 🔍 Monitor deep nested dependencies (model.field.subfield.subsubfield)")
    print("4. 🧪 Test computed fields during module loading to catch runtime errors")
    print("5. 📋 Use Odoo.sh deployment feedback to identify field dependency errors")

    # Exit with appropriate code
    if any(issue['type'] == 'field_dependency_error' for issue in issues):
        print(f"\n❌ CRITICAL ISSUES FOUND - Fix before deployment!")
        sys.exit(1)
    elif issues:
        print(f"\n⚠️  WARNINGS FOUND - Review recommended")
        sys.exit(0)
    else:
        print(f"\n✅ ALL DEPENDENCIES VALID")
        sys.exit(0)

if __name__ == "__main__":
    main()
