#!/usr/bin/env python3
"""
XML Formatter for Odoo 18.0 - Records Management Module
Ensures consistent 4-space indentation and Odoo 18.0 compliance
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
import re

def format_xml_file(file_path):
    """Format an XML file with consistent 4-space indentation"""
    try:
        # Parse the XML to ensure it's valid
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Read the original file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if this is an Odoo XML file
        if '<odoo>' not in content and '<openerp>' not in content:
            return False, "Not an Odoo XML file"
            
        # Replace deprecated openerp tags with odoo
        content = content.replace('<openerp>', '<odoo>')
        content = content.replace('</openerp>', '</odoo>')
        
        # Replace deprecated tree tags with list (Odoo 18.0)
        content = re.sub(r'<tree([^>]*)>', r'<list\1>', content)
        content = re.sub(r'</tree>', '</list>', content)
        
        # Split into lines for indentation fixing
        lines = content.split('\n')
        formatted_lines = []
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                formatted_lines.append('')
                continue
                
            # Handle closing tags
            if stripped.startswith('</') and not stripped.startswith('<!--'):
                indent_level = max(0, indent_level - 1)
            
            # Add properly indented line
            formatted_lines.append('    ' * indent_level + stripped)
            
            # Handle opening tags (but not self-closing or comments)
            if (stripped.startswith('<') and 
                not stripped.startswith('</') and 
                not stripped.startswith('<!--') and
                not stripped.startswith('<?') and
                not stripped.endswith('/>')):
                indent_level += 1
        
        # Write the formatted content
        formatted_content = '\n'.join(formatted_lines)
        
        # Validate the formatted XML
        try:
            ET.fromstring(formatted_content)
        except ET.ParseError as e:
            return False, f"Formatting created invalid XML: {e}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
            
        return True, "Successfully formatted"
        
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Main function to format all XML files in records_management"""
    base_path = Path('records_management')
    
    if not base_path.exists():
        print("❌ records_management directory not found")
        return
    
    # Find all XML files
    xml_files = list(base_path.glob('**/*.xml'))
    
    print(f"🔍 Found {len(xml_files)} XML files to check")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for xml_file in xml_files:
        try:
            success, message = format_xml_file(xml_file)
            
            if success:
                print(f"✅ {xml_file.relative_to(Path('.'))} - {message}")
                success_count += 1
            elif "Not an Odoo XML file" in message:
                print(f"⚠️  {xml_file.relative_to(Path('.'))} - {message}")
                skipped_count += 1
            else:
                print(f"❌ {xml_file.relative_to(Path('.'))} - {message}")
                error_count += 1
                
        except Exception as e:
            print(f"💥 {xml_file.relative_to(Path('.'))} - Exception: {e}")
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY:")
    print(f"✅ Successfully formatted: {success_count}")
    print(f"⚠️  Skipped (non-Odoo): {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📁 Total files: {len(xml_files)}")

if __name__ == "__main__":
    main()
