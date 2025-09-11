#!/usr/bin/env python3
"""
Complete Partner ID Standardization Script
Fix ALL missing partner_id fields across the entire system
"""

import os
import re


def add_partner_id_to_model(file_path, model_name):
    """Add partner_id field to a model file"""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Check if partner_id already exists
        if "partner_id = fields." in content:
            print(f"   ✅ {model_name}: partner_id already exists")
            return False

        # Check if customer_id exists - if so, add as related field
        if "customer_id = fields.Many2one" in content:
            partner_field = """    partner_id = fields.Many2one(
        "res.partner",
        string="Partner", 
        related="customer_id",
        store=True,
        help="Related partner field for One2many relationships compatibility"
    )"""
            print(f"   🔧 {model_name}: Adding partner_id as related to customer_id")
        else:
            # Add as regular Many2one field
            partner_field = """    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    )"""
            print(f"   🔧 {model_name}: Adding partner_id as regular Many2one field")

        # Find a good place to insert the field (after company_id or user_id)
        insert_patterns = [
            r"(\s+company_id = fields\.Many2one[^}]+}[^)]*\)[^\n]*\n)",
            r"(\s+user_id = fields\.Many2one[^}]+}[^)]*\)[^\n]*\n)",
            r"(\s+active = fields\.Boolean[^)]*\)[^\n]*\n)",
            r"(\s+name = fields\.Char[^)]*\)[^\n]*\n)",
        ]

        inserted = False
        for pattern in insert_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                insert_pos = match.end()
                new_content = (
                    content[:insert_pos]
                    + "\n"
                    + partner_field
                    + "\n"
                    + content[insert_pos:]
                )

                with open(file_path, "w") as f:
                    f.write(new_content)
                inserted = True
                break

        if not inserted:
            print(f"   ❌ {model_name}: Could not find insertion point")
            return False

        return True

    except Exception as e:
        print(f"   ❌ {model_name}: Error - {str(e)}")
        return False


def main():
    print("🔧 COMPLETE PARTNER_ID STANDARDIZATION")
    print("=" * 60)
    print("Adding partner_id fields to ALL models that need them...")

    models_dir = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )

    # Models that need partner_id fields (from script output)
    models_to_fix = [
        ("installer.py", "records.installer"),
        ("bin_key_history.py", "bin.key.history"),
        ("naid_destruction_record.py", "naid.destruction.record"),
        ("base_rates.py", "base.rates"),
        ("barcode_pricing_tier.py", "barcode.pricing.tier"),
        ("field_label_customization.py", "field.label.customization"),
        ("transitory_items.py", "transitory.items"),
        ("records_billing_config.py", "records.billing.config"),
        ("records_chain_of_custody.py", "records.chain.of.custody"),
        ("barcode_product.py", "barcode.product"),
        ("records_management_base_menus.py", "records.management.base.menus"),
        ("survey_improvement_action.py", "survey.improvement.action"),
        ("service_item.py", "service.item"),
        ("shredding_hard_drive.py", "shredding.hard_drive"),
        ("portal_feedback_support_models.py", "portal.feedback.resolution"),
        ("processing_log.py", "processing.log"),
        ("required_document.py", "required.document"),
        ("shredding_service_log.py", "shredding.service.log"),
        ("paper_bale.py", "paper.bale"),
        ("records_location.py", "records.location"),
        ("shredding_team.py", "shredding.team"),
        ("records_container_type_converter.py", "records.container.type.converter"),
        ("paper_bale_recycling.py", "paper.bale.recycling"),
        ("shredding_inventory_item.py", "shredding.inventory.item"),
        ("destruction_item.py", "destruction.item"),
        ("container_contents.py", "container.contents"),
        ("paper_load_shipment.py", "paper.load.shipment"),
        ("barcode_generation_history.py", "barcode.generation.history"),
        ("res_partner_key_restriction.py", "res.partner.key.restriction"),
        ("bin_key.py", "bin.key"),
        ("records_retention_policy.py", "records.retention.policy"),
        ("records_vehicle.py", "records.vehicle"),
        ("unlock_service_history.py", "unlock.service.history"),
        ("paper_bale_source_document.py", "paper.bale.source.document"),
        ("records_access_log.py", "records.access.log"),
        ("portal_feedback.py", "portal.feedback"),
        ("temp_inventory.py", "temp.inventory"),
        ("file_retrieval_work_order.py", "file.retrieval.work.order"),
        ("records_tag.py", "records.tag"),
        ("signed_document.py", "signed.document"),
        ("pickup_route.py", "pickup.route"),
        ("records_document_type.py", "records.document.type"),
        ("records_container_movement.py", "records.container.movement"),
        ("transitory_field_config.py", "transitory.field.config"),
    ]

    # Special cases that need different handling
    special_cases = {
        "records_container.py": "records.container",
        "records_document.py": "records.document",
    }

    fixed_count = 0
    total_count = 0

    # Fix special cases first
    print("\n🔧 FIXING SPECIAL CASES...")
    for file_name, model_name in special_cases.items():
        total_count += 1
        file_path = os.path.join(models_dir, file_name)
        if os.path.exists(file_path):
            if add_partner_id_to_model(file_path, model_name):
                fixed_count += 1
        else:
            print(f"   ❌ {model_name}: File not found")

    # Fix regular models
    print("\n🔧 FIXING REGULAR MODELS...")
    for file_name, model_name in models_to_fix:
        total_count += 1
        file_path = os.path.join(models_dir, file_name)
        if os.path.exists(file_path):
            if add_partner_id_to_model(file_path, model_name):
                fixed_count += 1
        else:
            print(f"   ❌ {model_name}: File not found")

    print(f"\n📊 SUMMARY:")
    print(f"   🎯 Total models checked: {total_count}")
    print(f"   ✅ Models fixed: {fixed_count}")
    print(f"   ❌ Models skipped: {total_count - fixed_count}")

    print(f"\n🚀 NEXT STEPS:")
    print("1. Review the changes made")
    print(
        "2. Commit all changes: git add . && git commit -m 'Complete partner_id standardization'"
    )
    print("3. Push to trigger Odoo.sh rebuild")
    print("4. Test for remaining KeyErrors")


if __name__ == "__main__":
    main()
