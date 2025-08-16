#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Odoo-Aware Syntax Fixer
=====================================

This tool fixes common syntax errors that occur in Odoo modules, with special
attention to Odoo-specific patterns and constructs.

Key Features:
- Handles unterminated triple-quoted strings
- Fixes unmatched parentheses, brackets, and braces
- Corrects missing commas in field definitions
- Fixes indentation issues
- Handles unterminated string literals
- Preserves Odoo-specific patterns
- Maintains proper field definition structure
"""

import os
import re
import ast
import sys
from pathlib import Path

class OdooSyntaxFixer:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.fixes_applied = 0
        self.files_processed = 0
        
    def fix_all_files(self):
        """Fix syntax errors in all Python files in the records_management module"""
        print("🔧 Starting comprehensive Odoo syntax fixing...")
        
        models_dir = self.base_path / "records_management" / "models"
        if not models_dir.exists():
            print(f"❌ Models directory not found: {models_dir}")
            return
            
        # Get all Python files
        python_files = list(models_dir.glob("*.py"))
        print(f"📁 Found {len(python_files)} Python files to process")
        
        for file_path in python_files:
            try:
                self.fix_file(file_path)
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")
                
        print(f"\n✅ Processing complete!")
        print(f"📊 Files processed: {self.files_processed}")
        print(f"🔧 Total fixes applied: {self.fixes_applied}")
        
    def fix_file(self, file_path):
        """Fix syntax errors in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            print(f"⚠️ Encoding issue in {file_path.name}, skipping...")
            return
            
        original_content = content
        
        # Apply various fixes
        content = self.fix_unterminated_triple_quotes(content)
        content = self.fix_unterminated_strings(content)
        content = self.fix_unmatched_parentheses(content)
        content = self.fix_missing_commas(content)
        content = self.fix_indentation_issues(content)
        content = self.fix_invalid_characters(content)
        content = self.fix_bracket_mismatches(content)
        content = self.fix_incomplete_field_definitions(content)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"🔧 Fixed {file_path.name}")
            self.fixes_applied += 1
            
        self.files_processed += 1
        
    def fix_unterminated_triple_quotes(self, content):
        """Fix unterminated triple-quoted strings"""
        lines = content.split('\n')
        fixed_lines = []
        in_triple_quote = False
        quote_type = None
        
        for i, line in enumerate(lines):
            # Check for triple quotes
            if '"""' in line or "'''" in line:
                if '"""' in line:
                    count = line.count('"""')
                    if count % 2 == 1:  # Odd number means opening or closing
                        if not in_triple_quote:
                            in_triple_quote = True
                            quote_type = '"""'
                        else:
                            in_triple_quote = False
                            quote_type = None
                elif "'''" in line:
                    count = line.count("'''")
                    if count % 2 == 1:
                        if not in_triple_quote:
                            in_triple_quote = True
                            quote_type = "'''"
                        else:
                            in_triple_quote = False
                            quote_type = None
            
            fixed_lines.append(line)
            
        # If we're still in a triple quote at the end, close it
        if in_triple_quote and quote_type:
            fixed_lines.append(f'    {quote_type}')
            
        return '\n'.join(fixed_lines)
        
    def fix_unterminated_strings(self, content):
        """Fix unterminated string literals"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Look for unterminated strings
            if line.strip().endswith("'") and line.count("'") % 2 == 1:
                # Check if it's not a comment
                if '#' not in line or line.index("'") < line.index('#'):
                    line = line + "'"
            elif line.strip().endswith('"') and line.count('"') % 2 == 1:
                if '#' not in line or line.index('"') < line.index('#'):
                    line = line + '"'
                    
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines)
        
    def fix_unmatched_parentheses(self, content):
        """Fix unmatched parentheses"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Count parentheses
            open_parens = line.count('(')
            close_parens = line.count(')')
            
            if open_parens > close_parens:
                # Add missing closing parentheses
                diff = open_parens - close_parens
                # Only add if line doesn't end with comma (multi-line definition)
                if not line.rstrip().endswith(','):
                    line = line + ')' * diff
            elif close_parens > open_parens:
                # Remove extra closing parentheses
                diff = close_parens - open_parens
                for _ in range(diff):
                    line = line.rsplit(')', 1)[0] if ')' in line else line
                    
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines)
        
    def fix_missing_commas(self, content):
        """Fix missing commas in field definitions"""
        lines = content.split('\n')
        fixed_lines = []
        
        field_pattern = re.compile(r'^\s*\w+\s*=\s*fields\.\w+\([^)]*\)$')
        
        for i, line in enumerate(lines):
            # Check if this looks like a field definition without a comma
            if field_pattern.match(line):
                # Check if next line is also a field or method definition
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if (next_line and 
                        not next_line.startswith('#') and 
                        ('=' in next_line or next_line.startswith('def ') or next_line.startswith('@'))):
                        # Add comma if missing
                        if not line.rstrip().endswith(','):
                            line = line + ','
                            
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines)
        
    def fix_indentation_issues(self, content):
        """Fix basic indentation issues"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix unexpected indents after class or def
            if line.strip().startswith('class ') or line.strip().startswith('def '):
                # Ensure proper indentation level
                indent_level = len(line) - len(line.lstrip())
                if indent_level > 0 and not line.lstrip().startswith('@'):
                    line = line.lstrip()  # Remove unexpected indent
                    
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines)
        
    def fix_invalid_characters(self, content):
        """Fix invalid characters like arrows"""
        # Replace arrow characters with comments
        content = content.replace('→', '# ->')
        content = content.replace('←', '# <-')
        return content
        
    def fix_bracket_mismatches(self, content):
        """Fix bracket and brace mismatches"""
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix common bracket issues
            open_brackets = line.count('[')
            close_brackets = line.count(']')
            
            if open_brackets > close_brackets:
                diff = open_brackets - close_brackets
                if not line.rstrip().endswith(','):
                    line = line + ']' * diff
            elif close_brackets > open_brackets:
                diff = close_brackets - open_brackets
                for _ in range(diff):
                    line = line.rsplit(']', 1)[0] if ']' in line else line
                    
            # Fix brace issues
            open_braces = line.count('{')
            close_braces = line.count('}')
            
            if open_braces > close_braces:
                diff = open_braces - close_braces
                if not line.rstrip().endswith(','):
                    line = line + '}' * diff
            elif close_braces > open_braces:
                diff = close_braces - open_braces
                for _ in range(diff):
                    line = line.rsplit('}', 1)[0] if '}' in line else line
                    
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines)
        
    def fix_incomplete_field_definitions(self, content):
        """Fix incomplete field definitions"""
        # Pattern to match incomplete field definitions
        patterns = [
            (r'(\w+\s*=\s*fields\.\w+\([^)]*$)', r'\1)'),  # Missing closing paren
            (r'(string=)"([^"]*$)', r'\1"\2"'),  # Unterminated string parameter
            (r"(string=)'([^']*$)", r"\1'\2'"),  # Unterminated string parameter
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
        return content

def main():
    """Main function to run the syntax fixer"""
    base_path = Path.cwd()
    
    # Check if we're in the right directory
    if not (base_path / "records_management").exists():
        print("❌ records_management directory not found!")
        print("Please run this script from the project root directory.")
        return 1
        
    fixer = OdooSyntaxFixer(base_path)
    fixer.fix_all_files()
    
    print("\n🔍 Running syntax validation to check results...")
    
    # Try to run the syntax checker if it exists
    syntax_checker = base_path / "development-tools" / "syntax-tools" / "find_syntax_errors.py"
    if syntax_checker.exists():
        os.system(f"python {syntax_checker}")
    else:
        print("⚠️ Syntax checker not found, please run manual validation")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
