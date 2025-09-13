#!/usr/bin/env python3
"""
Apply mass field fixes based on validation results
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def apply_field_fixes():
    """Apply automatic field fixes"""

    # Common field corrections that can be applied automatically
    field_corrections = {
        # Status to state is already handled
        'arch': None,  # Skip arch field issues - these are view structure issues

        # NOTE: Removed incorrect many2many mappings that were breaking the chain_of_custody model
        # document_ids and container_ids are CORRECT Many2many field names in chain.of.custody
        # DO NOT change them to document_id/container_id
    }    # Files to process (high priority ones)
    priority_files = [
        'records_management/views/chain_of_custody_views.xml',
        'records_management/views/customer_inventory_views.xml',
        'records_management/views/records_retrieval_order_views.xml',
    ]

    fixes_applied = 0

    for file_path in priority_files:
        if not os.path.exists(file_path):
            continue

        print(f"Processing: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Apply field name corrections
        for wrong_field, correct_field in field_corrections.items():
            if correct_field and wrong_field in content:
                # Only replace field name attributes, not other occurrences
                pattern = rf'<field[^>]*name=[\'"]({re.escape(wrong_field)})[\'"]'
                replacement = rf'<field name="{correct_field}"'

                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    fixes_applied += 1
                    print(f"  Fixed: {wrong_field} → {correct_field}")

        # Save if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Saved changes to {file_path}")

    print(f"\n✅ Applied {fixes_applied} automatic field fixes")
    return fixes_applied

if __name__ == "__main__":
    print("🔧 Applying mass field fixes...")
    fixes = apply_field_fixes()
    print(f"🎯 Total fixes applied: {fixes}")
