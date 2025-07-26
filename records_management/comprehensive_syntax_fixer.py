#!/usr/bin/env python3
"""
Comprehensive syntax fixer for Records Management module
Fixes common syntax issues from duplicate field removal
"""

import os
import re
import sys

def fix_file_syntax(filepath):
    """Fix common syntax issues in a Python file"""
    print(f"Checking {filepath}...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixed_issues = []
        
        # Fix 1: Orphaned field parameters (missing field name/type)
        # Pattern: starts with whitespace, then (, then field parameters
        pattern = r'\n(\s+)\(\s*string=.*?\),?\s*\n'
        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            # Remove orphaned field parameters
            content = re.sub(pattern, '\n', content)
            fixed_issues.append("Removed orphaned field parameters")
        
        # Fix 2: Orphaned closing brackets/parentheses
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Check for orphaned closing brackets
            if stripped in (']', '], string=', '], required=True)', ')', '),'):
                # Check if previous line suggests this is orphaned
                if i > 0:
                    prev_line = lines[i-1].strip()
                    if not prev_line.endswith(',') and not prev_line.endswith('[') and not prev_line.endswith('('):
                        fixed_issues.append(f"Removed orphaned closing bracket on line {i+1}")
                        i += 1
                        continue
            
            # Check for lines that start with field parameters without field definition
            if re.match(r'^\s*\], string=.*$', line):
                fixed_issues.append(f"Removed orphaned field parameter on line {i+1}")
                i += 1
                continue
                
            fixed_lines.append(line)
            i += 1
        
        content = '\n'.join(fixed_lines)
        
        # Fix 3: Missing indentation after class/function definitions
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            fixed_lines.append(line)
            
            # Check if this is a class/function/if/else that needs indentation
            stripped = line.strip()
            if (stripped.endswith(':') and 
                ('class ' in stripped or 'def ' in stripped or 
                 stripped.startswith('if ') or stripped.startswith('else'))):
                
                # Check if next line is properly indented
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip() and not next_line.startswith('    ') and not next_line.startswith('\t'):
                        # Add a pass statement
                        indent = '    ' * (len(line) - len(line.lstrip()) + 1)
                        fixed_lines.append(f"{indent}pass")
                        fixed_issues.append(f"Added pass statement after line {i+1}")
        
        content = '\n'.join(fixed_lines)
        
        # Fix 4: Remove duplicate consecutive empty lines (more than 2)
        content = re.sub(r'\n\n\n+', '\n\n', content)
        
        # Write back if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if fixed_issues:
                print(f"  ✅ Fixed issues: {', '.join(fixed_issues)}")
                return True
            else:
                print(f"  ✅ Minor formatting fixes applied")
                return True
        else:
            print(f"  ✅ No issues found")
            return False
            
    except Exception as e:
        print(f"  ❌ Error processing {filepath}: {e}")
        return False

def main():
    """Main function to fix all Python files in models directory"""
    models_dir = "models"
    
    if not os.path.exists(models_dir):
        print("❌ Models directory not found")
        return
    
    print("🔧 Starting comprehensive syntax fixing...")
    
    fixed_files = 0
    total_files = 0
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            total_files += 1
            
            if fix_file_syntax(filepath):
                fixed_files += 1
    
    print(f"\n📊 Summary: Fixed {fixed_files} out of {total_files} Python files")
    print("🚀 Running syntax validation...")
    
    # Test compilation of all files
    errors = []
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            try:
                compile(open(filepath).read(), filepath, 'exec')
                print(f"  ✅ {filename}")
            except SyntaxError as e:
                errors.append(f"{filename}: {e}")
                print(f"  ❌ {filename}: {e}")
    
    if errors:
        print(f"\n⚠️  {len(errors)} files still have syntax errors:")
        for error in errors:
            print(f"    {error}")
        print("\nThese may require manual fixing.")
    else:
        print("\n🎉 All Python files compile successfully!")

if __name__ == "__main__":
    main()
