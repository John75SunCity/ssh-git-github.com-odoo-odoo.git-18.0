#!/usr/bin/env python3
"""
Emergency Bracket Fixer - Fix critical parenthesis and bracket issues
"""

import os
import re
from pathlib import Path

def fix_bracket_mismatches(content):
    """Fix specific bracket and parenthesis mismatch patterns"""
    
    # Pattern 1: fields.Selection( [ -> fields.Selection([
    content = re.sub(r'fields\.Selection\(\s*\[', 'fields.Selection([', content)
    
    # Pattern 2: fields.Type( "string" -> fields.Type("string"
    content = re.sub(r'fields\.(Many2one|Many2many)\(\s*"', r'fields.\1("', content)
    
    # Pattern 3: Fix broken field inheritance with ] instead of )
    content = re.sub(r'_inherit = \[\s*[\'"][^\'"]*[\'"]\s*\]', 
                     lambda m: m.group(0).replace('[', '(').replace(']', ')'), content)
    
    # Pattern 4: Fix trailing commas before closing brackets
    content = re.sub(r',\s*\]', ']', content)
    content = re.sub(r',\s*\)', ')', content)
    
    # Pattern 5: Fix Selection fields with ] at the end instead of )
    content = re.sub(r'fields\.Selection\(\[([^\]]+)\],\s*string=([^,\)]+)\]', 
                     r'fields.Selection([\1], string=\2)', content)
    
    return content

def fix_simple_syntax_errors(content):
    """Fix simple syntax errors"""
    
    # Fix double commas
    content = re.sub(r',,+', ',', content)
    
    # Fix empty function calls field() -> field(
    content = re.sub(r'fields\.[A-Za-z]+\(\)\s*\n', lambda m: m.group(0).replace('()', '('), content)
    
    # Fix invalid syntax patterns
    content = re.sub(r'_inherit = \[([^\]]+)\]', r'_inherit = [\1]', content)
    
    return content

def emergency_fix_file(file_path):
    """Emergency fix for a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Apply fixes
        content = fix_bracket_mismatches(content)
        content = fix_simple_syntax_errors(content)
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Apply emergency fixes to all Python files"""
    base_dir = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management")
    models_dir = base_dir / "models"
    
    python_files = [f for f in models_dir.glob("*.py") if f.name != "__init__.py"]
    
    print(f"Emergency Bracket Fixer - Processing {len(python_files)} files")
    
    fixed_count = 0
    for file_path in python_files:
        if emergency_fix_file(file_path):
            fixed_count += 1
            print(f"✓ Fixed: {file_path.name}")
    
    print(f"\nFixed {fixed_count}/{len(python_files)} files")
    
    # Test a few files
    print("\nTesting compilation of first 5 files...")
    for file_path in python_files[:5]:
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), file_path, 'exec')
            print(f"✓ {file_path.name}: OK")
        except SyntaxError as e:
            print(f"✗ {file_path.name}: {e.msg} at line {e.lineno}")

if __name__ == "__main__":
    main()
