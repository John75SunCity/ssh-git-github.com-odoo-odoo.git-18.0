#!/usr/bin/env python3
"""
Analyze Mass Fix Damage - Identify what the mass fix broke
Compare working files (before) vs broken files (after) to find corruption patterns
"""

import os
import difflib
from pathlib import Path

def analyze_mass_fix_damage():
    """Analyze what files the mass fix broke by comparing with backups"""

    # Files that worked BEFORE mass fix but are broken AFTER
    broken_files = [
        "views/permanent_flag_wizard_views.xml",
        "views/pickup_schedule_wizard_views.xml",
        "views/processing_log_resolution_wizard_views.xml",
        "views/rate_change_confirmation_wizard_views.xml",
        "views/records_container_type_converter_wizard_views.xml",
        "views/records_document_flag_permanent_wizard_views.xml",
        "views/records_location_report_wizard_views.xml",
        "views/records_permanent_flag_wizard_views.xml",
        "views/records_user_invitation_wizard_views.xml",
        "views/shredding_bin_barcode_wizard_views.xml",
        "views/system_flowchart_wizard_views.xml",
        "views/temp_inventory_reject_wizard_views.xml",
        "views/visitor_pos_wizard_views.xml",
        "views/work_order_bin_assignment_wizard_views.xml",
        "views/advanced_billing_contact_views.xml",
        "views/advanced_billing_profile_views.xml",
        "views/approval_history_views.xml",
        "views/base_rates_views.xml",
        "views/billing_period_views.xml",
        "views/bin_barcode_inventory_views.xml",
        "views/chain_of_custody_views.xml",
        "views/container_retrieval_views.xml",
        "views/custody_transfer_event_views.xml",
        "views/customer_feedback_views.xml",
        "views/customer_inventory_report_views.xml",
        "views/customer_negotiated_rate_views.xml",
        "views/destruction_event_views.xml",
        "views/destruction_certificate_views.xml",
        "views/records_work_vehicle_views.xml",
        "views/inventory_adjustment_reason_views.xml",
        "views/inventory_item_destruction_views.xml",
        "views/inventory_item_location_transfer_views.xml",
        "views/inventory_item_profile_views.xml",
        "views/inventory_item_retrieval_views.xml",
        "views/inventory_item_type_views.xml",
        "views/location_group_views.xml",
        "views/maintenance_request_views.xml",
        "views/naid_certificate_views.xml",
        "views/paper_bale_inspection_views.xml",
        "views/paper_bale_line_views.xml",
        "views/paper_bale_movement_views.xml",
        "views/paper_bale_recycling_views.xml",
        "views/paper_bale_views.xml",
        "views/paper_load_shipment_views.xml",
        "views/paper_model_bale_views.xml",
        "views/payment_split_views.xml",
        "views/pickup_route_views.xml",
        "views/portal_feedback_views.xml",
        "views/portal_request_line_views.xml",
        "views/records_approval_workflow_views.xml",
        "views/records_audit_log_views.xml",
        "views/records_bulk_user_import_views.xml",
        "views/records_category_views.xml"
    ]

    base_path = Path("records_management")
    backup_path = Path("backup/views_backup_20250913")
    corruptions_found = []

    print("🔍 ANALYZING MASS FIX DAMAGE")
    print("=" * 50)

    for file_path in broken_files:
        current_file = base_path / file_path
        # Find backup file with .backup_20250913_* pattern
        backup_filename = file_path.replace("views/", "") + ".backup_20250913_231913"
        backup_file = backup_path / backup_filename

        # Try alternative backup pattern if not found
        if not backup_file.exists():
            backup_filename = file_path.replace("views/", "") + ".backup_20250913_231851"
            backup_file = backup_path / backup_filename

        if current_file.exists() and backup_file.exists():
            try:
                with open(current_file, 'r', encoding='utf-8') as f:
                    current_content = f.readlines()
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_content = f.readlines()

                # Find differences
                diff = list(difflib.unified_diff(
                    backup_content,
                    current_content,
                    fromfile=f"BACKUP/{file_path}",
                    tofile=f"CURRENT/{file_path}",
                    n=3
                ))

                if diff:
                    print(f"\n📄 CORRUPTION FOUND: {file_path}")
                    print("-" * 40)

                    # Analyze common corruption patterns
                    corruption_patterns = []

                    for line in diff:
                        if line.startswith('-') and not line.startswith('---'):
                            original = line[1:].strip()
                        elif line.startswith('+') and not line.startswith('+++'):
                            corrupted = line[1:].strip()

                            # Check for common mass fix corruptions
                            if 'document_id' in original and 'document_ids' in corrupted:
                                corruption_patterns.append("Field name corrupted: document_id → document_ids")
                            elif 'invisible=' in original and 'invisible=' in corrupted:
                                corruption_patterns.append("Invisible attribute syntax changed")
                            elif '"' in original and '"' not in corrupted:
                                corruption_patterns.append("Missing quotes")
                            elif original != corrupted:
                                corruption_patterns.append(f"Line changed: {original[:50]}... → {corrupted[:50]}...")

                    for pattern in set(corruption_patterns):
                        print(f"  ⚠️  {pattern}")

                    corruptions_found.append({
                        'file': file_path,
                        'patterns': corruption_patterns,
                        'diff_lines': len([l for l in diff if l.startswith(('+', '-'))])
                    })

            except Exception as e:
                print(f"❌ Error analyzing {file_path}: {e}")
        else:
            if not current_file.exists():
                print(f"❌ MISSING: {file_path} (current file not found)")
            if not backup_file.exists():
                print(f"❌ MISSING: {file_path} (backup file not found)")

    print(f"\n📊 SUMMARY")
    print("=" * 50)
    print(f"Total files analyzed: {len(broken_files)}")
    print(f"Files with corruptions: {len(corruptions_found)}")

    if corruptions_found:
        print(f"\n🛠️  CORRUPTION PATTERNS FOUND:")
        all_patterns = []
        for corruption in corruptions_found:
            all_patterns.extend(corruption['patterns'])

        pattern_counts = {}
        for pattern in all_patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {count:2d}x {pattern}")

    return corruptions_found

if __name__ == "__main__":
    corruptions = analyze_mass_fix_damage()

    if corruptions:
        print(f"\n🎯 NEXT STEPS:")
        print("1. Create surgical repair script for identified patterns")
        print("2. Apply fixes only to corrupted parts")
        print("3. Preserve all good changes from mass fix")
        print("4. Test deployment after surgical repair")
    else:
        print("✅ No corruptions found - files may need different analysis")
