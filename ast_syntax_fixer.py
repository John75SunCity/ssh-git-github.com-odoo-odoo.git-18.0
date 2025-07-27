#!/usr/bin/env python3
"""
Advanced Python AST-based syntax fixer
Uses Python's AST parser to identify and fix specific syntax patterns
"""

import ast
import os
import re

def check_and_fix_python_file(filepath):
    """
    Use AST parsing to identify syntax errors and apply targeted fixes
    """
    print(f"Processing: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    fixed = False
    
    # Try to parse with AST first
    try:
        ast.parse(content)
        print(f"  ✅ {filepath} - Already valid syntax")
        return False
    except SyntaxError as e:
        print(f"  🔧 {filepath} - Line {e.lineno}: {e.msg}")
        
        # Apply targeted fixes based on common patterns
        lines = content.split('\n')
        
        # Fix 1: Missing closing bracket in Selection fields
        if "closing parenthesis ')' does not match opening parenthesis '['" in str(e):
            for i, line in enumerate(lines):
                if 'fields.Selection([' in line and i + 1 < len(lines):
                    # Look for the problematic closing pattern
                    j = i + 1
                    while j < len(lines) and not ('fields.' in lines[j] or lines[j].strip().startswith('def ') or lines[j].strip() == ''):
                        if '), string=' in lines[j] and '[' in ''.join(lines[i:j+1]):
                            # This should be ], string=
                            lines[j] = lines[j].replace('), string=', '], string=')
                            fixed = True
                            break
                        j += 1
        
        # Fix 2: Missing closing parentheses in general
        elif "'(' was never closed" in str(e) or "was not closed" in str(e):
            error_line = e.lineno - 1
            if error_line < len(lines):
                line = lines[error_line]
                
                # Simple heuristic: add missing closing parenthesis
                if line.count('(') > line.count(')'):
                    missing_parens = line.count('(') - line.count(')')
                    lines[error_line] = line.rstrip() + ')' * missing_parens
                    fixed = True
        
        # Fix 3: Missing comma patterns
        elif "Perhaps you forgot a comma?" in str(e):
            error_line = e.lineno - 1
            if error_line < len(lines) and error_line > 0:
                # Check previous line for missing comma
                prev_line = lines[error_line - 1]
                if (prev_line.strip().endswith("'") or prev_line.strip().endswith('"')) and not prev_line.strip().endswith(','):
                    lines[error_line - 1] = prev_line.rstrip() + ','
                    fixed = True
        
        # Fix 4: Invalid syntax for class definitions
        elif "invalid syntax" in str(e) and error_line < len(lines):
            line = lines[error_line]
            if 'class ' in line and '(models.Model:' in line:
                lines[error_line] = line.replace('(models.Model:', '(models.Model):')
                fixed = True
        
        if fixed:
            new_content = '\n'.join(lines)
            
            # Verify the fix worked
            try:
                ast.parse(new_content)
                print(f"  ✅ Fixed successfully!")
                
                # Write the fixed content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True
                
            except SyntaxError as new_e:
                print(f"  ⚠️  Fix didn't work, trying different approach...")
                # Try more fixes...
                return try_regex_fixes(filepath, original_content)
        else:
            print(f"  ❌ Could not automatically fix")
            return False
    
    except Exception as e:
        print(f"  ❌ Error processing {filepath}: {e}")
        return False

def try_regex_fixes(filepath, content):
    """Apply regex-based fixes for common patterns"""
    print(f"  🔧 Applying regex fixes to {filepath}")
    
    original_content = content
    
    # Fix Selection field patterns
    content = re.sub(r'(\s+)\), string="Selection Field"\)', r'\1], string="Selection Field")', content)
    content = re.sub(r'(\s+)\), string=\'([^\']+)\'\)', r'\1], string=\'\2\')', content)
    
    # Fix missing commas in tuple definitions
    content = re.sub(r"(\('[^']*', '[^']*'\))(\s*)$", r"\1,\2", content, flags=re.MULTILINE)
    
    # Fix class definitions
    content = re.sub(r'class\s+(\w+)\(models\.Model:', r'class \1(models.Model):', content)
    
    # Fix incomplete field definitions
    content = re.sub(r"help='([^']+)'$", r"help='\1',", content, flags=re.MULTILINE)
    
    if content != original_content:
        try:
            ast.parse(content)
            print(f"  ✅ Regex fixes worked!")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except SyntaxError:
            print(f"  ❌ Regex fixes didn't work")
            return False
    
    return False

def main():
    """Process all Python files in records_management/models/"""
    
    models_dir = "records_management/models"
    if not os.path.exists(models_dir):
        print(f"Directory not found: {models_dir}")
        return
    
    python_files = []
    for file in os.listdir(models_dir):
        if file.endswith('.py') and not file.startswith('__'):
            python_files.append(os.path.join(models_dir, file))
    
    print(f"🔍 Found {len(python_files)} Python files to check")
    print("=" * 60)
    
    fixed_count = 0
    error_count = 0
    
    for filepath in sorted(python_files):
        try:
            if check_and_fix_python_file(filepath):
                fixed_count += 1
        except Exception as e:
            print(f"  ❌ Error with {filepath}: {e}")
            error_count += 1
    
    print("=" * 60)
    print(f"📊 SUMMARY:")
    print(f"✅ Files fixed: {fixed_count}")
    print(f"❌ Files with errors: {error_count}")
    print(f"📁 Total processed: {len(python_files)}")

if __name__ == "__main__":
    main()
