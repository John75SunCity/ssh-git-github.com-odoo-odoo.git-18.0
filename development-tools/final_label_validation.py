#!/usr/bin/env python3
"""
Final validation: Check if all label_* field references are now properly defined
"""

import os
import re


def validate_all_label_references():
    """Validate that all label_* references in the module are now properly defined"""

    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    model_file = os.path.join(base_path, "models/field_label_customization.py")

    print("🔍 FINAL LABEL FIELD VALIDATION")
    print("=" * 50)

    # Get all defined fields from the model
    defined_fields = set()
    try:
        with open(model_file, "r", encoding="utf-8") as f:
            model_content = f.read()

        # Extract all label_ field definitions
        field_matches = re.findall(r"(label_[a-zA-Z_]+)\s*=\s*fields\.", model_content)
        defined_fields.update(field_matches)

        print(f"✅ Found {len(defined_fields)} defined label fields in model")

    except Exception as e:
        print(f"❌ Error reading model file: {e}")
        return False

    # Find all label_ references in the entire module
    referenced_fields = set()
    missing_fields = set()

    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith((".xml", ".py", ".js", ".csv")):
                file_path = os.path.join(root, file)

                # Skip the model file itself
                if file_path == model_file:
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Find label_ references that look like field names
                    matches = re.findall(r"label_[a-zA-Z_]+", content)
                    for match in matches:
                        # Filter out non-field references
                        if not any(
                            exclude in match
                            for exclude in [
                                "label_selection",
                                "bale_label",
                                "field_label",
                                "label_report",
                                "label_template",
                                "label_customization_",
                                "label_manager",
                                "label_user",
                                "label_portal",
                                "label_demo_data",
                                "label_customizer",
                                "label_views",
                            ]
                        ):
                            referenced_fields.add(match)
                            if match not in defined_fields:
                                missing_fields.add(match)

                except Exception as e:
                    continue  # Skip files that can't be read

    print(f"✅ Found {len(referenced_fields)} unique label field references")

    if missing_fields:
        print(f"\n❌ MISSING FIELDS ({len(missing_fields)}):")
        for field in sorted(missing_fields):
            print(f"  - {field}")
        return False
    else:
        print(f"\n✅ ALL LABEL FIELD REFERENCES ARE PROPERLY DEFINED!")
        print(f"✅ {len(referenced_fields)} referenced fields")
        print(f"✅ {len(defined_fields)} defined fields")
        print(f"✅ 0 missing fields")
        return True


if __name__ == "__main__":
    if validate_all_label_references():
        print(f"\n🎉 SUCCESS: All label field references are properly handled!")
        print("✅ The module should now deploy without missing field errors")
    else:
        print(f"\n❌ VALIDATION FAILED: Some label fields are still missing")
        print("⚠️  Run the script again to fix remaining issues")
