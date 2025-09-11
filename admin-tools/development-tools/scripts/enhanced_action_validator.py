#!/usr/bin/env python3
"""
Enhanced Action Method Validation Script
=======================================

This script comprehensively validates that all action methods referenced
in view files are actually defined in the corresponding model files.

Enhanced to properly detect:
- Button action references (name="action_*")
- View model mappings
- Missing method implementations
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict


def extract_action_methods_from_model(model_file):
    """Extract action methods defined in a Python model file."""
    actions = []

    if not os.path.exists(model_file):
        return actions

    with open(model_file, "r") as f:
        content = f.read()

    # Find action methods with regex
    pattern = r"def\s+(action_[a-zA-Z_0-9]+)\s*\("
    matches = re.finditer(pattern, content)

    for match in matches:
        actions.append(match.group(1))

    return actions


def extract_model_from_view_file(xml_file):
    """Extract model name from view file."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Find record elements with model="ir.ui.view"
        for record in root.findall(".//record[@model='ir.ui.view']"):
            model_field = record.find(".//field[@name='model']")
            if model_field is not None and model_field.text:
                return model_field.text.strip()
    except Exception as e:
        print(f"⚠️ Error parsing {xml_file}: {e}")

    return None


def extract_action_references_from_view(xml_file):
    """Extract action method references from a view XML file."""
    action_refs = []
    model_name = extract_model_from_view_file(xml_file)

    if not model_name:
        return action_refs

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Find all elements with action references
        for elem in root.iter():
            # Check for type="object" with name attribute
            if elem.get("type") == "object" and elem.get("name"):
                action_name = elem.get("name")
                if action_name.startswith("action_"):
                    action_refs.append((model_name, action_name))

    except Exception as e:
        print(f"⚠️ Error parsing {xml_file}: {e}")

    return action_refs


def get_model_file_path(model_name, models_dir):
    """Get the Python file path for a model name."""
    # Convert model name to file name
    # e.g., "records.document" -> "records_document.py"
    file_name = model_name.replace(".", "_") + ".py"
    file_path = models_dir / file_name

    if file_path.exists():
        return file_path

    # Try alternative naming conventions
    alternatives = [
        model_name.split(".")[-1] + ".py",  # last part only
        "_".join(model_name.split(".")[1:]) + ".py",  # without first part
    ]

    for alt in alternatives:
        alt_path = models_dir / alt
        if alt_path.exists():
            return alt_path

    return None


def main():
    """Main validation function."""
    print("🔍 Enhanced Action Method Validation")
    print("=" * 50)

    base_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )
    views_dir = base_path / "views"
    models_dir = base_path / "models"

    if not views_dir.exists() or not models_dir.exists():
        print("❌ Views or models directory not found")
        return 1

    # Step 1: Extract all action references from views
    all_action_refs = []
    view_files = list(views_dir.glob("*.xml"))

    print(f"📁 Scanning {len(view_files)} view files...")

    for view_file in view_files:
        refs = extract_action_references_from_view(view_file)
        all_action_refs.extend(refs)
        if refs:
            print(f"   📄 {view_file.name}: {len(refs)} action references")

    # Step 2: Group by model
    model_actions = defaultdict(set)
    for model_name, action_name in all_action_refs:
        model_actions[model_name].add(action_name)

    print(
        f"\n📊 Found {len(all_action_refs)} action references across {len(model_actions)} models"
    )
    print("-" * 60)

    # Step 3: Validate each model
    missing_methods = []
    total_missing = 0

    for model_name, required_actions in model_actions.items():
        model_file = get_model_file_path(model_name, models_dir)

        if not model_file:
            print(f"❌ {model_name}: Model file not found")
            missing_methods.extend(
                [(model_name, action, "FILE_NOT_FOUND") for action in required_actions]
            )
            total_missing += len(required_actions)
            continue

        # Get existing actions
        existing_actions = set(extract_action_methods_from_model(model_file))
        missing_actions = required_actions - existing_actions

        if missing_actions:
            print(f"❌ {model_name} ({model_file.name}):")
            for action in sorted(missing_actions):
                print(f"   🔴 Missing: {action}")
                missing_methods.append((model_name, action, str(model_file)))
            total_missing += len(missing_actions)
        else:
            print(f"✅ {model_name}: All {len(required_actions)} actions defined")

    # Summary
    print("\n" + "=" * 60)
    if missing_methods:
        print(f"❌ VALIDATION FAILED: {total_missing} missing action methods")
        print(f"📋 Models needing attention: {len(set(m[0] for m in missing_methods))}")

        # Group by model for summary
        by_model = defaultdict(list)
        for model, action, file_path in missing_methods:
            by_model[model].append(action)

        print("\n📝 MISSING METHODS SUMMARY:")
        for model in sorted(by_model.keys()):
            actions = by_model[model]
            print(f"   {model}: {len(actions)} missing")
    else:
        print("✅ ALL ACTION METHODS VALIDATED SUCCESSFULLY!")

    return 1 if missing_methods else 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
