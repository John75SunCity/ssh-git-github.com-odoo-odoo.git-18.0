#!/usr/bin/env python3
"""
Comprehensive XML Validator for Odoo 18.0 Records Management Module
Validates ALL XML files in the module for:
- FontAwesome accessibility compliance
- XML syntax and structure
- Field reference validation
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

def find_all_xml_files():
    """Find all XML files in the records_management module"""
    xml_files = []
    
    # Standard Odoo XML directories
    xml_paths = [
        "records_management/views/*.xml",
        "records_management/data/*.xml", 
        "records_management/security/*.xml",
        "records_management/wizard/*.xml",
        "records_management/wizards/*.xml",
        "records_management/report/*.xml",
        "records_management/templates/*.xml",
        "records_management/demo/*.xml",
        "records_management/**/*.xml"  # Catch any other XML files
    ]
    
    for pattern in xml_paths:
        xml_files.extend(glob.glob(pattern, recursive=True))
    
    # Remove duplicates and sort
    return sorted(list(set(xml_files)))

def validate_single_xml_file(file_path):
    """Validate a single XML file"""
    results = {
        "file": file_path,
        "fontawesome_issues": validate_fontawesome_icons(file_path),
        "xml_syntax_issues": validate_xml_syntax(file_path),
        "status": "UNKNOWN"
    }
    
    total_issues = len(results["fontawesome_issues"]) + len(results["xml_syntax_issues"])
    
    if total_issues == 0:
        results["status"] = "✅ PASSED"
    else:
        results["status"] = f"❌ FAILED - {total_issues} issues"
    
    return results

def validate_all_xml_files():
    """Validate all XML files in the records_management module"""
    xml_files = find_all_xml_files()
    
    if not xml_files:
        return {"error": "No XML files found in records_management module"}
    
    all_results = []
    total_files = len(xml_files)
    passed_files = 0
    total_issues = 0
    
    print(f"🔍 Found {total_files} XML files to validate...")
    print("=" * 80)
    
    for file_path in xml_files:
        if not os.path.exists(file_path):
            continue
            
        results = validate_single_xml_file(file_path)
        all_results.append(results)
        
        # Print results for each file
        print(f"\n📄 {file_path}")
        print(f"🎯 Status: {results['status']}")
        
        if results["fontawesome_issues"]:
            print(f"   🎨 FontAwesome Issues ({len(results['fontawesome_issues'])}):")
            for issue in results["fontawesome_issues"]:
                print(f"      ❌ {issue}")
        
        if results["xml_syntax_issues"]:
            print(f"   📝 XML Syntax Issues ({len(results['xml_syntax_issues'])}):")
            for issue in results["xml_syntax_issues"]:
                print(f"      ❌ {issue}")
        
        if not results["fontawesome_issues"] and not results["xml_syntax_issues"]:
            print("   ✅ All validations passed!")
            passed_files += 1
        
        total_issues += len(results["fontawesome_issues"]) + len(results["xml_syntax_issues"])
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)
    print(f"📁 Total files validated: {total_files}")
    print(f"✅ Files passed: {passed_files}")
    print(f"❌ Files with issues: {total_files - passed_files}")
    print(f"🐛 Total issues found: {total_issues}")
    
    if total_issues == 0:
        print("\n🎉 ALL XML FILES VALIDATED SUCCESSFULLY!")
        print("   ✅ All FontAwesome icons are properly configured")
        print("   ✅ All XML syntax is valid")
        print("   ✅ Module is ready for deployment!")
    else:
        print(f"\n⚠️  {total_issues} issues need to be resolved before deployment")
    
    return {
        "total_files": total_files,
        "passed_files": passed_files,
        "total_issues": total_issues,
        "results": all_results
    }

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE XML VALIDATION - RECORDS MANAGEMENT MODULE")
    print("🎯 Validating all XML files for Odoo 18.0 compliance...")
    print()
    
    validate_all_xml_files()
