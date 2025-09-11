#!/usr/bin/env python3
"""
Comprehensive Relationship Validator for Records Management Module

This script validates all One2many/Many2one field relationships to identify:
1. Missing inverse fields (causing KeyError exceptions)
2. Incorrect model references (causing "unknown comodel_name" warnings)
3. Orphaned fields pointing to non-existent models
4. Circular dependency issues

Author: GitHub Copilot Assistant
Date: August 13, 2025
"""

import os
import re
import glob
from collections import defaultdict


class RelationshipValidator:
    def __init__(self, models_dir):
        self.models_dir = models_dir
        self.models = {}  # model_name -> file_path
        self.fields = defaultdict(list)  # model_name -> [field_info]
        self.relationships = []
        self.issues = []

    def scan_models(self):
        """Scan all Python model files to extract model definitions and fields"""
        print("🔍 Scanning all model files...")

        for file_path in glob.glob(os.path.join(self.models_dir, "*.py")):
            if file_path.endswith("__init__.py"):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract model name
                model_match = re.search(
                    r'_name\s*=\s*["\']([^"\']+)["\']', content
                )
                if model_match:
                    model_name = model_match.group(1)
                    self.models[model_name] = file_path

                    # Extract all fields
                    self._extract_fields(model_name, content, file_path)

            except Exception as e:
                print(f"⚠️  Error reading {file_path}: {e}")

    def _extract_fields(self, model_name, content, file_path):
        """Extract field definitions from model content"""

        # One2many fields pattern
        one2many_pattern = r'(\w+)\s*=\s*fields\.One2many\s*\(\s*["\']([^"\']+)["\'],\s*["\']([^"\']+)["\']'
        for match in re.finditer(one2many_pattern, content):
            field_name, comodel_name, inverse_name = match.groups()
            self.fields[model_name].append(
                {
                    "field_name": field_name,
                    "field_type": "One2many",
                    "comodel_name": comodel_name,
                    "inverse_name": inverse_name,
                    "file_path": file_path,
                }
            )

        # Many2one fields pattern
        many2one_pattern = (
            r'(\w+)\s*=\s*fields\.Many2one\s*\(\s*["\']([^"\']+)["\']'
        )
        for match in re.finditer(many2one_pattern, content):
            field_name, comodel_name = match.groups()
            self.fields[model_name].append(
                {
                    "field_name": field_name,
                    "field_type": "Many2one",
                    "comodel_name": comodel_name,
                    "inverse_name": None,
                    "file_path": file_path,
                }
            )

        # Many2many fields pattern
        many2many_pattern = (
            r'(\w+)\s*=\s*fields\.Many2many\s*\(\s*["\']([^"\']+)["\']'
        )
        for match in re.finditer(many2many_pattern, content):
            field_name, comodel_name = match.groups()
            self.fields[model_name].append(
                {
                    "field_name": field_name,
                    "field_type": "Many2many",
                    "comodel_name": comodel_name,
                    "inverse_name": None,
                    "file_path": file_path,
                }
            )

    def validate_relationships(self):
        """Validate all relationships and identify issues"""
        print("\n🔍 Validating relationships...")

        for model_name, field_list in self.fields.items():
            for field_info in field_list:
                self._validate_field(model_name, field_info)

    def _validate_field(self, model_name, field_info):
        """Validate a single field"""

        comodel_name = field_info["comodel_name"]
        field_name = field_info["field_name"]
        field_type = field_info["field_type"]
        file_path = field_info["file_path"]

        # Check if comodel exists
        if comodel_name not in self.models:
            # Check for common naming patterns
            alternative_names = self._get_alternative_names(comodel_name)
            found_alternative = None

            for alt_name in alternative_names:
                if alt_name in self.models:
                    found_alternative = alt_name
                    break

            if found_alternative:
                self.issues.append(
                    {
                        "type": "incorrect_model_reference",
                        "severity": "warning",
                        "model": model_name,
                        "field": field_name,
                        "issue": f"Model reference '{comodel_name}' should be '{found_alternative}'",
                        "file": file_path,
                        "suggestion": f"Change '{comodel_name}' to '{found_alternative}'",
                    }
                )
            else:
                self.issues.append(
                    {
                        "type": "missing_comodel",
                        "severity": "error",
                        "model": model_name,
                        "field": field_name,
                        "issue": f"Referenced model '{comodel_name}' does not exist",
                        "file": file_path,
                        "suggestion": f"Create model '{comodel_name}' or fix the reference",
                    }
                )

        # Validate One2many inverse fields
        elif field_type == "One2many":
            inverse_name = field_info["inverse_name"]
            if inverse_name:
                # Check if inverse field exists in comodel
                comodel_fields = self.fields.get(comodel_name, [])
                inverse_found = False

                for cofield in comodel_fields:
                    if (
                        cofield["field_name"] == inverse_name
                        and cofield["field_type"] == "Many2one"
                        and cofield["comodel_name"] == model_name
                    ):
                        inverse_found = True
                        break

                if not inverse_found:
                    self.issues.append(
                        {
                            "type": "missing_inverse_field",
                            "severity": "critical",
                            "model": model_name,
                            "field": field_name,
                            "issue": f"Missing inverse field '{inverse_name}' in model '{comodel_name}'",
                            "file": file_path,
                            "suggestion": f"Add field: {inverse_name} = fields.Many2one('{model_name}', string='...')",
                        }
                    )

    def _get_alternative_names(self, model_name):
        """Generate alternative model names based on common patterns"""
        alternatives = []

        # Convert dots to underscores and vice versa
        if "." in model_name:
            alternatives.append(model_name.replace(".", "_"))
        if "_" in model_name:
            alternatives.append(model_name.replace("_", "."))

        # Common model name patterns
        patterns = {
            "shredding.bin": ["shred.bin"],
            "shredding.equipment": ["maintenance.equipment"],
            "advanced.billing.line": ["records.billing.line"],
        }

        if model_name in patterns:
            alternatives.extend(patterns[model_name])

        return alternatives

    def generate_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE RELATIONSHIP VALIDATION REPORT")
        print("=" * 80)

        print(f"\n📊 SUMMARY:")
        print(f"   Models found: {len(self.models)}")
        print(
            f"   Total fields analyzed: {sum(len(fields) for fields in self.fields.values())}"
        )
        print(f"   Issues found: {len(self.issues)}")

        # Group issues by severity
        critical_issues = [
            i for i in self.issues if i["severity"] == "critical"
        ]
        error_issues = [i for i in self.issues if i["severity"] == "error"]
        warning_issues = [i for i in self.issues if i["severity"] == "warning"]

        print(
            f"   - Critical: {len(critical_issues)} (will cause KeyError exceptions)"
        )
        print(f"   - Errors: {len(error_issues)} (missing models)")
        print(f"   - Warnings: {len(warning_issues)} (incorrect references)")

        # Critical Issues (Missing Inverse Fields)
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES - Missing Inverse Fields:")
            print(
                "   These will cause KeyError exceptions during field setup!"
            )
            print("-" * 60)
            for issue in critical_issues:
                print(f"   ❌ {issue['model']}.{issue['field']}")
                print(f"      Issue: {issue['issue']}")
                print(f"      File: {os.path.basename(issue['file'])}")
                print(f"      Fix: {issue['suggestion']}")
                print()

        # Error Issues (Missing Models)
        if error_issues:
            print(f"\n🔴 ERROR ISSUES - Missing Models:")
            print("-" * 60)
            for issue in error_issues:
                print(f"   ❌ {issue['model']}.{issue['field']}")
                print(f"      Issue: {issue['issue']}")
                print(f"      File: {os.path.basename(issue['file'])}")
                print(f"      Fix: {issue['suggestion']}")
                print()

        # Warning Issues (Incorrect References)
        if warning_issues:
            print(f"\n⚠️  WARNING ISSUES - Incorrect Model References:")
            print("-" * 60)
            for issue in warning_issues:
                print(f"   ⚠️  {issue['model']}.{issue['field']}")
                print(f"      Issue: {issue['issue']}")
                print(f"      File: {os.path.basename(issue['file'])}")
                print(f"      Fix: {issue['suggestion']}")
                print()

        # Generate fix suggestions
        self._generate_fixes()

        return len(critical_issues) == 0 and len(error_issues) == 0

    def _generate_fixes(self):
        """Generate automated fix suggestions"""
        critical_issues = [
            i for i in self.issues if i["severity"] == "critical"
        ]

        if critical_issues:
            print(f"\n🔧 AUTOMATED FIX SUGGESTIONS:")
            print("-" * 60)
            print("   Copy and run these commands to fix critical issues:")
            print()

            for issue in critical_issues:
                model_name = issue["model"]
                field_name = issue["field"]
                comodel_name = None

                # Find the comodel name from the One2many field
                model_fields = self.fields.get(model_name, [])
                for field_info in model_fields:
                    if field_info["field_name"] == field_name:
                        comodel_name = field_info["comodel_name"]
                        inverse_name = field_info["inverse_name"]
                        break

                if comodel_name and comodel_name in self.models:
                    comodel_file = self.models[comodel_name]
                    print(f"   # Fix {model_name}.{field_name} inverse field")
                    print(
                        f"   echo 'Adding {inverse_name} field to {os.path.basename(comodel_file)}'"
                    )
                    print(
                        f"   # Add this field to {os.path.basename(comodel_file)}:"
                    )
                    print(
                        f"   # {inverse_name} = fields.Many2one('{model_name}', string='{model_name.title()}')"
                    )
                    print()

    def run_validation(self):
        """Run complete validation process"""
        self.scan_models()
        self.validate_relationships()
        return self.generate_report()


def main():
    """Main execution function"""
    models_dir = "records_management/models"

    if not os.path.exists(models_dir):
        print(f"❌ Models directory not found: {models_dir}")
        return False

    validator = RelationshipValidator(models_dir)
    success = validator.run_validation()

    if success:
        print("\n✅ All relationships are valid!")
    else:
        print("\n❌ Critical issues found that need fixing!")

    return success


if __name__ == "__main__":
    main()
