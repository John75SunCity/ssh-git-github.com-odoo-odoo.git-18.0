#!/usr/bin/env python3
"""
Script to replace emojis with FontAwesome icons in Odoo view files
"""

import os
import re
import glob

# Emoji to FontAwesome mapping
EMOJI_TO_FA = {
    # Document and content icons
    '📋': '<i class="fa fa-clipboard"/>',
    '📄': '<i class="fa fa-file-o"/>',
    '📝': '<i class="fa fa-pencil"/>',
    '📊': '<i class="fa fa-bar-chart"/>',
    '📈': '<i class="fa fa-line-chart"/>',
    '📅': '<i class="fa fa-calendar"/>',
    '📦': '<i class="fa fa-box"/>',
    '📢': '<i class="fa fa-bullhorn"/>',
    '📱': '<i class="fa fa-mobile"/>',

    # People and user icons
    '👤': '<i class="fa fa-user"/>',
    '👥': '<i class="fa fa-users"/>',
    '🆔': '<i class="fa fa-id-card-o"/>',

    # Business and money icons
    '💰': '<i class="fa fa-money"/>',
    '🏢': '<i class="fa fa-building"/>',
    '🏆': '<i class="fa fa-trophy"/>',

    # Action and status icons
    '✅': '<i class="fa fa-check-circle text-success"/>',
    '❌': '<i class="fa fa-times-circle text-danger"/>',
    '🎯': '<i class="fa fa-bullseye"/>',
    '⚡': '<i class="fa fa-bolt"/>',
    '🔍': '<i class="fa fa-search"/>',
    '💡': '<i class="fa fa-lightbulb-o"/>',

    # Security and lock icons
    '🔒': '<i class="fa fa-lock"/>',
    '🔐': '<i class="fa fa-unlock"/>',
    '🔧': '<i class="fa fa-wrench"/>',

    # Transport and logistics
    '🚚': '<i class="fa fa-truck"/>',
    '🔗': '<i class="fa fa-link"/>',

    # Technology icons
    '🌐': '<i class="fa fa-globe"/>',
}

def fix_emojis_in_file(file_path):
    """Replace emojis with FontAwesome icons in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes_made = 0

        # Replace each emoji with its FontAwesome equivalent
        for emoji, fa_icon in EMOJI_TO_FA.items():
            if emoji in content:
                content = content.replace(emoji, fa_icon)
                changes_made += content.count(fa_icon) - original_content.count(fa_icon)

        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed {changes_made} emojis in {file_path}")
            return True
        else:
            print(f"ℹ️  No emojis found in {file_path}")
            return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all view files"""
    views_dir = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views"

    # Find all XML files in views directory
    xml_files = glob.glob(os.path.join(views_dir, "*.xml"))

    print(f"🔍 Found {len(xml_files)} XML files to process...")
    print("=" * 60)

    files_changed = 0
    total_changes = 0

    for file_path in sorted(xml_files):
        if fix_emojis_in_file(file_path):
            files_changed += 1

    print("=" * 60)
    print(f"📊 Summary: {files_changed} files updated")

    if files_changed > 0:
        print("\n🎯 Next steps:")
        print("1. Review the changes: git diff")
        print("2. Test the views in Odoo")
        print("3. Commit: git add . && git commit -m 'fix: Replace emojis with FontAwesome icons in all view files'")
        print("4. Push: git push origin main")

if __name__ == "__main__":
    main()
