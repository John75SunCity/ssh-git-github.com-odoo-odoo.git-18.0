#!/usr/bin/env python3
"""
COMPREHENSIVE FIELD COMPLETION FROM RECOMMENDATIONS
==================================================

This script parses the gap analysis recommendations and adds ALL missing fields
to ALL models with comprehensive field definitions.
"""

import os
import re
import subprocess
from pathlib import Path


def get_intelligent_field_type(field_name):
    """Get intelligent field type based on field name patterns."""
    field_lower = field_name.lower()

    # ID fields -> Many2one with intelligent model mapping
    if field_lower.endswith("_id"):
        base = field_lower.replace("_id", "")

        model_mappings = {
            "partner": "fields.Many2one('res.partner', string='Partner', tracking=True)",
            "customer": "fields.Many2one('res.partner', string='Customer', tracking=True)",
            "user": "fields.Many2one('res.users', string='User', tracking=True)",
            "company": "fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)",
            "employee": "fields.Many2one('hr.employee', string='Employee', tracking=True)",
            "product": "fields.Many2one('product.product', string='Product', tracking=True)",
            "currency": "fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)",
            "location": "fields.Many2one('stock.location', string='Location', tracking=True)",
            "project": "fields.Many2one('project.project', string='Project', tracking=True)",
            "task": "fields.Many2one('project.task', string='Task', tracking=True)",
            "order": "fields.Many2one('sale.order', string='Order', tracking=True)",
            "invoice": "fields.Many2one('account.move', string='Invoice', tracking=True)",
            "box": "fields.Many2one('records.container', string='Box', tracking=True)",
            "container": "fields.Many2one('records.container', string='Container', tracking=True)",
            "document": "fields.Many2one('records.document', string='Document', tracking=True)",
            "billing": "fields.Many2one('records.billing.config', string='Billing Config', tracking=True)",
            "service": "fields.Many2one('records.billing.service', string='Service', tracking=True)",
        }

        for key, mapping in model_mappings.items():
            if key in base:
                return mapping

        # Default Many2one
        model_name = base.replace("_", ".")
        return f"fields.Many2one('{model_name}', string='{field_name.replace('_', ' ').title()}', tracking=True)"

    # IDS fields -> One2many with better model guessing
    if field_lower.endswith("_ids"):
        base = field_lower.replace("_ids", "")
        if "line" in base:
            return f"fields.One2many('{base.replace('_', '.')}.line', 'parent_id', string='{field_name.replace('_', ' ').title()}')"
        else:
            return f"fields.One2many('{base.replace('_', '.')}.item', 'parent_id', string='{field_name.replace('_', ' ').title()}')"

    # Monetary fields with currency support
    if any(
        word in field_lower
        for word in [
            "amount",
            "cost",
            "price",
            "rate",
            "fee",
            "total",
            "balance",
            "charge",
        ]
    ):
        return "fields.Monetary(string='Amount', currency_field='currency_id', tracking=True)"

    # Date fields with intelligent defaults
    if "date" in field_lower:
        if any(word in field_lower for word in ["created", "start", "begin"]):
            return (
                "fields.Date(string='Date', default=fields.Date.today, tracking=True)"
            )
        elif any(word in field_lower for word in ["deadline", "due", "end", "expir"]):
            return "fields.Date(string='Date', tracking=True)"
        else:
            return "fields.Date(string='Date', tracking=True)"

    # DateTime fields
    if any(word in field_lower for word in ["datetime", "timestamp"]):
        return "fields.Datetime(string='Date Time', tracking=True)"

    # Boolean fields with smart defaults
    if field_lower.startswith(("is_", "has_", "can_", "should_", "must_")):
        return "fields.Boolean(string='Flag', default=False, tracking=True)"
    elif any(
        word in field_lower for word in ["active", "enabled", "published", "approved"]
    ):
        default = "True" if "active" in field_lower else "False"
        return f"fields.Boolean(string='Flag', default={default}, tracking=True)"
    elif any(
        word in field_lower
        for word in ["required", "mandatory", "locked", "completed", "destroyed"]
    ):
        return "fields.Boolean(string='Flag', default=False, tracking=True)"

    # Integer fields with appropriate defaults
    if any(word in field_lower for word in ["count", "number", "qty", "quantity"]):
        return "fields.Integer(string='Count', default=0, tracking=True)"
    elif any(word in field_lower for word in ["sequence", "order", "priority"]):
        return "fields.Integer(string='Sequence', default=10, tracking=True)"

    # Float fields with proper digits
    if any(word in field_lower for word in ["weight", "volume", "capacity", "size"]):
        return "fields.Float(string='Value', digits=(10, 3), tracking=True)"
    elif any(word in field_lower for word in ["percentage", "rate", "score", "ratio"]):
        return "fields.Float(string='Percentage', digits=(5, 2), tracking=True)"
    elif any(word in field_lower for word in ["length", "width", "height", "depth"]):
        return "fields.Float(string='Dimension', digits=(10, 2), tracking=True)"

    # Selection fields with intelligent options
    if any(word in field_lower for word in ["status", "state"]):
        return "fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], string='Status', default='draft', tracking=True)"
    elif "type" in field_lower:
        return "fields.Selection([('standard', 'Standard'), ('premium', 'Premium'), ('custom', 'Custom')], string='Type', tracking=True)"
    elif "priority" in field_lower:
        return "fields.Selection([('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], string='Priority', default='normal', tracking=True)"
    elif "method" in field_lower:
        return "fields.Selection([('manual', 'Manual'), ('automatic', 'Automatic')], string='Method', default='manual', tracking=True)"

    # Text fields for longer content
    if any(
        word in field_lower
        for word in [
            "description",
            "notes",
            "comment",
            "message",
            "details",
            "remarks",
            "instruction",
        ]
    ):
        return "fields.Text(string='Description', tracking=True)"

    # HTML fields for rich content
    if any(word in field_lower for word in ["content", "body", "html"]):
        return "fields.Html(string='Content')"

    # Email and phone fields
    if any(word in field_lower for word in ["email", "mail"]):
        return "fields.Char(string='Email', tracking=True)"
    elif any(word in field_lower for word in ["phone", "mobile", "tel"]):
        return "fields.Char(string='Phone', tracking=True)"

    # URL fields
    if any(word in field_lower for word in ["url", "link", "website"]):
        return "fields.Char(string='URL')"

    # Binary fields
    if any(word in field_lower for word in ["image", "photo", "picture", "logo"]):
        return "fields.Binary(string='Image')"
    elif any(word in field_lower for word in ["file", "attachment", "document"]):
        return "fields.Binary(string='File')"

    # Default to Char with proper string
    title = field_name.replace("_", " ").title()
    return f"fields.Char(string='{title}', tracking=True)"


def parse_gap_analysis_recommendations():
    """Parse the gap analysis output to extract field recommendations."""
    try:
        print("🔍 Running complete gap analysis...")
        result = subprocess.run(
            ["python3", "development-tools/smart_field_gap_analysis.py"],
            capture_output=True,
            text=True,
            cwd="/workspaces/ssh-git-github.com-odoo-odoo.git-18.0",
        )

        if result.returncode != 0:
            print("❌ Could not run gap analysis")
            return {}

        output = result.stdout
        lines = output.split("\n")

        model_fields = {}
        current_model = None
        parsing_fields = False

        for line in lines:
            # Look for model sections in recommendations
            if line.strip().startswith("📝 ") and ":" in line:
                # Extract model name
                model_part = line.split("📝 ")[1].split(":")[0].strip()
                current_model = model_part
                parsing_fields = True
                model_fields[current_model] = []
                continue

            # Parse field definitions
            if parsing_fields and current_model and line.strip():
                if line.strip().startswith("#") or line.strip().startswith("🚀"):
                    # End of model section
                    parsing_fields = False
                    current_model = None
                    continue

                # Extract field name from field definitions
                if "=" in line and "fields." in line:
                    field_line = line.strip()
                    field_name = field_line.split("=")[0].strip()
                    if field_name and field_name.isidentifier():
                        model_fields[current_model].append(field_name)

        # Also parse from the summary sections
        for line in lines:
            if (
                line.strip().startswith("📋 ")
                and "(" in line
                and "missing fields):" in line
            ):
                # Extract model name and check for business fields
                model_part = line.split("📋 ")[1].split("(")[0].strip()

                # Look for business fields section
                if model_part not in model_fields:
                    model_fields[model_part] = []

        # Filter out empty entries
        model_fields = {k: v for k, v in model_fields.items() if v}

        print(f"📋 Found field recommendations for {len(model_fields)} models")
        for model, fields in model_fields.items():
            print(f"   • {model}: {len(fields)} fields")

        return model_fields

    except Exception as e:
        print(f"❌ Error parsing recommendations: {e}")
        return {}


def add_comprehensive_fields_to_model(model_file, field_names):
    """Add comprehensive field definitions to model file."""
    try:
        with open(model_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find insertion point (after last field)
        field_pattern = (
            r"(\s+\w+\s*=\s*fields\..*?)(?=\n\s*(?:def|\s*#|\s*@|\s*$|class))"
        )
        field_matches = list(re.finditer(field_pattern, content, re.DOTALL))

        if field_matches:
            insert_pos = field_matches[-1].end()
        else:
            # Insert after class definition
            class_match = re.search(r"class\s+\w+\(.*?\):\s*\n", content)
            if class_match:
                insert_pos = class_match.end()
                # Skip docstring
                remaining = content[insert_pos:].lstrip()
                if remaining.startswith('"""') or remaining.startswith("'''"):
                    quote = '"""' if remaining.startswith('"""') else "'''"
                    docstring_end = remaining.find(quote, 3)
                    if docstring_end != -1:
                        insert_pos += (
                            len(content[insert_pos:])
                            - len(remaining)
                            + docstring_end
                            + 3
                        )
                        while insert_pos < len(content) and content[insert_pos] != "\n":
                            insert_pos += 1
                        insert_pos += 1
            else:
                return False

        # Generate field definitions
        additions = []
        additions.append("\n    # === COMPREHENSIVE MISSING FIELDS ===")

        for field_name in field_names:
            field_def = get_intelligent_field_type(field_name)
            additions.append(f"    {field_name} = {field_def}")

        additions.append("")

        # Insert fields
        new_content = content[:insert_pos] + "\n".join(additions) + content[insert_pos:]

        with open(model_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True

    except Exception as e:
        print(f"      ❌ Error: {e}")
        return False


def check_syntax(model_file):
    """Check Python syntax."""
    try:
        result = subprocess.run(
            ["python3", "-m", "py_compile", model_file], capture_output=True, text=True
        )
        return result.returncode == 0, result.stderr
    except:
        return False, "Compilation failed"


def main():
    """Main execution."""
    print("🚀 COMPREHENSIVE FIELD COMPLETION FROM RECOMMENDATIONS")
    print("=" * 70)

    # Parse recommendations
    model_fields = parse_gap_analysis_recommendations()

    if not model_fields:
        print("❌ No field recommendations found!")

        # Try direct processing from the most critical models
        print("🔄 Attempting direct processing of critical models...")

        critical_models = [
            "visitor.pos.wizard",
            "customer.inventory.report",
            "portal.feedback",
            "shredding.hard_drive",
            "records.container",
            "bin.unlock.service",
            "paper.bale.recycling",
            "shredding.inventory.item",
            "records.location",
            "key.restriction.checker",
        ]

        # Add some common fields to these models
        common_fields = [
            "active",
            "sequence",
            "notes",
            "state",
            "created_date",
            "updated_date",
        ]
        model_fields = {model: common_fields for model in critical_models}

    base_dir = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )
    models_dir = base_dir / "models"

    total_fields_added = 0
    models_processed = 0

    print(f"\n🔧 Processing {len(model_fields)} models...")

    for model_name, field_names in model_fields.items():
        print(f"\n📝 {model_name} ({len(field_names)} fields)")

        # Find model file
        model_file_name = model_name.replace(".", "_") + ".py"
        model_file = models_dir / model_file_name

        if not model_file.exists():
            print(f"      ⚠️  Model file not found: {model_file_name}")
            continue

        # Add fields
        if add_comprehensive_fields_to_model(model_file, field_names):
            # Check syntax
            syntax_ok, error_msg = check_syntax(model_file)
            if syntax_ok:
                print(f"      ✅ Added {len(field_names)} comprehensive fields")
                total_fields_added += len(field_names)
                models_processed += 1
            else:
                print(f"      ⚠️  Syntax error after adding fields")
                print(f"         {error_msg[:150]}...")
        else:
            print(f"      ❌ Failed to add fields")

    print("\n" + "=" * 70)
    print("📊 COMPLETION SUMMARY")
    print(f"✅ Successfully processed: {models_processed} models")
    print(f"📝 Total fields added: {total_fields_added}")

    if total_fields_added > 0:
        print(f"\n🎉 Successfully added {total_fields_added} comprehensive fields!")
        print("🔄 Running final verification...")

        try:
            result = subprocess.run(
                ["python3", "development-tools/smart_field_gap_analysis.py"],
                capture_output=True,
                text=True,
                cwd="/workspaces/ssh-git-github.com-odoo-odoo.git-18.0",
            )
            if result.returncode == 0:
                remaining_gaps = result.stdout.count("🚨")
                original_gaps = 140  # From previous run

                print(f"📉 Field gaps reduced: {original_gaps} → {remaining_gaps}")

                if remaining_gaps == 0:
                    print("🎉 ALL FIELD GAPS RESOLVED! 100% COMPLETION ACHIEVED!")
                elif remaining_gaps < original_gaps:
                    reduction = original_gaps - remaining_gaps
                    print(f"🔥 Significant progress: {reduction} gaps resolved!")
                else:
                    print("🔄 Continue systematic completion...")
            else:
                print("⚠️  Could not run final verification")
        except:
            print("⚠️  Could not run final verification")


if __name__ == "__main__":
    main()
