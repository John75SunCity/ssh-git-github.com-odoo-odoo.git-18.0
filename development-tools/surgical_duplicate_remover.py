#!/usr/bin/env python3
"""
Surgical Duplicate Field Remover for Records Management module
Safely removes duplicate field definitions that cause KeyError issues
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the file before modification"""
    backup_dir = Path('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/development-tools/backups')
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{file_path.name}.backup_{timestamp}"
    backup_path = backup_dir / backup_name
    
    shutil.copy2(file_path, backup_path)
    return backup_path

def analyze_field_duplicates(file_path):
    """Analyze duplicate fields and determine which ones to remove"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find all field definitions with full context
    field_pattern = r'(\w+)\s*=\s*fields\.(\w+)'
    field_occurrences = {}
    
    for line_num, line in enumerate(lines):
        matches = re.findall(field_pattern, line.strip())
        for field_name, field_type in matches:
            if field_name not in field_occurrences:
                field_occurrences[field_name] = []
            field_occurrences[field_name].append({
                'line_num': line_num + 1,
                'line_index': line_num,
                'field_type': field_type,
                'line_content': line.strip(),
                'full_line': line
            })
    
    # Find duplicates
    duplicates_to_remove = []
    for field_name, occurrences in field_occurrences.items():
        if len(occurrences) > 1:
            # Keep the first occurrence, mark others for removal
            for i in range(1, len(occurrences)):
                duplicates_to_remove.append(occurrences[i])
    
    return duplicates_to_remove, lines

def remove_duplicate_fields(file_path):
    """Remove duplicate field definitions from a file"""
    duplicates_to_remove, lines = analyze_field_duplicates(file_path)
    
    if not duplicates_to_remove:
        return False, []
    
    # Create backup
    backup_path = backup_file(file_path)
    print(f"   📁 Backup created: {backup_path.name}")
    
    # Sort duplicates by line number in reverse order to maintain line indices
    duplicates_to_remove.sort(key=lambda x: x['line_index'], reverse=True)
    
    removed_info = []
    
    # Remove duplicate lines
    for duplicate in duplicates_to_remove:
        line_index = duplicate['line_index']
        field_name = duplicate['line_content'].split('=')[0].strip()
        
        # Check if this line might be part of a multi-line field definition
        # Look ahead to see if next lines are continuations
        lines_to_remove = [line_index]
        
        # Check for multi-line field definitions (lines with opening parentheses)
        if '(' in lines[line_index] and ')' not in lines[line_index]:
            # This is a multi-line field, find the closing parenthesis
            for next_line_idx in range(line_index + 1, min(line_index + 10, len(lines))):
                lines_to_remove.append(next_line_idx)
                if ')' in lines[next_line_idx]:
                    break
        
        # Remove the lines (in reverse order to maintain indices)
        for remove_idx in reversed(lines_to_remove):
            removed_line = lines.pop(remove_idx)
            removed_info.append({
                'field_name': field_name,
                'line_num': remove_idx + 1,
                'content': removed_line.strip()
            })
    
    # Write the cleaned content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    return True, removed_info

def main():
    """Main function to remove duplicate fields from all problematic files"""
    models_dir = Path('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models')
    
    print("🔧 SURGICAL DUPLICATE FIELD REMOVER")
    print("=" * 60)
    print("⚠️  This will modify files and create backups")
    print("=" * 60)
    
    # Files with known duplicates (from previous scan)
    problematic_files = [
        'advanced_billing.py', 'records_box.py', 'records_box_movement.py',
        'records_chain_of_custody.py', 'records_deletion_request.py',
        'barcode_models.py', 'barcode_product.py', 'naid_compliance.py',
        'survey_improvement_action.py', 'billing_automation.py',
        'document_retrieval_work_order.py', 'shredding_rates.py',
        'billing_models.py', 'naid_custody.py', 'naid_audit.py',
        'stock_lot.py', 'product.py', 'shredding_inventory.py',
        'shredding_bin_models.py', 'fsm_task.py', 'records_approval_workflow.py',
        'portal_request.py', 'shredding_service.py', 'work_order_shredding.py',
        'hr_employee_naid.py', 'records_retention_policy.py',
        'records_document.py', 'visitor_pos_wizard.py',
        'records_department_billing_contact.py', 'pickup_request.py',
        'customer_inventory_report.py'
    ]
    
    total_files_processed = 0
    total_duplicates_removed = 0
    processed_files = []
    
    for filename in problematic_files:
        file_path = models_dir / filename
        if not file_path.exists():
            print(f"⚠️  File not found: {filename}")
            continue
        
        print(f"\n🔍 Processing: {filename}")
        
        try:
            modified, removed_info = remove_duplicate_fields(file_path)
            
            if modified:
                total_files_processed += 1
                duplicates_count = len(removed_info)
                total_duplicates_removed += duplicates_count
                processed_files.append((filename, duplicates_count))
                
                print(f"   ✅ Removed {duplicates_count} duplicate fields:")
                for info in removed_info:
                    print(f"      - Line {info['line_num']}: {info['field_name']}")
            else:
                print(f"   ✅ No duplicates found (already clean)")
                
        except Exception as e:
            print(f"   ❌ Error processing {filename}: {e}")
    
    print("\n" + "=" * 60)
    print("📊 SURGERY COMPLETE!")
    print(f"   Files processed: {total_files_processed}")
    print(f"   Total duplicates removed: {total_duplicates_removed}")
    print(f"   Backups created in: development-tools/backups/")
    
    if processed_files:
        print(f"\n🎯 Modified files:")
        for filename, count in processed_files:
            print(f"   - {filename}: {count} duplicates removed")
    
    print("\n🔬 Next steps:")
    print("   1. Test module installation: ./odoo-bin -d records_management -i records_management")
    print("   2. Check for any remaining KeyError issues")
    print("   3. If issues persist, check the backups in development-tools/backups/")

if __name__ == "__main__":
    main()
