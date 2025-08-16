#!/usr/bin/env python3
"""
Final Comprehensive Syntax Fixer for Records Management Module
Specifically handles indentation and remaining syntax issues
"""

import os
import re
import ast

class FinalSyntaxFixer:
    def __init__(self, base_dir="/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"):
        self.base_dir = base_dir
        self.models_dir = os.path.join(base_dir, "models")
        self.fixes_applied = []

    def fix_indentation_errors(self, content):
        """Fix unexpected indentation errors"""
        fixes = []
        lines = content.split('\n')
        fixed_lines = []

        in_class = False
        class_indent = 0
        prev_line_indent = 0

        for i, line in enumerate(lines):
            original_line = line
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                fixed_lines.append(line)
                continue

            # Detect class definition
            if stripped.startswith('class '):
                in_class = True
                class_indent = len(line) - len(line.lstrip())
                fixed_lines.append(line)
                prev_line_indent = class_indent
                continue

            # Check if we're leaving a class
            if in_class and line.startswith('from ') or line.startswith('import ') or (stripped.startswith('class ') and i > 0):
                in_class = False

            # Fix indentation within class
            if in_class:
                current_indent = len(line) - len(line.lstrip())

                # Class-level items should be indented 4 spaces from class
                if stripped.startswith(('_name', '_description', '_inherit', '_order', '_rec_name')):
                    correct_indent = class_indent + 4
                    if current_indent != correct_indent:
                        line = ' ' * correct_indent + stripped
                        fixes.append(f"Fixed class attribute indentation at line {i+1}")

                # Field definitions should be indented 4 spaces from class
                elif '= fields.' in stripped or stripped.endswith('= fields.'):
                    correct_indent = class_indent + 4
                    if current_indent != correct_indent:
                        line = ' ' * correct_indent + stripped
                        fixes.append(f"Fixed field definition indentation at line {i+1}")

                # Method definitions should be indented 4 spaces from class
                elif stripped.startswith('def '):
                    correct_indent = class_indent + 4
                    if current_indent != correct_indent:
                        line = ' ' * correct_indent + stripped
                        fixes.append(f"Fixed method definition indentation at line {i+1}")

                # Method body should be indented 8 spaces from class (4 + 4)
                elif prev_line_indent == class_indent + 4 and stripped and not stripped.startswith(('def ', '@', 'class ')):
                    # This is likely method body
                    if current_indent < class_indent + 8:
                        correct_indent = class_indent + 8
                        line = ' ' * correct_indent + stripped
                        fixes.append(f"Fixed method body indentation at line {i+1}")

                # General indentation fix for class content
                elif current_indent < class_indent + 4 and not stripped.startswith(('def ', 'class ', '@')):
                    correct_indent = class_indent + 4
                    line = ' ' * correct_indent + stripped
                    fixes.append(f"Fixed general class content indentation at line {i+1}")

            fixed_lines.append(line)
            prev_line_indent = len(line) - len(line.lstrip())

        return '\n'.join(fixed_lines), fixes

    def fix_triple_quote_issues(self, content):
        """Fix unterminated triple quote issues"""
        fixes = []

        # Fix common triple quote patterns
        # Look for incomplete docstrings
        content = re.sub(r'(\s+"""[^"]*)\n(\s+[a-zA-Z])', r'\1"""\n\2', content)

        # Fix triple quotes that should be closed
        lines = content.split('\n')
        in_triple_quote = False
        quote_start_line = None

        for i, line in enumerate(lines):
            if '"""' in line:
                quote_count = line.count('"""')
                if quote_count % 2 == 1:  # Odd number of triple quotes
                    if not in_triple_quote:
                        # Starting a triple quote block
                        in_triple_quote = True
                        quote_start_line = i
                    else:
                        # Ending a triple quote block
                        in_triple_quote = False
                        quote_start_line = None
                elif quote_count % 2 == 0 and quote_count > 0:
                    # Even number of triple quotes (complete pairs)
                    in_triple_quote = False
                    quote_start_line = None

        # If we end with an unclosed triple quote, close it
        if in_triple_quote and quote_start_line is not None:
            lines.append('    """')
            fixes.append(f"Closed unterminated triple quote started at line {quote_start_line + 1}")

        return '\n'.join(lines), fixes

    def fix_basic_syntax_issues(self, content):
        """Fix basic syntax issues"""
        fixes = []

        # Fix missing colons after if, for, while, etc.
        content = re.sub(r'\b(if|for|while|def|class)\s+[^:\n]*[^:]\s*\n', lambda m: m.group(0).rstrip() + ':\n', content)

        # Fix missing pass statements in empty functions/classes
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().endswith(':') and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if not next_line or (next_line and len(lines[i + 1]) - len(lines[i + 1].lstrip()) <= len(line) - len(line.lstrip())):
                    # Next line is empty or at same indentation level, need pass
                    indent = len(line) - len(line.lstrip()) + 4
                    lines.insert(i + 1, ' ' * indent + 'pass')
                    fixes.append(f"Added pass statement after line {i + 1}")
                    break

        return '\n'.join(lines), fixes

    def fix_file(self, filepath):
        """Fix a single file comprehensively"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            all_fixes = []

            # Apply all fixes
            content, fixes = self.fix_indentation_errors(content)
            all_fixes.extend(fixes)

            content, fixes = self.fix_triple_quote_issues(content)
            all_fixes.extend(fixes)

            content, fixes = self.fix_basic_syntax_issues(content)
            all_fixes.extend(fixes)

            # Validate syntax
            try:
                ast.parse(content)
                is_valid = True
                error = None
            except SyntaxError as e:
                is_valid = False
                error = str(e)

            if content != original_content:
                # Write the fixed content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

                self.fixes_applied.extend([f"{os.path.basename(filepath)}: {fix}" for fix in all_fixes])

                if is_valid:
                    print(f"✅ FIXED & VALID: {os.path.basename(filepath)} - {len(all_fixes)} fixes")
                    return True
                else:
                    print(f"⚠️ FIXED BUT INVALID: {os.path.basename(filepath)} - {len(all_fixes)} fixes - {error}")
                    return False
            else:
                if is_valid:
                    print(f"✅ ALREADY VALID: {os.path.basename(filepath)}")
                    return True
                else:
                    print(f"❌ NO FIXES POSSIBLE: {os.path.basename(filepath)} - {error}")
                    return False

        except Exception as e:
            print(f"❌ ERROR: {os.path.basename(filepath)} - {e}")
            return False

    def fix_all_files(self):
        """Fix all Python files in models directory"""
        print("🔧 Final Comprehensive Syntax Fixer - Processing all Python files...")

        python_files = []
        for file in os.listdir(self.models_dir):
            if file.endswith('.py') and not file.startswith('__'):
                python_files.append(os.path.join(self.models_dir, file))

        fixed_count = 0
        valid_count = 0

        for filepath in sorted(python_files):
            result = self.fix_file(filepath)
            if result:
                fixed_count += 1
                valid_count += 1
            else:
                fixed_count += 1

        print(f"\n📊 Final Summary:")
        print(f"   Files processed: {len(python_files)}")
        print(f"   Files fixed: {fixed_count}")
        print(f"   Files with valid syntax: {valid_count}")
        print(f"   Total fixes applied: {len(self.fixes_applied)}")

        return valid_count == len(python_files)

def main():
    fixer = FinalSyntaxFixer()
    success = fixer.fix_all_files()

    if success:
        print("\n🎉 ALL FILES NOW HAVE VALID SYNTAX!")
    else:
        print("\n⚠️ Some files still have syntax errors - manual review needed")

if __name__ == "__main__":
    main()
