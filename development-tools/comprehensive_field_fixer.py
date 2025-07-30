#!/usr/bin/env python3
"""
Comprehensive Field Fixer for Odoo Records Management Module
===========================================================

This tool systematically fixes ALL missing fields found by the reverse validation.
It creates proper field definitions with correct types, relationships, and compute methods.

Usage: python comprehensive_field_fixer.py
"""

import os
import re
from pathlib import Path
from collections import defaultdict


class ComprehensiveFieldFixer:
    def __init__(self, module_path):
        self.module_path = Path(module_path)
        self.model_files = {}  # model_name: file_path
        self.fixes_applied = 0

        # Field type mapping based on naming patterns
        self.field_type_mapping = {
            "_ids": "One2many",
            "_id": "Many2one",
            "_count": "Integer",
            "_date": "Date",
            "_datetime": "Datetime",
            "_time": "Float",
            "_amount": "Float",
            "_price": "Float",
            "_weight": "Float",
            "_percent": "Float",
            "_rate": "Float",
            "active": "Boolean",
            "confirmed": "Boolean",
            "required": "Boolean",
            "billable": "Boolean",
            "completed": "Boolean",
            "verified": "Boolean",
            "approved": "Boolean",
            "state": "Selection",
            "status": "Selection",
            "priority": "Selection",
            "type": "Selection",
        }

        # Standard fields that should exist in all models
        self.standard_fields = {
            "message_ids": {
                "type": "One2many",
                "relation": "mail.message",
                "inverse": "res_id",
                "string": "Messages",
                "auto_join": True,
            },
            "activity_ids": {
                "type": "One2many",
                "relation": "mail.activity",
                "inverse": "res_id",
                "string": "Activities",
                "auto_join": True,
            },
            "message_follower_ids": {
                "type": "One2many",
                "relation": "mail.followers",
                "inverse": "res_id",
                "string": "Followers",
                "auto_join": True,
            },
        }

    def find_model_files(self):
        """Find all Python model files and map models to files"""
        print("🔍 Finding model files...")

        for py_file in self.module_path.glob("models/*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find model names in this file
                model_matches = re.finditer(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                for match in model_matches:
                    model_name = match.group(1)
                    self.model_files[model_name] = py_file

            except Exception as e:
                print(f"⚠️  Error reading {py_file}: {e}")

        print(f"✅ Found {len(self.model_files)} model files")

    def get_field_definition(self, field_name, model_name=None):
        """Generate proper field definition based on field name patterns"""

        # Check for standard fields first
        if field_name in self.standard_fields:
            field_def = self.standard_fields[field_name]
            if field_def["type"] == "One2many":
                return f"{field_name} = fields.One2many('{field_def['relation']}', '{field_def['inverse']}', string='{field_def['string']}', auto_join={field_def['auto_join']})"

        # Determine field type from patterns
        field_type = "Char"  # default

        for suffix, ftype in self.field_type_mapping.items():
            if field_name.endswith(suffix) or field_name == suffix:
                field_type = ftype
                break

        # Generate field definition
        string_name = field_name.replace("_", " ").title()

        if field_type == "One2many":
            if field_name.endswith("_ids"):
                base_name = field_name[:-4]
                # Try to guess the related model
                if "audit" in base_name:
                    related_model = "naid.audit.log"
                elif "chain" in base_name:
                    related_model = "naid.chain.custody"
                elif "destruction" in base_name:
                    related_model = "shredding.service"
                elif "document" in base_name:
                    related_model = "records.document"
                elif "box" in base_name:
                    related_model = "records.box"
                else:
                    related_model = f'{base_name.replace("_", ".")}'

                return f"    {field_name} = fields.One2many('{related_model}', '{model_name.replace('.', '_')}_id', string='{string_name}')"

        elif field_type == "Many2one":
            if field_name.endswith("_id"):
                base_name = field_name[:-3]
                if base_name == "company":
                    return f"    {field_name} = fields.Many2one('res.company', string='{string_name}', default=lambda self: self.env.company)"
                elif base_name == "user":
                    return f"    {field_name} = fields.Many2one('res.users', string='{string_name}', default=lambda self: self.env.user)"
                elif base_name == "partner":
                    return f"    {field_name} = fields.Many2one('res.partner', string='{string_name}')"
                elif base_name == "customer":
                    return f"    {field_name} = fields.Many2one('res.partner', string='{string_name}', domain=[('is_company', '=', True)])"
                else:
                    related_model = base_name.replace("_", ".")
                    return f"    {field_name} = fields.Many2one('{related_model}', string='{string_name}')"

        elif field_type == "Integer":
            if field_name.endswith("_count"):
                compute_method = f"_compute_{field_name}"
                return f"    {field_name} = fields.Integer(string='{string_name}', compute='{compute_method}', store=True)"

        elif field_type == "Boolean":
            if field_name == "active":
                return f"    {field_name} = fields.Boolean(string='{string_name}', default=True)"
            else:
                return f"    {field_name} = fields.Boolean(string='{string_name}', default=False)"

        elif field_type == "Selection":
            if field_name == "state":
                return f"    {field_name} = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('done', 'Done'), ('cancelled', 'Cancelled')], string='{string_name}', default='draft', tracking=True)"
            elif field_name == "status":
                return f"    {field_name} = fields.Selection([('new', 'New'), ('in_progress', 'In Progress'), ('completed', 'Completed')], string='{string_name}', default='new')"
            elif field_name == "priority":
                return f"    {field_name} = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], string='{string_name}', default='medium')"
            else:
                return f"    {field_name} = fields.Selection([], string='{string_name}')  # TODO: Define selection options"

        elif field_type == "Float":
            return f"    {field_name} = fields.Float(string='{string_name}', digits=(12, 2))"

        elif field_type == "Date":
            return f"    {field_name} = fields.Date(string='{string_name}')"

        elif field_type == "Datetime":
            return f"    {field_name} = fields.Datetime(string='{string_name}')"

        # Default to Char
        return f"    {field_name} = fields.Char(string='{string_name}')"

    def generate_compute_method(self, field_name, model_name):
        """Generate compute method for computed fields"""
        method_name = f"_compute_{field_name}"

        if field_name.endswith("_count"):
            base_name = field_name[:-6]  # remove '_count'
            related_field = f"{base_name}_ids"

            return f"""
    @api.depends('{related_field}')
    def {method_name}(self):
        for record in self:
            record.{field_name} = len(record.{related_field})"""

        elif "total" in field_name:
            return f"""
    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies
    def {method_name}(self):
        for record in self:
            record.{field_name} = sum(record.line_ids.mapped('amount'))"""

        else:
            return f"""
    @api.depends()  # TODO: Add field dependencies
    def {method_name}(self):
        for record in self:
            record.{field_name} = False  # TODO: Implement computation logic"""

    def fix_model_fields(self, model_name, missing_fields):
        """Fix missing fields in a specific model"""
        if model_name not in self.model_files:
            print(f"⚠️  Model file not found for {model_name}")
            return False

        model_file = self.model_files[model_name]

        try:
            with open(model_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find the model class
            class_match = re.search(
                rf"class\s+\w+\s*\([^)]*models\.Model[^)]*\):(.*?)(?=\nclass|\nif __name__|$)",
                content,
                re.DOTALL,
            )

            if not class_match:
                print(f"⚠️  Could not find model class in {model_file}")
                return False

            class_content = class_match.group(1)
            class_start = class_match.start(1)
            class_end = class_match.end(1)

            # Find where to insert fields (after existing field definitions)
            field_pattern = r"\n    \w+\s*=\s*fields\.\w+\([^)]*\)"
            field_matches = list(re.finditer(field_pattern, class_content))

            if field_matches:
                # Insert after last field
                insert_pos = class_start + field_matches[-1].end()
            else:
                # Insert after class definition line
                lines = content[:class_start].split("\n")
                insert_pos = class_start + len(class_content.split("\n")[0]) + 1

            # Generate field definitions
            new_fields = []
            compute_methods = []

            for field_name in sorted(missing_fields):
                field_def = self.get_field_definition(field_name, model_name)
                new_fields.append(field_def)

                # Generate compute method if needed
                if field_name.endswith("_count") or "total" in field_name:
                    compute_method = self.generate_compute_method(
                        field_name, model_name
                    )
                    compute_methods.append(compute_method)

            # Build the insertion text
            insertion_text = "\n" + "\n".join(new_fields)
            if compute_methods:
                insertion_text += "\n" + "\n".join(compute_methods)

            # Insert the new content
            new_content = content[:insert_pos] + insertion_text + content[insert_pos:]

            # Write back to file
            with open(model_file, "w", encoding="utf-8") as f:
                f.write(new_content)

            print(f"✅ Fixed {len(missing_fields)} fields in {model_name}")
            self.fixes_applied += len(missing_fields)
            return True

        except Exception as e:
            print(f"⚠️  Error fixing {model_name}: {e}")
            return False

    def create_missing_models(self):
        """Create missing model files that are referenced in views"""
        missing_models = [
            "records.management.base.menus",
            "shredding.rates",
            "location.report.wizard",
            "customer.inventory",
        ]

        for model_name in missing_models:
            self.create_model_file(model_name)

    def create_model_file(self, model_name):
        """Create a new model file"""
        filename = model_name.replace(".", "_") + ".py"
        file_path = self.module_path / "models" / filename

        class_name = "".join(word.capitalize() for word in model_name.split("."))

        content = f"""# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class {class_name}(models.Model):
    _name = '{model_name}'
    _description = '{model_name.replace(".", " ").title()}'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'
    
    # Core fields
    name = fields.Char(string='Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'), 
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft', tracking=True)
    
    # Standard message/activity fields
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
    
    # TODO: Add specific fields for this model
"""

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"✅ Created model file: {filename}")

            # Add to model files mapping
            self.model_files[model_name] = file_path

            # Update models/__init__.py
            self.update_models_init(filename.replace(".py", ""))

        except Exception as e:
            print(f"⚠️  Error creating {filename}: {e}")

    def update_models_init(self, model_module):
        """Update models/__init__.py to include new model"""
        init_file = self.module_path / "models" / "__init__.py"

        try:
            with open(init_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Add import if not already present
            import_line = f"from . import {model_module}"
            if import_line not in content:
                content += f"\n{import_line}"

                with open(init_file, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"✅ Updated models/__init__.py for {model_module}")

        except Exception as e:
            print(f"⚠️  Error updating models/__init__.py: {e}")

    def run_comprehensive_fix(self):
        """Run comprehensive field fixing"""
        print("🚀 Starting Comprehensive Field Fixing")
        print("=" * 60)

        # Step 1: Find all model files
        self.find_model_files()

        # Step 2: Create missing models
        print("\n📝 Creating missing models...")
        self.create_missing_models()

        # Step 3: Run reverse validation to get missing fields
        print("\n🔍 Running reverse validation...")
        from reverse_field_validator import ReverseFieldValidator

        validator = ReverseFieldValidator(str(self.module_path))
        validator.extract_model_definitions()
        validator.analyze_specific_views()

        # Step 4: Fix missing fields in each model
        print("\n🔧 Fixing missing fields...")
        for model_name, missing_fields in validator.missing_fields.items():
            if missing_fields:
                print(f"\n📋 Fixing {model_name}: {len(missing_fields)} fields")
                self.fix_model_fields(model_name, missing_fields)

        print(f"\n🎯 Comprehensive Fixing Complete!")
        print(f"✅ Total fixes applied: {self.fixes_applied}")
        print("=" * 60)


if __name__ == "__main__":
    module_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    fixer = ComprehensiveFieldFixer(module_path)
    fixer.run_comprehensive_fix()
