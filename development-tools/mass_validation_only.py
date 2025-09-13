#!/usr/bin/env python3
"""
Mass View Field Validator - VALIDATION ONLY MODE
Scans all 300 XML view files and validates field references against model definitions
NO AUTO-FIXES - Pure validation and reporting for manual review
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

class MassViewFieldValidator:
    def __init__(self, records_management_path):
        self.base_path = records_management_path
        self.models_path = os.path.join(records_management_path, 'models')
        self.views_path = os.path.join(records_management_path, 'views')

        # Model field mappings
        self.model_fields = {}  # {model_name: {field_name: field_type}}
        self.field_errors = []  # List of field validation errors
        self.manual_review = [] # Complex issues requiring manual review

        # Common inherited fields from base Odoo models
        self.inherited_fields = {
            'mail.thread': ['message_follower_ids', 'message_ids', 'message_main_attachment_id', 'message_has_error', 'message_has_error_counter', 'message_has_sms_error', 'message_bounce', 'website_message_ids'],
            'mail.activity.mixin': ['activity_ids', 'activity_state', 'activity_user_id', 'activity_type_id', 'activity_type_icon', 'activity_date_deadline', 'activity_summary', 'activity_exception_decoration', 'activity_exception_icon'],
            'base': ['id', 'create_date', 'create_uid', 'write_date', 'write_uid', '__last_update', 'display_name'],
        }

        # System fields that exist in all models
        self.system_fields = {'id', 'create_date', 'create_uid', 'write_date', 'write_uid', '__last_update', 'display_name'}

        # Field patterns that commonly need correction (for suggestion purposes only)
        self.common_corrections = {
            'status': 'state',
            'document_id': 'document_ids',  # Many2one vs Many2many pattern
            'container_id': 'container_ids',  # Many2one vs Many2many pattern
        }

        # Load all model definitions
        self._scan_model_definitions()

    def _scan_model_definitions(self):
        """Scan all Python model files to extract field definitions"""
        print("🔍 Scanning all Python models for field definitions...")

        model_count = 0
        for root, dirs, files in os.walk(self.models_path):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Extract model name
                        model_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)

                        for model_name in model_matches:
                            if model_name not in self.model_fields:
                                self.model_fields[model_name] = set()
                                model_count += 1

                            # Add system fields to all models
                            self.model_fields[model_name].update(self.system_fields)

                            # Check for inherited models and add their fields
                            # Handle both single inheritance and list inheritance
                            inherit_matches = re.findall(r"_inherit\s*=\s*['\"]([^'\"]+)['\"]", content)  # Single inherit
                            inherit_list_matches = re.findall(r"_inherit\s*=\s*\[(.*?)\]", content, re.DOTALL)  # List inherit

                            # Process single inheritance
                            for inherit_model in inherit_matches:
                                if inherit_model in self.inherited_fields:
                                    self.model_fields[model_name].update(self.inherited_fields[inherit_model])

                            # Process list inheritance
                            for inherit_list in inherit_list_matches:
                                # Extract individual models from the list
                                individual_inherits = re.findall(r"['\"]([^'\"]+)['\"]", inherit_list)
                                for inherit_model in individual_inherits:
                                    if inherit_model in self.inherited_fields:
                                        self.model_fields[model_name].update(self.inherited_fields[inherit_model])

                            # Extract field definitions
                            field_matches = re.findall(r"(\w+)\s*=\s*fields\.\w+", content)
                            for field_name in field_matches:
                                self.model_fields[model_name].add(field_name)

                    except Exception as e:
                        print(f"Error scanning {file_path}: {e}")

        print(f"✅ Found {model_count} models with field definitions")

    def _validate_field_reference(self, field_name, model_name, file_path):
        """Validate a single field reference"""
        if model_name not in self.model_fields:
            self.field_errors.append({
                'file': os.path.basename(file_path),
                'model': model_name,
                'field': field_name,
                'error': f'Model {model_name} not found in scanned models',
                'type': 'missing_model'
            })
            return

        model_fields = self.model_fields[model_name]

        if field_name not in model_fields:
            # Find similar field names
            similar_fields = [f for f in model_fields if field_name.lower() in f.lower() or f.lower() in field_name.lower()]

            # Check for common correction patterns
            suggested_correction = self.common_corrections.get(field_name)

            self.field_errors.append({
                'file': os.path.basename(file_path),
                'model': model_name,
                'field': field_name,
                'error': f'Field {field_name} not found in model {model_name}',
                'similar_fields': similar_fields[:5],  # Show top 5 similar fields
                'suggested_correction': suggested_correction,
                'type': 'missing_field'
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
            # Skip view structure fields and system fields
            if field_name in self.system_fields or field_name == 'arch':
                continue
            self._validate_field_reference(field_name, model_name, file_path)

    def _check_actions_and_menus(self, file_path):
        """Check for missing action and menu references"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find action references that might be missing
            action_refs = re.findall(r'action=[\'"]([^\'"]+)[\'"]', content)
            menu_refs = re.findall(r'parent=[\'"]([^\'"]+)[\'"]', content)

            for action_ref in action_refs:
                if action_ref not in content:
                    self.manual_review.append({
                        'file': os.path.basename(file_path),
                        'issue': f'Action reference {action_ref} might be missing',
                        'type': 'missing_action'
                    })

        except Exception as e:
            pass  # Skip files that can't be processed

    def scan_all_views(self):
        """Scan all XML view files for field validation issues"""
        print("🔍 Scanning all XML view files for field references...")

        view_files = []
        for root, dirs, files in os.walk(self.views_path):
            for file in files:
                if file.endswith('.xml'):
                    view_files.append(os.path.join(root, file))

        print(f"📊 Found {len(view_files)} XML files to validate")

        for file_path in view_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Parse XML
                root = ET.fromstring(content)

                # Find all view records
                view_records = root.findall('.//record[@model="ir.ui.view"]')

                for record in view_records:
                    # Get the model this view is for
                    model_field = record.find('.//field[@name="model"]')
                    if model_field is not None:
                        model_name = model_field.text
                        if model_name:
                            self._check_fields_in_arch(record, model_name, file_path)

                # Check for other issues
                self._check_actions_and_menus(file_path)

            except ET.ParseError as e:
                self.field_errors.append({
                    'file': os.path.basename(file_path),
                    'model': 'XML_PARSE_ERROR',
                    'field': 'N/A',
                    'error': f'XML Parse Error: {e}',
                    'type': 'xml_error'
                })
            except Exception as e:
                self.field_errors.append({
                    'file': os.path.basename(file_path),
                    'model': 'VALIDATION_ERROR',
                    'field': 'N/A',
                    'error': f'Validation Error: {e}',
                    'type': 'validation_error'
                })

    def generate_report(self):
        """Generate comprehensive validation report"""
        total_errors = len(self.field_errors)
        manual_reviews = len(self.manual_review)

        print(f"📊 Scan complete:")
        print(f"   - Field errors found: {total_errors}")
        print(f"   - Manual review needed: {manual_reviews}")
        print(f"   - AUTO-FIXES DISABLED - Validation only mode")

        # Group errors by file for targeted fixes
        errors_by_file = defaultdict(list)
        for error in self.field_errors:
            errors_by_file[error['file']].append(error)

        # Save detailed report
        report_file = "mass_validation_report_no_autofixes.txt"
        with open(report_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("MASS VIEW FIELD VALIDATION REPORT - VALIDATION ONLY\n")
            f.write("=" * 80 + "\n")
            f.write(f"Models scanned: {len(self.model_fields)}\n")
            f.write(f"Field errors found: {total_errors}\n")
            f.write(f"Manual review needed: {manual_reviews}\n")
            f.write(f"AUTO-FIXES: DISABLED (Pure validation mode)\n\n")

            if self.field_errors:
                f.write("FIELD VALIDATION ERRORS BY FILE:\n")
                f.write("-" * 40 + "\n")

                for file_name, file_errors in sorted(errors_by_file.items()):
                    f.write(f"\n📄 {file_name} ({len(file_errors)} errors):\n")

                    # Group by error type
                    by_type = defaultdict(list)
                    for error in file_errors:
                        by_type[error['type']].append(error)

                    for error_type, errors in by_type.items():
                        f.write(f"  🔸 {error_type.upper().replace('_', ' ')} ({len(errors)} errors):\n")
                        for error in errors:
                            f.write(f"    Model: {error['model']}\n")
                            f.write(f"    Field: {error['field']}\n")
                            f.write(f"    Error: {error['error']}\n")

                            if 'suggested_correction' in error and error['suggested_correction']:
                                f.write(f"    💡 Suggested fix: {error['field']} → {error['suggested_correction']}\n")
                            elif 'similar_fields' in error and error['similar_fields']:
                                f.write(f"    Similar fields: {', '.join(error['similar_fields'])}\n")
                            f.write("\n")

            if self.manual_review:
                f.write("\nMANUAL REVIEW ITEMS:\n")
                f.write("-" * 20 + "\n")
                for item in self.manual_review:
                    f.write(f"  {item['file']}: {item['issue']} (Type: {item['type']})\n")

        print(f"\n📄 Full report saved to: {report_file}")

        # Show top 20 errors for immediate action
        if self.field_errors:
            print(f"\n🎯 TOP 20 FIELD ERRORS FOR IMMEDIATE FIXING:")
            print("=" * 60)
            for i, error in enumerate(self.field_errors[:20]):
                print(f"{i+1}. {error['file']} - {error['model']}.{error['field']}")
                if 'suggested_correction' in error and error['suggested_correction']:
                    print(f"   💡 Fix: {error['field']} → {error['suggested_correction']}")
                elif 'similar_fields' in error and error['similar_fields']:
                    print(f"   Similar: {', '.join(error['similar_fields'][:3])}")
                print()

def main():
    if not os.path.exists('records_management'):
        print("❌ Error: Run this script from the workspace root directory")
        return

    print("🔍 MASS VIEW FIELD VALIDATOR - VALIDATION ONLY MODE")
    print("🚫 AUTO-FIXES DISABLED - Manual corrections required")
    print("=" * 60)

    validator = MassViewFieldValidator('records_management')
    validator.scan_all_views()
    validator.generate_report()

if __name__ == "__main__":
    main()
