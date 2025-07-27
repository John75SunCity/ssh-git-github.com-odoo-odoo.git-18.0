#!/usr/bin/env python3
"""
Advanced Syntax Fixer for Records Management Module
Fixes the remaining specific syntax patterns identified
"""

import os
import re
from pathlib import Path

def fix_selection_mismatched_brackets(content):
    """Fix Selection fields with mismatched brackets like ), string= after ["""
    # Pattern: fields.Selection([ ... ), string=
    # Should be: fields.Selection([ ... ], string=
    
    lines = content.split('\n')
    fixed_lines = []
    in_selection = False
    bracket_count = 0
    paren_count = 0
    
    for i, line in enumerate(lines):
        original_line = line
        
        if 'fields.Selection(' in line and '[' in line:
            in_selection = True
            bracket_count = line.count('[') - line.count(']')
            paren_count = line.count('(') - line.count(')')
        elif in_selection:
            bracket_count += line.count('[') - line.count(']')
            paren_count += line.count('(') - line.count(')')
            
            # Look for lines like "), string=" when we have open brackets
            if bracket_count > 0 and '), string=' in line:
                line = line.replace('), string=', '], string=')
                bracket_count = 0
                in_selection = False
            elif bracket_count == 0 and in_selection:
                in_selection = False
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_missing_commas(content):
    """Fix missing commas in various contexts"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        original_line = line
        stripped = line.strip()
        
        # Fix missing comma in field definitions
        if (stripped.endswith("'") or stripped.endswith('"')) and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if (next_line.startswith(('ondelete=', 'help=', 'string=', 'default=', 'index=', 'tracking=')) and
                not stripped.endswith(',') and not stripped.endswith(')')):
                line = line.rstrip() + ','
        
        # Fix specific missing comma patterns
        if "help='" in line and not line.strip().endswith(',') and not line.strip().endswith(')'):
            if i + 1 < len(lines):
                next_stripped = lines[i + 1].strip()
                if next_stripped and not next_stripped.startswith(')') and not next_stripped.startswith('}'):
                    line = line.rstrip() + ','
        
        # Fix tuples missing commas like ('item', 'Item Text')
        if re.search(r"\('[^']*',\s*'[^']*'\)$", stripped) and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.startswith('], string=') or next_line.startswith('), string='):
                line = line.rstrip() + ','
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_incomplete_field_definitions(content):
    """Fix incomplete field definitions"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        original_line = line
        stripped = line.strip()
        
        # Fix incomplete field definitions ending with just parameter name
        if (stripped.endswith('=') and 
            ('ondelete=' in stripped or 'help=' in stripped or 'string=' in stripped)):
            # Look ahead for the value
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith("'") and next_line.endswith("'"):
                    # Combine the lines
                    line = line.rstrip() + next_line
                    # Skip the next line
                    if i + 1 < len(lines):
                        lines[i + 1] = ''  # Mark for removal
        
        # Fix lines that should end with closing parenthesis
        if ('fields.' in line and '(' in line and 
            not line.strip().endswith(')') and 
            not line.strip().endswith(',')):
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if (next_line.startswith(('def ', 'class ', '@', '#')) or 
                    'fields.' in next_line or next_line == ''):
                    if not line.strip().endswith(')'):
                        line = line.rstrip() + ')'
        
        if line.strip():  # Only add non-empty lines
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_specific_syntax_issues(content):
    """Fix specific syntax issues found in the error report"""
    
    # Fix logger definition missing closing parenthesis
    content = re.sub(r'_logger = logging\.getLogger\(__name__$', 
                     '_logger = logging.getLogger(__name__)', content)
    
    # Fix search method missing closing bracket
    content = re.sub(r"search\(\[([^\]]+)$", r"search\([\1])", content, flags=re.MULTILINE)
    
    # Fix incomplete string definitions
    content = re.sub(r"help='([^']+)'$", r"help='\1',", content, flags=re.MULTILINE)
    
    # Fix Selection field issues - double closing parens
    content = re.sub(r'\)\), string="Selection Field"\)', '), string="Selection Field")', content)
    
    # Fix trailing comma issues in tuples
    content = re.sub(r"',\), string=", "'), string=", content)
    
    return content

def fix_file(filepath):
    """Fix a single Python file with advanced patterns"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes in order
        content = fix_selection_mismatched_brackets(content)
        content = fix_missing_commas(content)
        content = fix_incomplete_field_definitions(content)
        content = fix_specific_syntax_issues(content)
        
        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    """Main function to fix remaining syntax errors"""
    
    # Files that still have syntax errors
    error_files = [
        'records_management/models/advanced_billing.py',
        'records_management/models/barcode_models.py',
        'records_management/models/barcode_product.py',
        'records_management/models/billing_models.py',
        'records_management/models/box_contents.py',
        'records_management/models/customer_feedback.py',
        'records_management/models/customer_inventory_report.py',
        'records_management/models/department_billing.py',
        'records_management/models/destruction_item.py',
        'records_management/models/document_retrieval_work_order.py',
        'records_management/models/fsm_task.py',
        'records_management/models/hr_employee.py',
        'records_management/models/hr_employee_naid.py',
        'records_management/models/ir_module.py',
        'records_management/models/load.py'
    ]
    
    print("🔧 Advanced Syntax Fixer for Records Management Module")
    print("=" * 60)
    print(f"🎯 Fixing {len(error_files)} files with remaining syntax errors")
    print()
    
    fixed_count = 0
    
    for i, filepath in enumerate(error_files, 1):
        if os.path.exists(filepath):
            print(f"[{i:2d}/{len(error_files)}] Fixing {filepath}...", end=" ")
            
            if fix_file(filepath):
                print("✅ FIXED")
                fixed_count += 1
            else:
                print("⚪ NO CHANGES")
        else:
            print(f"[{i:2d}/{len(error_files)}] {filepath}... ❌ NOT FOUND")
    
    print()
    print("=" * 60)
    print(f"📊 SUMMARY: Fixed {fixed_count}/{len(error_files)} files")
    print("🎯 Run comprehensive_syntax_checker.py to verify fixes")

if __name__ == "__main__":
    main()
