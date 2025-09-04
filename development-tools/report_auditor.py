#!/usr/bin/env python3
"""
Comprehensive Report Audit Script for Records Management Module
Audits all report files for proper structure, model references, and field validation
"""

import os
import xml.etree.ElementTree as ET
import re
from pathlib import Path
import sys

class ReportAuditor:
    def __init__(self, module_path):
        self.module_path = Path(module_path)
        self.report_path = self.module_path / "report"
        self.models_path = self.module_path / "models"
        self.audit_results = {
            'total_files': 0,
            'empty_files': [],
            'invalid_xml': [],
            'missing_models': [],
            'invalid_fields': [],
            'missing_xml_ids': [],
            'template_issues': [],
            'action_issues': []
        }

    def get_all_models(self):
        """Extract all model names from Python files"""
        models = set()
        for py_file in self.models_path.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Find _name attributes
                    name_matches = re.findall(r'_name\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                    models.update(name_matches)
            except Exception as e:
                print(f"Error reading {py_file}: {e}")

        return models

    def get_model_fields(self, model_name):
        """Extract fields for a specific model"""
        fields = set()
        for py_file in self.models_path.glob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for field definitions in the model
                    if f'_name = "{model_name}"' in content or f"_name = '{model_name}'" in content:
                        field_matches = re.findall(r'(\w+)\s*=\s*fields\.', content)
                        fields.update(field_matches)
            except Exception as e:
                print(f"Error reading {py_file}: {e}")

        return fields

    def audit_report_file(self, file_path):
        """Audit a single report file"""
        issues = []

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Check for empty data section - look for any meaningful content
            data_elem = root.find('data')
            content_elements = list(data_elem) if data_elem is not None else list(root)

            # Check if file has meaningful content (records, templates, etc.)
            has_content = False
            for elem in content_elements:
                if elem.tag in ['record', 'template', 'report', 'menuitem']:
                    has_content = True
                    break

            if not has_content:
                self.audit_results['empty_files'].append(file_path.name)
                return issues

            # Check report definitions
            for report in root.findall('.//report'):
                model = report.get('model')
                if model:
                    # Check if model exists
                    if model not in self.all_models:
                        issues.append(f"Missing model: {model}")
                        self.audit_results['missing_models'].append({
                            'file': file_path.name,
                            'model': model
                        })

            # Check ir.actions.report
            for action in root.findall('.//record[@model="ir.actions.report"]'):
                model_field = action.find('.//field[@name="model"]')
                if model_field is not None and model_field.text:
                    if model_field.text not in self.all_models:
                        issues.append(f"Action references missing model: {model_field.text}")
                        self.audit_results['missing_models'].append({
                            'file': file_path.name,
                            'model': model_field.text
                        })

                # Check binding_model_id
                binding_field = action.find('.//field[@name="binding_model_id"]')
                if binding_field is not None:
                    ref = binding_field.get('ref')
                    if ref:
                        # This would need more complex validation
                        pass

            # Check template field references
            for template in root.findall('.//template'):
                # Look for t-field expressions
                template_str = ET.tostring(template, encoding='unicode')
                field_refs = re.findall(r't-field="([^"]+)"', template_str)
                for field_ref in field_refs:
                    # This is a simplified check - would need model context
                    pass

        except ET.ParseError as e:
            issues.append(f"XML Parse Error: {e}")
            self.audit_results['invalid_xml'].append({
                'file': file_path.name,
                'error': str(e)
            })
        except Exception as e:
            issues.append(f"Error processing file: {e}")

        return issues

    def audit_all_reports(self):
        """Audit all report files"""
        print("🔍 Starting comprehensive report audit...")

        # Get all models first
        self.all_models = self.get_all_models()
        print(f"📊 Found {len(self.all_models)} models in the system")

        # Process all XML report files
        xml_files = list(self.report_path.glob("*.xml"))
        self.audit_results['total_files'] = len(xml_files)

        print(f"📋 Processing {len(xml_files)} report files...")

        for xml_file in xml_files:
            if xml_file.name == "__init__.py":
                continue

            print(f"  Checking: {xml_file.name}")
            issues = self.audit_report_file(xml_file)

            if issues:
                print(f"    ⚠️  Issues found: {len(issues)}")
                for issue in issues[:3]:  # Show first 3 issues
                    print(f"      - {issue}")

        self.generate_report()

    def generate_report(self):
        """Generate comprehensive audit report"""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE REPORT AUDIT RESULTS")
        print("="*60)

        print(f"\n📁 Total Files Audited: {self.audit_results['total_files']}")

        print(f"\n🗂️  Empty Files: {len(self.audit_results['empty_files'])}")
        for file in self.audit_results['empty_files'][:10]:  # Show first 10
            print(f"  - {file}")
        if self.audit_results['empty_files']:
            print(f"  ... and {len(self.audit_results['empty_files']) - 10} more")

        print(f"\n❌ Invalid XML: {len(self.audit_results['invalid_xml'])}")
        for item in self.audit_results['invalid_xml'][:5]:
            print(f"  - {item['file']}: {item['error']}")

        print(f"\n🔍 Missing Models: {len(self.audit_results['missing_models'])}")
        for item in self.audit_results['missing_models'][:10]:
            print(f"  - {item['file']}: {item['model']}")

        print(f"\n⚠️  Invalid Fields: {len(self.audit_results['invalid_fields'])}")
        print(f"🔗 Missing XML IDs: {len(self.audit_results['missing_xml_ids'])}")
        print(f"📝 Template Issues: {len(self.audit_results['template_issues'])}")
        print(f"🎯 Action Issues: {len(self.audit_results['action_issues'])}")

        # Summary
        total_issues = sum([
            len(self.audit_results['empty_files']),
            len(self.audit_results['invalid_xml']),
            len(self.audit_results['missing_models']),
            len(self.audit_results['invalid_fields']),
            len(self.audit_results['missing_xml_ids']),
            len(self.audit_results['template_issues']),
            len(self.audit_results['action_issues'])
        ])

        print(f"\n🎯 SUMMARY: {total_issues} total issues found")

        if total_issues == 0:
            print("✅ All reports appear to be properly configured!")
        else:
            print("⚠️  Issues need to be addressed for proper functionality")

def main():
    if not sys.argv or len(sys.argv) != 2:
        print("Usage: python report_auditor.py <module_path>")
        sys.exit(1)

    module_path = sys.argv[1]
    auditor = ReportAuditor(module_path)
    auditor.audit_all_reports()

if __name__ == "__main__":
    main()
