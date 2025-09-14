#!/usr/bin/env python3
"""
Single File Field Validator - VALIDATION ONLY (No Auto-fixes)
Validates field references in a specific XML view file against model definitions
"""

import os
import re
import xml.etree.ElementTree as ET
import sys

class SingleFileValidator:
    def __init__(self, records_management_path):
        self.base_path = records_management_path
        self.models_path = os.path.join(records_management_path, 'models')

        # Model field mappings
        self.model_fields = {}  # {model_name: {field_name: field_type}}
        self.field_errors = []  # List of field validation errors

        # Common inherited fields from base Odoo models
        self.inherited_fields = {
            'mail.thread': ['message_follower_ids', 'message_ids', 'message_main_attachment_id', 'message_has_error', 'message_has_error_counter', 'message_has_sms_error', 'message_bounce', 'website_message_ids'],
            'mail.activity.mixin': ['activity_ids', 'activity_state', 'activity_user_id', 'activity_type_id', 'activity_type_icon', 'activity_date_deadline', 'activity_summary', 'activity_exception_decoration', 'activity_exception_icon'],
            'base': ['id', 'create_date', 'create_uid', 'write_date', 'write_uid', '__last_update', 'display_name'],
        }

        # System fields that exist in all models
        self.system_fields = {'id', 'create_date', 'create_uid', 'write_date', 'write_uid', '__last_update', 'display_name'}

        # Load all model definitions
        self._scan_model_definitions()

    def _scan_model_definitions(self):
        """Scan all Python model files to extract field definitions"""
        print("🔍 Scanning Python models for field definitions...")

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
                            inherit_matches = re.findall(r"_inherit\s*=\s*\[?['\"]([^'\"]+)['\"]", content)
                            for inherit_model in inherit_matches:
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

            self.field_errors.append({
                'file': os.path.basename(file_path),
                'model': model_name,
                'field': field_name,
                'error': f'Field {field_name} not found in model {model_name}',
                'similar_fields': similar_fields[:5],  # Show top 5 similar fields
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
            # Skip computed/special field references and system fields
            if field_name in self.system_fields:
                continue
            # Skip view structure fields
            if field_name == 'arch':
                continue
            self._validate_field_reference(field_name, model_name, file_path)

    def validate_file(self, file_path):
        """Validate a single XML view file"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        print(f"🔍 Validating: {os.path.basename(file_path)}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse XML
            root = ET.fromstring(content)

            # Find all view records
            view_records = root.findall('.//record[@model="ir.ui.view"]')

            if not view_records:
                print(f"  ⚠️  No view records found")
                return True

            print(f"  📊 Found {len(view_records)} view records")

            for record in view_records:
                # Get the model this view is for
                model_field = record.find('.//field[@name="model"]')
                if model_field is not None:
                    model_name = model_field.text
                    if model_name:
                        self._check_fields_in_arch(record, model_name, file_path)

            return True

        except ET.ParseError as e:
            self.field_errors.append({
                'file': os.path.basename(file_path),
                'model': 'XML_PARSE_ERROR',
                'field': 'N/A',
                'error': f'XML Parse Error: {e}',
                'type': 'xml_error'
            })
            return False
        except Exception as e:
            self.field_errors.append({
                'file': os.path.basename(file_path),
                'model': 'VALIDATION_ERROR',
                'field': 'N/A',
                'error': f'Validation Error: {e}',
                'type': 'validation_error'
            })
            return False

    def print_results(self, file_path):
        """Print validation results for the file"""
        file_name = os.path.basename(file_path)
        file_errors = [e for e in self.field_errors if e['file'] == file_name]

        print(f"\n📋 VALIDATION RESULTS FOR: {file_name}")
        print("=" * 60)

        if not file_errors:
            print("✅ No field validation errors found!")
            return

        print(f"❌ Found {len(file_errors)} field validation errors:")
        print()

        # Group by error type
        by_type = {}
        for error in file_errors:
            error_type = error['type']
            if error_type not in by_type:
                by_type[error_type] = []
            by_type[error_type].append(error)

        for error_type, errors in by_type.items():
            print(f"🔸 {error_type.upper().replace('_', ' ')} ({len(errors)} errors):")
            for error in errors[:10]:  # Show first 10 errors of each type
                print(f"   Model: {error['model']}")
                print(f"   Field: {error['field']}")
                print(f"   Error: {error['error']}")
                if 'similar_fields' in error and error['similar_fields']:
                    print(f"   Similar fields: {', '.join(error['similar_fields'])}")
                print()

            if len(errors) > 10:
                print(f"   ... and {len(errors) - 10} more {error_type} errors")
                print()

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 single_file_validator.py <view_file_path>")
        print("Example: python3 single_file_validator.py records_management/views/chain_of_custody_views.xml")
        sys.exit(1)

    file_path = sys.argv[1]

    # Ensure we're in the right directory
    if not os.path.exists('records_management'):
        print("❌ Error: Run this script from the workspace root directory")
        sys.exit(1)

    validator = SingleFileValidator('records_management')

    if validator.validate_file(file_path):
        validator.print_results(file_path)
    else:
        print(f"❌ Failed to validate {file_path}")

if __name__ == "__main__":
    main()
