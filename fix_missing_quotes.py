#!/usr/bin/env python3
"""
Fix missing closing quotes and other XML syntax errors
"""

import os
import re

def fix_missing_quotes():
    """Fix missing closing quotes in XML files"""
    views_dir = '/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views'

    error_files = [
        'rm_module_configurator_views.xml',
        'chain_of_custody_views.xml',
        'service_item_menus.xml',
        'records_document_type_views.xml',
        'records_location_views.xml',
        'barcode_product_views.xml',
        'records_retention_policy_views.xml',
        'product_template_views.xml',
        'records_department_billing_contact_views.xml',
        'work_order_shredding_views.xml',
        'scan_retrieval_item_views.xml',
        'records_department_views.xml',
        'base_rate_views.xml',
        'naid_compliance_views.xml',
        'system_diagram_data_views.xml',
        'portal_request_views.xml',
        'records_billing_config_views.xml',
        'permanent_flag_wizard_views.xml',
        'paper_bale_views.xml',
        'bin_unlock_service_views.xml',
        'system_flowchart_wizard_views.xml',
        'load_views.xml',
        'records_retrieval_work_order_views.xml',
        'records_digital_scan_views.xml',
        'stock_lot_views.xml'
    ]

    fixed_count = 0

    for filename in error_files:
        filepath = os.path.join(views_dir, filename)
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filename}")
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Fix missing closing quotes on XML attributes
            # Pattern: attribute="value/> should be attribute="value"/>
            content = re.sub(r'(\w+)="([^"]*)/>', r'\1="\2"/>', content)

            # Fix missing closing quotes where quote is followed by /> or >
            content = re.sub(r'="([^"]*)/>', r'="\1"/>', content)
            content = re.sub(r'="([^"]*)>', r'="\1">', content)

            # Fix specific patterns that are still broken
            content = re.sub(r'name="([^"]*)/>', r'name="\1"/>', content)
            content = re.sub(r'string="([^"]*)/>', r'string="\1"/>', content)
            content = re.sub(r'class="([^"]*)/>', r'class="\1"/>', content)
            content = re.sub(r'invisible="([^"]*)/>', r'invisible="\1"/>', content)
            content = re.sub(r'confirm="([^"]*)/>', r'confirm="\1"/>', content)

            # Fix missing quotes after certain attributes
            content = re.sub(r'True/>', r'True"/>', content)
            content = re.sub(r'False/>', r'False"/>', content)
            content = re.sub(r'\?/>', r'?"/>', content)

            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                print(f"🔧 Fixed missing quotes in {filename}")
            else:
                print(f"✅ No missing quotes in {filename}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    print(f"\n🎯 Fixed missing quotes in {fixed_count} files")

if __name__ == '__main__':
    fix_missing_quotes()
