#!/usr/bin/env python3
"""
Final Syntax Fixer for Records Management Module
Comprehensive fix for all remaining syntax patterns
"""

import os
import re
import subprocess

def fix_selection_field_brackets(content):
    """Fix Selection fields with wrong bracket types"""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Look for Selection field starts
        if 'fields.Selection([' in line:
            # Track if we're in a Selection field
            selection_lines = [line]
            bracket_depth = line.count('[') - line.count(']')
            paren_depth = line.count('(') - line.count(')')
            j = i + 1
            
            # Collect all lines until Selection is complete
            while j < len(lines) and (bracket_depth > 0 or paren_depth > 1):
                selection_lines.append(lines[j])
                bracket_depth += lines[j].count('[') - lines[j].count(']')
                paren_depth += lines[j].count('(') - lines[j].count(')')
                j += 1
            
            # Check if the last line has wrong bracket type
            if j < len(lines) and ('), string=' in lines[j] or lines[j].strip() == ')'):
                # Need to fix this - should be ], string= not ), string=
                if '), string=' in lines[j]:
                    lines[j] = lines[j].replace('), string=', '], string=')
                elif lines[j].strip() == ')':
                    lines[j] = lines[j].replace(')', ']')
                selection_lines.append(lines[j])
                j += 1
            
            # Add all the selection lines
            fixed_lines.extend(selection_lines)
            i = j
        else:
            fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines)

def fix_missing_closing_parentheses(content):
    """Fix field definitions missing closing parentheses"""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for field definitions that might need closing parens
        if ('fields.' in line and '(' in line and 
            not line.strip().endswith(')') and 
            not line.strip().endswith(',') and
            not 'fields.Selection(' in line):  # Skip Selection fields
            
            # Look ahead to see what comes next
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                
                # If next line is a new field, method, or empty, close this field
                if (next_line.startswith(('def ', 'class ', '@', '#')) or
                    'fields.' in next_line or
                    next_line == '' or
                    next_line.startswith('_') or
                    i + 1 == len(lines) - 1):
                    
                    if not line.strip().endswith(')'):
                        line = line.rstrip() + ')'
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_missing_commas(content):
    """Fix missing commas in field definitions"""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Fix specific patterns that need commas
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            
            # Pattern: string ending with quote, next line has parameter
            if (stripped.endswith("'") or stripped.endswith('"')) and next_line:
                if (next_line.startswith(('ondelete=', 'help=', 'string=', 'default=', 'required=', 'tracking=')) and
                    not stripped.endswith(',') and not stripped.endswith(')')):
                    line = line.rstrip() + ','
            
            # Pattern: help= parameter missing comma
            elif 'help=' in stripped and not stripped.endswith(',') and not stripped.endswith(')'):
                if next_line and not next_line.startswith(')'):
                    line = line.rstrip() + ','
            
            # Pattern: tuple in Selection missing comma
            elif re.search(r"\('[^']*',\s*'[^']*'\)$", stripped):
                if (next_line.startswith(('], string=', '), string=')) or 
                    next_line.startswith(('(', "'")) or
                    re.match(r"^\s*\('[^']*',", next_line)):
                    if not stripped.endswith(','):
                        line = line.rstrip() + ','
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

def fix_specific_issues(content):
    """Fix specific syntax issues"""
    
    # Fix logger definitions
    content = re.sub(r'_logger = logging\.getLogger\(__name__$', 
                     '_logger = logging.getLogger(__name__)', content)
    
    # Fix incomplete string literals
    content = re.sub(r"help='([^']+)'$", r"help='\1',", content, flags=re.MULTILINE)
    
    # Fix double closing parens in Selection fields
    content = re.sub(r'\)\), string=', '), string=', content)
    
    # Fix trailing commas in Selection tuples
    content = re.sub(r"',\), string=", "'), string=", content)
    
    # Fix search domain missing closing bracket
    content = re.sub(r"search\(\[([^\]]+)$", r"search([\1])", content, flags=re.MULTILINE)
    
    # Fix incomplete if statements
    content = re.sub(r'if ([^:]+):$\s*$', r'if \1:\n    pass', content, flags=re.MULTILINE)
    
    return content

def fix_file(filepath):
    """Fix a single file comprehensively"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Apply all fixes
        content = fix_selection_field_brackets(content)
        content = fix_missing_closing_parentheses(content)
        content = fix_missing_commas(content)
        content = fix_specific_issues(content)
        
        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Test the syntax
            result = subprocess.run(['python3', '-m', 'py_compile', filepath], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        
        return None  # No changes made
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Fix all files systematically"""
    
    # Get all Python files in models directory
    models_dir = 'records_management/models'
    python_files = []
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            python_files.append(os.path.join(models_dir, filename))
    
    python_files.sort()
    
    print("🔧 Final Comprehensive Syntax Fixer")
    print("=" * 50)
    print(f"Processing {len(python_files)} model files")
    print()
    
    fixed_count = 0
    unchanged_count = 0
    error_count = 0
    
    for i, filepath in enumerate(python_files, 1):
        print(f"[{i:2d}/{len(python_files)}] {os.path.basename(filepath)}...", end=" ")
        
        result = fix_file(filepath)
        
        if result is True:
            print("✅ FIXED")
            fixed_count += 1
        elif result is False:
            print("❌ STILL ERROR")
            error_count += 1
        else:
            print("⚪ UNCHANGED")
            unchanged_count += 1
    
    print()
    print("=" * 50)
    print(f"✅ Fixed: {fixed_count}")
    print(f"⚪ Unchanged: {unchanged_count}")
    print(f"❌ Still errors: {error_count}")
    print(f"📊 Total processed: {len(python_files)}")

if __name__ == '__main__':
    main()
