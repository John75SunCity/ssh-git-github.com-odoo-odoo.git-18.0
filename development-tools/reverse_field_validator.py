#!/usr/bin/env python3
"""
Reverse Field Validation for Odoo Records Management Module
===========================================================

This tool performs reverse validation by:
1. Starting from view files and tracing back to model definitions
2. Verifying all referenced fields exist in the models
3. Checking for missing compute methods
4. Validating field relationships and dependencies

Usage: python reverse_field_validator.py
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict


class ReverseFieldValidator:
    def __init__(self, module_path):
        self.module_path = Path(module_path)
        self.model_fields = defaultdict(dict)  # model_name: {field_name: field_info}
        self.model_methods = defaultdict(set)  # model_name: {method_names}
        self.view_field_refs = defaultdict(set)  # model_name: {field_names_from_views}
        self.missing_fields = defaultdict(set)
        self.missing_compute_methods = defaultdict(set)

    def extract_model_definitions(self):
        """Extract all model definitions and their fields"""
        print("🔍 Extracting model definitions from Python files...")

        for py_file in self.module_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find model classes
                model_matches = re.finditer(
                    r"class\s+(\w+)\s*\([^)]*models\.Model[^)]*\):(.*?)(?=\nclass|\nif __name__|$)",
                    content,
                    re.DOTALL,
                )

                for match in model_matches:
                    class_name = match.group(1)
                    class_content = match.group(2)

                    # Find _name declaration
                    name_match = re.search(
                        r"_name\s*=\s*['\"]([^'\"]+)['\"]", class_content
                    )
                    if not name_match:
                        continue

                    model_name = name_match.group(1)

                    # Extract fields
                    field_matches = re.finditer(
                        r"(\w+)\s*=\s*fields\.(\w+)\([^)]*\)", class_content
                    )

                    for field_match in field_matches:
                        field_name = field_match.group(1)
                        field_type = field_match.group(2)

                        self.model_fields[model_name][field_name] = {
                            "type": field_type,
                            "file": py_file.name,
                        }

                    # Extract methods
                    method_matches = re.finditer(r"def\s+(\w+)\s*\(", class_content)
                    for method_match in method_matches:
                        method_name = method_match.group(1)
                        self.model_methods[model_name].add(method_name)

            except Exception as e:
                print(f"⚠️  Error reading {py_file}: {e}")

    def extract_view_field_references(self):
        """Extract field references from XML view files"""
        print("\n🔍 Extracting field references from XML views...")

        for xml_file in self.module_path.rglob("*.xml"):
            if "static" in str(xml_file):
                continue

            try:
                # Parse XML
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Find all records with model references
                for record in root.findall(".//record"):
                    model_field = record.find(".//field[@name='model_id']")
                    if model_field is not None:
                        # This is likely a view definition
                        model_ref = model_field.get("ref", "")
                        if model_ref.startswith("model_"):
                            model_name = model_ref[6:].replace("_", ".")

                            # Find all field references in this view
                            arch_field = record.find(".//field[@name='arch']")
                            if arch_field is not None:
                                arch_content = ET.tostring(
                                    arch_field, encoding="unicode"
                                )
                                field_refs = re.findall(
                                    r'name=["\']([^"\']+)["\']', arch_content
                                )

                                for field_ref in field_refs:
                                    if not field_ref.startswith(
                                        "__"
                                    ):  # Skip special fields
                                        self.view_field_refs[model_name].add(field_ref)

                # Also check for direct field references
                for elem in root.iter():
                    if elem.tag == "field" and "name" in elem.attrib:
                        field_name = elem.attrib["name"]

                        # Try to determine model from context
                        parent = elem.getparent()
                        while parent is not None:
                            if (
                                parent.tag == "form"
                                or parent.tag == "tree"
                                or parent.tag == "kanban"
                            ):
                                model_attr = parent.get("string", "").lower()
                                # This is a simplified approach - could be improved
                                break
                            parent = parent.getparent()

            except Exception as e:
                print(f"⚠️  Error parsing {xml_file}: {e}")

    def analyze_specific_views(self):
        """Analyze specific view files for field references"""
        print("\n🔍 Analyzing specific view files...")

        view_files = list(self.module_path.glob("views/*.xml"))

        for view_file in view_files:
            print(f"  📄 Analyzing: {view_file.name}")

            try:
                with open(view_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract model from filename or content
                model_from_filename = self.guess_model_from_filename(view_file.name)

                # Find field references
                field_refs = re.findall(
                    r'name=["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']', content
                )

                # Filter out obvious non-fields
                actual_fields = []
                for field in field_refs:
                    if field not in [
                        "arch",
                        "model",
                        "inherit_id",
                        "priority",
                        "sequence",
                    ]:
                        actual_fields.append(field)

                if model_from_filename and actual_fields:
                    print(f"    Model: {model_from_filename}")
                    print(f"    Fields found: {len(actual_fields)}")

                    # Check which fields are missing
                    if model_from_filename in self.model_fields:
                        existing_fields = set(
                            self.model_fields[model_from_filename].keys()
                        )
                        missing = set(actual_fields) - existing_fields

                        if missing:
                            print(f"    🚨 Missing fields: {missing}")
                            self.missing_fields[model_from_filename].update(missing)
                        else:
                            print(f"    ✅ All fields found in model")
                    else:
                        print(f"    ⚠️  Model definition not found")

            except Exception as e:
                print(f"    ⚠️  Error: {e}")

    def guess_model_from_filename(self, filename):
        """Guess model name from view filename"""
        # Remove common suffixes
        base_name = (
            filename.replace("_views.xml", "")
            .replace("_view.xml", "")
            .replace(".xml", "")
        )

        # Convert to model name format
        if base_name in ["records_document", "records_container", "records_location"]:
            return base_name.replace("_", ".")
        elif base_name in ["portal_request", "portal_feedback"]:
            return base_name.replace("_", ".")
        elif base_name in ["shredding_service", "shredding_rates"]:
            return base_name.replace("_", ".")
        elif base_name.startswith("naid_"):
            return base_name.replace("_", ".")
        else:
            # Default conversion
            return base_name.replace("_", ".")

    def check_computed_fields(self):
        """Check for computed fields that need compute methods"""
        print("\n🔍 Checking computed fields...")

        for model_name, fields in self.model_fields.items():
            print(f"  📊 Model: {model_name}")

            computed_fields = []
            for field_name, field_info in fields.items():
                # This is a simplified check - would need to parse field definitions more carefully
                if field_name.endswith("_count") or field_name.startswith("total_"):
                    computed_fields.append(field_name)

            if computed_fields:
                print(f"    Potential computed fields: {computed_fields}")

                # Check for corresponding compute methods
                for field_name in computed_fields:
                    expected_method = f"_compute_{field_name}"
                    if expected_method not in self.model_methods[model_name]:
                        print(f"    🚨 Missing compute method: {expected_method}")
                        self.missing_compute_methods[model_name].add(expected_method)

    def check_field_relationships(self):
        """Check Many2one/One2many field relationships"""
        print("\n🔍 Checking field relationships...")

        for model_name, fields in self.model_fields.items():
            many2one_fields = [
                f for f, info in fields.items() if info["type"] == "Many2one"
            ]
            one2many_fields = [
                f for f, info in fields.items() if info["type"] == "One2many"
            ]

            if many2one_fields or one2many_fields:
                print(f"  📊 Model: {model_name}")
                if many2one_fields:
                    print(f"    Many2one fields: {many2one_fields}")
                if one2many_fields:
                    print(f"    One2many fields: {one2many_fields}")

    def generate_missing_field_fixes(self):
        """Generate code to fix missing fields"""
        print("\n🔧 Generating fixes for missing fields...")

        for model_name, missing_fields in self.missing_fields.items():
            if missing_fields:
                print(f"\n# Missing fields for {model_name}:")
                for field in sorted(missing_fields):
                    if field.endswith("_ids"):
                        print(
                            f"    {field} = fields.One2many('related.model', 'inverse_field', string='{field.replace('_', ' ').title()}')"
                        )
                    elif field.endswith("_id"):
                        print(
                            f"    {field} = fields.Many2one('related.model', string='{field.replace('_', ' ').title()}')"
                        )
                    elif field.endswith("_count"):
                        print(
                            f"    {field} = fields.Integer(string='{field.replace('_', ' ').title()}', compute='_compute_{field}')"
                        )
                    elif field in ["active", "state"]:
                        if field == "active":
                            print(
                                f"    {field} = fields.Boolean(string='Active', default=True)"
                            )
                        else:
                            print(
                                f"    {field} = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='State', default='draft')"
                            )
                    else:
                        print(
                            f"    {field} = fields.Char(string='{field.replace('_', ' ').title()}')"
                        )

    def run_reverse_validation(self):
        """Run complete reverse validation"""
        print("🚀 Starting Reverse Field Validation")
        print("=" * 60)

        self.extract_model_definitions()
        print(f"✅ Found {len(self.model_fields)} models with fields")

        self.extract_view_field_references()
        self.analyze_specific_views()
        self.check_computed_fields()
        self.check_field_relationships()
        self.generate_missing_field_fixes()

        # Summary
        total_missing = sum(len(fields) for fields in self.missing_fields.values())
        total_missing_methods = sum(
            len(methods) for methods in self.missing_compute_methods.values()
        )

        print(f"\n📊 Summary:")
        print(f"   Missing fields: {total_missing}")
        print(f"   Missing compute methods: {total_missing_methods}")

        print("\n🎯 Reverse Validation Complete!")
        print("=" * 60)


if __name__ == "__main__":
    module_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    validator = ReverseFieldValidator(module_path)
    validator.run_reverse_validation()
