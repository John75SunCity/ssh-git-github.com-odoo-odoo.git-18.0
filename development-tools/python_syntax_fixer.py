#!/usr/bin/env python3
"""
Python Syntax Fixer for Odoo Records Management Module
=======================================================

This tool fixes Python syntax errors found during validation.
It handles common issues like unexpected indentation, missing commas, unterminated strings.

Usage: python python_syntax_fixer.py
"""

import os
import re
from pathlib import Path


class PythonSyntaxFixer:
    def __init__(self, module_path):
        self.module_path = Path(module_path)
        self.fixes_applied = 0

    def fix_unexpected_indent(self, file_path, line_number):
        """Fix unexpected indentation errors"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if line_number <= len(lines):
                line = lines[line_number - 1]

                # Check if line has excessive indentation
                if line.strip() and line.startswith("        "):  # 8+ spaces
                    # Reduce to 4 spaces
                    fixed_line = "    " + line.lstrip()
                    lines[line_number - 1] = fixed_line

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)

                    print(f"  ✅ Fixed indentation at line {line_number}")
                    return True

        except Exception as e:
            print(f"  ❌ Error fixing indentation: {e}")

        return False

    def fix_missing_comma(self, file_path, line_number):
        """Fix missing comma errors"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if line_number <= len(lines):
                line = lines[line_number - 1]

                # Common patterns that need commas
                patterns = [
                    (r"(\))\s*$", r"\1,"),  # Missing comma after closing parenthesis
                    (r"(])\s*$", r"\1,"),  # Missing comma after closing bracket
                    (r"(})\s*$", r"\1,"),  # Missing comma after closing brace
                    (r"('[^']*')\s*$", r"\1,"),  # Missing comma after string
                    (r'("[^"]*")\s*$', r"\1,"),  # Missing comma after string
                ]

                for pattern, replacement in patterns:
                    if re.search(pattern, line):
                        fixed_line = re.sub(pattern, replacement, line)
                        lines[line_number - 1] = fixed_line

                        with open(file_path, "w", encoding="utf-8") as f:
                            f.writelines(lines)

                        print(f"  ✅ Fixed missing comma at line {line_number}")
                        return True

        except Exception as e:
            print(f"  ❌ Error fixing comma: {e}")

        return False

    def fix_unterminated_string(self, file_path, line_number):
        """Fix unterminated string literals"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if line_number <= len(lines):
                line = lines[line_number - 1]

                # Check for unterminated strings
                if line.count('"') % 2 == 1:  # Odd number of quotes
                    # Add closing quote at end
                    lines[line_number - 1] = line.rstrip() + '"\n'

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)

                    print(f"  ✅ Fixed unterminated string at line {line_number}")
                    return True

        except Exception as e:
            print(f"  ❌ Error fixing string: {e}")

        return False

    def fix_syntax_errors(self):
        """Fix all known syntax errors"""
        print("🔧 Fixing Python syntax errors...")

        # Known syntax errors from validation
        syntax_errors = {
            "models/advanced_billing.py": [(132, "comma")],
            "models/field_label_customization.py": [(210, "syntax")],
            "models/naid_compliance.py": [(72, "indent")],
            "models/records_container.py": [(241, "indent")],
            "models/paper_bale.py": [(48, "indent")],
            "models/records_location.py": [(169, "comma")],
            "models/paper_bale_recycling.py": [(78, "indent")],
            "models/records_digital_scan.py": [(62, "indent")],
            "models/paper_load_shipment.py": [(47, "indent")],
            "models/fsm_task.py": [(46, "indent")],
            "models/portal_request.py": [(166, "indent")],
            "models/records_retention_policy.py": [(56, "indent")],
            "models/bin_key_management.py": [(43, "indent")],
            "models/records_vehicle.py": [(152, "indent")],
            "models/portal_feedback.py": [(114, "string")],
            "models/records_document.py": [(209, "indent")],
            "models/load.py": [(51, "indent")],
            "models/file_retrieval_work_order.py": [(222, "indent")],
            "models/visitor_pos_wizard.py": [(135, "indent")],
            "models/records_document_type.py": [(87, "indent")],
        }

        for file_path, errors in syntax_errors.items():
            full_path = self.module_path / file_path

            if not full_path.exists():
                print(f"  ⚠️  File not found: {file_path}")
                continue

            print(f"  🔧 Fixing {file_path}...")

            for line_number, error_type in errors:
                if error_type == "indent":
                    if self.fix_unexpected_indent(full_path, line_number):
                        self.fixes_applied += 1
                elif error_type == "comma":
                    if self.fix_missing_comma(full_path, line_number):
                        self.fixes_applied += 1
                elif error_type == "string":
                    if self.fix_unterminated_string(full_path, line_number):
                        self.fixes_applied += 1
                elif error_type == "syntax":
                    # Generic syntax fix - check common issues
                    if self.fix_missing_comma(
                        full_path, line_number
                    ) or self.fix_unexpected_indent(full_path, line_number):
                        self.fixes_applied += 1

    def validate_fixes(self):
        """Validate that syntax errors are fixed"""
        print("\n🔍 Validating syntax fixes...")

        # Try to compile each Python file
        py_files = list(self.module_path.rglob("*.py"))
        errors_remaining = []

        for py_file in py_files:
            if "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                compile(content, py_file, "exec")

            except SyntaxError as e:
                errors_remaining.append(f"{py_file.relative_to(self.module_path)}: {e}")
            except Exception as e:
                errors_remaining.append(f"{py_file.relative_to(self.module_path)}: {e}")

        if errors_remaining:
            print(f"  ⚠️  {len(errors_remaining)} syntax errors still remain:")
            for error in errors_remaining[:5]:  # Show first 5
                print(f"    - {error}")
            if len(errors_remaining) > 5:
                print(f"    ... and {len(errors_remaining) - 5} more")
        else:
            print("  ✅ All syntax errors fixed!")

        return len(errors_remaining) == 0

    def run_syntax_fix(self):
        """Run complete syntax fixing"""
        print("🚀 Starting Python Syntax Fixing")
        print("=" * 60)

        self.fix_syntax_errors()

        print(f"\n📊 Fixes applied: {self.fixes_applied}")

        success = self.validate_fixes()

        print("\n🎯 Syntax Fixing Complete!")
        print("=" * 60)

        return success


if __name__ == "__main__":
    module_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    fixer = PythonSyntaxFixer(module_path)
    success = fixer.run_syntax_fix()

    if success:
        print("✅ All syntax errors fixed!")
    else:
        print("⚠️  Some syntax errors remain - manual review needed")
