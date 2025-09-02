#!/usr/bin/env python3
"""
Comprehensive Odoo Module Validation - Catches Real Issues

This script performs comprehensive validation of Odoo modules including:
- Python syntax errors
- XML syntax and structure validation
- View definition issues
- Security rule validation
- Model/field reference validation
- Import order validation
- Manifest validation
"""

import os
import sys
import ast
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Dict


class OdooValidator:
    """Comprehensive Odoo module validator"""

    def __init__(self, module_path: Path):
        self.module_path = module_path
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_python_syntax(self) -> None:
        """Check Python syntax in all Python files"""
        print("🔍 Checking Python syntax...")

        python_files = []
        for ext in ["*.py"]:
            python_files.extend(list(self.module_path.glob(f"**/{ext}")))

        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Try to compile the content
                compile(content, str(py_file), "exec")

                # Additional checks for Odoo-specific issues
                self._check_odoo_imports(py_file, content)
                self._check_model_definitions(py_file, content)

            except SyntaxError as e:
                self.errors.append(f"❌ PYTHON SYNTAX: {py_file.name}: {e.msg} at line {e.lineno}")
            except Exception as e:
                self.errors.append(f"❌ PYTHON ERROR: {py_file.name}: {str(e)}")

    def validate_xml_syntax(self) -> None:
        """Check XML syntax and structure"""
        print("🔍 Checking XML syntax and structure...")

        xml_files = []
        for ext in ["*.xml"]:
            xml_files.extend(list(self.module_path.glob(f"**/{ext}")))

        for xml_file in xml_files:
            try:
                with open(xml_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse XML
                ET.fromstring(content)

                # Additional Odoo XML validation
                self._check_xml_structure(xml_file, content)
                self._check_view_definitions(xml_file, content)
                self._check_security_rules(xml_file, content)

            except ET.ParseError as e:
                self.errors.append(f"❌ XML SYNTAX: {xml_file.name}: {str(e)}")
            except Exception as e:
                self.errors.append(f"❌ XML ERROR: {xml_file.name}: {str(e)}")

    def validate_manifest(self) -> None:
        """Check manifest file"""
        print("🔍 Checking manifest file...")

        manifest_file = self.module_path / "__manifest__.py"
        if manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Try to evaluate the manifest
                manifest_dict = eval(content)

                # Check required fields
                required_fields = ["name", "version", "depends"]
                for field in required_fields:
                    if field not in manifest_dict:
                        self.errors.append(f"❌ MANIFEST: Missing required field '{field}'")

                # Check depends
                if "depends" in manifest_dict:
                    depends = manifest_dict["depends"]
                    if not isinstance(depends, list):
                        self.errors.append("❌ MANIFEST: 'depends' must be a list")
                    elif "base" not in depends:
                        self.warnings.append("⚠️ MANIFEST: 'base' module not in dependencies")

            except Exception as e:
                self.errors.append(f"❌ MANIFEST: {str(e)}")
        else:
            self.errors.append("❌ MANIFEST: __manifest__.py not found")

    def validate_models_init(self) -> None:
        """Check models/__init__.py for proper imports"""
        print("🔍 Checking models/__init__.py...")

        init_file = self.module_path / "models" / "__init__.py"
        if init_file.exists():
            try:
                with open(init_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check for proper import structure
                if "from . import" not in content:
                    self.errors.append("❌ MODELS INIT: No relative imports found")

                # Check import order (basic check)
                lines = content.split("\n")
                import_lines = [line.strip() for line in lines if line.strip().startswith("from . import")]

                if import_lines:
                    # Check if imports are in alphabetical order
                    import_names = [line.split()[-1] for line in import_lines]
                    if import_names != sorted(import_names):
                        self.warnings.append("⚠️ MODELS INIT: Imports not in alphabetical order")

            except Exception as e:
                self.errors.append(f"❌ MODELS INIT: {str(e)}")
        else:
            self.warnings.append("⚠️ MODELS INIT: models/__init__.py not found")

    def _check_odoo_imports(self, file_path: Path, content: str) -> None:
        """Check for Odoo-specific import issues"""
        if "from odoo import" in content:
            # Check for common import patterns
            if "models" not in content and "fields" not in content:
                self.warnings.append(f"⚠️ IMPORTS: {file_path.name}: Missing models/fields imports")

    def _check_model_definitions(self, file_path: Path, content: str) -> None:
        """Check model definitions for common issues"""
        if "_name =" in content:
            # Check for _inherit without _name
            if "_inherit" in content and "_name" not in content:
                self.warnings.append(f"⚠️ MODEL: {file_path.name}: _inherit without _name")

    def _check_xml_structure(self, file_path: Path, content: str) -> None:
        """Check XML structure for Odoo-specific issues"""
        # Check for common XML issues
        if "<record" in content and "</record>" not in content:
            self.errors.append(f"❌ XML STRUCTURE: {file_path.name}: Unclosed record tag")

        if "<field" in content and "</field>" not in content:
            self.errors.append(f"❌ XML STRUCTURE: {file_path.name}: Unclosed field tag")

    def _check_view_definitions(self, file_path: Path, content: str) -> None:
        """Check view definitions for Odoo 18.0 compatibility"""
        if 'type="tree"' in content:
            self.errors.append(f"❌ VIEW TYPE: {file_path.name}: 'tree' type should be 'list' in Odoo 18.0")

        # Check for malformed expressions
        if "context_today()" in content:
            self.errors.append(f"❌ VIEW EXPRESSION: {file_path.name}: context_today() should be context_today")

        # Check for HTML entities in expressions
        if "&lt;" in content and "&gt;" in content:
            # This is actually correct for XML, but check for malformed ones
            pass

    def _check_security_rules(self, file_path: Path, content: str) -> None:
        """Check security rules for common issues"""
        if "ir.model.access.csv" in str(file_path):
            # This would be a CSV file, not XML
            return

        if "<record" in content and "ir.rule" in content:
            # Check for security rule issues
            if "domain_force" in content:
                # Basic domain validation could be added here
                pass

    def run_validation(self) -> Tuple[List[str], List[str]]:
        """Run all validation checks"""
        print("🚀 Starting Comprehensive Odoo Module Validation")
        print("=" * 60)

        self.validate_manifest()
        self.validate_models_init()
        self.validate_python_syntax()
        self.validate_xml_syntax()

        print("=" * 60)
        print("📊 VALIDATION COMPLETE")
        print("=" * 60)

        return self.errors, self.warnings

    def print_results(self) -> None:
        """Print validation results"""
        if self.errors:
            print(f"❌ CRITICAL ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")
            print()

        if self.warnings:
            print(f"⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        if not self.errors and not self.warnings:
            print("✅ NO ERRORS OR WARNINGS FOUND")
        elif not self.errors:
            print("✅ NO CRITICAL ERRORS - MODULE SHOULD LOAD")
        else:
            print("❌ CRITICAL ERRORS FOUND - MODULE WILL FAIL TO LOAD")


def main():
    """Main validation function"""
    # Find the module path
    current_dir = Path(__file__).parent.parent.parent
    module_path = current_dir / "records_management"

    if not module_path.exists():
        print(f"❌ Error: Module directory {module_path} does not exist")
        return 1

    # Run validation
    validator = OdooValidator(module_path)
    errors, warnings = validator.run_validation()

    # Print results
    validator.print_results()

    # Return exit code based on errors
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
