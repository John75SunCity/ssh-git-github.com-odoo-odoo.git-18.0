#!/usr/bin/env python3
"""
Odoo-Enhanced Relationship Auditor for Records Management
Uses Odoo's built-in validation patterns and best practices
"""
import os
import re
import ast
import json
from collections import defaultdict


class OdooEnhancedAuditor:
    """Enhanced auditor that follows Odoo coding standards and patterns"""

    def __init__(self, base_path):
        self.base_path = base_path
        self.models_path = os.path.join(base_path, "records_management", "models")
        self.results = {
            "critical_issues": [],
            "warnings": [],
            "recommendations": [],
            "optimizations": [],
            "validation_errors": [],
        }

        # Standard Odoo models that should not be flagged as missing
        self.standard_odoo_models = {
            "res.company",
            "res.users",
            "res.partner",
            "res.currency",
            "res.country",
            "res.groups",
            "mail.template",
            "mail.message",
            "mail.followers",
            "mail.activity",
            "ir.model",
            "ir.ui.view",
            "ir.attachment",
            "ir.sequence",
            "ir.cron",
            "ir.actions.act_window",
            "account.move",
            "account.tax",
            "product.product",
            "product.template",
            "product.category",
            "stock.move",
            "stock.lot",
            "pos.config",
            "pos.session",
            "pos.order",
            "hr.employee",
            "project.task",
            "fleet.vehicle",
            "res.partner.category",
            "maintenance.equipment",
            "maintenance.request",
        }

        # Track model relationships
        self.model_definitions = {}
        self.field_relationships = defaultdict(list)

    def scan_python_files(self):
        """Scan Python files with AST parsing for better accuracy"""
        print("🔍 Enhanced Python file scanning with AST parsing...")

        py_files = [
            f
            for f in os.listdir(self.models_path)
            if f.endswith(".py") and not f.startswith("__")
        ]

        for py_file in py_files:
            file_path = os.path.join(self.models_path, py_file)
            self._analyze_python_file(file_path)

        print(f"✅ Analyzed {len(py_files)} Python files")
        print(f"📊 Found {len(self.model_definitions)} model definitions")

    def _analyze_python_file(self, file_path):
        """Analyze Python file using AST for precise parsing"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse with AST for better accuracy
            try:
                tree = ast.parse(content)
                self._extract_from_ast(tree, file_path, content)
            except SyntaxError:
                # Fallback to regex if AST fails
                self._extract_with_regex(content, file_path)

        except Exception as e:
            self.results["validation_errors"].append(
                {"file": file_path, "error": str(e), "type": "file_read_error"}
            )

    def _extract_from_ast(self, tree, file_path, content):
        """Extract model information using AST"""
        # Find all class definitions first
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if this class inherits from models.Model or has _name
                model_name = self._extract_model_name(node, content)
                if model_name:
                    self.model_definitions[model_name] = {
                        "file": file_path,
                        "fields": {},
                        "class_name": node.name,
                    }

                    # Extract fields from this class
                    for class_node in node.body:
                        if isinstance(class_node, ast.Assign):
                            self._extract_field_from_assignment(
                                class_node, model_name, content
                            )

    def _extract_model_name(self, class_node, content):
        """Extract _name from class body"""
        # First try AST approach
        for node in class_node.body:
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "_name"
            ):
                if isinstance(node.value, ast.Str):
                    return node.value.s
                elif isinstance(node.value, ast.Constant):
                    return node.value.value

        # Fallback to regex in this class area
        class_start = class_node.lineno
        class_lines = content.split("\n")[
            class_start - 1 : class_start + 50
        ]  # Look in first 50 lines
        class_content = "\n".join(class_lines)

        model_match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', class_content)
        if model_match:
            return model_match.group(1)

        return None

    def _extract_field_from_assignment(self, node, model_name, content):
        """Extract field information from assignment node"""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):

            field_name = node.targets[0].id

            # Check if this is a fields assignment
            if isinstance(node.value, ast.Call):
                field_info = self._analyze_field_call(node.value, content)
                if field_info:
                    self.model_definitions[model_name]["fields"][
                        field_name
                    ] = field_info

                    # Track relationships
                    if field_info["type"] in ["Many2one", "One2many", "Many2many"]:
                        self.field_relationships[model_name].append(
                            {
                                "field_name": field_name,
                                "field_type": field_info["type"],
                                "comodel": field_info.get("comodel"),
                                "inverse": field_info.get("inverse"),
                            }
                        )

    def _analyze_field_call(self, call_node, content):
        """Analyze a field method call"""
        if (
            isinstance(call_node.func, ast.Attribute)
            and isinstance(call_node.func.value, ast.Name)
            and call_node.func.value.id == "fields"
        ):

            field_type = call_node.func.attr
            field_info = {"type": field_type}

            # Extract comodel from first argument for relational fields
            if field_type in ["Many2one", "One2many", "Many2many"] and call_node.args:
                if isinstance(call_node.args[0], ast.Str):
                    field_info["comodel"] = call_node.args[0].s
                elif isinstance(call_node.args[0], ast.Constant):
                    field_info["comodel"] = call_node.args[0].value

            # Extract inverse from second argument for One2many
            if field_type == "One2many" and len(call_node.args) > 1:
                if isinstance(call_node.args[1], ast.Str):
                    field_info["inverse"] = call_node.args[1].s
                elif isinstance(call_node.args[1], ast.Constant):
                    field_info["inverse"] = call_node.args[1].value

            # Extract named parameters (comodel_name, inverse_name, etc.)
            for keyword in call_node.keywords:
                if keyword.arg == "comodel_name":
                    if isinstance(keyword.value, ast.Str):
                        field_info["comodel"] = keyword.value.s
                    elif isinstance(keyword.value, ast.Constant):
                        field_info["comodel"] = keyword.value.value
                elif keyword.arg == "inverse_name":
                    if isinstance(keyword.value, ast.Str):
                        field_info["inverse"] = keyword.value.s
                    elif isinstance(keyword.value, ast.Constant):
                        field_info["inverse"] = keyword.value.value

            return field_info

        return None

    def _extract_with_regex(self, content, file_path):
        """Fallback regex extraction"""
        # Extract model name
        model_match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', content)
        if model_match:
            model_name = model_match.group(1)
            self.model_definitions[model_name] = {"file": file_path, "fields": {}}

            # Extract fields
            field_pattern = r"(\w+)\s*=\s*fields\.(Many2one|One2many|Many2many|Char|Text|Boolean|Integer|Float|Date|Datetime|Selection)\s*\([^)]*\)"
            for match in re.finditer(field_pattern, content):
                field_name = match.group(1)
                field_type = match.group(2)
                self.model_definitions[model_name]["fields"][field_name] = {
                    "type": field_type
                }

    def validate_relationships(self):
        """Validate One2many/Many2one relationships"""
        print("🔍 Validating model relationships...")

        critical_issues = []
        warnings = []

        for model_name, relationships in self.field_relationships.items():
            for rel in relationships:
                if rel["field_type"] == "One2many":
                    issue = self._validate_one2many(model_name, rel)
                    if issue:
                        if issue["severity"] == "critical":
                            critical_issues.append(issue)
                        else:
                            warnings.append(issue)

                elif rel["field_type"] == "Many2one":
                    issue = self._validate_many2one(model_name, rel)
                    if issue:
                        warnings.append(issue)

        self.results["critical_issues"] = critical_issues
        self.results["warnings"] = warnings

        print(f"⚠️  Found {len(critical_issues)} critical relationship issues")
        print(f"💡 Found {len(warnings)} relationship warnings")

    def _validate_one2many(self, model_name, relationship):
        """Validate One2many relationship"""
        comodel = relationship.get("comodel")
        inverse_field = relationship.get("inverse")

        if not comodel or not inverse_field:
            return {
                "type": "incomplete_one2many",
                "severity": "critical",
                "model": model_name,
                "field": relationship["field_name"],
                "message": f"One2many field {relationship['field_name']} missing comodel or inverse field",
            }

        # Check if comodel exists
        if (
            comodel not in self.model_definitions
            and comodel not in self.standard_odoo_models
        ):
            return {
                "type": "missing_comodel",
                "severity": "critical",
                "model": model_name,
                "field": relationship["field_name"],
                "comodel": comodel,
                "message": f"One2many field {relationship['field_name']} references unknown model {comodel}",
            }

        # Check if inverse field exists in comodel
        if (
            comodel in self.model_definitions
            and inverse_field not in self.model_definitions[comodel]["fields"]
        ):
            return {
                "type": "missing_inverse_field",
                "severity": "critical",
                "model": model_name,
                "field": relationship["field_name"],
                "comodel": comodel,
                "inverse_field": inverse_field,
                "message": f"Inverse field {inverse_field} not found in {comodel}",
            }

        return None

    def _validate_many2one(self, model_name, relationship):
        """Validate Many2one relationship"""
        comodel = relationship.get("comodel")

        if not comodel:
            return {
                "type": "incomplete_many2one",
                "severity": "warning",
                "model": model_name,
                "field": relationship["field_name"],
                "message": f"Many2one field {relationship['field_name']} missing comodel",
            }

        # Check if comodel exists
        if (
            comodel not in self.model_definitions
            and comodel not in self.standard_odoo_models
        ):
            return {
                "type": "missing_comodel",
                "severity": "warning",
                "model": model_name,
                "field": relationship["field_name"],
                "comodel": comodel,
                "message": f"Many2one field {relationship['field_name']} references unknown model {comodel}",
            }

        return None

    def suggest_optimizations(self):
        """Suggest code optimizations"""
        print("💡 Analyzing optimization opportunities...")

        optimizations = []

        for model_name, model_info in self.model_definitions.items():
            file_path = model_info["file"]

            # Check file size
            file_size = os.path.getsize(file_path)
            line_count = self._count_lines(file_path)

            if line_count > 500:
                optimizations.append(
                    {
                        "type": "large_file",
                        "file": file_path,
                        "model": model_name,
                        "lines": line_count,
                        "recommendation": f"Consider splitting {model_name} model (>{line_count} lines)",
                    }
                )

            # Check for duplicate field patterns
            field_types = [f["type"] for f in model_info["fields"].values()]
            common_fields = ["company_id", "user_id", "active", "name"]
            missing_common = [f for f in common_fields if f not in model_info["fields"]]

            if missing_common:
                optimizations.append(
                    {
                        "type": "missing_standard_fields",
                        "model": model_name,
                        "missing_fields": missing_common,
                        "recommendation": f"Consider adding standard fields: {', '.join(missing_common)}",
                    }
                )

        self.results["optimizations"] = optimizations
        print(f"📊 Found {len(optimizations)} optimization opportunities")

    def _count_lines(self, file_path):
        """Count lines in file"""
        try:
            with open(file_path, "r") as f:
                return sum(1 for _ in f)
        except:
            return 0

    def generate_fixes(self):
        """Generate specific fixes for critical issues"""
        print("🔧 Generating automated fixes...")

        fixes = []

        for issue in self.results["critical_issues"]:
            if issue["type"] == "missing_inverse_field":
                fix = self._generate_inverse_field_fix(issue)
                if fix:
                    fixes.append(fix)

        return fixes

    def _generate_inverse_field_fix(self, issue):
        """Generate fix for missing inverse field"""
        comodel = issue["comodel"]
        inverse_field = issue["inverse_field"]
        source_model = issue["model"]

        if comodel not in self.model_definitions:
            return None

        comodel_file = self.model_definitions[comodel]["file"]

        # Generate Many2one field definition
        field_def = f'    {inverse_field} = fields.Many2one("{source_model}", string="{inverse_field.replace("_", " ").title()}")'

        return {
            "type": "add_inverse_field",
            "file": comodel_file,
            "field_definition": field_def,
            "description": f"Add missing inverse field {inverse_field} to {comodel}",
        }

    def run_comprehensive_audit(self):
        """Run complete audit with enhanced validation"""
        print("🚀 Starting Odoo-Enhanced Relationship Audit")
        print("=" * 60)

        # Step 1: Scan files
        self.scan_python_files()

        # Step 2: Validate relationships
        self.validate_relationships()

        # Step 3: Suggest optimizations
        self.suggest_optimizations()

        # Step 4: Generate fixes
        fixes = self.generate_fixes()

        # Step 5: Generate report
        report = self.generate_report()

        # Save detailed report
        report_file = os.path.join(
            self.base_path, "development-tools", "odoo_enhanced_audit_report.json"
        )

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Enhanced audit report saved to: {report_file}")

        return report, fixes

    def generate_report(self):
        """Generate comprehensive report"""
        return {
            "timestamp": "2025-08-05",
            "audit_type": "odoo_enhanced",
            "summary": {
                "total_models": len(self.model_definitions),
                "critical_issues": len(self.results["critical_issues"]),
                "warnings": len(self.results["warnings"]),
                "optimizations": len(self.results["optimizations"]),
                "validation_errors": len(self.results["validation_errors"]),
            },
            "models": self.model_definitions,
            "critical_issues": self.results["critical_issues"],
            "warnings": self.results["warnings"],
            "optimizations": self.results["optimizations"],
            "validation_errors": self.results["validation_errors"],
            "standard_odoo_models": list(self.standard_odoo_models),
        }


def main():
    """Main execution"""
    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0"

    auditor = OdooEnhancedAuditor(base_path)

    print("Running Odoo-Enhanced Relationship Auditor...")
    report, fixes = auditor.run_comprehensive_audit()

    print(f"\n📊 AUDIT SUMMARY:")
    print(f"   Total Models: {report['summary']['total_models']}")
    print(f"   Critical Issues: {report['summary']['critical_issues']}")
    print(f"   Warnings: {report['summary']['warnings']}")
    print(f"   Optimizations: {report['summary']['optimizations']}")
    print(f"   Validation Errors: {report['summary']['validation_errors']}")

    if report["summary"]["critical_issues"] > 0:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in report["critical_issues"]:
            print(f"   ❌ {issue['message']}")

    if fixes:
        print(f"\n🔧 GENERATED FIXES: {len(fixes)}")
        for fix in fixes:
            print(f"   🔨 {fix['description']}")

    return report, fixes


if __name__ == "__main__":
    main()
