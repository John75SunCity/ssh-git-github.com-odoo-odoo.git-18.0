#!/usr/bin/env python3
"""
Bulk State Field Adder Script
Systematically adds state fields to all Records Management models that need them
"""

import os
import re
import glob


def add_state_field_to_model(filepath):
    """Add state field to a model file"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Skip if state field already exists
        if re.search(r"state\s*=\s*fields\.", content):
            return False, "Already has state field"

        # Skip if this is not a regular model
        if "TransientModel" in content or "_abstract = True" in content:
            return False, "TransientModel or Abstract"

        # Skip inheritance models that don't define new models
        if "_inherit =" in content and "_name =" not in content:
            return False, "Inheritance only"

        # Validate this is an Odoo model file
        if not re.search(r"from odoo import.*models", content):
            return False, "Not an Odoo model file"

        # Find insertion point using improved logic
        lines = content.split("\n")
        insertion_point = find_field_insertion_point(lines)

        if insertion_point == -1:
            return False, "Could not find suitable insertion point"

        # Generate appropriate state field for Records Management
        state_field = generate_state_field(filepath)

        # Insert the field
        lines[insertion_point:insertion_point] = state_field

        # Write back to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return True, "State field added successfully"

    except Exception as e:
        return False, f"Error: {str(e)}"


def find_field_insertion_point(lines):
    """Find the best place to insert state field"""
    insertion_point = -1

    # Strategy 1: Find after last field definition
    field_pattern = re.compile(r"^\s+\w+\s*=\s*fields\.")
    last_field_line = -1

    i = 0
    while i < len(lines):
        line = lines[i]
        if field_pattern.match(line):
            last_field_line = i
            # Skip multi-line field definitions properly
            i = skip_multiline_field(lines, i)
        else:
            i += 1

    if last_field_line != -1:
        return last_field_line + 1

    # Strategy 2: Find after class metadata but before methods
    in_class = False
    metadata_end = -1

    for i, line in enumerate(lines):
        if "class " in line and "(models." in line:
            in_class = True
            continue

        if in_class:
            stripped = line.strip()
            # Skip metadata lines
            if (
                stripped.startswith("_") and "=" in stripped
            ) or stripped == "":
                metadata_end = i + 1
            elif stripped and not stripped.startswith("#"):
                # Found first non-metadata line
                break

    if metadata_end != -1:
        return metadata_end

    return -1


def skip_multiline_field(lines, start_line):
    """Skip multi-line field definitions properly"""
    i = start_line
    open_parens = lines[i].count("(") - lines[i].count(")")

    # Continue until parentheses are balanced and line doesn't end with comma
    while i < len(lines) - 1:
        i += 1
        line = lines[i]
        open_parens += line.count("(") - line.count(")")

        if open_parens <= 0 and not line.rstrip().endswith(","):
            break

    return i


def generate_state_field(filepath):
    """Generate appropriate state field based on model type"""
    filename = os.path.basename(filepath).lower()

    # Determine appropriate states based on model type
    if any(term in filename for term in ["pickup", "request", "service"]):
        states = [
            "        ('draft', 'Draft'),",
            "        ('submitted', 'Submitted'),",
            "        ('confirmed', 'Confirmed'),",
            "        ('in_progress', 'In Progress'),",
            "        ('completed', 'Completed'),",
            "        ('cancelled', 'Cancelled'),",
        ]
    elif any(term in filename for term in ["billing", "invoice", "payment"]):
        states = [
            "        ('draft', 'Draft'),",
            "        ('confirmed', 'Confirmed'),",
            "        ('sent', 'Sent'),",
            "        ('paid', 'Paid'),",
            "        ('overdue', 'Overdue'),",
            "        ('cancelled', 'Cancelled'),",
        ]
    elif any(
        term in filename for term in ["destruction", "shredding", "audit"]
    ):
        states = [
            "        ('pending', 'Pending'),",
            "        ('scheduled', 'Scheduled'),",
            "        ('in_progress', 'In Progress'),",
            "        ('completed', 'Completed'),",
            "        ('verified', 'Verified'),",
            "        ('cancelled', 'Cancelled'),",
        ]
    else:
        # Generic workflow states
        states = [
            "        ('draft', 'Draft'),",
            "        ('active', 'Active'),",
            "        ('inactive', 'Inactive'),",
            "        ('archived', 'Archived'),",
        ]

    return [
        "",
        "    # Workflow state management",
        "    state = fields.Selection([",
        *states,
        "    ], string='Status', default='draft', tracking=True, required=True, index=True,",
        "       help='Current status of the record')",
    ]


def find_models_needing_state_fields():
    """Find all models that need state fields"""
    model_files = glob.glob("records_management/models/*.py")
    models_needing_state = []

    for filepath in sorted(model_files):
        if "__init__.py" in filepath:
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Skip if not a regular model
            if (
                "TransientModel" in content
                or "_abstract = True" in content
                or ("_inherit =" in content and "_name =" not in content)
            ):
                continue

            # Must be an Odoo model file
            if not re.search(r"from odoo import.*models", content):
                continue

            # Check if model name exists
            model_name_match = re.search(
                r"_name\s*=\s*['\"]([^'\"]+)['\"]", content
            )
            if not model_name_match:
                continue

            # Check if state field exists
            if not re.search(r"state\s*=\s*fields\.", content):
                models_needing_state.append(
                    {
                        "filepath": filepath,
                        "filename": os.path.basename(filepath),
                        "model_name": model_name_match.group(1),
                    }
                )

        except Exception as e:
            print(f"Error checking {filepath}: {e}")
            continue

    return models_needing_state


def validate_syntax_after_changes():
    """Quick syntax validation of modified files"""
    try:
        import ast

        model_files = glob.glob("records_management/models/*.py")
        errors = []

        for filepath in model_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    ast.parse(f.read())
            except SyntaxError as e:
                errors.append(f"{filepath}: {e}")

        return errors
    except ImportError:
        return ["Cannot validate syntax - ast module not available"]


def main():
    """Main function"""
    print("🔍 Finding models that need state fields...\n")

    models_to_update = find_models_needing_state_fields()

    if not models_to_update:
        print("✅ All models already have state fields!")
        return

    print(f"Found {len(models_to_update)} models that need state fields:\n")

    success_count = 0
    failed_models = []

    for model_info in models_to_update:
        print(
            f"🔧 Processing {model_info['filename']} ({model_info['model_name']})..."
        )
        success, message = add_state_field_to_model(model_info["filepath"])

        if success:
            print(f"   ✅ {message}")
            success_count += 1
        else:
            print(f"   ⏭️  Skipped: {message}")
            failed_models.append((model_info["filename"], message))

    print(
        f"\n📊 Summary: {success_count}/{len(models_to_update)} models updated"
    )

    if failed_models:
        print(f"\n⚠️  Failed to update {len(failed_models)} models:")
        for filename, reason in failed_models:
            print(f"   - {filename}: {reason}")

    if success_count > 0:
        print("\n🔍 Running syntax validation...")
        syntax_errors = validate_syntax_after_changes()

        if syntax_errors:
            print("❌ Syntax errors found:")
            for error in syntax_errors[:5]:  # Show first 5 errors
                print(f"   {error}")
            if len(syntax_errors) > 5:
                print(f"   ... and {len(syntax_errors) - 5} more")
        else:
            print("✅ No syntax errors found!")

        print("\n🎉 State fields added! Next steps:")
        print("1. Review the added state fields for appropriateness")
        print("2. Add state transition methods if needed")
        print("3. Test the models in Odoo")
        print("4. Consider adding workflow actions for state changes")


if __name__ == "__main__":
    main()
