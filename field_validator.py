#!/usr/bin/env python3
"""
Comprehensive field validation and auto-fix for view XML files.
This script validates that all field references in views exist in their corresponding models
and attempts to fix common naming issues automatically.
"""

import os
import re
import ast
import glob
from xml.etree import ElementTree as ET

class FieldValidator:
    def __init__(self):
        self.model_fields = {}
        self.fixes_applied = 0

    def scan_models(self):
        """Scan Python model files to collect field definitions."""
        print("🔍 Scanning model files for field definitions...")

        model_files = glob.glob('records_management/models/*.py')

        for file_path in model_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Look for _name attribute
                        model_name = None
                        for item in node.body:
                            if (isinstance(item, ast.Assign) and
                                len(item.targets) == 1 and
                                isinstance(item.targets[0], ast.Name) and
                                item.targets[0].id == '_name'):
                                if isinstance(item.value, ast.Constant):
                                    model_name = item.value.value
                                elif isinstance(item.value, ast.Str):
                                    model_name = item.value.s

                        if model_name:
                            fields = set()
                            # Scan for field definitions
                            for item in node.body:
                                if (isinstance(item, ast.Assign) and
                                    len(item.targets) == 1 and
                                    isinstance(item.targets[0], ast.Name)):

                                    field_name = item.targets[0].id
                                    if isinstance(item.value, ast.Call):
                                        # Check if it's a fields.* call
                                        if (isinstance(item.value.func, ast.Attribute) and
                                            isinstance(item.value.func.value, ast.Name) and
                                            item.value.func.value.id == 'fields'):
                                            fields.add(field_name)

                            if fields:
                                self.model_fields[model_name] = fields
                                print(f"  ✅ {model_name}: {len(fields)} fields")

            except Exception as e:
                print(f"  ⚠️ Error scanning {file_path}: {e}")

    def get_common_fixes(self, model_name, field_name):
        """Get common field name fixes based on patterns."""
        if model_name not in self.model_fields:
            return []

        available_fields = self.model_fields[model_name]
        potential_fixes = []

        # Common patterns
        # Plural to singular
        if field_name.endswith('_ids') and field_name[:-4] + '_id' in available_fields:
            potential_fixes.append(field_name[:-4] + '_id')

        # Singular to plural
        if field_name.endswith('_id') and field_name[:-3] + '_ids' in available_fields:
            potential_fixes.append(field_name[:-3] + '_ids')

        # Remove/add common suffixes
        for suffix in ['_count', '_total', '_amount', '_date', '_datetime']:
            if field_name.endswith(suffix):
                base = field_name[:-len(suffix)]
                if base in available_fields:
                    potential_fixes.append(base)
            else:
                candidate = field_name + suffix
                if candidate in available_fields:
                    potential_fixes.append(candidate)

        return potential_fixes

    def fix_view_file(self, file_path):
        """Fix field references in a single view file."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            fixes_in_file = 0

            # Find all view records
            for record in root.findall(".//record[@model='ir.ui.view']"):
                model_field = record.find(".//field[@name='model']")
                arch_field = record.find(".//field[@name='arch']")

                if model_field is not None and arch_field is not None:
                    model_name = model_field.text

                    if model_name in self.model_fields:
                        available_fields = self.model_fields[model_name]

                        # Find all field references in arch
                        for field_elem in arch_field.findall(".//field[@name]"):
                            field_name = field_elem.get('name')

                            if field_name not in available_fields:
                                # Try to find a fix
                                potential_fixes = self.get_common_fixes(model_name, field_name)

                                if potential_fixes:
                                    fix = potential_fixes[0]  # Use first fix
                                    print(f"    🔧 {model_name}.{field_name} → {fix}")
                                    field_elem.set('name', fix)
                                    fixes_in_file += 1
                                else:
                                    print(f"    ❌ {model_name}.{field_name} - no fix found")

            if fixes_in_file > 0:
                # Write back the fixed XML
                tree.write(file_path, encoding='utf-8', xml_declaration=True)
                self.fixes_applied += fixes_in_file
                return True

            return False

        except Exception as e:
            print(f"  ⚠️ Error processing {file_path}: {e}")
            return False

    def validate_and_fix_views(self):
        """Validate and fix all view files."""
        print("\n🔧 Validating and fixing view files...")

        view_files = glob.glob('records_management/views/*.xml')
        fixed_files = 0

        for file_path in view_files:
            print(f"  📄 {os.path.basename(file_path)}")
            if self.fix_view_file(file_path):
                fixed_files += 1
                print(f"    ✅ Fixed")
            else:
                print(f"    ⏭️ No changes needed")

        print(f"\n📊 Summary:")
        print(f"   Files processed: {len(view_files)}")
        print(f"   Files with fixes: {fixed_files}")
        print(f"   Total field fixes: {self.fixes_applied}")

def main():
    validator = FieldValidator()

    # First scan all models to understand available fields
    validator.scan_models()

    print(f"\n✅ Found {len(validator.model_fields)} models with field definitions")

    # Then validate and fix view files
    validator.validate_and_fix_views()

if __name__ == "__main__":
    main()
