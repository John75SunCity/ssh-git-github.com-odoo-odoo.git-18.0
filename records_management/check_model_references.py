#!/usr/bin/env python3
"""
Check for invalid model references that could cause KeyError during field setup
"""

import os
import re
import glob

def find_one2many_references():
    """Find all One2many field references and check if target models exist"""
    model_files = glob.glob('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/*.py')
    
    # Extract all model names defined in our module
    defined_models = set()
    external_models = {
        'mail.activity', 'mail.followers', 'mail.message', 'ir.attachment',
        'res.users', 'res.partner', 'res.company', 'product.product',
        'ir.sequence', 'ir.ui.view', 'res.currency', 'ir.model.access'
    }
    
    # First pass: collect all model names defined in the module
    for file_path in model_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                # Find all _name definitions
                name_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                defined_models.update(name_matches)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    print(f"Found {len(defined_models)} models defined in the module:")
    for model in sorted(defined_models):
        print(f"  - {model}")
    
    # Second pass: find One2many/Many2one references
    issues = []
    
    for file_path in model_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Skip commented lines
                    if line.strip().startswith('#'):
                        continue
                    
                    # Look for One2many/Many2one field definitions
                    one2many_match = re.search(r"fields\.One2many\s*\(\s*['\"]([^'\"]+)['\"]", line)
                    many2one_match = re.search(r"fields\.Many2one\s*\(\s*['\"]([^'\"]+)['\"]", line)
                    
                    for match in [one2many_match, many2one_match]:
                        if match:
                            target_model = match.group(1)
                            # Check if this model exists in our definitions or is a known external model
                            if (target_model not in defined_models and 
                                target_model not in external_models and
                                not target_model.startswith('account.') and
                                not target_model.startswith('stock.') and
                                not target_model.startswith('project.') and
                                not target_model.startswith('sale.') and
                                not target_model.startswith('purchase.')):
                                
                                # Check if this line uses compute (which is OK)
                                if 'compute=' not in line:
                                    issues.append({
                                        'file': file_path,
                                        'line': i,
                                        'content': line.strip(),
                                        'model': target_model,
                                        'type': 'One2many' if one2many_match else 'Many2one'
                                    })
                                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return issues, defined_models

def main():
    print("=== Checking for Invalid Model References ===\n")
    
    issues, defined_models = find_one2many_references()
    
    if issues:
        print(f"❌ Found {len(issues)} potentially problematic model references:")
        for issue in issues:
            print(f"\n  File: {os.path.basename(issue['file'])}:{issue['line']}")
            print(f"  Type: {issue['type']}")
            print(f"  Target Model: {issue['model']}")
            print(f"  Code: {issue['content']}")
            
            # Suggest fix
            if issue['type'] == 'One2many' and 'inverse' in issue['content']:
                print(f"  💡 Suggestion: Convert to compute method")
            elif issue['model'].startswith('records.'):
                print(f"  💡 Suggestion: Check if '{issue['model']}' model should be created")
    else:
        print("✅ No problematic model references found!")
    
    print(f"\n=== Module Statistics ===")
    print(f"Total models defined: {len(defined_models)}")
    print(f"Potential issues found: {len(issues)}")

if __name__ == "__main__":
    main()
