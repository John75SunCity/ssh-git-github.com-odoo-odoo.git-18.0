#!/usr/bin/env python3
"""
Comprehensive Odoo Module Validation - Catches Real Issues

This script performs comprehensive validation of Odoo modules including:
- Python syntax errors
- XML syntax and structure validation
- Model definition issues
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
    """
    Comprehensive Odoo module validator.

    This class accumulates errors and warnings in lists for later reporting.
    """

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

                # Try to safely evaluate the manifest
                # SECURITY WARNING: Using eval() to parse manifest files is dangerous and can execute arbitrary code.
                # Always use ast.literal_eval() for safe parsing of Python literals in manifest files.
                import ast
                manifest_dict = ast.literal_eval(content)

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

    def validate_security_access(self) -> None:
        """Check security access rules for completeness"""
        print("🔍 Checking security access rules...")

        access_file = self.module_path / "security" / "ir.model.access.csv"
        if access_file.exists():
            try:
                with open(access_file, "r", encoding="utf-8") as f:
                    # Use proper CSV parsing instead of simple split
                    import csv

                    reader = csv.reader(f)
                    data_lines = list(reader)

                # Skip header
                if data_lines and data_lines[0][0] == "id":
                    data_lines = data_lines[1:]

                # Collect model names from access rules
                access_models = set()
                for row in data_lines:
                    if row and len(row) >= 3:  # Need at least id, name, model_id:id
                        model_ref = row[2].strip()  # model_id:id column
                        if model_ref.startswith("model_"):
                            model_name = model_ref[6:]  # Remove 'model_' prefix
                            # Keep underscores as-is for model name matching
                            access_models.add(model_name)
                        else:
                            # Handle direct model names (correct Odoo format)
                            access_models.add(model_ref)

                # Check for missing access rules
                python_files = list(self.module_path.glob("models/*.py"))
                model_locations: dict[str, str] = {}  # Track where each model is defined

                for py_file in python_files:
                    try:
                        with open(py_file, "r", encoding="utf-8") as f:
                            content = f.read()

                        # Find model names - more specific pattern to avoid false matches
                        import re

                        name_pattern = r'^\s*_name\s*=\s*["\']([^"\']+)["\']'
                        matches = re.findall(name_pattern, content, re.MULTILINE)

                        for model_name in matches:
                            # Check for duplicate model names across files
                            if model_name in model_locations:
                                existing_file = model_locations[model_name]
                                self.errors.append(
                                    f"❌ DUPLICATE MODEL: Model '{model_name}' defined in both {existing_file} and {py_file.name} - this will cause module loading failure"
                                )
                            else:
                                model_locations[model_name] = py_file.name

                            # Check for missing access rules
                            if model_name not in access_models:
                                self.errors.append(
                                    f"❌ SECURITY: Missing access rules for model '{model_name}' in {py_file.name}"
                                )

                    except Exception as e:
                        self.warnings.append(f"⚠️ SECURITY CHECK: Could not parse {py_file.name}: {str(e)}")

            except Exception as e:
                self.errors.append(f"❌ SECURITY FILE: {str(e)}")
        else:
            self.errors.append("❌ SECURITY: ir.model.access.csv not found")

    def validate_translation_patterns(self) -> None:
        """Check for correct translation pattern usage"""
        print("🔍 Checking translation patterns...")

        python_files = list(self.module_path.glob("**/*.py"))
        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check for incorrect translation patterns
                import re

                # Pattern: _("Text") % value - WRONG (formatting after translation)
                wrong_pattern = r'_\(\s*["\'][^"\'%]*["\']\s*\)\s*%\s*[^%\n]*'
                if re.search(wrong_pattern, content):
                    self.errors.append(
                        f"❌ TRANSLATION: {py_file.name}: Don't format after translation - use _('Text %s', value) instead"
                    )

                # Pattern: _("Text %s") % value - This creates inconsistency
                inconsistent_pattern = r'_\(\s*["\'][^"\'%]*%[^"\'%]*["\']\s*\)\s*%\s*[^%\n]*'
                if re.search(inconsistent_pattern, content):
                    self.warnings.append(
                        f"⚠️ TRANSLATION: {py_file.name}: Consider using _('Text %s', value) for consistency"
                    )

            except Exception as e:
                self.warnings.append(f"⚠️ TRANSLATION CHECK: Could not parse {py_file.name}: {str(e)}")

    def validate_field_types(self) -> None:
        """Check for field type inconsistencies"""
        print("🔍 Checking field type consistency...")

        python_files = list(self.module_path.glob("models/*.py"))
        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check for Monetary fields without currency_field
                if "fields.Monetary(" in content and "currency_field" not in content:
                    self.warnings.append(f"⚠️ FIELD TYPE: {py_file.name}: Monetary field without currency_field")

                # Check for inconsistent field naming
                import re

                # Many2one fields should end with _id
                many2one_pattern = r"(\w+)\s*=\s*fields\.Many2one\("
                matches = re.findall(many2one_pattern, content)
                for field_name in matches:
                    if not field_name.endswith("_id"):
                        self.warnings.append(
                            f"⚠️ FIELD NAMING: {py_file.name}: Many2one field '{field_name}' should end with '_id'"
                        )

                # One2many/Many2many fields should end with _ids
                many_pattern = r"(\w+)\s*=\s*fields\.(One2many|Many2many)\("
                matches = re.findall(many_pattern, content)
                for field_name, field_type in matches:
                    if not field_name.endswith("_ids"):
                        self.warnings.append(
                            f"⚠️ FIELD NAMING: {py_file.name}: {field_type} field '{field_name}' should end with '_ids'"
                        )

            except Exception as e:
                self.warnings.append(f"⚠️ FIELD TYPE CHECK: Could not parse {py_file.name}: {str(e)}")

    def validate_model_structure(self) -> None:
        """Check model structure and organization"""
        print("🔍 Checking model structure...")

        python_files = list(self.module_path.glob("models/*.py"))
        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Count model classes in this file
                import re

                class_pattern = r"class\s+(\w+)\s*\([^)]*models\.Model[^)]*\):"
                model_classes = re.findall(class_pattern, content)

                if len(model_classes) > 1:  # Multiple models found
                    # Check if these models are related via One2many/Many2one/Many2many
                    has_relationships = self._check_related_models(content, model_classes)

                    if has_relationships:
                        # This is likely valid - related models in same file
                        self.warnings.append(
                            f"⚠️ MODEL STRUCTURE: {py_file.name}: Multiple related model classes: {', '.join(model_classes)} (valid for related models)"
                        )
                    else:
                        # No clear relationships - might be an issue
                        self.warnings.append(
                            f"⚠️ MODEL STRUCTURE: {py_file.name}: Multiple unrelated model classes: {', '.join(model_classes)} (consider separating)"
                        )

                # Check for models without _name
                for class_name in model_classes:
                    class_content = content[
                        content.find(f"class {class_name}") : (
                            content.find(f"class {class_name.split()[0]}", content.find(f"class {class_name}") + 1)
                            if content.find(f"class {class_name}", content.find(f"class {class_name}") + 1) != -1
                            else len(content)
                        )
                    ]
                    if "_name =" not in class_content:
                        self.warnings.append(
                            f"⚠️ MODEL STRUCTURE: {py_file.name}: Model class '{class_name}' missing _name attribute"
                        )

            except Exception as e:
                self.warnings.append(f"⚠️ MODEL STRUCTURE CHECK: Could not parse {py_file.name}: {str(e)}")

    def _check_related_models(self, content: str, model_classes: List[str]) -> bool:
        """Check if multiple models in a file are related via One2many/Many2one/Many2many"""
        import re

        # Extract model names from _name attributes
        model_names = []
        for class_name in model_classes:
            # Find the class definition and look for _name
            class_start = content.find(f"class {class_name}")
            if class_start != -1:
                # Look for _name in this class
                class_end = content.find("class ", class_start + 1)
                if class_end == -1:
                    class_end = len(content)
                class_content = content[class_start:class_end]

                name_match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', class_content)
                if name_match:
                    model_names.append(name_match.group(1))

        # Check for relationships between these models
        for model_name in model_names:
            # Look for references to other models in relationships
            for other_model in model_names:
                if model_name != other_model:
                    # Check for One2many/Many2one/Many2many relationships
                    relation_patterns = [
                        rf'comodel_name\s*=\s*["\']{re.escape(other_model)}["\']',
                        rf'["\']{re.escape(other_model)}["\']',  # In domain expressions
                    ]

                    for pattern in relation_patterns:
                        if re.search(pattern, content):
                            return True  # Found relationship

        return False  # No relationships found

    def validate_configurator_integration(self) -> None:
        """Check RM Module Configurator integration"""
        print("🔍 Checking RM Module Configurator integration...")

        config_file = self.module_path / "models" / "rm_module_configurator.py"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_content = f.read()

                # Check for new models that might need configurator integration
                python_files = list(self.module_path.glob("models/*.py"))
                for py_file in python_files:
                    if py_file.name != "rm_module_configurator.py":
                        try:
                            with open(py_file, "r", encoding="utf-8") as f:
                                content = f.read()

                            # Find model names
                            import re

                            name_pattern = r'_name\s*=\s*["\']([^"\']+)["\']'
                            matches = re.findall(name_pattern, content)

                            for model_name in matches:
                                # Check if this model has configurator integration
                                config_pattern = re.escape(model_name.replace(".", "_"))
                                if config_pattern not in config_content:
                                    self.warnings.append(
                                        f"⚠️ CONFIGURATOR: Model '{model_name}' may need configurator integration"
                                    )

                        except Exception as e:
                            continue

            except Exception as e:
                self.warnings.append(f"⚠️ CONFIGURATOR CHECK: Could not parse configurator file: {str(e)}")
        else:
            self.warnings.append("⚠️ CONFIGURATOR: rm_module_configurator.py not found")

    def validate_menu_actions(self) -> None:
        """Check menu and action references"""
        print("🔍 Checking menu and action references...")

        xml_files = list(self.module_path.glob("**/*.xml"))
        # Cache all XML file contents once
        xml_contents = {}
        for xml_file in xml_files:
            try:
                with open(xml_file, "r", encoding="utf-8") as f:
                    xml_contents[xml_file] = f.read()
            except Exception as e:
                self.warnings.append(f"⚠️ MENU ACTION CHECK: Could not read {xml_file.name}: {str(e)}")

        for xml_file, content in xml_contents.items():
            try:
                # Check for action references in menus
                import re

                action_refs = re.findall(r'action="([^"]+)"', content)
                menu_refs = re.findall(r'parent="([^"]+)"', content)

                # Check if referenced actions/menus exist
                # This is a basic check - could be enhanced with cross-file validation
                for action_ref in action_refs:
                    if not any(
                        action_ref in other_content
                        for other_file, other_content in xml_contents.items()
                        if other_file != xml_file
                    ):
                        self.warnings.append(
                            f"⚠️ MENU ACTION: {xml_file.name}: Referenced action '{action_ref}' may not exist"
                        )

            except Exception as e:
                self.warnings.append(f"⚠️ MENU ACTION CHECK: Could not parse {xml_file.name}: {str(e)}")

    def validate_domain_expressions(self) -> None:
        """Check domain expressions for syntax errors"""
        print("🔍 Checking domain expressions...")

        python_files = list(self.module_path.glob("**/*.py"))
        xml_files = list(self.module_path.glob("**/*.xml"))

        for file_path in python_files + xml_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check for common domain syntax issues
                import re

                # Find domain assignments - handle multi-line domains properly
                # Look for domain = [ patterns
                domain_pattern = r"domain\s*=\s*\["
                domain_starts = list(re.finditer(domain_pattern, content))

                for match in domain_starts:
                    start_pos = match.end() - 1  # Position of the opening bracket

                    # Find the matching closing bracket
                    bracket_count = 0
                    end_pos = start_pos
                    in_string = False
                    string_char = None

                    while end_pos < len(content):
                        char = content[end_pos]

                        # Handle string literals
                        if not in_string and char in ['"', "'"]:
                            check_pos = end_pos - 1
                            while check_pos >= 0 and content[check_pos] == "\\":
                                escape_count += 1
                                check_pos -= 1
                            escape_count = 0
                            check_pos = end_pos - 1
                            while check_pos >= 0 and content[check_pos] == "":
                                escape_count += 1
                                check_pos -= 1
                            if escape_count % 2 == 0:  # Not escaped
                                in_string = False
                                string_char = None
                        elif not in_string:
                            if char == "[":
                                bracket_count += 1
                            elif char == "]":
                                bracket_count -= 1
                                if bracket_count == 0:
                                    # Found the matching closing bracket
                                    domain_expr = content[start_pos : end_pos + 1]

                                    # Count brackets in the domain expression
                                    open_brackets = domain_expr.count("[")
                                    close_brackets = domain_expr.count("]")
                                    if open_brackets != close_brackets:
                                        self.errors.append(
                                            f"❌ DOMAIN: {file_path.name}: Unbalanced brackets in domain expression"
                                        )

                                    # Check for common syntax errors
                                    if domain_expr.strip().endswith(","):
                                        self.warnings.append(
                                            f"⚠️ DOMAIN: {file_path.name}: Domain expression ends with comma"
                                        )

                                    break

                        end_pos += 1

                    # If we didn't find a matching bracket, it's an error
                    if bracket_count != 0:
                        self.errors.append(
                            f"❌ DOMAIN: {file_path.name}: Unclosed domain expression starting at position {start_pos}"
                        )

            except Exception as e:
                self.warnings.append(f"⚠️ DOMAIN CHECK: Could not parse {file_path.name}: {str(e)}")

    def validate_csv_files(self) -> None:
        """Check CSV file format and content"""
        print("🔍 Checking CSV files...")

        csv_files = list(self.module_path.glob("**/*.csv"))
        for csv_file in csv_files:
            try:
                with open(csv_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                if not lines:
                    self.errors.append(f"❌ CSV: {csv_file.name}: Empty CSV file")
                    continue

                # Check header
                header = lines[0].strip()
                if not header:
                    self.errors.append(f"❌ CSV: {csv_file.name}: Missing header row")

                # Check data rows
                for i, line in enumerate(lines[1:], 1):
                    if line.strip():  # Skip empty lines
                        parts = line.split(",")
                        if parts and len(parts) < 4:  # Basic check for access CSV
                            self.warnings.append(f"⚠️ CSV: {csv_file.name}: Line {i+1} may have insufficient columns")

            except Exception as e:
                self.errors.append(f"❌ CSV: {csv_file.name}: {str(e)}")

    def validate_computed_fields(self) -> None:
        """Check computed field dependencies"""
        print("🔍 Checking computed field dependencies...")

        python_files = list(self.module_path.glob("models/*.py"))
        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find computed fields
                import re

                computed_pattern = r"@.*\.depends\(([^)]+)\)"
                depends_matches = re.findall(computed_pattern, content)

                for depends_str in depends_matches:
                    # Extract field names from depends
                    field_names = re.findall(r'["\']([^"\']+)["\']', depends_str)

                    # Check if these fields exist in the same model
                    for field_name in field_names:
                        if "fields." in content:  # Basic check
                            # This is a simplified check - could be enhanced
                            pass

            except Exception as e:
                self.warnings.append(f"⚠️ COMPUTED FIELD CHECK: Could not parse {py_file.name}: {str(e)}")

    def validate_view_field_references(self) -> None:
        """Check that all fields referenced in views exist in their models"""
        print("🔍 Checking view field references...")

        # First, collect all model fields
        model_fields = self._collect_model_fields()

        # Check XML files for view field references
        xml_files = []
        for ext in ["*.xml"]:
            xml_files.extend(list(self.module_path.glob(f"**/{ext}")))

        for xml_file in xml_files:
            try:
                with open(xml_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Only check view files
                if (
                    'model="ir.ui.view"' in content
                    or 'type="form"' in content
                    or 'type="list"' in content
                    or 'type="kanban"' in content
                ):
                    self._check_view_fields(xml_file, content, model_fields)

            except Exception as e:
                self.errors.append(f"❌ VIEW FIELD CHECK: {xml_file.name}: {str(e)}")

    def _collect_model_fields(self) -> Dict[str, List[str]]:
        """Collect all fields from model definitions"""
        model_fields = {}

        python_files = []
        for ext in ["*.py"]:
            python_files.extend(list(self.module_path.glob(f"**/{ext}")))

        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse the Python file to find model definitions
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if this is an Odoo model
                        model_name = None
                        fields = []

                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                # Check for _name assignment
                                if len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                                    if item.targets[0].id == "_name":
                                        if isinstance(item.value, ast.Str):
                                            model_name = item.value.s
                                        elif isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                                            model_name = item.value.value

                                # Check for field definitions
                                elif isinstance(item.value, ast.Call):
                                    # Look for fields.XXX pattern
                                    if isinstance(item.value.func, ast.Attribute):
                                        if (
                                            isinstance(item.value.func.value, ast.Name)
                                            and item.value.func.value.id == "fields"
                                        ):
                                            # This is a fields.XXX call
                                            if len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                                                fields.append(item.targets[0].id)

                        if model_name and fields:
                            model_fields[model_name] = fields

            except Exception as e:
                # Skip files that can't be parsed
                continue

        return model_fields

    def _check_view_fields(self, xml_file: Path, content: str, model_fields: Dict[str, List[str]]) -> None:
        """Check field references in a view file"""
        try:
            # Extract model name from view
            model_name = None
            if 'model="records.document"' in content:
                model_name = "records.document"
            elif 'model="records.container"' in content:
                model_name = "records.container"
            elif 'model="records.request"' in content:
                model_name = "records.request"
            # Add more model mappings as needed

            if not model_name:
                return

            # Extract field references from XML
            import re

            field_pattern = r'<field\s+name="([^"]+)"'
            field_matches = re.findall(field_pattern, content)

            # Check each field reference
            available_fields = model_fields.get(model_name, [])
            for field_name in field_matches:
                if field_name not in available_fields:
                    # Skip common computed/related fields that might not be in the basic field list
                    skip_fields = ["display_name", "create_date", "write_date", "create_uid", "write_uid"]
                    if field_name not in skip_fields:
                        self.errors.append(
                            f"❌ VIEW FIELD: {xml_file.name}: Field '{field_name}' does not exist in model '{model_name}'"
                        )

        except Exception as e:
            self.errors.append(f"❌ VIEW FIELD CHECK: {xml_file.name}: {str(e)}")

    def run_validation(self) -> Tuple[List[str], List[str]]:
        """Run all validation checks"""
        print("🚀 Starting Comprehensive Odoo Module Validation")
        print("=" * 60)

        self.validate_manifest()
        self.validate_models_init()
        self.validate_python_syntax()
        self.validate_xml_syntax()
        self.validate_security_access()
        self.validate_translation_patterns()
        self.validate_field_types()
        self.validate_model_structure()
        self.validate_configurator_integration()
        self.validate_menu_actions()
        self.validate_domain_expressions()
        self.validate_csv_files()
        self.validate_computed_fields()
        self.validate_view_field_references()

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
    return 1 if len(errors) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
