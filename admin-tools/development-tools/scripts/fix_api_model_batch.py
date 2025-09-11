#!/usr/bin/env python3
"""
Batch fix @api.model to @api.model_create_multi for Odoo 18.0 compatibility
"""
import os
import re
import glob


def fix_api_model_decorators():
    """Fix @api.model decorators to @api.model_create_multi for create methods"""

    # List of models that need fixing based on the error log
    models_to_fix = [
        "records_location.py",
        "records_retention_policy.py",
        "records_container.py",
        "shredding_service.py",
        "paper_load_shipment.py",
        "paper_bale.py",
        "load.py",
        "naid_compliance.py",
        "portal_request.py",
        "field_label_customization.py",
        "fsm_task.py",
        "barcode_product.py",
    ]

    base_path = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/"
    )

    for model_file in models_to_fix:
        file_path = os.path.join(base_path, model_file)

        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {file_path}")
            continue

        print(f"🔧 Processing: {model_file}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for @api.model decorated create methods
        pattern = r"(@api\.model\s*\n\s*def\s+create\s*\()"

        if re.search(pattern, content):
            # Replace @api.model with @api.model_create_multi for create methods
            new_content = re.sub(
                pattern, r"@api.model_create_multi\n    def create(", content
            )

            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"✅ Fixed @api.model in: {model_file}")
            else:
                print(f"ℹ️  No changes needed in: {model_file}")
        else:
            print(f"ℹ️  No @api.model create method found in: {model_file}")


if __name__ == "__main__":
    print("🚀 Starting batch @api.model fix...")
    fix_api_model_decorators()
    print("✅ Batch fix completed!")
