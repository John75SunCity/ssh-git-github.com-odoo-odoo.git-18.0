#!/usr/bin/env python3
"""
Indentation Fixer for Odoo Records Management Module
====================================================

This tool fixes Python indentation errors systematically.
It normalizes all indentation to 4 spaces and fixes unexpected indents.

Usage: python indentation_fixer.py
"""

import os
import re
from pathlib import Path

class IndentationFixer:
    def __init__(self, module_path):
        self.module_path = Path(module_path)
        self.fixes_applied = 0

    def fix_file_indentation(self, file_path):
        """Fix indentation in a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            fixed_lines = []
            
            for line in lines:
                if not line.strip():  # Empty line
                    fixed_lines.append('\n')
                    continue
                    
                # Count current indentation level
                original_indent = len(line) - len(line.lstrip())
                
                # Normalize to 4-space indentation
                if original_indent > 0:
                    # Calculate proper indentation level (divisible by 4)
                    indent_level = original_indent // 4
                    if original_indent % 4 != 0:
                        # If not divisible by 4, round down to nearest 4-space level
                        pass
                    
                    # Apply 4-space indentation
                    fixed_line = '    ' * indent_level + line.lstrip()
                else:
                    fixed_line = line.lstrip()
                    
                fixed_lines.append(fixed_line)
                
            # Write back if changed
            new_content = ''.join(fixed_lines)
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            if new_content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True
                
        except Exception as e:
            print(f"  ❌ Error fixing {file_path}: {e}")
            
        return False

    def fix_all_indentation(self):
        """Fix indentation in all Python files"""
        print("🔧 Fixing indentation in all Python files...")
        
        py_files = list(self.module_path.rglob("*.py"))
        
        for py_file in py_files:
            if '__pycache__' in str(py_file):
                continue
                
            if self.fix_file_indentation(py_file):
                print(f"  ✅ Fixed {py_file.relative_to(self.module_path)}")
                self.fixes_applied += 1

    def validate_syntax(self):
        """Validate syntax after fixes"""
        print("\n🔍 Validating syntax...")
        
        py_files = list(self.module_path.rglob("*.py"))
        errors = []
        
        for py_file in py_files:
            if '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                compile(content, py_file, 'exec')
                
            except SyntaxError as e:
                errors.append(f"{py_file.relative_to(self.module_path)}:{e.lineno}: {e.msg}")
            except Exception as e:
                errors.append(f"{py_file.relative_to(self.module_path)}: {e}")
                
        if errors:
            print(f"  ⚠️  {len(errors)} syntax errors remain:")
            for error in errors[:5]:
                print(f"    - {error}")
            if len(errors) > 5:
                print(f"    ... and {len(errors) - 5} more")
            return False
        else:
            print("  ✅ All syntax errors fixed!")
            return True

    def run_indentation_fix(self):
        """Run complete indentation fixing"""
        print("🚀 Indentation Fixer")
        print("=" * 40)
        
        self.fix_all_indentation()
        syntax_ok = self.validate_syntax()
        
        print(f"\n📊 Files fixed: {self.fixes_applied}")
        
        if syntax_ok:
            print("✅ All indentation issues resolved!")
            return True
        else:
            print("⚠️  Some syntax errors remain")
            return False


if __name__ == "__main__":
    module_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    fixer = IndentationFixer(module_path)
    success = fixer.run_indentation_fix()
    
    if not success:
        print("\n🔧 Running module validation to see remaining issues...")
        import subprocess
        subprocess.run(["python", "development-tools/module_validation.py"], 
                      cwd="/workspaces/ssh-git-github.com-odoo-odoo.git-18.0")
