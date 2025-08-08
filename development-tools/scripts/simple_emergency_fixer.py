#!/usr/bin/env python3
"""
Simple Emergency Syntax Fixer for Odoo Deployment
Fixes only the most critical syntax errors to make the module loadable
"""

import os
import re
from pathlib import Path

def simple_fix_file(file_path):
    """Apply simple fixes to make file parseable by Python"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = []
        
        # Fix 1: Replace Selection([) with Selection([('temp', 'Temporary')])
        pattern = r'fields\.Selection\(\[\)'
        if re.search(pattern, content):
            content = re.sub(pattern, "fields.Selection([('temp', 'Temporary')])", content)
            fixes_applied.append("Fixed empty Selection fields")
        
        # Fix 2: Remove orphaned pass statements that cause indentation errors
        content = re.sub(r'\n\s*pass\s*\n(\s*)(\w+)', r'\n\1\2', content)
        if content != original_content and not fixes_applied:
            fixes_applied.append("Removed orphaned pass statements")
        
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
    
    print("=== Simple Emergency Syntax Fixer ===")
    print("Applying minimal fixes to make module loadable...")
    
    python_files = list(models_dir.glob("*.py"))
    fixed_count = 0
    
    for py_file in python_files:
        if py_file.name == '__init__.py':
            continue
            
        print(f"Fixing: {py_file.name}")
        
        success, fixes = simple_fix_file(py_file)
        if success:
            print(f"  ✓ Applied: {', '.join(fixes)}")
            fixed_count += 1
        else:
            print(f"  - No changes needed")
    
    print(f"\n=== Summary ===")
    print(f"Files processed: {len(python_files)-1}")  # Exclude __init__.py
    print(f"Files fixed: {fixed_count}")
    
    return True

if __name__ == "__main__":
    main()
