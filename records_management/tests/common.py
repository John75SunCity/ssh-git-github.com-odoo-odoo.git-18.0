"""
Common test utilities and patterns for Records Management tests.

This module provides shared utilities that help with:
- Test data creation
- Common assertions
- Mock objects
- Test fixtures

Usage in test files:
    from .common import RecordsManagementTestCase

    class TestMyModel(RecordsManagementTestCase):
        def test_something(self):
            container = self.create_test_container()
            # ... test logic
"""

from odoo.tests.common import TransactionCase, Form
from odoo.exceptions import ValidationError, UserError, AccessError
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock
import json

class RecordsManagementTestCase(TransactionCase):
    """
    Base test case class for Records Management tests.

    Provides common test data and utility methods that can be used
    across all Records Management model tests.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test data once for all test methods"""
        super().setUpClass()

        # Disable tracking for better performance
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Common test data
        cls.setup_test_companies()
        cls.setup_test_users()
        cls.setup_test_partners()
        cls.setup_test_products()
        cls.setup_test_locations()
        cls.setup_test_containers()

    @classmethod
    def setup_test_companies(cls):
        """Set up test companies"""
        cls.main_company = cls.env.ref('base.main_company')
        cls.test_company = cls.env['res.company'].create({
            'name': 'Test Records Company',
            'currency_id': cls.env.ref('base.USD').id,
        })

    @classmethod
    def setup_test_users(cls):
        """Set up test users with different access levels"""
        cls.admin_user = cls.env.ref('base.user_admin')

        # Records management user
        cls.records_user = cls.env['res.users'].create({
            'name': 'Records User',
            'login': 'records_user',
            'email': 'records@test.com',
            'groups_id': [(6, 0, [cls.env.ref('records_management.group_records_user').id])]
        })

        # Records management manager
        cls.records_manager = cls.env['res.users'].create({
            'name': 'Records Manager',
            'login': 'records_manager',
            'email': 'manager@test.com',
            'groups_id': [(6, 0, [cls.env.ref('records_management.group_records_manager').id])]
        })

    @classmethod
    def setup_test_partners(cls):
        """Set up test partner records"""
        cls.customer_partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@test.com',
            'phone': '+1-555-0001',
            'is_company': True,
            'customer_rank': 1,
        })

        cls.vendor_partner = cls.env['res.partner'].create({
            'name': 'Test Vendor',
            'email': 'vendor@test.com',
            'phone': '+1-555-0002',
            'is_company': True,
            'supplier_rank': 1,
        })

    @classmethod
    def setup_test_products(cls):
        """Set up test product records"""
        cls.storage_product = cls.env['product.product'].create({
            'name': 'Records Storage Service',
            'type': 'service',
            'list_price': 10.0,
            'standard_price': 8.0,
        })

        cls.destruction_product = cls.env['product.product'].create({
            'name': 'Document Destruction Service',
            'type': 'service',
            'list_price': 25.0,
            'standard_price': 20.0,
        })

    @classmethod
    def setup_test_locations(cls):
        """Set up test location records"""
        if cls.env['records.location']._name in cls.env:
            cls.main_location = cls.env['records.location'].create({
                'name': 'Main Storage Facility',
                'code': 'MAIN-001',
                'capacity': 1000.0,
                'security_level': 'high',
                'active': True,
            })

            cls.secondary_location = cls.env['records.location'].create({
                'name': 'Secondary Storage',
                'code': 'SEC-001',
                'capacity': 500.0,
                'security_level': 'medium',
                'active': True,
            })

    @classmethod
    def setup_test_containers(cls):
        """Set up test container records"""
        if cls.env['records.container']._name in cls.env:
            cls.test_container = cls.env['records.container'].create({
                'name': 'TEST-BOX-001',
                'container_type': 'TYPE 01',
                'partner_id': cls.customer_partner.id,
                'location_id': cls.main_location.id if hasattr(cls, 'main_location') else False,
                'status': 'active',
            })

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def create_test_container(self, **kwargs):
        """Create a test container with default values"""
        default_values = {
            'name': f'TEST-BOX-{self.env["ir.sequence"].next_by_code("test.sequence") or "001"}',
            'container_type': 'TYPE 01',
            'partner_id': self.customer_partner.id,
            'status': 'active',
        }

        if hasattr(self, 'main_location') and self.main_location:
            default_values['location_id'] = self.main_location.id

        default_values.update(kwargs)
        return self.env['records.container'].create(default_values)

    def create_test_work_order(self, **kwargs):
        """Create a test work order with default values"""
        default_values = {
            'name': f'WO-{self.env["ir.sequence"].next_by_code("test.sequence") or "001"}',
            'partner_id': self.customer_partner.id,
            'state': 'draft',
        }
        default_values.update(kwargs)
        return self.env['document.retrieval.work.order'].create(default_values)

    def create_test_invoice(self, **kwargs):
        """Create a test invoice with default values"""
        default_values = {
            'move_type': 'out_invoice',
            'partner_id': self.customer_partner.id,
            'invoice_date': date.today(),
        }
        default_values.update(kwargs)
        return self.env['account.move'].create(default_values)

    def create_test_invoice_line(self, move_id=None, **kwargs):
        """Create a test invoice line with default values"""
        if not move_id:
            invoice = self.create_test_invoice()
            move_id = invoice.id

        default_values = {
            'move_id': move_id,
            'product_id': self.storage_product.id,
            'quantity': 1.0,
            'price_unit': 10.0,
        }
        default_values.update(kwargs)
        return self.env['account.move.line'].create(default_values)

    # ========================================================================
    # ASSERTION HELPERS
    # ========================================================================

    def assertRecordValues(self, records, expected_values):
        """
        Assert that records have expected field values.

        Args:
            records: Recordset to check
            expected_values: List of dicts with expected field values
        """
        self.assertEqual(len(records), len(expected_values))

        for record, expected in zip(records, expected_values):
            for field, value in expected.items():
                self.assertEqual(record[field], value,
                    f"Field {field} expected {value}, got {record[field]}")

    def assertValidationError(self, expected_message, callable_obj, *args, **kwargs):
        """
        Assert that a ValidationError is raised with expected message.

        Args:
            expected_message: Expected error message (can be partial)
            callable_obj: Function/method to call
            *args, **kwargs: Arguments to pass to callable
        """
        with self.assertRaises(ValidationError) as cm:
            callable_obj(*args, **kwargs)

        self.assertIn(expected_message.lower(), str(cm.exception).lower())

    def assertUserError(self, expected_message, callable_obj, *args, **kwargs):
        """
        Assert that a UserError is raised with expected message.

        Args:
            expected_message: Expected error message (can be partial)
            callable_obj: Function/method to call
            *args, **kwargs: Arguments to pass to callable
        """
        with self.assertRaises(UserError) as cm:
            callable_obj(*args, **kwargs)

        self.assertIn(expected_message.lower(), str(cm.exception).lower())

    def assertAccessError(self, callable_obj, *args, **kwargs):
        """
        Assert that an AccessError is raised.

        Args:
            callable_obj: Function/method to call
            *args, **kwargs: Arguments to pass to callable
        """
        with self.assertRaises(AccessError):
            callable_obj(*args, **kwargs)

    # ========================================================================
    # MOCK HELPERS
    # ========================================================================

    def mock_email_send(self):
        """Mock email sending to prevent actual emails during tests"""
        return patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail')

    def mock_sms_send(self):
        """Mock SMS sending to prevent actual SMS during tests"""
        return patch('odoo.addons.sms.models.sms_sms.SmsSms._send')

    def mock_external_api(self, return_value=None):
        """Mock external API calls"""
        return patch('requests.post', return_value=MagicMock(
            status_code=200,
            json=lambda: return_value or {'success': True}
        ))

    # ========================================================================
    # DATA VALIDATION HELPERS
    # ========================================================================

    def validate_required_fields(self, model_name, exclude_fields=None):
        """
        Test that all required fields raise ValidationError when missing.

        Args:
            model_name: Name of the model to test
            exclude_fields: List of fields to exclude from testing
        """
        exclude_fields = exclude_fields or []
        model = self.env[model_name]

        # Get required fields
        required_fields = []
        for field_name, field in model._fields.items():
            if field.required and field_name not in exclude_fields:
                required_fields.append(field_name)

        # Test each required field
        for field_name in required_fields:
            with self.subTest(field=field_name):
                with self.assertRaises(ValidationError):
                    model.create({})  # Should fail without required field

    def validate_field_constraints(self, record, field_name, valid_values, invalid_values):
        """
        Test field constraints with valid and invalid values.

        Args:
            record: Record to test
            field_name: Name of field to test
            valid_values: List of values that should be accepted
            invalid_values: List of values that should raise ValidationError
        """
        # Test valid values
        for value in valid_values:
            with self.subTest(value=value, valid=True):
                record.write({field_name: value})  # Should not raise error

        # Test invalid values
        for value in invalid_values:
            with self.subTest(value=value, valid=False):
                with self.assertRaises(ValidationError):
                    record.write({field_name: value})

    # ========================================================================
    # PERFORMANCE HELPERS
    # ========================================================================

    def measure_query_count(self, func, *args, **kwargs):
        """
        Measure the number of database queries executed by a function.

        Args:
            func: Function to measure
            *args, **kwargs: Arguments to pass to function

        Returns:
            Tuple of (result, query_count)
        """
        with self.assertQueryCount():
            result = func(*args, **kwargs)

        # Get query count from context
        query_count = getattr(self, '_query_count', 0)
        return result, query_count

    def create_bulk_test_data(self, model_name, count=100, **base_values):
        """
        Create bulk test data for performance testing.

        Args:
            model_name: Name of model to create records for
            count: Number of records to create
            **base_values: Base values for all records

        Returns:
            Created recordset
        """
        model = self.env[model_name]

        # Prepare bulk data
        bulk_data = []
        for i in range(count):
            data = dict(base_values)
            # Add sequence number to make records unique
            if 'name' in data:
                data['name'] = f"{data['name']}-{i:03d}"
            bulk_data.append(data)

        # Bulk create
        return model.create(bulk_data)
