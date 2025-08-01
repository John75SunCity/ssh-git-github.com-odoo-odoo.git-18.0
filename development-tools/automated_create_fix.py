#!/usr/bin/env python3
"""
Automated fix for all create methods in the records_management module
"""

import os
import glob


def fix_all_create_methods():
    """Fix all create methods automatically"""

    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    models_path = os.path.join(base_path, "models")

    print("🔧 AUTOMATED CREATE METHOD FIXES")
    print("=" * 40)

    # Get all Python model files
    model_files = glob.glob(os.path.join(models_path, "*.py"))
    model_files = [f for f in model_files if not f.endswith("__init__.py")]

    fixed_files = []

    for file_path in model_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if file has the problematic create method pattern
            if "def create(self, vals):" in content and "vals.get(" in content:

                # Replace the old pattern with new pattern
                old_lines = [
                    "    def create(self, vals):",
                    '        """Override create to set default values."""',
                    "        if not vals.get('name'):",
                    "            vals['name'] = _('New Record')",
                    "        return super().create(vals)",
                ]

                new_lines = [
                    "    @api.model_create_multi",
                    "    def create(self, vals_list):",
                    '        """Override create to set default values."""',
                    "        # Handle both single dict and list of dicts",
                    "        if not isinstance(vals_list, list):",
                    "            vals_list = [vals_list]",
                    "        ",
                    "        for vals in vals_list:",
                    "            if not vals.get('name'):",
                    "                vals['name'] = _('New Record')",
                    "        ",
                    "        return super().create(vals_list)",
                ]

                old_block = "\n".join(old_lines)
                new_block = "\n".join(new_lines)

                if old_block in content:
                    new_content = content.replace(old_block, new_block)

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)

                    filename = os.path.basename(file_path)
                    fixed_files.append(filename)
                    print(f"✅ Fixed: {filename}")

        except Exception as e:
            print(f"❌ Error in {os.path.basename(file_path)}: {e}")

    print(f"\n✅ SUCCESSFULLY FIXED {len(fixed_files)} FILES")
    if fixed_files:
        print("Fixed files:")
        for file in fixed_files:
            print(f"  - {file}")

    return len(fixed_files)


if __name__ == "__main__":
    fix_all_create_methods()
