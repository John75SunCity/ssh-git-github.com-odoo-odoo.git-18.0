#!/usr/bin/env python3
"""
Find and analyze all computed fields in the records_management module
"""

import os
import re
import ast


def find_all_computed_fields():
    """Find all computed fields across the entire records_management module"""

    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    computed_fields = []

    print("🔍 COMPREHENSIVE COMPUTED FIELD ANALYSIS")
    print("=" * 60)

    # Search through all Python model files
    models_path = os.path.join(base_path, "models")

    for file in os.listdir(models_path):
        if file.endswith(".py") and file != "__init__.py":
            file_path = os.path.join(models_path, file)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find all field definitions with compute parameter - improved regex for multiline
                compute_pattern = r'(\w+)\s*=\s*fields\.\w+\([^)]*compute\s*=\s*[\'"]([^\'"]+)[\'"][^)]*\)'
                matches = re.findall(compute_pattern, content, re.MULTILINE | re.DOTALL)

                # Also find @api.depends decorators and their associated methods
                depends_pattern = r"@api\.depends\([^)]+\)\s*def\s+(\w+)\(self[^)]*\):"
                depends_matches = re.findall(depends_pattern, content)

                # Find @api.depends with multi-line definitions
                multiline_depends = (
                    r"@api\.depends\(\s*([^)]+)\s*\)\s*def\s+(\w+)\(self[^)]*\):"
                )
                multiline_matches = re.findall(
                    multiline_depends, content, re.MULTILINE | re.DOTALL
                )

                for field_name, compute_method in matches:
                    computed_fields.append(
                        {
                            "file": file,
                            "field_name": field_name,
                            "compute_method": compute_method,
                            "has_depends": compute_method in depends_matches
                            or any(
                                compute_method in match for match in multiline_matches
                            ),
                        }
                    )

                # Check for computed fields without proper field definition
                for method_name in depends_matches:
                    if not any(
                        cf["compute_method"] == method_name
                        for cf in computed_fields
                        if cf["file"] == file
                    ):
                        computed_fields.append(
                            {
                                "file": file,
                                "field_name": "UNKNOWN",
                                "compute_method": method_name,
                                "has_depends": True,
                                "orphaned": True,
                            }
                        )

            except Exception as e:
                print(f"Warning: Could not analyze {file}: {e}")

    return computed_fields


def analyze_compute_method_functionality(computed_fields):
    """Analyze each compute method for functionality and potential issues"""

    print(f"\n🔧 ANALYZING {len(computed_fields)} COMPUTED FIELDS")
    print("=" * 50)

    base_path = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    )

    analysis_results = []

    for field_info in computed_fields:
        file_path = os.path.join(base_path, field_info["file"])

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Find the compute method implementation
            method_pattern = rf'def\s+{re.escape(field_info["compute_method"])}\(self[^)]*\):(.*?)(?=\n\s*def|\n\s*@|\nclass|\n\s*$|\Z)'
            method_match = re.search(method_pattern, content, re.DOTALL)

            analysis = {
                "file": field_info["file"],
                "field_name": field_info["field_name"],
                "compute_method": field_info["compute_method"],
                "has_depends": field_info.get("has_depends", False),
                "has_implementation": method_match is not None,
                "implementation_length": (
                    len(method_match.group(1).strip()) if method_match else 0
                ),
                "has_for_loop": False,
                "assigns_field": False,
                "has_error_handling": False,
                "orphaned": field_info.get("orphaned", False),
            }

            if method_match:
                method_code = method_match.group(1)

                # Analyze implementation quality
                analysis["has_for_loop"] = (
                    "for record in self:" in method_code
                    or "for r in self:" in method_code
                    or "for line in self:" in method_code
                    or "for wizard in self:" in method_code
                )
                analysis["assigns_field"] = (
                    f"record.{field_info['field_name']}" in method_code
                    or f"self.{field_info['field_name']}" in method_code
                    or f"line.{field_info['field_name']}" in method_code
                    or f"wizard.{field_info['field_name']}" in method_code
                )
                analysis["has_error_handling"] = (
                    "try:" in method_code or "except" in method_code
                )

                # Check for common issues
                issues = []
                if not analysis["has_for_loop"]:
                    issues.append("Missing 'for record in self:' loop")
                if not analysis["assigns_field"] and not analysis["orphaned"]:
                    issues.append(
                        f"Doesn't assign to field '{field_info['field_name']}'"
                    )
                if not analysis["has_depends"]:
                    issues.append("Missing @api.depends decorator")

                analysis["issues"] = issues

            analysis_results.append(analysis)

        except Exception as e:
            analysis_results.append(
                {
                    "file": field_info["file"],
                    "field_name": field_info["field_name"],
                    "compute_method": field_info["compute_method"],
                    "error": str(e),
                }
            )

    return analysis_results


def display_comprehensive_results(computed_fields, analysis_results):
    """Display comprehensive results of computed field analysis"""

    print(f"\n📊 COMPREHENSIVE COMPUTED FIELD REPORT")
    print("=" * 60)

    print(f"\n📋 SUMMARY STATISTICS:")
    print(f"  • Total computed fields found: {len(computed_fields)}")

    functional_fields = [
        a
        for a in analysis_results
        if a.get("has_implementation") and not a.get("issues", [])
    ]
    problematic_fields = [a for a in analysis_results if a.get("issues", [])]
    orphaned_fields = [a for a in analysis_results if a.get("orphaned")]

    print(f"  • Functional computed fields: {len(functional_fields)}")
    print(f"  • Problematic computed fields: {len(problematic_fields)}")
    print(f"  • Orphaned compute methods: {len(orphaned_fields)}")

    print(f"\n✅ FUNCTIONAL COMPUTED FIELDS ({len(functional_fields)}):")
    for field in functional_fields:
        print(
            f"  • {field['file']}::{field['field_name']} -> {field['compute_method']}()"
        )

    if problematic_fields:
        print(f"\n⚠️  PROBLEMATIC COMPUTED FIELDS ({len(problematic_fields)}):")
        for field in problematic_fields:
            issues_str = ", ".join(field.get("issues", []))
            print(
                f"  • {field['file']}::{field['field_name']} -> {field['compute_method']}() - ISSUES: {issues_str}"
            )

    if orphaned_fields:
        print(f"\n🔍 ORPHANED COMPUTE METHODS ({len(orphaned_fields)}):")
        for field in orphaned_fields:
            print(
                f"  • {field['file']}::{field['compute_method']}() - No corresponding field definition found"
            )

    print(f"\n📋 DETAILED FIELD LIST:")
    for field in analysis_results:
        status = (
            "✅" if not field.get("issues") and field.get("has_implementation") else "⚠️"
        )
        depends = "✓" if field.get("has_depends") else "✗"
        impl = "✓" if field.get("has_implementation") else "✗"

        print(
            f"  {status} {field['file']}::{field['field_name']} -> {field['compute_method']}() [Depends:{depends}, Impl:{impl}]"
        )


if __name__ == "__main__":
    # Find all computed fields
    computed_fields = find_all_computed_fields()

    if computed_fields:
        # Analyze functionality
        analysis_results = analyze_compute_method_functionality(computed_fields)

        # Display comprehensive results
        display_comprehensive_results(computed_fields, analysis_results)

        print(f"\n🎉 ANALYSIS COMPLETE")
        print("✅ All computed fields have been analyzed for functionality")
    else:
        print("\n❌ No computed fields found to analyze")
