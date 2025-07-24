#!/usr/bin/env python3
"""
Extract and analyze all field definitions to spot syntax issues
"""
import os
import re

def extract_field_definitions():
    """Extract all field definitions from Python files"""
    models_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    field_pattern = r'(\w+)\s*=\s*fields\.(Char|Text|Integer|Float|Boolean|Date|Datetime|Selection|Many2one|One2many|Many2many|Binary|Html|Json)\s*\((.*?)\)'
    
    results = []
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            filepath = os.path.join(models_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove comments and strings to avoid false matches
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    if 'fields.' in line and '=' in line and not line.strip().startswith('#'):
                        # Simple field pattern matching
                        line_clean = line.strip()
                        if line_clean:
                            results.append({
                                'file': filename,
                                'line': line_num,
                                'content': line_clean
                            })
                            
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    return results

def analyze_one2many_fields(results):
    """Analyze One2many fields for potential syntax issues"""
    issues = []
    
    for result in results:
        content = result['content']
        if 'fields.One2many(' in content:
            # Check for common issues
            
            # Issue 1: Missing string= prefix for third parameter
            # Pattern: fields.One2many('model', 'field', 'Label')
            if re.search(r"fields\.One2many\([^,]+,\s*[^,]+,\s*'[^']+'\s*\)", content):
                issues.append({
                    'type': 'missing_string_prefix',
                    'file': result['file'],
                    'line': result['line'],
                    'content': content,
                    'issue': 'Third parameter should use string= prefix'
                })
            
            # Issue 2: Only 2 parameters (missing inverse or string)
            param_count = content.count(',') + 1 if 'fields.One2many(' in content else 0
            if param_count <= 2:
                issues.append({
                    'type': 'insufficient_parameters',
                    'file': result['file'],
                    'line': result['line'],
                    'content': content,
                    'issue': 'Only 2 parameters - missing string parameter'
                })
    
    return issues

def main():
    print("Extracting all field definitions...")
    results = extract_field_definitions()
    
    print(f"\nFound {len(results)} field definitions")
    
    # Focus on One2many fields
    one2many_fields = [r for r in results if 'One2many(' in r['content']]
    print(f"Found {len(one2many_fields)} One2many fields")
    
    # Analyze for issues
    issues = analyze_one2many_fields(results)
    
    if issues:
        print(f"\n🚨 Found {len(issues)} potential issues:")
        for issue in issues:
            print(f"\n📁 {issue['file']}:{issue['line']}")
            print(f"   Issue: {issue['issue']}")
            print(f"   Content: {issue['content']}")
    else:
        print("\n✅ No obvious syntax issues found in One2many fields")
    
    # Show all One2many fields for manual inspection
    print(f"\n📋 All One2many fields for manual review:")
    for field in one2many_fields:
        print(f"{field['file']}:{field['line']} - {field['content']}")

if __name__ == "__main__":
    main()
