#!/usr/bin/env python3
"""
COMPREHENSIVE DEEP ANALYSIS FOR RECORDS MANAGEMENT MODULE
Identifies potential deployment issues before they occur
"""

import os
import re
import ast
from pathlib import Path
from collections import defaultdict


def deep_deployment_analysis():
    """Comprehensive analysis of potential deployment issues"""

    base_path = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )
    models_dir = base_path / "models"
    views_dir = base_path / "views"
    security_dir = base_path / "security"

    issues = []
    warnings = []

    print("🔍 DEEP DEPLOYMENT ANALYSIS")
    print("=" * 80)

    # 1. Check for circular dependencies in @api.depends
    print("\n1️⃣ CHECKING FOR CIRCULAR DEPENDENCIES...")
    circular_deps = check_circular_dependencies(models_dir)
    if circular_deps:
        issues.extend(circular_deps)
    else:
        print("✅ No circular dependencies found")

    # 2. Check for missing Many2one targets
    print("\n2️⃣ CHECKING MANY2ONE TARGETS...")
    many2one_issues = check_many2one_targets(models_dir)
    if many2one_issues:
        issues.extend(many2one_issues)
    else:
        print("✅ All Many2one targets exist")

    # 3. Check for One2many inverse field issues
    print("\n3️⃣ CHECKING ONE2MANY INVERSE FIELDS...")
    one2many_issues = check_one2many_inverse_fields(models_dir)
    if one2many_issues:
        issues.extend(one2many_issues)
    else:
        print("✅ All One2many inverse fields correct")

    # 4. Check for missing access rights
    print("\n4️⃣ CHECKING ACCESS RIGHTS...")
    access_issues = check_access_rights(models_dir, security_dir)
    if access_issues:
        issues.extend(access_issues)
    else:
        print("✅ All models have access rights")

    # 5. Check for invalid field references in views
    print("\n5️⃣ CHECKING VIEW FIELD REFERENCES...")
    view_issues = check_view_field_references(models_dir, views_dir)
    if view_issues:
        issues.extend(view_issues)
    else:
        print("✅ All view field references valid")

    # 6. Check for SQL constraints conflicts
    print("\n6️⃣ CHECKING SQL CONSTRAINTS...")
    sql_issues = check_sql_constraints(models_dir)
    if sql_issues:
        issues.extend(sql_issues)
    else:
        print("✅ No SQL constraint conflicts")

    # 7. Check for selection field values
    print("\n7️⃣ CHECKING SELECTION FIELD VALUES...")
    selection_issues = check_selection_fields(models_dir)
    if selection_issues:
        warnings.extend(selection_issues)
    else:
        print("✅ All selection fields have values")

    # 8. Check for required field conflicts
    print("\n8️⃣ CHECKING REQUIRED FIELD CONFLICTS...")
    required_issues = check_required_fields(models_dir)
    if required_issues:
        issues.extend(required_issues)
    else:
        print("✅ No required field conflicts")

    # 9. Check for compute method store conflicts
    print("\n9️⃣ CHECKING COMPUTE FIELD STORE CONFLICTS...")
    store_issues = check_compute_store_conflicts(models_dir)
    if store_issues:
        issues.extend(store_issues)
    else:
        print("✅ No compute store conflicts")

    # 10. Check for model inheritance issues
    print("\n🔟 CHECKING MODEL INHERITANCE...")
    inheritance_issues = check_model_inheritance(models_dir)
    if inheritance_issues:
        issues.extend(inheritance_issues)
    else:
        print("✅ Model inheritance is correct")

    # Summary
    print(f"\n📊 DEEP ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"🚨 Critical Issues Found: {len(issues)}")
    print(f"⚠️  Warnings Found: {len(warnings)}")

    if issues:
        print(f"\n🚨 CRITICAL ISSUES TO FIX:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")

    if warnings:
        print(f"\n⚠️  WARNINGS (potential future issues):")
        for i, warning in enumerate(warnings, 1):
            print(f"{i}. {warning}")

    if not issues and not warnings:
        print(f"\n🎉 NO CRITICAL ISSUES FOUND!")
        print("Module appears ready for deployment")

    return issues, warnings


def check_circular_dependencies(models_dir):
    """Check for circular dependencies in compute fields"""
    issues = []

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find compute fields and their dependencies
        compute_pattern = (
            r'(\w+)\s*=\s*fields\.\w+\([^)]*compute=["\'](_compute_\w+)["\'][^)]*\)'
        )
        depends_pattern = r"@api\.depends\((.*?)\)\s*def\s+(_compute_\w+)"

        compute_fields = {}
        field_deps = {}

        # Map compute methods to field names
        for match in re.finditer(compute_pattern, content):
            field_name = match.group(1)
            method_name = match.group(2)
            compute_fields[method_name] = field_name

        # Map dependencies to compute methods
        for match in re.finditer(depends_pattern, content, re.DOTALL):
            deps_str = match.group(1)
            method_name = match.group(2)

            deps = re.findall(r'["\']([^"\']+)["\']', deps_str)
            field_deps[method_name] = deps

        # Check for circular dependencies
        for method, deps in field_deps.items():
            if method in compute_fields:
                field_name = compute_fields[method]
                if field_name in deps:
                    issues.append(
                        f"❌ {py_file.name}: Circular dependency - field '{field_name}' depends on itself in method '{method}'"
                    )

    return issues


def check_many2one_targets(models_dir):
    """Check if all Many2one field targets exist"""
    issues = []

    # Get all model names
    model_names = set()
    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
        name_match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', content)
        if name_match:
            model_names.add(name_match.group(1))

    # Add common Odoo core models
    core_models = {
        "res.company",
        "res.users",
        "res.partner",
        "mail.thread",
        "mail.activity.mixin",
        "ir.ui.view",
        "ir.model",
        "ir.actions.report",
        "product.product",
        "account.move",
        "project.task",
        "fsm.task",
        "pos.config",
        "hr.employee",
        "stock.lot",
        "stock.picking",
        "survey.user_input",
        "survey.survey",
        "mail.message",
        "mail.activity",
        "mail.followers",
    }
    model_names.update(core_models)

    # Check Many2one targets
    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        many2one_pattern = r'fields\.Many2one\s*\(\s*["\']([^"\']+)["\']'
        for match in re.finditer(many2one_pattern, content):
            target_model = match.group(1)
            if target_model not in model_names:
                issues.append(
                    f"❌ {py_file.name}: Many2one target '{target_model}' not found"
                )

    return issues


def check_one2many_inverse_fields(models_dir):
    """Check One2many inverse field existence"""
    issues = []

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find One2many fields with inverse
        one2many_pattern = (
            r'fields\.One2many\s*\(\s*["\']([^"\']+)["\'][^)]*["\']([^"\']+)["\']'
        )
        for match in re.finditer(one2many_pattern, content):
            target_model = match.group(1)
            inverse_field = match.group(2)

            # Check if target model file exists and has the inverse field
            target_file = None
            for model_file in models_dir.glob("*.py"):
                if model_file.name == "__init__.py":
                    continue
                with open(model_file, "r", encoding="utf-8") as f:
                    model_content = f.read()
                name_match = re.search(
                    r'_name\s*=\s*["\']([^"\']+)["\']', model_content
                )
                if name_match and name_match.group(1) == target_model:
                    target_file = model_file
                    break

            if target_file:
                with open(target_file, "r", encoding="utf-8") as f:
                    target_content = f.read()
                inverse_pattern = rf"{inverse_field}\s*=\s*fields\."
                if not re.search(inverse_pattern, target_content):
                    issues.append(
                        f"❌ {py_file.name}: One2many inverse field '{inverse_field}' not found in {target_model}"
                    )

    return issues


def check_access_rights(models_dir, security_dir):
    """Check if all models have access rights defined"""
    issues = []

    # Get all model names
    model_names = set()
    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
        name_match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', content)
        if name_match:
            model_names.add(name_match.group(1))

    # Get models with access rights
    models_with_access = set()
    access_file = security_dir / "ir.model.access.csv"
    if access_file.exists():
        with open(access_file, "r", encoding="utf-8") as f:
            for line in f:
                if "," in line and not line.startswith("id"):
                    parts = line.split(",")
                    if len(parts) >= 3:
                        model_ref = parts[2].strip().strip('"')
                        # Convert model reference to model name
                        model_name = model_ref.replace("model_", "").replace("_", ".")
                        models_with_access.add(model_name)

    # Check for missing access rights
    for model in model_names:
        if model not in models_with_access:
            # Skip some system models that might not need explicit access
            if not any(skip in model for skip in ["base.", "ir.", "mail."]):
                issues.append(f"❌ Missing access rights for model: {model}")

    return issues


def check_view_field_references(models_dir, views_dir):
    """Check if view field references exist in models"""
    issues = []

    # Get all fields for each model
    model_fields = {}
    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        name_match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', content)
        if name_match:
            model_name = name_match.group(1)
            fields = re.findall(r"(\w+)\s*=\s*fields\.", content)
            model_fields[model_name] = set(fields)

    # Check view field references
    for view_file in views_dir.glob("*.xml"):
        with open(view_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find model references in views
        model_matches = re.findall(r'model=["\']([^"\']+)["\']', content)
        for model_name in model_matches:
            if model_name in model_fields:
                # Find field references in this view
                field_matches = re.findall(r'field=["\']([^"\']+)["\']', content)
                for field_name in field_matches:
                    # Skip dotted field references (related fields)
                    if (
                        "." not in field_name
                        and field_name not in model_fields[model_name]
                    ):
                        # Skip some common Odoo fields
                        common_fields = {
                            "id",
                            "create_date",
                            "write_date",
                            "create_uid",
                            "write_uid",
                            "__last_update",
                        }
                        if field_name not in common_fields:
                            issues.append(
                                f"❌ {view_file.name}: Field '{field_name}' not found in model '{model_name}'"
                            )

    return issues


def check_sql_constraints(models_dir):
    """Check for potential SQL constraint conflicts"""
    issues = []
    constraints = defaultdict(list)

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        name_match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', content)
        if name_match:
            model_name = name_match.group(1)

            # Find _sql_constraints
            constraint_pattern = r"_sql_constraints\s*=\s*\[(.*?)\]"
            constraint_match = re.search(constraint_pattern, content, re.DOTALL)
            if constraint_match:
                constraint_content = constraint_match.group(1)
                # Extract constraint names
                constraint_names = re.findall(
                    r'\(\s*["\']([^"\']+)["\']', constraint_content
                )
                for constraint_name in constraint_names:
                    constraints[constraint_name].append(model_name)

    # Check for duplicate constraint names
    for constraint_name, models in constraints.items():
        if len(models) > 1:
            issues.append(
                f"❌ Duplicate SQL constraint name '{constraint_name}' in models: {', '.join(models)}"
            )

    return issues


def check_selection_fields(models_dir):
    """Check for selection fields with empty values"""
    warnings = []

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find Selection fields with empty lists
        selection_pattern = r"(\w+)\s*=\s*fields\.Selection\s*\(\s*\[\s*\]"
        for match in re.finditer(selection_pattern, content):
            field_name = match.group(1)
            warnings.append(
                f"⚠️ {py_file.name}: Selection field '{field_name}' has empty selection list"
            )

    return warnings


def check_required_fields(models_dir):
    """Check for required field conflicts"""
    issues = []

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find required compute fields (potential issue)
        required_compute_pattern = (
            r"(\w+)\s*=\s*fields\.\w+\([^)]*required\s*=\s*True[^)]*compute\s*="
        )
        for match in re.finditer(required_compute_pattern, content):
            field_name = match.group(1)
            issues.append(
                f"❌ {py_file.name}: Field '{field_name}' is both required and computed (can cause issues)"
            )

    return issues


def check_compute_store_conflicts(models_dir):
    """Check for compute fields with store=True but missing dependencies"""
    issues = []

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find stored compute fields
        stored_compute_pattern = r'(\w+)\s*=\s*fields\.\w+\([^)]*compute\s*=\s*["\'](_compute_\w+)["\'][^)]*store\s*=\s*True'
        compute_depends = {}

        # Find @api.depends for compute methods
        depends_pattern = r"@api\.depends\([^)]*\)\s*def\s+(_compute_\w+)"
        depends_methods = set(re.findall(depends_pattern, content))

        for match in re.finditer(stored_compute_pattern, content):
            field_name = match.group(1)
            method_name = match.group(2)

            if method_name not in depends_methods:
                issues.append(
                    f"❌ {py_file.name}: Stored compute field '{field_name}' method '{method_name}' missing @api.depends"
                )

    return issues


def check_model_inheritance(models_dir):
    """Check for model inheritance issues"""
    issues = []

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for models with both _name and _inherit (should be one or the other for extensions)
        name_pattern = r'_name\s*=\s*["\']([^"\']+)["\']'
        inherit_pattern = r'_inherit\s*=\s*["\']([^"\']+)["\']'

        name_match = re.search(name_pattern, content)
        inherit_match = re.search(inherit_pattern, content)

        if name_match and inherit_match:
            name_model = name_match.group(1)
            inherit_model = inherit_match.group(1)

            # Check if it's trying to inherit from itself or a core model it's redefining
            if name_model == inherit_model:
                issues.append(
                    f"❌ {py_file.name}: Model '{name_model}' cannot inherit from itself"
                )
            elif inherit_model in [
                "res.partner",
                "res.config.settings",
                "hr.employee",
                "pos.config",
            ]:
                # This is an extension - should only have _inherit, not _name
                issues.append(
                    f"❌ {py_file.name}: Extension of core model '{inherit_model}' should only have _inherit, not _name"
                )

    return issues


if __name__ == "__main__":
    issues, warnings = deep_deployment_analysis()

    # Return exit code based on issues
    exit(1 if issues else 0)
