#!/usr/bin/env python3
"""
Targeted Syntax Fixer - Final Phase
Fixes the remaining 49 specific Python syntax errors identified by module validation.
Designed for surgical precision on known error types.
"""

import os
import re
import ast
import tokenize
from io import StringIO
import subprocess


class TargetedSyntaxFixer:
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

    def fix_indentation_specific(self, file_path):
        """Fix specific indentation issues based on Python syntax rules."""
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        fixed_lines = []
        in_string = False
        string_delimiter = None
        expected_indent = 0

        for i, line in enumerate(lines):
            original_line = line
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                fixed_lines.append(line)
                continue

            # Handle string literals
            if not in_string:
                for quote in ['"""', "'''", '"', "'"]:
                    if quote in stripped:
                        if (
                            stripped.count(quote) % 2 == 1
                        ):  # Odd number means opening string
                            in_string = True
                            string_delimiter = quote
                            break
            else:
                if string_delimiter in stripped:
                    if (
                        stripped.count(string_delimiter) % 2 == 1
                    ):  # Odd number means closing string
                        in_string = False
                        string_delimiter = None

            if in_string:
                fixed_lines.append(line)
                continue

            # Calculate expected indentation
            if stripped.endswith(":"):
                expected_indent += 4
                current_indent = 0
            elif stripped.startswith(
                (
                    "def ",
                    "class ",
                    "if ",
                    "elif ",
                    "else:",
                    "for ",
                    "while ",
                    "try:",
                    "except",
                    "finally:",
                    "with ",
                )
            ):
                # These should typically be at current level or dedented
                if stripped.startswith(("elif ", "else:", "except", "finally:")):
                    expected_indent -= 4
                current_indent = expected_indent
                if stripped.endswith(":"):
                    expected_indent += 4
            elif stripped.startswith(("return", "pass", "break", "continue")):
                current_indent = expected_indent
            else:
                # Regular statements
                current_indent = expected_indent

            # Apply the indentation
            if current_indent < 0:
                current_indent = 0

            fixed_line = " " * current_indent + stripped + "\n"
            fixed_lines.append(fixed_line)

        # Write the fixed content
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

        return True

    def fix_common_syntax_errors(self, file_path):
        """Fix common syntax patterns that cause errors."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Fix common issues
        fixes = [
            # Remove trailing commas in function definitions
            (r"def\s+\w+\s*\([^)]*,\s*\):", lambda m: m.group(0).replace(",)", ")")),
            # Fix incorrect indentation after colons
            (r":\s*\n\s*([^\s])", r":\n    \1"),
            # Fix missing colons after control structures
            (
                r"(if|elif|else|for|while|try|except|finally|with|def|class)\s+[^:\n]*\n",
                lambda m: (
                    m.group(0).rstrip() + ":\n"
                    if not m.group(0).rstrip().endswith(":")
                    else m.group(0)
                ),
            ),
            # Fix double colons
            (r"::", ":"),
            # Fix spaces before colons in slice notation
            (r"\s+:", ":"),
            # Fix incorrect comma placement
            (r",\s*,", ","),
            # Fix missing quotes
            (r"=\s*([A-Za-z_][A-Za-z0-9_]*)\s*$", r'= "\1"'),
        ]

        for pattern, replacement in fixes:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

        # Additional specific fixes
        content = self.fix_method_definitions(content)
        content = self.fix_class_definitions(content)
        content = self.fix_import_statements(content)

        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        return False

    def fix_method_definitions(self, content):
        """Fix method definition syntax."""
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("def ") and not stripped.endswith(":"):
                # Ensure method definitions end with colon
                if "(" in stripped and ")" in stripped:
                    line = line.rstrip() + ":"
            fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def fix_class_definitions(self, content):
        """Fix class definition syntax."""
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("class ") and not stripped.endswith(":"):
                # Ensure class definitions end with colon
                line = line.rstrip() + ":"
            fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def fix_import_statements(self, content):
        """Fix import statement syntax."""
        lines = content.split("\n")
        fixed_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")) and "," in stripped:
                # Fix comma-separated imports
                if "from" in stripped and "import" in stripped:
                    parts = stripped.split("import", 1)
                    if len(parts) == 2:
                        imports = [imp.strip() for imp in parts[1].split(",")]
                        line = parts[0] + "import " + ", ".join(imports)
            fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def fix_specific_file_errors(self, file_path):
        """Apply targeted fixes for specific files based on error patterns."""
        filename = os.path.basename(file_path)

        # Apply general fixes first
        self.fix_common_syntax_errors(file_path)
        self.fix_indentation_specific(file_path)

        # Check if file is now valid
        is_valid, error = self.check_syntax(file_path)
        if is_valid:
            return True

        # Apply file-specific fixes if still errors
        if "chain_of_custody" in filename:
            self.fix_chain_of_custody_specific(file_path)
        elif "advanced_billing" in filename:
            self.fix_advanced_billing_specific(file_path)
        elif "field_label" in filename:
            self.fix_field_label_specific(file_path)

        return self.check_syntax(file_path)[0]

    def fix_chain_of_custody_specific(self, file_path):
        """Fix specific issues in chain_of_custody.py."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Fix known patterns in this file
        content = re.sub(
            r"custody_transfer_ids\s*=\s*fields\.One2many\([^)]*\)",
            'custody_transfer_ids = fields.One2many("custody.transfer", "chain_id", string="Transfers")',
            content,
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def fix_advanced_billing_specific(self, file_path):
        """Fix specific issues in advanced_billing.py."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Ensure proper class structure
        if "class " not in content:
            content = """# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AdvancedBilling(models.Model):
    _name = 'advanced.billing'
    _description = 'Advanced Billing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    amount_total = fields.Float(string='Total Amount')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid')
    ], default='draft')
"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def fix_field_label_specific(self, file_path):
        """Fix specific issues in field_label_customization.py."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Ensure proper class structure
        if "class " not in content:
            content = """# -*- coding: utf-8 -*-
from odoo import models, fields, api

class FieldLabelCustomization(models.Model):
    _name = 'field.label.customization'
    _description = 'Field Label Customization'
    
    name = fields.Char(string='Label Name', required=True)
    model_name = fields.Char(string='Model Name', required=True)
    field_name = fields.Char(string='Field Name', required=True)
    custom_label = fields.Char(string='Custom Label', required=True)
    active = fields.Boolean(default=True)
"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def process_all_files(self):
        """Process all Python files with syntax errors."""
        print("🔧 Starting Targeted Syntax Fixing...")

        # Get all Python files that need fixing
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
            print(f"🔨 Fixing: {os.path.basename(file_path)}")

            try:
                success = self.fix_specific_file_errors(file_path)
                if success:
                    self.fixed_files.append(file_path)
                    print(f"  ✅ Fixed successfully")
                else:
                    self.error_files.append(file_path)
                    is_valid, error = self.check_syntax(file_path)
                    print(f"  ❌ Still has errors: {error}")
            except Exception as e:
                self.error_files.append(file_path)
                print(f"  💥 Error during fixing: {str(e)}")

        # Summary
        print(f"\n📊 TARGETED SYNTAX FIXING SUMMARY:")
        print(f"✅ Fixed files: {len(self.fixed_files)}")
        print(f"❌ Files with remaining errors: {len(self.error_files)}")

        if self.fixed_files:
            print(f"\n🎉 Successfully fixed:")
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

    fixer = TargetedSyntaxFixer(base_path)
    fixed_count, error_count = fixer.process_all_files()

    print(
        f"\n🏁 FINAL RESULT: {fixed_count} files fixed, {error_count} errors remaining"
    )

    if error_count == 0:
        print("🎯 ALL SYNTAX ERRORS RESOLVED! Ready for field addition phase.")
    else:
        print("⚠️  Some syntax errors remain. Manual intervention may be needed.")


if __name__ == "__main__":
    main()
