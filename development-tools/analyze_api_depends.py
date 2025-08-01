#!/usr/bin/env python3
"""
Comprehensive API Depends Analysis for Records Management Module
Validates all @api.depends decorators to ensure dependencies are logical
"""

import os
import re
import ast
from pathlib import Path


def analyze_api_depends():
    """Analyze all @api.depends decorators in the records_management module"""

    models_dir = Path(
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )

    issues = []
    analysis_results = []

    print("🔍 COMPREHENSIVE API DEPENDS ANALYSIS")
    print("=" * 80)

    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        print(f"\n📄 Analyzing: {py_file.name}")

        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find all @api.depends decorators
        depends_pattern = r"@api\.depends\((.*?)\)"
        depends_matches = re.finditer(depends_pattern, content, re.DOTALL)

        # Find all field definitions
        field_pattern = r"(\w+)\s*=\s*fields\."
        field_matches = re.findall(field_pattern, content)

        # Find model class name
        class_pattern = r"class\s+(\w+)\(.*\):"
        class_match = re.search(class_pattern, content)
        model_class = class_match.group(1) if class_match else "Unknown"

        # Find _name attribute
        name_pattern = r'_name\s*=\s*["\']([^"\']+)["\']'
        name_match = re.search(name_pattern, content)
        model_name = name_match.group(1) if name_match else "Unknown"

        file_analysis = {
            "file": py_file.name,
            "model_class": model_class,
            "model_name": model_name,
            "fields": field_matches,
            "depends": [],
            "issues": [],
        }

        for depends_match in depends_matches:
            depends_content = depends_match.group(1)

            # Extract field names from the depends
            field_deps = []
            # Handle both quoted and unquoted dependencies
            dep_pattern = r'["\']([^"\']+)["\']'
            deps = re.findall(dep_pattern, depends_content)

            # Find the compute method this belongs to
            method_start = depends_match.end()
            method_pattern = r"def\s+(_compute_\w+)\s*\("
            method_match = re.search(
                method_pattern, content[method_start : method_start + 200]
            )
            method_name = method_match.group(1) if method_match else "Unknown"

            depends_info = {
                "dependencies": deps,
                "method": method_name,
                "raw": depends_content,
            }

            file_analysis["depends"].append(depends_info)

            # Validate dependencies
            for dep in deps:
                # Check for dotted dependencies (related fields)
                if "." in dep:
                    base_field = dep.split(".")[0]
                    if base_field not in field_matches:
                        issue = f"❌ {py_file.name}::{method_name} - Base field '{base_field}' not found for dependency '{dep}'"
                        issues.append(issue)
                        file_analysis["issues"].append(issue)
                else:
                    # Simple field dependency
                    if dep not in field_matches:
                        issue = f"❌ {py_file.name}::{method_name} - Field '{dep}' not found in model"
                        issues.append(issue)
                        file_analysis["issues"].append(issue)

        analysis_results.append(file_analysis)

    # Print summary
    print(f"\n📊 ANALYSIS SUMMARY")
    print("=" * 80)

    total_files = len(analysis_results)
    files_with_depends = len([f for f in analysis_results if f["depends"]])
    total_dependencies = sum(len(f["depends"]) for f in analysis_results)
    files_with_issues = len([f for f in analysis_results if f["issues"]])

    print(f"Total Python files analyzed: {total_files}")
    print(f"Files with @api.depends: {files_with_depends}")
    print(f"Total @api.depends decorators: {total_dependencies}")
    print(f"Files with dependency issues: {files_with_issues}")
    print(f"Total dependency issues found: {len(issues)}")

    # Print detailed issues
    if issues:
        print(f"\n🚨 DEPENDENCY ISSUES FOUND:")
        print("=" * 80)
        for issue in issues:
            print(issue)
    else:
        print(f"\n✅ NO DEPENDENCY ISSUES FOUND!")

    # Print files with complex dependencies
    print(f"\n📋 FILES WITH COMPLEX DEPENDENCIES:")
    print("=" * 80)
    for file_info in analysis_results:
        if len(file_info["depends"]) > 2:
            print(f"📄 {file_info['file']} ({file_info['model_name']})")
            for dep in file_info["depends"]:
                print(f"   - {dep['method']}: {dep['dependencies']}")

    return issues, analysis_results


if __name__ == "__main__":
    issues, results = analyze_api_depends()

    # Return exit code based on issues found
    exit(1 if issues else 0)
