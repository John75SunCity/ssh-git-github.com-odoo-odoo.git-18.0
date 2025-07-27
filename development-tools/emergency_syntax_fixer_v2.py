#!/usr/bin/env python3
"""
Emergency Syntax Fixer - Fix the most critical deployment-blocking syntax errors
"""

import os
import re
from pathlib import Path

def emergency_fix_file(file_path):
    """Apply emergency fixes to make Python files parseable"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = []
        
        # Fix 1: Remove orphaned pass statements
        content = re.sub(r'\n\s*pass\s*\n(\s*)(\w+)', r'\n\1\2', content)
        if content != original_content:
            fixes_applied.append("Removed orphaned pass statements")
        
        # Fix 2: Fix malformed field definitions like:
        # field_name = fields.Type()
        #     parameter='value'
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for malformed field definitions
            if re.match(r'\s*\w+\s*=\s*fields\.\w+\(\)\s*$', line):
                field_lines = [line.replace('()', '(')]
                i += 1
                
                while i < len(lines):
                    param_line = lines[i]
                    field_lines.append(param_line)
                    if ')' in param_line:
                        break
                    i += 1
                
                fixed_lines.extend(field_lines)
                fixes_applied.append("Fixed malformed field definition")
            else:
                fixed_lines.append(line)
            
            i += 1
        
        content = '\n'.join(fixed_lines)
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, fixes_applied
        
        return False, []
        
    except Exception as e:
        return False, [f"Error: {str(e)}"]

def main():
    """Apply emergency fixes to all Python files"""
    models_dir = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models")
    
    print("=== Emergency Syntax Fixer ===")
    
    python_files = list(models_dir.glob("*.py"))
    fixed_count = 0
    
    for py_file in python_files:
        if py_file.name == '__init__.py':
            continue
            
        print(f"Processing: {py_file.name}")
        
        success, fixes = emergency_fix_file(py_file)
        if success:
            print(f"  ✓ Fixed: {', '.join(fixes)}")
            fixed_count += 1
        else:
            print(f"  - No fixes needed")
    
    print(f"\nFiles fixed: {fixed_count}")
    return True

if __name__ == "__main__":
    main()
