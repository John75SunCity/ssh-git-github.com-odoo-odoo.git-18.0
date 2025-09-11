#!/usr/bin/env python3
"""
Rename Report Files to Follow Odoo Naming Conventions

This script renames report XML files to follow proper Odoo conventions:
- _reports.xml (plural) for multiple report definitions
- _report_views.xml for report view definitions  
- _templates.xml for QWeb report templates

Based on Odoo guidelines and content analysis.
"""

import os
import re
import shutil
from pathlib import Path

def analyze_file_content(filepath):
    """Analyze file content to determine appropriate naming convention"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count different types of elements
        report_actions = len(re.findall(r'<record[^>]+model="ir\.actions\.report"', content))
        qweb_templates = len(re.findall(r'<template[^>]+id=', content))
        report_views = len(re.findall(r'<record[^>]+model="ir\.ui\.view".*report', content, re.IGNORECASE))
        
        # Decision logic based on content
        if qweb_templates > 0 and report_actions == 0:
            return "_templates.xml"  # Pure QWeb templates
        elif report_views > 0:
            return "_report_views.xml"  # Report view definitions
        elif report_actions > 1:
            return "_reports.xml"  # Multiple report actions (plural)
        elif report_actions == 1:
            return "_reports.xml"  # Single report action (still use plural per Odoo convention)
        else:
            return "_reports.xml"  # Default to reports (plural)
            
    except Exception as e:
        print(f"⚠️ Error analyzing {filepath}: {e}")
        return "_reports.xml"  # Default fallback

def get_new_filename(current_name, content_analysis):
    """Generate new filename based on current name and content analysis"""
    
    # Remove current extensions
    base_name = current_name
    if base_name.endswith('.xml'):
        base_name = base_name[:-4]
    
    # Remove existing suffixes that we might replace
    suffixes_to_remove = [
        '_report', '_reports', '_report_views', '_templates', 
        '_template', '_view', '_views'
    ]
    
    for suffix in suffixes_to_remove:
        if base_name.endswith(suffix):
            base_name = base_name[:-len(suffix)]
            break
    
    # Apply new suffix based on content analysis
    return base_name + content_analysis

def rename_report_files():
    """Rename all report files to follow Odoo conventions"""
    
    report_dir = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/report")
    
    if not report_dir.exists():
        print("❌ Report directory not found!")
        return
    
    print("🔧 RENAMING REPORT FILES TO FOLLOW ODOO CONVENTIONS")
    print("=" * 60)
    
    xml_files = list(report_dir.glob("*.xml"))
    renamed_count = 0
    skipped_count = 0
    
    # Track renames for updating references
    rename_mapping = {}
    
    for xml_file in xml_files:
        current_name = xml_file.name
        
        # Skip __init__.py and already correctly named files
        if current_name == "__init__.py":
            continue
            
        # Check if already follows convention
        if (current_name.endswith('_reports.xml') or 
            current_name.endswith('_report_views.xml') or 
            current_name.endswith('_templates.xml')):
            print(f"✅ {current_name} - Already correctly named")
            skipped_count += 1
            continue
        
        # Analyze content to determine proper suffix
        content_suffix = analyze_file_content(xml_file)
        new_name = get_new_filename(current_name, content_suffix)
        
        # Check if rename is needed
        if new_name == current_name:
            print(f"✅ {current_name} - No change needed")
            skipped_count += 1
            continue
        
        # Perform the rename
        new_path = report_dir / new_name
        
        # Check if target already exists
        if new_path.exists():
            print(f"⚠️ {current_name} - Target {new_name} already exists, skipping")
            skipped_count += 1
            continue
        
        try:
            xml_file.rename(new_path)
            print(f"✅ {current_name} → {new_name}")
            rename_mapping[current_name] = new_name
            renamed_count += 1
            
        except Exception as e:
            print(f"❌ Failed to rename {current_name}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY:")
    print(f"✅ Files renamed: {renamed_count}")
    print(f"⏭️ Files skipped (already correct): {skipped_count}")
    print(f"📁 Total XML files processed: {len(xml_files)}")
    
    if rename_mapping:
        print(f"\n📝 RENAMES PERFORMED:")
        for old_name, new_name in sorted(rename_mapping.items()):
            print(f"   {old_name} → {new_name}")
    
    # Update __init__.py if it exists and has imports
    init_file = report_dir / "__init__.py"
    if init_file.exists() and rename_mapping:
        update_init_file(init_file, rename_mapping)
    
    print(f"\n🎯 Report file renaming complete!")
    return rename_mapping

def update_init_file(init_file, rename_mapping):
    """Update __init__.py file with new filenames"""
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        updated_content = content
        updates_made = 0
        
        for old_name, new_name in rename_mapping.items():
            # Remove .xml extension for import statements
            old_module = old_name.replace('.xml', '')
            new_module = new_name.replace('.xml', '')
            
            # Update import statements
            import_patterns = [
                f"from . import {old_module}",
                f"import {old_module}",
                f'"{old_module}"',
                f"'{old_module}'"
            ]
            
            for pattern in import_patterns:
                if pattern in updated_content:
                    new_pattern = pattern.replace(old_module, new_module)
                    updated_content = updated_content.replace(pattern, new_pattern)
                    updates_made += 1
        
        if updates_made > 0:
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"✅ Updated __init__.py with {updates_made} import changes")
        else:
            print("ℹ️ No import updates needed in __init__.py")
            
    except Exception as e:
        print(f"⚠️ Could not update __init__.py: {e}")

if __name__ == "__main__":
    rename_mapping = rename_report_files()
    
    if rename_mapping:
        print(f"\n💡 NEXT STEPS:")
        print(f"1. Check that all renames are correct")
        print(f"2. Update any references to these files in other modules")
        print(f"3. Test that reports still work correctly")
        print(f"4. Consider updating manifest dependencies if needed")
