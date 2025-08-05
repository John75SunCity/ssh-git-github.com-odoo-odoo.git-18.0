#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add only the legitimate missing inverse fields found by the relationship auditor.
This script adds the specific missing Many2one fields needed for One2many relationships.
"""

import os


def add_missing_inverse_fields():
    """Add the specific missing inverse fields identified by the auditor"""

    base_path = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )

    fixes = [
        {
            "file": "barcode_storage_box.py",
            "field": 'product_id = fields.Many2one("barcode.product", string="Product")',
            "comment": "# Missing inverse field for barcode.product One2many relationship",
        },
        {
            "file": "portal_request.py",
            "field": 'service_item_id = fields.Many2one("service.item", string="Service Item")',
            "comment": "# Missing inverse field for service.item One2many relationship",
        },
        {
            "file": "barcode_product.py",
            "field": 'storage_box_id = fields.Many2one("barcode.storage.box", string="Storage Box")',
            "comment": "# Missing inverse field for barcode.storage.box One2many relationship",
        },
        {
            "file": "processing_log.py",
            "field": 'pos_wizard_id = fields.Many2one("visitor.pos.wizard", string="POS Wizard")',
            "comment": "# Missing inverse field for visitor.pos.wizard One2many relationship",
        },
        {
            "file": "service_item.py",
            "field": 'pos_wizard_id = fields.Many2one("visitor.pos.wizard", string="POS Wizard")',
            "comment": "# Missing inverse field for visitor.pos.wizard One2many relationship",
        },
    ]

    for fix in fixes:
        filepath = os.path.join(base_path, fix["file"])

        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filepath}")
            continue

        print(f"🔧 Adding inverse field to {fix['file']}")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the best place to insert the field (after other relationship fields)
        if "# RELATIONSHIP FIELDS" in content:
            # Insert after the relationship fields comment
            insertion_point = content.find("# RELATIONSHIP FIELDS")
            end_of_line = content.find("\n", insertion_point) + 1

            # Find the end of the relationship fields section
            next_section = content.find("# ===", end_of_line)
            if next_section == -1:
                next_section = content.find("    # Mail Thread", end_of_line)
            if next_section == -1:
                next_section = len(content)

            # Insert before the next section
            new_field = f"    {fix['comment']}\n    {fix['field']}\n\n"
            updated_content = (
                content[:next_section] + new_field + content[next_section:]
            )

        else:
            # If no relationship fields section, add before Mail Thread fields
            if "# Mail Thread Framework Fields" in content:
                insertion_point = content.find("# Mail Thread Framework Fields")
                new_field = f"    # ============================================================================\n    # RELATIONSHIP FIELDS\n    # ============================================================================\n    {fix['comment']}\n    {fix['field']}\n\n    # "
                updated_content = (
                    content[:insertion_point] + new_field + content[insertion_point:]
                )

            else:
                print(f"⚠️  Could not find suitable insertion point in {fix['file']}")
                continue

        # Write the updated content
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(updated_content)

        print(f"✅ Added {fix['field']} to {fix['file']}")

    print("\n🎉 Successfully added all missing inverse fields!")


if __name__ == "__main__":
    add_missing_inverse_fields()
