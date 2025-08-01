#!/usr/bin/env python3
"""
Comprehensive Field Label Conflict Fixer
Fixes ALL remaining "Responsible User" conflicts systematically
"""

import os
import re
import sys


def fix_all_responsible_user_conflicts():
    """Fix all remaining 'Responsible User' field conflicts"""

    models_dir = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )

    # Models that still have conflicts based on the error log
    conflicted_models = [
        "customer_rate_profile.py",
        "records_retention_policy.py",
        "container_contents.py",
        "records_document.py",
        "records_container_movement.py",
        "temp_inventory.py",
        "pickup_route.py",
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

    for filename in conflicted_models:
        filepath = os.path.join(models_dir, filename)

        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filename}")
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Multiple patterns to catch different user_id field formats
            patterns = [
                (
                    r'user_id\s*=\s*fields\.Many2one\(\s*["\']res\.users["\'],\s*string=["\']Responsible User["\']([^)]*)\)',
                    r'user_id = fields.Many2one("res.users", string="Assigned User"\1)',
                ),
                (
                    r'user_id\s*=\s*fields\.Many2one\(\s*["\']res\.users["\'],\s*([^,]*,\s*)*string=["\']Responsible User["\']',
                    lambda m: m.group(0).replace(
                        'string="Responsible User"', 'string="Assigned User"'
                    ),
                ),
                (
                    r'(["\']res\.users["\'],\s*string=["\'])Responsible User(["\'])',
                    r"\1Assigned User\2",
                ),
            ]

            content_modified = False
            for pattern, replacement in patterns:
                if re.search(pattern, content):
                    if callable(replacement):
                        content = re.sub(pattern, replacement, content)
                    else:
                        content = re.sub(pattern, replacement, content)
                    content_modified = True

            if content_modified:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

                fixes_applied += 1
                print(f"✅ Fixed user_id label conflict in: {filename}")
            else:
                print(f"ℹ️  No 'Responsible User' conflicts found in: {filename}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    return fixes_applied


def scan_all_models_for_conflicts():
    """Scan all model files for any remaining 'Responsible User' labels"""

    models_dir = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )
    remaining_conflicts = []

    for filename in os.listdir(models_dir):
        if not filename.endswith(".py") or filename == "__init__.py":
            continue

        filepath = os.path.join(models_dir, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if 'string="Responsible User"' in content:
                remaining_conflicts.append(filename)

        except Exception as e:
            print(f"❌ Error scanning {filename}: {e}")

    return remaining_conflicts


if __name__ == "__main__":
    print("🔧 COMPREHENSIVE FIELD LABEL CONFLICT FIXER")
    print("=" * 60)

    # First pass: Fix known conflicts
    print("\n📋 Fixing known conflicted models...")
    fixes_applied = fix_all_responsible_user_conflicts()

    # Second pass: Scan for any remaining conflicts
    print("\n🔍 Scanning for remaining conflicts...")
    remaining = scan_all_models_for_conflicts()

    if remaining:
        print(f"\n⚠️  Found {len(remaining)} files with remaining conflicts:")
        for filename in remaining:
            print(f"   - {filename}")

        # Fix any remaining conflicts
        print("\n🔧 Fixing remaining conflicts...")
        for filename in remaining:
            filepath = os.path.join(
                "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models",
                filename,
            )
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                content = content.replace(
                    'string="Responsible User"', 'string="Assigned User"'
                )

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

                fixes_applied += 1
                print(f"✅ Fixed remaining conflicts in: {filename}")

            except Exception as e:
                print(f"❌ Error fixing {filename}: {e}")

    print("\n" + "=" * 60)
    print(f"🎉 FIELD LABEL CONFLICT RESOLUTION COMPLETE!")
    print(f"📊 Total fixes applied: {fixes_applied}")

    # Final verification
    final_scan = scan_all_models_for_conflicts()
    if final_scan:
        print(f"❌ WARNING: {len(final_scan)} files still have conflicts!")
        for f in final_scan:
            print(f"   - {f}")
    else:
        print("✅ SUCCESS: No remaining 'Responsible User' conflicts found!")
        print("\n💡 Next: Commit changes and push to trigger Odoo.sh rebuild")
