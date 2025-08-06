#!/usr/bin/env python3
"""
Priority Field Completion Script
Systematically adds missing fields to the highest-priority models based on view analysis.
"""

import os
import json
import re
from pathlib import Path

# Priority models based on missing field count
PRIORITY_MODELS = [
    "visitor.pos.wizard",
    "records.billing.config",
    "naid.compliance",
    "shredding.service",
    "document.retrieval.work.order",
    "records.document.type",
    "records.location",
    "records.container",
]


def load_field_analysis():
    """Load the comprehensive field analysis results"""
    analysis_file = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/field_analysis_results.json"
    )
    if os.path.exists(analysis_file):
        with open(analysis_file, "r") as f:
            return json.load(f)
    return {}


def get_field_definitions_from_views(model_name, missing_fields):
    """Extract field definitions from view files to understand field types"""
    view_files = []
    records_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )

    # Find view files that might contain this model
    model_underscore = model_name.replace(".", "_")
    for view_file in records_path.rglob("*.xml"):
        if model_underscore in view_file.name or "views" in str(view_file):
            view_files.append(view_file)

    field_definitions = {}
    for field_name in missing_fields:
        # Smart field type detection based on common patterns
        if field_name.endswith("_id"):
            field_definitions[field_name] = (
                f'fields.Many2one("res.partner", string="{field_name.replace("_", " ").title()}")'
            )
        elif field_name.endswith("_ids"):
            field_definitions[field_name] = (
                f'fields.One2many("mail.message", "res_id", string="{field_name.replace("_", " ").title()}")'
            )
        elif "date" in field_name or field_name.endswith("_date"):
            field_definitions[field_name] = (
                f'fields.Date(string="{field_name.replace("_", " ").title()}")'
            )
        elif "time" in field_name or field_name.endswith("_time"):
            field_definitions[field_name] = (
                f'fields.Datetime(string="{field_name.replace("_", " ").title()}")'
            )
        elif field_name in ["state", "status"]:
            field_definitions[field_name] = (
                'fields.Selection([("draft", "Draft"), ("active", "Active")], default="draft", tracking=True)'
            )
        elif (
            "amount" in field_name
            or "cost" in field_name
            or "price" in field_name
            or "total" in field_name
        ):
            field_definitions[field_name] = (
                f'fields.Float(string="{field_name.replace("_", " ").title()}", digits="Product Price")'
            )
        elif "count" in field_name or "qty" in field_name or "quantity" in field_name:
            field_definitions[field_name] = (
                f'fields.Integer(string="{field_name.replace("_", " ").title()}")'
            )
        elif field_name in ["active"]:
            field_definitions[field_name] = (
                'fields.Boolean(string="Active", default=True)'
            )
        elif field_name in ["company_id"]:
            field_definitions[field_name] = (
                'fields.Many2one("res.company", default=lambda self: self.env.company)'
            )
        elif field_name in ["user_id"]:
            field_definitions[field_name] = (
                'fields.Many2one("res.users", default=lambda self: self.env.user)'
            )
        else:
            # Default to Char field
            field_definitions[field_name] = (
                f'fields.Char(string="{field_name.replace("_", " ").title()}")'
            )

    return field_definitions


def add_fields_to_model(model_file_path, field_definitions):
    """Add missing fields to a model file"""
    if not os.path.exists(model_file_path):
        print(f"Model file not found: {model_file_path}")
        return False

    with open(model_file_path, "r") as f:
        content = f.read()

    # Find the class definition
    class_match = re.search(r"class\s+\w+\(models\.\w+\):", content)
    if not class_match:
        print(f"Could not find class definition in {model_file_path}")
        return False

    # Find a good insertion point (after existing fields)
    insertion_patterns = [
        r"(\n\s*# .*FIELDS.*\n)",  # After field section comments
        r"(\n\s*@api\.depends)",  # Before compute methods
        r"(\n\s*def\s+\w+)",  # Before method definitions
        r"(\n\s*_inherit\s*=.*\n)",  # After _inherit
    ]

    insertion_point = len(content)
    for pattern in insertion_patterns:
        match = re.search(pattern, content)
        if match:
            insertion_point = match.start(1)
            break

    # Create field definitions
    new_fields = []
    new_fields.append(
        "\n    # ============================================================================"
    )
    new_fields.append("    # MISSING FIELDS (Auto-generated)")
    new_fields.append(
        "    # ============================================================================"
    )

    for field_name, field_def in field_definitions.items():
        new_fields.append(f"    {field_name} = {field_def}")

    new_fields.append("")

    # Insert the fields
    new_content = (
        content[:insertion_point] + "\n".join(new_fields) + content[insertion_point:]
    )

    # Write back to file
    with open(model_file_path, "w") as f:
        f.write(new_content)

    print(f"Added {len(field_definitions)} fields to {model_file_path}")
    return True


def main():
    """Main execution function"""
    print("🚀 Priority Field Completion Script")
    print("=====================================")

    # Load field analysis
    analysis_data = load_field_analysis()

    if not analysis_data:
        print(
            "❌ No field analysis data found. Run comprehensive_field_analysis.py first."
        )
        return

    records_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )

    for model_name in PRIORITY_MODELS:
        if model_name not in analysis_data:
            print(f"⚠️  Model {model_name} not found in analysis data")
            continue

        missing_fields = analysis_data[model_name]
        if not missing_fields:
            print(f"✅ Model {model_name} has no missing fields")
            continue

        print(f"\n🎯 Processing {model_name}: {len(missing_fields)} missing fields")

        # Find model file
        model_file_name = model_name.replace(".", "_") + ".py"
        model_file_path = None

        # Search in models and wizards directories
        for search_dir in ["models", "wizards"]:
            potential_path = records_path / search_dir / model_file_name
            if potential_path.exists():
                model_file_path = potential_path
                break

        if not model_file_path:
            print(f"❌ Model file not found for {model_name}")
            continue

        # Get field definitions
        field_definitions = get_field_definitions_from_views(model_name, missing_fields)

        # Add fields to model
        if add_fields_to_model(str(model_file_path), field_definitions):
            print(f"✅ Successfully added fields to {model_name}")
        else:
            print(f"❌ Failed to add fields to {model_name}")


if __name__ == "__main__":
    main()
