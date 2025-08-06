#!/usr/bin/env python3
"""
Smart Field Addition Script
Analyzes view files and adds missing fields to models systematically
"""

import os
import re
from pathlib import Path


def get_fields_from_view_file(view_file_path):
    """Extract field names from a view file"""
    fields = set()

    try:
        with open(view_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find all field name="" references
        field_matches = re.findall(r'<field\s+name="([^"]+)"', content)
        fields.update(field_matches)

        # Also check for domain references like [('field_name', '=', value)]
        domain_matches = re.findall(r"\('([^']+)',\s*[!=<>]+", content)
        fields.update(domain_matches)

        # Check for states="field_name" references
        states_matches = re.findall(r'states="([^"]+)"', content)
        fields.update(states_matches)

    except Exception as e:
        print(f"Error reading {view_file_path}: {e}")

    return fields


def get_existing_fields_from_model(model_file_path):
    """Get existing field names from a model file"""
    existing_fields = set()

    try:
        with open(model_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find field definitions: field_name = fields.Type(...)
        field_matches = re.findall(r"^\s*(\w+)\s*=\s*fields\.", content, re.MULTILINE)
        existing_fields.update(field_matches)

    except Exception as e:
        print(f"Error reading {model_file_path}: {e}")

    return existing_fields


def smart_field_type_detection(field_name, view_content=""):
    """Intelligently detect field type based on name patterns and view context"""
    field_name_lower = field_name.lower()

    # Many2one relationships (ends with _id)
    if field_name.endswith("_id"):
        if "user" in field_name_lower:
            return f'fields.Many2one("res.users", string="{field_name.replace("_", " ").title()}")'
        elif "company" in field_name_lower:
            return f'fields.Many2one("res.company", string="{field_name.replace("_", " ").title()}")'
        elif "partner" in field_name_lower or "customer" in field_name_lower:
            return f'fields.Many2one("res.partner", string="{field_name.replace("_", " ").title()}")'
        elif "product" in field_name_lower:
            return f'fields.Many2one("product.product", string="{field_name.replace("_", " ").title()}")'
        elif "pos_" in field_name_lower:
            return f'fields.Many2one("pos.config", string="{field_name.replace("_", " ").title()}")'
        else:
            # Generic Many2one - will need manual adjustment
            return f'fields.Many2one("res.partner", string="{field_name.replace("_", " ").title()}")  # TODO: Fix comodel'

    # One2many relationships (ends with _ids)
    elif field_name.endswith("_ids"):
        return f'fields.One2many("mail.message", "res_id", string="{field_name.replace("_", " ").title()}")  # TODO: Fix comodel and inverse'

    # Date/Time fields
    elif any(keyword in field_name_lower for keyword in ["date", "time"]):
        if "time" in field_name_lower and "date" not in field_name_lower:
            return f'fields.Datetime(string="{field_name.replace("_", " ").title()}")'
        else:
            return f'fields.Date(string="{field_name.replace("_", " ").title()}")'

    # State/Status fields
    elif field_name in ["state", "status"]:
        return 'fields.Selection([("draft", "Draft"), ("active", "Active"), ("done", "Done")], default="draft", tracking=True)'

    # Boolean fields
    elif field_name in ["active"] or any(
        keyword in field_name_lower for keyword in ["is_", "has_", "can_", "enable"]
    ):
        if field_name == "active":
            return 'fields.Boolean(string="Active", default=True)'
        else:
            return f'fields.Boolean(string="{field_name.replace("_", " ").title()}", default=False)'

    # Numeric fields
    elif any(
        keyword in field_name_lower
        for keyword in ["amount", "cost", "price", "total", "weight", "value"]
    ):
        return f'fields.Float(string="{field_name.replace("_", " ").title()}", digits="Product Price")'

    elif any(
        keyword in field_name_lower
        for keyword in ["count", "qty", "quantity", "number", "sequence"]
    ):
        return f'fields.Integer(string="{field_name.replace("_", " ").title()}")'

    # Selection fields (common patterns)
    elif any(
        keyword in field_name_lower for keyword in ["priority", "category", "type"]
    ) and not field_name.endswith("_id"):
        return f'fields.Selection([("normal", "Normal"), ("high", "High")], string="{field_name.replace("_", " ").title()}", default="normal")'

    # Text fields
    elif any(
        keyword in field_name_lower
        for keyword in ["description", "notes", "comment", "purpose"]
    ):
        return f'fields.Text(string="{field_name.replace("_", " ").title()}")'

    # Default to Char field
    else:
        return f'fields.Char(string="{field_name.replace("_", " ").title()}")'


def add_fields_to_model_file(model_file_path, missing_fields):
    """Add missing fields to a model file"""
    if not missing_fields:
        return True

    try:
        with open(model_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find a good insertion point - after existing field definitions
        insertion_patterns = [
            r"(\n\s*# .*FIELDS.*\n)",  # After field section comments
            r"(\n\s*@api\.depends)",  # Before compute methods
            r"(\n\s*def\s+\w+)",  # Before method definitions
            r"(\n\s*_rec_name\s*=.*\n)",  # After _rec_name
            r"(\n\s*_order\s*=.*\n)",  # After _order
            r"(\n\s*_inherit\s*=.*\n)",  # After _inherit
        ]

        insertion_point = -1
        for pattern in insertion_patterns:
            matches = list(re.finditer(pattern, content))
            if matches:
                # Take the last match to insert after all existing fields
                insertion_point = matches[-1].end()
                break

        if insertion_point == -1:
            # Fallback: insert before the last class closing
            insertion_point = content.rfind("\n\n")
            if insertion_point == -1:
                insertion_point = len(content)

        # Generate field definitions
        new_fields_lines = []
        new_fields_lines.append("")
        new_fields_lines.append(
            "    # ============================================================================"
        )
        new_fields_lines.append("    # AUTO-GENERATED FIELDS (from view analysis)")
        new_fields_lines.append(
            "    # ============================================================================"
        )

        for field_name in sorted(missing_fields):
            field_def = smart_field_type_detection(field_name)
            new_fields_lines.append(f"    {field_name} = {field_def}")

        new_fields_lines.append("")

        # Insert the new fields
        new_content = (
            content[:insertion_point]
            + "\n".join(new_fields_lines)
            + content[insertion_point:]
        )

        # Write back to file
        with open(model_file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True

    except Exception as e:
        print(f"Error modifying {model_file_path}: {e}")
        return False


def process_model(model_name, model_file_path, view_file_paths):
    """Process a single model - analyze views and add missing fields"""
    print(f"\n🎯 Processing {model_name}")
    print(f"   Model file: {model_file_path}")
    print(f"   View files: {len(view_file_paths)} found")

    # Get all fields referenced in views
    view_fields = set()
    for view_file_path in view_file_paths:
        fields_in_view = get_fields_from_view_file(view_file_path)
        view_fields.update(fields_in_view)
        print(f"   View {view_file_path.name}: {len(fields_in_view)} fields")

    # Get existing fields in model
    existing_fields = get_existing_fields_from_model(model_file_path)
    print(f"   Existing fields in model: {len(existing_fields)}")

    # Find missing fields
    missing_fields = view_fields - existing_fields

    # Filter out obvious framework/system fields that shouldn't be added
    system_fields = {
        "id",
        "create_date",
        "create_uid",
        "write_date",
        "write_uid",
        "__last_update",
        "display_name",
        "x_studio_",
        "message_main_attachment_id",
    }
    missing_fields = {
        f for f in missing_fields if not any(sf in f for sf in system_fields)
    }

    print(f"   Missing fields: {len(missing_fields)}")
    if missing_fields:
        print(
            f"   Fields to add: {', '.join(sorted(list(missing_fields)[:10]))}{'...' if len(missing_fields) > 10 else ''}"
        )

    if missing_fields:
        if add_fields_to_model_file(model_file_path, missing_fields):
            print(f"   ✅ Successfully added {len(missing_fields)} fields")
            return len(missing_fields)
        else:
            print(f"   ❌ Failed to add fields")
            return 0
    else:
        print(f"   ✅ No missing fields")
        return 0


def main():
    """Main function"""
    print("🚀 Smart Field Addition Script")
    print("===============================")

    records_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )

    # Priority models to process
    priority_models = [
        "visitor.pos.wizard",
        "records.billing.config",
        "naid.compliance",
        "records.document.type",
        "records.location",
    ]

    total_fields_added = 0

    for model_name in priority_models:
        # Find model file
        model_underscore = model_name.replace(".", "_")
        model_file_path = None

        # Search in models and wizards directories
        for search_dir in ["models", "wizards"]:
            potential_path = records_path / search_dir / f"{model_underscore}.py"
            if potential_path.exists():
                model_file_path = potential_path
                break

        if not model_file_path:
            print(f"\n❌ Model file not found for {model_name}")
            continue

        # Find related view files
        view_file_paths = []
        for view_file in records_path.rglob("*.xml"):
            if model_underscore in str(view_file) or model_name in str(view_file):
                view_file_paths.append(view_file)

        # Also search for any view that might reference this model
        if not view_file_paths:
            for view_file in (records_path / "views").glob("*.xml"):
                try:
                    with open(view_file, "r") as f:
                        content = f.read()
                        if model_name in content:
                            view_file_paths.append(view_file)
                except:
                    continue

        # Process the model
        fields_added = process_model(model_name, model_file_path, view_file_paths)
        total_fields_added += fields_added

    print(
        f"\n🎉 Complete! Added {total_fields_added} total fields across {len(priority_models)} models"
    )
    print(
        f"📝 Review the auto-generated fields and adjust comodel references as needed"
    )
    print(f"🚀 Ready for commit and deployment")


if __name__ == "__main__":
    main()
