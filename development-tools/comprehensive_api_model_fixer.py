#!/usr/bin/env python3

"""
Comprehensive Fix for @api.model Deprecation Warnings

This script removes all problematic @api.model decorators that are causing
deprecation warnings in Odoo 18.0. The warnings occur when @api.model is used
on methods that don't actually need to be model methods.
"""

import os
import re


def fix_model_deprecation_warnings():
    """Remove @api.model decorators that cause deprecation warnings"""

    models_dir = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )

    # List of model files mentioned in the error log
    problem_models = [
        "records_tag.py",
        "records_document_type.py",
        "records_retention_policy.py",
        "container_contents.py",
        "records_document.py",
        "temp_inventory.py",
        "pickup_route.py",
        "records_vehicle.py",
        "shredding_service.py",
        "shredding_service_log.py",
        "destruction_item.py",
        "document_retrieval_work_order.py",
        "file_retrieval_work_order.py",
        "customer_retrieval_rates.py",
        "bin_key_management.py",
        "bin_unlock_service.py",
        "paper_bale_recycling.py",
        "paper_load_shipment.py",
        "load.py",
        "naid_certificate.py",
        "portal_request.py",
        "portal_feedback.py",
        "survey_improvement_action.py",
        "field_label_customization.py",
        "res_partner.py",
        "fsm_task.py",
        "pos_config.py",
    ]

    fixed_files = []

    for model_file in problem_models:
        filepath = os.path.join(models_dir, model_file)

        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {model_file}")
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Find the problematic @api.model decorator (typically at line 65 based on error)
            # The pattern that causes warnings is when @api.model is used without proper create override

            # Remove @api.model decorators that are followed by empty methods or simple returns
            patterns_to_remove = [
                # Remove @api.model from line 65 area (common location from errors)
                r'(\s*)@api\.model\s*\n(\s*def\s+\w+\([^)]*\):\s*\n\s*(?:pass|return\s+["\'\w\[\]{}(),.\s]*)\s*\n)',
                # Remove standalone @api.model that don't have proper method overrides
                r"(\s*)@api\.model\s*\n(?=\s*\n|\s*#|\s*$)",
                # Remove @api.model from methods that just return static values
                r'(\s*)@api\.model\s*\n(\s*def\s+[^(]+\([^)]*\):\s*\n\s*return\s+(?:False|True|None|""|\'\'|\[\]|\{\})\s*\n)',
            ]

            for pattern in patterns_to_remove:
                content = re.sub(pattern, r"\1\2", content, flags=re.MULTILINE)

            # More specific fix: Remove @api.model from methods that don't override create
            # This is the main cause of the deprecation warnings
            content = re.sub(
                r"(\s+)@api\.model\s*\n(\s+def\s+(?!create)[^(]+\([^)]*\):\s*\n(?:\s+.*\n)*?\s+.*\n)",
                r"\1\2",
                content,
                flags=re.MULTILINE,
            )

            # Remove any remaining standalone @api.model decorators
            content = re.sub(r"^\s*@api\.model\s*$", "", content, flags=re.MULTILINE)

            if content != original_content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_files.append(model_file)
                print(f"✅ Fixed deprecation warnings in: {model_file}")
            else:
                print(f"📝 No changes needed in: {model_file}")

        except Exception as e:
            print(f"❌ Error processing {model_file}: {str(e)}")
            continue

    return fixed_files


def clean_up_all_models():
    """Clean up @api.model decorators in all model files"""

    models_dir = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )

    fixed_count = 0

    for filename in os.listdir(models_dir):
        if not filename.endswith(".py") or filename == "__init__.py":
            continue

        filepath = os.path.join(models_dir, filename)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Remove problematic @api.model decorators
            # Keep only @api.model on actual create, write, unlink method overrides

            # Remove @api.model from non-override methods
            content = re.sub(
                r"(\s+)@api\.model\s*\n(\s+def\s+(?!create|write|unlink)[^(]+\([^)]*\):[^\n]*\n(?:\s+[^\n]*\n)*?)",
                r"\1\2",
                content,
                flags=re.MULTILINE,
            )

            if content != original_content:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                fixed_count += 1
                print(f"✅ Cleaned up: {filename}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {str(e)}")
            continue

    return fixed_count


if __name__ == "__main__":
    print("🔧 COMPREHENSIVE @API.MODEL DEPRECATION FIX")
    print("=" * 50)

    print("\n1️⃣ Fixing specific problem models...")
    fixed_files = fix_model_deprecation_warnings()

    print(f"\n2️⃣ Cleaning up all model files...")
    cleaned_count = clean_up_all_models()

    print(f"\n🎯 FIXES COMPLETED")
    print(f"   📁 Problem models fixed: {len(fixed_files)}")
    print(f"   🧹 All models cleaned: {cleaned_count}")
    print(f"\n✅ Deprecation warnings should now be resolved!")
