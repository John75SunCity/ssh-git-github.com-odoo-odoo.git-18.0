#!/usr/bin/env python3
"""
Black-based syntax fixer for Records Management module
Uses Black formatter to identify and systematically fix Python syntax errors
"""

import os
import subprocess
import sys
from pathlib import Path

def run_black_check(file_path):
    """Run Black check on a file and capture output"""
    python_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/.venv/bin/python"
    cmd = [python_path, "-m", "black", "--check", str(file_path)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=file_path.parent)
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)

def format_with_black(file_path):
    """Try to format file with Black"""
    python_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/.venv/bin/python"
    cmd = [python_path, "-m", "black", str(file_path)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=file_path.parent)
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)

def fix_common_patterns(file_path):
    """Fix common syntax patterns that Black can't handle"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix common patterns
        fixes_applied = []
        
        # Remove orphaned pass statements (pass followed by actual code)
        import re
        
        # Pattern 1: Remove pass statements in wrong places
        pattern1 = r'(\s+)pass\n(\s+)(\w+.*=|if |elif |else:|def |class |return |for |while )'
        if re.search(pattern1, content):
            content = re.sub(pattern1, r'\2\3', content)
            fixes_applied.append("Removed orphaned pass statements")
        
        # Pattern 2: Fix incomplete method definitions
        pattern2 = r'def\s+\w+\([^)]*:\s*\n'
        matches = re.findall(pattern2, content)
        if matches:
            content = re.sub(r'def\s+(\w+)\(([^)]*):(\s*\n)', r'def \1(\2):\3', content)
            fixes_applied.append("Fixed incomplete method definitions")
        
        # Pattern 3: Fix missing closing parentheses in method calls
        pattern3 = r'(\w+\([^)]*)\n\s*(\w+)'
        if re.search(pattern3, content):
            # This is complex - let's handle specific cases
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '(' in line and ')' not in line and not line.strip().endswith(':'):
                    # Check if next line starts with a word (potential continuation)
                    if i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].strip().startswith((')', '#', '"""', "'''")):
                        lines[i] = lines[i] + ')'
                        fixes_applied.append(f"Added missing closing parenthesis on line {i+1}")
            
            content = '\n'.join(lines)
        
        # Pattern 4: Fix Selection field bracket issues
        pattern4 = r'(\[\'[^]]*)\)'
        content = re.sub(pattern4, r'\1]', content)
        if re.search(pattern4, original_content):
            fixes_applied.append("Fixed Selection field brackets")
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, fixes_applied
        
        return False, []
        
    except Exception as e:
        return False, [f"Error: {str(e)}"]

def main():
    """Main function to fix syntax errors systematically"""
    models_dir = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models")
    
    if not models_dir.exists():
        print(f"Error: Models directory not found: {models_dir}")
        return
    
    print("=== Black-based Syntax Fixer ===")
    print(f"Scanning: {models_dir}")
    
    # Find all Python files
    python_files = list(models_dir.glob("*.py"))
    print(f"Found {len(python_files)} Python files")
    
    fixed_files = []
    error_files = []
    skipped_files = []
    
    for py_file in python_files:
        if py_file.name in ['__init__.py']:
            skipped_files.append(py_file.name)
            continue
            
        print(f"\n--- Processing: {py_file.name} ---")
        
        # First, try our pattern fixes
        pattern_fixed, fixes = fix_common_patterns(py_file)
        if pattern_fixed:
            print(f"✓ Applied pattern fixes: {', '.join(fixes)}")
        
        # Check with Black
        is_valid, error_msg = run_black_check(py_file)
        
        if is_valid:
            print(f"✓ {py_file.name} - Valid syntax")
            if pattern_fixed:
                fixed_files.append(py_file.name)
            continue
        
        # Try to format with Black
        formatted, format_error = format_with_black(py_file)
        if formatted:
            print(f"✓ {py_file.name} - Formatted with Black")
            fixed_files.append(py_file.name)
        else:
            print(f"✗ {py_file.name} - Black error: {format_error}")
            error_files.append((py_file.name, format_error))
    
    # Summary
    print("\n" + "="*50)
    print("SYNTAX FIXING SUMMARY")
    print("="*50)
    print(f"Total files processed: {len(python_files)}")
    print(f"Successfully fixed: {len(fixed_files)}")
    print(f"Files with errors: {len(error_files)}")
    print(f"Skipped files: {len(skipped_files)}")
    
    if fixed_files:
        print(f"\n✓ Fixed files ({len(fixed_files)}):")
        for file in fixed_files:
            print(f"  - {file}")
    
    if error_files:
        print(f"\n✗ Files with persistent errors ({len(error_files)}):")
        for file, error in error_files:
            print(f"  - {file}: {error}")
    
    success_rate = (len(fixed_files) / (len(python_files) - len(skipped_files))) * 100 if python_files else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    return len(error_files) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
