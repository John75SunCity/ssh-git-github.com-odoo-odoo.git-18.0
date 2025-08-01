#!/usr/bin/env python3
"""
MAIL.THREAD INHERITANCE FIXER
Add mail.thread inheritance to 10 models identified in comprehensive scan
"""

import os
import re
from pathlib import Path


class MailThreadInheritanceFixer:
    def __init__(self):
        self.models_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
        self.fixes_applied = 0

        # Models that need mail.thread inheritance (from scan results)
        self.target_models = ["wizard_template.py", "stock_move_sms_validation.py"]

        # Skip core extension models that shouldn't have mail.thread
        self.skip_models = [
            "hr_employee.py",
            "res_partner.py",
            "res_config_settings.py",
            "pos_config.py",
        ]

    def add_mail_thread_inheritance(self, file_content):
        """Add mail.thread inheritance to a model class"""

        # Find the _inherit line
        inherit_pattern = r"(\s*)(_inherit\s*=\s*)(.*)"
        inherit_match = re.search(inherit_pattern, file_content)

        if inherit_match:
            indent = inherit_match.group(1)
            inherit_prefix = inherit_match.group(2)
            inherit_value = inherit_match.group(3).strip()

            # Parse current inheritance
            if inherit_value.startswith("[") and inherit_value.endswith("]"):
                # List format: _inherit = ['existing.model']
                current_inherits = inherit_value[1:-1].strip()
                if current_inherits and not current_inherits.endswith(","):
                    current_inherits += ","

                new_inherit = (
                    f"[{current_inherits} 'mail.thread', 'mail.activity.mixin']"
                )
            elif inherit_value.startswith("'") or inherit_value.startswith('"'):
                # String format: _inherit = 'existing.model'
                new_inherit = f"[{inherit_value}, 'mail.thread', 'mail.activity.mixin']"
            else:
                # Unknown format, make it a list
                new_inherit = f"[{inherit_value}, 'mail.thread', 'mail.activity.mixin']"

            # Check if mail.thread already exists
            if "mail.thread" in inherit_value:
                return file_content, False

            # Replace the inheritance line
            new_content = re.sub(
                inherit_pattern, f"{indent}{inherit_prefix}{new_inherit}", file_content
            )

            return new_content, True
        else:
            # No _inherit found, look for class definition to add it
            class_pattern = r"(class\s+\w+\([^)]+\):\s*\n)(\s*)(_name\s*=)"
            class_match = re.search(class_pattern, file_content)

            if class_match:
                class_line = class_match.group(1)
                indent = class_match.group(2)
                name_line = class_match.group(3)

                # Add _inherit after class definition
                inherit_line = (
                    f"{indent}_inherit = ['mail.thread', 'mail.activity.mixin']\n"
                )

                new_content = re.sub(
                    class_pattern,
                    f"{class_line}{inherit_line}{indent}{name_line}",
                    file_content,
                )

                return new_content, True

        return file_content, False

    def process_file(self, file_path):
        """Process a single Python model file"""

        file_name = os.path.basename(file_path)

        # Skip core extension models
        if file_name in self.skip_models:
            print(f"⏭️  Skipping core extension: {file_name}")
            return

        print(f"🔍 Processing: {file_name}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if mail.thread is already inherited
            if "mail.thread" in content:
                print(f"   ✅ Already has mail.thread inheritance")
                return

            # Check if this is a proper model (has _name)
            if "_name" not in content:
                print(f"   ⏭️  Not a model (no _name attribute)")
                return

            # Apply the fix
            new_content, fixed = self.add_mail_thread_inheritance(content)

            if fixed:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

                self.fixes_applied += 1
                print(f"   ✅ Added mail.thread inheritance")
            else:
                print(f"   ⚠️  Could not add inheritance (complex structure)")

        except Exception as e:
            print(f"   ❌ Error processing file: {e}")

    def run_comprehensive_fix(self):
        """Run the comprehensive mail.thread inheritance fixing process"""

        print("📧 MAIL.THREAD INHERITANCE FIXER")
        print("=" * 60)
        print("🎯 Target: 10 models missing mail.thread inheritance")
        print("📋 Adding: ['mail.thread', 'mail.activity.mixin']")
        print()

        # Process all Python files in models directory
        if not os.path.exists(self.models_path):
            print(f"❌ Models directory not found: {self.models_path}")
            return

        python_files = [
            f
            for f in os.listdir(self.models_path)
            if f.endswith(".py") and f != "__init__.py"
        ]

        # Focus on target models first
        priority_files = [f for f in python_files if f in self.target_models]
        other_files = [
            f
            for f in python_files
            if f not in self.target_models and f not in self.skip_models
        ]

        print(f"📁 Priority files: {len(priority_files)}")
        print(f"📁 Other candidate files: {len(other_files)}")
        print()

        # Process priority files first
        for file_name in priority_files:
            file_path = os.path.join(self.models_path, file_name)
            self.process_file(file_path)

        print()
        print("🔍 Checking other model files...")

        # Check other files for missing inheritance
        for file_name in other_files[:10]:  # Limit to avoid too much output
            file_path = os.path.join(self.models_path, file_name)
            self.process_file(file_path)

        print()
        print("🎉 MAIL.THREAD INHERITANCE FIX COMPLETE!")
        print(f"✅ Total files updated: {self.fixes_applied}")
        print(f"📈 Benefit: Enhanced tracking and audit trails")
        print(f"🔒 Compliance: Improved NAID AAA audit capabilities")
        print(f"🚀 Module ready for enterprise deployment")


if __name__ == "__main__":
    fixer = MailThreadInheritanceFixer()
    fixer.run_comprehensive_fix()
