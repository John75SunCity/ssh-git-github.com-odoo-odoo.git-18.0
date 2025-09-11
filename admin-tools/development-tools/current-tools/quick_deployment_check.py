#!/usr/bin/env python3
"""
QUICK DEPLOYMENT ISSUE CHECKER
Identifies the most common causes of deployment failures
"""

import os
import re
from pathlib import Path


def quick_deployment_check():
    """Quick check for common deployment issues"""

    base_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )
    models_dir = base_path / "models"

    issues = []
    warnings = []

    print("🔍 QUICK DEPLOYMENT ISSUE CHECK")
    print("=" * 60)

    # 1. Check for problematic @api.depends
    print("\n1️⃣ Checking @api.depends issues...")
    depends_issues = check_api_depends_issues(models_dir)
    issues.extend(depends_issues)

    # 2. Check for Many2one target issues
    print("2️⃣ Checking Many2one targets...")
    many2one_issues = check_many2one_simple(models_dir)
    issues.extend(many2one_issues)

    # 3. Check for required compute field issues
    print("3️⃣ Checking required compute fields...")
    required_issues = check_required_compute(models_dir)
    issues.extend(required_issues)

    # 4. Check for missing compute methods
    print("4️⃣ Checking missing compute methods...")
    compute_issues = check_missing_compute_methods(models_dir)
    issues.extend(compute_issues)

    # 5. Check for model inheritance problems
    print("5️⃣ Checking model inheritance...")
    inheritance_issues = check_inheritance_problems(models_dir)
    issues.extend(inheritance_issues)

    # 6. Check for selection fields with empty lists
    print("6️⃣ Checking selection fields...")
    selection_issues = check_empty_selections(models_dir)
    warnings.extend(selection_issues)

    # Summary
    print(f"\n📊 QUICK ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"🚨 Critical Issues: {len(issues)}")
    print(f"⚠️  Warnings: {len(warnings)}")

    if issues:
        print(f"\n🚨 CRITICAL ISSUES TO FIX:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")

    if warnings:
        print(f"\n⚠️  WARNINGS:")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")

    if not issues:
        print(f"\n🎉 NO CRITICAL ISSUES FOUND!")

        # Estimate remaining errors based on patterns
        print(f"\n🔮 DEPLOYMENT PREDICTION:")
        if len(warnings) == 0:
            print("   📈 High confidence: 0-2 more errors expected")
        elif len(warnings) <= 3:
            print("   📊 Medium confidence: 1-3 more errors expected")
        else:
            print("   📉 Lower confidence: 2-5 more errors expected")

        print("   🎯 Most likely remaining issues:")
        print("      - View field references")
        print("      - Access rights missing")
        print("      - Data file syntax errors")
        print("      - External module dependencies")

    return issues, warnings


def check_api_depends_issues(models_dir):
    """Check for @api.depends problems"""
    issues = []

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Get all field names in this file
        field_names = set(re.findall(r"(\w+)\s*=\s*fields\.", content))

        # Check @api.depends for non-existent fields
        depends_pattern = r"@api\.depends\((.*?)\)"
        for match in re.finditer(depends_pattern, content, re.DOTALL):
            deps_str = match.group(1)
            deps = re.findall(r'["\']([^"\']+)["\']', deps_str)

            for dep in deps:
                # Skip dotted dependencies (related fields)
                if "." not in dep:
                    if dep not in field_names:
                        issues.append(
                            f"❌ {py_file.name}: @api.depends references unknown field '{dep}'"
                        )

    return issues


def check_many2one_simple(models_dir):
    """Simple check for Many2one target issues"""
    issues = []

    # Common problematic targets
    problematic_targets = ["non.existent.model", "missing.model", "undefined.model"]

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        many2one_pattern = r'fields\.Many2one\s*\(\s*["\']([^"\']+)["\']'
        for match in re.finditer(many2one_pattern, content):
            target = match.group(1)
            if target in problematic_targets:
                issues.append(
                    f"❌ {py_file.name}: Many2one target '{target}' is problematic"
                )

    return issues


def check_required_compute(models_dir):
    """Check for required compute fields (problematic)"""
    issues = []

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for fields that are both required and computed
        lines = content.split("\n")
        current_field = None

        for i, line in enumerate(lines):
            # Start of field definition
            field_match = re.match(r"\s*(\w+)\s*=\s*fields\.", line)
            if field_match:
                current_field = field_match.group(1)
                field_def = line

                # Collect multi-line field definition
                j = i + 1
                while j < len(lines) and not lines[j].strip().endswith(")"):
                    field_def += lines[j]
                    j += 1
                if j < len(lines):
                    field_def += lines[j]

                # Check if both required and compute
                if "required=True" in field_def and "compute=" in field_def:
                    issues.append(
                        f"❌ {py_file.name}: Field '{current_field}' is both required and computed"
                    )

    return issues


def check_missing_compute_methods(models_dir):
    """Check for compute fields without methods"""
    issues = []

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find compute field definitions
        compute_pattern = r'compute\s*=\s*["\'](_compute_\w+)["\']'
        compute_methods = set(re.findall(compute_pattern, content))

        # Find actual method definitions
        method_pattern = r"def\s+(_compute_\w+)\s*\("
        defined_methods = set(re.findall(method_pattern, content))

        # Check for missing methods
        for method in compute_methods:
            if method not in defined_methods:
                issues.append(
                    f"❌ {py_file.name}: Compute method '{method}' is referenced but not defined"
                )

    return issues


def check_inheritance_problems(models_dir):
    """Check for model inheritance problems"""
    issues = []

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for problematic inheritance patterns
        name_match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', content)
        inherit_match = re.search(r'_inherit\s*=\s*["\']([^"\']+)["\']', content)

        if name_match and inherit_match:
            name_model = name_match.group(1)
            inherit_model = inherit_match.group(1)

            # Check for core model redefinition
            core_models = [
                "res.partner",
                "res.config.settings",
                "hr.employee",
                "pos.config",
            ]
            if inherit_model in core_models and name_model == inherit_model:
                issues.append(
                    f"❌ {py_file.name}: Redefining core model '{inherit_model}' - should only have _inherit"
                )

    return issues


def check_empty_selections(models_dir):
    """Check for selection fields with empty lists"""
    warnings = []

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for Selection fields with empty lists
        empty_selection_pattern = r"(\w+)\s*=\s*fields\.Selection\s*\(\s*\[\s*\]"
        for match in re.finditer(empty_selection_pattern, content):
            field_name = match.group(1)
            warnings.append(
                f"⚠️ {py_file.name}: Selection field '{field_name}' has empty selection list"
            )

    return warnings


if __name__ == "__main__":
    issues, warnings = quick_deployment_check()
    exit(1 if issues else 0)
