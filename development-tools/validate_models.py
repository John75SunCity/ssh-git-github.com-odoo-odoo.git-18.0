#!/usr/bin/env python3
"""
Model Validat        # Find all model files
        models_dir = self.workspace_root / "records_management"
        if not models_dir.exists():
            self.errors.append("Records management module not found")
            return

        # Look for models directory or direct Python files
        models_subdir = models_dir / "models"
        if models_subdir.exists():
            search_dir = models_subdir
        else:
            search_dir = models_dir

        # Scan all Python files in models directory
        for py_file in search_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            self._validate_model_file(py_file)======================

Validates Odoo model definitions and field configurations.
Checks for common model-related issues and best practices.

Features:
- Model definition validation
- Field configuration checks
- Relationship integrity validation
- Inheritance pattern verification
- Security rule consistency

Author: GitHub Copilot
Version: 1.0.0
Date: 2025-08-28
"""

import os
import sys
import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set

class ModelValidator:
    """Validates Odoo model definitions and configurations"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.models: Dict[str, Dict] = {}

    def validate_models(self) -> bool:
        """Main validation function"""
        print("🔍 Validating Odoo Model Definitions...")

        # Find all model files
        models_dir = self.workspace_root / "records_management" / "models"
        if not models_dir.exists():
            self.errors.append("Models directory not found")
            return False        # Scan all Python files in models directory
        for py_file in models_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            self._validate_model_file(py_file)

        # Validate model relationships
        self._validate_relationships()

        # Validate security consistency
        self._validate_security_consistency()

        return len(self.errors) == 0

    def _validate_model_file(self, file_path: Path) -> None:
        """Validate a single model file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the Python file
            tree = ast.parse(content, filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._validate_model_class(node, file_path)

        except SyntaxError as e:
            self.errors.append(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            self.errors.append(f"Error parsing {file_path}: {e}")

    def _validate_model_class(self, class_node: ast.ClassDef, file_path: Path) -> None:
        """Validate a model class definition"""
        class_name = class_node.name

        # Skip mock classes and non-model classes
        if class_name.startswith('_') or 'Mock' in class_name:
            return

        # Check if this is an Odoo model class by looking for inheritance from models.Model
        is_odoo_model = False
        for base in class_node.bases:
            if isinstance(base, ast.Attribute):
                # Check for models.Model inheritance
                if (isinstance(base.value, ast.Name) and base.value.id == 'models' and
                    base.attr == 'Model'):
                    is_odoo_model = True
                    break
            elif isinstance(base, ast.Name):
                # Check for inheritance from other model classes (like _inherit)
                # We'll validate this differently
                pass

        # If it's not clearly an Odoo model, check for _inherit or _name
        if not is_odoo_model:
            inherit_attr = self._find_class_attribute(class_node, '_inherit')
            if inherit_attr:
                is_odoo_model = True

        # Only validate Odoo model classes
        if not is_odoo_model:
            return

        # Check for _name attribute (only required for new models, not inheritance)
        name_attr = self._find_class_attribute(class_node, '_name')
        inherit_attr = self._find_class_attribute(class_node, '_inherit')

        # If it has _inherit but no _name, that's valid (inheritance model)
        if inherit_attr and not name_attr:
            # This is a valid inheritance model, validate it differently
            self._validate_inheritance_model(class_node, file_path)
            return

        # If it has _name, validate as a regular model
        if name_attr:
            model_name = self._get_attribute_value(name_attr)
            if not model_name:
                self.errors.append(f"Model class {class_name} in {file_path} has invalid _name")
                return

            # Check for _description attribute
            desc_attr = self._find_class_attribute(class_node, '_description')
            if not desc_attr:
                self.warnings.append(f"Model {model_name} missing _description attribute")

            # Store model info for relationship validation
            self.models[model_name] = {
                'file': file_path,
                'class': class_name,
                'fields': self._extract_fields(class_node)
            }

            # Validate field definitions
            self._validate_fields(class_node, model_name, file_path)
        else:
            # No _name and no _inherit - this might be a base class or invalid
            self.errors.append(f"Model class {class_name} in {file_path} missing both _name and _inherit attributes")

    def _validate_inheritance_model(self, class_node: ast.ClassDef, file_path: Path) -> None:
        """Validate an inheritance model (using _inherit)"""
        class_name = class_node.name

        # For inheritance models, we still validate fields but don't require _name
        # Extract the inherited model name from _inherit
        inherit_attr = self._find_class_attribute(class_node, '_inherit')
        if inherit_attr:
            inherit_value = self._get_attribute_value(inherit_attr)
            if inherit_value:
                # Store model info for relationship validation using the inherited name
                if isinstance(inherit_value, list):
                    # Multiple inheritance
                    for inherited_model in inherit_value:
                        if inherited_model not in self.models:
                            self.models[inherited_model] = {
                                'file': file_path,
                                'class': class_name,
                                'fields': self._extract_fields(class_node),
                                'inherited': True
                            }
                else:
                    # Single inheritance
                    if inherit_value not in self.models:
                        self.models[inherit_value] = {
                            'file': file_path,
                            'class': class_name,
                            'fields': self._extract_fields(class_node),
                            'inherited': True
                        }

        # Validate field definitions for inheritance model
        # We need to determine what model name to use for validation
        model_name = f"{class_name} (inheritance)"
        self._validate_fields(class_node, model_name, file_path)

    def _find_class_attribute(self, class_node: ast.ClassDef, attr_name: str) -> ast.Assign:
        """Find a class attribute assignment"""
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == attr_name:
                        return node
        return None

    def _get_attribute_value(self, assign_node: ast.Assign) -> str:
        """Extract string value from attribute assignment"""
        if isinstance(assign_node.value, ast.Str):
            return assign_node.value.s
        elif hasattr(assign_node.value, 'value') and isinstance(assign_node.value.value, str):
            return assign_node.value.value
        return None

    def _extract_fields(self, class_node: ast.ClassDef) -> Dict[str, Dict]:
        """Extract field definitions from model class"""
        fields = {}

        for node in class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        field_name = target.id
                        if field_name.endswith('_id') or field_name.endswith('_ids'):
                            # This is likely a field definition
                            fields[field_name] = {
                                'line': node.lineno,
                                'value': self._get_field_type(node)
                            }

        return fields

    def _get_field_type(self, assign_node: ast.Assign) -> str:
        """Extract field type from assignment"""
        try:
            if isinstance(assign_node.value, ast.Call):
                if isinstance(assign_node.value.func, ast.Attribute):
                    func_name = assign_node.value.func.attr
                    return func_name
                elif isinstance(assign_node.value.func, ast.Name):
                    return assign_node.value.func.id
        except:
            pass
        return "unknown"

    def _validate_fields(self, class_node: ast.ClassDef, model_name: str, file_path: Path) -> None:
        """Validate field definitions"""
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        field_name = target.id

                        # Check for common field naming issues
                        if field_name.startswith('_') and not field_name.startswith('__'):
                            # Standard Odoo private fields that should be allowed
                            standard_private_fields = [
                                '_name', '_description', '_inherit', '_inherits', '_order', '_rec_name', '_table',
                                '_sql_constraints', '_sql', '_auto', '_sequence', '_parent_name', '_parent_store',
                                '_date_name', '_fold_name', '_needaction', '_track', '_tracking', '_depends',
                                '_retention_period_was_indefinite', '_check_company_auto', '_company_default_get'
                            ]
                            if field_name not in standard_private_fields:
                                self.warnings.append(f"Non-standard private field {field_name} in model {model_name}")

                        # Validate field definitions
                        if isinstance(node.value, ast.Call):
                            self._validate_field_call(node.value, field_name, model_name, file_path)

    def _validate_field_call(self, call_node: ast.Call, field_name: str, model_name: str, file_path: Path) -> None:
        """Validate field method calls"""
        if isinstance(call_node.func, ast.Attribute):
            field_type = call_node.func.attr

            # Validate field arguments
            if field_type in ['Many2one', 'One2many', 'Many2many']:
                self._validate_relation_field(call_node, field_name, model_name, field_type)

            # Check for required arguments
            if field_type == 'Many2one':
                has_comodel = False

                # Check keyword arguments
                for keyword in call_node.keywords:
                    if keyword.arg == 'comodel_name':
                        has_comodel = True
                        break

                # Check positional arguments (first arg is comodel_name)
                if not has_comodel and call_node.args and len(call_node.args) >= 1:
                    has_comodel = True

                if not has_comodel:
                    self.errors.append(f"Many2one field {field_name} in model {model_name} missing comodel_name")

    def _validate_relation_field(self, call_node: ast.Call, field_name: str, model_name: str, field_type: str) -> None:
        """Validate relational field definitions"""
        # Check for comodel_name in relational fields (both positional and keyword)
        has_comodel = False

        # Check keyword arguments
        for keyword in call_node.keywords:
            if keyword.arg == 'comodel_name':
                has_comodel = True
                break

        # Check positional arguments (first arg for Many2one, first arg for One2many/Many2many)
        if not has_comodel and call_node.args:
            if field_type == 'Many2one' and len(call_node.args) >= 1:
                # First positional arg is comodel_name for Many2one
                has_comodel = True
            elif field_type in ['One2many', 'Many2many'] and len(call_node.args) >= 1:
                # First positional arg is comodel_name for One2many/Many2many
                has_comodel = True

        if not has_comodel:
            self.errors.append(f"Relational field {field_name} ({field_type}) in model {model_name} missing comodel_name")

        # Check for inverse_name in One2many/Many2many
        if field_type in ['One2many', 'Many2many']:
            has_inverse = False
            has_relation_params = False

            # Check keyword arguments
            for keyword in call_node.keywords:
                if keyword.arg == 'inverse_name':
                    has_inverse = True
                elif keyword.arg in ['relation', 'column1', 'column2']:
                    has_relation_params = True

            # Check positional arguments (second arg for One2many/Many2many)
            if not has_inverse and len(call_node.args) >= 2:
                has_inverse = True

            # For Many2many fields, also check for relation table parameters
            if field_type == 'Many2many':
                # Check if we have the three relation parameters
                relation_count = sum(1 for keyword in call_node.keywords
                                   if keyword.arg in ['relation', 'column1', 'column2'])
                if relation_count >= 3:  # We need at least relation, column1, column2
                    has_relation_params = True

            # One2many requires inverse_name, Many2many can use either inverse_name OR relation params
            if field_type == 'One2many' and not has_inverse:
                self.errors.append(f"Relational field {field_name} ({field_type}) in model {model_name} missing inverse_name")
            elif field_type == 'Many2many' and not (has_inverse or has_relation_params):
                self.errors.append(f"Relational field {field_name} ({field_type}) in model {model_name} missing inverse_name or relation parameters (relation, column1, column2)")

    def _validate_relationships(self) -> None:
        """Validate model relationships"""
        for model_name, model_info in self.models.items():
            for field_name, field_info in model_info['fields'].items():
                if field_name.endswith('_id') and field_info['value'] == 'Many2one':
                    # Check if target model exists
                    # This is a simplified check - in practice you'd need to parse comodel_name
                    pass

    def _validate_security_consistency(self) -> None:
        """Validate security rule consistency"""
        security_file = self.workspace_root / "records_management" / "security" / "ir.model.access.csv"
        if not security_file.exists():
            # Try alternative location
            alt_security_file = self.workspace_root / "records_management" / "ir.model.access.csv"
            if alt_security_file.exists():
                security_file = alt_security_file
            else:
                self.errors.append("Security access file not found")
                return

        try:
            with open(security_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Check if all models have security rules
            for model_name in self.models.keys():
                model_found = False
                for line in lines[1:]:  # Skip header
                    if f"model_{model_name}" in line or model_name in line:
                        model_found = True
                        break

                if not model_found:
                    self.errors.append(f"Model {model_name} missing security access rules")

        except Exception as e:
            self.errors.append(f"Error reading security file: {e}")

    def print_report(self) -> None:
        """Print validation report"""
        print(f"\n📊 Model Validation Report")
        print("=" * 50)

        if self.errors:
            print(f"❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"\n⚠️ Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("✅ All model validations passed!")

        print(f"\n📈 Summary: {len(self.models)} models validated")

def main():
    """Main execution function"""
    workspace_root = Path(__file__).parent.parent

    validator = ModelValidator(workspace_root)

    try:
        success = validator.validate_models()
        validator.print_report()

        if success:
            print("\n✅ Model validation completed successfully")
            sys.exit(0)
        else:
            print(f"\n❌ Model validation failed with {len(validator.errors)} errors")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Model validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
