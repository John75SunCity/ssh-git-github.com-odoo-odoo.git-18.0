#!/usr/bin/env python3
"""
Bracket Balance Fixer - Surgical Precision Tool
Fixes unmatched parentheses, brackets, and braces in Python files.
Designed to resolve the specific "unmatched ')'" errors found in 47 files.
"""

import os
import re


class BracketBalanceFixer:
    def __init__(self, base_path):
        self.base_path = base_path
        self.models_path = os.path.join(base_path, "records_management", "models")
        self.wizards_path = os.path.join(base_path, "records_management", "wizards")
        self.fixed_files = []
        self.error_files = []

    def check_syntax(self, file_path):
        """Check if a Python file has syntax errors."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            compile(content, file_path, "exec")
            return True, None
        except SyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)

    def balance_brackets(self, content):
        """Fix bracket balance issues in content."""
        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            # Skip comments and empty lines
            if line.strip().startswith("#") or not line.strip():
                fixed_lines.append(line)
                continue

            # Count brackets in this line
            open_parens = line.count("(")
            close_parens = line.count(")")
            open_brackets = line.count("[")
            close_brackets = line.count("]")
            open_braces = line.count("{")
            close_braces = line.count("}")

            # Fix common bracket issues
            fixed_line = line

            # Pattern 1: Extra closing parenthesis at end of line
            if close_parens > open_parens and fixed_line.rstrip().endswith(")"):
                # Remove extra closing parenthesis
                excess = close_parens - open_parens
                for _ in range(excess):
                    # Remove the last occurrence of )
                    last_paren = fixed_line.rfind(")")
                    if last_paren != -1:
                        fixed_line = (
                            fixed_line[:last_paren] + fixed_line[last_paren + 1 :]
                        )

            # Pattern 2: Missing opening parenthesis
            elif close_parens > open_parens and "=" in fixed_line:
                # Common pattern: field = fields.Something(...))
                # Add missing opening parenthesis after '('
                if "fields." in fixed_line and "(" in fixed_line:
                    # Find the first ( and add another one
                    first_paren = fixed_line.find("(")
                    if first_paren != -1:
                        fixed_line = (
                            fixed_line[: first_paren + 1]
                            + "("
                            + fixed_line[first_paren + 1 :]
                        )

            # Pattern 3: Unmatched closing in multi-line constructs
            elif close_parens > open_parens:
                # Just remove excess closing parens
                excess = close_parens - open_parens
                for _ in range(excess):
                    last_paren = fixed_line.rfind(")")
                    if last_paren != -1:
                        fixed_line = (
                            fixed_line[:last_paren] + fixed_line[last_paren + 1 :]
                        )

            # Similar fixes for brackets and braces
            if close_brackets > open_brackets:
                excess = close_brackets - open_brackets
                for _ in range(excess):
                    last_bracket = fixed_line.rfind("]")
                    if last_bracket != -1:
                        fixed_line = (
                            fixed_line[:last_bracket] + fixed_line[last_bracket + 1 :]
                        )

            if close_braces > open_braces:
                excess = close_braces - open_braces
                for _ in range(excess):
                    last_brace = fixed_line.rfind("}")
                    if last_brace != -1:
                        fixed_line = (
                            fixed_line[:last_brace] + fixed_line[last_brace + 1 :]
                        )

            fixed_lines.append(fixed_line)

        return "\n".join(fixed_lines)

    def fix_specific_patterns(self, content):
        """Fix specific problematic patterns."""

        # Pattern 1: Double closing parentheses
        content = re.sub(r"\)\)", ")", content)

        # Pattern 2: Trailing commas with closing parens
        content = re.sub(r",\s*\)", ")", content)

        # Pattern 3: Extra closing parens at end of field definitions
        content = re.sub(r"fields\.[^)]+\)\)", lambda m: m.group(0)[:-1], content)

        # Pattern 4: Unmatched closing in string parameters
        content = re.sub(r"string=([^,)]+)\)", r"string=\1", content)

        # Pattern 5: Fix common field definition issues
        content = re.sub(
            r"= fields\.([A-Za-z0-9_]+)\([^)]*\)\)", lambda m: m.group(0)[:-1], content
        )

        return content

    def fix_multiline_constructs(self, content):
        """Fix multiline function calls and field definitions."""
        lines = content.split("\n")
        fixed_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this is a field definition
            if "= fields." in line and "(" in line:
                # Collect the complete field definition
                field_lines = [line]
                paren_count = line.count("(") - line.count(")")
                j = i + 1

                while j < len(lines) and paren_count > 0:
                    next_line = lines[j]
                    field_lines.append(next_line)
                    paren_count += next_line.count("(") - next_line.count(")")
                    j += 1

                # Now fix the complete field definition
                complete_field = "\n".join(field_lines)
                fixed_field = self.fix_field_definition(complete_field)

                # Split back into lines
                new_lines = fixed_field.split("\n")
                fixed_lines.extend(new_lines)
                i = j
            else:
                fixed_lines.append(line)
                i += 1

        return "\n".join(fixed_lines)

    def fix_field_definition(self, field_def):
        """Fix a specific field definition."""
        # Remove extra closing parentheses
        while field_def.count(")") > field_def.count("("):
            last_paren = field_def.rfind(")")
            field_def = field_def[:last_paren] + field_def[last_paren + 1 :]

        # Ensure field definitions end properly
        if not field_def.rstrip().endswith(")"):
            field_def = field_def.rstrip() + ")"

        return field_def

    def fix_file(self, file_path):
        """Fix a single file's bracket issues."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Apply various fixes
            content = self.fix_specific_patterns(content)
            content = self.balance_brackets(content)
            content = self.fix_multiline_constructs(content)

            # Write back if changed
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # Check if syntax is now valid
            is_valid, error = self.check_syntax(file_path)
            return is_valid, error

        except Exception as e:
            return False, str(e)

    def process_all_files(self):
        """Process all Python files with bracket issues."""
        print("🔧 Starting Bracket Balance Fixing...")

        # Get all Python files with syntax errors
        python_files = []

        for root in [self.models_path, self.wizards_path]:
            if os.path.exists(root):
                for file in os.listdir(root):
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        is_valid, error = self.check_syntax(file_path)
                        if not is_valid and (
                            "unmatched" in error
                            or "bracket" in error
                            or "paren" in error
                        ):
                            python_files.append(file_path)

        print(f"📁 Found {len(python_files)} files with bracket issues")

        # Fix each file
        for file_path in python_files:
            filename = os.path.basename(file_path)
            print(f"🔨 Fixing brackets in: {filename}")

            success, error = self.fix_file(file_path)
            if success:
                self.fixed_files.append(file_path)
                print(f"  ✅ Brackets fixed successfully")
            else:
                self.error_files.append(file_path)
                print(f"  ❌ Still has errors: {error}")

        # Summary
        print(f"\n📊 BRACKET FIXING SUMMARY:")
        print(f"✅ Fixed files: {len(self.fixed_files)}")
        print(f"❌ Files with remaining errors: {len(self.error_files)}")

        if self.fixed_files:
            print(f"\n🎉 Successfully fixed brackets:")
            for file_path in self.fixed_files:
                print(f"  - {os.path.basename(file_path)}")

        if self.error_files:
            print(f"\n⚠️  Files still needing attention:")
            for file_path in self.error_files:
                print(f"  - {os.path.basename(file_path)}")

        return len(self.fixed_files), len(self.error_files)


def main():
    """Main execution function."""
    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0"

    fixer = BracketBalanceFixer(base_path)
    fixed_count, error_count = fixer.process_all_files()

    print(
        f"\n🏁 BRACKET FIXING RESULT: {fixed_count} files fixed, {error_count} errors remaining"
    )

    if error_count == 0:
        print("🎯 ALL BRACKET ISSUES RESOLVED!")
    else:
        print("⚠️  Some bracket issues remain.")


if __name__ == "__main__":
    main()
