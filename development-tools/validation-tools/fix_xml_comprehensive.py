#!/usr/bin/env python3
"""
Comprehensive XML indentation fixer for all view files
"""
import os
import re
import glob

def fix_xml_indentation_comprehensive(file_path):
    """Fix XML indentation issues comprehensively"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        lines = content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith('<!--'):
                fixed_lines.append(line)
                continue

            # XML declaration should not be indented
            if stripped.startswith('<?xml'):
                fixed_lines.append(stripped)
                continue

            # Root odoo tag should not be indented
            if stripped in ['<odoo>', '</odoo>']:
                fixed_lines.append(stripped)
                continue

            # Record tags should be indented with 4 spaces
            if stripped.startswith('<record ') or stripped.startswith('</record>'):
                fixed_lines.append('    ' + stripped)
                continue

            # Field tags within records should be indented with 8 spaces
            if stripped.startswith('<field '):
                fixed_lines.append('        ' + stripped)
                continue

            # Menu items and act_window should be indented with 4 spaces
            if stripped.startswith('<menuitem ') or stripped.startswith('<act_window '):
                fixed_lines.append('    ' + stripped)
                continue

            # Comments should be indented with 4 spaces if they're not already properly indented
            if stripped.startswith('<!--') and not line.startswith('    <!--'):
                fixed_lines.append('    ' + stripped)
                continue

            # For everything else, preserve existing structure but fix obvious issues
            if line.startswith('<') and not line.startswith('    ') and not line.startswith('        '):
                # If it's a tag that should be indented
                if any(tag in stripped for tag in ['<tree', '<form', '<search', '<list', '<group', '<page', '<sheet', '<div', '<h1', '<label']):
                    # Determine indentation level based on context
                    if any(parent in str(lines[max(0, i-5):i]) for parent in ['<arch type="xml">']):
                        fixed_lines.append('            ' + stripped)
                    else:
                        fixed_lines.append('        ' + stripped)
                    continue

            # Keep line as-is if no specific rule applies
            fixed_lines.append(line)

        content = '\n'.join(fixed_lines)

        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Fix indentation in all view XML files"""
    # Get files that have indentation issues
    view_files = []

    for file_path in glob.glob('records_management/views/*.xml'):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            # Check for indentation issues
            if (re.search(r'^<record ', content, re.MULTILINE) or
                re.search(r'^<field ', content, re.MULTILINE)):
                view_files.append(file_path)
        except:
            pass

    print(f"🔍 Found {len(view_files)} XML files that need indentation fixes")

    # Process in batches
    batch_size = 25
    for i in range(0, min(len(view_files), 50), batch_size):  # Limit to first 50 files
        batch = view_files[i:i+batch_size]
        print(f"\n📦 Processing batch {i//batch_size + 1}: files {i+1}-{min(i+batch_size, len(view_files))}")

        fixed_count = 0
        for file_path in batch:
            if fix_xml_indentation_comprehensive(file_path):
                fixed_count += 1
                print(f"✅ Fixed: {os.path.basename(file_path)}")
            else:
                print(f"⚪ No changes: {os.path.basename(file_path)}")

        print(f"📊 Batch summary: Fixed {fixed_count}/{len(batch)} files")

    print(f"\n🎯 Total files processed: {min(len(view_files), 50)}")

if __name__ == "__main__":
    main()
