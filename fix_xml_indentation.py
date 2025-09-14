#!/usr/bin/env python3
"""
Fix XML indentation issues in view files
"""
import os
import re
import glob

def fix_xml_indentation(file_path):
    """Fix common XML indentation issues in Odoo view files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Store original content
        original_content = content

        # Fix record tags that start at beginning of line (should be indented)
        content = re.sub(r'^<record ', r'    <record ', content, flags=re.MULTILINE)

        # Fix field tags that start at beginning of line within records
        lines = content.split('\n')
        fixed_lines = []
        inside_record = False

        for line in lines:
            stripped = line.strip()

            # Track if we're inside a record
            if '<record ' in stripped:
                inside_record = True
            elif '</record>' in stripped:
                inside_record = False

            # Fix field indentation inside records
            if inside_record and stripped.startswith('<field '):
                # If the field is at the beginning of the line, indent it properly
                if line.startswith('<field '):
                    line = '        ' + line

            fixed_lines.append(line)

        content = '\n'.join(fixed_lines)

        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            print(f"⚪ No changes needed: {file_path}")
            return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Fix indentation in all view XML files"""
    view_files = glob.glob('records_management/views/*.xml')
    print(f"🔍 Found {len(view_files)} XML files to check")

    fixed_count = 0
    for file_path in view_files[:10]:  # Start with first 10 files
        if fix_xml_indentation(file_path):
            fixed_count += 1

    print(f"\n📊 Summary: Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
