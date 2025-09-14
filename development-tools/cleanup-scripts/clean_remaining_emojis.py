#!/usr/bin/env python3
"""
Comprehensive emoji cleanup for remaining emojis in view files
"""

import os
import re
import glob

def clean_remaining_emojis():
    """Clean all remaining emojis from view files"""
    views_dir = '/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views'

    # Extended emoji mapping
    emoji_replacements = {
        '👤': '&lt;i class="fa fa-user"&gt;',
        '👥': '&lt;i class="fa fa-users"&gt;',
        '🏢': '&lt;i class="fa fa-building"&gt;',
        '📋': '&lt;i class="fa fa-clipboard"&gt;',
        '⚠️': '&lt;i class="fa fa-warning"&gt;',
        '🛣️': '&lt;i class="fa fa-road"&gt;',
        '⚙️': '&lt;i class="fa fa-cog"&gt;',
        '🏷️': '&lt;i class="fa fa-tag"&gt;',
        '🗑️': '&lt;i class="fa fa-trash"&gt;',
        '🗓️': '&lt;i class="fa fa-calendar"&gt;',
        '🔑': '&lt;i class="fa fa-key"&gt;',
        '🔄': '&lt;i class="fa fa-refresh"&gt;',
        '🚫': '&lt;i class="fa fa-ban"&gt;',
        '♻️': '&lt;i class="fa fa-recycle"&gt;',
        '⏱️': '&lt;i class="fa fa-clock-o"&gt;',
        '🚀': '&lt;i class="fa fa-rocket"&gt;',
        '⚡': '&lt;i class="fa fa-bolt"&gt;',
        '💰': '&lt;i class="fa fa-money"&gt;',
        '🎯': '&lt;i class="fa fa-bullseye"&gt;',
        '📦': '&lt;i class="fa fa-box"&gt;',
        '📂': '&lt;i class="fa fa-folder"&gt;',
        '💼': '&lt;i class="fa fa-briefcase"&gt;',
        '🌐': '&lt;i class="fa fa-globe"&gt;',
        '🔧': '&lt;i class="fa fa-wrench"&gt;',
        '⏸️': '&lt;i class="fa fa-pause"&gt;',
        '🕒': '&lt;i class="fa fa-clock-o"&gt;',
        '📊': '&lt;i class="fa fa-bar-chart"&gt;',
        '🔍': '&lt;i class="fa fa-search"&gt;',
        '📈': '&lt;i class="fa fa-line-chart"&gt;',
        '🎨': '&lt;i class="fa fa-paint-brush"&gt;',
        '📱': '&lt;i class="fa fa-mobile"&gt;',
        '🔒': '&lt;i class="fa fa-lock"&gt;',
        '⚖️': '&lt;i class="fa fa-balance-scale"&gt;',
        '🏠': '&lt;i class="fa fa-home"&gt;',
        '🎪': '&lt;i class="fa fa-circle"&gt;',
        '🔔': '&lt;i class="fa fa-bell"&gt;',
        '💡': '&lt;i class="fa fa-lightbulb-o"&gt;',
        '🎭': '&lt;i class="fa fa-theater-masks"&gt;',
        '🎲': '&lt;i class="fa fa-dice"&gt;',
        '🎬': '&lt;i class="fa fa-film"&gt;',
        '🎮': '&lt;i class="fa fa-gamepad"&gt;',
        '🎰': '&lt;i class="fa fa-gift"&gt;',
        '⭐': '&lt;i class="fa fa-star"&gt;',
        '✅': '&lt;i class="fa fa-check"&gt;',
        '❌': '&lt;i class="fa fa-times"&gt;',
        '⬆️': '&lt;i class="fa fa-arrow-up"&gt;',
        '⬇️': '&lt;i class="fa fa-arrow-down"&gt;',
        '➡️': '&lt;i class="fa fa-arrow-right"&gt;',
        '⬅️': '&lt;i class="fa fa-arrow-left"&gt;',
        '🔥': '&lt;i class="fa fa-fire"&gt;',
        '💯': '&lt;i class="fa fa-percent"&gt;',
        '📅': '&lt;i class="fa fa-calendar"&gt;',
        '📄': '&lt;i class="fa fa-file-o"&gt;',
        '📝': '&lt;i class="fa fa-pencil"&gt;',
        '📞': '&lt;i class="fa fa-phone"&gt;',
        '📧': '&lt;i class="fa fa-envelope"&gt;',
        '🎵': '&lt;i class="fa fa-music"&gt;',
        '🔊': '&lt;i class="fa fa-volume-up"&gt;',
        '🔇': '&lt;i class="fa fa-volume-off"&gt;',
        '🎧': '&lt;i class="fa fa-headphones"&gt;',
        '📸': '&lt;i class="fa fa-camera"&gt;',
        '🎥': '&lt;i class="fa fa-video-camera"&gt;',
        '💻': '&lt;i class="fa fa-laptop"&gt;',
        '🖥️': '&lt;i class="fa fa-desktop"&gt;',
        '⌨️': '&lt;i class="fa fa-keyboard-o"&gt;',
        '🖱️': '&lt;i class="fa fa-mouse-pointer"&gt;',
        '🖨️': '&lt;i class="fa fa-print"&gt;',
        '📠': '&lt;i class="fa fa-fax"&gt;',
        '✏️': '&lt;i class="fa fa-pencil"&gt;',
        '📦': '&lt;i class="fa fa-box"&gt;',
        '🎯': '&lt;i class="fa fa-bullseye"&gt;',
        '📋': '&lt;i class="fa fa-clipboard"&gt;',
        '⏱️': '&lt;i class="fa fa-clock-o"&gt;',
        '🎵': '&lt;i class="fa fa-music"&gt;'
    }

    # Find all XML files
    xml_files = glob.glob(os.path.join(views_dir, '*.xml'))
    fixed_count = 0

    for filepath in xml_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Apply emoji replacements
            for emoji, replacement in emoji_replacements.items():
                if emoji in content:
                    content = content.replace(emoji, replacement)
                    print(f"✅ Fixed {emoji} in {os.path.basename(filepath)}")

            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                print(f"🔧 Updated {os.path.basename(filepath)}")

        except Exception as e:
            print(f"❌ Error processing {os.path.basename(filepath)}: {e}")

    print(f"\n🎯 Updated {fixed_count} files with remaining emoji fixes")

if __name__ == '__main__':
    clean_remaining_emojis()
