#!/usr/bin/env python3
"""
Mass View Field Validator & Auto-Fixer
Scans all 300 XML view files and validates field references against model definitions
Performs automated bulk fixes for common patterns
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
import subprocess

class MassViewFieldValidator:
    def __init__(self, records_management_path):
        self.base_path = records_management_path
        self.models_path = os.path.join(records_management_path, 'models')
        self.views_path = os.path.join(records_management_path, 'views')

        # Model field mappings
        self.model_fields = {}  # {model_name: {field_name: field_type}}
        self.field_errors = []  # List of field validation errors
        self.auto_fixes = []    # List of automatic fixes applied
        self.manual_review = [] # Complex issues requiring manual review

        # Common field mapping patterns from actual fixes
        self.field_mappings = {
            'status': 'state',  # Common pattern: status -> state
            'quality_grade': 'inspection_type',  # Specific pattern we found
            'load_number': 'name',  # paper.load.shipment pattern
            'pickup_date': 'scheduled_pickup_date',  # shipment pattern
            'driver_name': 'driver_id',  # Many2one relationship
            'partner_id': 'carrier_id',  # specific model mappings
        }

        # Menu parent reference fixes
        self.menu_mappings = {
            'records_management_main_menu': 'menu_records_management_root',
        }

        # Related field patterns to check
        self.relation_patterns = {
            'Many2one': ['_id'],  # Many2one fields usually end with _id
            'One2many': ['_ids'], # One2many fields usually end with _ids
            'Many2many': ['_ids'], # Many2many fields usually end with _ids
        }

        # Models to skip (external dependencies)
        self.skip_models = {
            'ir.ui.view', 'ir.actions.act_window', 'ir.ui.menu',
            'res.partner', 'res.users', 'res.company', 'account.move'
        }

    def scan_all_models(self):
        """Scan all Python model files to extract field definitions"""
        print("🔍 Scanning all Python models for field definitions...")

        for filename in os.listdir(self.models_path):
            if filename.endswith('.py') and filename != '__init__.py':
                self._parse_model_file(os.path.join(self.models_path, filename))

        print(f"✅ Found {len(self.model_fields)} models with field definitions")
        return self.model_fields

    def _parse_model_file(self, file_path):
        """Parse a single Python model file for field definitions"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract model names
            model_matches = re.findall(r'_name\s*=\s*[\'"]([^\'"]+)[\'"]', content)

            for model_name in model_matches:
                if model_name not in self.skip_models:
                    self.model_fields[model_name] = self._extract_fields_from_content(content)

        except Exception as e:
            print(f"⚠️  Error parsing {file_path}: {e}")

    def _extract_fields_from_content(self, content):
        """Extract field definitions from model file content"""
        fields = {}

        # Match field definitions: field_name = fields.FieldType(...)
        field_pattern = r'(\w+)\s*=\s*fields\.(\w+)\s*\('
        matches = re.findall(field_pattern, content)

        for field_name, field_type in matches:
            # Skip private/magic fields
            if not field_name.startswith('_'):
                fields[field_name] = field_type

        # Add common inherited fields
        if 'mail.thread' in content:
            fields.update({
                'message_ids': 'One2many',
                'message_follower_ids': 'One2many',
                'activity_ids': 'One2many'
            })

        # Add common base fields
        fields.update({
            'id': 'Integer',
            'create_date': 'Datetime',
            'create_uid': 'Many2one',
            'write_date': 'Datetime',
            'write_uid': 'Many2one',
            'display_name': 'Char'
        })

        return fields

    def scan_all_views(self):
        """Scan all XML view files for field validation errors"""
        print("🔍 Scanning all 300 XML view files for field references...")

        view_files = [f for f in os.listdir(self.views_path) if f.endswith('.xml')]

        for view_file in view_files:
            file_path = os.path.join(self.views_path, view_file)
            self._validate_view_file(file_path)
            self._check_menu_references(file_path)
            self._validate_action_references(file_path)

        print(f"📊 Scan complete:")
        print(f"   - Field errors found: {len(self.field_errors)}")
        print(f"   - Auto-fixes applied: {len(self.auto_fixes)}")
        print(f"   - Manual review needed: {len(self.manual_review)}")

        return self.field_errors

    def _validate_view_file(self, file_path):
        """Validate field references in a single XML view file"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Find all view records
            for record in root.findall('.//record[@model="ir.ui.view"]'):
                model_field = record.find('.//field[@name="model"]')
                if model_field is not None:
                    model_name = model_field.text
                    self._check_fields_in_arch(record, model_name, file_path)

        except ET.ParseError as e:
            self.manual_review.append({
                'file': os.path.basename(file_path),
                'error': f'XML Parse Error: {e}',
                'type': 'syntax_error'
            })
        except Exception as e:
            self.manual_review.append({
                'file': os.path.basename(file_path),
                'error': f'Validation Error: {e}',
                'type': 'validation_error'
            })

    def _check_fields_in_arch(self, record, model_name, file_path):
        """Check field references in the view architecture"""
        arch_field = record.find('.//field[@name="arch"]')
        if arch_field is None:
            return

        # Get all content from arch field including child elements
        arch_content = ET.tostring(arch_field, encoding='unicode')

        # Use regex to find all field references in the XML string
        field_matches = re.findall(r'<field[^>]*name=[\'"]([^\'"]+)[\'"]', arch_content)

        for field_name in field_matches:
            # Skip computed/special field references and system fields
            if field_name in ['display_name', '__last_update', 'create_date', 'write_date', 'create_uid', 'write_uid']:
                continue
            self._validate_field_reference(field_name, model_name, file_path)

        # Also check for button actions and other references
        button_matches = re.findall(r'<button[^>]*name=[\'"]([^\'"]+)[\'"]', arch_content)
        for button_name in button_matches:
            # Validate button action methods exist
            if button_name.startswith('action_'):
                self._validate_model_method(button_name, model_name, file_path)

    def _validate_model_method(self, method_name, model_name, file_path):
        """Validate that a model method exists"""
        if model_name not in self.model_definitions:
            return

        model_info = self.model_definitions[model_name]
        if method_name not in model_info.get('methods', []):
            self.field_errors.append({
                'file': file_path,
                'model': model_name,
                'field': method_name,
                'error': f'Method {method_name} not found in model {model_name}',
                'suggestion': 'Add method to model or check button name'
            })

    def _validate_field_reference(self, field_name, model_name, file_path):
        """Validate a single field reference"""
        if model_name not in self.model_fields:
            self.manual_review.append({
                'file': os.path.basename(file_path),
                'model': model_name,
                'error': f'Model {model_name} not found in scanned models',
                'type': 'missing_model'
            })
            return

        model_fields = self.model_fields[model_name]

        if field_name not in model_fields:
            # Check for common field mappings
            if field_name in self.field_mappings:
                correct_field = self.field_mappings[field_name]
                if correct_field in model_fields:
                    self.field_errors.append({
                        'file': os.path.basename(file_path),
                        'model': model_name,
                        'field': field_name,
                        'suggested_fix': correct_field,
                        'type': 'auto_fixable'
                    })
                    return

            # Check for related field patterns (e.g., partner_id.name should use partner_id)
            if '.' in field_name:
                base_field = field_name.split('.')[0]
                if base_field in model_fields:
                    # This is a related field access, check if base field is Many2one
                    if model_fields[base_field] in ['Many2one']:
                        return  # Valid related field access
                    else:
                        self.field_errors.append({
                            'file': os.path.basename(file_path),
                            'model': model_name,
                            'field': field_name,
                            'error': f'Invalid related field access on {model_fields[base_field]} field',
                            'type': 'relation_error'
                        })
                        return

            # Look for similar field names
            similar_fields = []
            for available_field in model_fields:
                if (field_name.lower() in available_field.lower() or
                    available_field.lower() in field_name.lower() or
                    self._field_similarity(field_name, available_field) > 0.7):
                    similar_fields.append(available_field)            # No auto-fix available
            self.field_errors.append({
                'file': os.path.basename(file_path),
                'model': model_name,
                'field': field_name,
                'available_fields': list(model_fields.keys()),
                'similar_fields': similar_fields[:5],  # Top 5 similar
                'type': 'missing_field'
            })

    def _field_similarity(self, field1, field2):
        """Calculate similarity between two field names"""
        # Simple Jaccard similarity
        set1 = set(field1.lower())
        set2 = set(field2.lower())
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0

    def _check_menu_references(self, file_path):
        """Check for invalid menu parent references"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for menuitem parent references
            menu_matches = re.findall(r'<menuitem[^>]*parent=[\'"]([^\'"]+)[\'"]', content)

            for parent_ref in menu_matches:
                if parent_ref in self.menu_mappings:
                    self.field_errors.append({
                        'file': os.path.basename(file_path),
                        'error_type': 'menu_reference',
                        'old_ref': parent_ref,
                        'suggested_fix': self.menu_mappings[parent_ref],
                        'type': 'auto_fixable_menu'
                    })

        except Exception as e:
            pass  # Skip file if can't read

    def _validate_action_references(self, file_path):
        """Check for missing action references in menus"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for menuitem action references
            action_matches = re.findall(r'<menuitem[^>]*action=[\'"]([^\'"]+)[\'"]', content)

            for action_ref in action_matches:
                # Check if action is defined in any XML file
                if not self._validate_action_exists(action_ref):
                    self.manual_review.append({
                        'file': os.path.basename(file_path),
                        'error': f'Menu references undefined action: {action_ref}',
                        'type': 'missing_action'
                    })

        except Exception as e:
            pass  # Skip file if can't read

    def _validate_action_exists(self, action_id):
        """Check if an action is defined in any view file"""
        # This is a simplified check - in reality you'd scan all XML files
        # For now, assume actions starting with 'action_' are likely valid
        return action_id.startswith('action_')

    def apply_auto_fixes(self):
        """Apply automatic fixes for common field mapping issues"""
        print("🔧 Applying automatic fixes...")

        auto_fixable = [err for err in self.field_errors if err.get('type') == 'auto_fixable']
        menu_fixable = [err for err in self.field_errors if err.get('type') == 'auto_fixable_menu']

        # Fix field references
        for error in auto_fixable:
            file_path = os.path.join(self.views_path, error['file'])
            self._apply_field_replacement(file_path, error['field'], error['suggested_fix'])

            self.auto_fixes.append({
                'file': error['file'],
                'change': f"Field: {error['field']} → {error['suggested_fix']}"
            })

        # Fix menu references
        for error in menu_fixable:
            file_path = os.path.join(self.views_path, error['file'])
            self._apply_menu_replacement(file_path, error['old_ref'], error['suggested_fix'])

            self.auto_fixes.append({
                'file': error['file'],
                'change': f"Menu: {error['old_ref']} → {error['suggested_fix']}"
            })

        print(f"✅ Applied {len(self.auto_fixes)} automatic fixes")

    def _apply_menu_replacement(self, file_path, old_ref, new_ref):
        """Replace menu parent reference in XML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Replace parent="old_ref" with parent="new_ref"
            pattern = rf'(parent=[\'"]){old_ref}([\'"])'
            replacement = rf'\1{new_ref}\2'
            content = re.sub(pattern, replacement, content)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            print(f"⚠️  Error applying menu fix to {file_path}: {e}")

    def _apply_field_replacement(self, file_path, old_field, new_field):
        """Replace field name in XML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Replace field name="old_field" with field name="new_field"
            pattern = rf'(<field[^>]*name=[\'"]){old_field}([\'"][^>]*>)'
            replacement = rf'\1{new_field}\2'
            content = re.sub(pattern, replacement, content)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            print(f"⚠️  Error applying fix to {file_path}: {e}")

    def generate_report(self):
        """Generate comprehensive error report"""
        report = []
        report.append("=" * 80)
        report.append("MASS VIEW FIELD VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Models scanned: {len(self.model_fields)}")
        report.append(f"Field errors found: {len(self.field_errors)}")
        report.append(f"Auto-fixes applied: {len(self.auto_fixes)}")
        report.append(f"Manual review needed: {len(self.manual_review)}")
        report.append("")

        # Auto-fixes applied
        if self.auto_fixes:
            report.append("AUTO-FIXES APPLIED:")
            report.append("-" * 40)
            for fix in self.auto_fixes:
                report.append(f"  {fix['file']}: {fix['change']}")
            report.append("")

        # Remaining field errors
        remaining_errors = [err for err in self.field_errors if err.get('type') != 'auto_fixable']
        if remaining_errors:
            report.append("REMAINING FIELD ERRORS:")
            report.append("-" * 40)
            for error in remaining_errors[:20]:  # Show first 20
                report.append(f"  {error['file']} - Model: {error.get('model', 'Unknown')}")
                if error.get('field'):
                    report.append(f"    Missing field: {error['field']}")
                if error.get('similar_fields'):
                    report.append(f"    Similar fields: {', '.join(error['similar_fields'])}")
                if error.get('error'):
                    report.append(f"    Error: {error['error']}")
                report.append("")

            more_errors = len(remaining_errors) - 20
            if more_errors > 0:
                report.append(f"  ... and {more_errors} more errors")
            report.append("")

        # Manual review items
        if self.manual_review:
            report.append("MANUAL REVIEW REQUIRED:")
            report.append("-" * 40)
            for item in self.manual_review[:10]:
                report.append(f"  {item['file']}: {item['error']}")
            more_items = len(self.manual_review) - 10
            if more_items > 0:
                report.append(f"  ... and {more_items} more items")

        return "\n".join(report)

def main():
    records_management_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management"

    validator = MassViewFieldValidator(records_management_path)

    # Step 1: Scan all models
    validator.scan_all_models()

    # Step 2: Scan all views
    validator.scan_all_views()

    # Step 3: Apply auto-fixes
    validator.apply_auto_fixes()

    # Step 4: Generate report
    report = validator.generate_report()
    print("\n" + report)

    # Save report to file
    report_file = "mass_view_validation_report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"\n📄 Full report saved to: {report_file}")

if __name__ == "__main__":
    main()
