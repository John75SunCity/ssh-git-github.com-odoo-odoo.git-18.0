#!/usr/bin/env python3
"""
Comprehensive Records Management Validator - VALIDATION ONLY
============================================================

SAFE version without auto-fix functionality to prevent accidental mass changes.
This validator only reports issues and does NOT modify any files.

Usage:
  python3 comprehensive_validator_validation_only.py                    # Validate all files
  python3 comprehensive_validator_validation_only.py path/to/file.xml   # Validate single file
  python3 comprehensive_validator_validation_only.py file1.xml file2.xml # Validate specific files
  python3 comprehensive_validator_validation_only.py --help             # Show help

Key Changes from Original:
- Removed all auto-fix functionality
- Removed --auto-fix flag
- Added support for checking multiple specific files
- Safe to run on any files without risk of modification
"""

import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
import argparse
from pathlib import Path

class SafeValidator:
    """Validation-only validator - NO FILE MODIFICATIONS"""

    def __init__(self, records_management_path):
        self.base_path = records_management_path
        self.models_path = os.path.join(records_management_path, 'models')
        self.views_path = os.path.join(records_management_path, 'views')

        # Error collections
        self.field_errors = []
        self.accessibility_errors = []
        self.method_errors = []
        self.xmlid_errors = []
        self.xml_syntax_errors = []
        self.manual_review = []

        # Model field mappings
        self.model_fields = {}
        self.model_methods = {}

        # XML ID mappings
        self.xml_ids = set()
        self.external_xml_ids = set()

        # System fields that exist in all models
        self.system_fields = {'id', 'create_date', 'create_uid', 'write_date', 'write_uid', '__last_update', 'display_name'}

        # Common inherited fields from base Odoo models
        self.inherited_fields = {
            'mail.thread': ['message_follower_ids', 'message_ids', 'message_main_attachment_id', 'message_has_error', 'message_has_error_counter', 'message_has_sms_error', 'message_bounce', 'website_message_ids'],
            'mail.activity.mixin': ['activity_ids', 'activity_state', 'activity_user_id', 'activity_type_id', 'activity_type_icon', 'activity_date_deadline', 'activity_summary', 'activity_exception_decoration', 'activity_exception_icon'],
            'base': ['id', 'create_date', 'create_uid', 'write_date', 'write_uid', '__last_update', 'display_name'],
        }

        # Core Odoo models that are commonly used in data files
        self.core_odoo_models = {
            'ir.actions.act_window': {
                'name', 'res_model', 'view_mode', 'view_id', 'view_ids', 'domain', 'context',
                'limit', 'target', 'type', 'binding_model_id', 'binding_type', 'usage',
                'groups_id', 'help', 'auto_search', 'filter', 'multi', 'search_view_id'
            },
            'ir.ui.menu': {
                'name', 'parent_id', 'action', 'sequence', 'groups_id', 'web_icon',
                'active', 'web_icon_data'
            },
            'ir.model.access': {
                'name', 'model_id', 'group_id', 'perm_read', 'perm_write', 'perm_create', 'perm_unlink'
            },
            'ir.rule': {
                'name', 'model_id', 'groups', 'domain_force', 'perm_read', 'perm_write',
                'perm_create', 'perm_unlink', 'active'
            },
            'ir.sequence': {
                'name', 'code', 'prefix', 'suffix', 'padding', 'number_next', 'number_increment',
                'implementation', 'active', 'company_id'
            },
            'mail.template': {
                'name', 'model_id', 'subject', 'body_html', 'email_from', 'email_to',
                'email_cc', 'auto_delete', 'use_default_to', 'attachment_ids'
            },
            'res.config.settings': {
                'id', 'create_date', 'create_uid', 'write_date', 'write_uid',
                'display_name', '__last_update', 'company_id', 'user_id', 'module_ids',
                'config_parameter_ids', 'active', 'sequence', 'name', 'state',
                # Add common Records Management settings fields
                'records_auto_barcode_generation', 'records_enable_advanced_search',
                'naid_compliance_enabled', 'billing_auto_invoice_generation'
            },
            'res.partner': {
                'id', 'name', 'display_name', 'email', 'phone', 'mobile',
                'street', 'street2', 'city', 'zip', 'state_id', 'country_id',
                'is_company', 'active', 'partner_type', 'company_id', 'parent_id',
                'user_id', 'company_type', 'website', 'vat', 'ref', 'lang',
                'category_id', 'title', 'function', 'comment', 'image_1920',
                # Records Management specific fields
                'is_records_customer', 'department_ids', 'department_count',
                'container_count', 'document_count'
            }
        }

        # Field patterns that commonly need correction
        self.common_corrections = {
            'status': 'state',
            'groups': 'groups_id',
            'document_id': 'document_ids',
            'container_id': 'container_ids',
        }

        # Load all model definitions and XML IDs
        self._scan_model_definitions()
        self._scan_xml_ids()

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
                            inherit_matches = re.findall(r"_inherit\s*=\s*['\"]([^'\"]+)['\"]", content)
                            inherit_list_matches = re.findall(r"_inherit\s*=\s*\[(.*?)\]", content, re.DOTALL)

                            # Process single inheritance
                            for inherit_model in inherit_matches:
                                if inherit_model in self.inherited_fields:
                                    self.model_fields[model_name].update(self.inherited_fields[inherit_model])

                            # Process list inheritance
                            for inherit_list in inherit_list_matches:
                                individual_inherits = re.findall(r"['\"]([^'\"]+)['\"]", inherit_list)
                                for inherit_model in individual_inherits:
                                    if inherit_model in self.inherited_fields:
                                        self.model_fields[model_name].update(self.inherited_fields[inherit_model])

                            # Extract field definitions
                            field_matches = re.findall(r"(\w+)\s*=\s*fields\.\w+", content)
                            for field_name in field_matches:
                                self.model_fields[model_name].add(field_name)

                            # Extract method definitions
                            if model_name not in self.model_methods:
                                self.model_methods[model_name] = set()

                            method_matches = re.findall(r"def\s+(\w+)\s*\(", content)
                            for method_name in method_matches:
                                self.model_methods[model_name].add(method_name)

                    except Exception as e:
                        print(f"Error scanning {file_path}: {e}")

        print(f"✅ Found {model_count} models with field definitions")

    def _scan_xml_ids(self):
        """Scan all XML files to build a database of available XML IDs"""
        # Core XML IDs that are always available from base Odoo
        self.external_xml_ids.update([
            'base.main_company', 'base.group_user', 'base.group_system', 'base.group_portal',
            'portal.portal_menu', 'mail.menu_mail_message', 'stock.menu_stock_root',
            'account.menu_finance', 'sale.menu_sale_root', 'project.menu_main_pm'
        ])

        # Scan all XML files in the module
        xml_files = []
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith('.xml'):
                    xml_files.append(os.path.join(root, file))

        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                for elem in root.iter():
                    if 'id' in elem.attrib:
                        xml_id = elem.attrib['id']
                        self.xml_ids.add(xml_id)
                        self.xml_ids.add(f"records_management.{xml_id}")

            except ET.ParseError:
                continue

    def _check_xml_syntax(self, file_path):
        """Check XML syntax and report detailed errors"""
        errors = []

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Check for Odoo 18.0 compatibility issues
            if root.tag == 'odoo':
                # Check for deprecated <tree> tags
                tree_elements = root.findall('.//tree')
                for elem in tree_elements:
                    # Get line number (approximate)
                    errors.append({
                        'type': 'odoo18_compatibility',
                        'file': os.path.basename(file_path),
                        'line': 0,  # Would need more complex parsing for exact line
                        'column': 0,
                        'error': 'Deprecated <tree> tag found. Use <list> in Odoo 18.0+',
                        'context': ET.tostring(elem, encoding='unicode')[:100] + '...',
                        'fix_suggestion': 'Replace <tree> with <list> and </tree> with </list>'
                    })

                # Check for data wrapper issues
                data_elements = [child for child in root if child.tag == 'data']
                if data_elements:
                    errors.append({
                        'type': 'odoo_schema_warning',
                        'file': os.path.basename(file_path),
                        'line': 3,
                        'column': 0,
                        'error': 'Unnecessary <data> wrapper detected. In Odoo 18.0, <data> inside <odoo> can cause schema validation errors.',
                        'context': '<data>',
                        'fix_suggestion': 'Remove <data> wrapper and place records directly under <odoo>.'
                    })

            return errors

        except ET.ParseError as e:
            error_line = getattr(e, 'lineno', 0)
            error_col = getattr(e, 'offset', 0)

            context_line = ""
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if error_line > 0 and error_line <= len(lines):
                        context_line = lines[error_line - 1].strip()
            except:
                pass

            return [{
                'type': 'xml_syntax_error',
                'file': os.path.basename(file_path),
                'line': error_line,
                'column': error_col,
                'error': str(e),
                'context': context_line,
                'fix_suggestion': self._suggest_xml_fix(str(e))
            }]
        except Exception as e:
            return [{
                'type': 'xml_file_error',
                'file': os.path.basename(file_path),
                'line': 0,
                'column': 0,
                'error': f"Could not read XML file: {e}",
                'context': "",
                'fix_suggestion': "Check file encoding and permissions"
            }]

    def _suggest_xml_fix(self, error_message):
        """Suggest fixes for common XML syntax errors"""
        error_lower = error_message.lower()

        if "opening and ending tag mismatch" in error_lower:
            return "Check for missing closing tags or extra closing tags. Ensure all XML tags are properly paired."
        elif "expected" in error_lower and ">" in error_lower:
            return "Check for missing '>' character or malformed tag attributes."
        elif "not well-formed" in error_lower:
            return "Check for unescaped special characters (&, <, >) or malformed XML structure."
        elif "junk after document element" in error_lower:
            return "Remove duplicate content after closing </odoo> tag."
        else:
            return "Review XML structure and ensure proper formatting."

    def _validate_model_existence(self, model_name, file_path):
        """Validate that a model referenced in views actually exists"""
        # Skip core Odoo models - they exist in the system
        if model_name in self.core_odoo_models:
            return

        # Check if the model exists in our scanned models
        if model_name not in self.model_fields:
            self.field_errors.append({
                'file': os.path.basename(file_path),
                'model': model_name,
                'field': 'N/A',
                'error': f'🚨 DEPLOYMENT BLOCKER: Model "{model_name}" does not exist! Referenced in view but model not found in scanned Python files.',
                'type': 'missing_model_definition'
            })

    def _validate_field_reference(self, field_name, model_name, file_path):
        """Validate a single field reference"""
        # First check if it's a system field
        if field_name in self.system_fields:
            return

        # Check if it's a core Odoo model
        if model_name in self.core_odoo_models:
            model_fields = self.core_odoo_models[model_name]
            if field_name not in model_fields:
                suggestion = self.common_corrections.get(field_name, '')
                suggestion_text = f" → Try: {suggestion}" if suggestion else ""

                self.field_errors.append({
                    'file': os.path.basename(file_path),
                    'model': model_name,
                    'field': field_name,
                    'error': f'Field "{field_name}" is not valid for core Odoo model "{model_name}"{suggestion_text} - DEPLOYMENT BLOCKER!',
                    'type': 'invalid_core_field'
                })
            return

        # Check custom models
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
            similar_fields = [f for f in model_fields if field_name.lower() in f.lower() or f.lower() in field_name.lower()]

            self.field_errors.append({
                'file': os.path.basename(file_path),
                'model': model_name,
                'field': field_name,
                'error': f'Field {field_name} not found in model {model_name}',
                'similar_fields': similar_fields[:5],
                'type': 'missing_field'
            })

    def _check_fields_in_arch(self, record, model_name, file_path):
        """Check field references in view architectures"""
        arch_field = record.find('.//field[@name="arch"]')
        if arch_field is None:
            return

        arch_content = ET.tostring(arch_field, encoding='unicode')
        field_matches = re.findall(r'<field[^>]*name=[\'"]([^\'"]+)[\'"]', arch_content)

        for field_name in field_matches:
            if field_name not in self.system_fields and field_name != 'arch':
                self._validate_field_reference(field_name, model_name, file_path)

    def _check_data_record_fields(self, record, model_name, file_path):
        """Check field references in data records"""
        field_elements = record.findall('.//field[@name]')

        for field_element in field_elements:
            field_name = field_element.get('name')
            if field_name and field_name not in self.system_fields:
                self._validate_field_reference(field_name, model_name, file_path)

    def validate_single_file(self, file_path):
        """Validate a single XML file - VALIDATION ONLY, NO MODIFICATIONS"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        print(f"🔍 Validating: {os.path.basename(file_path)}")

        # Check XML syntax
        xml_syntax_errors = self._check_xml_syntax(file_path)
        if xml_syntax_errors:
            self.xml_syntax_errors.extend(xml_syntax_errors)
            print(f"❌ XML syntax errors found")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            root = ET.fromstring(content)

            # Find all records
            view_records = root.findall('.//record[@model="ir.ui.view"]')
            all_records = root.findall('.//record[@model]')
            data_records = [r for r in all_records if r.get('model') != 'ir.ui.view']

            if not view_records and not data_records:
                print(f"  ⚠️  No records found")
                return True

            print(f"  📊 Found {len(view_records)} view records, {len(data_records)} data records")

            # Validate view records
            for record in view_records:
                model_field = record.find('.//field[@name="model"]')
                if model_field is not None:
                    model_name = model_field.text
                    if model_name:
                        # First check if the model exists
                        self._validate_model_existence(model_name, file_path)
                        # Then check fields in the view
                        self._check_fields_in_arch(record, model_name, file_path)

            # Validate data records
            for record in data_records:
                model_name = record.get('model')
                if model_name:
                    # Check for action records with res_model field that references other models
                    if model_name == 'ir.actions.act_window':
                        res_model_field = record.find('.//field[@name="res_model"]')
                        if res_model_field is not None and res_model_field.text:
                            self._validate_model_existence(res_model_field.text, file_path)

                    self._check_data_record_fields(record, model_name, file_path)

            return True

        except Exception as e:
            self.field_errors.append({
                'file': os.path.basename(file_path),
                'model': 'VALIDATION_ERROR',
                'field': 'N/A',
                'error': f'Validation Error: {e}',
                'type': 'validation_error'
            })
            return False

    def validate_files(self, file_paths):
        """Validate specific list of files - VALIDATION ONLY"""
        print(f"🔍 Validating {len(file_paths)} specific files...")

        for file_path in file_paths:
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue
            self.validate_single_file(file_path)

    def validate_all_files(self):
        """Validate all XML files in the views directory - VALIDATION ONLY"""
        print("🔍 Scanning all XML view files...")

        view_files = []
        for root, dirs, files in os.walk(self.views_path):
            for file in files:
                if file.endswith('.xml'):
                    view_files.append(os.path.join(root, file))

        print(f"📊 Found {len(view_files)} XML files to validate")
        print("🔒 VALIDATION-ONLY MODE: No files will be modified")

        for file_path in view_files:
            file_name = os.path.basename(file_path)

            # Check XML syntax
            xml_syntax_errors = self._check_xml_syntax(file_path)
            if xml_syntax_errors:
                self.xml_syntax_errors.extend(xml_syntax_errors)
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                root = ET.fromstring(content)

                # Validate view records
                view_records = root.findall('.//record[@model="ir.ui.view"]')
                for record in view_records:
                    model_field = record.find('.//field[@name="model"]')
                    if model_field is not None:
                        model_name = model_field.text
                        if model_name:
                            self._check_fields_in_arch(record, model_name, file_path)

                # Validate data records
                all_records = root.findall('.//record[@model]')
                data_records = [r for r in all_records if r.get('model') != 'ir.ui.view']
                for record in data_records:
                    model_name = record.get('model')
                    if model_name:
                        self._check_data_record_fields(record, model_name, file_path)

            except ET.ParseError as e:
                # Should have been caught by syntax check, but just in case
                pass
            except Exception as e:
                self.field_errors.append({
                    'file': os.path.basename(file_path),
                    'model': 'VALIDATION_ERROR',
                    'field': 'N/A',
                    'error': f'Validation Error: {e}',
                    'type': 'validation_error'
                })

    def print_results(self, file_paths=None):
        """Print validation results"""
        total_field_errors = len(self.field_errors)
        total_xml_syntax_errors = len(self.xml_syntax_errors)
        total_errors = total_field_errors + total_xml_syntax_errors

        if file_paths:
            print(f"\n📋 VALIDATION RESULTS FOR {len(file_paths)} FILES:")
        else:
            print(f"\n📊 COMPREHENSIVE VALIDATION RESULTS:")

        print("=" * 60)
        print("🔒 VALIDATION-ONLY MODE: No files were modified")
        print("=" * 60)

        print(f"   - XML syntax errors: {total_xml_syntax_errors}")
        print(f"   - Field validation errors: {total_field_errors}")
        print(f"   - Total errors: {total_errors}")

        if total_errors == 0:
            print("✅ No validation errors found!")
            return

        # Show syntax errors first (highest priority)
        if self.xml_syntax_errors:
            print(f"\n🚨 XML SYNTAX ERRORS ({len(self.xml_syntax_errors)}) - DEPLOYMENT BLOCKERS:")
            for error in self.xml_syntax_errors[:10]:  # Show first 10
                print(f"   {error['file']}:{error['line']} - {error['error']}")
                if error['fix_suggestion']:
                    print(f"   💡 Fix: {error['fix_suggestion']}")

        # Show core field errors (high priority)
        core_field_errors = [e for e in self.field_errors if e['type'] == 'invalid_core_field']
        if core_field_errors:
            print(f"\n🔸 CORE FIELD ERRORS ({len(core_field_errors)}) - HIGH PRIORITY:")
            for error in core_field_errors[:10]:
                print(f"   {error['file']} - {error['model']}.{error['field']}: {error['error']}")

        # Show other field errors
        other_field_errors = [e for e in self.field_errors if e['type'] != 'invalid_core_field']
        if other_field_errors:
            print(f"\n⚠️  OTHER FIELD ERRORS ({len(other_field_errors)}):")
            for error in other_field_errors[:10]:
                print(f"   {error['file']} - {error['model']}.{error['field']}: {error['error']}")

        if total_errors > 20:
            print(f"\n... and {total_errors - 20} more errors (showing first 20)")

        print(f"\n💡 To fix issues manually, edit the files listed above.")
        print(f"🔧 For automatic fixes, use the original comprehensive_validator_with_autofix.py with --auto-fix flag.")

def main():
    parser = argparse.ArgumentParser(description='Safe Records Management Validator - VALIDATION ONLY')
    parser.add_argument('files', nargs='*', help='Specific XML files to validate (optional)')
    parser.add_argument('--all', action='store_true', help='Validate all files (default if no files specified)')
    parser.add_argument('--module-path', default='records_management', help='Path to Records Management module')

    args = parser.parse_args()

    if not os.path.exists(args.module_path):
        print(f"❌ Error: Module path not found: {args.module_path}")
        print("   Run this script from the workspace root directory")
        return 1

    print("🔍 SAFE VALIDATION-ONLY MODE")
    print("🔒 NO FILES WILL BE MODIFIED")
    print("=" * 60)

    validator = SafeValidator(args.module_path)

    if args.files:
        # Validate specific files
        # Convert relative paths to absolute paths
        file_paths = []
        for file_path in args.files:
            if os.path.exists(file_path):
                file_paths.append(file_path)
            else:
                # Try in views directory
                views_file = os.path.join(args.module_path, 'views', file_path)
                if os.path.exists(views_file):
                    file_paths.append(views_file)
                else:
                    print(f"❌ File not found: {file_path}")

        if file_paths:
            validator.validate_files(file_paths)
            validator.print_results(file_paths)
        else:
            print("❌ No valid files found to validate")
            return 1
    else:
        # Validate all files
        validator.validate_all_files()
        validator.print_results()

    return 0

if __name__ == "__main__":
    sys.exit(main())
