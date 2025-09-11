#!/usr/bin/env python3
"""
Comprehensive Syntax Validator for Records Management Module
Finds all syntax errors, mismatched parentheses, unclosed brackets, and common Python issues
"""

import os
import ast
import sys
import re
from typing import List, Dict, Tuple

class SyntaxValidator:
    def __init__(self, module_path: str):
        self.module_path = module_path
        self.errors = []
        self.warnings = []
        
    def validate_all_files(self):
        """Validate all Python files in the module"""
        print("🔍 Starting comprehensive syntax validation...")
        
        python_files = self._find_python_files()
        print(f"Found {len(python_files)} Python files to validate")
        
        for file_path in python_files:
            relative_path = os.path.relpath(file_path, self.module_path)
            print(f"\n📄 Validating: {relative_path}")
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                self._add_error(relative_path, 0, f"Cannot read file: {e}")
                continue
            
            # Run all validation checks
            self._validate_python_syntax(file_path, relative_path, content)
            self._validate_brackets_parentheses(file_path, relative_path, content)
            self._validate_string_quotes(file_path, relative_path, content)
            self._validate_indentation(file_path, relative_path, content)
            self._validate_odoo_specific(file_path, relative_path, content)
        
        self._print_summary()
    
    def _find_python_files(self) -> List[str]:
        """Find all Python files in the module"""
        python_files = []
        
        for root, dirs, files in os.walk(self.module_path):
            # Skip __pycache__ directories
            dirs[:] = [d for d in dirs if d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        return sorted(python_files)
    
    def _validate_python_syntax(self, file_path: str, relative_path: str, content: str):
        """Validate Python syntax using AST"""
        try:
            ast.parse(content, filename=file_path)
            print(f"  ✅ Python syntax: OK")
        except SyntaxError as e:
            self._add_error(relative_path, e.lineno or 0, 
                          f"SyntaxError: {e.msg} (line {e.lineno}, col {e.offset})")
            print(f"  ❌ Python syntax: SyntaxError on line {e.lineno}")
        except Exception as e:
            self._add_error(relative_path, 0, f"Parse error: {e}")
            print(f"  ❌ Python syntax: Parse error")
    
    def _validate_brackets_parentheses(self, file_path: str, relative_path: str, content: str):
        """Validate matching brackets and parentheses"""
        lines = content.split('\n')
        stack = []
        brackets = {'(': ')', '[': ']', '{': '}'}
        
        errors_found = 0
        
        for line_num, line in enumerate(lines, 1):
            # Skip comments and strings (basic detection)
            in_string = False
            in_comment = False
            i = 0
            
            while i < len(line):
                char = line[i]
                
                # Handle string literals
                if char in ['"', "'"] and not in_comment:
                    if not in_string:
                        in_string = char
                    elif in_string == char:
                        in_string = False
                
                # Handle comments
                elif char == '#' and not in_string:
                    in_comment = True
                
                # Handle brackets/parentheses
                elif not in_string and not in_comment:
                    if char in brackets:
                        stack.append((char, line_num, i + 1))
                    elif char in brackets.values():
                        if not stack:
                            self._add_error(relative_path, line_num, 
                                          f"Unmatched closing '{char}' at column {i + 1}")
                            errors_found += 1
                        else:
                            opener, open_line, open_col = stack.pop()
                            if brackets[opener] != char:
                                self._add_error(relative_path, line_num,
                                              f"Mismatched bracket: '{opener}' (line {open_line}) closed with '{char}' (line {line_num})")
                                errors_found += 1
                
                i += 1
        
        # Check for unclosed brackets
        for opener, line_num, col in stack:
            self._add_error(relative_path, line_num, 
                          f"Unclosed '{opener}' at line {line_num}, column {col}")
            errors_found += 1
        
        if errors_found == 0:
            print(f"  ✅ Brackets/Parentheses: OK")
        else:
            print(f"  ❌ Brackets/Parentheses: {errors_found} errors")
    
    def _validate_string_quotes(self, file_path: str, relative_path: str, content: str):
        """Validate string quote matching"""
        lines = content.split('\n')
        errors_found = 0
        
        for line_num, line in enumerate(lines, 1):
            # Check for unmatched quotes (simple detection)
            single_quotes = line.count("'")
            double_quotes = line.count('"')
            
            # Skip lines with triple quotes
            if '"""' in line or "'''" in line:
                continue
            
            # Check for basic quote mismatches
            if single_quotes % 2 != 0 and line.strip() and not line.strip().startswith('#'):
                self._add_warning(relative_path, line_num, "Possible unmatched single quote")
                errors_found += 1
            
            if double_quotes % 2 != 0 and line.strip() and not line.strip().startswith('#'):
                self._add_warning(relative_path, line_num, "Possible unmatched double quote")
                errors_found += 1
        
        if errors_found == 0:
            print(f"  ✅ String quotes: OK")
        else:
            print(f"  ⚠️  String quotes: {errors_found} warnings")
    
    def _validate_indentation(self, file_path: str, relative_path: str, content: str):
        """Validate Python indentation"""
        lines = content.split('\n')
        errors_found = 0
        
        for line_num, line in enumerate(lines, 1):
            if line.strip():  # Skip empty lines
                # Check for tabs mixed with spaces
                if '\t' in line and ' ' in line.replace('\t', ''):
                    leading_whitespace = line[:len(line) - len(line.lstrip())]
                    if '\t' in leading_whitespace and ' ' in leading_whitespace:
                        self._add_warning(relative_path, line_num, "Mixed tabs and spaces in indentation")
                        errors_found += 1
        
        if errors_found == 0:
            print(f"  ✅ Indentation: OK")
        else:
            print(f"  ⚠️  Indentation: {errors_found} warnings")
    
    def _validate_odoo_specific(self, file_path: str, relative_path: str, content: str):
        """Validate Odoo-specific syntax patterns"""
        lines = content.split('\n')
        errors_found = 0
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for common Odoo field definition issues
            if 'fields.' in stripped and '=' in stripped:
                # Check for missing commas in field definitions
                if stripped.endswith('fields.Char(') or stripped.endswith('fields.Text('):
                    if line_num < len(lines):
                        next_line = lines[line_num].strip()
                        if next_line and not next_line.startswith(('"', "'", 'string=', 'help=', 'required=', 'default=')):
                            self._add_warning(relative_path, line_num, "Possible incomplete field definition")
                            errors_found += 1
            
            # Check for selection field syntax
            if 'fields.Selection(' in stripped and '[' in stripped:
                bracket_count = stripped.count('[') - stripped.count(']')
                if bracket_count > 0 and not stripped.endswith(','):
                    # This might be a multi-line selection - check if properly closed
                    closing_found = False
                    for check_line_num in range(line_num, min(line_num + 10, len(lines))):
                        if check_line_num < len(lines) and ']' in lines[check_line_num]:
                            closing_found = True
                            break
                    if not closing_found:
                        self._add_warning(relative_path, line_num, "Possible unclosed Selection field")
                        errors_found += 1
        
        if errors_found == 0:
            print(f"  ✅ Odoo-specific: OK")
        else:
            print(f"  ⚠️  Odoo-specific: {errors_found} warnings")
    
    def _add_error(self, file: str, line: int, message: str):
        """Add an error to the list"""
        self.errors.append({
            'file': file,
            'line': line,
            'type': 'ERROR',
            'message': message
        })
    
    def _add_warning(self, file: str, line: int, message: str):
        """Add a warning to the list"""
        self.warnings.append({
            'file': file,
            'line': line,
            'type': 'WARNING',
            'message': message
        })
    
    def _print_summary(self):
        """Print validation summary"""
        print("\n" + "="*80)
        print("📊 VALIDATION SUMMARY")
        print("="*80)
        
        if not self.errors and not self.warnings:
            print("🎉 NO ISSUES FOUND! All files are syntactically correct.")
            return
        
        # Print errors
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            print("-" * 40)
            for error in self.errors:
                print(f"  📄 {error['file']}:{error['line']}")
                print(f"     {error['message']}")
                print()
        
        # Print warnings
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            print("-" * 40)
            for warning in self.warnings:
                print(f"  📄 {warning['file']}:{warning['line']}")
                print(f"     {warning['message']}")
                print()
        
        print(f"\n📈 STATISTICS:")
        print(f"  🔴 Errors:   {len(self.errors)}")
        print(f"  🟡 Warnings: {len(self.warnings)}")
        print(f"  📁 Total:    {len(self.errors) + len(self.warnings)} issues")
        
        if self.errors:
            print(f"\n💡 NEXT STEPS:")
            print(f"  1. Fix the {len(self.errors)} syntax errors first")
            print(f"  2. Address warnings for better code quality")
            print(f"  3. Run this script again to verify fixes")
    
    def fix_common_issues(self):
        """Attempt to fix common syntax issues automatically"""
        print("\n🔧 ATTEMPTING TO FIX COMMON ISSUES...")
        
        fixed_files = []
        
        for error in self.errors:
            if "mismatched" in error['message'].lower() or "unclosed" in error['message'].lower():
                file_path = os.path.join(self.module_path, error['file'])
                if self._try_fix_bracket_issue(file_path, error):
                    fixed_files.append(error['file'])
        
        if fixed_files:
            print(f"✅ Attempted fixes in {len(set(fixed_files))} files")
            print("🔄 Please run validation again to check results")
        else:
            print("ℹ️  No automatic fixes available for current issues")

    def _try_fix_bracket_issue(self, file_path: str, error: Dict) -> bool:
        """Try to fix simple bracket/parenthesis issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            line_idx = error['line'] - 1
            if line_idx < len(lines):
                line = lines[line_idx]
                
                # Simple fixes for common patterns
                if "closing parenthesis ')' does not match opening parenthesis '['" in error['message']:
                    # Replace ')' with ']' at the end of line
                    if line.rstrip().endswith(')'):
                        lines[line_idx] = line.rstrip()[:-1] + ']\n'
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.writelines(lines)
                        return True
            
        except Exception as e:
            print(f"❌ Could not fix {file_path}: {e}")
        
        return False

def main():
    module_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management'
    
    if not os.path.exists(module_path):
        print(f"❌ Module path not found: {module_path}")
        return
    
    validator = SyntaxValidator(module_path)
    validator.validate_all_files()
    
    # Ask if user wants to attempt automatic fixes
    if validator.errors:
        print(f"\n🤖 Would you like to attempt automatic fixes for common issues?")
        print(f"   (This will modify files - make sure you have backups!)")
        
        # For now, we'll attempt fixes automatically
        validator.fix_common_issues()

if __name__ == "__main__":
    main()
