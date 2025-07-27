#!/usr/bin/env python3
"""
Comprehensive Syntax Checker for Records Management Module
Identifies all Python files with syntax errors and reports them systematically
"""

import os
import subprocess
import sys
from pathlib import Path

def check_file_syntax(filepath):
    """Check syntax of a single Python file"""
    try:
        result = subprocess.run(
            ['python3', '-m', 'py_compile', filepath],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return True, None
        else:
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Timeout during syntax check"
    except Exception as e:
        return False, f"Error checking syntax: {e}"

def find_python_files(directory):
    """Find all Python files in the records_management module"""
    python_files = []
    
    # Define the search path
    search_path = Path(directory) / 'records_management'
    
    if not search_path.exists():
        print(f"❌ Directory not found: {search_path}")
        return []
    
    # Find all .py files
    for py_file in search_path.rglob('*.py'):
        if py_file.is_file():
            python_files.append(str(py_file))
    
    return sorted(python_files)

def main():
    """Main function to check all files"""
    print("🔍 Comprehensive Syntax Checker for Records Management Module")
    print("=" * 70)
    
    # Get current directory
    current_dir = os.getcwd()
    print(f"📂 Working directory: {current_dir}")
    
    # Find all Python files
    python_files = find_python_files(current_dir)
    
    if not python_files:
        print("❌ No Python files found in records_management module")
        return
    
    print(f"📋 Found {len(python_files)} Python files to check")
    print()
    
    # Check each file
    syntax_errors = []
    syntax_ok = []
    
    for i, filepath in enumerate(python_files, 1):
        # Get relative path for cleaner output
        rel_path = os.path.relpath(filepath, current_dir)
        
        print(f"[{i:2d}/{len(python_files)}] Checking {rel_path}...", end=" ")
        
        is_valid, error_msg = check_file_syntax(filepath)
        
        if is_valid:
            print("✅ OK")
            syntax_ok.append(rel_path)
        else:
            print("❌ SYNTAX ERROR")
            syntax_errors.append((rel_path, error_msg))
    
    print()
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    print(f"✅ Files with valid syntax: {len(syntax_ok)}")
    print(f"❌ Files with syntax errors: {len(syntax_errors)}")
    print(f"📈 Success rate: {len(syntax_ok)/len(python_files)*100:.1f}%")
    
    if syntax_errors:
        print()
        print("🚨 FILES WITH SYNTAX ERRORS:")
        print("-" * 40)
        
        for i, (filepath, error) in enumerate(syntax_errors, 1):
            print(f"\n{i}. {filepath}")
            # Extract line number and error from stderr
            lines = error.split('\n')
            for line in lines:
                if line.strip():
                    if 'File "' in line:
                        # Extract just the line info
                        if ', line ' in line:
                            parts = line.split(', line ')
                            if len(parts) > 1:
                                line_info = parts[1].split('\n')[0]
                                print(f"   📍 Line {line_info}")
                    elif 'SyntaxError:' in line:
                        error_msg = line.split('SyntaxError:')[1].strip()
                        print(f"   🔥 Error: {error_msg}")
                    elif line.strip() and not line.startswith('  File'):
                        # This might be the problematic code line
                        if '^' not in line:  # Skip pointer lines
                            print(f"   💥 Code: {line.strip()}")
    
    if syntax_ok:
        print()
        print("✅ FILES WITH VALID SYNTAX:")
        print("-" * 30)
        for filepath in syntax_ok:
            print(f"   {filepath}")
    
    print()
    if syntax_errors:
        print("🎯 NEXT STEPS:")
        print("1. Fix the syntax errors shown above")
        print("2. Run this script again to verify fixes")
        print("3. Test module installation after all fixes")
        
        return len(syntax_errors)  # Return error count
    else:
        print("🎉 ALL FILES HAVE VALID SYNTAX!")
        print("✅ Ready for module installation")
        return 0

if __name__ == "__main__":
    error_count = main()
    sys.exit(error_count)
