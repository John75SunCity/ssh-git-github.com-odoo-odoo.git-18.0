#!/usr/bin/env python3
"""
Systematic Syntax Error Fixer for Records Management Models

This script fixes syntax errors that were introduced during the partner_id field addition
process, where fields got inserted in wrong places causing syntax errors.
"""

import os
import re
from pathlib import Path


class SyntaxErrorFixer:
    def __init__(self, models_path):
        self.models_path = Path(models_path)
        self.fixed_files = []
        self.errors = []

    def fix_misplaced_partner_id_fields(self):
        """Fix partner_id fields that were inserted in wrong places causing syntax errors."""

        # Files known to have partner_id placement issues
        problem_files = [
            "barcode_product.py",
            "service_item.py",
            "shredding_hard_drive.py",
            "portal_feedback_support_models.py",
            "processing_log.py",
            "paper_bale.py",
            "records_location.py",
            "shredding_team.py",
            "paper_bale_recycling.py",
            "shredding_inventory_item.py",
            "records_vehicle.py",
            "unlock_service_history.py",
            "records_access_log.py",
            "temp_inventory.py",
            "signed_document.py",
            "pickup_route.py",
            "records_document_type.py",
            "records_container_movement.py",
        ]

        for filename in problem_files:
            file_path = self.models_path / filename
            if file_path.exists():
                print(f"🔧 Fixing {filename}...")
                try:
                    self.fix_single_file(file_path)
                except Exception as e:
                    self.errors.append({"file": filename, "error": str(e)})
                    print(f"   ❌ Error: {e}")

    def fix_single_file(self, file_path):
        """Fix a single file by removing misplaced partner_id and adding it properly."""

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        fixed = False

        # Common patterns where partner_id got misplaced

        # Pattern 1: partner_id field inserted in middle of list/dict structures
        pattern1 = r"\s*partner_id = fields\.Many2one\(\s*[^)]+\)\s*[,}]\s*"
        if re.search(pattern1, content):
            content = re.sub(pattern1, "", content)
            fixed = True

        # Pattern 2: partner_id field inserted in middle of methods
        pattern2 = r"(\s*)(partner_id = fields\.Many2one\([^)]+\))\s*\n(\s*[a-zA-Z_].*)"

        def method_fix(match):
            indent, partner_field, next_line = match.groups()
            # Remove the partner_id field from this location
            return f"\n{next_line}"

        if re.search(pattern2, content):
            content = re.sub(pattern2, method_fix, content)
            fixed = True

        # Pattern 3: Broken indentation after partner_id removal
        # Fix unexpected indentation issues
        lines = content.split("\n")
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]

            # Look for lines that start with weird indentation and seem to be orphaned
            if re.match(r"^        [a-zA-Z_].*", line) and i > 0:
                prev_line = lines[i - 1].strip()
                # If previous line is empty or a comment, and this line looks like it should be method code
                if (not prev_line or prev_line.startswith("#")) and (
                    "if " in line or "for " in line or "record." in line
                ):
                    # This might be orphaned method code, try to fix indentation
                    line = "    " + line.strip()  # Reset to method level indentation

            fixed_lines.append(line)
            i += 1

        content = "\n".join(fixed_lines)

        # Fix common syntax issues

        # Fix missing commas in field definitions
        content = re.sub(
            r"(\s*)\)\s*\n(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*fields\.)",
            r"\1),\n\2",
            content,
        )

        # Fix missing closing parentheses
        # Look for field definitions that don't end properly
        content = re.sub(
            r"(fields\.[A-Za-z]+\([^)]+)\n(\s*[a-zA-Z_])", r"\1)\n\2", content
        )

        # Add partner_id field in proper location if not already present and original had it
        if (
            "partner_id" in original_content
            and "partner_id = fields.Many2one" not in content
        ):
            # Find a good place to insert partner_id (after user_id or company_id)
            insertion_patterns = [
                (
                    r"(\s*user_id = fields\.Many2one\([^)]+\)\s*,?\s*\n)",
                    r'\1    partner_id = fields.Many2one(\n        "res.partner",\n        string="Partner",\n        help="Associated partner for this record"\n    ),\n',
                ),
                (
                    r"(\s*company_id = fields\.Many2one\([^)]+\)\s*,?\s*\n)",
                    r'\1    partner_id = fields.Many2one(\n        "res.partner",\n        string="Partner",\n        help="Associated partner for this record"\n    ),\n',
                ),
            ]

            for pattern, replacement in insertion_patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    fixed = True
                    break

        # Clean up any double empty lines
        content = re.sub(r"\n\n\n+", "\n\n", content)

        if fixed or content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.fixed_files.append(str(file_path))
            print(f"   ✅ Fixed syntax errors")
        else:
            print(f"   ℹ️  No changes needed")

    def print_summary(self):
        """Print summary of fixes applied."""
        print()
        print("=" * 60)
        print("🔧 SYNTAX ERROR FIXING SUMMARY")
        print("=" * 60)
        print(f"• Files Fixed: {len(self.fixed_files)}")
        print(f"• Errors: {len(self.errors)}")
        print()

        if self.fixed_files:
            print("✅ SUCCESSFULLY FIXED:")
            for file_path in self.fixed_files:
                print(f"   • {Path(file_path).name}")
            print()

        if self.errors:
            print("❌ ERRORS:")
            for error in self.errors:
                print(f"   • {error['file']}: {error['error']}")
            print()


def main():
    """Main execution function."""
    models_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )

    if not models_path.exists():
        print(f"❌ Models directory not found: {models_path}")
        return

    fixer = SyntaxErrorFixer(models_path)
    fixer.fix_misplaced_partner_id_fields()
    fixer.print_summary()

    print()
    print("🧪 NEXT STEPS:")
    print("1. Run syntax check: python development-tools/find_syntax_errors.py")
    print("2. If issues remain, manual fixes may be needed for complex cases")
    print("3. Test module loading in Odoo.sh after fixes")


if __name__ == "__main__":
    main()
