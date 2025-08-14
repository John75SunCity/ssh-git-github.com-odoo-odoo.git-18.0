#!/usr/bin/env python3
"""
Update Manifest File with New Report Names

This script updates the __manifest__.py file to reflect the renamed report files
that now follow proper Odoo naming conventions (_reports.xml, _templates.xml, etc.)
"""

import os
import re
from pathlib import Path

def update_manifest_file():
    """Update manifest file with new report names"""
    
    manifest_path = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/__manifest__.py")
    report_dir = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/report")
    
    if not manifest_path.exists() or not report_dir.exists():
        print("❌ Manifest file or report directory not found!")
        return
    
    print("🔧 UPDATING MANIFEST FILE WITH NEW REPORT NAMES")
    print("=" * 60)
    
    # Read current manifest content
    with open(manifest_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get list of actual report files that exist
    existing_reports = []
    for xml_file in report_dir.glob("*.xml"):
        existing_reports.append(xml_file.name)
    
    existing_reports.sort()  # Sort for consistent output
    
    print(f"📁 Found {len(existing_reports)} XML report files")
    
    # Find all report references in manifest
    report_pattern = r'"reports?/([^"]+\.xml)"'
    matches = re.findall(report_pattern, content)
    
    print(f"📋 Found {len(matches)} report references in manifest")
    
    updates_made = 0
    not_found = []
    
    # Update each report reference
    updated_content = content
    for old_filename in matches:
        # Check if this file was renamed and exists in new form
        base_name = old_filename.replace('.xml', '')
        
        # Try different naming patterns
        possible_names = [
            f"{base_name}s.xml",           # Add 's' (most common)
            f"{base_name}_reports.xml",    # Change _report to _reports
            f"{base_name}_templates.xml",  # Change _report to _templates
            old_filename                   # Keep original if it exists
        ]
        
        new_filename = None
        for possible in possible_names:
            if possible in existing_reports:
                new_filename = possible
                break
        
        if new_filename and new_filename != old_filename:
            # Update the reference in manifest
            old_ref = f'"reports/{old_filename}"'
            new_ref = f'"report/{new_filename}"'
            
            if old_ref in updated_content:
                updated_content = updated_content.replace(old_ref, new_ref)
                print(f"✅ {old_filename} → {new_filename}")
                updates_made += 1
        elif new_filename == old_filename:
            # File exists with same name, just update directory
            old_ref = f'"reports/{old_filename}"'
            new_ref = f'"report/{old_filename}"'
            
            if old_ref in updated_content:
                updated_content = updated_content.replace(old_ref, new_ref)
                print(f"📁 {old_filename} - Updated directory only")
                updates_made += 1
        else:
            # File not found
            not_found.append(old_filename)
            print(f"⚠️ {old_filename} - File not found in report directory")
    
    # Write updated content back to manifest
    if updates_made > 0:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"\n✅ Manifest file updated with {updates_made} changes")
    else:
        print(f"\n✅ No updates needed in manifest file")
    
    if not_found:
        print(f"\n⚠️ FILES NOT FOUND ({len(not_found)}):")
        for filename in not_found:
            print(f"   - {filename}")
        print("\nConsider removing these references if the files are no longer needed.")
    
    print(f"\n📊 SUMMARY:")
    print(f"✅ References updated: {updates_made}")
    print(f"⚠️ References not found: {len(not_found)}")
    print(f"📁 Total report files: {len(existing_reports)}")
    
    return updates_made, not_found

if __name__ == "__main__":
    updates, missing = update_manifest_file()
    
    if updates > 0:
        print(f"\n🎯 Manifest update complete!")
        print(f"💡 NEXT STEPS:")
        print(f"1. Review the updated manifest file")
        print(f"2. Test module installation/upgrade")
        print(f"3. Verify all reports are accessible")
        
        if missing:
            print(f"4. Consider removing references to missing files")
