#!/usr/bin/env python3
"""
Diagnostic tool to find field relationship issues
"""

import re
import os

def find_field_relationship_issues():
    """Find potential One2many/Many2one relationship issues"""
    
    print("🔍 SEARCHING FOR FIELD RELATIONSHIP ISSUES")
    print("="*50)
    
    models_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    potential_issues = []
    
    # Read all Python files and look for field definitions
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Look for One2many fields that might have inverse issues
            one2many_pattern = r'fields\.One2many\s*\(\s*[\'"]([^\'"]+)[\'"]\s*,\s*[\'"]([^\'"]+)[\'"]\s*(?:,\s*[\'"]([^\'"]+)[\'"])?'
            many2one_pattern = r'([a-zA-Z_]+)\s*=\s*fields\.Many2one\s*\(\s*[\'"]([^\'"]+)[\'"]'
            
            one2many_matches = re.findall(one2many_pattern, content)
            many2one_matches = re.findall(many2one_pattern, content)
            
            if one2many_matches:
                print(f"\n📁 {filename}:")
                for match in one2many_matches:
                    comodel, inverse_field, domain = match
                    print(f"   One2many: {comodel} -> inverse field: '{inverse_field}'")
                    potential_issues.append((filename, 'One2many', comodel, inverse_field))
            
            if many2one_matches:
                if not one2many_matches:  # Only print header if not already printed
                    print(f"\n📁 {filename}:")
                for field_name, comodel in many2one_matches:
                    if '_id' in field_name:
                        print(f"   Many2one: {field_name} -> {comodel}")
    
    print(f"\n🔍 CHECKING FOR MISSING INVERSE FIELDS")
    print("="*40)
    
    # Check if any One2many fields reference non-existent inverse fields
    for filename, field_type, comodel, inverse_field in potential_issues:
        print(f"\n❓ Checking {filename}: {comodel}.{inverse_field}")
        
        # Try to find the inverse field in other files
        found_inverse = False
        for check_filename in os.listdir(models_dir):
            if check_filename.endswith('.py'):
                check_filepath = os.path.join(models_dir, check_filename)
                with open(check_filepath, 'r') as f:
                    check_content = f.read()
                
                if f"{inverse_field} =" in check_content:
                    found_inverse = True
                    print(f"   ✅ Found {inverse_field} in {check_filename}")
                    break
        
        if not found_inverse:
            print(f"   ❌ MISSING: {inverse_field} not found in any model!")
            print(f"      This could cause: KeyError: '{inverse_field}'")

def check_model_naming_conflicts():
    """Check for model naming conflicts"""
    
    print(f"\n🔍 CHECKING MODEL NAMING CONFLICTS")
    print("="*35)
    
    models_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    model_names = {}
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Look for _name definitions
            name_pattern = r'_name\s*=\s*[\'"]([^\'"]+)[\'"]'
            name_matches = re.findall(name_pattern, content)
            
            for model_name in name_matches:
                if model_name in model_names:
                    print(f"❌ CONFLICT: Model '{model_name}' defined in both:")
                    print(f"   - {model_names[model_name]}")
                    print(f"   - {filename}")
                else:
                    model_names[model_name] = filename
                    print(f"✅ {model_name} -> {filename}")

if __name__ == "__main__":
    find_field_relationship_issues()
    check_model_naming_conflicts()
    
    print(f"\n" + "="*50)
    print("🎯 RECOMMENDATIONS:")
    print("1. Fix any missing inverse fields found above")
    print("2. Resolve any model naming conflicts")
    print("3. Ensure all One2many fields have valid inverse relationships")
    print("="*50)
