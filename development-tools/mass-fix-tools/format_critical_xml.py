#!/usr/bin/env python3
"""
Format critical XML files with proper 4-space indentation
"""

import xml.etree.ElementTree as ET
import os

def format_xml_content(content):
    """Fix indentation and Odoo 18.0 compliance"""
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
    
    return '\n'.join(formatted_lines)

# List of critical view files to format
critical_files = [
    'records_management/views/destruction_certificate_views.xml',
    'records_management/views/records_container_views.xml', 
    'records_management/views/records_billing_views.xml',
    'records_management/views/records_department_views.xml',
    'records_management/views/portal_request_views.xml'
]

print('🔧 FORMATTING CRITICAL XML FILES:')
print('=' * 50)

for file_path in critical_files:
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f'⚠️  {file_path}: File not found')
            continue
            
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if valid XML first
        try:
            ET.fromstring(content)
        except ET.ParseError as e:
            print(f'❌ {file_path}: Invalid XML - {e}')
            continue
            
        # Format content
        formatted_content = format_xml_content(content)
        
        # Validate formatted content
        try:
            ET.fromstring(formatted_content)
        except ET.ParseError as e:
            print(f'❌ {file_path}: Formatting created invalid XML - {e}')
            continue
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
            
        print(f'✅ {file_path}: Successfully formatted')
        
    except Exception as e:
        print(f'❌ {file_path}: Error - {e}')

print('\n🎯 Formatting complete!')
