#!/usr/bin/env python3
"""
Script to fix Monetary fields missing currency_field parameter
"""

import os
import re
import glob


def fix_monetary_currency_field():
    """Fix Monetary fields missing currency_field parameter"""
    records_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    model_files = glob.glob(f"{records_path}/models/*.py")

    files_to_fix = [
        "bin_key_unlock_service.py",
        "unlock_service_history.py",
        "pickup_route.py",
        "bin_unlock_service.py",
        "customer_inventory_report_model.py",
        "records_department_billing_approval.py",
        "customer_negotiated_rate.py",
        "payment_split_line.py",
        "payment_split.py",
        "revenue_forecast.py",
        "records_deletion_request.py",
        "records_inventory_dashboard.py",
        "barcode_pricing_tier.py",
        "service_item.py",
    ]

    fixed_files = []

    for file_path in model_files:
        file_name = os.path.basename(file_path)
        if file_name not in files_to_fix:
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Check if currency_id field exists in the file
            if "currency_id" not in content:
                print(f"⚠️  Skipping {file_name}: No currency_id field found")
                continue

            # Pattern to match Monetary fields without currency_field
            # Look for fields.Monetary(...) without currency_field parameter
            pattern = r"(fields\.Monetary\([^)]*?)(\))"

            def fix_monetary_field(match):
                field_def = match.group(1)
                closing_paren = match.group(2)

                # Check if already has currency_field
                if "currency_field" in field_def:
                    return match.group(0)  # Return unchanged

                # Add currency_field parameter
                # If field_def ends with comma and space, add after it
                # Otherwise add with comma
                if field_def.rstrip().endswith(","):
                    return f"{field_def} currency_field='currency_id'{closing_paren}"
                else:
                    return f"{field_def}, currency_field='currency_id'{closing_paren}"

            content = re.sub(pattern, fix_monetary_field, content)

            # If content changed, write it back
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_files.append(file_name)
                print(f"✅ Fixed Monetary fields in: {file_name}")

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")

    print(f"\n🎯 Summary: Fixed {len(fixed_files)} files")
    for file in fixed_files:
        print(f"  - {file}")


if __name__ == "__main__":
    fix_monetary_currency_field()
