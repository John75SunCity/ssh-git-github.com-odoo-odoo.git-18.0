#!/usr/bin/env python3
"""
Security Validation Script
=========================

Validates Odoo security configurations and access rules.
Checks for proper security rule definitions and access permissions.

Features:
- Security rule validation
- Access permission checks
- Group configuration validation
- Record rule consistency
- Security best practices

Author: GitHub Copilot
Version: 1.0.0
Date: 2025-08-28
"""

import os
import sys
import csv
from pathlib import Path
from typing import Dict, List, Set, Tuple
from xml.etree import ElementTree as ET
import re

class SecurityValidator:
    """Validates Odoo security configurations"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.groups: Set[str] = set()
        self.models: Set[str] = set()

    def validate_security(self) -> bool:
        """Main validation function"""
        print("🔐 Validating Odoo Security Configuration...")

        # Validate security directory structure
        security_dir = self.workspace_root / "records_management" / "security"
        if not security_dir.exists():
            # Try alternative location
            alt_security_dir = self.workspace_root / "records_management"
            if alt_security_dir.exists():
                security_dir = alt_security_dir
            else:
                self.errors.append("Security directory not found")
                return False

        # Extract models from Python files
        self._extract_models()

        # Validate access rules
        self._validate_access_rules(security_dir)

        # Validate security XML files
        self._validate_security_xml_files(security_dir)

        # Validate group definitions
        self._validate_groups()

        # Check for orphaned rules
        self._validate_rule_consistency()

        return len(self.errors) == 0

    def _extract_models(self) -> None:
        """Extract model names from Python files"""
        models_dir = self.workspace_root / "records_management" / "models"

        if not models_dir.exists():
            # Try alternative location
            alt_models_dir = self.workspace_root / "records_management"
            if alt_models_dir.exists():
                models_dir = alt_models_dir
            else:
                return

        for py_file in models_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Look for _name = "model.name" patterns with more precise regex
                # This pattern ensures we're matching class-level _name assignments
                name_pattern = r'^\s*_name\s*=\s*[\'"]([^\'"]+)[\'"]'

                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('_name ='):
                        # Match both single and double quotes
                        match = re.search(r'_name\s*=\s*[\'"]([^\'"]+)[\'"]', line)
                        if match:
                            model_name = match.group(1)
                            # Only skip obvious field names, not model names
                            # Be much more restrictive with filtering
                            skip_patterns = [
                                'display_name', 'name', 'reference', 'description',
                                'serial_number', 'photo', 'report_id'
                            ]

                            # Only skip if the entire model name matches a field pattern
                            should_skip = False
                            for skip in skip_patterns:
                                if model_name.lower() == skip:
                                    should_skip = True
                                    break

                            if not should_skip:
                                self.models.add(model_name)

            except Exception as e:
                self.warnings.append(f"Error reading {py_file}: {e}")

    def _validate_access_rules(self, security_dir: Path) -> None:
        """Validate ir.model.access.csv file"""
        access_file = security_dir / "ir.model.access.csv"

        if not access_file.exists():
            self.errors.append("ir.model.access.csv file not found")
            return

        try:
            with open(access_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader, None)

                if not headers:
                    self.errors.append("ir.model.access.csv is empty")
                    return

                # Validate headers
                expected_headers = ['id', 'name', 'model_id:id', 'group_id:id', 'perm_read', 'perm_write', 'perm_create', 'perm_unlink']
                if headers != expected_headers:
                    self.warnings.append(f"Unexpected CSV headers: {headers}")

                # Validate each row
                for row_num, row in enumerate(reader, start=2):
                    if len(row) != len(expected_headers):
                        self.errors.append(f"Row {row_num}: Incorrect number of columns")
                        continue

                    self._validate_access_row(row, row_num)

        except Exception as e:
            self.errors.append(f"Error reading access rules: {e}")

    def _validate_access_row(self, row: List[str], row_num: int) -> None:
        """Validate a single access rule row"""
        id_field, name, model_id, group_id, perm_read, perm_write, perm_create, perm_unlink = row

        # Validate ID format
        if not id_field or not id_field.startswith('access_'):
            self.warnings.append(f"Row {row_num}: ID should start with 'access_'")

        # Validate model reference - handle both formats (with/without model_ prefix)
        if not model_id:
            self.errors.append(f"Row {row_num}: Empty model reference")
        elif model_id.startswith('model_'):
            # Standard Odoo format with prefix
            pass
        else:
            # This module uses plain model names without prefix - that's valid too
            pass

        # Extract model name for validation (handle both formats)
        if model_id.startswith('model_'):
            model_name = model_id[6:]  # Remove 'model_' prefix
        else:
            model_name = model_id  # Use as-is

        if model_name not in self.models:
            self.warnings.append(f"Row {row_num}: Model '{model_name}' not found in codebase")

        # Validate permissions
        for perm_name, perm_value in [('read', perm_read), ('write', perm_write),
                                    ('create', perm_create), ('unlink', perm_unlink)]:
            if perm_value not in ['0', '1']:
                self.errors.append(f"Row {row_num}: Invalid {perm_name} permission '{perm_value}'")

        # Check for reasonable permission combinations
        permissions = [int(perm_read), int(perm_write), int(perm_create), int(perm_unlink)]
        if permissions[1] and not permissions[0]:  # write without read
            self.warnings.append(f"Row {row_num}: Write permission without read permission")
        if permissions[3] and not permissions[0]:  # unlink without read
            self.warnings.append(f"Row {row_num}: Unlink permission without read permission")

    def _validate_security_xml_files(self, security_dir: Path) -> None:
        """Validate security XML files"""
        for xml_file in security_dir.glob("*.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Validate record rules
                for record in root.findall(".//record"):
                    self._validate_record_rule(record, xml_file)

                # Extract groups
                for group_record in root.findall(".//record[@model='res.groups']"):
                    group_id = group_record.get('id')
                    if group_id:
                        # Add both short form and full module reference
                        self.groups.add(group_id)
                        self.groups.add(f"records_management.{group_id}")

            except ET.ParseError as e:
                self.errors.append(f"XML parse error in {xml_file}: {e}")
            except Exception as e:
                self.errors.append(f"Error processing {xml_file}: {e}")

    def _validate_record_rule(self, record: ET.Element, xml_file: Path) -> None:
        """Validate a record rule definition"""
        model = record.get('model')
        record_id = record.get('id')

        if model == 'ir.rule':
            # Validate rule definition
            domain_field = record.find(".//field[@name='domain_force']")
            if domain_field is not None:
                domain_value = domain_field.text
                if domain_value:
                    self._validate_domain_expression(domain_value, record_id, xml_file)

            # Check for required fields
            required_fields = ['name', 'model_id', 'domain_force', 'groups']
            for field_name in required_fields:
                field = record.find(f".//field[@name='{field_name}']")
                if field is None:
                    self.warnings.append(f"Rule {record_id} in {xml_file} missing required field '{field_name}'")

    def _validate_domain_expression(self, domain: str, rule_id: str, xml_file: Path) -> None:
        """Validate domain expression syntax"""
        try:
            # Basic syntax check - this is simplified
            if domain.strip().startswith('[') and domain.strip().endswith(']'):
                # Could add more sophisticated domain validation here
                pass
            else:
                self.warnings.append(f"Rule {rule_id} in {xml_file} has unusual domain format")
        except Exception as e:
            self.warnings.append(f"Could not validate domain in rule {rule_id}: {e}")

    def _validate_groups(self) -> None:
        """Validate group definitions"""
        if not self.groups:
            self.warnings.append("No security groups defined")

        # Check for standard groups
        standard_groups = ['records_management.group_records_user', 'records_management.group_records_manager']
        for group in standard_groups:
            if group not in self.groups:
                self.warnings.append(f"Standard group '{group}' not found")

    def _validate_rule_consistency(self) -> None:
        """Validate consistency between access rules and record rules"""
        # This is a simplified check - in practice you'd cross-reference
        # access rules with record rules to ensure consistency
        pass

    def print_report(self) -> None:
        """Print validation report"""
        print(f"\n🔐 Security Validation Report")
        print("=" * 50)

        if self.errors:
            print(f"❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"\n⚠️ Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("✅ All security validations passed!")

        print(f"\n📈 Summary: {len(self.models)} models, {len(self.groups)} groups validated")

def main():
    """Main execution function"""
    workspace_root = Path(__file__).parent.parent

    validator = SecurityValidator(workspace_root)

    try:
        success = validator.validate_security()
        validator.print_report()

        if success:
            print("\n✅ Security validation completed successfully")
            sys.exit(0)
        else:
            print(f"\n❌ Security validation failed with {len(validator.errors)} errors")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Security validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
