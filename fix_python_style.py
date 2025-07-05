#!/usr/bin/env python3
"""
Script to fix common Python linting issues in the records_management module.
"""
import os
import re
import sys

def fix_file(filepath):
    """Fix common linting issues in a Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix trailing whitespace
        lines = content.split('\n')
        lines = [line.rstrip() for line in lines]
        
        # Ensure file ends with newline
        if lines and lines[-1] != '':
            lines.append('')
        
        # Fix multiple blank lines (reduce to maximum 2)
        fixed_lines = []
        blank_count = 0
        for line in lines:
            if line.strip() == '':
                blank_count += 1
                if blank_count <= 2:
                    fixed_lines.append(line)
            else:
                blank_count = 0
                fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {filepath}")
            return True
        else:
            print(f"No changes: {filepath}")
            return False
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Main function to process all Python files in records_management."""
    module_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-8.0/records_management"
    
    if not os.path.exists(module_path):
        print(f"Module path not found: {module_path}")
        sys.exit(1)
    
    fixed_count = 0
    total_count = 0
    
    # Process all .py files recursively
    for root, dirs, files in os.walk(module_path):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                total_count += 1
                if fix_file(filepath):
                    fixed_count += 1
    
    print(f"\nProcessed {total_count} Python files")
    print(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
