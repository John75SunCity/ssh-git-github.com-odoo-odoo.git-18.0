#!/usr/bin/env python3
"""
Fix Field Definition Syntax Errors

This script specifically fixes broken field definitions caused by auto-formatters
that move help parameters outside of field definition parentheses.
"""

import re
from pathlib import Path

def fix_field_definition_syntax(file_path):
    """Fix field definitions with misplaced help parameters."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match broken field definitions like:
    # field = fields.Type(...,)
    #     help="...",
    # ),
    
    # Step 1: Fix the immediate syntax issue with help parameter outside parentheses
    pattern1 = r'(\w+\s*=\s*fields\.\w+\([^)]*),\)\s*\n\s+help="([^"]*)",\s*\n\s*\),'
    replacement1 = r'\1,\n        help="\2",\n    )'
    
    content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE)
    
    # Step 2: Fix trailing commas outside field definitions
    pattern2 = r'(\w+\s*=\s*fields\.\w+\([^)]*\)),\s*\n\s+help="([^"]*)",\s*\n\s*\),'
    replacement2 = r'\1,\n        help="\2",\n    )'
    
    content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE)
    
    # Step 3: Fix any remaining broken field structures
    pattern3 = r'(\w+\s*=\s*fields\.\w+\([^)]*),\)\s*\n(\s+)help="([^"]*)",\s*\n\s*\),'
    replacement3 = r'\1,\n\2help="\3",\n    )'
    
    content = re.sub(pattern3, replacement3, content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def main():
    files_to_fix = [
        'service_item.py',
        'shredding_hard_drive.py',
        'portal_feedback_support_models.py',
        'processing_log.py',
        'paper_bale.py',
        'shredding_team.py',
        'shredding_inventory_item.py',
        'records_vehicle.py',
        'unlock_service_history.py',
        'records_access_log.py',
        'temp_inventory.py',
        'pickup_route.py',
        'records_document_type.py',
        'records_container_movement.py'
    ]
    
    models_path = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models")
    
    print("🔧 FIXING FIELD DEFINITION SYNTAX ERRORS")
    print("=" * 50)
    
    fixed_count = 0
    
    for filename in files_to_fix:
        file_path = models_path / filename
        if file_path.exists():
            if fix_field_definition_syntax(file_path):
                print(f"✅ Fixed: {filename}")
                fixed_count += 1
            else:
                print(f"ℹ️  No changes: {filename}")
        else:
            print(f"❌ Not found: {filename}")
    
    print(f"\n📊 Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
