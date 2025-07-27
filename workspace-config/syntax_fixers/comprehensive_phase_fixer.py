#!/usr/bin/env python3
"""
Phase-Based Syntax Fixer - Systematic approach to fix all syntax errors
Phase 1: Indentation
Phase 2: Brackets [] vs () mismatches  
Phase 3: Parenthesis () completion
Phase 4: Final syntax cleanup
"""

import os
import re
from pathlib import Path
import subprocess

def phase1_fix_indentation(content):
    """Phase 1: Fix all indentation issues"""
    lines = content.split('\n')
    fixed_lines = []
    
    # Track context
    class_indent = 0
    method_indent = 0
    in_class = False
    in_method = False
    
    for i, line in enumerate(lines):
        if not line.strip():
            fixed_lines.append(line)
            continue
            
        stripped = line.strip()
        
        # Class definitions
        if stripped.startswith('class ') and line.endswith(':'):
            in_class = True
            in_method = False
            class_indent = len(line) - len(line.lstrip())
            fixed_lines.append(line)
            continue
            
        # Method definitions inside classes
        elif stripped.startswith('def ') and line.endswith(':'):
            if in_class:
                in_method = True
                method_indent = class_indent + 4
                line = ' ' * method_indent + stripped
            fixed_lines.append(line)
            continue
            
        # Decorator lines
        elif stripped.startswith('@'):
            if in_class:
                line = ' ' * method_indent + stripped
            fixed_lines.append(line)
            continue
            
        # Class-level attributes and fields
        elif in_class and not in_method:
            if (stripped.startswith(('_name', '_description', '_inherit', '_order', '_rec_name')) or
                ' = fields.' in stripped or
                stripped.startswith('#')):
                line = ' ' * (class_indent + 4) + stripped
                
        # Method content
        elif in_method:
            if stripped.startswith('"""'):
                # Docstrings
                line = ' ' * (method_indent + 4) + stripped
            elif stripped and not line.startswith(' ' * (method_indent + 4)):
                # Method body content
                line = ' ' * (method_indent + 4) + stripped
                
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def phase2_fix_brackets(content):
    """Phase 2: Fix bracket [] vs () mismatches"""
    
    # Fix _inherit with wrong brackets - should be with ()
    content = re.sub(r'_inherit\s*=\s*\[\s*([\'"][^\'"]*[\'"])\s*\]', 
                     r'_inherit = \1', content)
    
    # Fix Selection fields with wrong bracket placement
    # Pattern: fields.Selection() [...] -> fields.Selection([...])
    content = re.sub(r'fields\.Selection\(\)\s*\n\s*\[', 'fields.Selection([', content)
    
    # Fix field definitions with ] instead of )
    # Pattern: field(..., string="name"] -> field(..., string="name")
    content = re.sub(r'(fields\.[A-Za-z]+\([^)]*)\]', r'\1)', content)
    
    # Fix search() calls with wrong brackets
    # Pattern: search([) ...stuff... ] -> search([...stuff...])
    content = re.sub(r'\.search\(\[\)\s*\n\s*([^]]+)\s*\n\s*\]', r'.search([\1])', content)
    
    return content

def phase3_fix_parentheses(content):
    """Phase 3: Fix parenthesis () completion and mismatches"""
    
    # Fix field definitions with missing opening parenthesis
    # Pattern: fields.Type() \n params \n ) -> fields.Type(params)
    pattern = r'(fields\.[A-Za-z]+)\(\)\s*\n\s*([^)]+)\s*\n\s*\)'
    def fix_field_params(match):
        field_type, params = match.groups()
        clean_params = re.sub(r'\s*\n\s*', ', ', params.strip())
        return f'{field_type}({clean_params})'
    
    content = re.sub(pattern, fix_field_params, content, flags=re.MULTILINE)
    
    # Fix method calls with broken parentheses
    # Pattern: method() \n {params} \n ) -> method({params})
    content = re.sub(r'(self\.[a-zA-Z_][a-zA-Z0-9_]*)\(\)\s*\n\s*(\{[^}]+\})\s*\n\s*\)', 
                     r'\1(\2)', content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix _() translation calls
    content = re.sub(r'_\(\)\s*\n\s*([^)]+)\s*\)', r'_(\1)', content, flags=re.MULTILINE)
    
    # Fix class definitions missing closing parenthesis
    content = re.sub(r'class\s+([A-Za-z_][A-Za-z0-9_]*)\(([^)]+):', r'class \1(\2):', content)
    
    return content

def phase4_final_cleanup(content):
    """Phase 4: Final syntax cleanup"""
    
    # Remove double commas
    content = re.sub(r',,+', ',', content)
    
    # Fix trailing commas before closing brackets/parentheses
    content = re.sub(r',\s*\)', ')', content)
    content = re.sub(r',\s*\]', ']', content)
    
    # Fix empty parentheses with space
    content = re.sub(r'\(\s+\)', '()', content)
    
    # Fix string formatting issues
    content = re.sub(r'string\s*=\s*"([^"]*)",,', r'string="\1",', content)
    
    # Fix broken conditional statements
    content = re.sub(r'if\s+([^)]+)\s+and\s+\(\)\s*\n\s*([^)]+)\s*\n\s*\):', 
                     r'if \1 and (\2):', content, flags=re.MULTILINE)
    
    return content

def validate_syntax(file_path):
    """Validate Python syntax"""
    try:
        result = subprocess.run(['python', '-m', 'py_compile', str(file_path)], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return True, "OK"
        else:
            error_lines = result.stderr.strip().split('\n')
            error_msg = error_lines[-1] if error_lines else "Unknown error"
            return False, error_msg
    except Exception as e:
        return False, str(e)

def fix_file(file_path):
    """Apply all phases to fix a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Apply all phases
        content = original_content
        content = phase1_fix_indentation(content)
        content = phase2_fix_brackets(content)  
        content = phase3_fix_parentheses(content)
        content = phase4_final_cleanup(content)
        
        # Only write if we made changes
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Validate the result
            is_valid, msg = validate_syntax(file_path)
            return True, is_valid, msg
        else:
            is_valid, msg = validate_syntax(file_path)
            return False, is_valid, msg
            
    except Exception as e:
        return False, False, f"Error processing file: {e}"

def main():
    """Fix all Python files in the models directory"""
    base_dir = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management")
    models_dir = base_dir / "models"
    
    if not models_dir.exists():
        print(f"Directory not found: {models_dir}")
        return
    
    python_files = [f for f in models_dir.glob("*.py") if f.name != "__init__.py"]
    
    print("🔧 PHASE-BASED SYNTAX FIXER")
    print("=" * 50)
    print(f"Processing {len(python_files)} Python files...")
    print("Phases: 1) Indentation  2) Brackets  3) Parentheses  4) Cleanup")
    print("=" * 50)
    
    results = {
        'fixed_and_working': [],
        'fixed_but_broken': [],
        'unchanged_working': [],
        'unchanged_broken': []
    }
    
    for file_path in python_files:
        print(f"Processing {file_path.name}...", end=" ")
        
        was_changed, is_valid, message = fix_file(file_path)
        
        if was_changed and is_valid:
            results['fixed_and_working'].append(file_path.name)
            print("✅ FIXED & WORKING")
        elif was_changed and not is_valid:
            results['fixed_but_broken'].append((file_path.name, message))
            print("🔧 FIXED BUT STILL BROKEN")
        elif not was_changed and is_valid:
            results['unchanged_working'].append(file_path.name)
            print("✅ ALREADY WORKING")
        else:
            results['unchanged_broken'].append((file_path.name, message))
            print("❌ STILL BROKEN")
    
    # Summary Report
    print("\n" + "=" * 50)
    print("📊 COMPREHENSIVE FIXING RESULTS")
    print("=" * 50)
    
    total_working = len(results['fixed_and_working']) + len(results['unchanged_working'])
    total_files = len(python_files)
    
    print(f"\n🎯 OVERALL SUCCESS: {total_working}/{total_files} files ({total_working/total_files*100:.1f}%) now compile successfully!")
    
    print(f"\n✅ Fixed and Now Working: {len(results['fixed_and_working'])}")
    for filename in results['fixed_and_working'][:10]:
        print(f"   ✓ {filename}")
    if len(results['fixed_and_working']) > 10:
        print(f"   ... and {len(results['fixed_and_working']) - 10} more")
    
    print(f"\n✅ Already Working: {len(results['unchanged_working'])}")
    for filename in results['unchanged_working'][:5]:
        print(f"   ✓ {filename}")
    if len(results['unchanged_working']) > 5:
        print(f"   ... and {len(results['unchanged_working']) - 5} more")
    
    print(f"\n🔧 Fixed but Still Have Issues: {len(results['fixed_but_broken'])}")
    for filename, error in results['fixed_but_broken'][:5]:
        print(f"   ⚠️  {filename}: {error.split(':')[-1].strip()}")
    if len(results['fixed_but_broken']) > 5:
        print(f"   ... and {len(results['fixed_but_broken']) - 5} more")
    
    print(f"\n❌ Still Broken (No Changes Made): {len(results['unchanged_broken'])}")
    for filename, error in results['unchanged_broken'][:5]:
        print(f"   ❌ {filename}: {error.split(':')[-1].strip()}")
    if len(results['unchanged_broken']) > 5:
        print(f"   ... and {len(results['unchanged_broken']) - 5} more")
    
    print(f"\n🏆 FINAL SCORE: {total_working}/{total_files} files working ({total_working/total_files*100:.1f}% success rate)")
    
    # Test overall module import capability
    print(f"\n🧪 Testing overall module structure...")
    try:
        # Check if __init__.py exists and is valid
        init_file = models_dir / "__init__.py"
        if init_file.exists():
            is_valid, msg = validate_syntax(init_file)
            if is_valid:
                print("✅ models/__init__.py is valid")
            else:
                print(f"❌ models/__init__.py has issues: {msg}")
        else:
            print("⚠️  models/__init__.py not found")
    except Exception as e:
        print(f"❌ Error checking module structure: {e}")

if __name__ == "__main__":
    main()
