#!/usr/bin/env python3
"""
Fix syntax errors in XML view files caused by emoji replacements
"""

import os
import re

# Files with known syntax errors
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

# Emoji to FontAwesome mapping for comprehensive replacement
emoji_replacements = {
    # Already in script but might be missed
    '🔄': '<i class="fa fa-exchange"/>',
    '🚀': '<i class="fa fa-rocket"/>',
    '🚫': '<i class="fa fa-ban"/>',
    '⏱️': '<i class="fa fa-clock-o"/>',
    '✏️': '<i class="fa fa-edit"/>',
    '⚠️': '<i class="fa fa-warning"/>',

    # Additional problem emojis found in error analysis
    '�': '<i class="fa fa-cog"/>',  # Malformed Unicode character
    '💰': '<i class="fa fa-money"/>',
    '📋': '<i class="fa fa-clipboard"/>',
    '🎯': '<i class="fa fa-bullseye"/>',
    '📦': '<i class="fa fa-box"/>',
    '🔑': '<i class="fa fa-key"/>',
    '⚙️': '<i class="fa fa-cog"/>',
    '📂': '<i class="fa fa-folder"/>',
    '💼': '<i class="fa fa-briefcase"/>',
    '🌐': '<i class="fa fa-globe"/>',
    '🔧': '<i class="fa fa-wrench"/>',
    '⏸️': '<i class="fa fa-pause"/>',
    '🕒': '<i class="fa fa-clock-o"/>',
    '🏢': '<i class="fa fa-building"/>',
    '📊': '<i class="fa fa-bar-chart"/>',
    '🔍': '<i class="fa fa-search"/>',
    '📈': '<i class="fa fa-line-chart"/>',
    '🎨': '<i class="fa fa-paint-brush"/>',
    '📱': '<i class="fa fa-mobile"/>',
    '🔒': '<i class="fa fa-lock"/>',
    '⚖️': '<i class="fa fa-balance-scale"/>',
    '👤': '<i class="fa fa-user"/>',
    '👥': '<i class="fa fa-users"/>',
    '🏠': '<i class="fa fa-home"/>',
    '🎪': '<i class="fa fa-circle"/>',
    '🔔': '<i class="fa fa-bell"/>',
    '💡': '<i class="fa fa-lightbulb-o"/>',
    '🎭': '<i class="fa fa-theater-masks"/>',
    '🎲': '<i class="fa fa-dice"/>',
    '🎬': '<i class="fa fa-film"/>',
    '🎮': '<i class="fa fa-gamepad"/>',
    '🎰': '<i class="fa fa-gift"/>',
    '⭐': '<i class="fa fa-star"/>',
    '✅': '<i class="fa fa-check"/>',
    '❌': '<i class="fa fa-times"/>',
    '⬆️': '<i class="fa fa-arrow-up"/>',
    '⬇️': '<i class="fa fa-arrow-down"/>',
    '➡️': '<i class="fa fa-arrow-right"/>',
    '⬅️': '<i class="fa fa-arrow-left"/>',
    '🔥': '<i class="fa fa-fire"/>',
    '💯': '<i class="fa fa-percent"/>',
    '📅': '<i class="fa fa-calendar"/>',
    '📄': '<i class="fa fa-file-o"/>',
    '📝': '<i class="fa fa-pencil"/>',
    '📞': '<i class="fa fa-phone"/>',
    '📧': '<i class="fa fa-envelope"/>',
    '🎵': '<i class="fa fa-music"/>',
    '🔊': '<i class="fa fa-volume-up"/>',
    '🔇': '<i class="fa fa-volume-off"/>',
    '🎧': '<i class="fa fa-headphones"/>',
    '📸': '<i class="fa fa-camera"/>',
    '🎥': '<i class="fa fa-video-camera"/>',
    '💻': '<i class="fa fa-laptop"/>',
    '🖥️': '<i class="fa fa-desktop"/>',
    '⌨️': '<i class="fa fa-keyboard-o"/>',
    '🖱️': '<i class="fa fa-mouse-pointer"/>',
    '🖨️': '<i class="fa fa-print"/>',
    '📠': '<i class="fa fa-fax"/>',
}

def fix_emoji_syntax_errors():
    """Fix emoji-related syntax errors in XML files"""
    views_dir = '/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views'
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

            # Apply emoji replacements
            for emoji, replacement in emoji_replacements.items():
                if emoji in content:
                    content = content.replace(emoji, replacement)
                    print(f"✅ Fixed {emoji} in {filename}")

            # Additional fixes for common XML syntax issues
            # Fix malformed quotes in attributes
            content = re.sub(r'class="([^"]*)"([^>]*)"', r'class="\1"\2', content)

            # Fix malformed FontAwesome classes
            content = re.sub(r'class="fa fa-([^"]*)"', r"class='fa fa-\1'", content)

            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                print(f"🔧 Fixed syntax errors in {filename}")
            else:
                print(f"✅ No changes needed in {filename}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    print(f"\n🎯 Fixed syntax errors in {fixed_count} files")

if __name__ == '__main__':
    fix_emoji_syntax_errors()
