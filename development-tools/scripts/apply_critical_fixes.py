#!/usr/bin/env python3
"""
Apply critical missing inverse field fixes
"""
import os
import re


def apply_inverse_field_fix(file_path, field_definition):
    """Add missing inverse field to a model file"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")

    # Find a good insertion point (after core fields)
    insert_pos = -1
    for i, line in enumerate(lines):
        if (
            "user_id =" in line
            or "company_id =" in line
            or "partner_id =" in line
            or "fields.Many2one" in line
        ):
            insert_pos = i + 1

    if insert_pos == -1:
        # Find class definition and add after _inherit line
        for i, line in enumerate(lines):
            if "_inherit" in line or "_name" in line:
                insert_pos = i + 1
                while insert_pos < len(lines) and (
                    lines[insert_pos].strip().startswith("_")
                    or lines[insert_pos].strip() == ""
                ):
                    insert_pos += 1
                break

    if insert_pos != -1:
        lines.insert(insert_pos, f"    {field_definition}")
        new_content = "\n".join(lines)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"✅ Added to {os.path.basename(file_path)}: {field_definition}")
        return True
    else:
        print(f"⚠️ Could not find insertion point in {os.path.basename(file_path)}")
        return False


def main():
    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0"

    # Critical missing inverse fields
    fixes = [
        {
            "file": os.path.join(
                base_path, "records_management/models/naid_compliance_checklist.py"
            ),
            "field": 'compliance_id = fields.Many2one("naid.compliance", string="Compliance")',
        },
        {
            "file": os.path.join(
                base_path, "records_management/models/records_chain_of_custody.py"
            ),
            "field": 'work_order_id = fields.Many2one("document.retrieval.work.order", string="Work Order")',
        },
        {
            "file": os.path.join(
                base_path, "records_management/models/records_container.py"
            ),
            "field": 'converter_id = fields.Many2one("records.container.type.converter", string="Converter")',
        },
        {
            "file": os.path.join(
                base_path, "records_management/models/shredding_service.py"
            ),
            "field": 'recycling_bale_id = fields.Many2one("paper.bale.recycling", string="Recycling Bale")',
        },
        {
            "file": os.path.join(base_path, "records_management/models/paper_bale.py"),
            "field": 'load_id = fields.Many2one("load", string="Load")',
        },
    ]

    print("🔧 Applying critical missing inverse field fixes...")

    success_count = 0
    for fix in fixes:
        if apply_inverse_field_fix(fix["file"], fix["field"]):
            success_count += 1

    print(f"\n✅ Applied {success_count}/{len(fixes)} critical fixes")
    print("These fixes should resolve the KeyError issues in One2many relationships")


if __name__ == "__main__":
    main()
