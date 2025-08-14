#!/usr/bin/env python3
"""
Comprehensive Syntax Error Fixer
Fixes common syntax errors that appear during bulk edits
"""

import os
import re
import glob
import ast

def fix_missing_commas(content):
    """Fix missing commas in field definitions and other common places"""
    # Fix field definitions missing commas
    patterns = [
        # State field definitions
        (r"(\s+)(\),\s*string='[^']*')", r"\1\2,"),
        (r"(\s+)(\),\s*default='[^']*')", r"\1\2,"),
        (r"(\s+)(\),\s*tracking=True)", r"\1\2,"),
        (r"(\s+)(\),\s*required=True)", r"\1\2,"),
        
        # Selection field patterns
        (r"(\('done', 'Done'\))\s*(\],)", r"\1\2,"),
        (r"(\('cancelled', 'Cancelled'\))\s*(\],)", r"\1\2,"),
        
        # Field parameter patterns
        (r"(tracking=True)\s*(\))", r"\1,\2"),
        (r"(required=True)\s*(\))", r"\1,\2"),
        (r"(default='[^']*')\s*(\))", r"\1,\2"),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def fix_indentation(content):
    """Fix common indentation issues"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Fix lines that start with ) but have wrong indentation
        if line.strip().startswith(')') and i > 0:
            # Find the matching opening parenthesis line to get proper indentation
            prev_line = lines[i-1]
            if '(' in prev_line:
                # Match indentation with the line that has the opening parenthesis
                base_indent = len(prev_line) - len(prev_line.lstrip())
                line = ' ' * base_indent + line.strip()
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_bracket_mismatch(content):
    """Fix bracket mismatches"""
    # Common patterns where } is used instead of )
    content = re.sub(r"(\s+)(\})", r"\1)", content)
    
    return content

def validate_python_syntax(filepath):
    """Check if Python file has valid syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, "Valid syntax"
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def fix_file_syntax(filepath):
    """Fix syntax issues in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply fixes
        original_content = content
        content = fix_missing_commas(content)
        content = fix_indentation(content)
        content = fix_bracket_mismatch(content)
        
        # Only write if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "Fixed syntax issues"
        else:
            return False, "No changes needed"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main function"""
    print("🔧 Comprehensive Syntax Error Fixer")
    print("=" * 50)
    
    # Get all Python files in models directory
    models_dir = "records_management/models"
    python_files = glob.glob(os.path.join(models_dir, "*.py"))
    
    errors_found = 0
    errors_fixed = 0
    
    print(f"Checking {len(python_files)} Python files...\n")
    
    for filepath in sorted(python_files):
        filename = os.path.basename(filepath)
        
        # Skip __init__.py
        if filename == "__init__.py":
            continue
        
        # Check for syntax errors
        is_valid, error_msg = validate_python_syntax(filepath)
        
        if not is_valid:
            errors_found += 1
            print(f"❌ {filename}: {error_msg}")
            
            # Try to fix the file
            fixed, fix_msg = fix_file_syntax(filepath)
            
            if fixed:
                # Validate again after fix
                is_valid_after, _ = validate_python_syntax(filepath)
                if is_valid_after:
                    print(f"   ✅ Fixed: {fix_msg}")
                    errors_fixed += 1
                else:
                    print(f"   ⚠️  Partial fix: {fix_msg} (may need manual review)")
            else:
                print(f"   ⏭️  {fix_msg}")
        
    print(f"\n📊 Summary:")
    print(f"Files with errors: {errors_found}")
    print(f"Files fixed: {errors_fixed}")
    print(f"Files still need manual review: {errors_found - errors_fixed}")
    
    if errors_fixed > 0:
        print(f"\n🎉 Fixed {errors_fixed} files! Run syntax validation again to verify.")

if __name__ == "__main__":
    main()
