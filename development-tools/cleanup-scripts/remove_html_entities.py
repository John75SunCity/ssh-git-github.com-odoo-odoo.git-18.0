#!/usr/bin/env python3
"""
Remove HTML entities that are causing XML validation errors
"""

import os
import re
import glob

def remove_html_entities():
    """Remove problematic HTML entities from XML files"""
    views_dir = '/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views'

    # List of files that still have errors
    error_files = [
        'barcode_product_views.xml',
        'base_rate_views.xml',
        'bin_key_views.xml',
        'bin_unlock_service_views.xml',
        'chain_of_custody_views.xml',
        'naid_compliance_views.xml',
        'paper_bale_views.xml',
        'permanent_flag_wizard_views.xml',
        'product_template_views.xml',
        'records_billing_config_views.xml',
        'records_department_billing_contact_views.xml',
        'records_department_views.xml',
        'records_document_type_views.xml',
        'records_retention_policy_views.xml',
        'rm_module_configurator_views.xml',
        'scan_retrieval_item_views.xml',
        'service_item_menus.xml',
        'stock_lot_views.xml',
        'system_diagram_data_views.xml',
        'system_flowchart_wizard_views.xml',
        'visitor_pos_wizard_views.xml'
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

            # Remove HTML entities and clean up string attributes
            # Pattern: string="&lt;i class="fa fa-icon"&gt; Text"
            # Replace with: string="Text"
            content = re.sub(r'string="&lt;i class="[^"]*"&gt;\s*([^"]*)"', r'string="\1"', content)
            content = re.sub(r'string="&lt;i class=&quot;[^&]*&quot;&gt;\s*([^"]*)"', r'string="\1"', content)

            # Clean up remaining HTML entities
            content = content.replace('&lt;', '<')
            content = content.replace('&gt;', '>')
            content = content.replace('&quot;', '"')

            # Remove any remaining HTML tags in string attributes
            content = re.sub(r'string="[^"]*<[^>]*>[^"]*"', lambda m: f'string="{re.sub(r"<[^>]*>", "", m.group(0)[8:-1])}"', content)

            # Clean up extra spaces
            content = re.sub(r'string="\s+([^"]*)\s*"', r'string="\1"', content)

            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                print(f"🔧 Cleaned HTML entities from {filename}")
            else:
                print(f"✅ No HTML entities to clean in {filename}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    print(f"\n🎯 Cleaned HTML entities from {fixed_count} files")

if __name__ == '__main__':
    remove_html_entities()
