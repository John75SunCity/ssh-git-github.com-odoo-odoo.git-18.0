#!/usr/bin/env python3
"""
Extract ALL label_ fields from entire records_management module and add them to field_label_customization model
"""

import os
import re
import xml.etree.ElementTree as ET


def extract_all_label_fields_comprehensive():
    """Extract all unique label_ field names from the entire records_management module"""

    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    label_fields = set()

    print("🔍 COMPREHENSIVE LABEL FIELD EXTRACTION")
    print("=" * 60)

    # Search in all file types for label_ references
    file_patterns = ["**/*.xml", "**/*.py", "**/*.js", "**/*.csv"]

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith((".xml", ".py", ".js", ".csv")):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Find all label_ field references
                    matches = re.findall(r"label_[a-zA-Z_]+", content)
                    for match in matches:
                        # Filter out non-field references
                        if not any(
                            exclude in match
                            for exclude in [
                                "label_selection",
                                "bale_label",
                                "field_label",
                            ]
                        ):
                            label_fields.add(match)

                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")

    # Sort and display results
    sorted_fields = sorted(label_fields)

    print(f"\n✅ FOUND {len(sorted_fields)} UNIQUE LABEL FIELDS:")
    for field in sorted_fields:
        print(f"  - {field}")

    return sorted_fields


def generate_comprehensive_field_definitions(label_fields):
    """Generate Python field definitions for all label fields"""

    print(f"\n🔧 GENERATING {len(label_fields)} FIELD DEFINITIONS")
    print("=" * 50)

    field_definitions = []

    for field_name in label_fields:
        # Convert field name to human-readable label
        label_parts = field_name.replace("label_", "").split("_")
        label_text = " ".join(word.title() for word in label_parts) + " Label"

        field_def = f'    {field_name} = fields.Char(string="{label_text}")'
        field_definitions.append(field_def)
        print(f"Generated: {field_name} -> {label_text}")

    return field_definitions


def update_model_file_comprehensive(field_definitions):
    """Update the field_label_customization.py file with ALL label fields"""

    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    model_file = os.path.join(base_path, "models/field_label_customization.py")

    print(f"\n📝 UPDATING MODEL FILE: {model_file}")
    print("=" * 50)

    try:
        with open(model_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove any existing label field definitions to avoid duplicates
        # Look for the section between priority field and state management
        pattern = r'(\s+# Priority for label customization \(required by demo data\)\s+priority = fields\.Integer\(string="Priority", default=10\)).*?(\s+# State Management)'

        # Create the comprehensive label fields section
        label_section = (
            "\n\n    # Label Customization Fields (comprehensive - auto-generated)\n"
        )
        label_section += "\n".join(field_definitions)
        label_section += "\n"

        # Replace with new comprehensive section
        new_content = re.sub(
            pattern, r"\1" + label_section + r"\2", content, flags=re.DOTALL
        )

        if new_content != content:
            with open(model_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ Updated model file with {len(field_definitions)} label fields")
            return True
        else:
            print("⚠️  No changes made to model file")
            return False

    except Exception as e:
        print(f"❌ Error updating model file: {e}")
        return False


def validate_model_syntax():
    """Validate that the updated model file has correct Python syntax"""

    model_file = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/field_label_customization.py"

    try:
        import ast

        with open(model_file, "r", encoding="utf-8") as f:
            content = f.read()

        ast.parse(content)
        print("✅ Python syntax validation: PASSED")
        return True

    except SyntaxError as e:
        print(f"❌ Python syntax validation: FAILED - {e}")
        return False


if __name__ == "__main__":
    # Extract all label fields comprehensively
    label_fields = extract_all_label_fields_comprehensive()

    if label_fields:
        # Generate field definitions
        field_definitions = generate_comprehensive_field_definitions(label_fields)

        # Update the model file
        if update_model_file_comprehensive(field_definitions):
            # Validate syntax
            if validate_model_syntax():
                print(f"\n🎉 SUCCESS: Added {len(label_fields)} label fields to model")
                print("✅ All label field references should now be properly defined")
            else:
                print(f"\n❌ SYNTAX ERROR: Model file has syntax issues")
        else:
            print(f"\n❌ FAILED: Could not update model file")
    else:
        print("\n❌ No label fields found to process")
