#!/usr/bin/env python3
"""
Debug script to find field relationship issues
"""
import os
import re
import glob


def find_one2many_fields():
    """Find all One2many fields and their inverse_name patterns"""
    patterns = []

    # Search for One2many field definitions
    py_files = glob.glob(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/*.py"
    )

    for py_file in py_files:
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

            # Find One2many patterns
            one2many_matches = re.findall(
                r'(\w+)\s*=\s*fields\.One2many\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']',
                content,
            )

            for field_name, comodel, inverse_name in one2many_matches:
                patterns.append(
                    {
                        "file": py_file,
                        "field_name": field_name,
                        "comodel": comodel,
                        "inverse_name": inverse_name,
                    }
                )
                if "billing" in inverse_name or "contact" in inverse_name:
                    print(f"POTENTIAL BILLING/CONTACT FIELD:")
                    print(f"  File: {os.path.basename(py_file)}")
                    print(f"  Field: {field_name}")
                    print(f"  Comodel: {comodel}")
                    print(f"  Inverse: {inverse_name}")
                    print("---")

    print(f"Total patterns found: {len(patterns)}")
    return patterns


if __name__ == "__main__":
    find_one2many_fields()
