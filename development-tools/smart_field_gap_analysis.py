#!/usr/bin/env python3
"""
Smart Field Gap Analysis
Identifies real view-model mismatches that would cause runtime errors
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
import re


def analyze_view_model_gaps():
    """Find real gaps between views and models"""

    print("🔍 SMART FIELD GAP ANALYSIS")
    print("=" * 60)

    models_dir = Path("records_management/models")
    views_dir = Path("records_management/views")

    # Load model field definitions
    model_fields = {}

    print("📄 Step 1: Scanning model files...")
    for model_file in models_dir.glob("*.py"):
        try:
            with open(model_file, "r") as f:
                content = f.read()

                # Extract model name
                model_match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', content)
                if model_match:
                    model_name = model_match.group(1)

                    # Extract field definitions
                    field_matches = re.findall(r"(\w+)\s*=\s*fields\.", content)
                    model_fields[model_name] = set(field_matches)

                    print(f"   ✓ {model_name}: {len(field_matches)} fields")
        except Exception as e:
            print(f"   ❌ Error reading {model_file.name}: {e}")

    print(
        f"\n📊 Found {len(model_fields)} models with {sum(len(fields) for fields in model_fields.values())} total fields"
    )

    # Analyze view files for field references
    print(f"\n📄 Step 2: Scanning view files...")
    critical_gaps = {}

    for view_file in views_dir.glob("*.xml"):
        try:
            # Parse XML to find field references
            tree = ET.parse(view_file)
            root = tree.getroot()

            # Find model references and field usage
            for record in root.findall(".//record[@model='ir.ui.view']"):
                model_field = record.find(".//field[@name='model']")
                arch_field = record.find(".//field[@name='arch']")

                if model_field is not None and arch_field is not None:
                    model_name = model_field.text

                    if model_name in model_fields:
                        # Find field references in arch
                        arch_content = ET.tostring(arch_field, encoding="unicode")
                        field_refs = re.findall(
                            r'field\s+name=["\']([^"\']+)["\']', arch_content
                        )

                        # Check for missing fields
                        missing_fields = []
                        for field_ref in field_refs:
                            if field_ref not in model_fields[model_name]:
                                # Skip known Odoo framework fields
                                if field_ref not in {
                                    "id",
                                    "create_date",
                                    "write_date",
                                    "create_uid",
                                    "write_uid",
                                    "__last_update",
                                }:
                                    missing_fields.append(field_ref)

                        if missing_fields:
                            if model_name not in critical_gaps:
                                critical_gaps[model_name] = set()
                            critical_gaps[model_name].update(missing_fields)

                            print(
                                f"   🚨 {view_file.name} -> {model_name}: {len(missing_fields)} missing fields"
                            )

        except Exception as e:
            print(f"   ❌ Error parsing {view_file.name}: {e}")

    # Report critical gaps
    print(f"\n🎯 CRITICAL GAPS ANALYSIS")
    print("=" * 60)

    if not critical_gaps:
        print("✅ No critical gaps found! All views match their models.")
        return {}

    total_missing = sum(len(fields) for fields in critical_gaps.values())
    print(f"Found {total_missing} missing fields across {len(critical_gaps)} models")

    # Sort by severity
    for model_name, missing_fields in sorted(
        critical_gaps.items(), key=lambda x: len(x[1]), reverse=True
    ):
        print(f"\n📋 {model_name} ({len(missing_fields)} missing fields):")

        # Categorize missing fields
        framework_fields = []
        business_fields = []

        for field in sorted(missing_fields):
            if any(
                pattern in field
                for pattern in ["activity_", "message_", "follower", "attachment"]
            ):
                framework_fields.append(field)
            elif any(
                pattern in field
                for pattern in ["arch", "model", "view_", "domain", "context"]
            ):
                continue  # Skip view-only fields
            else:
                business_fields.append(field)

        if framework_fields:
            print(f"   🔄 Framework (inherit): {', '.join(framework_fields[:5])}")
            if len(framework_fields) > 5:
                print(f"      ... and {len(framework_fields) - 5} more")

        if business_fields:
            print(f"   ✅ Business (add): {', '.join(business_fields[:5])}")
            if len(business_fields) > 5:
                print(f"      ... and {len(business_fields) - 5} more")

    return critical_gaps


def generate_field_fixes(critical_gaps):
    """Generate field addition code for critical gaps"""

    if not critical_gaps:
        return

    print(f"\n🔧 FIELD ADDITION RECOMMENDATIONS")
    print("=" * 60)

    # Focus on models with the most business fields
    for model_name, missing_fields in list(critical_gaps.items())[:3]:  # Top 3 models

        # Filter to business fields only
        business_fields = [
            field
            for field in missing_fields
            if not any(
                pattern in field
                for pattern in [
                    "activity_",
                    "message_",
                    "follower",
                    "attachment",
                    "arch",
                    "model",
                    "view_",
                    "domain",
                    "context",
                    "help",
                ]
            )
        ]

        if business_fields:
            print(f"\n📝 {model_name}:")
            print(f"   # Add these {len(business_fields)} fields:")

            for field in sorted(business_fields):
                field_type = suggest_field_type(field)
                print(f"   {field} = {field_type}")


def suggest_field_type(field_name):
    """Suggest appropriate field type based on naming patterns"""

    if field_name.endswith("_id"):
        return "fields.Many2one('res.partner', string='Related Record')"
    elif field_name.endswith("_ids"):
        return "fields.One2many('related.model', 'inverse_field', string='Related Records')"
    elif "date" in field_name or "time" in field_name:
        return "fields.Datetime(string='Date Time')"
    elif "amount" in field_name or "price" in field_name or "cost" in field_name:
        return "fields.Monetary(string='Amount', currency_field='currency_id')"
    elif "email" in field_name:
        return "fields.Char(string='Email Address')"
    elif "phone" in field_name:
        return "fields.Char(string='Phone Number')"
    elif "notes" in field_name or "description" in field_name:
        return "fields.Text(string='Notes')"
    elif any(word in field_name for word in ["required", "active", "is_", "has_"]):
        return "fields.Boolean(string='Flag', default=False)"
    else:
        return "fields.Char(string='Field')"


if __name__ == "__main__":
    try:
        critical_gaps = analyze_view_model_gaps()
        generate_field_fixes(critical_gaps)

        print(f"\n🚀 NEXT STEPS:")
        print("1. Review recommendations above")
        print("2. Add critical business fields to models")
        print("3. Test with targeted deployment")
        print("4. Fix any remaining runtime errors")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")
