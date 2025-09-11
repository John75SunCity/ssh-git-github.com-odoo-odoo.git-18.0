#!/usr/bin/env python3
"""
Ultra-Targeted Syntax Fixer - Handle the most persistent patterns
Focus on the exact error types that remain
"""

import os
import re
import ast
from pathlib import Path

class UltraTargetedFixer:
    def __init__(self, base_dir="/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"):
        self.base_dir = base_dir
        self.models_dir = os.path.join(base_dir, "models")
        self.files_fixed = 0

    def fix_specific_unterminated_strings(self, content):
        """Fix very specific unterminated string patterns"""
        lines = content.split('\n')
        fixed_lines = []

        for i, line in enumerate(lines):
            original_line = line

            # Pattern 1: Line ends with = " or = ' (incomplete assignment)
            if re.search(r'=\s*["\']$', line.rstrip()):
                line = line.rstrip() + 'PLACEHOLDER"'

            # Pattern 2: Triple quotes that never close
            if '"""' in line and line.count('"""') == 1 and not line.strip().startswith('#'):
                line = line + '"""'

            # Pattern 3: String that starts but has syntax after
            if re.search(r'["\'][^"\']*$', line) and not line.rstrip().endswith('"') and not line.rstrip().endswith("'"):
                # Find the quote type and close it
                if '"' in line and line.count('"') % 2 == 1:
                    line = line + '"'
                elif "'" in line and line.count("'") % 2 == 1:
                    line = line + "'"

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def fix_specific_bracket_mismatches(self, content):
        """Fix the exact bracket mismatch patterns we're seeing"""
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            original_line = line

            # Pattern: [text) -> [text]
            # Look for opening bracket followed by content and closing parenthesis
            if '[' in line and ')' in line and ']' not in line:
                # Find all instances of [content)
                pattern = r'\[([^[\]()]*)\)'
                matches = list(re.finditer(pattern, line))

                # Replace from right to left to maintain positions
                for match in reversed(matches):
                    start, end = match.span()
                    content_inside = match.group(1)
                    replacement = '[' + content_inside + ']'
                    line = line[:start] + replacement + line[end:]

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def fix_unexpected_indentation(self, content):
        """Fix unexpected indentation by normalizing the file structure"""
        lines = content.split('\n')
        fixed_lines = []
        current_indent = 0

        for i, line in enumerate(lines):
            if not line.strip():  # Empty lines
                fixed_lines.append('')
                continue

            # Check if this line should be at module level (0 indentation)
            if (line.strip().startswith('from ') or
                line.strip().startswith('import ') or
                line.strip().startswith('class ') or
                line.strip().startswith('def ') and not any(l.strip().startswith('class ') for l in lines[:i])):
                # Module level
                fixed_lines.append(line.lstrip())
                current_indent = 0

            # Check if we're inside a class
            elif any(lines[j].strip().startswith('class ') for j in range(max(0, i-20), i)):
                # We're in a class, check for proper method/field indentation
                if (line.strip().startswith('def ') or
                    line.strip().startswith('_name ') or
                    line.strip().startswith('_inherit ') or
                    '= fields.' in line):
                    # Class member - should be indented
                    fixed_lines.append('    ' + line.lstrip())
                else:
                    # Preserve existing structure for other lines
                    fixed_lines.append(line)
            else:
                # Preserve existing structure
                fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def fix_specific_invalid_syntax(self, content):
        """Fix specific invalid syntax patterns"""
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            original_line = line

            # Pattern: Missing comma after field definition
            if ('= fields.' in line and
                not line.rstrip().endswith(',') and
                not line.rstrip().endswith(')') and
                not line.rstrip().endswith('}')):
                # Add comma if this looks like a field definition
                line = line.rstrip() + ','

            # Pattern: Fix {text) -> {text}
            if '{' in line and ')' in line and '}' not in line:
                line = re.sub(r'\{([^{}]*)\)', r'{\1}', line)

            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def validate_syntax(self, content):
        """Check if the content has valid Python syntax"""
        try:
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, str(e)

    def process_file(self, file_path):
        """Process a single file with all fixes"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Check initial syntax
            is_valid_before, error_before = self.validate_syntax(original_content)

            if is_valid_before:
                print(f"✅ ALREADY VALID: {os.path.basename(file_path)}")
                return

            # Apply targeted fixes in order
            content = original_content
            content = self.fix_unexpected_indentation(content)
            content = self.fix_specific_unterminated_strings(content)
            content = self.fix_specific_bracket_mismatches(content)
            content = self.fix_specific_invalid_syntax(content)

            # Check if we made improvements
            is_valid_after, error_after = self.validate_syntax(content)

            if is_valid_after:
                # Write the fixed content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ FIXED & VALID: {os.path.basename(file_path)}")
                self.files_fixed += 1
            else:
                # Show the specific error type
                error_type = error_after.split(':')[0] if ':' in error_after else error_after
                print(f"⚠️ STILL INVALID: {os.path.basename(file_path)} - {error_type}")

        except Exception as e:
            print(f"❌ ERROR processing {os.path.basename(file_path)}: {e}")

    def run(self):
        """Process all Python files in the models directory"""
        print("=== Ultra-Targeted Syntax Fixer ===")
        print("Fixing remaining persistent syntax patterns...")

        if not os.path.exists(self.models_dir):
            print(f"Models directory not found: {self.models_dir}")
            return

        # Get all Python files
        python_files = list(Path(self.models_dir).glob("*.py"))
        python_files = [f for f in python_files if f.name != "__init__.py"]

        print(f"Found {len(python_files)} Python files to process")

        for py_file in sorted(python_files):
            self.process_file(str(py_file))

        print(f"\n=== Ultra-Targeted Results ===")
        print(f"Files completely fixed: {self.files_fixed}")

if __name__ == "__main__":
    fixer = UltraTargetedFixer()
    fixer.run()
