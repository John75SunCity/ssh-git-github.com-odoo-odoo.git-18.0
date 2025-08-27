#!/usr/bin/env python3
"""
Comprehensive Dependency Field Audit Tool

Analyzes all models in the records_management module to find potential
field dependency errors similar to the event_type/transfer_type issue.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import os
import re
import ast
import json
from pathlib import Path
from collections import defaultdict


class DependencyFieldAuditor:
    """Audits field dependencies across all models"""

    def __init__(self, module_path):
        self.module_path = Path(module_path)
        self.models_path = self.module_path / 'models'

        # Store discovered information
        self.models = {}  # model_name -> {fields: [], file_path: str}
        self.dependencies = []  # list of dependency issues
        self.mapped_calls = []  # list of mapped call issues
        self.relationship_refs = []  # list of relationship issues

        # Results
        self.issues = []

    def scan_all_models(self):
        """Scan all Python model files"""
        print("🔍 Scanning all model files...")

        if not self.models_path.exists():
            print(f"❌ Models path not found: {self.models_path}")
            return

        for py_file in self.models_path.glob('*.py'):
            if py_file.name.startswith('__'):
                continue

            print(f"   📄 Analyzing: {py_file.name}")
            self.analyze_model_file(py_file)

    def analyze_model_file(self, file_path):
        """Analyze a single model file for issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract model information
            model_info = self.extract_model_info(content, file_path)
            if model_info:
                self.models[model_info['name']] = model_info

            # Check for dependency issues
            self.check_api_depends(content, file_path)
            self.check_mapped_calls(content, file_path)
            self.check_relationship_fields(content, file_path)

        except Exception as e:
            self.issues.append({
                'type': 'file_error',
                'file': str(file_path),
                'error': str(e),
                'severity': 'high'
            })

    def extract_model_info(self, content, file_path):
        """Extract model name and field definitions"""
        model_name = None
        fields = []

        # Find model name
        model_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
        if model_match:
            model_name = model_match.group(1)
        else:
            # Try to find class name and infer model name
            class_match = re.search(r"class\s+(\w+)\(models\.Model\)", content)
            if not class_match:
                return None

        # Find field definitions
        field_patterns = [
            r"(\w+)\s*=\s*fields\.(Char|Text|Integer|Float|Boolean|Date|Datetime|Selection|Many2one|One2many|Many2many|Binary|Html|Monetary)\s*\(",
            r"(\w+)\s*=\s*fields\.(Char|Text|Integer|Float|Boolean|Date|Datetime|Selection|Many2one|One2many|Many2many|Binary|Html|Monetary)\b"
        ]

        for pattern in field_patterns:
            for match in re.finditer(pattern, content):
                field_name = match.group(1)
                field_type = match.group(2)
                fields.append({'name': field_name, 'type': field_type})

        return {
            'name': model_name,
            'fields': fields,
            'file_path': str(file_path)
        }

    def check_api_depends(self, content, file_path):
        """Check @api.depends decorators for invalid field references"""
        depends_pattern = r"@api\.depends\(['\"]([^'\"]+)['\"]\)"

        for match in re.finditer(depends_pattern, content):
            dependency = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            # Check if dependency contains relationship navigation
            if '.' in dependency:
                parts = dependency.split('.')
                base_field = parts[0]
                related_field = parts[1] if len(parts) > 1 else None

                self.dependencies.append({
                    'file': str(file_path),
                    'line': line_num,
                    'dependency': dependency,
                    'base_field': base_field,
                    'related_field': related_field,
                    'type': 'api_depends'
                })

    def check_mapped_calls(self, content, file_path):
        """Check .mapped() calls for invalid field references"""
        mapped_patterns = [
            r"\.mapped\(['\"]([^'\"]+)['\"]\)",
            r"\.mapped\(([^)]+)\)"
        ]

        for pattern in mapped_patterns:
            for match in re.finditer(pattern, content):
                mapped_field = match.group(1)
                line_num = content[:match.start()].count('\n') + 1

                # Skip complex expressions
                if mapped_field.startswith("'") or mapped_field.startswith('"'):
                    mapped_field = mapped_field.strip("'\"")
                else:
                    continue  # Skip lambda expressions

                self.mapped_calls.append({
                    'file': str(file_path),
                    'line': line_num,
                    'mapped_field': mapped_field,
                    'type': 'mapped_call'
                })

    def check_relationship_fields(self, content, file_path):
        """Check relationship field comodel references"""
        relationship_patterns = [
            r"fields\.(Many2one|One2many|Many2many)\s*\(\s*['\"]([^'\"]+)['\"]",
            r"comodel_name\s*=\s*['\"]([^'\"]+)['\"]"
        ]

        for pattern in relationship_patterns:
            for match in re.finditer(pattern, content):
                if len(match.groups()) == 2:
                    field_type = match.group(1)
                    comodel = match.group(2)
                else:
                    field_type = 'comodel_name'
                    comodel = match.group(1)

                line_num = content[:match.start()].count('\n') + 1

                self.relationship_refs.append({
                    'file': str(file_path),
                    'line': line_num,
                    'field_type': field_type,
                    'comodel': comodel,
                    'type': 'relationship'
                })

    def validate_dependencies(self):
        """Validate all found dependencies against actual model fields"""
        print("\n🔍 Validating @api.depends dependencies...")

        dependency_issues = []

        for dep in self.dependencies:
            if dep['related_field']:
                # Find the comodel for the base field
                base_model = self.find_model_for_file(dep['file'])
                if not base_model:
                    continue

                base_field_info = self.find_field_in_model(base_model, dep['base_field'])
                if not base_field_info:
                    dependency_issues.append({
                        'type': 'missing_base_field',
                        'file': dep['file'],
                        'line': dep['line'],
                        'field': dep['base_field'],
                        'dependency': dep['dependency'],
                        'severity': 'high',
                        'message': f"Base field '{dep['base_field']}' not found in model"
                    })
                    continue

                # Find the comodel and check if related field exists
                comodel_name = self.get_comodel_for_field(dep['file'], dep['base_field'])
                if comodel_name:
                    if comodel_name not in self.models:
                        dependency_issues.append({
                            'type': 'unknown_comodel',
                            'file': dep['file'],
                            'line': dep['line'],
                            'comodel': comodel_name,
                            'dependency': dep['dependency'],
                            'severity': 'medium',
                            'message': f"Comodel '{comodel_name}' not found in scanned models"
                        })
                    else:
                        # Check if related field exists in comodel
                        related_field_info = self.find_field_in_model(comodel_name, dep['related_field'])
                        if not related_field_info:
                            dependency_issues.append({
                                'type': 'missing_related_field',
                                'file': dep['file'],
                                'line': dep['line'],
                                'comodel': comodel_name,
                                'field': dep['related_field'],
                                'dependency': dep['dependency'],
                                'severity': 'high',
                                'message': f"Field '{dep['related_field']}' not found in model '{comodel_name}'"
                            })

        return dependency_issues

    def validate_mapped_calls(self):
        """Validate .mapped() calls"""
        print("🔍 Validating .mapped() calls...")

        mapped_issues = []

        for mapped_call in self.mapped_calls:
            mapped_field = mapped_call['mapped_field']

            # Skip complex field paths for now
            if '.' in mapped_field:
                continue

            # Find the model for this file
            model_name = self.find_model_for_file(mapped_call['file'])
            if not model_name:
                continue

            # Check if field exists
            field_info = self.find_field_in_model(model_name, mapped_field)
            if not field_info:
                mapped_issues.append({
                    'type': 'missing_mapped_field',
                    'file': mapped_call['file'],
                    'line': mapped_call['line'],
                    'field': mapped_field,
                    'model': model_name,
                    'severity': 'high',
                    'message': f"Mapped field '{mapped_field}' not found in model '{model_name}'"
                })

        return mapped_issues

    def find_model_for_file(self, file_path):
        """Find model name for a given file path"""
        for model_name, model_info in self.models.items():
            if model_info['file_path'] == file_path:
                return model_name
        return None

    def find_field_in_model(self, model_name, field_name):
        """Find field in a specific model"""
        if model_name not in self.models:
            return None

        for field in self.models[model_name]['fields']:
            if field['name'] == field_name:
                return field
        return None

    def get_comodel_for_field(self, file_path, field_name):
        """Extract comodel name for a relationship field"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for the field definition and extract comodel
            field_pattern = rf"{field_name}\s*=\s*fields\.(Many2one|One2many|Many2many)\s*\(\s*['\"]([^'\"]+)['\"]"
            match = re.search(field_pattern, content)
            if match:
                return match.group(2)

            # Look for comodel_name parameter
            field_section_start = content.find(f"{field_name} =")
            if field_section_start != -1:
                # Find the end of this field definition
                field_section = content[field_section_start:field_section_start + 500]  # Reasonable limit
                comodel_match = re.search(r"comodel_name\s*=\s*['\"]([^'\"]+)['\"]", field_section)
                if comodel_match:
                    return comodel_match.group(1)

        except Exception:
            pass

        return None

    def generate_report(self):
        """Generate comprehensive audit report"""
        print("\n📊 Generating comprehensive audit report...")

        # Validate all types of dependencies
        dependency_issues = self.validate_dependencies()
        mapped_issues = self.validate_mapped_calls()

        all_issues = dependency_issues + mapped_issues + self.issues

        # Categorize by severity
        high_severity = [issue for issue in all_issues if issue.get('severity') == 'high']
        medium_severity = [issue for issue in all_issues if issue.get('severity') == 'medium']
        low_severity = [issue for issue in all_issues if issue.get('severity') == 'low']

        report = {
            'summary': {
                'total_models_scanned': len(self.models),
                'total_issues_found': len(all_issues),
                'high_severity_issues': len(high_severity),
                'medium_severity_issues': len(medium_severity),
                'low_severity_issues': len(low_severity)
            },
            'models_scanned': list(self.models.keys()),
            'issues': {
                'high_severity': high_severity,
                'medium_severity': medium_severity,
                'low_severity': low_severity
            },
            'detailed_analysis': {
                'api_depends_count': len(self.dependencies),
                'mapped_calls_count': len(self.mapped_calls),
                'relationship_refs_count': len(self.relationship_refs)
            }
        }

        return report

    def print_summary(self, report):
        """Print a human-readable summary"""
        print("\n" + "="*60)
        print("🔍 DEPENDENCY FIELD AUDIT SUMMARY")
        print("="*60)

        print(f"📊 Total models scanned: {report['summary']['total_models_scanned']}")
        print(f"🚨 Total issues found: {report['summary']['total_issues_found']}")
        print(f"   🔴 High severity: {report['summary']['high_severity_issues']}")
        print(f"   🟡 Medium severity: {report['summary']['medium_severity_issues']}")
        print(f"   🟢 Low severity: {report['summary']['low_severity_issues']}")

        # Print high severity issues
        if report['issues']['high_severity']:
            print("\n🔴 HIGH SEVERITY ISSUES:")
            for issue in report['issues']['high_severity']:
                file_name = Path(issue['file']).name
                print(f"   ❌ {file_name}:{issue.get('line', '?')} - {issue['message']}")

        # Print medium severity issues
        if report['issues']['medium_severity']:
            print("\n🟡 MEDIUM SEVERITY ISSUES:")
            for issue in report['issues']['medium_severity']:
                file_name = Path(issue['file']).name
                print(f"   ⚠️  {file_name}:{issue.get('line', '?')} - {issue['message']}")

        print("\n" + "="*60)


def main():
    """Main execution function"""
    print("🚀 Starting Comprehensive Dependency Field Audit...")

    # Get the records_management module path
    script_dir = Path(__file__).parent
    module_path = script_dir.parent / 'records_management'

    if not module_path.exists():
        print(f"❌ Module path not found: {module_path}")
        return

    # Initialize auditor
    auditor = DependencyFieldAuditor(module_path)

    # Perform the audit
    auditor.scan_all_models()
    report = auditor.generate_report()

    # Save detailed report
    report_file = script_dir / 'dependency_field_audit_report.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"📄 Detailed report saved to: {report_file}")

    # Print summary
    auditor.print_summary(report)

    # Return exit code based on severity
    if report['summary']['high_severity_issues'] > 0:
        print("\n❌ Audit completed with HIGH SEVERITY issues found!")
        return 1
    elif report['summary']['medium_severity_issues'] > 0:
        print("\n⚠️  Audit completed with medium severity issues found.")
        return 0
    else:
        print("\n✅ Audit completed successfully with no critical issues!")
        return 0


if __name__ == '__main__':
    exit(main())
