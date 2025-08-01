#!/usr/bin/env python3
"""
Fix Field Label Conflicts
Resolves duplicate field labels by updating user_id field labels
"""

import os
import re
import sys


def fix_user_id_labels():
    """Fix user_id field labels to avoid conflicts with activity_user_id"""

    models_dir = (
        "/workspaces/ssh-git-github.com-odoo-odoo-git-18.0/records_management/models"
    )

    # Files that need user_id label updates
    files_to_fix = [
        "customer_rate_profile.py",
        "records_document_type.py",
        "records_retention_policy.py",
        "container_contents.py",
        "records_document.py",
        "records_container_movement.py",
        "temp_inventory.py",
        "pickup_route.py",
        "records_vehicle.py",
        "shredding_service.py",
        "shredding_service_log.py",
        "destruction_item.py",
        "document_retrieval_work_order.py",
        "file_retrieval_work_order.py",
        "customer_retrieval_rates.py",
        "bin_key_management.py",
        "bin_unlock_service.py",
        "paper_bale_recycling.py",
        "paper_load_shipment.py",
        "load.py",
        "naid_certificate.py",
        "records_chain_of_custody.py",
        "portal_request.py",
        "portal_feedback.py",
        "survey_improvement_action.py",
        "transitory_items.py",
        "transitory_field_config.py",
        "field_label_customization.py",
        "res_partner_key_restriction.py",
        "installer.py",
    ]

    fixes_applied = 0

    for filename in files_to_fix:
        filepath = os.path.join(models_dir, filename)

        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filename}")
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Pattern to match user_id field with "Responsible User" label
            pattern = r'user_id\s*=\s*fields\.Many2one\(\s*["\']res\.users["\'],\s*string=["\']Responsible User["\']'
            replacement = (
                'user_id = fields.Many2one("res.users", string="Assigned User"'
            )

            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

                fixes_applied += 1
                print(f"✅ Fixed user_id label in: {filename}")
            else:
                print(f"ℹ️  No conflicts found in: {filename}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    print(f"\n🎯 Total fixes applied: {fixes_applied}")
    return fixes_applied


def fix_special_cases():
    """Fix special field conflicts"""
    fixes = 0

    # Fix naid_destruction_record.py - responsible_user_id vs activity_user_id
    naid_file = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/naid_destruction_record.py"
    if os.path.exists(naid_file):
        try:
            with open(naid_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Update responsible_user_id label
            pattern = r'responsible_user_id\s*=\s*fields\.Many2one\([^)]+string=["\']Responsible User["\']'
            if re.search(pattern, content):
                content = re.sub(
                    r'(responsible_user_id\s*=\s*fields\.Many2one\([^)]+string=)["\']Responsible User["\']',
                    r'\1"Destruction Manager"',
                    content,
                )

                with open(naid_file, "w", encoding="utf-8") as f:
                    f.write(content)

                fixes += 1
                print(
                    f"✅ Fixed responsible_user_id label in: naid_destruction_record.py"
                )
        except Exception as e:
            print(f"❌ Error fixing naid_destruction_record.py: {e}")

    return fixes


if __name__ == "__main__":
    print("🔧 Fixing Field Label Conflicts...")
    print("=" * 50)

    user_fixes = fix_user_id_labels()
    special_fixes = fix_special_cases()

    total_fixes = user_fixes + special_fixes

    print("\n" + "=" * 50)
    print(f"🎉 Field label conflict fixes complete!")
    print(f"📊 Total fixes applied: {total_fixes}")

    if total_fixes > 0:
        print("\n✅ All field label conflicts should now be resolved.")
        print("💡 Recommendation: Commit and push changes to trigger Odoo.sh rebuild.")
    else:
        print("\nℹ️  No field label conflicts found to fix.")
