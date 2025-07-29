#!/usr/bin/env python3
"""
Advanced syntax fixer - Target specific patterns found in the analysis
"""

import os
import re
import subprocess
from pathlib import Path

def fix_file_manually(file_path):
    """Fix specific syntax errors based on the patterns we identified"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix 1: Selection fields missing closing bracket and parenthesis
        # Pattern: fields.Selection([...]) becomes fields.Selection([...], string='...')
        content = re.sub(
            r'(fields\.Selection\(\[\s*(?:[^]]+\),?\s*)+\]\s*)\)',
            r"\1, string='Selection')",
            content
        )
        
        # Fix 2: Selection fields with wrong closing - ]) instead of )
        content = re.sub(
            r'(fields\.Selection\(\[[^]]+\]), string=\'[^\']+\'\]',
            r"\1, string='Selection')",
            content
        )
        
        # Fix 3: Lists that are missing closing bracket
        # domain=[...
        content = re.sub(
            r'(domain\s*=\s*\[\s*(?:\([^)]+\),?\s*)+)\s*$',
            r'\1]',
            content,
            flags=re.MULTILINE
        )
        
        # Fix 4: Fix malformed comments with extra )
        content = re.sub(r'(\s+#[^)]+)\)', r'\1', content)
        
        # Fix 5: Field definitions missing closing parenthesis
        # Look for lines that start with field definitions but don't end properly
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # If this line has fields. and (, but no ), and next line starts with another field
            if ('fields.' in line and '(' in line and 
                ')' not in line and 
                i < len(lines) - 1 and 
                ('fields.' in lines[i+1] or lines[i+1].strip().startswith('def ') or lines[i+1].strip().startswith('@'))):
                
                # Add closing parenthesis
                line = line.rstrip() + ')'
            
            # Fix Selection fields that have wrong structure
            if 'fields.Selection([' in line and '])' in line:
                # Replace ]) with ), string='Selection')
                line = re.sub(r'\]\)', ', string=\'Selection\')', line)
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Test syntax
            result = subprocess.run(['python3', '-m', 'py_compile', file_path], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Fixed: {file_path}")
                return True
            else:
                print(f"⚠️  Partial fix: {file_path} - {result.stderr.strip()}")
                return False
        else:
            print(f"🔄 No changes: {file_path}")
            return True
            
    except Exception as e:
        print(f"❌ Error: {file_path} - {e}")
        return False

def main():
    """Fix the critical files first"""
    critical_files = [
        'records_management/models/naid_destruction_record.py',
        'records_management/models/advanced_billing.py',
        'records_management/models/records_approval_step.py',
        'records_management/models/hr_employee.py',
        'records_management/models/records_box.py',
        'records_management/models/records_box_movement.py',
        'records_management/models/department_billing.py',
        'records_management/models/records_chain_of_custody.py',
        'records_management/models/records_deletion_request.py',
        'records_management/models/records_retention_policy.py',
        'records_management/models/customer_feedback.py'
    ]
    
    print("🔧 Advanced Syntax Fixing - Critical Files")
    print("=" * 50)
    
    fixed_count = 0
    for file_path in critical_files:
        if os.path.exists(file_path):
            if fix_file_manually(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n📊 Fixed {fixed_count}/{len(critical_files)} critical files")
    
    # Now test all critical files
    print("\n🔍 Testing critical files...")
    all_good = True
    for file_path in critical_files:
        if os.path.exists(file_path):
            result = subprocess.run(['python3', '-m', 'py_compile', file_path], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ {file_path}: {result.stderr.strip()}")
                all_good = False
    
    if all_good:
        print("🎉 All critical files have valid syntax!")
    else:
        print("⚠️  Some critical files still need manual fixing")

if __name__ == "__main__":
    main()
