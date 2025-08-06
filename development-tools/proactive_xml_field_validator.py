#!/usr/bin/env python3
"""
Proactive XML Field Validator
Cross-references all XML data files with model definitions to catch field mismatches
before deployment. Uses systematic analysis to prevent runtime errors.
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def get_model_fields(model_file_path):
    """Extract all field definitions from a Python model file"""
    fields = set()

    try:
        with open(model_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find all field definitions: field_name = fields.Type(...)
        field_matches = re.findall(r"^\s*(\w+)\s*=\s*fields\.", content, re.MULTILINE)
        fields.update(field_matches)

        # Also look for related fields and computed fields
        related_matches = re.findall(r'related="([^"]+)"', content)
        for related_path in related_matches:
            # Extract the final field name from related paths like "partner_id.name"
            if "." in related_path:
                related_field = related_path.split(".")[-1]
                fields.add(related_field)

    except Exception as e:
        print(f"Error reading model {model_file_path}: {e}")

    return fields


def get_model_name_from_file(model_file_path):
    """Extract the model name (_name) from a Python model file"""
    try:
        with open(model_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find _name = "model.name"
        name_match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', content)
        if name_match:
            return name_match.group(1)

    except Exception as e:
        print(f"Error extracting model name from {model_file_path}: {e}")

    return None


def analyze_xml_file(xml_file_path):
    """Extract field references from an XML data file"""
    field_references = {}  # model_name -> set of field names

    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        # Find all record elements
        for record in root.findall(".//record"):
            model_name = record.get("model")
            if not model_name:
                continue

            if model_name not in field_references:
                field_references[model_name] = set()

            # Find all field elements within this record
            for field_elem in record.findall(".//field"):
                field_name = field_elem.get("name")
                if field_name:
                    field_references[model_name].add(field_name)

    except Exception as e:
        print(f"Error parsing XML file {xml_file_path}: {e}")

    return field_references


def build_model_registry(records_path):
    """Build a registry of all models and their fields"""
    model_registry = {}  # model_name -> set of field names

    # Search for model files in models/ and wizards/ directories
    for model_dir in ["models", "wizards"]:
        model_path = records_path / model_dir
        if not model_path.exists():
            continue

        for model_file in model_path.glob("*.py"):
            if model_file.name.startswith("__"):
                continue

            model_name = get_model_name_from_file(model_file)
            if model_name:
                model_fields = get_model_fields(model_file)
                model_registry[model_name] = model_fields

    return model_registry


def validate_xml_files(records_path, model_registry):
    """Validate all XML files against the model registry"""
    validation_results = {"errors": [], "warnings": [], "summary": {}}

    # Find all XML files
    xml_files = []
    for xml_dir in ["data", "demo", "views"]:
        xml_path = records_path / xml_dir
        if xml_path.exists():
            xml_files.extend(xml_path.glob("*.xml"))

    total_field_refs = 0
    total_errors = 0

    for xml_file in xml_files:
        print(f"\n🔍 Analyzing {xml_file.relative_to(records_path)}")

        field_references = analyze_xml_file(xml_file)

        for model_name, xml_fields in field_references.items():
            total_field_refs += len(xml_fields)

            # Check if model exists
            if model_name not in model_registry:
                error = f"❌ Model '{model_name}' not found in registry"
                validation_results["errors"].append(
                    {
                        "file": str(xml_file.relative_to(records_path)),
                        "model": model_name,
                        "error": error,
                    }
                )
                print(f"   {error}")
                continue

            model_fields = model_registry[model_name]
            missing_fields = xml_fields - model_fields

            if missing_fields:
                error_count = len(missing_fields)
                total_errors += error_count

                error = f"❌ {error_count} invalid fields in {model_name}: {', '.join(sorted(missing_fields)[:5])}{'...' if len(missing_fields) > 5 else ''}"
                validation_results["errors"].append(
                    {
                        "file": str(xml_file.relative_to(records_path)),
                        "model": model_name,
                        "invalid_fields": sorted(missing_fields),
                        "error": error,
                    }
                )
                print(f"   {error}")
            else:
                print(f"   ✅ {model_name}: {len(xml_fields)} fields validated")

    validation_results["summary"] = {
        "total_xml_files": len(xml_files),
        "total_field_references": total_field_refs,
        "total_errors": total_errors,
        "models_checked": len(
            set(
                model_name
                for xml_file in xml_files
                for model_name in analyze_xml_file(xml_file).keys()
            )
        ),
    }

    return validation_results


def generate_field_fixes(records_path, validation_results):
    """Generate suggested fixes for field mismatches"""
    fixes = []

    print(f"\n🔧 SUGGESTED FIXES:")
    print(f"==================")

    for error in validation_results["errors"]:
        if "invalid_fields" not in error:
            continue

        model_name = error["model"]
        invalid_fields = error["invalid_fields"]
        file_path = error["file"]

        print(f"\n📁 File: {file_path}")
        print(f"🎯 Model: {model_name}")
        print(
            f"❌ Invalid fields ({len(invalid_fields)}): {', '.join(invalid_fields[:10])}{'...' if len(invalid_fields) > 10 else ''}"
        )

        # Suggest common fixes
        for field in invalid_fields[:5]:  # Show fixes for first 5 fields
            suggestions = []

            if field.endswith("_id") and field.replace("_id", "") in [
                "customer",
                "client",
            ]:
                suggestions.append(f"   💡 {field} → partner_id (Odoo standard)")
            elif field == "retention_period":
                suggestions.append(f"   💡 {field} → retention_years (based on model)")
            elif "date" in field and not field.endswith("_date"):
                suggestions.append(f"   💡 {field} → {field}_date")
            elif "status" in field and field != "state":
                suggestions.append(f"   💡 {field} → state (Odoo standard)")

            if suggestions:
                for suggestion in suggestions:
                    print(suggestion)

        fixes.append(
            {"file": file_path, "model": model_name, "invalid_fields": invalid_fields}
        )

    return fixes


def main():
    """Main execution function"""
    print("🚀 Proactive XML Field Validator")
    print("=================================")

    records_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )

    if not records_path.exists():
        print("❌ Records management path not found")
        return

    # Build model registry
    print("📋 Building model registry...")
    model_registry = build_model_registry(records_path)
    print(f"   Found {len(model_registry)} models with field definitions")

    # Validate XML files
    print("\n🔍 Validating XML files against models...")
    validation_results = validate_xml_files(records_path, model_registry)

    # Print summary
    summary = validation_results["summary"]
    print(f"\n📊 VALIDATION SUMMARY:")
    print(f"======================")
    print(f"XML Files Analyzed: {summary['total_xml_files']}")
    print(f"Models Checked: {summary['models_checked']}")
    print(f"Field References: {summary['total_field_references']}")
    print(f"Errors Found: {summary['total_errors']}")

    if summary["total_errors"] > 0:
        print(
            f"\n❌ CRITICAL: {summary['total_errors']} field validation errors found!"
        )
        print(f"These will cause runtime ParseError exceptions during deployment.")

        # Generate fixes
        fixes = generate_field_fixes(records_path, validation_results)

        print(f"\n🎯 PRIORITY ACTION REQUIRED:")
        print(f"Fix these {summary['total_errors']} field mismatches before deployment")
        print(f"Each error will cause a ValueError during XML data loading")
    else:
        print(f"\n✅ SUCCESS: All XML field references validated successfully!")
        print(f"No field mismatches detected - ready for deployment")

    return validation_results


if __name__ == "__main__":
    main()
