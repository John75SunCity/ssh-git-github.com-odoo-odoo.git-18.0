#!/usr/bin/env python3
"""
SPECIFIC FIELD COMPLETION FROM RECOMMENDATIONS
==============================================

This script adds the exact fields recommended by the gap analysis.
"""

import os
import re
import subprocess
from pathlib import Path


def add_specific_recommended_fields():
    """Add the specific fields recommended by the gap analysis."""

    # These are the exact field recommendations from the gap analysis
    field_recommendations = {
        "visitor.pos.wizard": [
            ("compliance_officer", "fields.Char(string='Compliance Officer')"),
            (
                "digitization_format",
                "fields.Selection([('pdf', 'PDF'), ('image', 'Image'), ('text', 'Text')], string='Digitization Format')",
            ),
            ("document_count", "fields.Integer(string='Document Count', default=0)"),
            ("document_name", "fields.Char(string='Document Name')"),
            (
                "integration_error_ids",
                "fields.One2many('integration.error', 'pos_wizard_id', string='Integration Errors')",
            ),
            (
                "payment_split_ids",
                "fields.One2many('payment.split', 'pos_wizard_id', string='Payment Splits')",
            ),
            ("payment_terms", "fields.Char(string='Payment Terms')"),
            (
                "processing_log_ids",
                "fields.One2many('processing.log', 'pos_wizard_id', string='Processing Logs')",
            ),
            (
                "required_document_ids",
                "fields.One2many('required.document', 'pos_wizard_id', string='Required Documents')",
            ),
            (
                "service_item_ids",
                "fields.One2many('service.item', 'pos_wizard_id', string='Service Items')",
            ),
            (
                "shredding_type",
                "fields.Selection([('onsite', 'On-site'), ('offsite', 'Off-site'), ('witnessed', 'Witnessed')], string='Shredding Type')",
            ),
            ("step_name", "fields.Char(string='Step Name')"),
            (
                "total_discount",
                "fields.Monetary(string='Total Discount', currency_field='currency_id')",
            ),
        ]
    }

    base_dir = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )
    models_dir = base_dir / "models"

    total_fields_added = 0

    print("🎯 ADDING SPECIFIC RECOMMENDED FIELDS")
    print("=" * 50)

    for model_name, field_defs in field_recommendations.items():
        print(f"\n📝 {model_name} ({len(field_defs)} specific fields)")

        # Find model file
        model_file_name = model_name.replace(".", "_") + ".py"
        model_file = models_dir / model_file_name

        if not model_file.exists():
            print(f"      ⚠️  Model file not found: {model_file_name}")
            continue

        # Read current content
        try:
            with open(model_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check which fields already exist
            existing_fields = set()
            for line in content.split("\n"):
                if re.match(r"\\s*\\w+\\s*=\\s*fields\\.", line):
                    field_name = line.split("=")[0].strip()
                    existing_fields.add(field_name)

            # Filter out existing fields
            new_fields = [
                (name, definition)
                for name, definition in field_defs
                if name not in existing_fields
            ]

            if not new_fields:
                print(f"      ℹ️  All fields already exist")
                continue

            # Find insertion point
            field_pattern = r"(\\s+\\w+\\s*=\\s*fields\\..*?)(?=\\n\\s*(?:def|\\s*#|\\s*@|\\s*$|class))"
            field_matches = list(re.finditer(field_pattern, content, re.DOTALL))

            if field_matches:
                insert_pos = field_matches[-1].end()
            else:
                # Insert after class definition
                class_match = re.search(r"class\\s+\\w+\\(.*?\\):\\s*\\n", content)
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
                            while (
                                insert_pos < len(content)
                                and content[insert_pos] != "\\n"
                            ):
                                insert_pos += 1
                            insert_pos += 1
                else:
                    print(f"      ❌ Could not find insertion point")
                    continue

            # Generate field additions
            additions = []
            additions.append("\\n    # === SPECIFIC RECOMMENDED FIELDS ===")

            for field_name, field_definition in new_fields:
                additions.append(f"    {field_name} = {field_definition}")

            additions.append("")

            # Insert fields
            new_content = (
                content[:insert_pos] + "\\n".join(additions) + content[insert_pos:]
            )

            with open(model_file, "w", encoding="utf-8") as f:
                f.write(new_content)

            # Check syntax
            result = subprocess.run(
                ["python3", "-m", "py_compile", model_file],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                print(f"      ✅ Added {len(new_fields)} specific fields")
                total_fields_added += len(new_fields)

                # Show added fields
                field_names = [name for name, _ in new_fields]
                field_preview = ", ".join(field_names[:3])
                if len(field_names) > 3:
                    field_preview += f" (and {len(field_names) - 3} more)"
                print(f"         Fields: {field_preview}")
            else:
                print(f"      ⚠️  Syntax error after adding fields")
                print(f"         {result.stderr[:150]}...")

        except Exception as e:
            print(f"      ❌ Error: {e}")

    print(f"\\n📊 Added {total_fields_added} specific recommended fields")
    return total_fields_added


def main():
    """Main execution."""
    fields_added = add_specific_recommended_fields()

    if fields_added > 0:
        print(f"\\n🔄 Running final gap analysis...")

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
                else:
                    print(f"🔥 Progress made with specific field additions!")
            else:
                print("⚠️  Could not run final verification")
        except:
            print("⚠️  Could not run final verification")


if __name__ == "__main__":
    main()
