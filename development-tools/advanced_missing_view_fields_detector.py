#!/usr/bin/env python3
"""
Advanced Missing View Fields Detector for Records Management Module

This script performs comprehensive analysis to find:
1. Model fields that are missing from view files
2. View field references that don't exist in models
3. Critical UI accessibility gaps for business functionality
4. Recommendations for required vs optional field exposure

Enhanced for Odoo 18.0 and Records Management enterprise patterns.
Author: GitHub Copilot Assistant
Date: August 13, 2025
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
import ast
import json
from pathlib import Path


class MissingViewFieldsDetector:
    def __init__(self, records_management_path):
        self.rm_path = records_management_path
        self.models_dir = os.path.join(records_management_path, "models")
        self.views_dir = os.path.join(records_management_path, "views")

        # Data structures
        self.model_fields = defaultdict(
            dict
        )  # model_name -> {field_name: field_info}
        self.view_fields = defaultdict(set)  # model_name -> set(field_names)
        self.missing_in_views = defaultdict(
            set
        )  # model_name -> missing fields
        self.invalid_view_fields = defaultdict(
            set
        )  # model_name -> invalid references

        # Business critical field patterns
        self.critical_patterns = [
            "name",
            "active",
            "state",
            "company_id",
            "user_id",
            "partner_id",
            "date",
            "description",
            "notes",
            "create_date",
            "write_date",
            "create_uid",
            "write_uid",
        ]

        # UI field categories
        self.ui_categories = {
            "identification": ["name", "code", "reference", "barcode"],
            "relationships": [
                "partner_id",
                "company_id",
                "user_id",
                "location_id",
            ],
            "status": ["state", "active", "priority", "stage_id"],
            "dates": ["date", "start_date", "end_date", "deadline"],
            "financial": ["amount", "cost", "price", "total", "currency_id"],
            "tracking": ["sequence", "progress", "completion", "status"],
            "audit": ["create_date", "write_date", "create_uid", "write_uid"],
        }

    def scan_model_files(self):
        """Extract all model definitions and their fields"""
        print("🔍 Scanning model files...")

        for filename in os.listdir(self.models_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                filepath = os.path.join(self.models_dir, filename)
                self._extract_model_info(filepath, filename)

        print(f"📊 Found {len(self.model_fields)} models with fields")

    def _extract_model_info(self, filepath, filename):
        """Extract model name and field definitions from Python file"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract model name using regex (more reliable than AST for complex files)
            model_match = re.search(
                r'_name\s*=\s*["\']([^"\']+)["\']', content
            )
            if not model_match:
                return

            model_name = model_match.group(1)

            # Extract field definitions
            field_pattern = r"(\w+)\s*=\s*fields\.(\w+)\s*\("
            field_matches = re.finditer(field_pattern, content)

            for match in field_matches:
                field_name = match.group(1)
                field_type = match.group(2)

                # Skip special attributes that aren't user fields
                if field_name.startswith("_") or field_name in [
                    "env",
                    "cr",
                    "uid",
                    "context",
                ]:
                    continue

                # Extract field parameters for analysis
                field_info = self._analyze_field_definition(
                    content, match.start(), field_name, field_type
                )
                self.model_fields[model_name][field_name] = field_info

            print(
                f"✅ {model_name}: {len(self.model_fields[model_name])} fields ({filename})"
            )

        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")

    def _analyze_field_definition(
        self, content, start_pos, field_name, field_type
    ):
        """Analyze field definition to extract metadata"""
        # Find the complete field definition
        field_def_match = re.search(
            rf"{field_name}\s*=\s*fields\.{field_type}\s*\([^)]*(?:\([^)]*\)[^)]*)*\)",
            content[start_pos : start_pos + 500],
        )

        if not field_def_match:
            return {"type": field_type, "required": False, "readonly": False}

        field_def = field_def_match.group(0)

        return {
            "type": field_type,
            "required": "required=True" in field_def,
            "readonly": "readonly=True" in field_def,
            "string": self._extract_string_value(field_def),
            "help": self._extract_help_value(field_def),
            "tracking": "tracking=True" in field_def,
            "compute": "compute=" in field_def,
            "store": "store=True" in field_def,
            "related": "related=" in field_def,
        }

    def _extract_string_value(self, field_def):
        """Extract string parameter from field definition"""
        string_match = re.search(
            r'string\s*=\s*["\']([^"\']+)["\']', field_def
        )
        return string_match.group(1) if string_match else None

    def _extract_help_value(self, field_def):
        """Extract help parameter from field definition"""
        help_match = re.search(r'help\s*=\s*["\']([^"\']+)["\']', field_def)
        return help_match.group(1) if help_match else None

    def scan_view_files(self):
        """Extract all field references from XML view files"""
        print("\n🔍 Scanning view files...")

        for filename in os.listdir(self.views_dir):
            if filename.endswith(".xml"):
                filepath = os.path.join(self.views_dir, filename)
                self._extract_view_fields(filepath, filename)

        print(f"📊 Found field references in {len(self.view_fields)} models")

    def _extract_view_fields(self, filepath, filename):
        """Extract field references from XML view file"""
        try:
            # Read file content and fix common XML issues
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Skip files with malformed XML patterns
            if 'ref=""' in content or "expr=\"//field[@name='']\"" in content:
                print(f"⚠️ Skipping malformed XML: {filename}")
                return

            tree = ET.parse(filepath)
            root = tree.getroot()

            current_models = set()

            # Find all record elements with model references
            for record in root.findall(".//record[@model='ir.ui.view']"):
                model_elem = record.find("field[@name='model']")
                if model_elem is not None and model_elem.text:
                    current_models.add(model_elem.text)

                # Extract field references from arch
                arch_elem = record.find("field[@name='arch']")
                if arch_elem is not None:
                    self._extract_arch_fields(arch_elem, current_models)

            if current_models:
                model_list = ", ".join(current_models)
                print(f"✅ {filename}: {model_list}")

        except ET.ParseError as e:
            print(f"⚠️ XML syntax error in {filepath}: {e}")
            # Skip this file and continue
            return
        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")
            return

    def _extract_arch_fields(self, arch_elem, current_models):
        """Extract field names from view architecture"""
        # Convert to string for regex processing (handles nested XML better)
        arch_str = ET.tostring(arch_elem, encoding="unicode")

        # Find all field references
        field_pattern = r'<field\s+name\s*=\s*["\']([^"\']+)["\']'
        field_matches = re.finditer(field_pattern, arch_str)

        for match in field_matches:
            field_name = match.group(1)

            # Add field to all current models (some views might reference multiple models)
            for model_name in current_models:
                self.view_fields[model_name].add(field_name)

    def analyze_missing_fields(self):
        """Identify missing fields and categorize them"""
        print("\n🚨 ANALYZING MISSING VIEW FIELDS...")

        total_missing = 0
        critical_missing = 0

        for model_name, model_fields in self.model_fields.items():
            view_fields = self.view_fields.get(model_name, set())

            # Find fields in model but not in views
            missing = set(model_fields.keys()) - view_fields
            self.missing_in_views[model_name] = missing

            if missing:
                total_missing += len(missing)
                print(f"\n📋 {model_name} ({len(missing)} missing fields):")

                # Categorize missing fields
                categories = self._categorize_missing_fields(
                    missing, model_fields
                )

                for category, fields in categories.items():
                    if fields:
                        print(
                            f"   🔸 {category.upper()}: {', '.join(sorted(fields))}"
                        )
                        if category in [
                            "critical",
                            "identification",
                            "status",
                        ]:
                            critical_missing += len(fields)

        # Find invalid view field references
        self._find_invalid_view_references()

        print(f"\n📊 SUMMARY:")
        print(f"   Total missing fields: {total_missing}")
        print(f"   Critical missing fields: {critical_missing}")
        print(
            f"   Models with missing fields: {len([m for m in self.missing_in_views.values() if m])}"
        )

    def _categorize_missing_fields(self, missing_fields, model_fields):
        """Categorize missing fields by business importance"""
        categories = defaultdict(set)

        for field_name in missing_fields:
            field_info = model_fields.get(field_name, {})

            # Critical business fields
            if field_name in self.critical_patterns:
                categories["critical"].add(field_name)
                continue

            # Required fields
            if field_info.get("required"):
                categories["required"].add(field_name)
                continue

            # UI category classification
            categorized = False
            for ui_category, patterns in self.ui_categories.items():
                if any(pattern in field_name.lower() for pattern in patterns):
                    categories[ui_category].add(field_name)
                    categorized = True
                    break

            # Field type classification
            if not categorized:
                field_type = field_info.get("type", "")
                if field_type in ["Many2one", "Many2many"]:
                    categories["relationships"].add(field_name)
                elif field_type in ["Boolean"]:
                    categories["flags"].add(field_name)
                elif field_type in ["Text", "Html"]:
                    categories["content"].add(field_name)
                elif field_type in ["Selection"]:
                    categories["status"].add(field_name)
                else:
                    categories["other"].add(field_name)

        return categories

    def _find_invalid_view_references(self):
        """Find view field references that don't exist in models"""
        print(f"\n🔍 CHECKING FOR INVALID VIEW FIELD REFERENCES...")

        total_invalid = 0

        for model_name, view_fields in self.view_fields.items():
            if model_name not in self.model_fields:
                print(
                    f"⚠️  Model {model_name} referenced in views but no model file found"
                )
                continue

            model_fields = set(self.model_fields[model_name].keys())
            invalid = view_fields - model_fields

            if invalid:
                self.invalid_view_fields[model_name] = invalid
                total_invalid += len(invalid)
                print(f"❌ {model_name}: {', '.join(sorted(invalid))}")

        if total_invalid == 0:
            print("✅ No invalid view field references found!")
        else:
            print(f"📊 Total invalid references: {total_invalid}")

    def generate_recommendations(self):
        """Generate actionable recommendations"""
        print(f"\n💡 RECOMMENDATIONS:")

        high_priority_models = []

        for model_name, missing in self.missing_in_views.items():
            if not missing:
                continue

            model_fields = self.model_fields[model_name]

            # High priority: models with critical missing fields
            critical_count = len(
                [f for f in missing if f in self.critical_patterns]
            )
            required_count = len(
                [f for f in missing if model_fields.get(f, {}).get("required")]
            )

            if critical_count > 0 or required_count > 2:
                high_priority_models.append(
                    (model_name, critical_count, required_count, len(missing))
                )

        if high_priority_models:
            print(
                f"\n🚨 HIGH PRIORITY MODELS (Critical/Required fields missing):"
            )
            high_priority_models.sort(
                key=lambda x: (x[1], x[2], x[3]), reverse=True
            )

            for model_name, critical, required, total in high_priority_models[
                :10
            ]:
                print(
                    f"   🔥 {model_name}: {critical} critical, {required} required, {total} total missing"
                )

        print(f"\n🛠️  SUGGESTED ACTIONS:")
        print(
            f"   1. Add critical fields (name, active, state) to all model views"
        )
        print(f"   2. Ensure required fields are accessible in form views")
        print(f"   3. Add relationship fields for proper navigation")
        print(
            f"   4. Include audit fields (create_date, write_date) in list views"
        )
        print(f"   5. Add search fields to search views for better UX")

    def generate_detailed_report(self):
        """Generate detailed JSON report for further analysis"""
        report = {
            "timestamp": "2025-08-13",
            "summary": {
                "models_analyzed": len(self.model_fields),
                "total_missing_fields": sum(
                    len(fields) for fields in self.missing_in_views.values()
                ),
                "models_with_missing_fields": len(
                    [m for m in self.missing_in_views.values() if m]
                ),
                "invalid_view_references": sum(
                    len(fields) for fields in self.invalid_view_fields.values()
                ),
            },
            "missing_fields": {
                model: list(fields)
                for model, fields in self.missing_in_views.items()
                if fields
            },
            "invalid_references": {
                model: list(fields)
                for model, fields in self.invalid_view_fields.items()
                if fields
            },
            "model_field_counts": {
                model: len(fields)
                for model, fields in self.model_fields.items()
            },
        }

        output_path = os.path.join(
            self.rm_path,
            "..",
            "development-tools",
            "missing_view_fields_report.json",
        )
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Detailed report saved to: {output_path}")
        return report

    def run_complete_analysis(self):
        """Run the complete missing view fields analysis"""
        print("🚀 ADVANCED MISSING VIEW FIELDS DETECTOR")
        print("=" * 60)

        # Step 1: Scan models and views
        self.scan_model_files()
        self.scan_view_files()

        # Step 2: Analyze gaps
        self.analyze_missing_fields()

        # Step 3: Generate recommendations
        self.generate_recommendations()

        # Step 4: Save detailed report
        report = self.generate_detailed_report()

        print(f"\n✅ ANALYSIS COMPLETE!")
        return report


def main():
    """Main execution function"""
    records_management_path = (
        "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    )

    detector = MissingViewFieldsDetector(records_management_path)
    report = detector.run_complete_analysis()

    # Quick summary
    summary = report["summary"]
    print(f"\n📈 QUICK SUMMARY:")
    print(f"   📊 Models analyzed: {summary['models_analyzed']}")
    print(f"   ❌ Missing fields: {summary['total_missing_fields']}")
    print(
        f"   🚨 Models needing attention: {summary['models_with_missing_fields']}"
    )
    print(
        f"   ⚠️  Invalid view references: {summary['invalid_view_references']}"
    )


if __name__ == "__main__":
    main()
