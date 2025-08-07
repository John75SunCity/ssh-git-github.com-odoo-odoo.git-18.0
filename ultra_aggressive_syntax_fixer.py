#!/usr/bin/env python3
"""
Ultra Aggressive Syntax Fixer
Handles the most complex field definition syntax errors
"""

import os
import re
import ast
import sys
from pathlib import Path

def fix_field_definitions(content):
    """Fix field definitions with missing commas and parentheses"""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Skip comments and empty lines
        if not line.strip() or line.strip().startswith('#'):
            fixed_lines.append(line)
            i += 1
            continue
            
        # Look for field definitions
        field_match = re.match(r'^(\s*)(\w+)\s*=\s*fields\.(\w+)\s*\(', line)
        if field_match:
            indent, field_name, field_type = field_match.groups()
            
            # Collect the complete field definition across multiple lines
            field_lines = [line]
            paren_count = line.count('(') - line.count(')')
            j = i + 1
            
            while j < len(lines) and paren_count > 0:
                next_line = lines[j]
                field_lines.append(next_line)
                paren_count += next_line.count('(') - next_line.count(')')
                j += 1
            
            # Join all field lines
            field_content = '\n'.join(field_lines)
            
            # Fix common issues
            field_content = fix_field_content(field_content, field_name, field_type, indent)
            
            # Split back into lines
            new_lines = field_content.split('\n')
            fixed_lines.extend(new_lines)
            i = j
        else:
            fixed_lines.append(line)
            i += 1
    
    return '\n'.join(fixed_lines)

def fix_field_content(field_content, field_name, field_type, indent):
    """Fix a single field definition"""
    # Remove any trailing commas before closing parenthesis
    field_content = re.sub(r',(\s*)\)', r'\1)', field_content)
    
    # Ensure proper closing
    if not field_content.strip().endswith(')'):
        field_content = field_content.rstrip() + ')'
    
    # Add comma at the end if missing
    if not field_content.strip().endswith(',') and not field_content.strip().endswith('),'):
        field_content = field_content.rstrip() + ','
    
    # Fix specific field type patterns
    if field_type in ['Char', 'Text', 'Html']:
        field_content = fix_string_field(field_content)
    elif field_type in ['Integer', 'Float', 'Monetary']:
        field_content = fix_numeric_field(field_content)
    elif field_type in ['Boolean']:
        field_content = fix_boolean_field(field_content)
    elif field_type in ['Date', 'Datetime']:
        field_content = fix_date_field(field_content)
    elif field_type in ['Selection']:
        field_content = fix_selection_field(field_content)
    elif field_type in ['Many2one', 'One2many', 'Many2many']:
        field_content = fix_relation_field(field_content)
    
    return field_content

def fix_string_field(content):
    """Fix string field definitions"""
    # Ensure string parameter is properly quoted
    content = re.sub(r'string\s*=\s*([^,\)]+)', r'string="\1"', content)
    return content

def fix_numeric_field(content):
    """Fix numeric field definitions"""
    # Ensure digits parameter is properly formatted
    content = re.sub(r'digits\s*=\s*\((\d+),\s*(\d+)\)', r'digits=(\1, \2)', content)
    return content

def fix_boolean_field(content):
    """Fix boolean field definitions"""
    # Ensure default values are proper booleans
    content = re.sub(r'default\s*=\s*"?(True|False)"?', r'default=\1', content)
    return content

def fix_date_field(content):
    """Fix date field definitions"""
    # Fix datetime.now references
    content = re.sub(r'default\s*=\s*datetime\.now', r'default=lambda: fields.Datetime.now()', content)
    return content

def fix_selection_field(content):
    """Fix selection field definitions"""
    # Ensure selection list is properly formatted
    if 'selection=' in content and not re.search(r'selection\s*=\s*\[', content):
        content = re.sub(r'selection\s*=\s*([^,\]]+)', r'selection=[\1]', content)
    return content

def fix_relation_field(content):
    """Fix relational field definitions"""
    # Ensure comodel name is properly quoted
    lines = content.split('\n')
    first_line = lines[0]
    
    # Extract comodel from first line
    comodel_match = re.search(r'fields\.\w+\s*\(\s*["\']([^"\']+)["\']', first_line)
    if not comodel_match:
        # Try to find unquoted comodel name
        comodel_match = re.search(r'fields\.\w+\s*\(\s*([^,\)]+)', first_line)
        if comodel_match:
            comodel = comodel_match.group(1).strip()
            if not comodel.startswith('"') and not comodel.startswith("'"):
                content = content.replace(comodel, f'"{comodel}"', 1)
    
    return content

def validate_syntax(filepath):
    """Check if Python file has valid syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error: {str(e)}"

def fix_file_aggressively(filepath):
    """Apply ultra-aggressive fixes to a Python file"""
    print(f"🔧 Ultra-fixing {filepath.name}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply multiple rounds of fixes
        original_content = content
        
        # Round 1: Basic field definition fixes
        content = fix_field_definitions(content)
        
        # Round 2: Fix obvious syntax issues
        content = fix_basic_syntax_issues(content)
        
        # Round 3: Clean up formatting
        content = clean_up_formatting(content)
        
        # Only write if we made changes
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Validate the result
            is_valid, error = validate_syntax(filepath)
            if is_valid:
                print(f"  ✅ Fixed successfully")
                return True
            else:
                print(f"  ❌ Still has errors: {error}")
                return False
        else:
            print(f"  ℹ️ No changes needed")
            return True
            
    except Exception as e:
        print(f"  ❌ Error processing: {e}")
        return False

def fix_basic_syntax_issues(content):
    """Fix basic syntax issues"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Fix missing commas at end of field definitions
        if re.match(r'^\s+\w+\s*=\s*fields\.\w+\([^)]*\)$', line.strip()):
            if not line.strip().endswith(','):
                line = line.rstrip() + ','
        
        # Fix unbalanced parentheses in field definitions
        if 'fields.' in line and '(' in line and ')' not in line:
            # Simple heuristic: add closing paren if missing
            if line.count('(') > line.count(')'):
                line = line.rstrip() + ')'
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def clean_up_formatting(content):
    """Clean up formatting issues"""
    # Remove duplicate commas
    content = re.sub(r',+', ',', content)
    
    # Fix spacing around equals signs in field definitions
    content = re.sub(r'(\w+)\s*=\s*fields\.', r'\1 = fields.', content)
    
    # Remove trailing whitespace
    lines = [line.rstrip() for line in content.split('\n')]
    content = '\n'.join(lines)
    
    return content

def main():
    """Main execution function"""
    models_dir = Path(".")
    python_files = list(models_dir.glob("*.py"))
    
    if not python_files:
        print("No Python files found in current directory")
        return
    
    print(f"🔧 Ultra-aggressive fixing {len(python_files)} Python files...")
    
    fixed_count = 0
    failed_files = []
    
    for filepath in sorted(python_files):
        if filepath.name == "__init__.py":
            continue
            
        if fix_file_aggressively(filepath):
            fixed_count += 1
        else:
            failed_files.append(str(filepath))
    
    print(f"\n✅ Ultra-aggressive fixes applied to {fixed_count} files")
    
    if failed_files:
        print(f"\n❌ {len(failed_files)} files still need manual attention:")
        for f in failed_files[:10]:  # Show first 10
            print(f"  - {f}")
        if len(failed_files) > 10:
            print(f"  ... and {len(failed_files) - 10} more")
    
    # Final validation
    print(f"\n🔍 Final validation...")
    valid_count = 0
    for filepath in python_files:
        if filepath.name != "__init__.py":
            is_valid, _ = validate_syntax(filepath)
            if is_valid:
                valid_count += 1
    
    print(f"✅ {valid_count}/{len(python_files)-1} files now have valid syntax")

if __name__ == "__main__":
    main()
