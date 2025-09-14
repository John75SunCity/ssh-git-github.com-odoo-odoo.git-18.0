#!/usr/bin/env python3
"""
Restore Working Files - Restore only files that used to work but are now broken
"""

import os
import shutil
from pathlib import Path

def restore_working_files():
    """Restore files that were working before mass fix but are broken now"""

    backup_path = Path("backup/views_backup_20250913")
    target_path = Path("records_management/views")

    # Files that were definitely working before but are broken now
    # Based on the manifest loading order
    broken_files = [
        "permanent_flag_wizard_views.xml",
        "pickup_schedule_wizard_views.xml",
        "processing_log_resolution_wizard_views.xml",
        "rate_change_confirmation_wizard_views.xml",
        "records_container_type_converter_wizard_views.xml",
        "records_document_flag_permanent_wizard_views.xml",
        "records_location_report_wizard_views.xml",
        "records_permanent_flag_wizard_views.xml",
        "records_user_invitation_wizard_views.xml",
        "shredding_bin_barcode_wizard_views.xml",
        "system_flowchart_wizard_views.xml",
        "temp_inventory_reject_wizard_views.xml",
        "visitor_pos_wizard_views.xml",
        "work_order_bin_assignment_wizard_views.xml",
        "advanced_billing_contact_views.xml",
        "advanced_billing_profile_views.xml",
        "approval_history_views.xml",
        "base_rates_views.xml",
        "billing_period_views.xml",
        "bin_barcode_inventory_views.xml",
        "chain_of_custody_views.xml",
        "container_retrieval_views.xml",
        "custody_transfer_event_views.xml",
        "customer_feedback_views.xml",
        "customer_inventory_report_views.xml",
        "customer_negotiated_rate_views.xml",
        "destruction_event_views.xml",
        "destruction_certificate_views.xml",
        "records_work_vehicle_views.xml",
        "inventory_adjustment_reason_views.xml",
        "inventory_item_destruction_views.xml",
        "inventory_item_location_transfer_views.xml",
        "inventory_item_profile_views.xml",
        "inventory_item_retrieval_views.xml",
        "inventory_item_type_views.xml",
        "location_group_views.xml",
        "naid_certificate_views.xml",
        "paper_bale_inspection_views.xml",
        "paper_bale_line_views.xml",
        "paper_bale_movement_views.xml",
        "paper_bale_recycling_views.xml",
        "paper_bale_views.xml",
        "paper_load_shipment_views.xml",
        "paper_model_bale_views.xml",
        "payment_split_views.xml",
        "pickup_route_views.xml",
        "portal_feedback_views.xml",
        "portal_request_line_views.xml",
        "records_approval_workflow_views.xml",
        "records_audit_log_views.xml",
        "records_bulk_user_import_views.xml",
        "records_category_views.xml"
    ]

    restored_files = []
    skipped_files = []

    print("🔄 RESTORING WORKING FILES FROM BACKUP")
    print("=" * 50)
    print("Restoring files that were working before mass fix...")

    for filename in broken_files:
        # Try different backup filename patterns
        backup_patterns = [
            f"{filename}.backup_20250913_231913",
            f"{filename}.backup_20250913_231851"
        ]

        backup_file = None
        for pattern in backup_patterns:
            candidate = backup_path / pattern
            if candidate.exists():
                backup_file = candidate
                break

        target_file = target_path / filename

        if backup_file and backup_file.exists():
            try:
                # Backup current file before restoring
                if target_file.exists():
                    backup_current = target_file.with_suffix(f"{target_file.suffix}.broken_backup")
                    shutil.copy2(target_file, backup_current)

                # Restore working version
                shutil.copy2(backup_file, target_file)
                restored_files.append(filename)
                print(f"  ✅ Restored: {filename}")

            except Exception as e:
                print(f"  ❌ Error restoring {filename}: {e}")
                skipped_files.append(filename)
        else:
            print(f"  ⚠️  No backup found: {filename}")
            skipped_files.append(filename)

    print(f"\n📊 RESTORATION SUMMARY")
    print("=" * 50)
    print(f"Files restored: {len(restored_files)}")
    print(f"Files skipped: {len(skipped_files)}")

    if restored_files:
        print(f"\n✅ Successfully restored {len(restored_files)} working files")
        print("These files should now work as they did before the mass fix")

    if skipped_files:
        print(f"\n⚠️  Could not restore {len(skipped_files)} files - backups not found")

    return restored_files, skipped_files

if __name__ == "__main__":
    restored, skipped = restore_working_files()

    if restored:
        print(f"\n🎯 NEXT STEPS:")
        print("1. Test module loading with restored files")
        print("2. Commit working state")
        print("3. Deploy to verify fixes")
        print("\n🔧 Note: Current broken files backed up with .broken_backup extension")
    else:
        print("\n❌ No files were restored - may need alternative approach")
