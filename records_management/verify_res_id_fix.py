#!/usr/bin/env python3
"""
Verification script to ensure all res_id field issues are resolved
"""

import os
import re
import glob

def find_problematic_res_id_fields():
    """
    Find any problematic res_id field definitions that could cause KeyError
    """
    model_files = glob.glob('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/*.py')
    
    problematic_patterns = [
        r'res_id\s*=\s*fields\.',  # Direct field definition
        r'One2many\([^,]+,\s*[\'"]res_id[\'"]',  # One2many with res_id inverse
        r'Many2one\([^,]+,\s*[\'"]res_id[\'"]',  # Many2one with res_id inverse
    ]
    
    issues = []
    
    for file_path in model_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    for pattern in problematic_patterns:
                        if re.search(pattern, line):
                            # Skip commented lines
                            stripped = line.strip()
                            if not stripped.startswith('#'):
                                issues.append({
                                    'file': file_path,
                                    'line': i,
                                    'content': line.strip(),
                                    'pattern': pattern
                                })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return issues

def check_ir_attachment_relationships():
    """
    Check all ir.attachment relationships are properly implemented
    """
    model_files = glob.glob('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/*.py')
    
    attachment_fields = []
    
    for file_path in model_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Look for ir.attachment relationships
                    if "'ir.attachment'" in line or '"ir.attachment"' in line:
                        # Check if it's a field definition
                        if 'fields.' in line:
                            attachment_fields.append({
                                'file': file_path,
                                'line': i,
                                'content': line.strip()
                            })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return attachment_fields

def verify_compute_methods():
    """
    Verify all compute methods for ir.attachment relationships have proper @api.depends
    """
    model_files = glob.glob('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/*.py')
    
    missing_depends = []
    
    for file_path in model_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                i = 0
                while i < len(lines):
                    line = lines[i]
                    # Look for compute method definitions
                    if re.search(r'def _compute_\w+', line):
                        method_name = re.search(r'def (_compute_\w+)', line).group(1)
                        
                        # Check if previous line has @api.depends
                        has_depends = False
                        j = i - 1
                        while j >= 0 and lines[j].strip() == '':
                            j -= 1
                        if j >= 0 and '@api.depends' in lines[j]:
                            has_depends = True
                        
                        # Check if it's an attachment-related compute method
                        if ('attachment' in method_name.lower() or 
                            'photo' in method_name.lower() or
                            'document' in method_name.lower()):
                            if not has_depends:
                                missing_depends.append({
                                    'file': file_path,
                                    'line': i + 1,
                                    'method': method_name
                                })
                    i += 1
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return missing_depends

def main():
    print("=== Verifying res_id Field Issues Fix ===\n")
    
    # Check for problematic res_id field definitions
    print("1. Checking for problematic res_id field definitions...")
    issues = find_problematic_res_id_fields()
    
    if issues:
        print(f"❌ Found {len(issues)} problematic res_id field definitions:")
        for issue in issues:
            print(f"   File: {os.path.basename(issue['file'])}:{issue['line']}")
            print(f"   Content: {issue['content']}")
            print(f"   Pattern: {issue['pattern']}")
            print()
    else:
        print("✅ No problematic res_id field definitions found!")
    
    # Check ir.attachment relationships
    print("\n2. Checking ir.attachment relationships...")
    attachment_fields = check_ir_attachment_relationships()
    
    print(f"Found {len(attachment_fields)} ir.attachment field relationships:")
    for field in attachment_fields:
        print(f"   {os.path.basename(field['file'])}:{field['line']} - {field['content']}")
    
    # Verify compute methods
    print("\n3. Verifying compute methods for attachment fields...")
    missing_depends = verify_compute_methods()
    
    if missing_depends:
        print(f"❌ Found {len(missing_depends)} compute methods missing @api.depends:")
        for method in missing_depends:
            print(f"   {os.path.basename(method['file'])}:{method['line']} - {method['method']}")
    else:
        print("✅ All attachment-related compute methods have @api.depends!")
    
    # Summary
    print("\n=== SUMMARY ===")
    total_issues = len(issues) + len(missing_depends)
    
    if total_issues == 0:
        print("🎉 ALL CHECKS PASSED! No res_id field issues found.")
        print("The KeyError: 'res_id' should now be resolved.")
    else:
        print(f"⚠️  Found {total_issues} remaining issues that need to be fixed.")
    
    print(f"\nDetailed results:")
    print(f"- Problematic res_id fields: {len(issues)}")
    print(f"- ir.attachment relationships: {len(attachment_fields)}")
    print(f"- Missing @api.depends: {len(missing_depends)}")

if __name__ == "__main__":
    main()
