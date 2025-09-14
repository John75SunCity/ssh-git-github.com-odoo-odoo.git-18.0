#!/usr/bin/env python3
"""
Fix quote consistency issues in XML view files
"""

import os
import re

def fix_quote_consistency():
    """Fix XML quote consistency issues"""
    views_dir = '/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views'

    # List of files with known quote issues
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

            # Fix FontAwesome class quotes - standardize to double quotes
            content = re.sub(r"class='fa fa-([^']*)'", r'class="fa fa-\1"', content)

            # Fix mixed quotes in string attributes
            content = re.sub(r'string="([^"]*)<i class="([^"]*)"([^"]*)"', r'string="\1&lt;i class=&quot;\2&quot;\3"', content)

            # Fix HTML entities in XML attributes
            content = content.replace('<i class="', '&lt;i class=&quot;')
            content = content.replace('"/>', '&quot;/&gt;')
            content = content.replace('" string=', '&quot; string=')

            # Alternative approach - escape all FontAwesome icons properly
            # Pattern: string="text <i class="fa fa-icon"/> more text"
            # Replace with: string="text &lt;i class=&quot;fa fa-icon&quot;/&gt; more text"

            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                print(f"🔧 Fixed quote consistency in {filename}")
            else:
                print(f"✅ No quote issues in {filename}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    print(f"\n🎯 Fixed quote consistency in {fixed_count} files")

if __name__ == '__main__':
    fix_quote_consistency()
