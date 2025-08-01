#!/usr/bin/env python3
"""
Fix all create methods to use @api.model_create_multi decorator
"""

import os
import re


def fix_create_methods():
    """Fix all create methods that don't handle lists properly"""

    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"

    print("🔧 FIXING CREATE METHODS")
    print("=" * 40)

    # Files that need fixing based on grep results
    files_to_fix = [
        "models/bin_unlock_service.py",
        "models/bin_key_management.py",
        "models/records_vehicle.py",
        "models/naid_certificate.py",
        "models/pickup_route.py",
        "models/records_document_type.py",
        "models/customer_retrieval_rates.py",
        "models/records_tag.py",
        "models/file_retrieval_work_order.py",
        "models/load.py",
        "models/records_document.py",
        "models/temp_inventory.py",
        "models/portal_feedback.py",
        "models/pos_config.py",
        "models/records_retention_policy.py",
        "models/shredding_service.py",
        "models/portal_request.py",
        "models/container_contents.py",
        "models/destruction_item.py",
        "models/paper_bale_recycling.py",
        "models/paper_load_shipment.py",
    ]

    fixed_count = 0

    for file_path in files_to_fix:
        full_path = os.path.join(base_path, file_path)

        if os.path.exists(full_path):
            if fix_create_method_in_file(full_path):
                fixed_count += 1
                print(f"✅ Fixed: {file_path}")
            else:
                print(f"⚠️  Skipped: {file_path} (already correct or no create method)")
        else:
            print(f"❌ Not found: {file_path}")

    print(f"\n✅ FIXED {fixed_count} CREATE METHODS")


def fix_create_method_in_file(file_path):
    """Fix create method in a single file"""

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Pattern to match the old create method signature
        old_pattern = r'(\s+)def create\(self, vals\):\s*\n(\s+"""[^"]*"""\s*\n)?(\s+)(.*?return super\(\)\.create\(vals\))'

        # Check if file has the old pattern and needs fixing
        if re.search(old_pattern, content, re.DOTALL):
            # Replace with new pattern
            def replacement(match):
                indent = match.group(1)
                docstring = match.group(2) or ""
                body_indent = match.group(3)
                body_content = match.group(4)

                # Extract the logic inside the method (before return statement)
                body_lines = []
                for line in body_content.split("\n"):
                    if "return super()" not in line:
                        body_lines.append(line)

                new_method = f"""{indent}@api.model_create_multi
{indent}def create(self, vals_list):
{docstring}{body_indent}# Handle both single dict and list of dicts
{body_indent}if not isinstance(vals_list, list):
{body_indent}    vals_list = [vals_list]
{body_indent}
{body_indent}for vals in vals_list:
"""

                # Add the original logic for each vals
                for line in body_lines:
                    if line.strip():
                        new_method += f"{body_indent}    {line.strip()}\n"

                new_method += f"""
{body_indent}return super().create(vals_list)"""

                return new_method

            new_content = re.sub(old_pattern, replacement, content, flags=re.DOTALL)

            # Also ensure @api import is present
            if (
                "@api.model_create_multi" in new_content
                and "from odoo import" in new_content
            ):
                # Check if api is already imported
                if ", api" not in new_content and "import api" not in new_content:
                    new_content = re.sub(
                        r"(from odoo import [^,\n]*)", r"\1, api", new_content
                    )

            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return True

        return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


if __name__ == "__main__":
    fix_create_methods()
