#!/usr/bin/env python3
"""
Comprehensive Loading Order and Model Reference Audit
Checks for potential issues that could cause module loading failures
"""

import re
import os
import glob
from collections import defaultdict

def find_model_definitions():
    """Find all model definitions in the module"""
    models = {}
    model_files = glob.glob('records_management/models/*.py')

    for file_path in model_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find _name definitions
            name_matches = re.finditer(r'_name\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            for match in name_matches:
                model_name = match.group(1)
                models[model_name] = file_path

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return models

def find_field_references():
    """Find all Many2one, One2many, Many2many field references"""
    references = defaultdict(list)
    model_files = glob.glob('records_management/models/*.py')

    for file_path in model_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find field references
            field_patterns = [
                r'fields\.Many2one\([\'"]([^\'"]+)[\'"]',
                r'fields\.One2many\([\'"]([^\'"]+)[\'"]',
                r'fields\.Many2many\([\'"]([^\'"]+)[\'"]'
            ]

            for pattern in field_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    model_ref = match.group(1)
                    references[model_ref].append({
                        'file': file_path,
                        'line': content[:match.start()].count('\n') + 1,
                        # Avoid invalid escape warnings by splitting on literal backslash-dot
                        'field_type': pattern.split('\\.')[1].split('\\\\(')[0]
                    })

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return references

def find_inheritance_issues():
    """Find potential inheritance order issues"""
    inheritance = {}
    model_files = glob.glob('records_management/models/*.py')

    for file_path in model_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find _inherit patterns
            inherit_matches = re.finditer(r'_inherit\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            for match in inherit_matches:
                parent_model = match.group(1)

                # Get model name from same file
                name_match = re.search(r'_name\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                if name_match:
                    child_model = name_match.group(1)
                    inheritance[child_model] = parent_model

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return inheritance

def find_domain_references():
    """Find domain references that might cause issues"""
    domain_issues = []
    model_files = glob.glob('records_management/models/*.py')

    for file_path in model_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find domain references with model field access
            domain_pattern = r'domain\s*=\s*[\'"]?\[.*?[\'"]([^.\'"]+)\.([^.\'"]+)[\'"]'
            matches = re.finditer(domain_pattern, content)
            for match in matches:
                model_ref = match.group(1)
                field_ref = match.group(2)
                line_num = content[:match.start()].count('\n') + 1

                domain_issues.append({
                    'file': file_path,
                    'line': line_num,
                    'model': model_ref,
                    'field': field_ref,
                    'context': match.group(0)
                })

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return domain_issues

def check_security_access():
    """Check if all models have security access rules"""
    models = find_model_definitions()
    security_file = 'records_management/security/ir.model.access.csv'

    try:
        with open(security_file, 'r', encoding='utf-8') as f:
            security_content = f.read()
    except FileNotFoundError:
        print(f"Security file not found: {security_file}")
        return []

    missing_security = []
    for model_name in models.keys():
        # Convert model name to security rule format
        access_pattern = model_name.replace('.', '_')
        if access_pattern not in security_content:
            missing_security.append({
                'model': model_name,
                'file': models[model_name]
            })

    return missing_security

def audit_loading_order():
    """Main audit function"""
    print("=" * 80)
    print("COMPREHENSIVE LOADING ORDER AND MODEL REFERENCE AUDIT")
    print("=" * 80)

    # Get all model definitions
    models = find_model_definitions()
    print(f"\n📊 Found {len(models)} model definitions")

    # Check field references
    references = find_field_references()
    print(f"📊 Found {len(references)} unique model references in fields")

    missing_models = []
    for model_ref, usages in references.items():
        if model_ref not in models and not model_ref.startswith(('res.', 'account.', 'stock.', 'project.', 'mail.', 'ir.', 'base.')):
            missing_models.append((model_ref, usages))

    if missing_models:
        print(f"\n🚨 CRITICAL: {len(missing_models)} model references to non-existent models:")
        for model_ref, usages in missing_models:
            print(f"\n❌ Model '{model_ref}' referenced but not defined:")
            for usage in usages[:3]:  # Show first 3 usages
                file_short = usage['file'].split('/')[-1]
                print(f"   • {file_short}:{usage['line']} ({usage['field_type']})")
            if len(usages) > 3:
                print(f"   • ... and {len(usages) - 3} more references")
    else:
        print("\n✅ All field model references point to existing models")

    # Check inheritance issues
    inheritance = find_inheritance_issues()
    if inheritance:
        print(f"\n📊 Found {len(inheritance)} model inheritance relationships")
        inheritance_issues = []
        for child, parent in inheritance.items():
            if parent not in models and not parent.startswith(('res.', 'account.', 'stock.', 'project.', 'mail.', 'ir.', 'base.')):
                inheritance_issues.append((child, parent))

        if inheritance_issues:
            print(f"\n🚨 INHERITANCE ISSUES: {len(inheritance_issues)} models inherit from non-existent models:")
            for child, parent in inheritance_issues:
                print(f"   ❌ {child} inherits from {parent} (not found)")
        else:
            print("\n✅ All inheritance relationships are valid")

    # Check domain references
    domain_issues = find_domain_references()
    if domain_issues:
        print(f"\n📊 Found {len(domain_issues)} domain references with field access")
        print("⚠️  Domain field references (may need validation):")
        for issue in domain_issues[:5]:  # Show first 5
            file_short = issue['file'].split('/')[-1]
            print(f"   • {file_short}:{issue['line']} - {issue['model']}.{issue['field']}")
        if len(domain_issues) > 5:
            print(f"   • ... and {len(domain_issues) - 5} more domain references")

    # Check security access
    missing_security = check_security_access()
    if missing_security:
        print(f"\n🚨 SECURITY ISSUES: {len(missing_security)} models missing security access rules:")
        for missing in missing_security[:5]:
            file_short = missing['file'].split('/')[-1]
            print(f"   ❌ {missing['model']} (in {file_short})")
        if len(missing_security) > 5:
            print(f"   ❌ ... and {len(missing_security) - 5} more models")
    else:
        print("\n✅ All models appear to have security access rules")

    # Summary
    total_issues = len(missing_models) + len(inheritance_issues if 'inheritance_issues' in locals() else []) + len(missing_security)

    print(f"\n" + "=" * 80)
    print(f"AUDIT SUMMARY")
    print(f"=" * 80)
    print(f"📊 Total models: {len(models)}")
    print(f"📊 Total field references: {len(references)}")
    print(f"🚨 Critical issues found: {total_issues}")

    if total_issues == 0:
        print("🎉 No critical loading order issues detected!")
    else:
        print("⚠️  Issues found that may cause loading order problems")

    return {
        'models': models,
        'missing_models': missing_models,
        'missing_security': missing_security,
        'domain_issues': domain_issues
    }

if __name__ == '__main__':
    os.chdir('/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0')
    audit_loading_order()
