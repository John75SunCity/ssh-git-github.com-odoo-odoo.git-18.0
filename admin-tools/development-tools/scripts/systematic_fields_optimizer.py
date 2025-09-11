#!/usr/bin/env python3
"""
Systematic Standard Fields Optimizer
Adds missing standard fields (company_id, user_id, active, name) to models
"""

import os
import re
import json


def read_optimization_data():
    """Read optimization data from audit report"""
    with open("development-tools/odoo_enhanced_audit_report.json", "r") as f:
        data = json.load(f)

    missing_fields_optimizations = []
    for opt in data.get("optimizations", []):
        if opt.get("type") == "missing_standard_fields":
            missing_fields_optimizations.append(opt)

    return missing_fields_optimizations


def find_model_file(model_name):
    """Find the Python file containing the model"""
    # Convert model name to potential file name
    potential_names = [
        model_name.replace(".", "_") + ".py",
        model_name.replace("_", ".").replace(".", "_") + ".py",
        model_name.split(".")[-1] + ".py",
    ]

    # Search in models directory
    models_dir = "records_management/models"
    for filename in os.listdir(models_dir):
        if filename.endswith(".py") and any(
            name in filename for name in potential_names
        ):
            return os.path.join(models_dir, filename)

    # Search for model _name in all files
    for filename in os.listdir(models_dir):
        if filename.endswith(".py"):
            filepath = os.path.join(models_dir, filename)
            try:
                with open(filepath, "r") as f:
                    content = f.read()
                    if (
                        f'_name = "{model_name}"' in content
                        or f"_name = '{model_name}'" in content
                    ):
                        return filepath
            except:
                continue

    return None


def analyze_model_file(filepath, missing_fields):
    """Analyze model file to see what fields are actually missing"""
    try:
        with open(filepath, "r") as f:
            content = f.read()

        actually_missing = []
        for field in missing_fields:
            # Check if field already exists
            if not re.search(rf"{field}\s*=\s*fields\.", content):
                actually_missing.append(field)

        return actually_missing, content
    except:
        return missing_fields, ""


def generate_standard_fields(missing_fields):
    """Generate standard field definitions"""
    fields = []

    if "name" in missing_fields:
        fields.append(
            '    name = fields.Char(string="Name", required=True, tracking=True, index=True)'
        )

    if "company_id" in missing_fields:
        fields.append("    company_id = fields.Many2one(")
        fields.append(
            '        "res.company", default=lambda self: self.env.company, required=True'
        )
        fields.append("    )")

    if "user_id" in missing_fields:
        fields.append("    user_id = fields.Many2one(")
        fields.append(
            '        "res.users", default=lambda self: self.env.user, tracking=True'
        )
        fields.append("    )")

    if "active" in missing_fields:
        fields.append('    active = fields.Boolean(string="Active", default=True)')

    return fields


def add_mail_thread_inheritance(content, class_line):
    """Add mail.thread inheritance if missing"""
    if "_inherit = [" in content or "_inherit = ['mail.thread'" in content:
        return content  # Already has inheritance

    # Find class definition and add inheritance
    pattern = r"(class\s+\w+\(models\.Model\):)"
    replacement = r"\1\n    _inherit = [\'mail.thread\', \'mail.activity.mixin\']"

    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)

    return content


def optimize_model_file(filepath, missing_fields):
    """Add missing standard fields to model file"""
    try:
        actually_missing, content = analyze_model_file(filepath, missing_fields)

        if not actually_missing:
            print(f"✅ {filepath}: All standard fields already present")
            return True

        # Add mail.thread inheritance if needed
        if (
            any(field in actually_missing for field in ["user_id", "company_id"])
            and "_inherit" not in content
        ):
            content = add_mail_thread_inheritance(content, "")

        # Generate field definitions
        field_definitions = generate_standard_fields(actually_missing)

        if not field_definitions:
            return True

        # Find a good place to insert fields (after class definition, before other fields)
        class_match = re.search(
            r"(class\s+\w+\(models\.Model\):.*?\n)", content, re.DOTALL
        )
        if not class_match:
            print(f"❌ {filepath}: Could not find class definition")
            return False

        # Look for existing field definitions to insert before them
        field_pattern = r"(\n\s+\w+\s*=\s*fields\.)"
        field_match = re.search(field_pattern, content)

        if field_match:
            # Insert before first field
            insert_point = field_match.start(1)
            header = "\n    # ============================================================================"
            header += "\n    # CORE IDENTIFICATION FIELDS"
            header += "\n    # ============================================================================\n"
            fields_block = header + "\n".join(field_definitions) + "\n"
            content = content[:insert_point] + fields_block + content[insert_point:]
        else:
            # Insert after class definition
            class_end = class_match.end()
            header = "\n    # ============================================================================"
            header += "\n    # CORE IDENTIFICATION FIELDS"
            header += "\n    # ============================================================================\n"
            fields_block = header + "\n".join(field_definitions) + "\n"
            content = content[:class_end] + fields_block + content[class_end:]

        # Write back to file
        with open(filepath, "w") as f:
            f.write(content)

        print(
            f"✅ {filepath}: Added {len(actually_missing)} missing fields: {actually_missing}"
        )
        return True

    except Exception as e:
        print(f"❌ {filepath}: Error - {str(e)}")
        return False


def main():
    """Main optimization process"""
    print("🚀 Starting Systematic Standard Fields Optimization")
    print("=" * 60)

    # Read optimization data
    optimizations = read_optimization_data()
    print(f"📊 Found {len(optimizations)} models missing standard fields")

    processed = 0
    errors = 0

    for opt in optimizations:
        model_name = opt.get("model")
        missing_fields = opt.get("missing_fields", [])

        print(f"\n🔍 Processing {model_name}...")
        print(f"   Missing fields: {missing_fields}")

        # Find model file
        filepath = find_model_file(model_name)
        if not filepath:
            print(f"❌ Could not find file for model {model_name}")
            errors += 1
            continue

        # Optimize the file
        if optimize_model_file(filepath, missing_fields):
            processed += 1
        else:
            errors += 1

    print("\n" + "=" * 60)
    print(f"📊 OPTIMIZATION SUMMARY:")
    print(f"   Processed: {processed}")
    print(f"   Errors: {errors}")
    print(f"   Total: {len(optimizations)}")

    if errors == 0:
        print("🎉 All optimizations completed successfully!")
    else:
        print(f"⚠️  {errors} models had issues - check output above")


if __name__ == "__main__":
    main()
