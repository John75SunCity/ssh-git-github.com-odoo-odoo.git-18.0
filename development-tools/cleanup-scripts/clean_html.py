#!/usr/bin/env python3
"""
Remove HTML from XML string attributes to fix syntax errors
"""

import os
import re

def clean_html_from_xml_strings():
    """Remove HTML from XML string attributes"""
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

            # Remove HTML from string attributes - simplified approach
            # Pattern: string="text <i class='...'/>... text"
            # Replace with: string="text"

            # Remove FontAwesome icons from string attributes
            content = re.sub(r'string="([^"]*)<i class=\'[^\']*\'/>([^"]*)"', r'string="\1\2"', content)
            content = re.sub(r'string="([^"]*)<i class="[^"]*"/>([^"]*)"', r'string="\1\2"', content)
            content = re.sub(r'string="([^"]*)<i class=&quot;[^&]*&quot;/>([^"]*)"', r'string="\1\2"', content)
            content = re.sub(r'string="([^"]*)<i class=&quot;[^&]*&quot;/&gt;([^"]*)"', r'string="\1\2"', content)

            # Clean up extra spaces
            content = re.sub(r'string="(\s+)', r'string="\1', content)
            content = re.sub(r'(\s+)"', r'\1"', content)
            content = re.sub(r'string="\s+([^"]*)\s+"', r'string="\1"', content)

            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                print(f"🔧 Cleaned HTML from {filename}")
            else:
                print(f"✅ No HTML to clean in {filename}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    print(f"\n🎯 Cleaned HTML from {fixed_count} files")

if __name__ == '__main__':
    clean_html_from_xml_strings()
