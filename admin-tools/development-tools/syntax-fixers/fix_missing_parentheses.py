#!/usr/bin/env python3
"""
Fix Missing Parentheses and Commas in Field Definitions

This script identifies and fixes common syntax errors in Odoo model files:
- Missing closing parentheses in field definitions
- Missing commas after field definitions
- Mismatched parentheses in complex field definitions

Focuses on the 40 files identified by the syntax error scanner.
"""

import os
import re
import ast
import sys
from pathlib import Path


def check_python_syntax(content):
    """Check if Python code has valid syntax"""
    try:
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, str(e)


def fix_field_definition_syntax(content):
    """Fix common field definition syntax errors"""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Pattern 1: Field definition with missing closing parenthesis
        if re.search(r'^\s*\w+\s*=\s*fields\.\w+\(', line):
            # Look ahead for the closing pattern
            field_lines = [line]
            j = i + 1
            paren_count = line.count('(') - line.count(')')
            
            while j < len(lines) and paren_count > 0:
                next_line = lines[j]
                field_lines.append(next_line)
                paren_count += next_line.count('(') - next_line.count(')')
                j += 1
            
            # If we never closed the parentheses, add closing
            if paren_count > 0:
                # Find the last meaningful line (not just whitespace)
                last_meaningful_idx = len(field_lines) - 1
                while last_meaningful_idx > 0 and field_lines[last_meaningful_idx].strip() == '':
                    last_meaningful_idx -= 1
                
                # Add missing closing parenthesis
                if not field_lines[last_meaningful_idx].rstrip().endswith(')'):
                    field_lines[last_meaningful_idx] = field_lines[last_meaningful_idx].rstrip() + ')'
            
            # Check if we need a comma after the field definition
            if j < len(lines):
                next_non_empty = j
                while next_non_empty < len(lines) and lines[next_non_empty].strip() == '':
                    next_non_empty += 1
                
                if next_non_empty < len(lines):
                    next_line = lines[next_non_empty].strip()
                    # If next line is another field definition or method, we need a comma
                    if (re.match(r'\w+\s*=\s*fields\.', next_line) or 
                        next_line.startswith('def ') or
                        next_line.startswith('@')):
                        
                        # Add comma if not present
                        last_line = field_lines[-1]
                        if not last_line.rstrip().endswith(','):
                            field_lines[-1] = last_line.rstrip() + ','
            
            fixed_lines.extend(field_lines)
            i = j
        else:
            fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines)


def fix_specific_patterns(content):
    """Fix specific syntax patterns found in error analysis"""
    
    # Pattern 1: Selection field with missing closing bracket and parenthesis
    content = re.sub(
        r'(fields\.Selection\(\[\s*(?:\([^)]+\),?\s*)*)\n(\s*)(\w+\s*=)',
        r'\1], string="Selection")\n\2\3',
        content,
        flags=re.MULTILINE
    )
    
    # Pattern 2: Many2one field with missing closing parenthesis
    content = re.sub(
        r'(fields\.Many2one\([^)]*string="[^"]*"[^)]*)\n(\s*)(\w+\s*=)',
        r'\1)\n\2\3',
        content,
        flags=re.MULTILINE
    )
    
    # Pattern 3: Text/Char fields with missing closing parenthesis
    content = re.sub(
        r'(fields\.(Char|Text|Boolean|Float|Integer)\([^)]*)\n(\s*)(\w+\s*=)',
        r'\1)\n\3\4',
        content,
        flags=re.MULTILINE
    )
    
    return content


def fix_file_syntax(file_path):
    """Fix syntax errors in a specific Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Check original syntax
        is_valid, error = check_python_syntax(original_content)
        if is_valid:
            print(f"✅ {file_path.name}: Already valid")
            return True, "Already valid"
        
        print(f"🔧 {file_path.name}: Fixing syntax error: {error}")
        
        # Apply fixes
        fixed_content = original_content
        fixed_content = fix_field_definition_syntax(fixed_content)
        fixed_content = fix_specific_patterns(fixed_content)
        
        # Check if fixes worked
        is_valid_after, error_after = check_python_syntax(fixed_content)
        
        if is_valid_after:
            # Write fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"✅ {file_path.name}: Fixed successfully")
            return True, "Fixed"
        else:
            print(f"❌ {file_path.name}: Fix failed: {error_after}")
            return False, f"Fix failed: {error_after}"
            
    except Exception as e:
        print(f"❌ {file_path.name}: Exception during fix: {e}")
        return False, f"Exception: {e}"


def main():
    """Main function to fix all identified syntax error files"""
    
    # Files with syntax errors from the scan
    error_files = [
        "stock_lot_attribute_value.py", "document_retrieval_item.py", "advanced_billing.py",
        "partner_bin_key.py", "revenue_forecaster.py", "customer_negotiated_rates.py",
        "records_deletion_request.py", "barcode_product.py", "records_management_base_menus.py",
        "service_item.py", "shredding_hard_drive.py", "processing_log.py",
        "shredding_certificate.py", "paper_bale.py", "records_container_type_converter.py",
        "photo.py", "shredding_inventory_item.py", "bin_unlock_service.py",
        "shred_bins.py", "shredding_inventory.py", "paper_load_shipment.py",
        "fsm_task.py", "portal_request.py", "shredding_service.py",
        "hr_employee_naid.py", "records_retention_policy.py", "records_vehicle.py",
        "unlock_service_history.py", "records_container_type.py", "records_access_log.py",
        "records_document.py", "records_billing_contact.py", "temp_inventory.py",
        "signed_document.py", "shredding_equipment.py", "pickup_request.py",
        "pickup_route.py", "naid_certificate.py", "records_document_type.py",
        "transitory_field_config.py"
    ]
    
    models_dir = Path("records_management/models")
    
    if not models_dir.exists():
        print(f"❌ Models directory not found: {models_dir}")
        return
    
    print("🚀 Starting comprehensive syntax error fix...")
    print(f"📁 Scanning directory: {models_dir}")
    print(f"🎯 Target files: {len(error_files)}")
    print("=" * 70)
    
    results = {
        'fixed': [],
        'already_valid': [],
        'failed': [],
        'not_found': []
    }
    
    for filename in error_files:
        file_path = models_dir / filename
        
        if not file_path.exists():
            print(f"⚠️  {filename}: File not found")
            results['not_found'].append(filename)
            continue
        
        success, message = fix_file_syntax(file_path)
        
        if success:
            if message == "Already valid":
                results['already_valid'].append(filename)
            else:
                results['fixed'].append(filename)
        else:
            results['failed'].append((filename, message))
    
    print("=" * 70)
    print("📊 SUMMARY:")
    print(f"✅ Fixed: {len(results['fixed'])}")
    print(f"✅ Already Valid: {len(results['already_valid'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"⚠️  Not Found: {len(results['not_found'])}")
    
    if results['fixed']:
        print(f"\n🎉 Successfully fixed {len(results['fixed'])} files:")
        for filename in results['fixed']:
            print(f"  - {filename}")
    
    if results['failed']:
        print(f"\n💥 Failed to fix {len(results['failed'])} files:")
        for filename, error in results['failed']:
            print(f"  - {filename}: {error}")
    
    total_success = len(results['fixed']) + len(results['already_valid'])
    total_attempted = len(error_files) - len(results['not_found'])
    
    if total_attempted > 0:
        success_rate = (total_success / total_attempted) * 100
        print(f"\n📈 Success Rate: {success_rate:.1f}% ({total_success}/{total_attempted})")
    
    return len(results['failed']) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
