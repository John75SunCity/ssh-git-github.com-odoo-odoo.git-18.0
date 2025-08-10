#!/usr/bin/env python3
"""
Odoo Indentation Fixer Script

This script fixes indentation issues caused by Python auto-formatters (Black, Autopep8)
that don't understand Odoo's specific coding patterns and field definition structures.

Common issues fixed:
1. Unexpected indentation after field definitions
2. Missing indented blocks after method definitions
3. Incorrectly formatted One2many/Many2one field chains
4. Method definitions that got reformatted incorrectly
"""

import ast
import os
import re
from pathlib import Path

class OdooIndentationFixer:
    def __init__(self, models_path):
        self.models_path = Path(models_path)
        self.fixes_applied = []
        self.errors = []
    
    def fix_unexpected_indent_errors(self, file_path):
        """Fix 'unexpected indent' syntax errors in Odoo model files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            original_lines = lines.copy()
            fixed_lines = []
            i = 0
            
            while i < len(lines):
                line = lines[i]
                
                # Check for common problematic patterns
                if self._is_unexpected_indent_line(line, i, lines):
                    # Try to fix the indentation
                    fixed_line = self._fix_line_indentation(line, i, lines)
                    fixed_lines.append(fixed_line)
                else:
                    fixed_lines.append(line)
                
                i += 1
            
            if fixed_lines != original_lines:
                # Write the fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(fixed_lines)
                
                self.fixes_applied.append({
                    'file': str(file_path),
                    'status': 'FIXED_INDENTATION'
                })
                return True
            
            return False
            
        except Exception as e:
            self.errors.append({
                'file': str(file_path),
                'error': str(e)
            })
            return False
    
    def fix_missing_indent_errors(self, file_path):
        """Fix 'expected an indented block' syntax errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Pattern for method definitions followed by unindented lines
            pattern = r'(def\s+\w+\([^)]*\):\s*\n)(\s*)([^\s])'
            
            def fix_method_indent(match):
                method_def = match.group(1)
                existing_indent = match.group(2)
                next_line = match.group(3)
                
                # Add proper indentation (4 spaces)
                if not existing_indent or len(existing_indent) == 0:
                    return method_def + "    " + next_line
                else:
                    return match.group(0)  # Leave unchanged if already indented
            
            content = re.sub(pattern, fix_method_indent, content)
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.fixes_applied.append({
                    'file': str(file_path),
                    'status': 'FIXED_MISSING_INDENT'
                })
                return True
            
            return False
            
        except Exception as e:
            self.errors.append({
                'file': str(file_path),
                'error': str(e)
            })
            return False
    
    def _is_unexpected_indent_line(self, line, line_num, all_lines):
        """Check if a line has unexpected indentation."""
        # Look for lines that start with extra spaces but shouldn't
        if line.strip() == "":
            return False
        
        # Get the previous non-empty line
        prev_line = ""
        for j in range(line_num - 1, -1, -1):
            if all_lines[j].strip():
                prev_line = all_lines[j]
                break
        
        # Check if this line is over-indented compared to what it should be
        current_indent = len(line) - len(line.lstrip())
        
        # Common patterns that cause unexpected indentation:
        # 1. Field definitions that got extra indentation
        if re.match(r'\s+\w+\s*=\s*fields\.', line):
            # This should probably be at the same level as other fields
            if current_indent > 4:  # Probably over-indented
                return True
        
        # 2. Method calls or statements that got extra indentation
        if current_indent > 8 and not line.strip().startswith('#'):
            return True
        
        return False
    
    def _fix_line_indentation(self, line, line_num, all_lines):
        """Fix the indentation of a specific line."""
        stripped = line.lstrip()
        
        # For field definitions, use standard 4-space indentation
        if re.match(r'\w+\s*=\s*fields\.', stripped):
            return "    " + stripped
        
        # For other statements, try to determine proper indentation
        # Look at surrounding context
        prev_indent = 0
        for j in range(line_num - 1, -1, -1):
            if all_lines[j].strip():
                prev_indent = len(all_lines[j]) - len(all_lines[j].lstrip())
                break
        
        # Use same indentation as previous line, or reduce by 4 if over-indented
        current_indent = len(line) - len(line.lstrip())
        if current_indent > prev_indent + 8:
            return " " * (prev_indent + 4) + stripped
        
        return line
    
    def process_syntax_error_files(self, error_files):
        """Process files with known syntax errors."""
        print("🔧 ODOO INDENTATION FIXER")
        print("=" * 50)
        print(f"📁 Models Path: {self.models_path}")
        print(f"🐛 Files to Fix: {len(error_files)}")
        print()
        
        fixed_count = 0
        
        for filename in error_files:
            file_path = self.models_path / filename
            
            if not file_path.exists():
                self.errors.append({
                    'file': str(file_path),
                    'error': 'File not found'
                })
                continue
            
            print(f"🔍 Processing: {filename}")
            
            # Try to fix unexpected indent errors
            fixed1 = self.fix_unexpected_indent_errors(file_path)
            
            # Try to fix missing indent errors
            fixed2 = self.fix_missing_indent_errors(file_path)
            
            if fixed1 or fixed2:
                fixed_count += 1
                print(f"   ✅ Fixed indentation issues")
            else:
                print(f"   ℹ️  No indentation issues found or already correct")
        
        print()
        self.print_summary(fixed_count)
    
    def print_summary(self, fixed_count):
        """Print summary of fixes applied."""
        print("📊 INDENTATION FIX SUMMARY")
        print("=" * 35)
        print(f"• Files Fixed: {fixed_count}")
        print(f"• Errors: {len(self.errors)}")
        print()
        
        if self.fixes_applied:
            print("✅ FIXES APPLIED:")
            print("-" * 20)
            for fix in self.fixes_applied:
                print(f"   📄 {Path(fix['file']).name}: {fix['status']}")
            print()
        
        if self.errors:
            print("❌ ERRORS:")
            print("-" * 15)
            for error in self.errors:
                print(f"   📄 {Path(error['file']).name}: {error['error']}")
            print()
        
        print("🚀 NEXT STEPS:")
        print("=" * 20)
        print("1. ✅ Run syntax check: python development-tools/find_syntax_errors.py")
        print("2. 🧪 Test manually edited files for correct functionality")
        print("3. 💡 Consider disabling auto-formatting in VS Code for Python files")
        print()

# Files with syntax errors (from the latest run)
SYNTAX_ERROR_FILES = [
    'barcode_product.py',
    'service_item.py', 
    'shredding_hard_drive.py',
    'portal_feedback_support_models.py',
    'processing_log.py',
    'paper_bale.py',
    'records_location.py',
    'shredding_team.py',
    'paper_bale_recycling.py',
    'shredding_inventory_item.py',
    'records_vehicle.py',
    'unlock_service_history.py',
    'records_access_log.py',
    'temp_inventory.py',
    'signed_document.py',
    'pickup_route.py',
    'records_document_type.py',
    'records_container_movement.py'
]

def main():
    """Main execution function."""
    models_path = Path("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models")
    
    if not models_path.exists():
        print(f"❌ Models directory not found: {models_path}")
        return
    
    fixer = OdooIndentationFixer(models_path)
    fixer.process_syntax_error_files(SYNTAX_ERROR_FILES)

if __name__ == "__main__":
    main()
