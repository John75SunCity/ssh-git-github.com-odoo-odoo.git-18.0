#!/usr/bin/env python3
"""
Advanced XML-to-Model Field Validator
Cross-references XML data files with Python model definitions using AST parsing
Simulates Odoo extension capabilities for comprehensive field validation
"""

import os
import ast
import xml.etree.ElementTree as ET
import re
from pathlib import Path
from collections import defaultdict
import json


class OdooFieldExtractor:
    """Extract field definitions from Odoo model files using AST parsing"""

    def __init__(self):
        self.models = {}
        self.field_types = {}

    def parse_model_file(self, file_path):
        """Parse a Python model file and extract field definitions"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            models_info = self._extract_model_info(tree)

            for model_info in models_info:
                model_name = model_info["name"]
                fields = model_info["fields"]
                self.models[model_name] = fields
                self.field_types[model_name] = model_info["field_types"]

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    def _extract_model_info(self, tree):
        """Extract model information from AST"""
        models_found = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Look for Odoo model classes
                model_name = None
                fields = {}
                field_types = {}

                # Check if it's an Odoo model
                is_odoo_model = False
                for base in node.bases:
                    # Handle direct inheritance: models.Model, models.TransientModel
                    if isinstance(base, ast.Attribute):
                        if base.attr in ["Model", "TransientModel"]:
                            if (
                                isinstance(base.value, ast.Name)
                                and base.value.id == "models"
                            ):
                                is_odoo_model = True
                            elif base.attr in [
                                "Model",
                                "TransientModel",
                            ]:  # Direct Model/TransientModel
                                is_odoo_model = True

                if is_odoo_model:
                    # Found an Odoo model class

                    # Extract _name attribute
                    for stmt in node.body:
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Name):
                                    if target.id == "_name" and isinstance(
                                        stmt.value, ast.Constant
                                    ):
                                        model_name = stmt.value.value

                    # Extract field definitions
                    for stmt in node.body:
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if isinstance(target, ast.Name):
                                    field_name = target.id

                                    # Check if it's a field assignment
                                    if isinstance(stmt.value, ast.Call):
                                        if isinstance(stmt.value.func, ast.Attribute):
                                            if stmt.value.func.attr in [
                                                "Char",
                                                "Text",
                                                "Integer",
                                                "Float",
                                                "Boolean",
                                                "Date",
                                                "Datetime",
                                                "Selection",
                                                "Many2one",
                                                "One2many",
                                                "Many2many",
                                                "Binary",
                                                "Html",
                                                "Monetary",
                                            ]:
                                                fields[field_name] = True
                                                field_types[field_name] = (
                                                    stmt.value.func.attr
                                                )

                                                # Extract string parameter for better validation
                                                for keyword in stmt.value.keywords:
                                                    if (
                                                        keyword.arg == "string"
                                                        and isinstance(
                                                            keyword.value,
                                                            ast.Constant,
                                                        )
                                                    ):
                                                        field_types[
                                                            field_name + "_string"
                                                        ] = keyword.value.value

                    if model_name and fields:
                        models_found.append(
                            {
                                "name": model_name,
                                "fields": fields,
                                "field_types": field_types,
                            }
                        )

        return models_found


class XMLDataValidator:
    """Validate XML data against model field definitions"""

    def __init__(self, field_extractor):
        self.field_extractor = field_extractor
        self.errors = []
        self.warnings = []

    def validate_xml_file(self, xml_file_path):
        """Validate an XML data file against model definitions"""
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            file_errors = []
            file_warnings = []

            for record in root.findall(".//record"):
                model_name = record.get("model")
                record_id = record.get("id", "unknown")

                if model_name in self.field_extractor.models:
                    model_fields = self.field_extractor.models[model_name]

                    for field_elem in record.findall("field"):
                        field_name = field_elem.get("name")

                        if field_name and field_name not in model_fields:
                            # Check for common field naming patterns
                            suggestions = self._suggest_field_name(
                                field_name, model_fields
                            )

                            error_info = {
                                "file": xml_file_path.name,
                                "model": model_name,
                                "record_id": record_id,
                                "field": field_name,
                                "suggestions": suggestions,
                                "line": self._get_line_number(
                                    xml_file_path, field_name
                                ),
                            }
                            file_errors.append(error_info)

                elif (
                    model_name
                    and not model_name.startswith("ir.")
                    and not model_name.startswith("res.")
                ):
                    # Custom model not found
                    warning_info = {
                        "file": xml_file_path.name,
                        "model": model_name,
                        "record_id": record_id,
                        "issue": "Model definition not found",
                    }
                    file_warnings.append(warning_info)

            return file_errors, file_warnings

        except Exception as e:
            print(f"Error validating {xml_file_path}: {e}")
            return [], []

    def _suggest_field_name(self, field_name, model_fields):
        """Suggest correct field names based on common patterns"""
        suggestions = []

        # Common field mapping patterns
        field_mappings = {
            "customer_id": "partner_id",
            "retention_period": "retention_years",
            "customer": "partner_id",
            "client_id": "partner_id",
            "user": "user_id",
            "company": "company_id",
        }

        # Direct mapping suggestions
        if field_name in field_mappings:
            suggested_field = field_mappings[field_name]
            if suggested_field in model_fields:
                suggestions.append(suggested_field)

        # Pattern-based suggestions
        if field_name.endswith("_id") and field_name[:-3] + "_ids" in model_fields:
            suggestions.append(field_name[:-3] + "_ids")

        if field_name.endswith("_ids") and field_name[:-4] + "_id" in model_fields:
            suggestions.append(field_name[:-4] + "_id")

        # Fuzzy matching for similar field names
        for existing_field in model_fields:
            if self._similarity(field_name, existing_field) > 0.8:
                suggestions.append(existing_field)

        return suggestions[:3]  # Return top 3 suggestions

    def _similarity(self, a, b):
        """Calculate similarity between two strings"""
        if a == b:
            return 1.0

        # Simple similarity based on common characters
        common = len(set(a) & set(b))
        total = len(set(a) | set(b))
        return common / total if total > 0 else 0

    def _get_line_number(self, xml_file_path, field_name):
        """Get approximate line number of field in XML file"""
        try:
            with open(xml_file_path, "r") as f:
                lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    if f'name="{field_name}"' in line:
                        return i
        except:
            pass
        return None


def main():
    """Main execution function"""
    print("🔍 Advanced XML-to-Model Field Validator (with Odoo Extension Simulation)")
    print("=" * 80)

    records_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )

    # Step 1: Parse all Python model files
    print("\n📊 Phase 1: Extracting field definitions from Python models...")
    field_extractor = OdooFieldExtractor()

    model_files_processed = 0
    for model_dir in ["models", "wizards"]:
        model_path = records_path / model_dir
        if model_path.exists():
            for py_file in model_path.glob("*.py"):
                if py_file.name != "__init__.py":
                    field_extractor.parse_model_file(py_file)
                    model_files_processed += 1

    print(f"   ✅ Processed {model_files_processed} Python files")
    print(f"   ✅ Found {len(field_extractor.models)} Odoo models")

    for model_name, fields in field_extractor.models.items():
        print(f"      🔹 {model_name}: {len(fields)} fields")

    # Step 2: Validate XML data files
    print("\n🎯 Phase 2: Validating XML data files against model definitions...")
    validator = XMLDataValidator(field_extractor)

    all_errors = []
    all_warnings = []

    # Check both data and demo directories
    for data_dir in ["data", "demo"]:
        data_path = records_path / data_dir
        if data_path.exists():
            print(f"\n   📂 Scanning {data_dir}/ directory...")

            for xml_file in data_path.glob("*.xml"):
                print(f"      🔍 Validating {xml_file.name}...")
                errors, warnings = validator.validate_xml_file(xml_file)

                if errors:
                    print(f"         ❌ {len(errors)} field errors found")
                    all_errors.extend(errors)

                if warnings:
                    print(f"         ⚠️  {len(warnings)} warnings found")
                    all_warnings.extend(warnings)

                if not errors and not warnings:
                    print(f"         ✅ No issues found")

    # Step 3: Generate detailed report
    print("\n📋 Phase 3: Generating detailed validation report...")

    if all_errors:
        print(f"\n❌ FIELD ERRORS FOUND: {len(all_errors)}")
        print("=" * 50)

        # Group errors by model
        errors_by_model = defaultdict(list)
        for error in all_errors:
            errors_by_model[error["model"]].append(error)

        for model_name, model_errors in errors_by_model.items():
            print(f"\n🔹 Model: {model_name} ({len(model_errors)} errors)")

            for error in model_errors:
                print(f"   ❌ File: {error['file']}")
                print(f"      Record: {error['record_id']}")
                print(f"      Invalid field: '{error['field']}'")
                if error["line"]:
                    print(f"      Line: {error['line']}")
                if error["suggestions"]:
                    print(f"      Suggestions: {', '.join(error['suggestions'])}")
                print()

    # Step 4: Generate fix script
    if all_errors:
        print("\n🔧 Phase 4: Generating automated fix script...")

        fix_script = []
        fix_script.append("#!/bin/bash")
        fix_script.append("# Automated XML field fixes based on validation results")
        fix_script.append("# Generated by Advanced XML-to-Model Field Validator")
        fix_script.append("")

        for error in all_errors:
            if error["suggestions"]:
                suggested_field = error["suggestions"][0]
                file_path = f"records_management/{error['file']}"

                fix_script.append(
                    f"# Fix: {error['model']}.{error['field']} → {suggested_field}"
                )
                fix_script.append(
                    f"sed -i 's/name=\"{error['field']}\"/name=\"{suggested_field}\"/g' {file_path}"
                )
                fix_script.append("")

        # Write fix script
        fix_script_path = Path(
            "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/development-tools/auto_fix_xml_fields.sh"
        )
        with open(fix_script_path, "w") as f:
            f.write("\n".join(fix_script))

        os.chmod(fix_script_path, 0o755)
        print(f"   ✅ Generated fix script: {fix_script_path}")

    # Summary
    print(f"\n🎉 VALIDATION COMPLETE")
    print("=" * 40)
    print(f"Models analyzed: {len(field_extractor.models)}")
    print(f"Field errors found: {len(all_errors)}")
    print(f"Warnings: {len(all_warnings)}")

    if all_errors:
        print(f"\n🚨 Next steps:")
        print(f"   1. Review the errors above")
        print(f"   2. Run the generated fix script if suggestions look correct")
        print(f"   3. Manually verify critical field mappings")
        print(f"   4. Re-run this validator after fixes")
    else:
        print(f"\n✅ All XML data fields are valid!")

    return len(all_errors)


if __name__ == "__main__":
    errors_found = main()
    exit(errors_found)  # Exit with error count for CI/CD integration
