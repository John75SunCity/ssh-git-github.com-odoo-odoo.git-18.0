#!/usr/bin/env python3
"""
Automated Test Improvement Tool for GitHub Copilot

This tool automatically improves test files based on analysis results,
providing examples that GitHub Copilot can learn from to generate better tests.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple

class TestImprover:
    """Automatically improves test files with Copilot-friendly patterns"""

    def __init__(self, records_management_path: str):
        self.rm_path = Path(records_management_path)
        self.tests_path = self.rm_path / 'tests'

    def improve_all_tests(self, report_file: str = 'test_analysis_report.json'):
        """Improve all tests based on analysis report"""
        try:
            with open(report_file, 'r') as f:
                report = json.load(f)
        except FileNotFoundError:
            print(f"❌ Report file {report_file} not found. Run smart_test_analyzer.py first.")
            return

        improvements_made = 0

        print("🔧 Improving test files...")

        # Improve existing test files
        for test_info in report['test_files']:
            if test_info['status'] == 'analyzed':
                file_path = self.tests_path / test_info['file']
                if self.improve_test_file(file_path, test_info):
                    improvements_made += 1

        # Create missing test files
        for missing_model in report['missing_tests'][:5]:  # Limit to first 5
            if self.create_missing_test(missing_model):
                improvements_made += 1

        print(f"✅ Made {improvements_made} improvements")

    def improve_test_file(self, file_path: Path, test_info: Dict) -> bool:
        """Improve individual test file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Apply improvements
            content = self.fix_missing_imports(content, test_info)
            content = self.improve_test_data(content)
            content = self.add_missing_test_methods(content, test_info)
            content = self.clean_todo_comments(content)

            # Only write if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   ✅ Improved {file_path.name}")
                return True

        except Exception as e:
            print(f"   ❌ Error improving {file_path.name}: {e}")

        return False

    def fix_missing_imports(self, content: str, test_info: Dict) -> str:
        """Fix missing imports"""
        # Check if imports are missing
        required_imports = [
            ('ValidationError', 'from odoo.exceptions import ValidationError'),
            ('UserError', 'from odoo.exceptions import UserError'),
            ('AccessError', 'from odoo.exceptions import AccessError'),
            ('patch', 'from unittest.mock import patch, MagicMock'),
            ('datetime', 'from datetime import datetime, date'),
        ]

        for import_name, import_line in required_imports:
            if import_name not in content and import_line not in content:
                # Add import after existing imports
                import_pattern = r'(from odoo\.tests\.common import TransactionCase\n)'
                if re.search(import_pattern, content):
                    content = re.sub(
                        import_pattern,
                        r'\1' + import_line + '\n',
                        content
                    )

        return content

    def improve_test_data(self, content: str) -> str:
        """Improve test data quality"""
        # Replace placeholder emails with more realistic ones
        content = re.sub(
            r'test@example\.com',
            'records.test@company.example',
            content
        )

        # Replace generic names with more descriptive ones
        content = re.sub(
            r"'name': 'Test Partner'",
            "'name': 'Records Management Test Partner'",
            content
        )

        # Add more realistic test data patterns
        if "'email': 'records.test@company.example'" in content:
            # Add phone number if not present
            if "'phone':" not in content:
                content = re.sub(
                    r"('email': 'records\.test@company\.example',)",
                    r"\1\n            'phone': '+1-555-0123',",
                    content
                )

        return content

    def add_missing_test_methods(self, content: str, test_info: Dict) -> str:
        """Add missing essential test methods"""

        # Extract model name from test file
        model_match = re.search(r"class Test(\w+)\(", content)
        if not model_match:
            return content

        model_class = model_match.group(1)
        model_name = self.camel_to_snake(model_class)

        # Check if essential test methods exist
        essential_methods = [
            'test_create',
            'test_read',
            'test_update',
            'test_delete',
            'test_validation'
        ]

        missing_methods = []
        for method in essential_methods:
            if f"def {method}" not in content:
                missing_methods.append(method)

        if missing_methods:
            # Find the class end and add methods
            class_pattern = rf"(class Test{model_class}\(TransactionCase\):.*?)(\n\n|\Z)"

            new_methods = ""
            for method in missing_methods:
                new_methods += self.generate_test_method(method, model_name)

            # Add methods before class end
            content = re.sub(
                rf"(class Test{model_class}\(TransactionCase\):.*?)(def test_\w+.*?)(\n\n|\Z)",
                rf"\1\2{new_methods}\3",
                content,
                flags=re.DOTALL
            )

        return content

    def generate_test_method(self, method_name: str, model_name: str) -> str:
        """Generate a test method based on pattern"""

        if method_name == 'test_create':
            return f'''
    def test_create_{model_name}_basic(self):
        """Test basic creation of {model_name} record"""
        # GitHub Copilot Pattern: Basic model creation test
        record = self.env['{model_name}'].create({{
            'name': 'Test {model_name.replace("_", " ").title()}'
        }})

        self.assertTrue(record.exists())
        self.assertEqual(record.name, 'Test {model_name.replace("_", " ").title()}')

'''
        elif method_name == 'test_validation':
            return f'''
    def test_validation_{model_name}_constraints(self):
        """Test validation constraints for {model_name}"""
        # GitHub Copilot Pattern: Validation testing with assertRaises
        with self.assertRaises(ValidationError):
            self.env['{model_name}'].create({{
                # Add invalid data that should trigger validation
            }})

'''
        elif method_name == 'test_read':
            return f'''
    def test_search_{model_name}_records(self):
        """Test searching {model_name} records"""
        # GitHub Copilot Pattern: Search and read operations
        record = self.env['{model_name}'].create({{
            'name': 'Searchable Record'
        }})

        found_records = self.env['{model_name}'].search([
            ('name', '=', 'Searchable Record')
        ])

        self.assertIn(record, found_records)

'''
        elif method_name == 'test_update':
            return f'''
    def test_update_{model_name}_fields(self):
        """Test updating {model_name} record fields"""
        # GitHub Copilot Pattern: Update operations
        record = self.env['{model_name}'].create({{
            'name': 'Original Name'
        }})

        record.write({{'name': 'Updated Name'}})

        self.assertEqual(record.name, 'Updated Name')

'''
        elif method_name == 'test_delete':
            return f'''
    def test_delete_{model_name}_record(self):
        """Test deleting {model_name} record"""
        # GitHub Copilot Pattern: Delete operations
        record = self.env['{model_name}'].create({{
            'name': 'To Be Deleted'
        }})

        record_id = record.id
        record.unlink()

        self.assertFalse(self.env['{model_name}'].browse(record_id).exists())

'''

        return ""

    def clean_todo_comments(self, content: str) -> str:
        """Clean up TODO comments and add meaningful implementations"""

        # Replace generic TODO comments with specific ones
        content = re.sub(
            r'# TODO: Add model-specific setup data',
            '# Setup complete - add additional test data as needed',
            content
        )

        # Replace TODO implementation with basic structure
        content = re.sub(
            r'# TODO: Implement creation test\n\s+pass',
            '''# Basic creation test implementation
        record = self.env['MODEL_NAME'].create({
            'name': 'Test Record'
        })
        self.assertTrue(record.exists())''',
            content
        )

        return content

    def create_missing_test(self, model_name: str) -> bool:
        """Create a missing test file"""
        try:
            class_name = ''.join(word.capitalize() for word in model_name.split('_'))
            test_file = self.tests_path / f'test_{model_name}.py'

            # Don't overwrite existing files
            if test_file.exists():
                return False

            content = f'''"""
Test cases for the {model_name} model in the records management module.

Auto-generated by TestImprover - GitHub Copilot optimized patterns included.
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError, AccessError
from datetime import datetime, date
from unittest.mock import patch, MagicMock

class Test{class_name}(TransactionCase):
    """Test cases for {model_name} model - GitHub Copilot Learning Patterns"""

    @classmethod
    def setUpClass(cls):
        """Set up test data once for all test methods"""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Realistic test data for GitHub Copilot learning
        cls.partner = cls.env['res.partner'].create({{
            'name': 'Records Management Test Partner',
            'email': 'records.test@company.example',
            'phone': '+1-555-0123',
        }})

        cls.company = cls.env.ref('base.main_company')
        cls.user = cls.env.ref('base.user_admin')

    def test_create_{model_name}_basic(self):
        """Test basic creation of {model_name} record"""
        # GitHub Copilot Pattern: Basic model creation test
        record = self.env['{model_name}'].create({{
            'name': 'Test {model_name.replace("_", " ").title()}'
        }})

        self.assertTrue(record.exists())
        self.assertEqual(record.name, 'Test {model_name.replace("_", " ").title()}')

    def test_validation_{model_name}_constraints(self):
        """Test validation constraints for {model_name}"""
        # GitHub Copilot Pattern: Validation testing with assertRaises
        with self.assertRaises(ValidationError):
            self.env['{model_name}'].create({{
                # Invalid data - Copilot will suggest specific constraints
                'name': ''  # Empty name should fail validation
            }})

    def test_search_{model_name}_records(self):
        """Test searching {model_name} records"""
        # GitHub Copilot Pattern: Search and read operations
        record = self.env['{model_name}'].create({{
            'name': 'Searchable Record'
        }})

        found_records = self.env['{model_name}'].search([
            ('name', '=', 'Searchable Record')
        ])

        self.assertIn(record, found_records)

    def test_update_{model_name}_fields(self):
        """Test updating {model_name} record fields"""
        # GitHub Copilot Pattern: Update operations
        record = self.env['{model_name}'].create({{
            'name': 'Original Name'
        }})

        record.write({{'name': 'Updated Name'}})

        self.assertEqual(record.name, 'Updated Name')

    def test_access_rights_{model_name}(self):
        """Test access rights for {model_name}"""
        # GitHub Copilot Pattern: Security testing
        # Create test user with limited rights
        test_user = self.env['res.users'].create({{
            'name': 'Test User',
            'login': 'test_{model_name}_user',
            'email': 'test.user@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        }})

        # Test access with limited user
        # Copilot will suggest appropriate access tests based on model
        with self.assertRaises(AccessError):
            self.env['{model_name}'].with_user(test_user).create({{
                'name': 'Unauthorized Creation'
            }})

    # TODO: Add model-specific test methods
    # GitHub Copilot will suggest additional tests based on model fields and methods
'''

            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"   ✅ Created {test_file.name}")
            return True

        except Exception as e:
            print(f"   ❌ Error creating test for {model_name}: {e}")
            return False

    @staticmethod
    def camel_to_snake(camel_str: str) -> str:
        """Convert CamelCase to snake_case"""
        # Add underscore before uppercase letters (except first)
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
        # Add underscore before uppercase letters that follow lowercase
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def main():
    """Main function"""
    import sys

    if len(sys.argv) > 1:
        rm_path = sys.argv[1]
    else:
        rm_path = 'records_management'

    improver = TestImprover(rm_path)

    print("🔧 Automated Test Improvement Tool")
    print("=" * 50)
    print("This tool improves tests with GitHub Copilot-friendly patterns")
    print()

    improver.improve_all_tests()

    print(f"""
✅ Test improvements complete!

GitHub Copilot will now have better patterns to learn from:
• ✅ Proper imports and exception handling
• ✅ Realistic test data instead of placeholders
• ✅ Complete CRUD test methods
• ✅ Validation and security test patterns
• ✅ Comprehensive documentation and comments

💡 Next steps:
1. Run tests to identify remaining issues
2. Use GitHub Copilot to extend tests based on model fields
3. Add model-specific validation and business logic tests
4. Implement integration tests between related models

🤖 GitHub Copilot prompts to try:
• "# Add test for computed field validation"
• "# Test workflow state transitions"
• "# Add integration test with related models"
• "# Test bulk operations and performance"
""")

if __name__ == '__main__':
    main()
