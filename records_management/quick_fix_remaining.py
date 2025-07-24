#!/usr/bin/env python3
"""
Quick script to find and fix remaining One2many field issues that are causing KeyError: 'res_id'
"""

import os
import re
import glob

def check_one2many_fields():
    """Find One2many fields that are truly problematic"""
    
    model_files = glob.glob('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/*.py')
    
    issues = []
    
    for file_path in model_files:
        filename = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Look for One2many field definitions
                    if 'fields.One2many(' in line:
                        # Get the complete field definition (may span multiple lines)
                        field_def = line
                        j = i
                        
                        # Continue reading until we find the closing parenthesis
                        while j < len(lines) and ')' not in field_def:
                            j += 1
                            if j < len(lines):
                                field_def += ' ' + lines[j].strip()
                        
                        # Count commas to determine parameters
                        # Remove string literals to avoid counting commas inside strings
                        cleaned_def = re.sub(r"'[^']*'", "", field_def)
                        cleaned_def = re.sub(r'"[^"]*"', "", cleaned_def)
                        
                        # Count commas between One2many( and )
                        start = cleaned_def.find('fields.One2many(')
                        if start != -1:
                            rest = cleaned_def[start + 16:]  # After 'fields.One2many('
                            end = rest.find(')')
                            if end != -1:
                                params_part = rest[:end]
                                comma_count = params_part.count(',')
                                
                                # One2many should have at least 2 commas (3 parameters minimum)
                                # model, inverse_name, string
                                if comma_count < 2:
                                    issues.append({
                                        'file': filename,
                                        'line': i,
                                        'issue': f'Only {comma_count + 1} parameters',
                                        'content': line.strip()
                                    })
                                    
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    
    if issues:
        print(f"Found {len(issues)} actual issues:")
        for issue in issues:
            print(f"\n📁 {issue['file']}:{issue['line']}")
            print(f"   Issue: {issue['issue']}")
            print(f"   Content: {issue['content']}")
    else:
        print("✅ No One2many field issues found!")
    
    return issues

if __name__ == "__main__":
    check_one2many_fields()
