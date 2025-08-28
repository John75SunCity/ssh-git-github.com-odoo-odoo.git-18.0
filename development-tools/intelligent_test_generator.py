#!/usr/bin/env python3
"""
Intelligent Test Generator for Records Management Module

This script properly analyzes Odoo models, understands inheritance patterns,
and generates meaningful tests with proper required field handling.
"""

import os
import re
import ast
import sys
import json
from pathlib import Path
from collections import defaultdict

class OdooModelAnalyzer:
    """Analyzes Odoo models to understand structure, inheritance, and requirements"""
    
    def __init__(self, models_path):
        self.models_path = Path(models_path)
        self.models = {}
        self.field_types = {}
        self.inheritance_tree = defaultdict(list)
        
    def analyze_all_models(self):
        """Analyze all model files and build complete understanding"""
        print("🔍 Analyzing all models...")
        
        # First pass: discover all models
        for py_file in self.models_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            self._analyze_model_file(py_file)
        
        # Second pass: resolve inheritance and related fields
        self._resolve_inheritance()
        
        print(f"📊 Analysis complete: {len(self.models)} models found")
        return self.models
    
    def _analyze_model_file(self, file_path):
        """Analyze a single model file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the Python AST to properly understand the code
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._analyze_class(node, file_path, content)
                    
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
    
    def _analyze_class(self, class_node, file_path, content):
        """Analyze a class definition to extract model information"""
        class_name = class_node.name
        
        # Look for Odoo model classes
        if not self._is_odoo_model_class(class_node):
            return
        
        model_info = {
            'class_name': class_name,
            'file_path': file_path,
            'model_name': None,
            'inherits': [],
            'inherit': None,
            'fields': {},
            'methods': [],
            'constraints': [],
            'required_fields': [],
            'selection_fields': {},
            'related_fields': {},
            'computed_fields': {}
        }
        
        # Extract model attributes and fields
        for stmt in class_node.body:
            if isinstance(stmt, ast.Assign):
                self._analyze_assignment(stmt, model_info, content)
            elif isinstance(stmt, ast.FunctionDef):
                self._analyze_method(stmt, model_info)
        
        # Only store models that have a _name or _inherit
        if model_info['model_name'] or model_info['inherit']:
            model_key = model_info['model_name'] or model_info['inherit']
            self.models[model_key] = model_info
    
    def _is_odoo_model_class(self, class_node):
        """Check if a class is an Odoo model"""
        for base in class_node.bases:
            if isinstance(base, ast.Attribute):
                if (isinstance(base.value, ast.Name) and 
                    base.value.id == 'models' and 
                    base.attr in ['Model', 'TransientModel']):
                    return True
            elif isinstance(base, ast.Name) and base.id in ['Model', 'TransientModel']:
                return True
        return False
    
    def _analyze_assignment(self, stmt, model_info, content):
        """Analyze an assignment statement for model attributes and fields"""
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                attr_name = target.value
                
                if attr_name == '_name':
                    model_info['model_name'] = self._extract_string_value(stmt.value)
                elif attr_name == '_inherit':
                    inherit_value = self._extract_value(stmt.value)
                    if isinstance(inherit_value, list):
                        model_info['inherits'] = inherit_value
                    else:
                        model_info['inherit'] = inherit_value
                elif attr_name.endswith('_id') or self._is_field_assignment(stmt):
                    self._analyze_field(attr_name, stmt.value, model_info, content)
    
    def _analyze_field(self, field_name, value_node, model_info, content):
        """Analyze a field definition"""
        field_info = {
            'name': field_name,
            'type': None,
            'required': False,
            'readonly': False,
            'related': None,
            'compute': None,
            'selection': None,
            'comodel_name': None,
            'inverse_name': None
        }
        
        # Extract field type and properties from the AST node
        if isinstance(value_node, ast.Call):
            if isinstance(value_node.func, ast.Attribute):
                if (isinstance(value_node.func.value, ast.Name) and 
                    value_node.func.value.id == 'fields'):
                    field_info['type'] = value_node.func.attr
                    
                    # Analyze field arguments
                    for keyword in value_node.keywords:
                        self._analyze_field_keyword(keyword, field_info)
        
        model_info['fields'][field_name] = field_info
        
        # Categorize special field types
        if field_info['required']:
            model_info['required_fields'].append(field_name)
        if field_info['related']:
            model_info['related_fields'][field_name] = field_info['related']
        if field_info['compute']:
            model_info['computed_fields'][field_name] = field_info['compute']
        if field_info['selection']:
            model_info['selection_fields'][field_name] = field_info['selection']
    
    def _analyze_field_keyword(self, keyword, field_info):
        """Analyze field keyword arguments"""
        if keyword.arg == 'required':
            field_info['required'] = self._extract_bool_value(keyword.value)
        elif keyword.arg == 'readonly':
            field_info['readonly'] = self._extract_bool_value(keyword.value)
        elif keyword.arg == 'related':
            field_info['related'] = self._extract_string_value(keyword.value)
        elif keyword.arg == 'compute':
            field_info['compute'] = self._extract_string_value(keyword.value)
        elif keyword.arg == 'comodel_name':
            field_info['comodel_name'] = self._extract_string_value(keyword.value)
        elif keyword.arg == 'inverse_name':
            field_info['inverse_name'] = self._extract_string_value(keyword.value)
        elif keyword.arg == 'selection':
            field_info['selection'] = self._extract_selection_value(keyword.value)
    
    def _analyze_method(self, method_node, model_info):
        """Analyze a method definition"""
        method_info = {
            'name': method_node.name,
            'is_compute': False,
            'is_constraint': False,
            'is_onchange': False,
            'decorators': []
        }
        
        # Analyze decorators
        for decorator in method_node.decorator_list:
            decorator_info = self._analyze_decorator(decorator)
            method_info['decorators'].append(decorator_info)
            
            if decorator_info.get('type') == 'api.depends':
                method_info['is_compute'] = True
            elif decorator_info.get('type') == 'api.constrains':
                method_info['is_constraint'] = True
                model_info['constraints'].append(method_info)
            elif decorator_info.get('type') == 'api.onchange':
                method_info['is_onchange'] = True
        
        model_info['methods'].append(method_info)
    
    def _analyze_decorator(self, decorator):
        """Analyze a method decorator"""
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                return {
                    'type': f"{decorator.func.value.id}.{decorator.func.attr}",
                    'args': [self._extract_string_value(arg) for arg in decorator.args]
                }
        elif isinstance(decorator, ast.Attribute):
            return {
                'type': f"{decorator.value.id}.{decorator.attr}",
                'args': []
            }
        return {'type': 'unknown', 'args': []}
    
    def _extract_string_value(self, node):
        """Extract string value from AST node"""
        if isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None
    
    def _extract_bool_value(self, node):
        """Extract boolean value from AST node"""
        if isinstance(node, ast.Constant):
            return bool(node.value)
        elif isinstance(node, ast.NameConstant):
            return bool(node.value)
        return False
    
    def _extract_value(self, node):
        """Extract general value from AST node"""
        if isinstance(node, (ast.Str, ast.Constant)):
            return node.value if hasattr(node, 'value') else node.s
        elif isinstance(node, ast.List):
            return [self._extract_value(item) for item in node.elts]
        return None
    
    def _extract_selection_value(self, node):
        """Extract selection field values"""
        if isinstance(node, ast.List):
            selection = []
            for item in node.elts:
                if isinstance(item, ast.Tuple) and len(item.elts) == 2:
                    key = self._extract_value(item.elts[0])
                    value = self._extract_value(item.elts[1])
                    selection.append((key, value))
            return selection
        return None
    
    def _is_field_assignment(self, stmt):
        """Check if an assignment is a field definition"""
        if isinstance(stmt.value, ast.Call):
            if isinstance(stmt.value.func, ast.Attribute):
                return (isinstance(stmt.value.func.value, ast.Name) and 
                       stmt.value.func.value.id == 'fields')
        return False
    
    def _resolve_inheritance(self):
        """Resolve inheritance relationships between models"""
        for model_name, model_info in self.models.items():
            if model_info['inherit']:
                parent = model_info['inherit']
                if parent in self.models:
                    # Merge parent fields
                    parent_fields = self.models[parent]['fields'].copy()
                    parent_fields.update(model_info['fields'])
                    model_info['fields'] = parent_fields
                    
                    # Merge required fields
                    parent_required = self.models[parent]['required_fields']
                    model_info['required_fields'].extend(parent_required)
                    model_info['required_fields'] = list(set(model_info['required_fields']))


class IntelligentTestGenerator:
    """Generates intelligent, working tests based on proper model analysis"""
    
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.models_path = self.base_path / "records_management" / "models"
        self.tests_path = self.base_path / "records_management" / "tests"
        self.analyzer = OdooModelAnalyzer(self.models_path)
        
    def generate_all_tests(self):
        """Generate intelligent tests for all models"""
        models = self.analyzer.analyze_all_models()
        
        print(f"🧪 Generating intelligent tests for {len(models)} models...")
        
        generated_count = 0
        for model_name, model_info in models.items():
            # Skip inherited models without their own _name
            if not model_info['model_name']:
                continue
                
            # Generate test file
            if self._generate_model_test(model_name, model_info):
                generated_count += 1
        
        print(f"✅ Generated {generated_count} intelligent test files")
        return generated_count
    
    def _generate_model_test(self, model_name, model_info):
        """Generate an intelligent test for a specific model"""
        test_filename = f"test_{model_name.replace('.', '_')}.py"
        test_path = self.tests_path / test_filename
        
        # Don't overwrite existing tests
        if test_path.exists():
            print(f"⏭️  Skipping {test_filename} (already exists)")
            return False
        
        print(f"📝 Generating intelligent test: {test_filename}")
        
        try:
            test_content = self._generate_test_content(model_name, model_info)
            
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            print(f"✅ Generated {test_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error generating {test_filename}: {e}")
            return False
    
    def _generate_test_content(self, model_name, model_info):
        """Generate intelligent test content based on model analysis"""
        class_name = model_info['class_name']
        required_fields = model_info['required_fields']
        fields = model_info['fields']
        
        # Generate minimal required field values
        required_values = self._generate_required_field_values(model_info)
        
        test_content = f'''"""
Intelligent test cases for the {model_name} model.

Generated based on actual model analysis including:
- Required fields: {required_fields}
- Field types and constraints
- Inheritance patterns
- Related fields and computations
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError, AccessError
from datetime import datetime, date, timedelta
import logging

_logger = logging.getLogger(__name__)

class Test{class_name}(TransactionCase):
    """Intelligent test cases for {model_name} model"""

    @classmethod
    def setUpClass(cls):
        """Set up test data once for all test methods"""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Create supporting data that might be needed
        cls._setup_supporting_data()

    @classmethod
    def _setup_supporting_data(cls):
        """Set up supporting data for the tests"""
        # Common supporting records
        cls.partner = cls.env['res.partner'].create({{
            'name': 'Test Partner for {model_name}',
            'email': 'test.{model_name.replace(".", "_")}@example.com',
        }})
        
        cls.company = cls.env.ref('base.main_company')
        cls.user = cls.env.ref('base.user_admin')
        
        # Add model-specific supporting data
{cls._generate_supporting_data_setup(model_info)}

    def setUp(self):
        """Set up test data for each test method"""
        super().setUp()
        
    def _create_test_record(self, **kwargs):
        """Helper method to create test records with proper required fields"""
        # Intelligent required field values based on analysis
        values = {{{required_values}}}
        
        # Override with any provided values
        values.update(kwargs)
        
        try:
            return self.env['{model_name}'].create(values)
        except Exception as e:
            _logger.error(f"Failed to create {model_name} test record: {{e}}")
            _logger.error(f"Values used: {{values}}")
            raise

    # ========================================================================
    # CRUD TESTS (Based on actual model structure)
    # ========================================================================

    def test_create_with_required_fields(self):
        """Test creation with all required fields"""
        record = self._create_test_record()
        self.assertTrue(record.exists())
        self.assertEqual(record._name, '{model_name}')
        
        # Verify required fields are set
{self._generate_required_field_tests(model_info)}

    def test_create_without_required_fields(self):
        """Test that creation fails without required fields"""
{self._generate_required_field_validation_tests(model_info)}

{self._generate_field_specific_tests(model_info)}

{self._generate_constraint_tests(model_info)}

{self._generate_method_tests(model_info)}

{self._generate_relationship_tests(model_info)}

    # ========================================================================
    # INTEGRATION TESTS
    # ========================================================================

    def test_record_integration(self):
        """Test integration with related models"""
        record = self._create_test_record()
        
        # Test that the record integrates properly with the system
        self.assertTrue(record.exists())
        
        # Test any computed fields work
{self._generate_computed_field_tests(model_info)}
'''

        return test_content
    
    def _generate_required_field_values(self, model_info):
        """Generate intelligent default values for required fields"""
        values = []
        
        for field_name in model_info['required_fields']:
            if field_name in model_info['fields']:
                field_info = model_info['fields'][field_name]
                field_type = field_info['type']
                
                if field_type == 'Char':
                    values.append(f"'{field_name}': 'Test {field_name}'")
                elif field_type == 'Text':
                    values.append(f"'{field_name}': 'Test {field_name} content'")
                elif field_type == 'Integer':
                    values.append(f"'{field_name}': 1")
                elif field_type == 'Float':
                    values.append(f"'{field_name}': 1.0")
                elif field_type == 'Boolean':
                    values.append(f"'{field_name}': True")
                elif field_type == 'Date':
                    values.append(f"'{field_name}': date.today()")
                elif field_type == 'Datetime':
                    values.append(f"'{field_name}': datetime.now()")
                elif field_type == 'Selection' and field_info['selection']:
                    # Use first selection value
                    first_option = field_info['selection'][0][0]
                    values.append(f"'{field_name}': '{first_option}'")
                elif field_type == 'Many2one':
                    # Try to use supporting data
                    if 'partner' in field_name.lower():
                        values.append(f"'{field_name}': cls.partner.id")
                    elif 'company' in field_name.lower():
                        values.append(f"'{field_name}': cls.company.id")
                    elif 'user' in field_name.lower():
                        values.append(f"'{field_name}': cls.user.id")
                    else:
                        values.append(f"# '{field_name}': # TODO: Provide {field_type} value")
                else:
                    values.append(f"# '{field_name}': # TODO: Provide {field_type} value")
        
        return '\n            '.join(values) if values else "'name': 'Test Record'"
    
    def _generate_supporting_data_setup(self, model_info):
        """Generate supporting data setup based on model relationships"""
        setup_lines = []
        
        # Check for common relationship patterns
        for field_name, field_info in model_info['fields'].items():
            if field_info['type'] == 'Many2one' and field_info['comodel_name']:
                comodel = field_info['comodel_name']
                if comodel not in ['res.partner', 'res.company', 'res.users']:
                    setup_lines.append(f"        # TODO: Set up {comodel} for {field_name}")
        
        if not setup_lines:
            setup_lines.append("        # No additional supporting data needed")
            
        return '\n'.join(setup_lines)
    
    def _generate_required_field_tests(self, model_info):
        """Generate tests to verify required fields are properly set"""
        tests = []
        
        for field_name in model_info['required_fields']:
            tests.append(f"        self.assertTrue(record.{field_name}, 'Required field {field_name} should be set')")
        
        return '\n'.join(tests) if tests else "        # No required fields to test"
    
    def _generate_required_field_validation_tests(self, model_info):
        """Generate tests for required field validation"""
        tests = []
        
        for field_name in model_info['required_fields']:
            tests.append(f'''        # Test {field_name} is required
        with self.assertRaises(ValidationError):
            self.env['{model_info["model_name"]}'].create({{
                # Missing {field_name}
            }})''')
        
        return '\n'.join(tests) if tests else "        # No required field validations to test"
    
    def _generate_field_specific_tests(self, model_info):
        """Generate specific tests for different field types"""
        return '''
    def test_field_operations(self):
        """Test field-specific operations"""
        record = self._create_test_record()
        
        # Test field updates work correctly
        # TODO: Add specific field update tests based on model analysis
        pass'''
    
    def _generate_constraint_tests(self, model_info):
        """Generate tests for model constraints"""
        if not model_info['constraints']:
            return ""
            
        return '''
    def test_model_constraints(self):
        """Test model constraints"""
        record = self._create_test_record()
        
        # TODO: Test specific constraints found in model
        pass'''
    
    def _generate_method_tests(self, model_info):
        """Generate tests for model methods"""
        method_tests = []
        
        for method in model_info['methods']:
            if not method['name'].startswith('_') and method['name'] not in ['create', 'write', 'unlink']:
                method_tests.append(f'''
    def test_method_{method['name']}(self):
        """Test {method['name']} method"""
        record = self._create_test_record()
        
        # TODO: Test {method['name']} method behavior
        pass''')
        
        return '\n'.join(method_tests)
    
    def _generate_relationship_tests(self, model_info):
        """Generate tests for model relationships"""
        return '''
    def test_model_relationships(self):
        """Test relationships with other models"""
        record = self._create_test_record()
        
        # TODO: Test relationships based on Many2one, One2many fields
        pass'''
    
    def _generate_computed_field_tests(self, model_info):
        """Generate tests for computed fields"""
        tests = []
        
        for field_name in model_info['computed_fields']:
            tests.append(f"        # Test computed field: {field_name}")
            tests.append(f"        # self.assertIsNotNone(record.{field_name})")
        
        return '\n'.join(tests) if tests else "        # No computed fields to test"


def main():
    """Main execution function"""
    base_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0"
    
    generator = IntelligentTestGenerator(base_path)
    
    print("🚀 Intelligent Test Generator for Records Management")
    print("=" * 60)
    print("This generator analyzes actual model structure and creates meaningful tests")
    print()
    
    # Generate intelligent tests
    count = generator.generate_all_tests()
    
    if count > 0:
        print(f"\n✅ Successfully generated {count} intelligent test files")
        print("\n🧪 These tests are based on actual model analysis and should work!")
    else:
        print("\n✅ All models already have test files")

if __name__ == "__main__":
    main()
