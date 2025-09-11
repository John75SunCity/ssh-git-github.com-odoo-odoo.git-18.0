#!/usr/bin/env python3
"""
Comprehensive Indentation and Syntax Fixer
Fixes common indentation issues and field definition problems in Odoo models
"""

import os
import re
from pathlib import Path

def fix_field_definitions(content):
    """Fix broken field definitions across multiple lines"""
    
    # Pattern 1: Fix fields where opening parenthesis is on wrong line
    # field_name = fields.Type()
    #     parameter="value"
    # )
    pattern1 = r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*fields\.([A-Za-z]+)\(\)\s*\n\s*([^)]+)\n\s*\)'
    
    def fix_pattern1(match):
        indent, field_name, field_type, params = match.groups()
        # Clean up parameters and put them on correct line
        clean_params = params.strip().replace('\n    ', ', ')
        return f'{indent}{field_name} = fields.{field_type}({clean_params})'
    
    content = re.sub(pattern1, fix_pattern1, content, flags=re.MULTILINE)
    
    # Pattern 2: Fix Selection fields with broken bracket placement
    # activity_type = fields.Selection()
    #     [
    #         ("value", "Label"),
    #     ],
    #     string="Activity Type",
    # )
    pattern2 = r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*fields\.Selection\(\)\s*\n\s*\[\s*\n((?:\s*\([^)]+\),?\s*\n)*)\s*\],?\s*\n\s*([^)]*)\s*\)'
    
    def fix_pattern2(match):
        indent, field_name, selections, params = match.groups()
        # Clean up selections
        clean_selections = []
        for line in selections.strip().split('\n'):
            line = line.strip()
            if line and line != ',':
                clean_selections.append('        ' + line)
        
        selection_text = '\n'.join(clean_selections)
        clean_params = params.strip().replace('\n    ', ', ') if params.strip() else ''
        
        if clean_params:
            return f'{indent}{field_name} = fields.Selection([\n{selection_text}\n    ], {clean_params})'
        else:
            return f'{indent}{field_name} = fields.Selection([\n{selection_text}\n    ])'
    
    content = re.sub(pattern2, fix_pattern2, content, flags=re.MULTILINE | re.DOTALL)
    
    # Pattern 3: Fix method calls with wrong parenthesis placement
    # self.write()
    #     {
    #         "key": "value"
    #     }
    # )
    pattern3 = r'(\s*)(self\.[a-zA-Z_][a-zA-Z0-9_]*)\(\)\s*\n\s*(\{[^}]+\})\s*\n\s*\)'
    
    def fix_pattern3(match):
        indent, method_call, params = match.groups()
        # Clean up the dictionary parameter
        clean_params = re.sub(r'\n\s+', ' ', params.strip())
        return f'{indent}{method_call}({clean_params})'
    
    content = re.sub(pattern3, fix_pattern3, content, flags=re.MULTILINE | re.DOTALL)
    
    # Pattern 4: Fix broken conditional statements
    # if condition and ()
    #     other_condition
    # ):
    pattern4 = r'(\s*if\s+[^)]+)\s+and\s+\(\)\s*\n\s*([^)]+)\s*\n\s*\):'
    
    def fix_pattern4(match):
        condition_start, condition_end = match.groups()
        return f'{condition_start} and ({condition_end.strip()}):'
    
    content = re.sub(pattern4, fix_pattern4, content, flags=re.MULTILINE)
    
    return content

def fix_indentation_issues(content):
    """Fix common indentation problems"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue
            
        # Fix common indentation issues
        stripped = line.lstrip()
        
        # Calculate proper indentation based on context
        if i > 0:
            prev_line = lines[i-1].strip()
            
            # Inside class definition
            if prev_line.startswith('class ') and prev_line.endswith(':'):
                if not stripped.startswith('"""') and not stripped.startswith('#'):
                    line = '    ' + stripped
            
            # Inside method definition
            elif prev_line.startswith('def ') and prev_line.endswith(':'):
                if not stripped.startswith('"""') and not stripped.startswith('#'):
                    line = '        ' + stripped
            
            # Field definitions should be at class level (4 spaces)
            elif stripped.startswith(('_name', '_description', '_inherit', '_order', '_rec_name')):
                line = '    ' + stripped
            elif ' = fields.' in stripped:
                line = '    ' + stripped
                
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def process_python_file(file_path):
    """Process a single Python file to fix indentation and syntax issues"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_field_definitions(content)
        content = fix_indentation_issues(content)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "Fixed"
        else:
            return True, "No changes needed"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Process all Python files in the records_management models directory"""
    base_dir = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management")
    models_dir = base_dir / "models"
    
    if not models_dir.exists():
        print(f"Models directory not found: {models_dir}")
        return
    
    python_files = list(models_dir.glob("*.py"))
    print(f"Found {len(python_files)} Python files to process")
    
    results = {
        'fixed': [],
        'no_changes': [],
        'errors': []
    }
    
    for file_path in python_files:
        if file_path.name == "__init__.py":
            continue
            
        print(f"Processing: {file_path.name}")
        success, message = process_python_file(file_path)
        
        if success:
            if "Fixed" in message:
                results['fixed'].append(file_path.name)
            else:
                results['no_changes'].append(file_path.name)
        else:
            results['errors'].append((file_path.name, message))
    
    # Print summary
    print("\n" + "="*50)
    print("INDENTATION AND SYNTAX FIXING SUMMARY")
    print("="*50)
    
    print(f"\nFiles Fixed: {len(results['fixed'])}")
    for filename in results['fixed']:
        print(f"  ✓ {filename}")
    
    print(f"\nFiles with No Changes Needed: {len(results['no_changes'])}")
    for filename in results['no_changes']:
        print(f"  - {filename}")
    
    print(f"\nFiles with Errors: {len(results['errors'])}")
    for filename, error in results['errors']:
        print(f"  ✗ {filename}: {error}")
    
    print(f"\nTotal Processed: {len(python_files) - 1}")  # -1 for __init__.py

if __name__ == "__main__":
    main()
