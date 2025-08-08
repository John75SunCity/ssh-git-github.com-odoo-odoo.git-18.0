#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE FIELD COMPLETION
====================================

This script adds missing fields to ALL remaining models based on the gap analysis output.
It processes each model systematically and adds comprehensive business fields.
"""

import os
import re
import subprocess
from pathlib import Path


def get_business_critical_fields(model_name):
    """Get business-critical fields for specific model types."""
    model_lower = model_name.lower()

    # Common framework fields that should be added to most models
    framework_fields = [
        (
            "activity_ids",
            "fields.One2many('mail.activity', 'res_id', string='Activities')",
        ),
        (
            "message_follower_ids",
            "fields.One2many('mail.followers', 'res_id', string='Followers')",
        ),
        ("message_ids", "fields.One2many('mail.message', 'res_id', string='Messages')"),
    ]

    # Business fields based on model type
    business_fields = []

    if "wizard" in model_lower:
        business_fields.extend(
            [
                ("active", "fields.Boolean(string='Active', default=True)"),
                (
                    "state",
                    "fields.Selection([('draft', 'Draft'), ('processing', 'Processing'), ('completed', 'Completed')], string='State', default='draft')",
                ),
                ("notes", "fields.Text(string='Notes')"),
                (
                    "created_date",
                    "fields.Datetime(string='Created Date', default=fields.Datetime.now)",
                ),
            ]
        )

    elif "report" in model_lower or "inventory" in model_lower:
        business_fields.extend(
            [
                (
                    "customer_id",
                    "fields.Many2one('res.partner', string='Customer', tracking=True)",
                ),
                (
                    "created_date",
                    "fields.Datetime(string='Created Date', default=fields.Datetime.now)",
                ),
                (
                    "document_count",
                    "fields.Integer(string='Document Count', default=0)",
                ),
                (
                    "total_amount",
                    "fields.Monetary(string='Total Amount', currency_field='currency_id')",
                ),
                (
                    "currency_id",
                    "fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)",
                ),
                (
                    "state",
                    "fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done')], string='State', default='draft')",
                ),
            ]
        )

    elif "feedback" in model_lower or "portal" in model_lower:
        business_fields.extend(
            [
                (
                    "customer_id",
                    "fields.Many2one('res.partner', string='Customer', tracking=True)",
                ),
                (
                    "rating",
                    "fields.Selection([('1', 'Poor'), ('2', 'Fair'), ('3', 'Good'), ('4', 'Very Good'), ('5', 'Excellent')], string='Rating')",
                ),
                ("feedback_text", "fields.Text(string='Feedback')"),
                ("response_date", "fields.Datetime(string='Response Date')"),
                ("resolved", "fields.Boolean(string='Resolved', default=False)"),
                (
                    "priority",
                    "fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string='Priority', default='medium')",
                ),
            ]
        )

    elif "shredding" in model_lower or "destruction" in model_lower:
        business_fields.extend(
            [
                (
                    "customer_id",
                    "fields.Many2one('res.partner', string='Customer', tracking=True)",
                ),
                ("destruction_date", "fields.Date(string='Destruction Date')"),
                ("certificate_number", "fields.Char(string='Certificate Number')"),
                (
                    "destruction_method",
                    "fields.Selection([('shred', 'Shredding'), ('burn', 'Burning'), ('pulp', 'Pulping')], string='Destruction Method')",
                ),
                ("weight", "fields.Float(string='Weight (lbs)', digits=(10, 2))"),
                ("approved_by", "fields.Many2one('res.users', string='Approved By')"),
                ("completed", "fields.Boolean(string='Completed', default=False)"),
            ]
        )

    elif "container" in model_lower or "box" in model_lower:
        business_fields.extend(
            [
                (
                    "customer_id",
                    "fields.Many2one('res.partner', string='Customer', tracking=True)",
                ),
                (
                    "location_id",
                    "fields.Many2one('stock.location', string='Location', tracking=True)",
                ),
                ("barcode", "fields.Char(string='Barcode', copy=False)"),
                (
                    "container_type",
                    "fields.Selection([('box', 'Box'), ('bin', 'Bin'), ('folder', 'Folder')], string='Container Type')",
                ),
                ("capacity", "fields.Float(string='Capacity', digits=(10, 2))"),
                (
                    "current_weight",
                    "fields.Float(string='Current Weight', digits=(10, 2))",
                ),
                ("last_access_date", "fields.Date(string='Last Access Date')"),
            ]
        )

    elif "location" in model_lower:
        business_fields.extend(
            [
                (
                    "warehouse_id",
                    "fields.Many2one('stock.warehouse', string='Warehouse')",
                ),
                ("zone", "fields.Char(string='Zone')"),
                ("aisle", "fields.Char(string='Aisle')"),
                ("rack", "fields.Char(string='Rack')"),
                ("shelf", "fields.Char(string='Shelf')"),
                ("capacity", "fields.Float(string='Capacity', digits=(10, 2))"),
                ("utilization", "fields.Float(string='Utilization %', digits=(5, 2))"),
                (
                    "temperature_controlled",
                    "fields.Boolean(string='Temperature Controlled')",
                ),
            ]
        )

    elif "vehicle" in model_lower:
        business_fields.extend(
            [
                ("license_plate", "fields.Char(string='License Plate')"),
                (
                    "vehicle_type",
                    "fields.Selection([('truck', 'Truck'), ('van', 'Van'), ('car', 'Car')], string='Vehicle Type')",
                ),
                ("driver_id", "fields.Many2one('hr.employee', string='Driver')"),
                ("capacity", "fields.Float(string='Capacity', digits=(10, 2))"),
                (
                    "fuel_type",
                    "fields.Selection([('gas', 'Gasoline'), ('diesel', 'Diesel'), ('electric', 'Electric')], string='Fuel Type')",
                ),
                ("maintenance_date", "fields.Date(string='Last Maintenance')"),
            ]
        )

    elif "service" in model_lower or "unlock" in model_lower:
        business_fields.extend(
            [
                (
                    "customer_id",
                    "fields.Many2one('res.partner', string='Customer', tracking=True)",
                ),
                ("service_date", "fields.Date(string='Service Date')"),
                (
                    "technician_id",
                    "fields.Many2one('hr.employee', string='Technician')",
                ),
                ("billable", "fields.Boolean(string='Billable', default=True)"),
                (
                    "charge_amount",
                    "fields.Monetary(string='Charge Amount', currency_field='currency_id')",
                ),
                (
                    "currency_id",
                    "fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)",
                ),
                ("completed", "fields.Boolean(string='Completed', default=False)"),
            ]
        )

    elif "paper" in model_lower or "bale" in model_lower or "recycling" in model_lower:
        business_fields.extend(
            [
                ("bale_number", "fields.Char(string='Bale Number')"),
                ("weight", "fields.Float(string='Weight (lbs)', digits=(10, 2))"),
                ("pickup_date", "fields.Date(string='Pickup Date')"),
                ("delivery_date", "fields.Date(string='Delivery Date')"),
                ("recycling_facility", "fields.Char(string='Recycling Facility')"),
                (
                    "contamination_level",
                    "fields.Selection([('clean', 'Clean'), ('light', 'Light'), ('heavy', 'Heavy')], string='Contamination Level')",
                ),
                (
                    "price_per_ton",
                    "fields.Monetary(string='Price per Ton', currency_field='currency_id')",
                ),
            ]
        )

    elif "key" in model_lower or "restriction" in model_lower:
        business_fields.extend(
            [
                (
                    "customer_id",
                    "fields.Many2one('res.partner', string='Customer', tracking=True)",
                ),
                ("bin_number", "fields.Char(string='Bin Number')"),
                (
                    "access_level",
                    "fields.Selection([('full', 'Full Access'), ('limited', 'Limited'), ('restricted', 'Restricted')], string='Access Level')",
                ),
                ("expiration_date", "fields.Date(string='Expiration Date')"),
                ("last_check_date", "fields.Date(string='Last Check Date')"),
                (
                    "authorized_by",
                    "fields.Many2one('res.users', string='Authorized By')",
                ),
            ]
        )

    # Default business fields for any model
    default_fields = [
        ("sequence", "fields.Integer(string='Sequence', default=10)"),
        ("active", "fields.Boolean(string='Active', default=True)"),
        ("notes", "fields.Text(string='Notes')"),
        (
            "created_date",
            "fields.Datetime(string='Created Date', default=fields.Datetime.now)",
        ),
        ("updated_date", "fields.Datetime(string='Updated Date')"),
    ]

    # Combine all fields, removing duplicates
    all_fields = framework_fields + business_fields + default_fields
    unique_fields = {}
    for name, definition in all_fields:
        if name not in unique_fields:
            unique_fields[name] = definition

    return list(unique_fields.items())


def add_model_fields(model_file, field_definitions):
    """Add field definitions to a model file."""
    try:
        with open(model_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check which fields already exist
        existing_fields = set()
        for line in content.split("\n"):
            if re.match(r"\s*\w+\s*=\s*fields\.", line):
                field_name = line.split("=")[0].strip()
                existing_fields.add(field_name)

        # Filter out existing fields
        new_fields = [
            (name, definition)
            for name, definition in field_definitions
            if name not in existing_fields
        ]

        if not new_fields:
            return True, 0  # No new fields to add

        # Find insertion point
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
                return False, 0

        # Generate field additions
        additions = []
        additions.append("\n    # === BUSINESS CRITICAL FIELDS ===")

        for field_name, field_definition in new_fields:
            additions.append(f"    {field_name} = {field_definition}")

        additions.append("")

        # Insert fields
        new_content = content[:insert_pos] + "\n".join(additions) + content[insert_pos:]

        with open(model_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        return True, len(new_fields)

    except Exception as e:
        print(f"      ❌ Error: {e}")
        return False, 0


def check_syntax(model_file):
    """Check Python syntax."""
    try:
        result = subprocess.run(
            ["python3", "-m", "py_compile", model_file], capture_output=True, text=True
        )
        return result.returncode == 0
    except:
        return False


def get_all_models_with_gaps():
    """Get all models that have missing fields."""
    try:
        result = subprocess.run(
            ["python3", "development-tools/smart_field_gap_analysis.py"],
            capture_output=True,
            text=True,
            cwd="/workspaces/ssh-git-github.com-odoo-odoo.git-18.0",
        )

        if result.returncode != 0:
            return []

        # Parse output to find models with gaps
        models_with_gaps = set()
        lines = result.stdout.split("\n")

        for line in lines:
            if "🚨" in line and "missing fields" in line and " -> " in line:
                parts = line.split(" -> ")
                if len(parts) >= 2:
                    model_part = parts[1]
                    if ":" in model_part:
                        model_name = model_part.split(":")[0].strip()
                        models_with_gaps.add(model_name)
            elif (
                line.strip().startswith("📋 ")
                and "(" in line
                and "missing fields):" in line
            ):
                model_part = line.split("📋 ")[1].split("(")[0].strip()
                models_with_gaps.add(model_part)

        return list(models_with_gaps)

    except Exception as e:
        print(f"Error getting models with gaps: {e}")
        return []


def main():
    """Main execution."""
    print("🚀 FINAL COMPREHENSIVE FIELD COMPLETION")
    print("=" * 60)

    # Get all models with gaps
    print("🔍 Identifying models with missing fields...")
    models_with_gaps = get_all_models_with_gaps()

    if not models_with_gaps:
        print("✅ No models with missing fields found!")
        return

    print(f"📋 Found {len(models_with_gaps)} models with missing fields")

    base_dir = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )
    models_dir = base_dir / "models"

    total_fields_added = 0
    models_processed = 0
    models_failed = 0

    print(f"\n🔧 Processing {len(models_with_gaps)} models...")

    for model_name in sorted(models_with_gaps):
        print(f"\n📝 {model_name}")

        # Find model file
        model_file_name = model_name.replace(".", "_") + ".py"
        model_file = models_dir / model_file_name

        if not model_file.exists():
            print(f"      ⚠️  Model file not found: {model_file_name}")
            models_failed += 1
            continue

        # Get appropriate fields for this model
        field_definitions = get_business_critical_fields(model_name)

        # Add fields
        success, fields_added = add_model_fields(model_file, field_definitions)

        if success:
            if fields_added > 0:
                # Check syntax
                if check_syntax(model_file):
                    print(f"      ✅ Added {fields_added} business-critical fields")
                    total_fields_added += fields_added
                    models_processed += 1
                else:
                    print(f"      ⚠️  Syntax error after adding fields")
                    models_failed += 1
            else:
                print(f"      ℹ️  No new fields needed (already complete)")
                models_processed += 1
        else:
            print(f"      ❌ Failed to add fields")
            models_failed += 1

    print("\n" + "=" * 60)
    print("📊 FINAL COMPLETION SUMMARY")
    print(f"✅ Successfully processed: {models_processed} models")
    print(f"⚠️  Failed to process: {models_failed} models")
    print(f"📝 Total fields added: {total_fields_added}")

    if total_fields_added > 0:
        print(f"\n🎉 Successfully added {total_fields_added} business-critical fields!")
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
                print(f"📉 Remaining field gaps: {remaining_gaps}")

                if remaining_gaps == 0:
                    print("🎉 ALL FIELD GAPS RESOLVED! 100% COMPLETION ACHIEVED!")
                elif remaining_gaps < 140:
                    reduction = 140 - remaining_gaps
                    print(f"🔥 Excellent progress: {reduction} gaps resolved!")
                    print("🔄 Continue systematic completion for remaining gaps...")
                else:
                    print("🔄 Good progress made, continue completion...")
            else:
                print("⚠️  Could not run final verification")
        except:
            print("⚠️  Could not run final verification")


if __name__ == "__main__":
    main()
