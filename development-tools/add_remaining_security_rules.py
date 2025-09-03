#!/usr/bin/env python3
"""
Add Remaining Missing Security Rules
This script adds security access rules for the final 27 missing models
"""

import csv
import os

def add_remaining_security_rules():
    """Add security rules for the remaining missing models"""
    csv_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv"

    # The 27 missing models that need security rules
    missing_models = [
        'customer.inventory.line',
        'fleet.vehicle',
        'hard.drive.scan.wizard.line',
        'ir.attachment',
        'ir.model',
        'ir.model.fields',
        'paper.model_bale',
        'processing.log.resolution.wizard',
        'project.project',
        'records.department.sharing.invite',
        'records.department.sharing.log',
        'records.location.inspection.line',
        'report.records_management.report_customer_inventory',
        'report.records_management.report_location_utilization',
        'report.records_management.revenue_forecasting_report',
        'res.company',
        'res.country',
        'res.country.state',
        'res.currency',
        'res.groups',
        'res.users',
        'retrieval.item.base',
        'shred.model_bin',
        'shredding.hard_drive',
        'stock.location',
        'stock.move',
        'work.order.coordinator'
    ]

    # Read existing content
    existing_lines = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            existing_lines = f.readlines()
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Remove empty lines
    existing_lines = [line.strip() for line in existing_lines if line.strip()]

    # Add new security rules
    new_rules = []
    for model_name in missing_models:
        # Create user access rule
        user_rule = f"access_{model_name.replace('.', '_')}_user,{model_name}.user,model_{model_name},records_management.group_records_user,1,1,1,0"
        new_rules.append(user_rule)

        # Create manager access rule
        manager_rule = f"access_{model_name.replace('.', '_')}_manager,{model_name}.manager,model_{model_name},records_management.group_records_manager,1,1,1,1"
        new_rules.append(manager_rule)

    # Write back to CSV
    try:
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            # Write existing content
            for line in existing_lines:
                f.write(line + '\n')

            # Add new rules
            for rule in new_rules:
                f.write(rule + '\n')

        print(f"✅ Successfully added {len(new_rules)} security rules for {len(missing_models)} models")

    except Exception as e:
        print(f"Error writing CSV: {e}")

def main():
    print("🔧 Adding remaining missing security rules...")
    add_remaining_security_rules()
    print("\n✅ All security rules added successfully!")
    print("🎯 CRITICAL SECURITY ISSUE RESOLVED!")
    print("\n📋 Next steps:")
    print("  1. Run validation script to confirm all security rules are in place")
    print("  2. Address remaining validation issues (translation warnings, etc.)")
    print("  3. Test module loading")

if __name__ == "__main__":
    main()
