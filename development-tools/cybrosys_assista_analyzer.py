#!/usr/bin/env python3
"""
Odoo Model Relationship Analyzer
Uses Cybrosys Assista patterns to analyze model relationships and find issues.

This script leverages Odoo development best practices from Cybrosys Assista
to detect missing inverses, broken relationships, and model inconsistencies.
Enhanced to exclude inherited fields and focus on custom module issues.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set


class OdooModelAnalyzer:
    """Analyze Odoo models using Cybrosys Assista patterns"""

    def __init__(self, module_path: str):
        self.module_path = Path(module_path)
        self.models_dir = self.module_path / "models"
        self.views_dir = self.module_path / "views"
        self.security_dir = self.module_path / "security"

        # Cybrosys Assista field patterns
        self.field_patterns = {
            'Many2one': r"fields\.Many2one\(['\"]([^'\"]+)['\"],\s*string=['\"]([^'\"]+)['\"]",
            'One2many': r"fields\.One2many\(['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]",
            'Many2many': r"fields\.Many2many\(['\"]([^'\"]+)['\"]"
        }

        # Odoo inherited fields to exclude from analysis
        self.inherited_fields = self._get_inherited_fields()

    def _get_inherited_fields(self) -> Dict[str, Set[str]]:
        """Get fields that are inherited from parent models"""
        inherited_fields = {}

        # Common Odoo mixins and their fields
        mixin_fields = {
            'mail.thread': {
                'message_ids', 'message_follower_ids', 'message_partner_ids',
                'message_channel_ids', 'message_main_attachment_id', 'website_message_ids',
                'message_has_sms_error', 'message_has_error', 'message_needaction',
                'message_needaction_counter', 'message_unread', 'message_unread_counter'
            },
            'mail.activity.mixin': {
                'activity_ids', 'activity_state', 'activity_user_id', 'activity_type_id',
                'activity_date_deadline', 'activity_summary', 'activity_exception_decoration',
                'activity_exception_icon'
            },
            'portal.mixin': {
                'access_url', 'access_token', 'access_warning'
            },
            'base': {  # Common base model fields
                'id', 'create_date', 'create_uid', 'write_date', 'write_uid',
                'name', 'active', 'company_id', 'display_name'
            }
        }

        # Extract inheritance information from models
        for model_file in self.models_dir.glob("*.py"):
            if model_file.name == "__init__.py":
                continue

            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                model_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                if not model_match:
                    continue

                model_name = model_match.group(1)

                # Find _inherit declarations
                inherit_match = re.search(r"_inherit\s*=\s*['\"]([^'\"]+)['\"]", content)
                if inherit_match:
                    parent_model = inherit_match.group(1)
                    if parent_model in mixin_fields:
                        inherited_fields[model_name] = mixin_fields[parent_model].copy()
                    else:
                        inherited_fields[model_name] = set()
                else:
                    inherited_fields[model_name] = set()

                # Check for multiple inheritance
                inherit_matches = re.findall(r"_inherit\s*=\s*\[([^\]]+)\]", content)
                for match in inherit_matches:
                    parents = re.findall(r"['\"]([^'\"]+)['\"]", match)
                    for parent in parents:
                        if parent in mixin_fields:
                            inherited_fields[model_name].update(mixin_fields[parent])

            except Exception as e:
                print(f"Error processing inheritance for {model_file}: {e}")
                inherited_fields[model_name] = set()

        return inherited_fields

    def find_missing_inverses(self) -> List[Dict]:
        """Find missing inverse relationships using Odoo best practices (excluding inherited)"""
        issues = []
        relationships = self._extract_relationships()

        for model_name, fields in relationships.items():
            # Get inherited fields for this model
            inherited = self.inherited_fields.get(model_name, set())

            for field_name, field_info in fields.items():
                # Skip inherited fields
                if field_name in inherited:
                    continue

                if field_info['type'] == 'Many2one':
                    # Check if inverse One2many exists
                    target_model = field_info['comodel']
                    inverse_found = False

                    if target_model in relationships:
                        for target_field, target_info in relationships[target_model].items():
                            if (target_info['type'] == 'One2many' and
                                target_info['comodel'] == model_name and
                                target_info.get('inverse_name') == field_name):
                                inverse_found = True
                                break

                    if not inverse_found:
                        issues.append({
                            'type': 'missing_inverse',
                            'model': model_name,
                            'field': field_name,
                            'target_model': target_model,
                            'severity': 'warning',
                            'message': "Missing inverse One2many field in {} for {}.{}".format(target_model, model_name, field_name)
                        })

        return issues

    def find_missing_view_fields(self) -> List[Dict]:
        """Find model fields missing from views (excluding inherited fields)"""
        issues = []
        model_fields = self._extract_model_fields()
        view_fields = self._extract_view_fields()

        for model_name in model_fields:
            if model_name in view_fields:
                # Get inherited fields for this model
                inherited = self.inherited_fields.get(model_name, set())

                # Exclude inherited fields from missing field check
                custom_fields = model_fields[model_name] - inherited
                missing_fields = custom_fields - view_fields[model_name]

                for field in missing_fields:
                    # Skip computed/related fields that might not need views
                    if not field.startswith('_') and field not in ['id', 'create_date', 'write_date', 'create_uid', 'write_uid']:
                        issues.append({
                            'type': 'missing_view_field',
                            'model': model_name,
                            'field': field,
                            'severity': 'info',
                            'message': f"Custom field '{field}' exists in model but not in views"
                        })

        return issues

    def find_calculation_errors(self) -> List[Dict]:
        """Find potential calculation errors in computed fields"""
        issues = []

        for model_file in self.models_dir.glob("*.py"):
            if model_file.name == "__init__.py":
                continue

            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find computed fields using Cybrosys Assista pattern
                compute_pattern = r"@api\.depends\(['\"]([^'\"]+)['\"]\)\s*def\s+_compute_(\w+)"
                for match in re.finditer(compute_pattern, content):
                    dependencies = match.group(1).split(',')
                    field_name = match.group(2)

                    # Check if dependencies exist
                    for dep in dependencies:
                        dep = dep.strip()
                        if not re.search(rf"{re.escape(dep)}\s*=\s*fields\.", content):
                            issues.append({
                                'type': 'missing_dependency',
                                'file': str(model_file),
                                'field': field_name,
                                'dependency': dep,
                                'severity': 'error',
                                'message': "Computed field '{}' depends on non-existent field '{}'".format(field_name, dep)
                            })

            except Exception as e:
                issues.append({
                    'type': 'parse_error',
                    'file': str(model_file),
                    'severity': 'error',
                    'message': "Error parsing {}: {}".format(model_file, str(e))
                })

        return issues

    def find_security_issues(self) -> List[Dict]:
        """Find security rule issues"""
        issues = []

        for security_file in self.security_dir.glob("*.xml"):
            try:
                tree = ET.parse(security_file)
                for elem in tree.iter():
                    if elem.tag == 'record' and elem.get('model') == 'ir.rule':
                        # Check for domain syntax issues
                        domain_elem = elem.find(".//field[@name='domain_force']")
                        if domain_elem is not None and domain_elem.text:
                            domain = domain_elem.text.strip()
                            if domain and not (domain.startswith('[') and domain.endswith(']')):
                                issues.append({
                                    'type': 'invalid_domain',
                                    'file': str(security_file),
                                    'rule': elem.get('id'),
                                    'severity': 'error',
                                    'message': "Invalid domain syntax in rule {}: {}".format(elem.get('id'), domain)
                                })

            except Exception as e:
                issues.append({
                    'type': 'xml_parse_error',
                    'file': str(security_file),
                    'severity': 'error',
                    'message': "Error parsing {}: {}".format(security_file, str(e))
                })

        return issues

    def _extract_relationships(self) -> Dict[str, Dict]:
        """Extract model relationships using field patterns"""
        relationships = {}

        for model_file in self.models_dir.glob("*.py"):
            if model_file.name == "__init__.py":
                continue

            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find model name
                model_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                if not model_match:
                    continue

                model_name = model_match.group(1)
                relationships[model_name] = {}

                # Extract relationships using Cybrosys Assista patterns
                for field_type, pattern in self.field_patterns.items():
                    for match in re.finditer(pattern, content):
                        if field_type == 'Many2one':
                            comodel, field_name = match.groups()[:2]
                            relationships[model_name][field_name] = {
                                'type': field_type,
                                'comodel': comodel
                            }
                        elif field_type == 'One2many':
                            comodel, inverse_name = match.groups()[:2]
                            # Find the field name from the line
                            line = content[match.start():match.end()].split('\n')[0]
                            field_match = re.search(r"(\w+)\s*=\s*fields\.One2many", line)
                            if field_match:
                                field_name = field_match.group(1)
                                relationships[model_name][field_name] = {
                                    'type': field_type,
                                    'comodel': comodel,
                                    'inverse_name': inverse_name
                                }

            except Exception as e:
                print("Error processing {}: {}".format(model_file, e))

        return relationships

    def _extract_model_fields(self) -> Dict[str, Set[str]]:
        """Extract all fields from models (excluding inherited fields)"""
        model_fields = {}

        for model_file in self.models_dir.glob("*.py"):
            if model_file.name == "__init__.py":
                continue

            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                model_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                if not model_match:
                    continue

                model_name = model_match.group(1)
                fields = set()

                # Find all field definitions
                field_pattern = r"(\w+)\s*=\s*fields\."
                for match in re.finditer(field_pattern, content):
                    field_name = match.group(1)
                    fields.add(field_name)

                # Remove inherited fields from analysis
                inherited = self.inherited_fields.get(model_name, set())
                custom_fields = fields - inherited

                model_fields[model_name] = custom_fields

            except Exception as e:
                print("Error processing {}: {}".format(model_file, e))

        return model_fields

    def _extract_view_fields(self) -> Dict[str, Set[str]]:
        """Extract fields used in views"""
        view_fields = {}

        for view_file in self.views_dir.glob("*.xml"):
            try:
                tree = ET.parse(view_file)
                for elem in tree.iter():
                    if elem.tag == 'record' and elem.get('model') == 'ir.ui.view':
                        model_elem = elem.find(".//field[@name='model']")
                        if model_elem is not None and model_elem.text:
                            model_name = model_elem.text
                            if model_name not in view_fields:
                                view_fields[model_name] = set()

                            # Find all field elements
                            for field_elem in elem.iter('field'):
                                field_name = field_elem.get('name')
                                if field_name:
                                    view_fields[model_name].add(field_name)

            except Exception as e:
                print("Error processing {}: {}".format(view_file, e))

        return view_fields

    def get_inherited_fields_summary(self) -> Dict[str, List[str]]:
        """Get summary of inherited fields being excluded from analysis"""
        summary = {}
        for model_name, inherited_fields in self.inherited_fields.items():
            if inherited_fields:
                summary[model_name] = sorted(list(inherited_fields))
        return summary

def main():
    """Main analysis function"""
    analyzer = OdooModelAnalyzer("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management")

    print("🔍 Odoo Model Relationship Analyzer (Custom Fields Only)")
    print("=" * 60)
    print("📝 Note: This analysis excludes inherited fields from mixins like:")
    print("   - mail.thread, mail.activity.mixin, portal.mixin")
    print("   - base model fields (id, create_date, write_date, etc.)")
    print("   Focus: Custom module issues only")
    print("=" * 60)

    # Show inherited fields summary
    inherited_summary = analyzer.get_inherited_fields_summary()
    if inherited_summary:
        print("\n🛡️  Inherited Fields Excluded from Analysis:")
        print("-" * 45)
        for model_name, fields in inherited_summary.items():
            print("  {}: {}".format(model_name, ", ".join(fields[:5]) + ("..." if fields[5:] else "")))
        print()

    # Run all analyses
    analyses = [
        ("Missing Inverse Relationships", analyzer.find_missing_inverses),
        ("Missing View Fields", analyzer.find_missing_view_fields),
        ("Calculation Errors", analyzer.find_calculation_errors),
        ("Security Issues", analyzer.find_security_issues)
    ]

    total_issues = 0
    for analysis_name, analysis_func in analyses:
        print("\n📋 {}:".format(analysis_name))
        print("-" * 30)
        issues = analysis_func()
        if issues:
            for issue in issues:
                severity_icon = {
                    'error': '❌',
                    'warning': '⚠️',
                    'info': 'ℹ️'
                }.get(issue.get('severity', 'info'), 'ℹ️')

                print("  {} {}".format(severity_icon, issue['message']))
                if 'file' in issue:
                    print("     File: {}".format(issue['file']))
        else:
            print("  ✅ No issues found")

        total_issues += len(issues)

    print("\n📊 Summary: {} issues found".format(total_issues))
    print("\n💡 Tip: Use Cybrosys Assista shortcuts for quick fixes!")
    print("   - 'Odoo Compute Method' for missing calculations")
    print("   - 'Odoo One2many Field' for missing inverses")
    print("   - 'Odoo View Inherit' for missing view fields")
    print("\n🎯 Focus: Only custom module issues shown above")

if __name__ == "__main__":
    main()
