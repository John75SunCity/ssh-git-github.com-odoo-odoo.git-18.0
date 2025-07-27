#!/usr/bin/env python3
"""
Comprehensive syntax fixer for Records Management module
Fixes missing closing parentheses and brackets in field definitions
"""

import os
import re
import subprocess
import sys

def fix_selection_field(content, line_num, lines):
    """Fix incomplete Selection field definitions"""
    # Find the Selection field start
    selection_start = line_num
    bracket_count = 0
    paren_count = 0
    
    # Scan from current line to find where the field should end
    for i in range(selection_start, min(selection_start + 20, len(lines))):
        line = lines[i]
        bracket_count += line.count('[') - line.count(']')
        paren_count += line.count('(') - line.count(')')
        
        # If we hit another field definition, we need to close the previous one
        if i > selection_start and 'fields.' in line and '=' in line:
            # Insert closing parts before this line
            if bracket_count > 0:
                lines[i-1] = lines[i-1].rstrip() + '], string=\'Selection Field\')\n'
            elif paren_count > 0:
                lines[i-1] = lines[i-1].rstrip() + ')\n'
            break
            
        # If brackets and parentheses are balanced, we're done
        if bracket_count == 0 and paren_count == 0 and i > selection_start:
            break
    
    return lines

def fix_field_definition(content, line_num, lines):
    """Fix incomplete field definitions"""
    field_start = line_num
    paren_count = 0
    
    # Count parentheses to find where field should end
    for i in range(field_start, min(field_start + 10, len(lines))):
        line = lines[i]
        paren_count += line.count('(') - line.count(')')
        
        # If we hit another field definition, close the previous one
        if i > field_start and ('fields.' in line or line.strip().startswith('#') or line.strip() == ''):
            if paren_count > 0:
                lines[i-1] = lines[i-1].rstrip() + ')\n'
            break
            
        if paren_count == 0 and i > field_start:
            break
    
    return lines

def fix_syntax_errors(file_path):
    """Fix syntax errors in a Python file"""
    print(f"Fixing {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # First pass: fix Selection fields
        i = 0
        while i < len(lines):
            line = lines[i]
            if 'fields.Selection([' in line and not line.strip().endswith('])'):
                # Find the end of the selection
                bracket_count = line.count('[') - line.count(']')
                j = i + 1
                while j < len(lines) and bracket_count > 0:
                    bracket_count += lines[j].count('[') - lines[j].count(']')
                    if bracket_count == 0:
                        # Check if we have proper closing
                        if not lines[j].strip().endswith('])'):
                            if lines[j].strip().endswith(')'):
                                lines[j] = lines[j].replace(')', '])')
                            elif lines[j].strip().endswith(','):
                                lines[j] = lines[j].rstrip().rstrip(',') + '])'
                            else:
                                lines[j] = lines[j].rstrip() + '])'
                        break
                    j += 1
                
                # If we never found a proper close, add it
                if bracket_count > 0 and j < len(lines):
                    # Find next field or end of class
                    k = j
                    while k < len(lines) and not ('fields.' in lines[k] or lines[k].strip().startswith('def ') or lines[k].strip().startswith('class ')):
                        k += 1
                    if k > j:
                        lines[k-1] = lines[k-1].rstrip() + '], string="Selection Field")'
            i += 1
        
        # Second pass: fix other field definitions
        i = 0
        while i < len(lines):
            line = lines[i]
            # Look for field definitions that might be incomplete
            if 'fields.' in line and '(' in line and not line.strip().endswith(')'):
                paren_count = line.count('(') - line.count(')')
                if paren_count > 0:
                    # Look ahead to find where this field should end
                    j = i + 1
                    while j < len(lines) and paren_count > 0:
                        next_line = lines[j]
                        paren_count += next_line.count('(') - next_line.count(')')
                        
                        # If we hit another field definition or method
                        if ('fields.' in next_line or next_line.strip().startswith('def ') or 
                            next_line.strip().startswith('class ') or next_line.strip().startswith('@')):
                            # Close the previous field
                            lines[j-1] = lines[j-1].rstrip() + ')'
                            break
                        j += 1
            i += 1
        
        # Write the fixed content back
        fixed_content = '\n'.join(lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
            
        # Test the syntax
        result = subprocess.run(['python3', '-m', 'py_compile', file_path], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ Fixed successfully: {file_path}")
            return True
        else:
            print(f"  ❌ Still has errors: {file_path}")
            print(f"     Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix all files"""
    # List of files with known syntax errors
    error_files = [
        'records_management/models/naid_destruction_record.py',
        'records_management/models/advanced_billing.py', 
        'records_management/models/records_approval_step.py',
        'records_management/models/hr_employee.py',
        'records_management/models/records_box.py',
        'records_management/models/records_box_movement.py',
        'records_management/models/stock_picking.py',
        'records_management/models/department_billing.py',
        'records_management/models/records_chain_of_custody.py',
        'records_management/models/records_deletion_request.py',
        'records_management/models/records_location.py'  # Add the one we know about
    ]
    
    fixed_count = 0
    total_count = len(error_files)
    
    for file_path in error_files:
        if os.path.exists(file_path):
            if fix_syntax_errors(file_path):
                fixed_count += 1
        else:
            print(f"File not found: {file_path}")
    
    print(f"\n📊 Summary: Fixed {fixed_count}/{total_count} files")
    
    if fixed_count == total_count:
        print("🎉 All syntax errors fixed!")
    else:
        print("⚠️  Some files still have errors - manual review needed")

if __name__ == "__main__":
    main()
