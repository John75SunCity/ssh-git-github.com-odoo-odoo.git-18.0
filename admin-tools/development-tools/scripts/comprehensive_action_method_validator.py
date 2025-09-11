#!/usr/bin/env python3
"""
Comprehensive Action Method Validator
Finds ALL missing action methods referenced in XML views but not defined in Python models
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
import ast


def find_python_files(directory):
    """Find all Python model files"""
    python_files = []
    models_dir = os.path.join(directory, "models")
    if os.path.exists(models_dir):
        for file in os.listdir(models_dir):
            if file.endswith(".py") and file != "__init__.py":
                python_files.append(os.path.join(models_dir, file))
    return python_files


def find_xml_files(directory):
    """Find all XML view files"""
    xml_files = []
    views_dir = os.path.join(directory, "views")
    if os.path.exists(views_dir):
        for file in os.listdir(views_dir):
            if file.endswith(".xml"):
                xml_files.append(os.path.join(views_dir, file))
    return xml_files


def extract_model_info(python_file):
    """Extract model name and action methods from Python file"""
    try:
        with open(python_file, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        model_name = None
        action_methods = []

        for node in ast.walk(tree):
            # Find _name assignment for model name
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "_name":
                        if isinstance(node.value, ast.Str):
                            model_name = node.value.s
                        elif isinstance(node.value, ast.Constant) and isinstance(
                            node.value.value, str
                        ):
                            model_name = node.value.value

            # Find action methods (methods starting with 'action_')
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("action_"):
                    action_methods.append(node.name)

        return model_name, action_methods
    except Exception as e:
        print(f"Error parsing {python_file}: {e}")
        return None, []


def extract_xml_actions(xml_file):
    """Extract action method references from XML views"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        actions_by_model = defaultdict(set)

        for record in root.findall(".//record[@model='ir.ui.view']"):
            # Find the model this view is for
            model_field = record.find(".//field[@name='model']")
            view_model = None
            if model_field is not None:
                view_model = model_field.text

            if not view_model:
                continue

            # Find all action references in this view
            arch_field = record.find(".//field[@name='arch']")
            if arch_field is not None:
                arch_content = ET.tostring(arch_field, encoding="unicode")

                # Find action method references in buttons and other elements
                action_patterns = [
                    r'name="(action_[^"]+)"',
                    r'action="(action_[^"]+)"',
                ]

                for pattern in action_patterns:
                    matches = re.findall(pattern, arch_content)
                    for match in matches:
                        actions_by_model[view_model].add(match)

        return actions_by_model
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return defaultdict(set)


def main():
    """Main validation function"""
    base_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"

    print("🔍 COMPREHENSIVE ACTION METHOD VALIDATION")
    print("=" * 60)

    # Get all Python and XML files
    python_files = find_python_files(base_dir)
    xml_files = find_xml_files(base_dir)

    print(f"📄 Found {len(python_files)} Python model files")
    print(f"📄 Found {len(xml_files)} XML view files")

    # Extract model information from Python files
    models_info = {}
    for python_file in python_files:
        model_name, actions = extract_model_info(python_file)
        if model_name:
            models_info[model_name] = {"file": python_file, "actions": set(actions)}
            print(f"📝 Model {model_name}: {len(actions)} action methods")

    # Extract action references from XML files
    all_xml_actions = defaultdict(set)
    for xml_file in xml_files:
        xml_actions = extract_xml_actions(xml_file)
        for model, actions in xml_actions.items():
            all_xml_actions[model].update(actions)
            if actions:
                print(f"🎯 XML {os.path.basename(xml_file)}: {model} -> {actions}")

    print("\n" + "=" * 60)
    print("🚨 MISSING ACTION METHODS ANALYSIS")
    print("=" * 60)

    missing_actions = defaultdict(list)
    total_missing = 0

    for model, xml_actions in all_xml_actions.items():
        if model in models_info:
            model_actions = models_info[model]["actions"]
            missing = xml_actions - model_actions

            if missing:
                missing_actions[model] = list(missing)
                total_missing += len(missing)
                print(f"\n🔥 MODEL: {model}")
                print(f"   File: {models_info[model]['file']}")
                print(f"   Missing: {missing}")
        else:
            print(
                f"\n❓ UNKNOWN MODEL: {model} (referenced in XML but no Python model found)"
            )
            missing_actions[model] = list(xml_actions)
            total_missing += len(xml_actions)

    print(f"\n" + "=" * 60)
    print(f"📊 SUMMARY: {total_missing} TOTAL MISSING ACTION METHODS")
    print("=" * 60)

    if total_missing == 0:
        print("✅ ALL ACTION METHODS VALIDATED SUCCESSFULLY!")
    else:
        print("❌ MISSING ACTION METHODS NEED TO BE ADDED")

        # Generate fix suggestions
        print(f"\n🔧 AUTO-FIX SUGGESTIONS:")
        print("=" * 60)

        for model, actions in missing_actions.items():
            if model in models_info:
                print(f"\n# Add to {models_info[model]['file']}:")
                for action in actions:
                    print(
                        f"""
    def {action}(self):
        \"\"\"Generated action method for {action}\"\"\"
        self.ensure_one()
        # TODO: Implement {action} logic
        return {{
            "type": "ir.actions.act_window",
            "name": "Action: {action.replace('_', ' ').title()}",
            "res_model": "{model}",
            "view_mode": "form",
            "target": "new",
        }}"""
                    )

    return total_missing == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
