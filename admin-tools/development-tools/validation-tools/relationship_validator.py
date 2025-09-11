#!/usr/bin/env python3
"""
Comprehensive One2many/Many2one Relationship Validator
Proactively identifies missing inverse fields and relationship issues
"""
import os
import re
import sys
from collections import defaultdict


def extract_relationships(file_path):
    """Extract One2many and Many2one relationships from a Python file"""
    relationships = {"one2many": [], "many2one": [], "model_name": None}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract model name
        model_match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', content)
        if model_match:
            relationships["model_name"] = model_match.group(1)

        # Extract One2many fields
        one2many_pattern = r'(\w+)\s*=\s*fields\.One2many\(\s*["\']([^"\']+)["\']\s*,\s*["\']([^"\']+)["\']'
        one2many_matches = re.findall(one2many_pattern, content)
        for field_name, comodel, inverse_field in one2many_matches:
            relationships["one2many"].append(
                {
                    "field_name": field_name,
                    "comodel": comodel,
                    "inverse_field": inverse_field,
                    "file": file_path,
                }
            )

        # Extract Many2one fields
        many2one_pattern = (
            r'(\w+)\s*=\s*fields\.Many2one\(\s*["\']([^"\']+)["\']'
        )
        many2one_matches = re.findall(many2one_pattern, content)
        for field_name, comodel in many2one_matches:
            relationships["many2one"].append(
                {
                    "field_name": field_name,
                    "comodel": comodel,
                    "file": file_path,
                }
            )

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return relationships


def find_model_files():
    """Find all Python model files"""
    model_files = []
    models_dir = "records_management/models"

    if not os.path.exists(models_dir):
        print(f"Error: {models_dir} directory not found")
        return []

    for root, dirs, files in os.walk(models_dir):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                model_files.append(os.path.join(root, file))

    return model_files


def analyze_relationships():
    """Analyze all relationships and identify issues"""
    model_files = find_model_files()
    print(f"🔍 Analyzing {len(model_files)} model files...")

    # Data structures
    models = {}  # model_name -> file_info
    one2many_fields = []  # All One2many fields
    many2one_fields = {}  # comodel -> [many2one_fields]
    issues = []

    # Extract all relationships
    for file_path in model_files:
        rel_info = extract_relationships(file_path)
        if rel_info["model_name"]:
            models[rel_info["model_name"]] = {
                "file": file_path,
                "one2many": rel_info["one2many"],
                "many2one": rel_info["many2one"],
            }
            one2many_fields.extend(rel_info["one2many"])

            # Group Many2one fields by target model
            for m2o in rel_info["many2one"]:
                if m2o["comodel"] not in many2one_fields:
                    many2one_fields[m2o["comodel"]] = []
                many2one_fields[m2o["comodel"]].append(m2o)

    print(
        f"📊 Found {len(models)} models with {len(one2many_fields)} One2many relationships"
    )

    # Check for missing inverse fields
    print("\n🚨 CHECKING FOR MISSING INVERSE FIELDS:")
    missing_inverse = []

    for o2m in one2many_fields:
        target_model = o2m["comodel"]
        inverse_field = o2m["inverse_field"]

        # Check if target model exists
        if target_model not in models:
            issues.append(
                f"❌ MISSING MODEL: {o2m['field_name']} in {o2m['file']} references unknown model '{target_model}'"
            )
            continue

        # Check if inverse field exists in target model
        target_many2ones = models[target_model]["many2one"]
        inverse_exists = any(
            m2o["field_name"] == inverse_field for m2o in target_many2ones
        )

        if not inverse_exists:
            missing_inverse.append(
                {
                    "source_file": o2m["file"],
                    "source_field": o2m["field_name"],
                    "target_model": target_model,
                    "target_file": models[target_model]["file"],
                    "missing_field": inverse_field,
                }
            )

    # Check for orphaned Many2one fields
    print(f"\n🔗 CHECKING FOR ORPHANED MANY2ONE FIELDS:")
    orphaned_m2o = []

    for model_name, model_info in models.items():
        for m2o in model_info["many2one"]:
            target_model = m2o["comodel"]
            field_name = m2o["field_name"]

            # Skip standard Odoo models
            if target_model.startswith(("res.", "mail.", "ir.", "base.")):
                continue

            # Check if there's a corresponding One2many
            has_corresponding_o2m = any(
                o2m["comodel"] == model_name
                and o2m["inverse_field"] == field_name
                for o2m in one2many_fields
            )

            if not has_corresponding_o2m and target_model in models:
                orphaned_m2o.append(
                    {
                        "model": model_name,
                        "file": m2o["file"],
                        "field": field_name,
                        "target_model": target_model,
                    }
                )

    # Report results
    print(f"\n📋 RELATIONSHIP ANALYSIS RESULTS:")
    print(f"=" * 50)
    print(f"Models analyzed: {len(models)}")
    print(f"One2many fields: {len(one2many_fields)}")
    print(
        f"Total Many2one fields: {sum(len(m['many2one']) for m in models.values())}"
    )
    print(f"Missing inverse fields: {len(missing_inverse)}")
    print(f"Potentially orphaned Many2one fields: {len(orphaned_m2o)}")

    if missing_inverse:
        print(f"\n🚨 CRITICAL: {len(missing_inverse)} MISSING INVERSE FIELDS:")
        for issue in missing_inverse:
            print(f"  ❌ {issue['source_file']}")
            print(
                f"     One2many field '{issue['source_field']}' expects '{issue['missing_field']}' field"
            )
            print(
                f"     in model '{issue['target_model']}' ({issue['target_file']})"
            )
            print(
                f"     --> ADD: {issue['missing_field']} = fields.Many2one('{models[issue['target_model']]['file'].split('/')[-1].replace('.py', '').replace('_', '.')}')"
            )
            print()

    if orphaned_m2o:
        print(
            f"\n⚠️  POTENTIAL ORPHANED MANY2ONE FIELDS ({len(orphaned_m2o)}):"
        )
        for orphan in orphaned_m2o[:10]:  # Show first 10
            print(
                f"  🔗 {orphan['file']} -> {orphan['field']} -> {orphan['target_model']}"
            )
        if len(orphaned_m2o) > 10:
            print(f"  ... and {len(orphaned_m2o) - 10} more")

    if issues:
        print(f"\n🚨 MODEL REFERENCE ISSUES:")
        for issue in issues:
            print(f"  {issue}")

    return len(missing_inverse) + len(issues)


if __name__ == "__main__":
    print("🔍 ODOO RELATIONSHIP VALIDATOR")
    print("=" * 40)

    issues_found = analyze_relationships()

    if issues_found > 0:
        print(
            f"\n⚠️  Found {issues_found} relationship issues that need attention!"
        )
        print("Fix these before deploying to prevent KeyError exceptions.")
        sys.exit(1)
    else:
        print(f"\n✅ All relationships look good!")
        sys.exit(0)
