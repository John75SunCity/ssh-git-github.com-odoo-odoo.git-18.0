#!/usr/bin/env python3
"""
Script to identify and fix missing @api.depends decorators for compute methods
in Odoo Records Management module.
"""

import os
import re
import sys

def find_compute_methods_without_depends(file_path):
    """Find compute methods that are missing @api.depends decorators."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    missing_depends = []
    
    for i, line in enumerate(lines):
        # Look for compute method definitions
        if re.match(r'\s*def _compute_.*\(self.*\):', line):
            method_name = re.search(r'def (_compute_\w+)', line).group(1)
            
            # Check if the previous line has @api.depends
            has_depends = False
            j = i - 1
            
            # Look backwards for @api.depends, allowing for empty lines and comments
            while j >= 0 and (not lines[j].strip() or 
                             lines[j].strip().startswith('#') or
                             lines[j].strip().startswith('@')):
                if '@api.depends' in lines[j]:
                    has_depends = True
                    break
                # If we hit another method or class definition, stop looking
                if re.match(r'\s*def\s+\w+.*\(.*\):', lines[j]) or re.match(r'\s*class\s+\w+.*:', lines[j]):
                    break
                j -= 1
            
            if not has_depends:
                # Skip certain methods that don't need @api.depends
                skip_methods = [
                    '_compute_activity_ids',
                    '_compute_message_followers', 
                    '_compute_message_ids'
                ]
                
                if method_name not in skip_methods:
                    missing_depends.append({
                        'method': method_name,
                        'line': i + 1,
                        'content': line.strip()
                    })
    
    return missing_depends

def analyze_compute_method_fields(file_path, method_name):
    """Analyze a compute method to suggest appropriate @api.depends fields."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the method
    pattern = rf'def {re.escape(method_name)}\(self.*?\):(.*?)(?=\n\s*def\s|\n\s*@|\n\s*class\s|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        return []
    
    method_body = match.group(1)
    
    # Look for field references in the method body
    field_refs = set()
    
    # Pattern for self.field_name or record.field_name
    field_patterns = [
        r'self\.(\w+)',
        r'record\.(\w+)', 
        r'service\.(\w+)',
        r'policy\.(\w+)',
        r'item\.(\w+)',
        r'box\.(\w+)',
        r'document\.(\w+)',
        r'feedback\.(\w+)',
        r'load\.(\w+)',
        r'bale\.(\w+)',
        r'tag\.(\w+)',
        r'compliance\.(\w+)',
        r'report\.(\w+)',
        r'task\.(\w+)',
        r'config\.(\w+)',
        r'request\.(\w+)',
        r'lot\.(\w+)',
        r'location\.(\w+)',
        r'product\.(\w+)',
        r'billing\.(\w+)',
        r'department\.(\w+)',
        r'wizard\.(\w+)',
        r'customer\.(\w+)',
        r'partner\.(\w+)',
    ]
    
    for pattern in field_patterns:
        matches = re.findall(pattern, method_body)
        for match in matches:
            # Filter out common non-field references
            if match not in ['env', 'id', 'ids', 'sudo', 'with_context', 'create', 'write', 'search', 'browse']:
                field_refs.add(match)
    
    # Look for related field access patterns like record.field_ids.other_field
    related_patterns = [
        r'\.(\w+_ids)\.(\w+)',
        r'\.(\w+_id)\.(\w+)',
    ]
    
    for pattern in related_patterns:
        matches = re.findall(pattern, method_body)
        for match in matches:
            field_refs.add(match[0])
            field_refs.add(f"{match[0]}.{match[1]}")
    
    return sorted(list(field_refs))

def main():
    """Main function to scan all model files and identify missing @api.depends decorators."""
    models_dir = 'records_management/models'
    
    if not os.path.exists(models_dir):
        print(f"Error: {models_dir} directory not found!")
        sys.exit(1)
    
    print("🔍 Scanning for compute methods missing @api.depends decorators...")
    print("=" * 80)
    
    total_missing = 0
    
    for filename in sorted(os.listdir(models_dir)):
        if filename.endswith('.py') and filename != '__init__.py':
            file_path = os.path.join(models_dir, filename)
            missing = find_compute_methods_without_depends(file_path)
            
            if missing:
                print(f"\n📄 {filename}")
                print("-" * 40)
                
                for item in missing:
                    print(f"  ❌ {item['method']} (line {item['line']})")
                    
                    # Analyze method to suggest dependencies
                    suggested_fields = analyze_compute_method_fields(file_path, item['method'])
                    if suggested_fields:
                        print(f"     💡 Suggested @api.depends: {', '.join(repr(f) for f in suggested_fields[:5])}")
                    else:
                        print(f"     💡 Analysis: No clear field dependencies found")
                    
                total_missing += len(missing)
    
    print(f"\n📊 Summary:")
    print(f"   Total compute methods missing @api.depends: {total_missing}")
    
    if total_missing > 0:
        print(f"\n⚠️  These compute methods should have @api.depends decorators")
        print(f"   to ensure proper field recomputation when dependencies change.")
        print(f"   This can cause performance issues and incorrect field values.")

if __name__ == '__main__':
    main()
