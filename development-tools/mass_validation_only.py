#!/usr/bin/env python3
"""
Mass View Field Validator - VALIDATION ONLY MODE
Scans all 300 XML view files and validates field references against model definitions
NO AUTO-FIXES - Pure validation and reporting for manual review
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultd        # First collect all XML IDs across the module
        print("📋 Collecting XML IDs across module...")
        # self._collect_xml_ids()  # Temporarily disabled to test base validator

class MassViewFieldValidator:
    def __init__(self, records_management_path):
        self.base_path = records_management_path
        self.models_path = os.path.join(records_management_path, 'models')
        self.views_path = os.path.join(records_management_path, 'views')

        # Model field mappings
        self.model_fields = {}  # {model_name: {field_name: field_type}}
        self.model_methods = {}  # {model_name: set of method names}
        self.field_errors = []  # List of field validation errors
        self.accessibility_errors = []  # FontAwesome accessibility issues
        self.method_errors = []  # Missing method errors
        self.external_id_errors = []  # Missing external ID references
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

        # Collect all defined XML IDs for external reference validation
        self.defined_xml_ids = set()
        self._collect_xml_ids()

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

                            # Extract method definitions (for action validation)
                            if model_name not in self.model_methods:
                                self.model_methods[model_name] = set()

                            # Find def method_name patterns
                            method_matches = re.findall(r"def\s+(\w+)\s*\(", content)
                            for method_name in method_matches:
                                self.model_methods[model_name].add(method_name)

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

    def _check_fontawesome_accessibility(self, content, file_path):
        """Check for FontAwesome icons missing title attributes"""
        # Find all <i> tags with fa classes
        fa_icon_pattern = r'<i[^>]*class="[^"]*fa\s+fa-[^"]*"[^>]*>'
        fa_matches = re.finditer(fa_icon_pattern, content)

        for match in fa_matches:
            icon_tag = match.group(0)
            # Check if it has title attribute or contains text
            has_title = 'title=' in icon_tag
            # Check if the tag has closing content (not self-closing)
            is_self_closing = icon_tag.endswith('/>')

            if not has_title and is_self_closing:
                # Extract the fa class for better error reporting
                fa_class_match = re.search(r'fa\s+fa-[\w-]+', icon_tag)
                fa_class = fa_class_match.group(0) if fa_class_match else 'unknown'

                self.accessibility_errors.append({
                    'file': os.path.basename(file_path),
                    'icon_class': fa_class,
                    'icon_tag': icon_tag,
                    'error': f'FontAwesome icon ({fa_class}) missing title attribute for accessibility',
                    'type': 'accessibility_fa_title'
                })

    def _collect_xml_ids(self):
        """Collect all defined XML IDs from all XML files for external reference validation"""
        print("🔍 Collecting all defined XML IDs for external reference validation...")

        xml_files = []
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith('.xml'):
                    xml_files.append(os.path.join(root, file))

        for file_path in xml_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find all XML ID definitions: <record id="..." or <menuitem id="..." etc.
                id_pattern = r'<[^>]+\sid="([^"]+)"'
                matches = re.finditer(id_pattern, content)

                for match in matches:
                    xml_id = match.group(1)
                    # Add both with and without module prefix
                    self.defined_xml_ids.add(xml_id)
                    self.defined_xml_ids.add(f"records_management.{xml_id}")

            except Exception as e:
                continue

        print(f"📊 Found {len(self.defined_xml_ids)} defined XML IDs")

    def _check_external_id_references(self, content, file_path):
        """Check for external ID references that don't exist"""
        # Find parent references in menuitems
        parent_pattern = r'parent="([^"]+)"'
        parent_matches = re.finditer(parent_pattern, content)

        for match in parent_matches:
            parent_ref = match.group(1)
            if parent_ref not in self.defined_xml_ids:
                self.external_id_errors.append({
                    'file': os.path.basename(file_path),
                    'reference': parent_ref,
                    'type': 'menuitem_parent',
                    'error': f'External ID not found: {parent_ref}',
                    'context': match.group(0)
                })

        # Find action references in menuitems
        action_pattern = r'action="([^"]+)"'
        action_matches = re.finditer(action_pattern, content)

        for match in action_matches:
            action_ref = match.group(1)
            if action_ref not in self.defined_xml_ids:
                self.external_id_errors.append({
                    'file': os.path.basename(file_path),
                    'reference': action_ref,
                    'type': 'menuitem_action',
                    'error': f'External ID not found: {action_ref}',
                    'context': match.group(0)
                })

        # Find ref() references
        ref_pattern = r'ref\([\'"]([^\'"]+)[\'"]\)'
        ref_matches = re.finditer(ref_pattern, content)

        for match in ref_matches:
            ref_id = match.group(1)
            if ref_id not in self.defined_xml_ids:
                self.external_id_errors.append({
                    'file': os.path.basename(file_path),
                    'reference': ref_id,
                    'type': 'ref_function',
                    'error': f'External ID not found: {ref_id}',
                    'context': match.group(0)
                })

    def _check_action_methods(self, content, file_path):
        """Check for button actions that reference non-existent methods"""
        # Find all button name references
        action_pattern = r'<button[^>]*name="([^"]+)"[^>]*type="object"'
        action_matches = re.finditer(action_pattern, content)

        # Get model name from the file content
        model_match = re.search(r'<field name="model">([^<]+)</field>', content)
        if not model_match:
            return

        model_name = model_match.group(1)
        model_methods = self.model_methods.get(model_name, set())

        for match in action_matches:
            action_name = match.group(1)
            button_tag = match.group(0)

            if action_name not in model_methods:
                self.method_errors.append({
                    'file': os.path.basename(file_path),
                    'model': model_name,
                    'action': action_name,
                    'button_tag': button_tag,
                    'error': f'Action method "{action_name}" not found in model {model_name}',
                    'available_actions': [m for m in model_methods if m.startswith('action_')][:5],
                    'type': 'missing_action_method'
                })

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
        """Scan all view files in the module for various errors."""
        print("🔍 Starting comprehensive view scan...")

        # First collect all XML IDs across the module
        print("� Collecting XML IDs across module...")
        self.collect_xml_ids()

        view_files = []
        for root, dirs, files in os.walk("records_management"):
            for file in files:
                if file.endswith('.xml'):
                    view_files.append(os.path.join(root, file))

        print(f"Found {len(view_files)} XML files to scan")
        for file_path in view_files:
            print(f"Scanning: {file_path}")
            self.scan_view_file(file_path)
            # self._check_external_id_references(file_path)  # Temporarily disabled

    def generate_report(self):
        """Generate comprehensive validation report"""
        total_field_errors = len(self.field_errors)
        total_accessibility_errors = len(self.accessibility_errors)
        total_method_errors = len(self.method_errors)
        total_external_id_errors = len(self.external_id_errors)
        total_errors = total_field_errors + total_accessibility_errors + total_method_errors + total_external_id_errors
        manual_reviews = len(self.manual_review)

        print(f"📊 Scan complete:")
        print(f"   - Field errors found: {total_field_errors}")
        print(f"   - FontAwesome accessibility errors: {total_accessibility_errors}")
        print(f"   - Missing method errors: {total_method_errors}")
        print(f"   - External ID reference errors: {total_external_id_errors}")
        print(f"   - Total errors: {total_errors}")
        print(f"   - Manual review needed: {manual_reviews}")
        print(f"   - AUTO-FIXES DISABLED - Validation only mode")        # Group errors by file for targeted fixes
        errors_by_file = defaultdict(list)
        for error in self.field_errors:
            errors_by_file[error['file']].append(error)
        for error in self.accessibility_errors:
            errors_by_file[error['file']].append(error)
        for error in self.method_errors:
            errors_by_file[error['file']].append(error)

        # Save detailed report
        report_file = "mass_validation_report_no_autofixes.txt"
        with open(report_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("MASS VIEW FIELD VALIDATION REPORT - VALIDATION ONLY\n")
            f.write("=" * 80 + "\n")
            f.write(f"Models scanned: {len(self.model_fields)}\n")
            f.write(f"Field errors found: {total_field_errors}\n")
            f.write(f"FontAwesome accessibility errors: {total_accessibility_errors}\n")
            f.write(f"Missing method errors: {total_method_errors}\n")
            f.write(f"Total errors: {total_errors}\n")
            f.write(f"Manual review needed: {manual_reviews}\n")
            f.write(f"AUTO-FIXES: DISABLED (Pure validation mode)\n\n")

            if errors_by_file:
                f.write("VALIDATION ERRORS BY FILE:\n")
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
                            if error_type == 'missing_field':
                                f.write(f"    Model: {error['model']}\n")
                                f.write(f"    Field: {error['field']}\n")
                                f.write(f"    Error: {error['error']}\n")

                                if 'suggested_correction' in error and error['suggested_correction']:
                                    f.write(f"    💡 Suggested fix: {error['field']} → {error['suggested_correction']}\n")
                                elif 'similar_fields' in error and error['similar_fields']:
                                    f.write(f"    Similar fields: {', '.join(error['similar_fields'])}\n")

                            elif error_type == 'accessibility_fa_title':
                                f.write(f"    Icon: {error['icon_class']}\n")
                                f.write(f"    Error: {error['error']}\n")
                                f.write(f"    💡 Fix: Add title attribute like: <i class=\"{error['icon_class']}\" title=\"Description\"/>\n")

                            elif error_type == 'missing_action_method':
                                f.write(f"    Model: {error['model']}\n")
                                f.write(f"    Action: {error['action']}\n")
                                f.write(f"    Error: {error['error']}\n")
                                if error['available_actions']:
                                    f.write(f"    Available actions: {', '.join(error['available_actions'])}\n")
                                f.write(f"    💡 Fix: Add method to {error['model']} or remove button\n")

                            f.write("\n")

            if self.manual_review:
                f.write("\nMANUAL REVIEW ITEMS:\n")
                f.write("-" * 20 + "\n")
                for item in self.manual_review:
                    f.write(f"  {item['file']}: {item['issue']} (Type: {item['type']})\n")

        print(f"\n📄 Full report saved to: {report_file}")

        # Show top errors for immediate action by category
        if total_errors > 0:
            print(f"\n🎯 TOP ERRORS FOR IMMEDIATE FIXING:")
            print("=" * 60)

            error_count = 0

            # Show field errors
            for i, error in enumerate(self.field_errors[:10]):
                error_count += 1
                print(f"{error_count}. [FIELD] {error['file']} - {error['model']}.{error['field']}")
                if 'suggested_correction' in error and error['suggested_correction']:
                    print(f"   💡 Fix: {error['field']} → {error['suggested_correction']}")
                elif 'similar_fields' in error and error['similar_fields']:
                    print(f"   Similar: {', '.join(error['similar_fields'][:3])}")
                print()

            # Show accessibility errors
            for i, error in enumerate(self.accessibility_errors[:5]):
                error_count += 1
                print(f"{error_count}. [ACCESSIBILITY] {error['file']} - {error['icon_class']}")
                print(f"   💡 Fix: Add title attribute to FontAwesome icon")
                print()

            # Show method errors
            for i, error in enumerate(self.method_errors[:5]):
                error_count += 1
                print(f"{error_count}. [METHOD] {error['file']} - {error['model']}.{error['action']}")
                print(f"   💡 Fix: Add method to model or remove button")
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
