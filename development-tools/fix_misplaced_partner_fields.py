#!/usr/bin/env python3
"""
Systematic fix for misplaced partner_id fields causing syntax errors.

This script identifies and fixes partner_id fields that were incorrectly inserted
in the middle of methods or other code structures during partner_id standardization.
"""
import os
import re
import ast

def check_python_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Other error: {str(e)}"

def find_misplaced_partner_id(file_path):
    """Find misplaced partner_id field definitions in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    misplaced_locations = []
    partner_id_pattern = re.compile(r'^\s*partner_id\s*=\s*fields\.Many2one')
    
    for i, line in enumerate(lines):
        if partner_id_pattern.match(line):
            # Check if this partner_id is in a problematic location
            # Look at the previous few lines to see if it's interrupting something
            context_start = max(0, i - 5)
            context_lines = lines[context_start:i]
            
            # Check for decorators, method definitions, or incomplete structures
            for j, ctx_line in enumerate(context_lines):
                if (ctx_line.strip().startswith('@') or 
                    ctx_line.strip().startswith('def ') or
                    'def ' in ctx_line and ctx_line.endswith(':\n') or
                    ctx_line.strip().endswith(',') or
                    '[' in ctx_line and ']' not in ctx_line):
                    misplaced_locations.append({
                        'line_num': i + 1,
                        'line_content': line.strip(),
                        'context_start': context_start + j + 1,
                        'context': ctx_line.strip()
                    })
                    break
    
    return misplaced_locations

def fix_misplaced_partner_id(file_path):
    """Fix misplaced partner_id field in a Python file."""
    print(f"🔧 Fixing {os.path.basename(file_path)}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Standard partner_id field definition
    partner_field_def = '''    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    )'''
    
    # Remove misplaced partner_id field definitions
    # Pattern to match the entire field definition block
    misplaced_pattern = re.compile(
        r'\n?\s*partner_id\s*=\s*fields\.Many2one\(\s*\n'
        r'\s*"res\.partner",\s*\n'
        r'\s*string="Partner",\s*\n'
        r'\s*help="Associated partner for this record"\s*\n'
        r'\s*\)',
        re.MULTILINE
    )
    
    # Find all misplaced occurrences
    matches = list(misplaced_pattern.finditer(content))
    if not matches:
        print(f"   ❌ No misplaced partner_id found in {os.path.basename(file_path)}")
        return False
    
    # Remove all misplaced instances
    cleaned_content = misplaced_pattern.sub('', content)
    
    # Find where to insert the correct field definition
    # Look for field definition sections
    field_section_patterns = [
        r'(\n\s*#.*?fields.*?\n)',  # Field section comments
        r'(\n\s*active\s*=\s*fields\.Boolean.*?\n)',  # After active field
        r'(\n\s*user_id\s*=\s*fields\.Many2one.*?\n)',  # After user_id field
        r'(\n\s*company_id\s*=\s*fields\.Many2one.*?\n)',  # After company_id field
    ]
    
    field_inserted = False
    for pattern in field_section_patterns:
        if re.search(pattern, cleaned_content, re.DOTALL):
            # Insert after the found pattern
            def add_partner_field(match):
                return match.group(1) + '\n    # Partner Relationship\n' + partner_field_def + '\n'
            
            cleaned_content = re.sub(pattern, add_partner_field, cleaned_content, count=1, flags=re.DOTALL)
            field_inserted = True
            break
    
    if not field_inserted:
        print(f"   ⚠️  Could not find appropriate location for partner_id in {os.path.basename(file_path)}")
        return False
    
    # Write the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    # Verify syntax
    is_valid, error = check_python_syntax(file_path)
    if is_valid:
        print(f"   ✅ Fixed and validated {os.path.basename(file_path)}")
        return True
    else:
        print(f"   ❌ Fix introduced syntax error in {os.path.basename(file_path)}: {error}")
        return False

def main():
    """Main function to fix all files with syntax errors."""
    models_dir = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models'
    
    # List of files with known syntax errors (from the scan)
    error_files = [
        'records_chain_of_custody.py',
        'service_item.py', 
        'shredding_hard_drive.py',
        'portal_feedback_support_models.py',
        'processing_log.py',
        'paper_bale.py',
        'records_location.py',
        'shredding_team.py',
        'paper_bale_recycling.py',
        'shredding_inventory_item.py',
        'records_vehicle.py',
        'unlock_service_history.py',
        'records_access_log.py',
        'temp_inventory.py',
        'signed_document.py',
        'pickup_route.py',
        'records_document_type.py',
        'records_container_movement.py'
    ]
    
    print("🔍 Starting systematic partner_id field fixes...")
    print(f"📋 Processing {len(error_files)} files with syntax errors\n")
    
    fixed_count = 0
    for filename in error_files:
        file_path = os.path.join(models_dir, filename)
        if os.path.exists(file_path):
            if fix_misplaced_partner_id(file_path):
                fixed_count += 1
        else:
            print(f"   ⚠️  File not found: {filename}")
        print()
    
    print(f"✅ Summary: {fixed_count}/{len(error_files)} files fixed successfully")
    print("\n🔍 Run syntax check to verify all fixes...")

if __name__ == "__main__":
    main()
