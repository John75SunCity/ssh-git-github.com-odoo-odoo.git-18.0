#!/usr/bin/env python3
"""
Find all One2many fields with invalid model references that use 'config_id'
"""

import os
import re
import glob

def find_one2many_config_id_issues():
    """Find problematic One2many fields that reference non-existent models with config_id"""
    model_files = glob.glob('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/*.py')
    
    issues = []
    
    for file_path in model_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Look for One2many fields with 'config_id' inverse
                    if 'fields.One2many' in line and "'config_id'" in line:
                        # Extract model name
                        model_match = re.search(r"fields\.One2many\s*\(\s*['\"]([^'\"]+)['\"]", line)
                        if model_match:
                            model_name = model_match.group(1)
                            
                            # Skip standard Odoo models that should exist
                            if model_name.startswith(('pos.', 'account.', 'stock.', 'sale.', 'purchase.')):
                                continue
                                
                            issues.append({
                                'file': os.path.basename(file_path),
                                'line': i,
                                'content': line.strip(),
                                'model': model_name
                            })
                            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return issues

def main():
    print("=== Finding One2many fields with config_id inverse ===\n")
    
    issues = find_one2many_config_id_issues()
    
    if issues:
        print(f"Found {len(issues)} One2many fields with 'config_id' inverse:")
        for issue in issues:
            print(f"  {issue['file']}:{issue['line']} → {issue['model']}")
            print(f"    {issue['content']}")
            print()
    else:
        print("✅ No problematic One2many fields with 'config_id' inverse found!")

if __name__ == "__main__":
    main()
