#!/usr/bin/env python3
"""
Precision Syntax Emergency Fixer
Handles the specific syntax errors found in Python files:
- Missing commas in field definitions
- Mixed bracket types ('{' vs ')')
- Unclosed parentheses
- Invalid syntax patterns
"""

import os
import re


class PrecisionSyntaxFixer:
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

    def fix_comma_issues(self, content):
        """Fix missing commas in field definitions and other structures."""
        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip comments and empty lines
            if not stripped or stripped.startswith("#"):
                fixed_lines.append(line)
                continue

            # Pattern 1: Field definitions missing commas
            # Look for: field_name = fields.Type(params
            if "= fields." in line and "(" in line and not line.rstrip().endswith(","):
                # Check if next line exists and needs a comma
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if (
                        next_line
                        and not next_line.startswith("#")
                        and not next_line.startswith(")")
                        and ("= fields." in next_line or next_line.startswith("_"))
                    ):
                        # Add comma to current line
                        line = line.rstrip() + ","

            # Pattern 2: Missing commas after string parameters
            if (
                "string=" in line
                and not line.rstrip().endswith(",")
                and not line.rstrip().endswith(")")
            ):
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not next_line.startswith(")"):
                        line = line.rstrip() + ","

            # Pattern 3: Missing commas in lists/tuples
            if (
                stripped.endswith("]")
                or stripped.endswith("'")
                or stripped.endswith('"')
            ):
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if (
                        next_line
                        and not next_line.startswith(")")
                        and not next_line.startswith("]")
                        and not next_line.startswith("}")
                        and not next_line.startswith("#")
                    ):
                        line = line.rstrip() + ","

            fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def fix_bracket_mismatches(self, content):
        """Fix mixed bracket types like '{' with ')'."""

        # Pattern 1: Replace { with ( in field definitions
        content = re.sub(r"= fields\.[^{]*\{([^}]*)\}", r"= fields.\1(\1)", content)

        # Pattern 2: Fix dictionary syntax in field parameters
        content = re.sub(r"(\w+)=\{([^}]*)\}", r"\1=(\2)", content)

        # Pattern 3: Replace } with ) when preceded by (
        lines = content.split("\n")
        fixed_lines = []
        open_parens = 0

        for line in lines:
            fixed_line = line
            for i, char in enumerate(line):
                if char == "(":
                    open_parens += 1
                elif char == ")":
                    open_parens -= 1
                elif char == "{" and open_parens > 0:
                    # Replace { with ( when inside parentheses
                    fixed_line = fixed_line[:i] + "(" + fixed_line[i + 1 :]
                    open_parens += 1
                elif char == "}" and open_parens > 0:
                    # Replace } with ) when inside parentheses
                    fixed_line = fixed_line[:i] + ")" + fixed_line[i + 1 :]
                    open_parens -= 1

            fixed_lines.append(fixed_line)

        return "\n".join(fixed_lines)

    def fix_unclosed_parentheses(self, content):
        """Fix unclosed parentheses by analyzing context."""
        lines = content.split("\n")
        fixed_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if this line starts a field definition
            if "= fields." in line and "(" in line:
                # Collect all related lines
                field_lines = [line]
                paren_count = line.count("(") - line.count(")")
                j = i + 1

                # Continue collecting lines until parentheses are balanced
                while j < len(lines) and paren_count > 0:
                    next_line = lines[j]
                    field_lines.append(next_line)
                    paren_count += next_line.count("(") - next_line.count(")")
                    j += 1

                # If parentheses are still unbalanced, fix it
                if paren_count > 0:
                    # Add missing closing parentheses to the last line
                    field_lines[-1] = field_lines[-1].rstrip() + ")" * paren_count

                fixed_lines.extend(field_lines)
                i = j
            else:
                fixed_lines.append(line)
                i += 1

        return "\n".join(fixed_lines)

    def fix_specific_syntax_issues(self, content):
        """Fix specific syntax patterns that cause errors."""

        # Pattern 1: Fix malformed field definitions
        content = re.sub(
            r"= fields\.(\w+)\(\s*([^)]*)\s*([,\s]*)$",
            r"= fields.\1(\2)",
            content,
            flags=re.MULTILINE,
        )

        # Pattern 2: Remove extra trailing commas before closing parens
        content = re.sub(r",\s*\)", ")", content)

        # Pattern 3: Fix malformed string parameters
        content = re.sub(r"string=([^,)]+)([,)])", r'string="\1"\2', content)

        # Pattern 4: Ensure proper line endings for field definitions
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            stripped = line.strip()

            # Ensure class definitions have proper indentation
            if stripped.startswith("class ") and not line.startswith("class "):
                line = re.sub(r"^\s*", "", line)  # Remove leading whitespace

            # Fix missing pass statements in empty classes
            if stripped == "class" or (
                stripped.startswith("class ") and stripped.endswith(":")
            ):
                fixed_lines.append(line)
                # Check if next line is indented - if not, add pass
                continue

            fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def add_missing_pass_statements(self, content):
        """Add missing pass statements where needed."""
        lines = content.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            fixed_lines.append(line)
            stripped = line.strip()

            # If this line ends with : and next line is not indented more, add pass
            if stripped.endswith(":") and stripped.startswith(
                ("class ", "def ", "if ", "else:", "elif ", "for ", "while ")
            ):
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    current_indent = len(line) - len(line.lstrip())
                    next_indent = (
                        len(next_line) - len(next_line.lstrip())
                        if next_line.strip()
                        else 0
                    )

                    # If next line is not more indented or is empty, add pass
                    if next_indent <= current_indent or not next_line.strip():
                        fixed_lines.append(" " * (current_indent + 4) + "pass")

        return "\n".join(fixed_lines)

    def fix_file(self, file_path):
        """Apply all fixes to a single file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Apply all fixes in sequence
            content = self.fix_comma_issues(content)
            content = self.fix_bracket_mismatches(content)
            content = self.fix_unclosed_parentheses(content)
            content = self.fix_specific_syntax_issues(content)
            content = self.add_missing_pass_statements(content)

            # Write back if changed
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # Check syntax
            is_valid, error = self.check_syntax(file_path)
            return is_valid, error

        except Exception as e:
            return False, str(e)

    def process_all_files(self):
        """Process all Python files with syntax errors."""
        print("🔧 Starting Precision Syntax Fixing...")

        # Get all Python files with syntax errors
        python_files = []

        for root in [self.models_path, self.wizards_path]:
            if os.path.exists(root):
                for file in os.listdir(root):
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        is_valid, error = self.check_syntax(file_path)
                        if not is_valid:
                            python_files.append(file_path)

        print(f"📁 Found {len(python_files)} files with syntax errors")

        # Fix each file
        for file_path in python_files:
            filename = os.path.basename(file_path)
            print(f"🔨 Fixing: {filename}")

            success, error = self.fix_file(file_path)
            if success:
                self.fixed_files.append(file_path)
                print(f"  ✅ Fixed successfully")
            else:
                self.error_files.append(file_path)
                print(f"  ❌ Still has errors: {error[:100]}...")

        # Summary
        print(f"\n📊 PRECISION SYNTAX FIXING SUMMARY:")
        print(f"✅ Fixed files: {len(self.fixed_files)}")
        print(f"❌ Files with remaining errors: {len(self.error_files)}")

        if self.fixed_files:
            print(f"\n🎉 Successfully fixed:")
            for file_path in self.fixed_files:
                print(f"  - {os.path.basename(file_path)}")

        if self.error_files:
            print(f"\n⚠️  Files still needing attention:")
            for file_path in self.error_files[:10]:  # Show first 10
                print(f"  - {os.path.basename(file_path)}")
            if len(self.error_files) > 10:
                print(f"  ... and {len(self.error_files) - 10} more")

        return len(self.fixed_files), len(self.error_files)


def main():
    """Main execution function."""
    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0"

    fixer = PrecisionSyntaxFixer(base_path)
    fixed_count, error_count = fixer.process_all_files()

    print(
        f"\n🏁 FINAL RESULT: {fixed_count} files fixed, {error_count} errors remaining"
    )

    if error_count == 0:
        print("🎯 ALL SYNTAX ERRORS RESOLVED! Ready for field addition phase.")
    elif fixed_count > 0:
        print(f"📈 PROGRESS: Fixed {fixed_count} files. {error_count} remaining.")
    else:
        print("⚠️  No files could be automatically fixed. Manual review needed.")


if __name__ == "__main__":
    main()
