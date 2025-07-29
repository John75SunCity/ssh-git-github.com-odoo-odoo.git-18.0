#!/usr/bin/env python3
"""
Aggressive Bracket Fixer - Target specific bracket mismatch patterns
"""

import os
import re
from pathlib import Path
import subprocess

def aggressive_bracket_fixes(content):
    """Aggressively fix all bracket/parenthesis mismatches"""
    
    # Fix 1: _inherit bracket issues
    # _inherit = ['mail.thread'] -> _inherit = ['mail.thread']  (keep as list)
    # _inherit = 'model' -> _inherit = 'model' (keep as string)
    content = re.sub(r'_inherit\s*=\s*\(\s*([\'"][^\'"]*[\'"])\s*\)', r'_inherit = \1', content)
    
    # Fix 2: Search method calls with bracket mismatches
    # .search([) ...stuff... ] -> .search([...stuff...])
    content = re.sub(r'\.search\(\[\)\s*\n([^]]+)\s*\]', r'.search([\1])', content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix 3: Field definition bracket mismatches - most common issue
    # Pattern: fields.Selection( [options], string="name") -> fields.Selection([options], string="name")
    content = re.sub(r'fields\.Selection\(\s*\[([^\]]+)\],\s*([^)]+)\)', r'fields.Selection([\1], \2)', content)
    
    # Fix 4: Search calls with wrong bracket order
    # .search([) params ] -> .search([params])
    def fix_search_brackets(match):
        method_call = match.group(1)
        search_params = match.group(2).strip()
        # Clean up the parameters
        clean_params = re.sub(r'\s*\n\s*', ' ', search_params)
        return f'{method_call}.search([{clean_params}])'
    
    content = re.sub(r'(self\.env\[[^\]]+\]|[a-zA-Z_][a-zA-Z0-9_]*)\.search\(\[\)\s*\n([^]]+)\s*\]', 
                     fix_search_brackets, content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix 5: Many2one/Many2many field bracket issues
    # fields.Many2one( "model", params] -> fields.Many2one("model", params)
    content = re.sub(r'fields\.(Many2one|Many2many)\(\s*"([^"]+)",([^]]+)\]', 
                     r'fields.\1("\2",\3)', content)
    
    # Fix 6: Selection field with mismatched closing
    # fields.Selection([...], string="name"] -> fields.Selection([...], string="name")
    content = re.sub(r'(fields\.Selection\(\[[^\]]+\],[^]]+)\]', r'\1)', content)
    
    # Fix 7: General field parameter bracket fixes
    # fields.Type(..., param="value"] -> fields.Type(..., param="value")
    content = re.sub(r'(fields\.[A-Za-z]+\([^]]+)\]', r'\1)', content)
    
    # Fix 8: Method calls with dictionary parameters and wrong brackets
    # method({...}] -> method({...})
    content = re.sub(r'(\w+\(\{[^}]+\})\]', r'\1)', content)
    
    return content

def aggressive_parenthesis_fixes(content):
    """Aggressively fix parenthesis issues"""
    
    # Fix class definitions missing closing parenthesis
    content = re.sub(r'class\s+([A-Za-z_][A-Za-z0-9_]*)\(([^)]*?)(?:\s*:)', r'class \1(\2):', content)
    
    # Fix field calls with empty parentheses followed by parameters
    # fields.Type() \n string="name" \n ) -> fields.Type(string="name")
    def fix_field_empty_parens(match):
        field_call = match.group(1)
        params = match.group(2)
        # Clean up parameters
        clean_params = re.sub(r'\s*\n\s*', ', ', params.strip())
        clean_params = re.sub(r',\s*,', ',', clean_params)  # Remove double commas
        return f'{field_call}({clean_params})'
    
    content = re.sub(r'(fields\.[A-Za-z]+)\(\)\s*\n([^)]+)\s*\)', 
                     fix_field_empty_parens, content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix method calls with broken parentheses
    # self.method() \n {params} \n ) -> self.method({params})
    content = re.sub(r'(self\.[a-zA-Z_][a-zA-Z0-9_]*)\(\)\s*\n\s*(\{[^}]+\})\s*\n\s*\)', 
                     r'\1(\2)', content, flags=re.MULTILINE | re.DOTALL)
    
    # Fix translation calls
    # _() \n "text" \n ) -> _("text")
    content = re.sub(r'_\(\)\s*\n\s*([^)]+)\s*\)', r'_(\1)', content, flags=re.MULTILINE)
    
    return content

def emergency_syntax_fixes(content):
    """Emergency fixes for remaining syntax issues"""
    
    # Remove multiple consecutive commas
    content = re.sub(r',{2,}', ',', content)
    
    # Fix trailing commas before closing brackets/parentheses
    content = re.sub(r',\s*\)', ')', content)
    content = re.sub(r',\s*\]', ']', content)
    
    # Fix string concatenation issues
    content = re.sub(r'string\s*=\s*"([^"]*)",\s*,', r'string="\1",', content)
    
    # Fix broken f-string formatting
    content = re.sub(r'f"([^"]*){([^}]+)}([^"]*)"', r'f"\1{\2}\3"', content)
    
    return content

def validate_and_fix_file(file_path):
    """Validate and fix a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Apply aggressive fixes
        content = original_content
        content = aggressive_bracket_fixes(content)
        content = aggressive_parenthesis_fixes(content)
        content = emergency_syntax_fixes(content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Validate syntax
        result = subprocess.run(['python', '-m', 'py_compile', str(file_path)], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, "OK"
        else:
            error_msg = result.stderr.strip().split('\n')[-1]
            return False, error_msg
            
    except Exception as e:
        return False, str(e)

def main():
    """Process all files with aggressive bracket fixing"""
    base_dir = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management")
    models_dir = base_dir / "models"
    
    python_files = [f for f in models_dir.glob("*.py") if f.name != "__init__.py"]
    
    print("🚀 AGGRESSIVE BRACKET & PARENTHESIS FIXER")
    print("=" * 55)
    print(f"Processing {len(python_files)} files with aggressive fixes...")
    print("=" * 55)
    
    working_files = []
    broken_files = []
    
    for file_path in python_files:
        print(f"Fixing {file_path.name}...", end=" ")
        
        is_working, message = validate_and_fix_file(file_path)
        
        if is_working:
            working_files.append(file_path.name)
            print("✅ WORKING")
        else:
            broken_files.append((file_path.name, message))
            print("❌ BROKEN")
    
    # Final Report
    print("\n" + "=" * 55)
    print("📊 AGGRESSIVE FIXING RESULTS")
    print("=" * 55)
    
    total_working = len(working_files)
    total_files = len(python_files)
    success_rate = (total_working / total_files) * 100
    
    print(f"\n🎯 SUCCESS RATE: {total_working}/{total_files} files ({success_rate:.1f}%) are now working!")
    
    print(f"\n✅ WORKING FILES ({len(working_files)}):")
    for filename in sorted(working_files):
        print(f"   ✓ {filename}")
    
    if broken_files:
        print(f"\n❌ STILL BROKEN ({len(broken_files)}):")
        # Group by error type
        error_groups = {}
        for filename, error in broken_files:
            error_type = error.split(':')[-1].strip() if ':' in error else error
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(filename)
        
        for error_type, files in error_groups.items():
            print(f"\n   📋 {error_type} ({len(files)} files):")
            for filename in files[:5]:  # Show first 5
                print(f"      ❌ {filename}")
            if len(files) > 5:
                print(f"      ... and {len(files) - 5} more")
    
    print(f"\n🏆 FINAL RESULT: {success_rate:.1f}% of files are now syntax-correct!")
    
    if success_rate > 50:
        print("🎉 Great progress! More than half the files are working!")
    elif success_rate > 25:
        print("👍 Good progress! Keep going!")
    else:
        print("💪 Some files fixed, but more work needed.")

if __name__ == "__main__":
    main()
