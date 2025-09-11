#!/usr/bin/env python3
"""
Odoo Security & Access Analyzer
Uses Cybrosys Assista patterns to analyze security rules and access controls.

This script helps identify security vulnerabilities, missing access rules,
and permission inconsistencies in Odoo modules.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set


class OdooSecurityAnalyzer:
    """Analyze Odoo security using Cybrosys Assista patterns"""

    def __init__(self, module_path: str):
        self.module_path = Path(module_path)
        self.models_dir = self.module_path / "models"
        self.security_dir = self.module_path / "security"

    def find_missing_access_rules(self) -> List[Dict]:
        """Find models missing access rules"""
        issues = []

        # Get all models
        models = self._extract_models()

        # Get all access rules
        access_rules = self._extract_access_rules()

        for model_name in models:
            if model_name not in access_rules:
                issues.append({
                    'type': 'missing_access',
                    'model': model_name,
                    'severity': 'error',
                    'message': f"Model '{model_name}' has no access rules defined",
                    'fix_suggestion': 'Add ir.model.access records for user and manager groups'
                })

        return issues

    def find_inconsistent_permissions(self) -> List[Dict]:
        """Find inconsistent permission patterns"""
        issues = []

        access_rules = self._extract_access_rules()

        for model_name, rules in access_rules.items():
            # Check for both user and manager access
            has_user = any('user' in rule_id.lower() for rule_id in rules)
            has_manager = any('manager' in rule_id.lower() for rule_id in rules)

            if not has_user:
                issues.append({
                    'type': 'missing_user_access',
                    'model': model_name,
                    'severity': 'warning',
                    'message': f"Model '{model_name}' missing user-level access rule",
                    'fix_suggestion': 'Add access rule with perm_read=1, perm_write=1, perm_create=1, perm_unlink=0'
                })

            if not has_manager:
                issues.append({
                    'type': 'missing_manager_access',
                    'model': model_name,
                    'severity': 'warning',
                    'message': f"Model '{model_name}' missing manager-level access rule",
                    'fix_suggestion': 'Add access rule with perm_read=1, perm_write=1, perm_create=1, perm_unlink=1'
                })

        return issues

    def find_security_rule_issues(self) -> List[Dict]:
        """Find issues in security rules (ir.rule)"""
        issues = []

        for security_file in self.security_dir.glob("*.xml"):
            try:
                tree = ET.parse(security_file)
                for elem in tree.iter():
                    if elem.tag == 'record' and elem.get('model') == 'ir.rule':
                        rule_id = elem.get('id', 'unknown')

                        # Check domain syntax
                        domain_elem = elem.find(".//field[@name='domain_force']")
                        if domain_elem is not None and domain_elem.text:
                            domain = domain_elem.text.strip()
                            if domain:
                                issues.extend(self._validate_domain_syntax(domain, rule_id, security_file))

                        # Check groups reference
                        groups_elem = elem.find(".//field[@name='groups']")
                        if groups_elem is not None and groups_elem.text:
                            issues.extend(self._validate_groups_reference(groups_elem.text, rule_id, security_file))

            except Exception as e:
                issues.append({
                    'type': 'xml_parse_error',
                    'file': str(security_file),
                    'severity': 'error',
                    'message': f"Error parsing security file: {str(e)}"
                })

        return issues

    def find_orphaned_groups(self) -> List[Dict]:
        """Find security groups not referenced in any rules"""
        issues = []

        groups = self._extract_groups()
        referenced_groups = self._extract_referenced_groups()

        for group_id in groups:
            if group_id not in referenced_groups:
                issues.append({
                    'type': 'orphaned_group',
                    'group': group_id,
                    'severity': 'info',
                    'message': f"Security group '{group_id}' is not referenced in any access rules",
                    'fix_suggestion': 'Remove unused group or add it to relevant access rules'
                })

        return issues

    def _extract_models(self) -> Set[str]:
        """Extract all model names from Python files"""
        models = set()

        for model_file in self.models_dir.glob("*.py"):
            if model_file.name == "__init__.py":
                continue

            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find _name definitions
                name_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                models.update(name_matches)

            except Exception as e:
                print(f"Error reading {model_file}: {e}")

        return models

    def _extract_access_rules(self) -> Dict[str, Dict]:
        """Extract access rules from ir.model.access.csv"""
        access_rules = {}

        csv_file = self.security_dir / "ir.model.access.csv"
        if csv_file.exists():
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 6:
                            rule_id, model_name = parts[0], parts[2]
                            if model_name not in access_rules:
                                access_rules[model_name] = {}
                            access_rules[model_name][rule_id] = parts

            except Exception as e:
                print(f"Error reading access CSV: {e}")

        return access_rules

    def _extract_groups(self) -> Set[str]:
        """Extract all security groups"""
        groups = set()

        for security_file in self.security_dir.glob("*.xml"):
            try:
                tree = ET.parse(security_file)
                for elem in tree.iter():
                    if elem.tag == 'record' and elem.get('model') == 'res.groups':
                        group_id = elem.get('id')
                        if group_id:
                            groups.add(group_id)
            except Exception as e:
                print(f"Error parsing {security_file}: {e}")

        return groups

    def _extract_referenced_groups(self) -> Set[str]:
        """Extract groups referenced in rules"""
        referenced = set()

        for security_file in self.security_dir.glob("*.xml"):
            try:
                tree = ET.parse(security_file)
                for elem in tree.iter():
                    if elem.tag == 'record' and elem.get('model') == 'ir.rule':
                        groups_elem = elem.find(".//field[@name='groups']")
                        if groups_elem is not None and groups_elem.text:
                            # Extract group references from eval expression
                            group_refs = re.findall(r"ref\(['\"]([^'\"]+)['\"]\)", groups_elem.text)
                            referenced.update(group_refs)
            except Exception as e:
                print(f"Error parsing {security_file}: {e}")

        return referenced

    def _validate_domain_syntax(self, domain: str, rule_id: str, file_path: Path) -> List[Dict]:
        """Validate domain syntax"""
        issues = []

        # Basic syntax checks
        if not (domain.startswith('[') and domain.endswith(']')):
            issues.append({
                'type': 'invalid_domain_syntax',
                'file': str(file_path),
                'rule': rule_id,
                'severity': 'error',
                'message': f"Invalid domain syntax: {domain}",
                'fix_suggestion': 'Domain should be a list: [(field, operator, value), ...]'
            })

        # Check for common mistakes
        if 'user.partner_id' in domain and 'user.partner_id.id' not in domain:
            issues.append({
                'type': 'domain_field_reference',
                'file': str(file_path),
                'rule': rule_id,
                'severity': 'warning',
                'message': f"Domain may need proper field reference: {domain}",
                'fix_suggestion': 'Use user.partner_id.id instead of user.partner_id for Many2one comparisons'
            })

        return issues

    def _validate_groups_reference(self, groups_text: str, rule_id: str, file_path: Path) -> List[Dict]:
        """Validate groups references"""
        issues = []

        # Check for proper reference format
        if 'ref(' not in groups_text:
            issues.append({
                'type': 'invalid_groups_format',
                'file': str(file_path),
                'rule': rule_id,
                'severity': 'error',
                'message': f"Invalid groups reference format: {groups_text}",
                'fix_suggestion': 'Use [(4, ref(\'group_id\'))] format for groups'
            })

        return issues

def main():
    """Main security analysis function"""
    analyzer = OdooSecurityAnalyzer("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management")

    print("🔒 Odoo Security & Access Analyzer")
    print("=" * 50)

    # Run all security analyses
    analyses = [
        ("Missing Access Rules", analyzer.find_missing_access_rules),
        ("Inconsistent Permissions", analyzer.find_inconsistent_permissions),
        ("Security Rule Issues", analyzer.find_security_rule_issues),
        ("Orphaned Groups", analyzer.find_orphaned_groups)
    ]

    total_issues = 0
    for analysis_name, analysis_func in analyses:
        print(f"\n🛡️ {analysis_name}:")
        print("-" * 30)
        issues = analysis_func()
        if issues:
            for issue in issues:
                severity_icon = {
                    'error': '❌',
                    'warning': '⚠️',
                    'info': 'ℹ️'
                }.get(issue.get('severity', 'info'), 'ℹ️')

                print(f"  {severity_icon} {issue['message']}")
                if 'fix_suggestion' in issue:
                    print(f"     💡 {issue['fix_suggestion']}")
        else:
            print("  ✅ No issues found")

        total_issues += len(issues)

    print(f"\n📊 Summary: {total_issues} security issues found")
    print("\n💡 Cybrosys Assista Security Tips:")
    print("   - Use 'Odoo Security File' template for new access rules")
    print("   - Apply 'Odoo Constraints Method' for data validation")
    print("   - Use 'Odoo Action Method' for secure business logic")

if __name__ == "__main__":
    main()
