#!/usr/bin/env python3
"""
Comprehensive Action Method Validation Script

This script validates that all action methods referenced in view files
are actually defined in the corresponding model files.
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


def extract_action_references_from_view(xml_file):
    """Extract action method references from a view XML file."""
    action_refs = []

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Find all elements with action references
        for elem in root.iter():
            # Check for type="object" with name attribute
            if elem.get("type") == "object" and elem.get("name"):
                action_name = elem.get("name")
                if action_name.startswith("action_"):
                    # Get model from parent view definition
                    view_elem = elem
                    while view_elem is not None:
                        if (
                            view_elem.tag == "record"
                            and view_elem.get("model") == "ir.ui.view"
                        ):
                            # Find model field in this view record
                            for field in view_elem.findall('.//field[@name="model"]'):
                                if field.text:
                                    action_refs.append(
                                        {
                                            "file": xml_file,
                                            "model": field.text,
                                            "action": action_name,
                                            "element": elem.tag,
                                        }
                                    )
                                    break
                            break
                        view_elem = (
                            view_elem.getparent()
                            if hasattr(view_elem, "getparent")
                            else None
                        )

    except ET.ParseError as e:
        print(f"XML Parse Error in {xml_file}: {e}")

    return action_refs


def main():
    """Main validation function."""
    base_dir = Path(__file__).parent.parent
    views_dir = base_dir / "records_management" / "views"
    models_dir = base_dir / "records_management" / "models"

    print("🔍 Comprehensive Action Method Validation")
    print("=" * 50)

    # Collect all action references from view files
    all_action_refs = []
    view_files = list(views_dir.glob("*.xml"))

    for view_file in view_files:
        print(f"Scanning views: {view_file.name}")
        refs = extract_action_references_from_view(view_file)
        all_action_refs.extend(refs)

    # Group by model
    actions_by_model = defaultdict(list)
    for ref in all_action_refs:
        actions_by_model[ref["model"]].append(ref)

    print(
        f"\n📊 Found {len(all_action_refs)} action references across {len(actions_by_model)} models"
    )
    print("-" * 60)

    # Check each model for missing action methods
    missing_actions = []

    for model_name, action_refs in actions_by_model.items():
        # Convert model name to file path
        model_file = models_dir / f"{model_name.replace('.', '_')}.py"

        # Get defined action methods
        defined_actions = extract_action_methods_from_model(model_file)

        # Check for missing actions
        referenced_actions = list(set([ref["action"] for ref in action_refs]))

        for action in referenced_actions:
            if action not in defined_actions:
                missing_actions.append(
                    {
                        "model": model_name,
                        "action": action,
                        "model_file": model_file,
                        "references": [
                            ref for ref in action_refs if ref["action"] == action
                        ],
                    }
                )

        print(
            f"✅ {model_name}: {len(defined_actions)} defined, {len(referenced_actions)} referenced"
        )
        if defined_actions:
            print(f"   Defined: {', '.join(defined_actions)}")
        if referenced_actions:
            print(f"   Referenced: {', '.join(referenced_actions)}")
        print()

    # Report missing actions
    if missing_actions:
        print(f"❌ Found {len(missing_actions)} missing action methods:")
        print("=" * 60)

        for missing in missing_actions:
            print(f"🚨 Model: {missing['model']}")
            print(f"   Missing Action: {missing['action']}")
            print(f"   Model File: {missing['model_file']}")
            print(f"   Referenced in:")
            for ref in missing["references"]:
                print(f"     - {Path(ref['file']).name} ({ref['element']} element)")
            print()

        return len(missing_actions)
    else:
        print("✅ All action methods are properly defined!")
        return 0


if __name__ == "__main__":
    exit(main())
