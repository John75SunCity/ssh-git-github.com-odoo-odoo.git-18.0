#!/usr/bin/env python3
"""
Deep Bug Detection Audit - Find Specific Issues
Focus on custom names, missing references, broken computations, and edge cases
"""

import os
import re
import sys

def check_compute_field_issues():
    """Check for issues in computed fields"""
    issues = []
    models_dir = "records_management/models"
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find computed fields
            compute_pattern = r"(\w+)\s*=\s*fields\.\w+\([^)]*compute\s*=\s*['\"]([^'\"]+)['\"]"
            compute_matches = re.findall(compute_pattern, content)
            
            # Find @api.depends decorators
            depends_pattern = r"@api\.depends\s*\(\s*([^)]+)\s*\)\s*def\s+(\w+)"
            depends_matches = re.findall(depends_pattern, content, re.MULTILINE)
            
            # Check if compute methods exist
            for field_name, method_name in compute_matches:
                method_pattern = rf"def\s+{re.escape(method_name)}\s*\("
                if not re.search(method_pattern, content):
                    issues.append({
                        'file': filename,
                        'type': 'missing_compute_method',
                        'field': field_name,
                        'method': method_name
                    })
            
            # Check if depends decorators have matching methods
            for depends_fields, method_name in depends_matches:
                if not any(method_name == compute_method for _, compute_method in compute_matches):
                    # Check if method exists without compute field declaration
                    method_pattern = rf"def\s+{re.escape(method_name)}\s*\("
                    if re.search(method_pattern, content):
                        issues.append({
                            'file': filename,
                            'type': 'orphaned_depends',
                            'method': method_name,
                            'depends': depends_fields
                        })
    
    return issues

def check_selection_field_references():
    """Check selection fields for potential issues"""
    issues = []
    models_dir = "records_management/models"
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find selection fields with function references
            selection_pattern = r"(\w+)\s*=\s*fields\.Selection\s*\(\s*(\w+)"
            selection_matches = re.findall(selection_pattern, content)
            
            for field_name, selection_ref in selection_matches:
                if selection_ref != 'lambda' and not selection_ref.startswith('['):
                    # Check if the selection function/method exists
                    func_pattern = rf"def\s+{re.escape(selection_ref)}\s*\(|{re.escape(selection_ref)}\s*=\s*\["
                    if not re.search(func_pattern, content):
                        issues.append({
                            'file': filename,
                            'type': 'missing_selection_method',
                            'field': field_name,
                            'reference': selection_ref
                        })
    
    return issues

def check_onchange_method_references():
    """Check @api.onchange decorators"""
    issues = []
    models_dir = "records_management/models"
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find @api.onchange decorators
            onchange_pattern = r"@api\.onchange\s*\(\s*([^)]+)\s*\)\s*def\s+(\w+)"
            onchange_matches = re.findall(onchange_pattern, content)
            
            # Find all field definitions
            field_pattern = r"(\w+)\s*=\s*fields\."
            field_matches = re.findall(field_pattern, content)
            
            for onchange_fields, method_name in onchange_matches:
                # Extract field names from onchange decorator
                field_refs = re.findall(r"['\"]([^'\"]+)['\"]", onchange_fields)
                for field_ref in field_refs:
                    if field_ref not in field_matches and not field_ref.startswith('_'):
                        issues.append({
                            'file': filename,
                            'type': 'onchange_missing_field',
                            'method': method_name,
                            'field': field_ref
                        })
    
    return issues

def check_default_lambda_references():
    """Check default lambda functions for potential issues"""
    issues = []
    models_dir = "records_management/models"
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find default lambda expressions
            lambda_pattern = r"default\s*=\s*lambda\s+self:\s*([^,\)]+)"
            lambda_matches = re.findall(lambda_pattern, content)
            
            for lambda_expr in lambda_matches:
                # Check for potential issues in lambda expressions
                if 'env.' in lambda_expr and 'company' in lambda_expr:
                    # Common pattern, usually okay
                    continue
                elif 'env.' in lambda_expr and 'user' in lambda_expr:
                    # Common pattern, usually okay
                    continue
                elif '(' in lambda_expr and ')' not in lambda_expr:
                    issues.append({
                        'file': filename,
                        'type': 'incomplete_lambda',
                        'expression': lambda_expr
                    })
    
    return issues

def check_string_references():
    """Check for hardcoded strings that might need translation"""
    issues = []
    models_dir = "records_management/models"
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find string fields without translation
            string_pattern = r"string\s*=\s*['\"]([^'\"]+)['\"]"
            string_matches = re.findall(string_pattern, content)
            
            # Find help text without translation
            help_pattern = r"help\s*=\s*['\"]([^'\"]+)['\"]"
            help_matches = re.findall(help_pattern, content)
            
            # Find raise statements without _() translation
            raise_pattern = r"raise\s+\w+Error\s*\(\s*['\"]([^'\"]+)['\"]"
            raise_matches = re.findall(raise_pattern, content)
            
            for raise_text in raise_matches:
                if not raise_text.startswith('_'):
                    issues.append({
                        'file': filename,
                        'type': 'untranslated_error',
                        'text': raise_text[:50]
                    })
    
    return issues

def check_wizard_references():
    """Check wizard model references"""
    issues = []
    models_dir = "records_management/models"
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for wizard returns
            wizard_pattern = r"return\s*\{\s*['\"]type['\"]\s*:\s*['\"]ir\.actions\.act_window['\"]"
            if re.search(wizard_pattern, content):
                # This is likely a wizard - check for required wizard fields
                if '_transient' not in content and 'TransientModel' not in content:
                    issues.append({
                        'file': filename,
                        'type': 'potential_wizard_not_transient',
                        'note': 'File contains wizard patterns but may not inherit TransientModel'
                    })
    
    return issues

def main():
    print("=== DEEP BUG DETECTION AUDIT ===")
    print("Searching for specific potential issues...")
    print()
    
    all_issues = []
    
    # 1. Check computed field issues
    print("🔍 Checking computed field references...")
    compute_issues = check_compute_field_issues()
    all_issues.extend(compute_issues)
    print(f"   Found {len(compute_issues)} compute-related issues")
    
    # 2. Check selection field references
    print("🔍 Checking selection field references...")
    selection_issues = check_selection_field_references()
    all_issues.extend(selection_issues)
    print(f"   Found {len(selection_issues)} selection field issues")
    
    # 3. Check onchange method references
    print("🔍 Checking @api.onchange references...")
    onchange_issues = check_onchange_method_references()
    all_issues.extend(onchange_issues)
    print(f"   Found {len(onchange_issues)} onchange issues")
    
    # 4. Check default lambda expressions
    print("🔍 Checking default lambda expressions...")
    lambda_issues = check_default_lambda_references()
    all_issues.extend(lambda_issues)
    print(f"   Found {len(lambda_issues)} lambda expression issues")
    
    # 5. Check string references for translation
    print("🔍 Checking string translations...")
    string_issues = check_string_references()
    all_issues.extend(string_issues)
    print(f"   Found {len(string_issues)} translation issues")
    
    # 6. Check wizard references
    print("🔍 Checking wizard model patterns...")
    wizard_issues = check_wizard_references()
    all_issues.extend(wizard_issues)
    print(f"   Found {len(wizard_issues)} wizard-related issues")
    
    print()
    print("=== DETAILED FINDINGS ===")
    
    # Report detailed issues
    issue_types = {}
    for issue in all_issues:
        issue_type = issue['type']
        if issue_type not in issue_types:
            issue_types[issue_type] = []
        issue_types[issue_type].append(issue)
    
    for issue_type, issues in issue_types.items():
        print(f"\n📋 {issue_type.upper().replace('_', ' ')}:")
        for issue in issues[:10]:  # Limit to first 10 of each type
            if issue_type == 'missing_compute_method':
                print(f"   {issue['file']}: Field '{issue['field']}' references missing method '{issue['method']}'")
            elif issue_type == 'missing_selection_method':
                print(f"   {issue['file']}: Selection field '{issue['field']}' references '{issue['reference']}'")
            elif issue_type == 'onchange_missing_field':
                print(f"   {issue['file']}: @api.onchange method '{issue['method']}' references missing field '{issue['field']}'")
            elif issue_type == 'untranslated_error':
                print(f"   {issue['file']}: Error message not translated: '{issue['text']}'")
            elif issue_type == 'potential_wizard_not_transient':
                print(f"   {issue['file']}: {issue['note']}")
            else:
                print(f"   {issue['file']}: {issue}")
        
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more")
    
    print(f"\n=== AUDIT SUMMARY ===")
    print(f"Total potential issues found: {len(all_issues)}")
    
    if len(all_issues) == 0:
        print("🎉 No specific issues found! Code appears to be well-structured.")
    else:
        print("⚠️  Review the issues above to prevent potential runtime errors.")
        print("💡 Many of these may be false positives or minor issues.")
    
    return 0 if len(all_issues) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
