#!/usr/bin/env python3
"""
Comprehensive syntax error detector and fixer for Records Management module
Uses AST parsing to identify exact syntax errors and fix them systematically
"""

import os
import ast
import re
import subprocess
import sys
from pathlib import Path

def analyze_syntax_errors(file_path):
    """Analyze a Python file for syntax errors using AST"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse with AST
        try:
            ast.parse(content)
            return True, None, content
        except SyntaxError as e:
            return False, e, content
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False, None, None

def fix_common_syntax_patterns(content):
    """Fix common syntax error patterns"""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Pattern 1: Selection field with missing closing bracket/parenthesis
        if 'fields.Selection([' in line and not line.strip().endswith('])'):
            # Look ahead to find the proper closing
            bracket_count = line.count('[') - line.count(']')
            paren_count = line.count('(') - line.count(')')
            j = i + 1
            
            while j < len(lines) and (bracket_count > 0 or paren_count > 0):
                next_line = lines[j]
                bracket_count += next_line.count('[') - next_line.count(']')
                paren_count += next_line.count('(') - next_line.count(')')
                
                # If we hit another field definition, fix the previous one
                if ('fields.' in next_line and '=' in next_line) or next_line.strip().startswith('def '):
                    # Fix the previous line
                    if bracket_count > 0:
                        lines[j-1] = lines[j-1].rstrip() + '], string="Selection Field")'
                    elif paren_count > 0:
                        lines[j-1] = lines[j-1].rstrip() + ')'
                    break
                j += 1
        
        # Pattern 2: List with missing closing bracket
        elif re.search(r'=\s*\[', line) and '[' in line and ']' not in line:
            # Look ahead for closing bracket
            bracket_count = line.count('[') - line.count(']')
            j = i + 1
            
            while j < len(lines) and bracket_count > 0:
                next_line = lines[j]
                bracket_count += next_line.count('[') - next_line.count(']')
                
                # If we hit another assignment or field, close the list
                if ('=' in next_line and 'fields.' in next_line) or next_line.strip().startswith('def '):
                    lines[j-1] = lines[j-1].rstrip() + ']'
                    break
                j += 1
        
        # Pattern 3: Comments with malformed closing parenthesis
        elif line.strip().endswith(')') and not line.strip().startswith('#'):
            # Check if this is a malformed comment
            if ')' in line and '# ' not in line and line.count('(') < line.count(')'):
                # Remove extra closing parenthesis
                lines[i] = line.replace(')', '', 1)
        
        # Pattern 4: Field definitions that are cut off
        elif 'fields.' in line and '(' in line and ')' not in line:
            paren_count = line.count('(') - line.count(')')
            j = i + 1
            
            while j < len(lines) and paren_count > 0:
                next_line = lines[j]
                paren_count += next_line.count('(') - next_line.count(')')
                
                # If we hit another field definition, close the previous one
                if ('fields.' in next_line and '=' in next_line) or next_line.strip().startswith('def '):
                    lines[j-1] = lines[j-1].rstrip() + ')'
                    break
                j += 1
        
        fixed_lines.append(lines[i])
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_specific_patterns(content):
    """Fix specific known patterns"""
    # Fix Selection fields that are incomplete
    content = re.sub(
        r"fields\.Selection\(\[\s*([^]]+)\s*\n\s*\)\s*$",
        r"fields.Selection([\1], string='Selection')",
        content,
        flags=re.MULTILINE
    )
    
    # Fix lists that are missing closing brackets
    content = re.sub(
        r"=\s*\[\s*([^]]+)\s*\n\s*$",
        r"= [\1]",
        content,
        flags=re.MULTILINE
    )
    
    # Remove malformed comment closures
    content = re.sub(r'# ([^)]+)\)', r'# \1', content)
    
    return content

def fix_syntax_errors_comprehensive(file_path):
    """Comprehensively fix syntax errors in a file"""
    print(f"Analyzing {file_path}...")
    
    is_valid, error, content = analyze_syntax_errors(file_path)
    
    if is_valid:
        print(f"  ✅ {file_path} - No syntax errors")
        return True
    
    if content is None:
        print(f"  ❌ {file_path} - Could not read file")
        return False
    
    print(f"  🔧 {file_path} - Syntax error: {error}")
    
    # Apply fixes
    fixed_content = fix_common_syntax_patterns(content)
    fixed_content = fix_specific_patterns(fixed_content)
    
    # Write back the fixed content
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        # Test the fix
        is_valid_after, error_after, _ = analyze_syntax_errors(file_path)
        
        if is_valid_after:
            print(f"  ✅ {file_path} - Fixed successfully!")
            return True
        else:
            print(f"  ⚠️  {file_path} - Still has errors: {error_after}")
            return False
            
    except Exception as e:
        print(f"  ❌ {file_path} - Error writing file: {e}")
        return False

def find_all_python_files():
    """Find all Python files in the records_management module"""
    python_files = []
    records_dir = Path("records_management")
    
    if records_dir.exists():
        for py_file in records_dir.rglob("*.py"):
            if py_file.name != "__pycache__":
                python_files.append(str(py_file))
    
    return python_files

def main():
    """Main function to fix all syntax errors"""
    print("🔍 Comprehensive Syntax Error Analysis and Fixing")
    print("=" * 60)
    
    # Find all Python files
    python_files = find_all_python_files()
    
    if not python_files:
        print("No Python files found in records_management/")
        return
    
    print(f"Found {len(python_files)} Python files to analyze\n")
    
    # Analyze each file
    results = {}
    for py_file in python_files:
        is_valid, error, _ = analyze_syntax_errors(py_file)
        results[py_file] = (is_valid, error)
    
    # Show summary of errors
    error_files = [f for f, (valid, _) in results.items() if not valid]
    
    if not error_files:
        print("🎉 No syntax errors found!")
        return
    
    print(f"📋 Found syntax errors in {len(error_files)} files:")
    for i, file_path in enumerate(error_files, 1):
        _, error = results[file_path]
        print(f"  {i}. {file_path}")
        if error:
            print(f"     Line {error.lineno}: {error.msg}")
    
    print(f"\n🔧 Fixing {len(error_files)} files with syntax errors...\n")
    
    # Fix each file
    fixed_count = 0
    for file_path in error_files:
        if fix_syntax_errors_comprehensive(file_path):
            fixed_count += 1
    
    print(f"\n📊 SUMMARY")
    print("=" * 30)
    print(f"Total files analyzed: {len(python_files)}")
    print(f"Files with errors: {len(error_files)}")
    print(f"Files fixed: {fixed_count}")
    print(f"Success rate: {fixed_count}/{len(error_files)} ({100*fixed_count/len(error_files) if error_files else 100:.1f}%)")
    
    if fixed_count == len(error_files):
        print("\n🎉 All syntax errors fixed successfully!")
    else:
        print(f"\n⚠️  {len(error_files) - fixed_count} files still have errors - manual review needed")
    
    # Final validation
    print("\n🔍 Final validation...")
    all_valid = True
    for py_file in python_files:
        is_valid, error, _ = analyze_syntax_errors(py_file)
        if not is_valid:
            print(f"  ❌ {py_file}: {error}")
            all_valid = False
    
    if all_valid:
        print("✅ All Python files have valid syntax!")
    else:
        print("❌ Some files still have syntax errors")

if __name__ == "__main__":
    main()
