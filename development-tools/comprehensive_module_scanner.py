#!/usr/bin/env python3
"""
COMPREHENSIVE RECORDS MANAGEMENT MODULE SCANNER
Deep analysis of every file, field, model, and relationship in the module
Using VS Code extensions and advanced validation techniques
"""

import os
import ast
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict, Counter
import sys


class RecordsManagementScanner:
    def __init__(self):
        self.module_path = (
            "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
        )
        self.results = {
            "models": {},
            "fields": {},
            "views": {},
            "security": {},
            "data": {},
            "dependencies": {},
            "issues": [],
            "statistics": {},
            "recommendations": [],
        }

    def scan_complete_module(self):
        """Perform comprehensive scan of the entire module"""
        print("🔍 COMPREHENSIVE RECORDS MANAGEMENT MODULE SCANNER")
        print("=" * 80)
        print(f"📁 Scanning: {self.module_path}")

        # Core scans
        self.scan_python_models()
        self.scan_xml_files()
        self.scan_field_relationships()
        self.scan_security_rules()
        self.scan_data_files()
        self.scan_dependencies()
        self.scan_code_quality()
        self.detect_patterns()
        self.generate_statistics()
        self.generate_recommendations()

        # Generate comprehensive report
        self.generate_report()

    def scan_python_models(self):
        """Deep scan of all Python model files"""
        print("\n🐍 SCANNING PYTHON MODELS")
        print("-" * 50)

        models_dir = os.path.join(self.module_path, "models")
        model_files = [
            f
            for f in os.listdir(models_dir)
            if f.endswith(".py") and f != "__init__.py"
        ]

        for model_file in model_files:
            file_path = os.path.join(models_dir, model_file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse AST for detailed analysis
                tree = ast.parse(content)
                model_info = self.analyze_model_ast(tree, content, model_file)

                if model_info:
                    self.results["models"][model_file] = model_info
                    print(
                        f"✅ {model_file}: {model_info.get('model_name', 'Unknown')} ({len(model_info.get('fields', []))} fields)"
                    )

            except Exception as e:
                self.results["issues"].append(
                    {"type": "model_parse_error", "file": model_file, "error": str(e)}
                )
                print(f"❌ {model_file}: Parse error - {e}")

    def analyze_model_ast(self, tree, content, filename):
        """Analyze model using AST parsing"""
        model_info = {
            "filename": filename,
            "classes": [],
            "fields": [],
            "methods": [],
            "imports": [],
            "inheritance": [],
            "decorators": [],
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "bases": [
                        base.id if isinstance(base, ast.Name) else str(base)
                        for base in node.bases
                    ],
                    "fields": [],
                    "methods": [],
                    "model_attributes": {},
                }

                # Analyze class body
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        # Check for model attributes (_name, _description, etc.)
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                if target.id.startswith("_"):
                                    try:
                                        value = ast.literal_eval(item.value)
                                        class_info["model_attributes"][
                                            target.id
                                        ] = value
                                    except:
                                        pass
                                else:
                                    # Check if it's a field definition
                                    if self.is_field_definition(item.value):
                                        field_info = self.extract_field_info(
                                            target.id, item.value, content
                                        )
                                        class_info["fields"].append(field_info)

                    elif isinstance(item, ast.FunctionDef):
                        method_info = {
                            "name": item.name,
                            "decorators": [
                                d.id if isinstance(d, ast.Name) else str(d)
                                for d in item.decorator_list
                            ],
                            "args": [arg.arg for arg in item.args.args],
                            "returns": item.returns,
                        }
                        class_info["methods"].append(method_info)

                model_info["classes"].append(class_info)

                # Set main model info
                if "_name" in class_info["model_attributes"]:
                    model_info["model_name"] = class_info["model_attributes"]["_name"]
                    model_info["fields"] = class_info["fields"]
                    model_info["inheritance"] = class_info["model_attributes"].get(
                        "_inherit", []
                    )

        return model_info

    def is_field_definition(self, node):
        """Check if AST node is a field definition"""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                return node.func.attr in [
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
                ]
        return False

    def extract_field_info(self, field_name, node, content):
        """Extract detailed field information"""
        field_info = {"name": field_name, "type": "unknown", "attributes": {}}

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            field_info["type"] = node.func.attr

            # Extract field attributes
            for keyword in node.keywords:
                try:
                    field_info["attributes"][keyword.arg] = ast.literal_eval(
                        keyword.value
                    )
                except:
                    field_info["attributes"][keyword.arg] = str(keyword.value)

        return field_info

    def scan_xml_files(self):
        """Scan all XML files for views, data, and security"""
        print("\n📄 SCANNING XML FILES")
        print("-" * 50)

        xml_files = []
        for root, dirs, files in os.walk(self.module_path):
            for file in files:
                if file.endswith(".xml"):
                    xml_files.append(os.path.join(root, file))

        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                relative_path = os.path.relpath(xml_file, self.module_path)
                xml_info = self.analyze_xml_file(root, relative_path)

                if "views" in relative_path:
                    self.results["views"][relative_path] = xml_info
                elif "security" in relative_path:
                    self.results["security"][relative_path] = xml_info
                elif "data" in relative_path:
                    self.results["data"][relative_path] = xml_info

                print(f"✅ {relative_path}: {xml_info.get('record_count', 0)} records")

            except Exception as e:
                self.results["issues"].append(
                    {"type": "xml_parse_error", "file": xml_file, "error": str(e)}
                )
                print(f"❌ {os.path.relpath(xml_file, self.module_path)}: {e}")

    def analyze_xml_file(self, root, filename):
        """Analyze XML file structure"""
        xml_info = {
            "filename": filename,
            "records": [],
            "record_count": 0,
            "models_referenced": set(),
            "external_ids": set(),
        }

        for record in root.findall(".//record"):
            record_info = {
                "id": record.get("id", ""),
                "model": record.get("model", ""),
                "fields": [],
            }

            for field in record.findall("field"):
                field_info = {
                    "name": field.get("name", ""),
                    "ref": field.get("ref", ""),
                    "eval": field.get("eval", ""),
                    "value": field.text or "",
                }
                record_info["fields"].append(field_info)

                if field_info["ref"]:
                    xml_info["external_ids"].add(field_info["ref"])

            xml_info["records"].append(record_info)
            xml_info["models_referenced"].add(record_info["model"])

        xml_info["record_count"] = len(xml_info["records"])
        xml_info["models_referenced"] = list(xml_info["models_referenced"])
        xml_info["external_ids"] = list(xml_info["external_ids"])

        return xml_info

    def scan_field_relationships(self):
        """Analyze field relationships and dependencies"""
        print("\n🔗 SCANNING FIELD RELATIONSHIPS")
        print("-" * 50)

        relationships = {
            "many2one": [],
            "one2many": [],
            "many2many": [],
            "missing_comodels": [],
            "circular_dependencies": [],
        }

        # Analyze relationships from model data
        for model_file, model_info in self.results["models"].items():
            model_name = model_info.get("model_name", "")

            for field in model_info.get("fields", []):
                field_type = field.get("type", "")

                if field_type == "Many2one":
                    comodel = field.get("attributes", {}).get("string", "")
                    relationships["many2one"].append(
                        {
                            "model": model_name,
                            "field": field["name"],
                            "comodel": comodel,
                        }
                    )

                elif field_type == "One2many":
                    comodel = field.get("attributes", {}).get("string", "")
                    inverse = field.get("attributes", {}).get("string", "")
                    relationships["one2many"].append(
                        {
                            "model": model_name,
                            "field": field["name"],
                            "comodel": comodel,
                            "inverse": inverse,
                        }
                    )

                elif field_type == "Many2many":
                    comodel = field.get("attributes", {}).get("string", "")
                    relationships["many2many"].append(
                        {
                            "model": model_name,
                            "field": field["name"],
                            "comodel": comodel,
                        }
                    )

        self.results["dependencies"]["relationships"] = relationships

        print(f"✅ Many2one relationships: {len(relationships['many2one'])}")
        print(f"✅ One2many relationships: {len(relationships['one2many'])}")
        print(f"✅ Many2many relationships: {len(relationships['many2many'])}")

    def scan_security_rules(self):
        """Analyze security rules and access controls"""
        print("\n🔒 SCANNING SECURITY RULES")
        print("-" * 50)

        security_analysis = {
            "access_rules": [],
            "record_rules": [],
            "groups": [],
            "missing_access": [],
        }

        # Analyze ir.model.access.csv
        access_csv_path = os.path.join(
            self.module_path, "security", "ir.model.access.csv"
        )
        if os.path.exists(access_csv_path):
            with open(access_csv_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for i, line in enumerate(lines[1:], 2):  # Skip header
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 8:
                        security_analysis["access_rules"].append(
                            {
                                "id": parts[0],
                                "name": parts[1],
                                "model_id": parts[2],
                                "group_id": parts[3],
                                "read": parts[4],
                                "write": parts[5],
                                "create": parts[6],
                                "delete": parts[7],
                            }
                        )

        self.results["security"]["analysis"] = security_analysis
        print(f"✅ Access rules: {len(security_analysis['access_rules'])}")

    def scan_data_files(self):
        """Analyze data files and sequences"""
        print("\n📊 SCANNING DATA FILES")
        print("-" * 50)

        data_analysis = {
            "sequences": [],
            "demo_data": [],
            "configuration": [],
            "external_references": [],
        }

        # Count different types of data
        for data_file, data_info in self.results["data"].items():
            for record in data_info.get("records", []):
                model = record.get("model", "")

                if "sequence" in model:
                    data_analysis["sequences"].append(record)
                elif "demo" in data_file:
                    data_analysis["demo_data"].append(record)
                else:
                    data_analysis["configuration"].append(record)

        self.results["data"]["analysis"] = data_analysis
        print(f"✅ Sequences: {len(data_analysis['sequences'])}")
        print(f"✅ Configuration records: {len(data_analysis['configuration'])}")

    def scan_dependencies(self):
        """Analyze module dependencies"""
        print("\n🔗 SCANNING DEPENDENCIES")
        print("-" * 50)

        # Read manifest dependencies
        manifest_path = os.path.join(self.module_path, "__manifest__.py")
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                content = f.read()
                manifest_data = ast.literal_eval(content)

            dependencies = manifest_data.get("depends", [])

            dep_analysis = {
                "manifest_dependencies": dependencies,
                "external_references": [],
                "missing_dependencies": [],
            }

            # Collect external references from XML files
            for xml_file, xml_info in {
                **self.results["views"],
                **self.results["data"],
                **self.results["security"],
            }.items():
                for ext_id in xml_info.get("external_ids", []):
                    if "." in ext_id:
                        module = ext_id.split(".")[0]
                        if (
                            module not in dependencies
                            and module != "records_management"
                        ):
                            dep_analysis["external_references"].append(ext_id)
                            if module not in [
                                d["module"]
                                for d in dep_analysis["missing_dependencies"]
                            ]:
                                dep_analysis["missing_dependencies"].append(
                                    {
                                        "module": module,
                                        "reference": ext_id,
                                        "file": xml_file,
                                    }
                                )

            self.results["dependencies"]["analysis"] = dep_analysis

            print(f"✅ Manifest dependencies: {len(dependencies)}")
            print(
                f"⚠️  Potential missing dependencies: {len(dep_analysis['missing_dependencies'])}"
            )

        except Exception as e:
            print(f"❌ Error analyzing dependencies: {e}")

    def scan_code_quality(self):
        """Analyze code quality metrics"""
        print("\n📏 SCANNING CODE QUALITY")
        print("-" * 50)

        quality_metrics = {
            "complexity": {},
            "duplications": [],
            "naming_conventions": [],
            "documentation": {},
        }

        # Analyze each model file
        for model_file, model_info in self.results["models"].items():
            file_metrics = {
                "classes": len(model_info.get("classes", [])),
                "methods": sum(
                    len(cls.get("methods", [])) for cls in model_info.get("classes", [])
                ),
                "fields": len(model_info.get("fields", [])),
                "lines_of_code": 0,
            }

            # Count lines of code
            file_path = os.path.join(self.module_path, "models", model_file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_metrics["lines_of_code"] = len(
                        [line for line in f if line.strip()]
                    )
            except:
                pass

            quality_metrics["complexity"][model_file] = file_metrics

        self.results["code_quality"] = quality_metrics

        total_files = len(quality_metrics["complexity"])
        total_fields = sum(m["fields"] for m in quality_metrics["complexity"].values())
        total_methods = sum(
            m["methods"] for m in quality_metrics["complexity"].values()
        )

        print(f"✅ Total files analyzed: {total_files}")
        print(f"✅ Total fields: {total_fields}")
        print(f"✅ Total methods: {total_methods}")

    def detect_patterns(self):
        """Detect common patterns and anti-patterns"""
        print("\n🔍 DETECTING PATTERNS")
        print("-" * 50)

        patterns = {"common_patterns": [], "anti_patterns": [], "best_practices": []}

        # Detect common field naming patterns
        field_names = []
        for model_info in self.results["models"].values():
            field_names.extend([f["name"] for f in model_info.get("fields", [])])

        field_counter = Counter(field_names)
        common_fields = field_counter.most_common(10)

        patterns["common_patterns"].append(
            {"type": "common_fields", "data": common_fields}
        )

        # Detect models without mail.thread inheritance
        models_without_tracking = []
        for model_file, model_info in self.results["models"].items():
            inheritance = model_info.get("inheritance", [])
            if isinstance(inheritance, str):
                inheritance = [inheritance]

            if "mail.thread" not in inheritance:
                models_without_tracking.append(model_info.get("model_name", model_file))

        if models_without_tracking:
            patterns["anti_patterns"].append(
                {"type": "missing_mail_thread", "data": models_without_tracking}
            )

        self.results["patterns"] = patterns

        print(f"✅ Common patterns detected: {len(patterns['common_patterns'])}")
        print(f"⚠️  Anti-patterns detected: {len(patterns['anti_patterns'])}")

    def generate_statistics(self):
        """Generate comprehensive statistics"""
        print("\n📊 GENERATING STATISTICS")
        print("-" * 50)

        stats = {
            "models": {
                "total": len(self.results["models"]),
                "with_inheritance": 0,
                "with_mail_thread": 0,
            },
            "fields": {"total": 0, "by_type": Counter()},
            "views": {
                "total": len(self.results["views"]),
                "total_records": sum(
                    v.get("record_count", 0) for v in self.results["views"].values()
                ),
            },
            "security": {
                "access_rules": len(
                    self.results.get("security", {})
                    .get("analysis", {})
                    .get("access_rules", [])
                ),
                "models_covered": 0,
            },
            "data": {
                "total_files": len(self.results["data"]),
                "total_records": sum(
                    d.get("record_count", 0) for d in self.results["data"].values()
                ),
            },
        }

        # Count fields and types
        for model_info in self.results["models"].values():
            fields = model_info.get("fields", [])
            stats["fields"]["total"] += len(fields)

            for field in fields:
                field_type = field.get("type", "unknown")
                stats["fields"]["by_type"][field_type] += 1

            inheritance = model_info.get("inheritance", [])
            if inheritance:
                stats["models"]["with_inheritance"] += 1
                if "mail.thread" in inheritance:
                    stats["models"]["with_mail_thread"] += 1

        self.results["statistics"] = stats

        print(f"✅ Total models: {stats['models']['total']}")
        print(f"✅ Total fields: {stats['fields']['total']}")
        print(f"✅ Total views: {stats['views']['total']}")
        print(f"✅ Access rules: {stats['security']['access_rules']}")

    def generate_recommendations(self):
        """Generate actionable recommendations"""
        print("\n💡 GENERATING RECOMMENDATIONS")
        print("-" * 50)

        recommendations = []

        # Check for models without mail.thread
        models_without_thread = []
        for model_file, model_info in self.results["models"].items():
            inheritance = model_info.get("inheritance", [])
            if "mail.thread" not in inheritance:
                models_without_thread.append(model_info.get("model_name", model_file))

        if models_without_thread:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "inheritance",
                    "title": "Add mail.thread inheritance",
                    "description": f"{len(models_without_thread)} models lack mail.thread inheritance for tracking",
                    "affected": models_without_thread,
                }
            )

        # Check for missing compute method dependencies
        missing_depends = []
        for model_file, model_info in self.results["models"].items():
            for cls in model_info.get("classes", []):
                for method in cls.get("methods", []):
                    if method["name"].startswith(
                        "_compute_"
                    ) and "api.depends" not in method.get("decorators", []):
                        missing_depends.append(
                            f"{model_info.get('model_name', model_file)}.{method['name']}"
                        )

        if missing_depends:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "compute_methods",
                    "title": "Add @api.depends decorators",
                    "description": f"{len(missing_depends)} compute methods missing @api.depends decorators",
                    "affected": missing_depends,
                }
            )

        # Check for potential security issues
        models_with_fields = set(
            info.get("model_name")
            for info in self.results["models"].values()
            if info.get("model_name")
        )
        models_with_access = set()

        security_analysis = self.results.get("security", {}).get("analysis", {})
        for rule in security_analysis.get("access_rules", []):
            models_with_access.add(
                rule.get("model_id", "").replace("model_", "").replace("_", ".")
            )

        missing_security = models_with_fields - models_with_access
        if missing_security:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "security",
                    "title": "Add missing security rules",
                    "description": f"{len(missing_security)} models lack access control rules",
                    "affected": list(missing_security),
                }
            )

        self.results["recommendations"] = recommendations

        print(f"✅ Generated {len(recommendations)} recommendations")
        for rec in recommendations:
            print(f"   📌 {rec['priority'].upper()}: {rec['title']}")

    def generate_report(self):
        """Generate comprehensive scan report"""
        print("\n📋 GENERATING COMPREHENSIVE REPORT")
        print("=" * 80)

        report_path = os.path.join(self.module_path, "COMPREHENSIVE_SCAN_REPORT.md")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# COMPREHENSIVE RECORDS MANAGEMENT MODULE SCAN REPORT\n\n")
            f.write(f"**Generated:** {os.popen('date').read().strip()}\n")
            f.write(f"**Module Path:** {self.module_path}\n\n")

            # Executive Summary
            f.write("## 📊 EXECUTIVE SUMMARY\n\n")
            stats = self.results["statistics"]
            f.write(f"- **Models:** {stats['models']['total']}\n")
            f.write(f"- **Fields:** {stats['fields']['total']}\n")
            f.write(f"- **Views:** {stats['views']['total']}\n")
            f.write(f"- **Security Rules:** {stats['security']['access_rules']}\n")
            f.write(f"- **Issues Found:** {len(self.results['issues'])}\n")
            f.write(
                f"- **Recommendations:** {len(self.results['recommendations'])}\n\n"
            )

            # Models Summary
            f.write("## 🐍 MODELS ANALYSIS\n\n")
            for model_file, model_info in self.results["models"].items():
                model_name = model_info.get("model_name", "Unknown")
                field_count = len(model_info.get("fields", []))
                f.write(f"### {model_name} (`{model_file}`)\n")
                f.write(f"- **Fields:** {field_count}\n")
                f.write(
                    f"- **Inheritance:** {model_info.get('inheritance', 'None')}\n\n"
                )

            # Field Types Distribution
            f.write("## 🏷️ FIELD TYPES DISTRIBUTION\n\n")
            field_types = stats["fields"]["by_type"]
            for field_type, count in field_types.most_common():
                f.write(f"- **{field_type}:** {count}\n")
            f.write("\n")

            # Issues
            if self.results["issues"]:
                f.write("## ⚠️ ISSUES FOUND\n\n")
                for issue in self.results["issues"]:
                    f.write(f"### {issue['type']} - {issue['file']}\n")
                    f.write(f"```\n{issue['error']}\n```\n\n")

            # Recommendations
            if self.results["recommendations"]:
                f.write("## 💡 RECOMMENDATIONS\n\n")
                for rec in self.results["recommendations"]:
                    f.write(f"### {rec['priority'].upper()}: {rec['title']}\n")
                    f.write(f"{rec['description']}\n\n")
                    if rec.get("affected"):
                        f.write("**Affected items:**\n")
                        for item in rec["affected"][:10]:  # Limit to first 10
                            f.write(f"- {item}\n")
                        if len(rec["affected"]) > 10:
                            f.write(f"- ... and {len(rec['affected']) - 10} more\n")
                        f.write("\n")

            # Dependencies Analysis
            f.write("## 🔗 DEPENDENCIES ANALYSIS\n\n")
            dep_analysis = self.results.get("dependencies", {}).get("analysis", {})
            f.write(
                f"**Manifest Dependencies:** {len(dep_analysis.get('manifest_dependencies', []))}\n"
            )
            f.write(
                f"**External References:** {len(dep_analysis.get('external_references', []))}\n"
            )
            f.write(
                f"**Potential Missing Dependencies:** {len(dep_analysis.get('missing_dependencies', []))}\n\n"
            )

        print(f"✅ Comprehensive report generated: {report_path}")
        print(f"📄 Report size: {os.path.getsize(report_path)} bytes")

        # Also generate JSON report for machine processing
        json_report_path = os.path.join(self.module_path, "scan_results.json")
        with open(json_report_path, "w", encoding="utf-8") as f:
            # Convert sets to lists for JSON serialization
            json_results = self.convert_for_json(self.results)
            json.dump(json_results, f, indent=2, default=str)

        print(f"📊 JSON data generated: {json_report_path}")

    def convert_for_json(self, obj):
        """Convert objects for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self.convert_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_for_json(item) for item in obj]
        elif isinstance(obj, set):
            return list(obj)
        else:
            return obj


if __name__ == "__main__":
    scanner = RecordsManagementScanner()
    scanner.scan_complete_module()

    print("\n🎉 COMPREHENSIVE SCAN COMPLETE!")
    print("📋 Check COMPREHENSIVE_SCAN_REPORT.md for detailed results")
    print("📊 Check scan_results.json for machine-readable data")
