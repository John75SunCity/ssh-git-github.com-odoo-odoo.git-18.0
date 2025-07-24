#!/usr/bin/env python3

import os
import re

def analyze_compute_methods():
    """Analyze all compute methods and find missing @api.depends decorators"""
    
    models_dir = "records_management/models"
    issues = []
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all compute methods
            compute_pattern = r'def (_compute_\w+)\(self.*?\):'
            compute_methods = re.findall(compute_pattern, content)
            
            for method_name in compute_methods:
                # Check if this method has @api.depends before it
                method_start = content.find(f'def {method_name}(')
                if method_start == -1:
                    continue
                    
                # Look backwards for @api.depends
                before_method = content[:method_start]
                lines_before = before_method.split('\n')
                
                # Check last few lines for @api.depends
                has_depends = False
                for i in range(1, min(10, len(lines_before) + 1)):  # Look back up to 10 lines
                    line = lines_before[-i].strip()
                    if '@api.depends(' in line:
                        has_depends = True
                        break
                    elif line and not line.startswith('#') and not line.startswith('@') and 'def ' in line:
                        # Found another method definition - stop looking
                        break
                
                if not has_depends:
                    issues.append({
                        'file': filepath,
                        'method': method_name,
                        'line_number': content[:method_start].count('\n') + 1
                    })
    
    return issues

if __name__ == "__main__":
    print("🔍 Analyzing compute methods for missing @api.depends decorators...")
    issues = analyze_compute_methods()
    
    print(f"\n📊 Found {len(issues)} compute methods missing @api.depends decorators:\n")
    
    for issue in issues:
        print(f"❌ {issue['file']}:{issue['line_number']} - {issue['method']}")
    
    print(f"\n🎯 Total methods to fix: {len(issues)}")
