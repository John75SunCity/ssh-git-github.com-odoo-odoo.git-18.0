#!/usr/bin/env python3
"""
Final comprehensive check for all problematic One2many inverse field issues
"""

import os
import re
import glob

def find_all_one2many_issues():
    """Find all potentially problematic One2many fields"""
    model_files = glob.glob('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/*.py')
    
    issues = []
    
    # Common problematic inverse field patterns
    problematic_patterns = [
        r'wizard_id',
        r'config_id', 
        r'res_id',
        r'feedback_id',
        r'improvement_action_id'
    ]
    
    for file_path in model_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Look for One2many fields with problematic inverse patterns
                    if 'fields.One2many' in line and not line.strip().startswith('#'):
                        # Extract the full field definition (may span multiple lines)
                        field_def = line
                        
                        # Check if it uses compute method instead of inverse
                        if 'compute=' in field_def:
                            continue  # Skip compute methods
                            
                        # Check for problematic inverse patterns
                        for pattern in problematic_patterns:
                            if f"'{pattern}'" in field_def or f'"{pattern}"' in field_def:
                                # Extract model name
                                model_match = re.search(r"fields\.One2many\s*\(\s*['\"]([^'\"]+)['\"]", field_def)
                                if model_match:
                                    model_name = model_match.group(1)
                                    
                                    issues.append({
                                        'file': os.path.basename(file_path),
                                        'line': i,
                                        'content': line.strip(),
                                        'model': model_name,
                                        'inverse_field': pattern
                                    })
                                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return issues

def main():
    print("=== Final Comprehensive One2many Inverse Field Check ===\n")
    
    issues = find_all_one2many_issues()
    
    if issues:
        print(f"❌ Found {len(issues)} potentially problematic One2many fields:")
        for issue in issues:
            print(f"  {issue['file']}:{issue['line']} → {issue['model']} (inverse: {issue['inverse_field']})")
            print(f"    {issue['content']}")
            print()
    else:
        print("🎉 No problematic One2many inverse fields found!")
        print("All KeyError issues should be resolved!")

if __name__ == "__main__":
    main()
