#!/usr/bin/env python3
"""
Fix syntax errors caused by stray constraint messages

This script removes leftover constraint message strings that are causing
syntax errors after the constraint conversion.
"""

import os
import re
import glob

def fix_syntax_errors(file_path):
    """Fix syntax errors in a Python model file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern 1: Fix stray constraint messages after field definitions
    # Match: field_name = fields.Type(...)", "constraint message"
    pattern1 = r'(\s*\w+\s*=\s*fields\.[^)]+\))\s*[\'"][^\'\"]*[\'\"]\s*,?\s*([\'"][^\'\"]*[\'\"]\s*)\s*'
    content = re.sub(pattern1, r'\1', content)
    
    # Pattern 2: Fix stray closing parentheses and constraint messages
    # Match: )", "constraint message"
    pattern2 = r'\)\s*[\'"][^\'\"]*[\'\"]\s*,?\s*'
    content = re.sub(pattern2, ')', content)
    
    # Pattern 3: Fix lines that only contain constraint messages
    # Match: "constraint message", or "constraint message"
    pattern3 = r'^\s*[\'"][^\'\"]*[\'\"]\s*,?\s*$'
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        if re.match(pattern3, line):
            continue  # Skip lines that are only constraint messages
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Pattern 4: Fix unmatched closing parentheses
    # Remove standalone closing parentheses that don't match
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        # If line is just a closing parenthesis and the previous line doesn't need it
        if stripped == ')' and i > 0:
            prev_line = lines[i-1].strip()
            # Check if previous line already has proper closing or is complete
            if (prev_line.endswith(')') or 
                prev_line.endswith(',') or 
                prev_line.endswith(']') or
                'fields.' in prev_line and ')' in prev_line):
                continue  # Skip this standalone closing paren
        fixed_lines.append(line)
    
    content = '\n'.join(fixed_lines)
    
    # Pattern 5: Fix EOL while scanning string literal errors
    # Look for unclosed strings and try to fix them
    content = re.sub(r'([\'"])[^\'\"]*$', r'\1', content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def main():
    """Main function to fix all model files"""
    models_dir = '/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models'
    py_files = glob.glob(os.path.join(models_dir, '*.py'))
    
    fixed_files = []
    
    for file_path in py_files:
        if fix_syntax_errors(file_path):
            fixed_files.append(file_path)
            print(f"Fixed: {os.path.basename(file_path)}")
    
    print(f"\n=== SYNTAX ERROR FIX SUMMARY ===")
    print(f"Total files checked: {len(py_files)}")
    print(f"Files fixed: {len(fixed_files)}")
    
    if fixed_files:
        print("\nFixed files:")
        for file_path in fixed_files:
            print(f"  - {os.path.basename(file_path)}")

if __name__ == '__main__':
    main()
