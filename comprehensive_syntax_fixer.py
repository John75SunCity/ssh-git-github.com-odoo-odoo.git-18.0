#!/usr/bin/env python3
"""
Comprehensive Python syntax fixer for Records Management models.

This script fixes the widespread syntax issues caused by the automated cleanup that removed
closing parentheses and commas from field definitions across 80+ files.

Patterns Fixed:
1. Missing closing parentheses: 'string="Name", required=True' -> 'string="Name", required=True)'
2. Missing commas between field definitions
3. Orphaned closing parentheses that were missed
4. Field definitions that are not properly terminated
"""

import os
import re
import ast

def fix_field_definitions_comprehensive(content):
    """Fix missing parentheses and commas in field definitions"""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Look for field definitions that start with: field_name = fields.FieldType(
        field_def_match = re.match(r'^(\s*)(\w+)\s*=\s*fields\.\w+\(', line)
        
        if field_def_match:
            indent = field_def_match.group(1)
            field_name = field_def_match.group(2)
            
            # This is the start of a field definition
            # Collect all lines until we find the end
            field_lines = [line]
            j = i + 1
            paren_count = line.count('(') - line.count(')')
            
            # Keep collecting lines until parentheses are balanced
            while j < len(lines) and paren_count > 0:
                next_line = lines[j]
                field_lines.append(next_line)
                paren_count += next_line.count('(') - next_line.count(')')
                j += 1
            
            # If we never balanced parentheses, we need to add a closing paren
            if paren_count > 0:
                # Find the last non-empty line with content
                last_content_line_idx = len(field_lines) - 1
                while (last_content_line_idx >= 0 and 
                       not field_lines[last_content_line_idx].strip()):
                    last_content_line_idx -= 1
                
                if last_content_line_idx >= 0:
                    # Add closing parenthesis to the last content line
                    field_lines[last_content_line_idx] = field_lines[last_content_line_idx].rstrip() + ')'
                    print(f"  Fixed missing closing paren for field '{field_name}'")
            
            # Add the field lines to output
            for line in field_lines:
                fixed_lines.append(line)
            
            # Check if we need a comma after this field
            if j < len(lines):
                next_line = lines[j].strip()
                # If next line is another field definition, ensure we have a comma
                if (re.match(r'^\w+\s*=\s*fields\.', next_line) and 
                    field_lines[-1].strip() and 
                    not field_lines[-1].rstrip().endswith(',')):
                    # Add comma to the last field line
                    if field_lines:
                        fixed_lines[-1] = fixed_lines[-1].rstrip() + ','
                        print(f"  Added missing comma after field '{field_name}'")
            
            i = j
        else:
            fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines)

def fix_compute_method_signatures(content):
    """Fix compute methods that might have syntax issues"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Fix @api.depends that might be missing quotes
        if line.strip().startswith('@api.depends(') and not line.strip().endswith(')'):
            # This line might be incomplete
            if i + 1 < len(lines) and 'def ' in lines[i + 1]:
                # The depends line is incomplete, try to fix it
                line = line.rstrip() + ')'
                print(f"  Fixed incomplete @api.depends at line {i+1}")
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def comprehensive_fix_file(filepath):
    """Apply all comprehensive fixes to a Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply comprehensive fixes
        content = fix_field_definitions_comprehensive(content)
        content = fix_compute_method_signatures(content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def validate_python_syntax(filepath):
    """Check if Python file has valid syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Fix all Python files comprehensively"""
    
    # Get all Python files in current directory
    python_files = [f for f in os.listdir('.') if f.endswith('.py') and f != '__init__.py']
    
    print(f"🔧 Found {len(python_files)} Python files to fix comprehensively...")
    
    # First pass: fix the files
    fixed_count = 0
    for filename in sorted(python_files):
        is_valid, error = validate_python_syntax(filename)
        
        if not is_valid:
            print(f"\n🔧 Fixing {filename}")
            print(f"   Error: {error}")
            if comprehensive_fix_file(filename):
                fixed_count += 1
    
    print(f"\n✅ Applied comprehensive fixes to {fixed_count} files")
    
    # Second pass: validate results
    print("\n🔍 Validating results...")
    valid_count = 0
    still_broken = []
    
    for filename in sorted(python_files):
        is_valid, error = validate_python_syntax(filename)
        if is_valid:
            valid_count += 1
        else:
            still_broken.append((filename, error))
    
    print(f"✅ {valid_count}/{len(python_files)} files now have valid syntax")
    
    if still_broken:
        print(f"\n❌ {len(still_broken)} files still need manual attention:")
        for filename, error in still_broken[:10]:  # Show first 10
            print(f"  - {filename}: {error}")
        if len(still_broken) > 10:
            print(f"  ... and {len(still_broken) - 10} more")
    else:
        print("🎉 ALL files now have valid syntax!")

if __name__ == "__main__":
    main()
