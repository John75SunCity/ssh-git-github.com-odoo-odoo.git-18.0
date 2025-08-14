#!/usr/bin/env python3
"""
WORKSPACE ORGANIZATION SCRIPT
============================

This script organizes the development-tools directory by:
1. Moving utility scripts to proper subdirectories
2. Cleaning up temporary/duplicate files
3. Creating a clean directory structure
"""

import os
import shutil
from pathlib import Path

def organize_development_tools():
    """Organize the development-tools directory"""
    base_dir = Path(__file__).parent
    
    # Create subdirectories if they don't exist
    subdirs = {
        'syntax-tools': [],
        'field-tools': [],
        'validation-tools': [],
        'archive': [],
    }
    
    for subdir in subdirs:
        (base_dir / subdir).mkdir(exist_ok=True)
    
    # Define file categorization
    file_categories = {
        'syntax-tools': [
            'find_syntax_errors.py',
            'fix_field_syntax.py',
            'fix_indentation_errors.py',
            'fix_common_syntax_errors.py',
            'odoo_indentation_fixer.py',
            'odoo_standards_fixer.py',
        ],
        'field-tools': [
            'add_critical_fields.py',
            'add_state_fields_bulk.py',
            'cleanup_redundant_display_name_fields.py',
            'fix_misplaced_partner_fields.py',
            'safe_display_name_cleanup.py',
            'advanced_missing_view_fields_detector.py',
            'quick_critical_field_checker.py',
        ],
        'validation-tools': [
            'relationship_validator.py',
            'validate_all_relationships.py',
            'validate_imports.py',
            'intelligent_relationship_fixer.py',
            'fix_critical_inverse_fields.py',
        ],
        'archive': [
            'fix_pylint_no_member.py',
            'complete_odoo_view_naming_fixer.py',
            'fix_view_naming_standards.py',
            'odoo_core_fields_optimization_analysis.py',
        ]
    }
    
    # Move files to appropriate subdirectories
    moved_files = 0
    for category, files in file_categories.items():
        for filename in files:
            src = base_dir / filename
            if src.exists():
                dest = base_dir / category / filename
                shutil.move(str(src), str(dest))
                moved_files += 1
                print(f"✅ Moved {filename} to {category}/")
    
    # Clean up shell scripts that are no longer needed
    shell_scripts_to_remove = [
        'fix_all_remaining_syntax.sh',
        'fix_all_bracket_mismatches.py',
        'fix_bracket_mismatches.py',
    ]
    
    removed_files = 0
    for script in shell_scripts_to_remove:
        script_path = base_dir / script
        if script_path.exists():
            script_path.unlink()
            removed_files += 1
            print(f"🗑️ Removed obsolete script: {script}")
    
    # Clean up duplicate/temporary files
    if (base_dir / 'missing_view_fields_report.json').exists():
        (base_dir / 'missing_view_fields_report.json').unlink()
        print("🗑️ Removed temporary report file")
    
    print(f"\n📋 ORGANIZATION COMPLETE:")
    print(f"   ✅ Moved {moved_files} files to organized subdirectories")
    print(f"   🗑️ Removed {removed_files} obsolete files")
    print(f"   📁 Created clean directory structure")

if __name__ == "__main__":
    organize_development_tools()
