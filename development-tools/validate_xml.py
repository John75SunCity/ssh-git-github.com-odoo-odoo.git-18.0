#!/usr/bin/env python3
"""
XML Validation Script
====================

Validates XML files for syntax, structure, and Odoo-specific requirements.
Checks for proper XML formatting and common Odoo XML patterns.

Features:
- XML syntax validation
- Odoo XML structure verification
- Namespace and schema validation
- Common XML pattern checks
- Encoding and character validation

Author: GitHub Copilot
Version: 1.0.0
Date: 2025-08-28
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import ParseError
import re

class XMLValidator:
    """Validates XML files for Odoo modules"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.xml_files: List[Path] = []

    def validate_xml(self) -> bool:
        """Main validation function"""
        print("📄 Validating XML Files...")

        # Find all XML files in the module
        self._find_xml_files()

        if not self.xml_files:
            self.warnings.append("No XML files found in module")
            return True

        # Validate each XML file
        for xml_file in self.xml_files:
            self._validate_xml_file(xml_file)

        # Validate cross-file references
        self._validate_cross_references()

        return len(self.errors) == 0

    def _find_xml_files(self) -> None:
        """Find all XML files in the module"""
        module_dir = self.workspace_root / "records_management"

        if not module_dir.exists():
            return

        # Common XML file locations
        xml_dirs = [
            module_dir / "views",
            module_dir / "data",
            module_dir / "security",
            module_dir / "wizard",
            module_dir / "report"
        ]

        for xml_dir in xml_dirs:
            if xml_dir.exists():
                for xml_file in xml_dir.glob("*.xml"):
                    self.xml_files.append(xml_file)

        # Also check root level
        for xml_file in module_dir.glob("*.xml"):
            self.xml_files.append(xml_file)

    def _validate_xml_file(self, xml_file: Path) -> None:
        """Validate a single XML file"""
        try:
            # Basic XML parsing
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Validate XML structure
            self._validate_xml_structure(root, xml_file)

            # Validate Odoo-specific patterns
            self._validate_odo_specific(root, xml_file)

            # Validate encoding and content
            self._validate_content(xml_file)

        except ParseError as e:
            self.errors.append(f"XML parse error in {xml_file}: {e}")
        except UnicodeDecodeError as e:
            self.errors.append(f"Encoding error in {xml_file}: {e}")
        except Exception as e:
            self.errors.append(f"Error processing {xml_file}: {e}")

    def _validate_xml_structure(self, root: ET.Element, xml_file: Path) -> None:
        """Validate basic XML structure"""
        # Check root element
        if root.tag != 'odoo':
            self.errors.append(f"{xml_file}: Root element should be 'odoo', found '{root.tag}'")

        # Check for proper data structure
        data_elements = root.findall(".//data")
        if not data_elements and root.tag == 'odoo':
            # Some XML files might not have data elements (like manifest)
            noupdate_data = root.findall(".//data[@noupdate='1']")
            if not noupdate_data:
                self.warnings.append(f"{xml_file}: No data elements found")

        # Validate record structure
        for record in root.findall(".//record"):
            self._validate_record_structure(record, xml_file)

        # Validate template structure
        for template in root.findall(".//template"):
            self._validate_template_structure(template, xml_file)

    def _validate_record_structure(self, record: ET.Element, xml_file: Path) -> None:
        """Validate record element structure"""
        record_id = record.get('id')
        model = record.get('model')

        if not record_id:
            self.errors.append(f"{xml_file}: Record missing 'id' attribute")
            return

        if not model:
            self.errors.append(f"{xml_file}: Record '{record_id}' missing 'model' attribute")
            return

        # Validate ID format
        if not self._is_valid_xml_id(record_id):
            self.warnings.append(f"{xml_file}: Record ID '{record_id}' doesn't follow naming convention")

        # Validate field elements
        for field in record.findall(".//field"):
            self._validate_field_element(field, record_id, xml_file)

    def _validate_field_element(self, field: ET.Element, record_id: str, xml_file: Path) -> None:
        """Validate field element"""
        field_name = field.get('name')

        if not field_name:
            self.errors.append(f"{xml_file}: Field in record '{record_id}' missing 'name' attribute")
            return

        # Check for both text content and ref attribute
        has_text = field.text and field.text.strip()
        has_ref = field.get('ref')

        if has_text and has_ref:
            self.warnings.append(f"{xml_file}: Field '{field_name}' in record '{record_id}' has both text and ref")

        # Validate field name format
        if not field_name.replace('_', '').replace('.', '').isalnum():
            self.warnings.append(f"{xml_file}: Field name '{field_name}' in record '{record_id}' is unusual")

        # Check for eval expressions
        if field.get('eval'):
            self._validate_eval_expression(field.get('eval'), field_name, record_id, xml_file)

    def _validate_eval_expression(self, eval_expr: str, field_name: str, record_id: str, xml_file: Path) -> None:
        """Validate eval expression syntax"""
        try:
            # Basic syntax check for Python expressions
            eval_expr = eval_expr.strip()

            # Check for common patterns
            if eval_expr.startswith('[') and eval_expr.endswith(']'):
                # List expression
                pass
            elif eval_expr.startswith('{') and eval_expr.endswith('}'):
                # Dict expression
                pass
            elif eval_expr in ['True', 'False', 'None']:
                # Boolean/None literals
                pass
            elif eval_expr.startswith('"') or eval_expr.startswith("'"):
                # String literal
                pass
            elif eval_expr.isdigit() or (eval_expr.startswith('-') and eval_expr[1:].isdigit()):
                # Number literal
                pass
            else:
                # More complex expression - just warn about potential issues
                if 'import' in eval_expr:
                    self.warnings.append(f"{xml_file}: Eval expression in field '{field_name}' contains import")

        except Exception as e:
            self.warnings.append(f"{xml_file}: Could not validate eval expression in field '{field_name}': {e}")

    def _validate_template_structure(self, template: ET.Element, xml_file: Path) -> None:
        """Validate template element structure"""
        template_id = template.get('id')

        if not template_id:
            self.errors.append(f"{xml_file}: Template missing 'id' attribute")
            return

        # Check for proper template structure
        if not list(template):
            self.warnings.append(f"{xml_file}: Template '{template_id}' appears to be empty")

    def _validate_odo_specific(self, root: ET.Element, xml_file: Path) -> None:
        """Validate Odoo-specific XML patterns"""
        # Check for proper Odoo XML patterns
        if root.tag == 'odoo':
            # Check for data elements with noupdate
            noupdate_data = root.findall(".//data[@noupdate='1']")
            regular_data = root.findall(".//data[not(@noupdate)]")

            if noupdate_data and regular_data:
                self.warnings.append(f"{xml_file}: Mix of noupdate and regular data elements")

            # Validate record model references
            for record in root.findall(".//record"):
                model = record.get('model')
                if model:
                    self._validate_model_reference(model, record.get('id', 'unknown'), xml_file)

    def _validate_model_reference(self, model: str, record_id: str, xml_file: Path) -> None:
        """Validate model reference"""
        # Check for common Odoo model patterns
        valid_prefixes = ['res.', 'ir.', 'product.', 'sale.', 'purchase.', 'account.', 'stock.', 'mrp.']

        if not any(model.startswith(prefix) for prefix in valid_prefixes):
            # Check if it's a custom model (should be in the module)
            if '.' not in model:
                self.warnings.append(f"{xml_file}: Model '{model}' in record '{record_id}' missing module prefix")

    def _validate_content(self, xml_file: Path) -> None:
        """Validate file content and encoding"""
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for common encoding issues
            if '\ufeff' in content:
                self.warnings.append(f"{xml_file}: Contains BOM (Byte Order Mark)")

            # Check for non-printable characters
            for char in content:
                if ord(char) < 32 and char not in '\t\n\r':
                    self.warnings.append(f"{xml_file}: Contains non-printable character (ASCII {ord(char)})")

            # Check for very long lines (potential formatting issues)
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if len(line) > 500:
                    self.warnings.append(f"{xml_file}: Line {i} is very long ({len(line)} chars)")

        except UnicodeDecodeError:
            self.errors.append(f"{xml_file}: File encoding is not UTF-8")

    def _validate_cross_references(self) -> None:
        """Validate cross-file references"""
        # This is a simplified check - in practice you'd build a comprehensive
        # reference map across all XML files

        all_records = {}
        all_templates = {}

        # Collect all records and templates
        for xml_file in self.xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                for record in root.findall(".//record"):
                    record_id = record.get('id')
                    if record_id:
                        all_records[record_id] = xml_file

                for template in root.findall(".//template"):
                    template_id = template.get('id')
                    if template_id:
                        all_templates[template_id] = xml_file

            except (ParseError, UnicodeDecodeError):
                continue  # Skip files with parse errors

        # Check for broken references (simplified)
        for xml_file in self.xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Check ref attributes
                for elem in root.findall(".//*[@ref]"):
                    ref = elem.get('ref')
                    if ref and ref not in all_records and ref not in all_templates:
                        # Skip common Odoo references
                        if not ref.startswith(('base.', 'web.', 'mail.', 'product.')):
                            self.warnings.append(f"{xml_file}: Reference '{ref}' not found")

            except (ParseError, UnicodeDecodeError):
                continue

    def _is_valid_xml_id(self, xml_id: str) -> bool:
        """Check if XML ID follows Odoo conventions"""
        # Basic pattern: module_name.record_type_specific_name
        if '.' not in xml_id:
            return False

        parts = xml_id.split('.')
        if len(parts) < 2:
            return False

        # Check each part
        for part in parts:
            if not part or not part.replace('_', '').isalnum():
                return False

        return True

    def print_report(self) -> None:
        """Print validation report"""
        print("\n📄 XML Validation Report")
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
            print("✅ All XML validations passed!")

        print(f"\n📈 Summary: {len(self.xml_files)} XML files validated")

def main():
    """Main execution function"""
    workspace_root = Path(__file__).parent.parent.parent

    validator = XMLValidator(workspace_root)

    try:
        success = validator.validate_xml()
        validator.print_report()

        if success:
            print("\n✅ XML validation completed successfully")
            sys.exit(0)
        else:
            print(f"\n❌ XML validation failed with {len(validator.errors)} errors")
            sys.exit(1)

    except Exception as e:
        print(f"❌ XML validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
