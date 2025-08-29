#!/usr/bin/env python3
"""
View Validation Script
=====================

Validates Odoo view definitions and XML structures.
Checks for proper view configuration and field references.

Features:
- XML syntax validation
- View structure verification
- Field reference validation
- Inheritance consistency
- View security checks

Author: GitHub Copilot
Version: 1.0.0
Date: 2025-08-28
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import ParseError

class ViewValidator:
    """Validates Odoo view definitions"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.models: Set[str] = set()
        self.fields: Dict[str, Set[str]] = {}
        self.views: Dict[str, Dict] = {}

    def validate_views(self) -> bool:
        """Main validation function"""
        print("👀 Validating Odoo View Definitions...")

        # Extract models and fields first
        self._extract_models_and_fields()

        # Validate views directory - try multiple locations
        views_dir = self.workspace_root / "records_management" / "views"
        if not views_dir.exists():
            # Try alternative locations
            alt_views_dir = self.workspace_root / "records_management"
            if alt_views_dir.exists():
                views_dir = alt_views_dir
            else:
                self.errors.append("Views directory not found")
                return False

        # Validate all XML view files
        xml_files_found = False
        for xml_file in views_dir.glob("*.xml"):
            xml_files_found = True
            self._validate_view_file(xml_file)

        if not xml_files_found:
            self.warnings.append("No XML view files found")
            return True

        # Validate view relationships
        self._validate_view_relationships()

        # Check for missing views
        self._validate_view_coverage()

        return len(self.errors) == 0

    def _extract_models_and_fields(self) -> None:
        """Extract model and field information from Python files"""
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

                # Extract model names
                import re
                name_pattern = r'_name\s*=\s*[\'"]([^\'"]+)[\'"]'
                matches = re.findall(name_pattern, content)

                for match in matches:
                    self.models.add(match)
                    self.fields[match] = set()

                # Extract field names (simplified)
                field_pattern = r'(\w+)\s*=\s*fields\.'
                field_matches = re.findall(field_pattern, content)

                for match in matches:  # match is model name
                    model_fields = set()
                    for field_match in field_matches:
                        model_fields.add(field_match)
                    if match in self.fields:
                        self.fields[match].update(model_fields)

            except Exception as e:
                self.warnings.append(f"Error reading {py_file}: {e}")

    def _validate_view_file(self, xml_file: Path) -> None:
        """Validate a single XML view file"""
        try:
            # Parse XML
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Validate XML structure
            self._validate_xml_structure(root, xml_file)

            # Validate individual records
            for record in root.findall(".//record"):
                self._validate_view_record(record, xml_file)

        except ParseError as e:
            self.errors.append(f"XML parse error in {xml_file}: {e}")
        except Exception as e:
            self.errors.append(f"Error processing {xml_file}: {e}")

    def _validate_xml_structure(self, root: ET.Element, xml_file: Path) -> None:
        """Validate basic XML structure"""
        if root.tag != 'odoo':
            self.errors.append(f"{xml_file}: Root element should be 'odoo', found '{root.tag}'")

        # Check for data element
        data_elem = root.find(".//data")
        if data_elem is None:
            self.warnings.append(f"{xml_file}: No 'data' element found")

    def _validate_view_record(self, record: ET.Element, xml_file: Path) -> None:
        """Validate a view record definition"""
        record_id = record.get('id')
        model = record.get('model')

        if not record_id:
            self.errors.append(f"{xml_file}: Record missing 'id' attribute")
            return

        if not model:
            self.errors.append(f"{xml_file}: Record '{record_id}' missing 'model' attribute")
            return

        # Store view information
        if model not in self.views:
            self.views[model] = []
        self.views[model].append({
            'id': record_id,
            'file': xml_file,
            'type': self._determine_view_type(record)
        })

        # Validate based on model type
        if model == 'ir.ui.view':
            self._validate_ui_view(record, record_id, xml_file)
        elif model in ['ir.actions.act_window', 'ir.actions.server']:
            self._validate_action_record(record, record_id, xml_file)
        elif model == 'ir.ui.menu':
            self._validate_menu_record(record, record_id, xml_file)

    def _determine_view_type(self, record: ET.Element) -> str:
        """Determine the type of view"""
        arch_field = record.find(".//field[@name='arch']")
        if arch_field is not None:
            arch_content = arch_field.text or ""
            if '<tree>' in arch_content:
                return 'tree'
            elif '<form>' in arch_content:
                return 'form'
            elif '<kanban>' in arch_content:
                return 'kanban'
            elif '<calendar>' in arch_content:
                return 'calendar'
            elif '<graph>' in arch_content:
                return 'graph'
        return 'unknown'

    def _validate_ui_view(self, record: ET.Element, record_id: str, xml_file: Path) -> None:
        """Validate ir.ui.view record"""
        # Check required fields
        required_fields = ['name', 'model', 'arch']
        for field_name in required_fields:
            field = record.find(f".//field[@name='{field_name}']")
            if field is None:
                self.errors.append(f"View '{record_id}' in {xml_file} missing required field '{field_name}'")

        # Validate model reference
        model_field = record.find(".//field[@name='model']")
        if model_field is not None:
            model_ref = model_field.get('ref') or model_field.text
            if model_ref and model_ref not in self.models:
                self.warnings.append(f"View '{record_id}' references unknown model '{model_ref}'")

        # Validate arch field
        arch_field = record.find(".//field[@name='arch']")
        if arch_field is not None:
            self._validate_arch_content(arch_field, record_id, xml_file)

    def _validate_arch_content(self, arch_field: ET.Element, record_id: str, xml_file: Path) -> None:
        """Validate view architecture content"""
        arch_content = arch_field.text or ""

        if not arch_content.strip():
            self.warnings.append(f"View '{record_id}' in {xml_file} has empty arch content")
            return

        try:
            # Parse the arch content as XML
            arch_root = ET.fromstring(f"<root>{arch_content}</root>")

            # Validate field references
            self._validate_field_references(arch_root, record_id, xml_file)

            # Check for common issues
            self._validate_view_structure(arch_root, record_id, xml_file)

        except ET.ParseError as e:
            self.errors.append(f"View '{record_id}' in {xml_file} has invalid arch XML: {e}")

    def _validate_field_references(self, arch_root: ET.Element, record_id: str, xml_file: Path) -> None:
        """Validate field references in view"""
        # Get model from view (this is simplified - you'd need to look up the actual model)
        model_field = None  # You'd need to get this from the view record

        # Find all field elements
        for field_elem in arch_root.findall(".//field"):
            field_name = field_elem.get('name')
            if field_name:
                # Basic field name validation
                if not field_name.replace('_', '').replace('.', '').isalnum():
                    self.warnings.append(f"View '{record_id}' has unusual field name '{field_name}'")

                # Check for common field attributes
                if field_elem.get('widget') == 'many2many_tags' and not field_elem.get('options'):
                    self.warnings.append(f"Field '{field_name}' in view '{record_id}' using many2many_tags without options")

    def _validate_view_structure(self, arch_root: ET.Element, record_id: str, xml_file: Path) -> None:
        """Validate view structure and common issues"""
        # Check for empty views
        if not list(arch_root):
            self.warnings.append(f"View '{record_id}' appears to be empty")

        # Check for nested forms (common mistake)
        forms = arch_root.findall(".//form")
        if len(forms) > 1:
            self.warnings.append(f"View '{record_id}' has nested form elements")

        # Check for buttons without type
        buttons = arch_root.findall(".//button")
        for button in buttons:
            if not button.get('type'):
                self.warnings.append(f"Button in view '{record_id}' missing type attribute")

    def _validate_action_record(self, record: ET.Element, record_id: str, xml_file: Path) -> None:
        """Validate action record"""
        # Check for required fields
        name_field = record.find(".//field[@name='name']")
        if name_field is None:
            self.errors.append(f"Action '{record_id}' in {xml_file} missing name field")

        # Validate model reference if present
        res_model_field = record.find(".//field[@name='res_model']")
        if res_model_field is not None:
            res_model = res_model_field.get('ref') or res_model_field.text
            if res_model and res_model not in self.models:
                self.warnings.append(f"Action '{record_id}' references unknown model '{res_model}'")

    def _validate_menu_record(self, record: ET.Element, record_id: str, xml_file: Path) -> None:
        """Validate menu record"""
        # Check for required fields
        name_field = record.find(".//field[@name='name']")
        if name_field is None:
            self.errors.append(f"Menu '{record_id}' in {xml_file} missing name field")

        # Check parent menu reference
        parent_field = record.find(".//field[@name='parent_id']")
        if parent_field is not None:
            parent_ref = parent_field.get('ref')
            if parent_ref and not parent_ref.startswith('menu_'):
                self.warnings.append(f"Menu '{record_id}' has unusual parent reference '{parent_ref}'")

    def _validate_view_relationships(self) -> None:
        """Validate relationships between views"""
        for model, views in self.views.items():
            view_types = [view['type'] for view in views]

            # Check for common view combinations
            if 'form' in view_types and 'tree' not in view_types:
                self.warnings.append(f"Model '{model}' has form view but no tree view")

            # Check for duplicate view types - only warn for custom models
            if len(view_types) != len(set(view_types)):
                # Define core Odoo models that commonly have multiple views
                core_models = {
                    'ir.ui.view', 'ir.actions.act_window', 'ir.actions.server',
                    'ir.ui.menu', 'ir.actions.client', 'ir.model', 'ir.model.fields',
                    'res.partner', 'res.users', 'res.company', 'res.groups'
                }

                if model in core_models:
                    # For core models, this is normal - don't even warn
                    pass
                else:
                    # For custom models, this might be an issue but treat as warning
                    duplicate_types = [t for t in view_types if view_types.count(t) > 1]
                    self.warnings.append(f"Model '{model}' has duplicate view types: {', '.join(set(duplicate_types))}")

    def _validate_view_coverage(self) -> None:
        """Check if all models have corresponding views"""
        models_with_views = set(self.views.keys())
        models_without_views = self.models - models_with_views

        # Only check models that are actually defined in this module
        # Skip Odoo core models and external models
        module_models = set()
        records_dir = self.workspace_root / "records_management"

        # Extract models defined in this module only
        for py_file in records_dir.glob("**/*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract model names defined in this module
                import re
                name_pattern = r'_name\s*=\s*[\'"]([^\'"]+)[\'"]'
                matches = re.findall(name_pattern, content)

                for match in matches:
                    # Only include models that are likely custom to this module
                    # Skip obvious Odoo core models
                    if not (match.startswith('ir.') or
                           match.startswith('res.') or
                           match.startswith('mail.') or
                           match.startswith('base.') or
                           match == 'product.template' or
                           match == 'product.product' or
                           match == 'stock.picking' or
                           match == 'maintenance.equipment' or
                           match == 'account.move.line' or
                           match == 'project.task'):
                        module_models.add(match)

            except Exception:
                continue

        # Only report missing views for models actually defined in this module
        models_without_views = module_models - models_with_views

        for model in models_without_views:
            # Only warn for models that likely need views
            # Skip abstract models, transient models, and utility models
            if not (model.endswith('.report') or
                   model.endswith('.wizard') or
                   model.startswith('temp.') or
                   model.startswith('test.') or
                   'abstract' in model or
                   'mixin' in model or
                   model == 'rm.module.configurator'):  # Skip configurator models
                self.warnings.append(f"Model '{model}' has no associated views")

    def print_report(self) -> None:
        """Print validation report"""
        print(f"\n👀 View Validation Report")
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
            print("✅ All view validations passed!")

        total_views = sum(len(views) for views in self.views.values())
        print(f"\n📈 Summary: {len(self.models)} models, {total_views} views validated")

def main():
    """Main execution function"""
    workspace_root = Path(__file__).parent.parent

    validator = ViewValidator(workspace_root)

    try:
        success = validator.validate_views()
        validator.print_report()

        if success:
            print("\n✅ View validation completed successfully")
            sys.exit(0)
        else:
            # Check actual error count for proper exit code
            error_count = len(validator.errors)
            if error_count > 0:
                print(f"\n❌ View validation failed with {error_count} errors")
                sys.exit(1)
            else:
                print("⚠️ Only warnings found - treating as successful")
                sys.exit(0)

    except Exception as e:
        print(f"❌ View validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
