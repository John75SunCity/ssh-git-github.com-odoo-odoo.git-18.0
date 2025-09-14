#!/usr/bin/env python3
"""
Final emoji cleanup script for Records Management views
Handles remaining emojis in XML files for complete professional conversion
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def clean_remaining_emojis():
    """Clean the final remaining emojis in XML files"""

    # Comprehensive emoji to FontAwesome mapping
    emoji_mapping = {
        # Picture/Media emojis
        '🖼️': '<i class="fa fa-picture-o" aria-hidden="true"></i>',
        '🗺️': '<i class="fa fa-map" aria-hidden="true"></i>',

        # Building/Structure emojis
        '🏗️': '<i class="fa fa-building-o" aria-hidden="true"></i>',

        # Shield/Security emojis
        '🛡️': '<i class="fa fa-shield" aria-hidden="true"></i>',

        # Document/File emojis
        '📋': '<i class="fa fa-clipboard" aria-hidden="true"></i>',
        '📄': '<i class="fa fa-file-o" aria-hidden="true"></i>',
        '📝': '<i class="fa fa-edit" aria-hidden="true"></i>',

        # Navigation/Direction emojis
        '⬆️': '<i class="fa fa-arrow-up" aria-hidden="true"></i>',
        '⬇️': '<i class="fa fa-arrow-down" aria-hidden="true"></i>',
        '➡️': '<i class="fa fa-arrow-right" aria-hidden="true"></i>',
        '⬅️': '<i class="fa fa-arrow-left" aria-hidden="true"></i>',

        # Status/Indicator emojis
        '✅': '<i class="fa fa-check-circle text-success" aria-hidden="true"></i>',
        '❌': '<i class="fa fa-times-circle text-danger" aria-hidden="true"></i>',
        '⚠️': '<i class="fa fa-warning text-warning" aria-hidden="true"></i>',
        '🔥': '<i class="fa fa-fire text-danger" aria-hidden="true"></i>',

        # Business/Office emojis
        '💼': '<i class="fa fa-briefcase" aria-hidden="true"></i>',
        '🏢': '<i class="fa fa-building" aria-hidden="true"></i>',
        '💰': '<i class="fa fa-money" aria-hidden="true"></i>',
        '📊': '<i class="fa fa-bar-chart" aria-hidden="true"></i>',

        # Technology emojis
        '💻': '<i class="fa fa-laptop" aria-hidden="true"></i>',
        '🖥️': '<i class="fa fa-desktop" aria-hidden="true"></i>',
        '⌨️': '<i class="fa fa-keyboard-o" aria-hidden="true"></i>',
        '🖱️': '<i class="fa fa-mouse-pointer" aria-hidden="true"></i>',
        '🖨️': '<i class="fa fa-print" aria-hidden="true"></i>',

        # Communication emojis
        '📞': '<i class="fa fa-phone" aria-hidden="true"></i>',
        '📧': '<i class="fa fa-envelope" aria-hidden="true"></i>',
        '📠': '<i class="fa fa-fax" aria-hidden="true"></i>',

        # Tools/Settings emojis
        '🔧': '<i class="fa fa-wrench" aria-hidden="true"></i>',
        '⚙️': '<i class="fa fa-cog" aria-hidden="true"></i>',
        '🔑': '<i class="fa fa-key" aria-hidden="true"></i>',
        '🔒': '<i class="fa fa-lock" aria-hidden="true"></i>',

        # Action/Process emojis
        '🚀': '<i class="fa fa-rocket" aria-hidden="true"></i>',
        '🔄': '<i class="fa fa-refresh" aria-hidden="true"></i>',
        '⏸️': '<i class="fa fa-pause" aria-hidden="true"></i>',
        '🔍': '<i class="fa fa-search" aria-hidden="true"></i>',

        # Time/Calendar emojis
        '🕒': '<i class="fa fa-clock-o" aria-hidden="true"></i>',
        '📅': '<i class="fa fa-calendar" aria-hidden="true"></i>',
        '🗓️': '<i class="fa fa-calendar-o" aria-hidden="true"></i>',
        '⏱️': '<i class="fa fa-stopwatch" aria-hidden="true"></i>',

        # Organization emojis
        '📂': '<i class="fa fa-folder" aria-hidden="true"></i>',
        '📦': '<i class="fa fa-box" aria-hidden="true"></i>',
        '🗑️': '<i class="fa fa-trash" aria-hidden="true"></i>',
        '♻️': '<i class="fa fa-recycle" aria-hidden="true"></i>',

        # People emojis
        '👤': '<i class="fa fa-user" aria-hidden="true"></i>',
        '👥': '<i class="fa fa-users" aria-hidden="true"></i>',

        # Locations emojis
        '🏠': '<i class="fa fa-home" aria-hidden="true"></i>',
        '🌐': '<i class="fa fa-globe" aria-hidden="true"></i>',

        # Media/Entertainment emojis
        '🎪': '<i class="fa fa-ticket" aria-hidden="true"></i>',
        '🎵': '<i class="fa fa-music" aria-hidden="true"></i>',
        '🎥': '<i class="fa fa-video-camera" aria-hidden="true"></i>',
        '📸': '<i class="fa fa-camera" aria-hidden="true"></i>',

        # Special/Misc emojis
        '⭐': '<i class="fa fa-star" aria-hidden="true"></i>',
        '💯': '<i class="fa fa-percent" aria-hidden="true"></i>',
        '🎯': '<i class="fa fa-bullseye" aria-hidden="true"></i>',
        '🎨': '<i class="fa fa-paint-brush" aria-hidden="true"></i>',
        '📱': '<i class="fa fa-mobile" aria-hidden="true"></i>',
        '💡': '<i class="fa fa-lightbulb-o" aria-hidden="true"></i>',
        '🔔': '<i class="fa fa-bell" aria-hidden="true"></i>',
        '📈': '<i class="fa fa-line-chart" aria-hidden="true"></i>',
        '🏷️': '<i class="fa fa-tag" aria-hidden="true"></i>',

        # Sound emojis
        '🔊': '<i class="fa fa-volume-up" aria-hidden="true"></i>',
        '🔇': '<i class="fa fa-volume-off" aria-hidden="true"></i>',
        '🎧': '<i class="fa fa-headphones" aria-hidden="true"></i>',

        # Gaming emojis
        '🎭': '<i class="fa fa-theater-masks" aria-hidden="true"></i>',
        '🎲': '<i class="fa fa-dice" aria-hidden="true"></i>',
        '🎬': '<i class="fa fa-film" aria-hidden="true"></i>',
        '🎮': '<i class="fa fa-gamepad" aria-hidden="true"></i>',
        '🎰': '<i class="fa fa-money" aria-hidden="true"></i>',

        # Writing emojis
        '✏️': '<i class="fa fa-pencil" aria-hidden="true"></i>',

        # Blocked/Stop emojis
        '🚫': '<i class="fa fa-ban text-danger" aria-hidden="true"></i>',

        # Energy emojis
        '⚡': '<i class="fa fa-bolt text-warning" aria-hidden="true"></i>',

        # Legal emojis
        '⚖️': '<i class="fa fa-balance-scale" aria-hidden="true"></i>',
    }

    views_dir = Path("records_management/views")
    if not views_dir.exists():
        print("Views directory not found!")
        return

    files_updated = 0
    total_replacements = 0

    print("🧹 Starting final emoji cleanup...")

    # Process all XML files in views directory
    for xml_file in views_dir.glob("*.xml"):
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            file_replacements = 0

            # Apply emoji replacements
            for emoji, fontawesome in emoji_mapping.items():
                if emoji in content:
                    replacement_count = content.count(emoji)
                    content = content.replace(emoji, fontawesome)
                    file_replacements += replacement_count
                    total_replacements += replacement_count
                    print(f"  {emoji} → FontAwesome ({replacement_count}x) in {xml_file.name}")

            # Write back if changes were made
            if content != original_content:
                with open(xml_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_updated += 1
                print(f"✅ Updated {xml_file.name} ({file_replacements} emoji replacements)")

        except Exception as e:
            print(f"❌ Error processing {xml_file.name}: {e}")

    print(f"\n🎉 Final emoji cleanup complete!")
    print(f"📊 Files updated: {files_updated}")
    print(f"🔄 Total emoji replacements: {total_replacements}")

    # Validate XML syntax after cleanup
    validate_xml_files()

def validate_xml_files():
    """Validate XML syntax in all view files"""
    views_dir = Path("records_management/views")
    if not views_dir.exists():
        return

    print("\n🔍 Validating XML syntax...")

    valid_files = 0
    error_files = 0

    for xml_file in views_dir.glob("*.xml"):
        try:
            ET.parse(xml_file)
            valid_files += 1
        except ET.ParseError as e:
            error_files += 1
            print(f"❌ XML Error in {xml_file.name}: {e}")
        except Exception as e:
            error_files += 1
            print(f"❌ Error validating {xml_file.name}: {e}")

    total_files = valid_files + error_files
    success_rate = (valid_files / total_files * 100) if total_files > 0 else 0

    print(f"\n📋 XML Validation Results:")
    print(f"✅ Valid files: {valid_files}")
    print(f"❌ Files with errors: {error_files}")
    print(f"📊 Success rate: {success_rate:.1f}% ({valid_files}/{total_files})")

if __name__ == "__main__":
    clean_remaining_emojis()
