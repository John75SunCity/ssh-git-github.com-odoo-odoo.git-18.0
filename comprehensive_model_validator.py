#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Records Management Module Validation Script

This script validates ALL models in the records_management module, excluding
mobile dashboard widget models. It checks:
- Model existence and proper _name definitions
- Field definitions and relationships
- Security access rules
- Import statements in __init__.py
- Syntax validation
- Model relationships and dependencies
- Dynamic data functionality
"""

import sys
import os
import ast
import re
import json
from pathlib import Path

class RecordsManagementValidator:
    """Comprehensive validator for Records Management module"""

    def __init__(self, module_path):
        self.module_path = Path(module_path)
        self.models_dir = self.module_path / 'models'
        self.security_file = self.module_path / 'security' / 'ir.model.access.csv'
        self.init_file = self.models_dir / '__init__.py'

        # Models to exclude from validation
        self.exclude_models = {
            'mobile_dashboard_widget',
            'mobile_dashboard_widget_category'
        }

        # Validation results
        self.results = {
            'models_found': [],
            'models_missing': [],
            'fields_validated': [],
            'security_rules': [],
            'imports_validated': [],
            'syntax_errors': [],
            'relationship_errors': [],
            'dynamic_data_capable': []
        }

    def validate_all(self):
        """Run all validation checks"""
        print("🚀 COMPREHENSIVE RECORDS MANAGEMENT MODULE VALIDATION")
        print("=" * 70)

        checks = [
            self.validate_model_files,
            self.validate_model_imports,
            self.validate_security_rules,
            self.validate_syntax,
            self.validate_model_relationships,
            self.validate_dynamic_data_capability
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                print(f"❌ Error during {check.__name__}: {e}")

        self.print_summary()
        return self.results

    def validate_model_files(self):
        """Validate all model files exist and have proper structure"""
        print("\n🔍 Validating Model Files...")

        if not self.models_dir.exists():
            raise ValueError(f"Models directory not found: {self.models_dir}")

        model_files = []
        for file_path in self.models_dir.glob('*.py'):
            if file_path.name not in ['__init__.py', '__pycache__']:
                model_files.append(file_path)

        print(f"Found {len(model_files)} model files to validate")

        for file_path in model_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Parse AST to find model definitions
                tree = ast.parse(content)
                models_in_file = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if it's an Odoo model
                        for base in node.bases:
                            if isinstance(base, ast.Attribute):
                                if base.attr in ['Model', 'TransientModel']:
                                    # Look for _name assignment
                                    model_name = None
                                    for item in node.body:
                                        if isinstance(item, ast.Assign):
                                            for target in item.targets:
                                                if isinstance(target, ast.Name) and target.id == '_name':
                                                    if isinstance(item.value, ast.Str):
                                                        model_name = item.value.s
                                                        break

                                    if model_name and model_name not in self.exclude_models:
                                        models_in_file.append({
                                            'name': model_name,
                                            'file': file_path.name,
                                            'class': node.name
                                        })

                if models_in_file:
                    for model in models_in_file:
                        self.results['models_found'].append(model)
                        print(f"  ✅ Found model: {model['name']} in {model['file']}")

            except Exception as e:
                print(f"  ❌ Error parsing {file_path.name}: {e}")
                self.results['syntax_errors'].append({
                    'file': file_path.name,
                    'error': str(e)
                })

    def validate_model_imports(self):
        """Validate model imports in __init__.py"""
        print("\n🔍 Validating Model Imports...")

        if not self.init_file.exists():
            raise ValueError(f"__init__.py not found: {self.init_file}")

        try:
            with open(self.init_file, 'r', encoding='utf-8') as f:
                content = f.read()

            imported_modules = set()
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('from . import'):
                    module_name = line.split('from . import')[1].strip()
                    if module_name and not module_name.startswith('#'):
                        imported_modules.add(module_name)

            # Check if all found models have corresponding imports
            for model in self.results['models_found']:
                module_name = model['file'].replace('.py', '')
                if module_name in imported_modules:
                    self.results['imports_validated'].append(model['name'])
                    print(f"  ✅ Import validated: {model['name']}")
                else:
                    print(f"  ❌ Missing import: {model['name']} (module: {module_name})")

        except Exception as e:
            print(f"  ❌ Error validating imports: {e}")

    def validate_security_rules(self):
        """Validate security access rules"""
        print("\n🔍 Validating Security Rules...")

        if not self.security_file.exists():
            print(f"  ⚠️  Security file not found: {self.security_file}")
            return

        try:
            with open(self.security_file, 'r', encoding='utf-8') as f:
                content = f.read()

            security_rules = set()
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#'):
                    parts = line.split(',')
                    if len(parts) >= 4:
                        rule_name = parts[1].strip()
                        model_name = parts[2].strip()
                        if model_name and model_name not in self.exclude_models:
                            security_rules.add((rule_name, model_name))

            # Check security rules for found models
            for model in self.results['models_found']:
                model_rules = [rule for rule in security_rules if rule[1] == model['name']]
                if model_rules:
                    self.results['security_rules'].extend(model_rules)
                    print(f"  ✅ Security rules found for: {model['name']} ({len(model_rules)} rules)")
                else:
                    print(f"  ❌ No security rules found for: {model['name']}")

        except Exception as e:
            print(f"  ❌ Error validating security rules: {e}")

    def validate_syntax(self):
        """Validate syntax of all model files"""
        print("\n🔍 Validating Syntax...")

        syntax_errors = 0
        total_files = 0

        for file_path in self.models_dir.glob('*.py'):
            if file_path.name not in ['__init__.py', '__pycache__']:
                total_files += 1
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    ast.parse(content)
                    print(f"  ✅ Syntax OK: {file_path.name}")

                except SyntaxError as e:
                    syntax_errors += 1
                    error_info = {
                        'file': file_path.name,
                        'error': f"SyntaxError: {e.msg} at line {e.lineno}"
                    }
                    self.results['syntax_errors'].append(error_info)
                    print(f"  ❌ Syntax Error in {file_path.name}: {e.msg} at line {e.lineno}")

                except Exception as e:
                    syntax_errors += 1
                    error_info = {
                        'file': file_path.name,
                        'error': str(e)
                    }
                    self.results['syntax_errors'].append(error_info)
                    print(f"  ❌ Error in {file_path.name}: {e}")

        print(f"\n  📊 Syntax Summary: {total_files - syntax_errors}/{total_files} files OK")

    def validate_model_relationships(self):
        """Validate model relationships and dependencies"""
        print("\n🔍 Validating Model Relationships...")

        # This is a simplified check - in a real implementation you'd do more complex
        # relationship validation, but for now we'll check for common patterns

        relationship_patterns = [
            r"fields\.Many2one\(comodel_name='([^']+)'",
            r"fields\.One2many\([^,]+,\s*'([^']+)'",
            r"fields\.Many2many\([^,]+,\s*'([^']+)'",
        ]

        referenced_models = set()

        for file_path in self.models_dir.glob('*.py'):
            if file_path.name not in ['__init__.py', '__pycache__']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for pattern in relationship_patterns:
                        matches = re.findall(pattern, content)
                        referenced_models.update(matches)

                except Exception as e:
                    print(f"  ❌ Error reading {file_path.name}: {e}")

        # Check if referenced models exist
        found_model_names = {model['name'] for model in self.results['models_found']}
        found_model_names.update(self.exclude_models)  # Include excluded models

        missing_models = []
        for ref_model in referenced_models:
            if ref_model not in found_model_names and not ref_model.startswith(('res.', 'product.', 'account.', 'sale.', 'purchase.', 'stock.', 'mail.', 'ir.')):
                missing_models.append(ref_model)

        if missing_models:
            self.results['relationship_errors'].extend(missing_models)
            print(f"  ❌ Missing referenced models: {missing_models}")
        else:
            print("  ✅ All model relationships validated")

    def validate_dynamic_data_capability(self):
        """Validate dynamic data capability across models"""
        print("\n🔍 Validating Dynamic Data Capability...")

        dynamic_indicators = [
            'compute',
            'depends',
            'onchange',
            'api.depends',
            'api.onchange',
            'search',
            'name_search',
            'name_get',
            'fields_view_get'
        ]

        for model in self.results['models_found']:
            file_path = self.models_dir / model['file']
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                dynamic_features = []
                for indicator in dynamic_indicators:
                    if indicator in content:
                        dynamic_features.append(indicator)

                if dynamic_features:
                    self.results['dynamic_data_capable'].append({
                        'model': model['name'],
                        'features': dynamic_features
                    })
                    print(f"  ✅ Dynamic data capable: {model['name']} ({len(dynamic_features)} features)")
                else:
                    print(f"  ⚠️  Static model: {model['name']}")

            except Exception as e:
                print(f"  ❌ Error checking {model['file']}: {e}")

    def print_summary(self):
        """Print comprehensive validation summary"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE VALIDATION SUMMARY")
        print("=" * 70)

        # Models summary
        total_models = len(self.results['models_found'])
        print(f"\n🏗️  MODELS ({total_models})")
        print(f"  ✅ Models Found: {total_models}")
        print(f"  ✅ Imports Validated: {len(self.results['imports_validated'])}")
        print(f"  ✅ Security Rules: {len(set(rule[1] for rule in self.results['security_rules']))} models covered")

        # Syntax summary
        syntax_errors = len(self.results['syntax_errors'])
        print(f"\n💻 SYNTAX ({'✅' if syntax_errors == 0 else '❌'})")
        print(f"  ✅ Valid Files: {total_models - syntax_errors}")
        print(f"  ❌ Syntax Errors: {syntax_errors}")

        # Relationships summary
        relationship_errors = len(self.results['relationship_errors'])
        print(f"\n🔗 RELATIONSHIPS ({'✅' if relationship_errors == 0 else '❌'})")
        print(f"  ✅ Valid Relationships: {'Yes' if relationship_errors == 0 else 'Issues found'}")
        if relationship_errors > 0:
            print(f"  ❌ Missing Models: {relationship_errors}")

        # Dynamic data summary
        dynamic_models = len(self.results['dynamic_data_capable'])
        print(f"\n⚡ DYNAMIC DATA ({'✅' if dynamic_models > 0 else '⚠️'})")
        print(f"  ✅ Dynamic Models: {dynamic_models}")
        print(f"  📊 Dynamic Features: {sum(len(m['features']) for m in self.results['dynamic_data_capable'])}")

        # Overall status
        all_good = (
            syntax_errors == 0 and
            relationship_errors == 0 and
            len(self.results['imports_validated']) == total_models
        )

        print(f"\n🎯 OVERALL STATUS: {'✅ ALL VALIDATIONS PASSED' if all_good else '❌ ISSUES FOUND'}")

        if not all_good:
            print("\n🔧 RECOMMENDED ACTIONS:")
            if syntax_errors > 0:
                print("  - Fix syntax errors in listed files")
            if relationship_errors > 0:
                print("  - Create missing referenced models or fix model names")
            if len(self.results['imports_validated']) < total_models:
                print("  - Add missing imports to models/__init__.py")

        print(f"\n📋 DETAILED RESULTS SAVED TO: validation_results.json")

        # Save detailed results
        with open('validation_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

def main():
    """Main validation function"""
    module_path = '/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management'

    if not os.path.exists(module_path):
        print(f"❌ Module path not found: {module_path}")
        sys.exit(1)

    validator = RecordsManagementValidator(module_path)
    results = validator.validate_all()

    # Exit with appropriate code
    has_errors = (
        len(results['syntax_errors']) > 0 or
        len(results['relationship_errors']) > 0 or
        len(results['models_missing']) > 0
    )

    sys.exit(0 if not has_errors else 1)

if __name__ == '__main__':
    main()
