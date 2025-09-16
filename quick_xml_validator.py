#!/usr/bin/env python3
"""
Quick XML Validation for Critical Records Management Files
"""

import xml.etree.ElementTree as ET
import re
import os

def validate_fontawesome_icons(file_path):
    """Check if all FontAwesome icons have required title attributes"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find FontAwesome icons
    fa_pattern = r'<i[^>]*class="[^"]*fa\s+fa-([^"]*)"[^>]*>'
    fa_matches = re.finditer(fa_pattern, content)
    
    issues = []
    for match in fa_matches:
        icon_tag = match.group(0)
        icon_name = match.group(1)
        
        # Skip decorative icons with aria-hidden="true" - they should NOT have title attributes
        if 'aria-hidden="true"' in icon_tag:
            continue
            
        # Check if interactive icon has title attribute
        if 'title=' not in icon_tag:
            issues.append(f"Interactive FontAwesome icon 'fa-{icon_name}' missing title attribute")
    
    return issues

def validate_xml_syntax(file_path):
    """Validate XML syntax and structure"""
    try:
        tree = ET.parse(file_path)
        return []
    except ET.ParseError as e:
        return [f"XML Parse Error: {e}"]

def validate_critical_files():
    """Validate the most critical XML files"""
    critical_files = [
        "records_management/views/records_location_views.xml",
        "records_management/views/records_container_views.xml", 
        "records_management/views/portal_request_views.xml",
        "records_management/views/destruction_certificate_views.xml",
        "records_management/views/naid_audit_log_views.xml",
        "records_management/views/customer_feedback_views.xml"
    ]
    
    results = []
    total_issues = 0
    
    print("🎯 CRITICAL FILES VALIDATION")
    print("=" * 50)
    
    for file_path in critical_files:
        if not os.path.exists(file_path):
            print(f"⚠️  {file_path} - FILE NOT FOUND")
            continue
        
        fa_issues = validate_fontawesome_icons(file_path)
        xml_issues = validate_xml_syntax(file_path)
        
        file_issues = len(fa_issues) + len(xml_issues)
        total_issues += file_issues
        
        if file_issues == 0:
            print(f"✅ {file_path} - PASSED")
        else:
            print(f"❌ {file_path} - {file_issues} issues")
            for issue in fa_issues:
                print(f"   🎨 {issue}")
            for issue in xml_issues:
                print(f"   📝 {issue}")
    
    print("\n" + "=" * 50)
    if total_issues == 0:
        print("🎉 ALL CRITICAL FILES VALIDATED SUCCESSFULLY!")
    else:
        print(f"⚠️  {total_issues} issues found in critical files")
    
    return total_issues

if __name__ == "__main__":
    validate_critical_files()
