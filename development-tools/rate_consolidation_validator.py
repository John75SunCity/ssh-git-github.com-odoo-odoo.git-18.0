#!/usr/bin/env python3
"""
Rate Management Consolidation Validator
====================================

Validates that the rate management system consolidation was successful:
1. Confirms only base_rates.py and customer_negotiated_rates.py exist
2. Validates no references to purged models remain
3. Ensures models/__init__.py imports are clean
4. Verifies view files don't reference purged models

Extension-based validation using Odoo development tools.
"""

import os
import sys
import re
from pathlib import Path


def main():
    """Validate rate management consolidation"""
    print("🔍 RATE MANAGEMENT CONSOLIDATION VALIDATOR")
    print("=" * 50)

    base_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )
    models_path = base_path / "models"
    views_path = base_path / "views"
    security_path = base_path / "security"

    success = True

    # 1. Check rate model files
    print("\n📁 CHECKING RATE MODEL FILES")
    rate_files = list(models_path.glob("*rate*.py"))
    expected_files = {"base_rates.py", "customer_negotiated_rates.py"}
    actual_files = {f.name for f in rate_files}

    if actual_files == expected_files:
        print("✅ Rate model files correct:")
        for file in expected_files:
            print(f"   ✓ {file}")
    else:
        print("❌ Rate model files mismatch:")
        print(f"   Expected: {expected_files}")
        print(f"   Actual: {actual_files}")
        success = False

    # 2. Check models/__init__.py imports
    print("\n📝 CHECKING models/__init__.py IMPORTS")
    init_file = models_path / "__init__.py"
    if init_file.exists():
        with open(init_file, "r") as f:
            content = f.read()

        purged_references = [
            "customer_rate_profile",
            "customer_retrieval_rates",
            "shredding_rates",
        ]
        found_references = []

        for ref in purged_references:
            if ref in content:
                found_references.append(ref)

        if not found_references:
            print("✅ No purged model imports found")
        else:
            print(f"❌ Found purged model imports: {found_references}")
            success = False

    # 3. Check view files for purged model references
    print("\n🎨 CHECKING VIEW FILES")
    view_files = list(views_path.glob("*.xml"))
    purged_models = [
        "customer.rate.profile",
        "customer.retrieval.rates",
        "shredding.rates",
    ]

    view_issues = []
    for view_file in view_files:
        with open(view_file, "r") as f:
            content = f.read()

        for model in purged_models:
            if model in content:
                view_issues.append(f"{view_file.name}: references {model}")

    if not view_issues:
        print("✅ No purged model references in views")
    else:
        print("❌ Found purged model references in views:")
        for issue in view_issues:
            print(f"   {issue}")
        success = False

    # 4. Check security access rules
    print("\n🔐 CHECKING SECURITY ACCESS RULES")
    access_file = security_path / "ir.model.access.csv"
    if access_file.exists():
        with open(access_file, "r") as f:
            content = f.read()

        purged_access = [
            "customer_retrieval_rates",
            "shredding_rates",
            "customer_rate_profile",
        ]
        found_access = []

        for access in purged_access:
            if access in content:
                found_access.append(access)

        if not found_access:
            print("✅ No purged model access rules found")
        else:
            print(f"❌ Found purged model access rules: {found_access}")
            success = False

    # 5. Check manifest.py for view references
    print("\n📦 CHECKING MANIFEST.PY")
    manifest_file = base_path / "__manifest__.py"
    if manifest_file.exists():
        with open(manifest_file, "r") as f:
            content = f.read()

        purged_views = ["shredding_rates_views.xml"]
        found_views = []

        for view in purged_views:
            if view in content:
                found_views.append(view)

        if not found_views:
            print("✅ No purged view references in manifest")
        else:
            print(f"❌ Found purged view references: {found_views}")
            success = False

    # Final result
    print("\n" + "=" * 50)
    if success:
        print("🎉 RATE MANAGEMENT CONSOLIDATION SUCCESSFUL!")
        print("✅ System streamlined to base_rates.py + customer_negotiated_rates.py")
        print("✅ All purged model references cleaned up")
        print("✅ Ready for continued module loading")
    else:
        print("❌ RATE MANAGEMENT CONSOLIDATION INCOMPLETE")
        print("🔧 Some references to purged models still exist")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
