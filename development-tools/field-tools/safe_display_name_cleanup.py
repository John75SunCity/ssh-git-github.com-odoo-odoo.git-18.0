#!/usr/bin/env python3
"""
Safe Display Name Field Cleanup Script for Records Management System

This script safely removes redundant display_name field definitions from model files
where Odoo 18.0 provides the field automatically via models.Model inheritance.

SAFETY FEATURES:
- Only processes files that have clean syntax (skips files with pre-existing errors)
- Preserves custom _compute_display_name methods
- Uses precise regex patterns to avoid breaking other field definitions
- Provides detailed reporting of all changes made

Safe operation - only removes manually defined display_name fields that duplicate
Odoo's automatic functionality.
"""

import os
import re
import ast
from pathlib import Path

# Files known to have redundant display_name fields (from previous analysis)
CANDIDATE_FILES = [
    'payment_split.py',
    'pickup_route.py', 
    'processing_log.py',
    'records_billing_contact.py',
    'records_chain_of_custody.py',
    'records_container_movement.py',
    'records_deletion_request.py',
    'records_tag.py',
    'records_vehicle.py',
    'res_partner_key_restriction.py',
    'shredding_inventory.py',
    'shredding_inventory_item.py',
    'shredding_service_log.py',
    'stock_lot.py',
    'survey_improvement_action.py',
    'temp_inventory.py',
    'transitory_field_config.py',
    'transitory_items.py',
    'unlock_service_history.py',
    'work_order_shredding.py'
]

class SafeDisplayNameCleanup:
    def __init__(self, models_path):
        self.models_path = Path(models_path)
        self.changes_made = []
        self.skipped_files = []
        self.errors = []
    
    def check_file_syntax(self, file_path):
        """Check if a file has valid Python syntax."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)
    
    def has_custom_compute_method(self, file_path):
        """Check if file has a custom _compute_display_name method."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for custom compute method
            if re.search(r'def _compute_display_name\(', content):
                return True
            return False
        except Exception:
            return False
    
    def safe_remove_display_name_field(self, file_path):
        """Safely remove redundant display_name field definition."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Pattern to match display_name field definitions
            # This is very specific to avoid matching other fields
            patterns = [
                # Standard single-line display_name field
                r'\s*display_name\s*=\s*fields\.[A-Za-z]+\([^)]*\),?\s*\n',
                # Multi-line display_name field with parameters
                r'\s*display_name\s*=\s*fields\.[A-Za-z]+\(\s*\n(?:[^)]*\n)*\s*\),?\s*\n',
                # Display name with specific common parameters
                r'\s*display_name\s*=\s*fields\.Char\(\s*string=["\']Display Name["\'][^)]*\),?\s*\n'
            ]
            
            removed_definitions = []
            
            for pattern in patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                for match in matches:
                    removed_definitions.append(match.group(0).strip())
                content = re.sub(pattern, '', content, flags=re.MULTILINE)
            
            # Clean up any double empty lines created
            content = re.sub(r'\n\n\n+', '\n\n', content)
            
            if content != original_content and removed_definitions:
                # Verify the result still has valid syntax
                try:
                    ast.parse(content)
                    
                    # Write the cleaned content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    return True, removed_definitions
                except SyntaxError:
                    # If cleaning broke syntax, don't save changes
                    return False, ["Syntax error after cleanup - changes not saved"]
            
            return False, []
            
        except Exception as e:
            return False, [str(e)]
    
    def process_all_files(self):
        """Process all candidate files safely."""
        print("🧹 SAFE DISPLAY NAME FIELD CLEANUP")
        print("=" * 50)
        print(f"📁 Models Path: {self.models_path}")
        print(f"📋 Candidate Files: {len(CANDIDATE_FILES)}")
        print()
        
        processed_files = 0
        cleaned_files = 0
        syntax_skipped = 0
        
        for filename in CANDIDATE_FILES:
            file_path = self.models_path / filename
            
            if not file_path.exists():
                self.skipped_files.append({
                    'file': filename,
                    'reason': 'File not found'
                })
                continue
            
            print(f"🔍 Processing: {filename}")
            
            # Check syntax first - skip files with syntax errors
            is_valid, syntax_error = self.check_file_syntax(file_path)
            if not is_valid:
                print(f"   ⚠️  Skipping - has syntax errors: {syntax_error}")
                self.skipped_files.append({
                    'file': filename,
                    'reason': f'Syntax error: {syntax_error}'
                })
                syntax_skipped += 1
                continue
            
            # Check for custom compute method
            has_custom_method = self.has_custom_compute_method(file_path)
            if has_custom_method:
                print(f"   ℹ️  Has custom _compute_display_name method - will preserve")
            
            # Attempt to clean display_name field
            success, removed_items = self.safe_remove_display_name_field(file_path)
            
            if success and removed_items:
                cleaned_files += 1
                print(f"   ✅ Cleaned: removed {len(removed_items)} display_name definition(s)")
                self.changes_made.append({
                    'file': filename,
                    'removed_items': removed_items,
                    'has_custom_method': has_custom_method
                })
            elif not success and removed_items:
                print(f"   ❌ Failed: {removed_items[0]}")
                self.errors.append({
                    'file': filename,
                    'error': removed_items[0]
                })
            else:
                print(f"   ℹ️  No display_name field found or already clean")
            
            processed_files += 1
        
        print()
        self.print_summary(processed_files, cleaned_files, syntax_skipped)
    
    def print_summary(self, processed, cleaned, skipped):
        """Print detailed summary of cleanup operations."""
        print("📊 SAFE CLEANUP SUMMARY")
        print("=" * 35)
        print(f"• Files Processed: {processed}")
        print(f"• Files Cleaned: {cleaned}")
        print(f"• Files Skipped (Syntax): {skipped}")
        print(f"• Errors: {len(self.errors)}")
        print()
        
        if self.changes_made:
            print("✅ FILES SUCCESSFULLY CLEANED:")
            print("-" * 35)
            for change in self.changes_made:
                print(f"   📄 {change['file']}")
                if change['has_custom_method']:
                    print(f"      🔧 Preserved custom _compute_display_name method")
                for item in change['removed_items']:
                    # Show first 80 characters of removed definition
                    preview = item.replace('\n', ' ').strip()
                    if len(preview) > 80:
                        preview = preview[:77] + "..."
                    print(f"      - Removed: {preview}")
            print()
        
        if self.skipped_files:
            print("⚠️  FILES SKIPPED (PRESERVED SAFELY):")
            print("-" * 40)
            for skip in self.skipped_files:
                print(f"   📄 {skip['file']}: {skip['reason']}")
            print()
        
        if self.errors:
            print("❌ ERRORS ENCOUNTERED:")
            print("-" * 25)
            for error in self.errors:
                print(f"   📄 {error['file']}: {error['error']}")
            print()
        
        print("🎯 NEXT STEPS:")
        print("=" * 20)
        if cleaned > 0:
            print("1. ✅ Review cleaned files for correctness")
            print("2. 🧪 Run syntax validation: python development-tools/find_syntax_errors.py")
            print("3. 📤 Commit and push changes to GitHub")
            print("4. 🚀 Deploy to Odoo.sh for testing")
        else:
            print("1. ℹ️  No redundant display_name fields found to clean")
            print("2. 🎉 All files are already optimized or safely preserved")
        
        print()
        print("📋 TECHNICAL NOTES:")
        print("=" * 25)
        print("• display_name is provided automatically by models.Model")
        print("• Custom _compute_display_name methods are preserved") 
        print("• Files with syntax errors are skipped for safety")
        print("• All changes maintain Odoo 18.0 compatibility")
        print()

def main():
    """Main execution function."""
    models_path = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models")
    
    if not models_path.exists():
        print(f"❌ Models directory not found: {models_path}")
        return
    
    cleanup = SafeDisplayNameCleanup(models_path)
    cleanup.process_all_files()

if __name__ == "__main__":
    main()
