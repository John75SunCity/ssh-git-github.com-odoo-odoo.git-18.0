#!/usr/bin/env python3
"""
Field Dependency Validator for Records Management Module

This script validates all @api.depends decorators to ensure:
1. All referenced fields actually exist in the models
2. Complex nested dependencies are properly structured
3. Missing fields are identified for addition
4. Safe patterns are suggested where needed
"""

import os
import re
import ast
import json
from collections import defaultdict

class FieldDependencyValidator:
    def __init__(self, module_path):
        self.module_path = module_path
        self.models_path = os.path.join(module_path, 'models')
        self.issues = []
        self.model_fields = {}  # model_name -> set of field names
        self.model_classes = {}  # file_path -> list of (class_name, model_name)
        self.dependencies = []  # All found dependencies

    def scan_models(self):
        """Scan all model files to extract field definitions and class info"""
        print("📁 Scanning model files...")

        for filename in os.listdir(self.models_path):
            if filename.endswith('.py') and filename != '__init__.py':
                filepath = os.path.join(self.models_path, filename)
                self._analyze_model_file(filepath)

    def _analyze_model_file(self, filepath):
        """Analyze a single model file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the file with AST
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._extract_class_info(node, filepath)

        except Exception as e:
            print(f"❌ Error analyzing {filepath}: {e}")

    def _extract_class_info(self, class_node, filepath):
        """Extract model name and fields from a class node"""
        model_name = None
        fields = set()

        # Look for _name attribute to get model name
        for node in ast.walk(class_node):
            if (isinstance(node, ast.Assign) and
                any(isinstance(target, ast.Name) and target.id == '_name'
                    for target in node.targets)):
                if isinstance(node.value, ast.Constant):
                    model_name = node.value.value
                elif isinstance(node.value, ast.Str):  # Python < 3.8 compatibility
                    model_name = node.value.s

            # Extract field definitions
            if (isinstance(node, ast.Assign) and
                any(isinstance(target, ast.Name) for target in node.targets)):

                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Check if this is a field assignment
                        if isinstance(node.value, ast.Call):
                            if (isinstance(node.value.func, ast.Attribute) and
                                isinstance(node.value.func.value, ast.Name) and
                                node.value.func.value.id == 'fields'):
                                fields.add(target.id)

        if model_name:
            self.model_fields[model_name] = fields
            if filepath not in self.model_classes:
                self.model_classes[filepath] = []
            self.model_classes[filepath].append((class_node.name, model_name))

    def find_api_depends(self):
        """Find all @api.depends decorators and their dependencies"""
        print("🔍 Scanning @api.depends decorators...")

        for filename in os.listdir(self.models_path):
            if filename.endswith('.py') and filename != '__init__.py':
                filepath = os.path.join(self.models_path, filename)
                self._find_depends_in_file(filepath)

    def _find_depends_in_file(self, filepath):
        """Find @api.depends in a specific file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Use regex to find @api.depends patterns
            pattern = r'@api\.depends\([^)]+\)'
            matches = re.finditer(pattern, content, re.MULTILINE)

            for match in matches:
                depends_text = match.group(0)
                # Extract the dependencies from the decorator
                deps_match = re.search(r'@api\.depends\(([^)]+)\)', depends_text)
                if deps_match:
                    deps_str = deps_match.group(1)
                    # Parse the dependencies
                    dependencies = self._parse_dependencies(deps_str)

                    # Find the method name that follows
                    start_pos = match.end()
                    remaining_content = content[start_pos:]
                    method_match = re.search(r'def\s+(\w+)', remaining_content)
                    method_name = method_match.group(1) if method_match else "unknown"

                    self.dependencies.append({
                        'file': filepath,
                        'method': method_name,
                        'dependencies': dependencies,
                        'raw': depends_text
                    })

        except Exception as e:
            print(f"❌ Error scanning {filepath}: {e}")

    def _parse_dependencies(self, deps_str):
        """Parse dependency string to extract individual field references"""
        dependencies = []

        # Split by comma and clean up
        parts = deps_str.split(',')
        for part in parts:
            part = part.strip().strip('\'"')
            if part and not part.startswith('#'):  # Ignore comments
                dependencies.append(part)

        return dependencies

    def validate_dependencies(self):
        """Validate all found dependencies"""
        print("✅ Validating field dependencies...")

        for dep_info in self.dependencies:
            filepath = dep_info['file']
            method = dep_info['method']
            dependencies = dep_info['dependencies']

            # Determine which model this method belongs to
            model_names = []
            if filepath in self.model_classes:
                model_names = [model_name for _, model_name in self.model_classes[filepath]]

            for dependency in dependencies:
                self._validate_single_dependency(dependency, model_names, filepath, method)

    def _validate_single_dependency(self, dependency, model_names, filepath, method):
        """Validate a single field dependency"""
        # Parse the dependency path
        parts = dependency.split('.')

        if len(parts) == 1:
            # Direct field reference
            field_name = parts[0]
            self._check_direct_field(field_name, model_names, filepath, method, dependency)
        else:
            # Nested field reference
            self._check_nested_field(parts, model_names, filepath, method, dependency)

    def _check_direct_field(self, field_name, model_names, filepath, method, full_dependency):
        """Check if a direct field exists in the current model"""
        found = False

        for model_name in model_names:
            if model_name in self.model_fields:
                if field_name in self.model_fields[model_name]:
                    found = True
                    break

        if not found:
            self.issues.append({
                'type': 'missing_field',
                'severity': 'error',
                'file': filepath,
                'method': method,
                'dependency': full_dependency,
                'field': field_name,
                'models': model_names,
                'message': f"Field '{field_name}' not found in models {model_names}"
            })

    def _check_nested_field(self, parts, model_names, filepath, method, full_dependency):
        """Check nested field references (e.g., 'partner_id.name')"""
        base_field = parts[0]

        # Check if base field exists
        found_base = False
        for model_name in model_names:
            if model_name in self.model_fields:
                if base_field in self.model_fields[model_name]:
                    found_base = True
                    break

        if not found_base:
            self.issues.append({
                'type': 'missing_base_field',
                'severity': 'error',
                'file': filepath,
                'method': method,
                'dependency': full_dependency,
                'field': base_field,
                'models': model_names,
                'message': f"Base field '{base_field}' not found in models {model_names}"
            })
        else:
            # For now, we'll flag complex dependencies for review
            if len(parts) > 2:
                self.issues.append({
                    'type': 'complex_dependency',
                    'severity': 'warning',
                    'file': filepath,
                    'method': method,
                    'dependency': full_dependency,
                    'message': f"Complex nested dependency '{full_dependency}' should be validated"
                })

    def generate_report(self):
        """Generate a comprehensive validation report"""
        print("\n" + "="*80)
        print("📊 FIELD DEPENDENCY VALIDATION REPORT")
        print("="*80)

        # Summary statistics
        total_dependencies = len(self.dependencies)
        total_issues = len(self.issues)
        error_count = len([i for i in self.issues if i['severity'] == 'error'])
        warning_count = len([i for i in self.issues if i['severity'] == 'warning'])

        print(f"\n📈 SUMMARY:")
        print(f"  Total @api.depends found: {total_dependencies}")
        print(f"  Total issues found: {total_issues}")
        print(f"  Errors: {error_count}")
        print(f"  Warnings: {warning_count}")
        print(f"  Models analyzed: {len(self.model_fields)}")

        # Group issues by type
        issues_by_type = defaultdict(list)
        for issue in self.issues:
            issues_by_type[issue['type']].append(issue)

        # Report each issue type
        for issue_type, issues in issues_by_type.items():
            print(f"\n🔍 {issue_type.upper().replace('_', ' ')} ({len(issues)} issues):")
            print("-" * 60)

            for issue in issues[:10]:  # Limit to first 10 per type
                filename = os.path.basename(issue['file'])
                print(f"  ❌ {filename}::{issue['method']}")
                print(f"     Dependency: {issue['dependency']}")
                print(f"     Issue: {issue['message']}")
                print()

            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more issues of this type")
                print()

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 40)

        if error_count > 0:
            print("1. Fix missing field errors first - these will cause Odoo loading failures")
            print("2. Add missing fields to models or update dependencies")

        if warning_count > 0:
            print("3. Review complex dependencies for potential simplification")
            print("4. Consider adding hasattr() checks for optional fields")

        print("5. Use direct field references when possible")
        print("6. Validate that all relationship chains actually exist")

        # Save detailed report
        report_file = os.path.join(self.module_path, '..', 'development-tools', 'field_dependency_report.json')
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_dependencies': total_dependencies,
                    'total_issues': total_issues,
                    'errors': error_count,
                    'warnings': warning_count,
                    'models_analyzed': len(self.model_fields)
                },
                'issues': self.issues,
                'model_fields': {k: list(v) for k, v in self.model_fields.items()},
                'dependencies': self.dependencies
            }, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")

        return total_issues == 0

def main():
    module_path = '/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management'

    print("🔬 Field Dependency Validator for Records Management")
    print("=" * 60)

    validator = FieldDependencyValidator(module_path)

    # Run validation steps
    validator.scan_models()
    validator.find_api_depends()
    validator.validate_dependencies()

    # Generate report
    success = validator.generate_report()

    if success:
        print("\n✅ All field dependencies are valid!")
        return 0
    else:
        print("\n❌ Field dependency issues found - see report above")
        return 1

if __name__ == '__main__':
    exit(main())
