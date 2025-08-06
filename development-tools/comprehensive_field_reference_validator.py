#!/usr/bin/env python3
"""
Comprehensive Field Reference Validator
Finds ALL missing field references in XML views against Python models
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


def extract_model_fields(python_file):
    """Extract model name and all fields from Python file"""
    try:
        with open(python_file, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        model_name = None
        fields = set()

        for node in ast.walk(tree):
            # Find _name assignment for model name
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "_name":
                        if isinstance(node.value, ast.Constant) and isinstance(
                            node.value.value, str
                        ):
                            model_name = node.value.value

            # Find field assignments
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        field_name = target.id
                        # Check if it's a fields assignment
                        if isinstance(node.value, ast.Call):
                            if hasattr(node.value.func, "attr"):
                                if hasattr(node.value.func, "value") and hasattr(
                                    node.value.func.value, "id"
                                ):
                                    if node.value.func.value.id == "fields":
                                        fields.add(field_name)

        # Add standard Odoo fields that exist on all models
        standard_fields = {
            "id",
            "create_date",
            "create_uid",
            "write_date",
            "write_uid",
            "__last_update",
            "display_name",
        }
        fields.update(standard_fields)

        return model_name, fields
    except Exception as e:
        print(f"Error parsing {python_file}: {e}")
        return None, set()


def extract_xml_field_references(xml_file):
    """Extract field references from XML views"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        field_refs_by_model = defaultdict(set)

        for record in root.findall(".//record[@model='ir.ui.view']"):
            # Find the model this view is for
            model_field = record.find(".//field[@name='model']")
            view_model = None
            if model_field is not None:
                view_model = model_field.text

            if not view_model:
                continue

            # Find all field references in this view
            arch_field = record.find(".//field[@name='arch']")
            if arch_field is not None:
                # Parse the arch content as XML
                try:
                    arch_content = ET.tostring(arch_field, encoding="unicode")

                    # Find all field name references
                    field_pattern = r'<field[^>]+name="([^"]+)"'
                    matches = re.findall(field_pattern, arch_content)

                    for match in matches:
                        # Skip 'arch' and 'model' as these are view metadata fields
                        if match not in ["arch", "model"]:
                            field_refs_by_model[view_model].add(match)

                    # Also find field references in domains and other attributes
                    domain_pattern = r"'([^']+)'"
                    attr_pattern = r'["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']'

                    # Look for field references in domains and other contexts
                    for line in arch_content.split("\n"):
                        if "domain=" in line or "filter_domain=" in line:
                            # Extract potential field names from domain expressions
                            potential_fields = re.findall(
                                r"'([a-zA-Z_][a-zA-Z0-9_]*)'", line
                            )
                            for field in potential_fields:
                                if not field.startswith("_") and field not in [
                                    "ilike",
                                    "like",
                                    "=",
                                    "!=",
                                    ">",
                                    "<",
                                    ">=",
                                    "<=",
                                ]:
                                    field_refs_by_model[view_model].add(field)
                except:
                    pass

        return field_refs_by_model
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return defaultdict(set)


def main():
    """Main validation function"""
    base_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"

    print("🔍 COMPREHENSIVE FIELD REFERENCE VALIDATION")
    print("=" * 60)

    # Get all Python and XML files
    python_files = find_python_files(base_dir)
    xml_files = find_xml_files(base_dir)

    print(f"📄 Found {len(python_files)} Python model files")
    print(f"📄 Found {len(xml_files)} XML view files")

    # Extract model field information from Python files
    models_info = {}
    for python_file in python_files:
        model_name, fields = extract_model_fields(python_file)
        if model_name:
            models_info[model_name] = {"file": python_file, "fields": fields}
            print(f"📝 Model {model_name}: {len(fields)} fields")

    # Extract field references from XML files
    all_xml_field_refs = defaultdict(set)
    for xml_file in xml_files:
        xml_field_refs = extract_xml_field_references(xml_file)
        for model, field_refs in xml_field_refs.items():
            all_xml_field_refs[model].update(field_refs)
            if field_refs:
                print(
                    f"🎯 XML {os.path.basename(xml_file)}: {model} -> {len(field_refs)} field refs"
                )

    print(f"\n" + "=" * 60)
    print("🚨 MISSING FIELD REFERENCES ANALYSIS")
    print("=" * 60)

    missing_fields = defaultdict(list)
    total_missing = 0

    for model, xml_field_refs in all_xml_field_refs.items():
        if model in models_info:
            model_fields = models_info[model]["fields"]
            missing = xml_field_refs - model_fields

            if missing:
                missing_fields[model] = list(missing)
                total_missing += len(missing)
                print(f"\n🔥 MODEL: {model}")
                print(f"   File: {models_info[model]['file']}")
                print(f"   Missing Fields: {missing}")
        else:
            print(
                f"\n❓ UNKNOWN MODEL: {model} (referenced in XML but no Python model found)"
            )
            missing_fields[model] = list(xml_field_refs)
            total_missing += len(xml_field_refs)

    print(f"\n" + "=" * 60)
    print(f"📊 SUMMARY: {total_missing} TOTAL MISSING FIELD REFERENCES")
    print("=" * 60)

    if total_missing == 0:
        print("✅ ALL FIELD REFERENCES VALIDATED SUCCESSFULLY!")
    else:
        print("❌ MISSING FIELD REFERENCES NEED TO BE FIXED")

        # Generate suggestions for common field mapping fixes
        print(f"\n🔧 SUGGESTED FIELD MAPPINGS:")
        print("=" * 60)

        common_mappings = {
            "customer_id": "partner_id",
            "stored_date": "storage_start_date",
            "creation_date": "create_date",
            "container_type": "container_type_id",
            "capacity": "document_count",
            "current_usage": "document_count",
            "monthly_rate": "billing_rate",
        }

        for model, missing in missing_fields.items():
            if model in models_info:
                print(f"\n# Suggested fixes for {model}:")
                for field in missing:
                    if field in common_mappings:
                        print(f"  {field} → {common_mappings[field]}")
                    else:
                        print(f"  {field} → ADD TO MODEL OR REMOVE FROM VIEW")

    return total_missing == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
