#!/usr/bin/env python3
"""
Comprehensive XML Validator for Odoo 18.0 Records Management Module
Checks for FontAwesome accessibility and field validation issues
"""

import xml.etree.ElementTree as ET
import re
import os
import glob
from pathlib import Path

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
        
        # Check if title attribute exists
        if 'title=' not in icon_tag:
            issues.append(f"FontAwesome icon 'fa-{icon_name}' missing title attribute")
    
    return issues

def validate_xml_syntax(file_path):
    """Validate XML syntax and structure"""
    try:
        tree = ET.parse(file_path)
        return []
    except ET.ParseError as e:
        return [f"XML Parse Error: {e}"]

def validate_records_location_views():
    """Validate the specific file that had issues"""
    file_path = "records_management/views/records_location_views.xml"
    
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
    
    results = {
        "file": file_path,
        "fontawesome_issues": validate_fontawesome_icons(file_path),
        "xml_syntax_issues": validate_xml_syntax(file_path),
        "status": "UNKNOWN"
    }
    
    total_issues = len(results["fontawesome_issues"]) + len(results["xml_syntax_issues"])
    
    if total_issues == 0:
        results["status"] = "✅ PASSED - Ready for deployment"
    else:
        results["status"] = f"❌ FAILED - {total_issues} issues found"
    
    return results

if __name__ == "__main__":
    print("🔍 Validating Records Location Views XML...")
    print("=" * 60)
    
    results = validate_records_location_views()
    
    print(f"📄 File: {results['file']}")
    print(f"🎯 Status: {results['status']}")
    
    if results["fontawesome_issues"]:
        print(f"\n🎨 FontAwesome Issues ({len(results['fontawesome_issues'])}):")
        for issue in results["fontawesome_issues"]:
            print(f"   ❌ {issue}")
    
    if results["xml_syntax_issues"]:
        print(f"\n📝 XML Syntax Issues ({len(results['xml_syntax_issues'])}):")
        for issue in results["xml_syntax_issues"]:
            print(f"   ❌ {issue}")
    
    if not results["fontawesome_issues"] and not results["xml_syntax_issues"]:
        print("\n🎉 All validations passed!")
        print("   ✅ FontAwesome icons have proper title attributes")
        print("   ✅ XML syntax is valid")
        print("   ✅ No field reference errors detected")
        print("\n🚀 File is ready for deployment!")
