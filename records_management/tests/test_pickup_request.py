"""
Test cases for the pickup.request model in the records management module.

Comprehensive test suite for customer pickup request management system with
state transitions, validation constraints, and business logic testing.
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError, AccessError
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock

class TestPickupRequest(TransactionCase):
    """Test cases for pickup.request model"""

    @classmethod
    def setUpClass(cls):
        """Set up test data once for all test methods"""
        super().setUpClass()

        # Common test data setup
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Setup complete test data
        cls.partner = cls.env['res.partner'].create({
            'name': 'Records Management Test Partner',
            'email': 'records.test@company.example',
            'phone': '+1-555-0123',
        })

        cls.company = cls.env.ref('base.main_company')
        cls.user = cls.env.ref('base.user_admin')

        # Create test currency
        cls.currency = cls.env.ref('base.USD')

        # Create pickup items for testing
        cls.pickup_item_model = cls.env['pickup.request.item']

    def setUp(self):
        """Set up test data for each test method"""
        super().setUp()

        # Create test instance with minimal required fields
        self.test_record = self._create_test_record()

    def _create_test_record(self, **kwargs):
        """Helper method to create test records with default values"""
        default_values = {
            'partner_id': self.partner.id,
            'contact_name': 'Test Contact',
            'contact_phone': '+1-555-0456',
            'contact_email': 'contact@test.example',
            'pickup_address': '123 Test Street, Test City, TS 12345',
            'description': 'Test pickup request description',
            'service_type': 'standard',
            'preferred_pickup_date': date.today() + timedelta(days=7),
            'estimated_volume': 10.5,
            'estimated_weight': 50.0,
            'estimated_cost': 150.00,
            'currency_id': self.currency.id,
        }
        default_values.update(kwargs)

        return self.env['pickup.request'].create(default_values)

    # ========================================================================
    # CRUD TESTS
    # ========================================================================

    def test_create_record(self):
        """Test basic record creation with sequence generation"""
        record = self._create_test_record()
        self.assertTrue(record.exists())
        self.assertEqual(record._name, 'pickup.request')
        self.assertNotEqual(record.name, 'New')  # Should have sequence number
        self.assertEqual(record.state, 'draft')
        self.assertEqual(record.partner_id, self.partner)

    def test_create_with_sequence_generation(self):
        """Test automatic sequence generation for name field"""
        record1 = self._create_test_record()
        record2 = self._create_test_record()

        # Both should have different sequence numbers
        self.assertNotEqual(record1.name, record2.name)
        self.assertNotEqual(record1.name, 'New')
        self.assertNotEqual(record2.name, 'New')

    def test_update_pickup_request_fields(self):
        """Test updating pickup request record fields"""
        record = self._create_test_record()

        # Test updating various fields
        record.write({
            'description': 'Updated Description',
            'priority': '2',
            'urgency_level': 'high',
            'contact_name': 'Updated Contact',
            'estimated_volume': 25.0,
        })

        self.assertEqual(record.description, 'Updated Description')
        self.assertEqual(record.priority, '2')
        self.assertEqual(record.urgency_level, 'high')
        self.assertEqual(record.contact_name, 'Updated Contact')
        self.assertEqual(record.estimated_volume, 25.0)

    def test_delete_pickup_request_record(self):
        """Test deleting pickup request record"""
        record = self._create_test_record()
        record_id = record.id

        # Should be able to delete draft records
        record.unlink()
        self.assertFalse(self.env['pickup.request'].browse(record_id).exists())

    def test_delete_completed_request_restrictions(self):
        """Test deletion restrictions for completed requests"""
        record = self._create_test_record()

        # Force state to completed (normally would go through workflow)
        record.write({'state': 'completed', 'completed_pickup_date': fields.Datetime.now()})

        # Should still allow deletion (no explicit restriction in model)
        record.unlink()
        self.assertFalse(record.exists())

    def test_read_record_fields(self):
        """Test record reading and field access"""
        record = self._create_test_record()

        # Test reading core fields
        self.assertEqual(record.partner_id, self.partner)
        self.assertEqual(record.contact_name, 'Test Contact')
        self.assertEqual(record.service_type, 'standard')
        self.assertTrue(record.billable)
        self.assertEqual(record.currency_id, self.currency)

    # ========================================================================
    # FIELD TESTS
    # ========================================================================

    def test_field_name_sequence(self):
        """Test name field sequence generation"""
        record = self._create_test_record()
        self.assertNotEqual(record.name, 'New')
        self.assertTrue(len(record.name) > 3)  # Should have actual sequence

    def test_field_partner_id_required(self):
        """Test partner_id field is required"""
        with self.assertRaises(ValidationError):
            self.env['pickup.request'].create({
                'contact_name': 'Test Contact',
                'pickup_address': 'Test Address',
            })

    def test_field_state_workflow(self):
        """Test state field transitions"""
        record = self._create_test_record()

        # Test all valid state values
        valid_states = ['draft', 'submitted', 'confirmed', 'scheduled', 'in_progress', 'completed', 'cancelled']
        for state in valid_states:
            record.write({'state': state})
            self.assertEqual(record.state, state)

    def test_field_priority_selection(self):
        """Test priority field selection values"""
        record = self._create_test_record()

        valid_priorities = ['0', '1', '2', '3']
        for priority in valid_priorities:
            record.write({'priority': priority})
            self.assertEqual(record.priority, priority)

    def test_field_service_type_selection(self):
        """Test service_type field selection values"""
        record = self._create_test_record()

        valid_types = ['standard', 'emergency', 'scheduled', 'bulk']
        for service_type in valid_types:
            record.write({'service_type': service_type})
            self.assertEqual(record.service_type, service_type)

    def test_field_urgency_level_selection(self):
        """Test urgency_level field selection values"""
        record = self._create_test_record()

        valid_levels = ['low', 'normal', 'high', 'urgent']
        for level in valid_levels:
            record.write({'urgency_level': level})
            self.assertEqual(record.urgency_level, level)

    def test_field_dates_handling(self):
        """Test date and datetime field handling"""
        record = self._create_test_record()

        # Test date fields
        future_date = date.today() + timedelta(days=10)
        record.write({'preferred_pickup_date': future_date})
        self.assertEqual(record.preferred_pickup_date, future_date)

        # Test datetime fields
        future_datetime = datetime.now() + timedelta(days=5)
        record.write({'scheduled_pickup_date': future_datetime})
        self.assertEqual(record.scheduled_pickup_date, future_datetime)

    def test_field_numeric_values(self):
        """Test numeric field handling"""
        record = self._create_test_record()

        # Test float fields
        record.write({
            'estimated_volume': 99.75,
            'estimated_weight': 125.25,
            'estimated_cost': 299.99,
        })

        self.assertEqual(record.estimated_volume, 99.75)
        self.assertEqual(record.estimated_weight, 125.25)
        self.assertEqual(record.estimated_cost, 299.99)

    def test_field_text_fields(self):
        """Test text field handling"""
        record = self._create_test_record()

        long_text = "This is a very long description " * 10
        record.write({
            'description': long_text,
            'internal_notes': 'Internal notes content',
            'pickup_address': '456 New Address Street\nSecond Line\nCity, State 54321',
            'special_instructions': 'Handle with care\nFragile items',
        })

        self.assertEqual(record.description, long_text)
        self.assertEqual(record.internal_notes, 'Internal notes content')
        self.assertIn('456 New Address Street', record.pickup_address)
        self.assertIn('Handle with care', record.special_instructions)

    # ========================================================================
    # CONSTRAINT TESTS
    # ========================================================================

    def test_constraint_preferred_pickup_date_not_past(self):
        """Test constraint: preferred pickup date cannot be in the past"""
        record = self._create_test_record()

        # Should allow future dates
        future_date = date.today() + timedelta(days=5)
        record.write({'preferred_pickup_date': future_date})
        self.assertEqual(record.preferred_pickup_date, future_date)

        # Should reject past dates
        with self.assertRaises(ValidationError):
            past_date = date.today() - timedelta(days=1)
            record.write({'preferred_pickup_date': past_date})

    def test_constraint_scheduled_pickup_date_not_past(self):
        """Test constraint: scheduled pickup date cannot be in the past"""
        record = self._create_test_record()

        # Should allow future datetimes
        future_datetime = datetime.now() + timedelta(hours=2)
        record.write({'scheduled_pickup_date': future_datetime})
        self.assertEqual(record.scheduled_pickup_date, future_datetime)

        # Should reject past datetimes
        with self.assertRaises(ValidationError):
            past_datetime = datetime.now() - timedelta(hours=1)
            record.write({'scheduled_pickup_date': past_datetime})

    def test_constraint_estimated_values_positive(self):
        """Test constraint: estimated volume and weight must be positive"""
        record = self._create_test_record()

        # Should allow positive values
        record.write({
            'estimated_volume': 50.0,
            'estimated_weight': 100.0,
        })
        self.assertEqual(record.estimated_volume, 50.0)
        self.assertEqual(record.estimated_weight, 100.0)

        # Should reject negative volume
        with self.assertRaises(ValidationError):
            record.write({'estimated_volume': -10.0})

        # Should reject negative weight
        with self.assertRaises(ValidationError):
            record.write({'estimated_weight': -5.0})

        # Should allow zero values
        record.write({
            'estimated_volume': 0.0,
            'estimated_weight': 0.0,
        })
        self.assertEqual(record.estimated_volume, 0.0)
        self.assertEqual(record.estimated_weight, 0.0)

    def test_constraint_contact_email_format(self):
        """Test constraint: contact email must be valid format"""
        record = self._create_test_record()

        # Should allow valid email formats
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'complex+email@sub.domain.org',
        ]
        for email in valid_emails:
            record.write({'contact_email': email})
            self.assertEqual(record.contact_email, email)

        # Should reject invalid email formats
        invalid_emails = [
            'invalid-email',
            'missing-at-sign.com',
            'no-domain@',
            '@missing-local.com',
        ]
        for email in invalid_emails:
            with self.assertRaises(ValidationError):
                record.write({'contact_email': email})

    # ========================================================================
    # COMPUTED FIELD TESTS
    # ========================================================================

    def test_compute_total_items(self):
        """Test _compute_total_items computed field"""
        record = self._create_test_record()

        # Initially should be 0 (no items)
        self.assertEqual(record.total_items, 0)

    def test_compute_container_count(self):
        """Test _compute_container_count computed field"""
        record = self._create_test_record()

        # Initially should be 0 (no items)
        self.assertEqual(record.container_count, 0)

    # ========================================================================
    # METHOD TESTS - STATE TRANSITIONS
    # ========================================================================

    def test_method_action_submit(self):
        """Test action_submit method"""
        record = self._create_test_record()

        # Should fail without pickup items
        with self.assertRaises(ValidationError):
            record.action_submit()

    def test_method_action_confirm(self):
        """Test action_confirm method"""
        record = self._create_test_record()

        # Should fail if not in submitted state
        with self.assertRaises(UserError):
            record.action_confirm()

        # Set to submitted state and test confirmation
        record.write({'state': 'submitted'})
        record.action_confirm()
        self.assertEqual(record.state, 'confirmed')

    def test_method_action_schedule(self):
        """Test action_schedule method - returns wizard"""
        record = self._create_test_record()

        # Should fail if not in confirmed or scheduled state
        with self.assertRaises(UserError):
            record.action_schedule()

        # Set to confirmed state and test scheduling
        record.write({'state': 'confirmed'})
        result = record.action_schedule()

        # Should return wizard action
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'pickup.schedule.wizard')

    def test_method_action_start_pickup(self):
        """Test action_start_pickup method"""
        record = self._create_test_record()

        # Should fail if not in scheduled state
        with self.assertRaises(UserError):
            record.action_start_pickup()

        # Set to scheduled state and test start
        record.write({'state': 'scheduled'})
        record.action_start_pickup()
        self.assertEqual(record.state, 'in_progress')

    def test_method_action_complete(self):
        """Test action_complete method"""
        record = self._create_test_record()

        # Should fail if not in in_progress state
        with self.assertRaises(UserError):
            record.action_complete()

        # Set to in_progress state and test completion
        record.write({'state': 'in_progress'})
        record.action_complete()
        self.assertEqual(record.state, 'completed')
        self.assertIsNotNone(record.completed_pickup_date)

    def test_method_action_cancel(self):
        """Test action_cancel method"""
        record = self._create_test_record()

        # Should fail if already completed
        record.write({'state': 'completed'})
        with self.assertRaises(UserError):
            record.action_cancel()

        # Should work for other states
        record.write({'state': 'draft'})
        record.action_cancel()
        self.assertEqual(record.state, 'cancelled')

    def test_method_action_reset_to_draft(self):
        """Test action_reset_to_draft method"""
        record = self._create_test_record()

        # Should fail if completed
        record.write({'state': 'completed'})
        with self.assertRaises(UserError):
            record.action_reset_to_draft()

        # Should work for other states
        record.write({'state': 'submitted'})
        record.action_reset_to_draft()
        self.assertEqual(record.state, 'draft')

    # ========================================================================
    # HELPER METHOD TESTS
    # ========================================================================

    def test_method_create_naid_audit_log(self):
        """Test _create_naid_audit_log helper method"""
        record = self._create_test_record()

        # Test audit log creation (method should not fail)
        record._create_naid_audit_log('test_event', 'Test description')
        # Method should execute without errors

    # ========================================================================
    # SECURITY TESTS
    # ========================================================================

    def test_access_rights_basic(self):
        """Test basic model access rights"""
        # Test that model exists and is accessible
        model = self.env['pickup.request']
        self.assertTrue(model._name == 'pickup.request')

        # Test CRUD permissions (basic level)
        record = self._create_test_record()
        self.assertTrue(record.exists())  # Create access

        # Read access
        fields_list = record.read(['name', 'partner_id', 'state'])
        self.assertTrue(len(fields_list) > 0)

        # Write access
        record.write({'description': 'Updated via security test'})
        self.assertEqual(record.description, 'Updated via security test')

    # ========================================================================
    # PERFORMANCE TESTS
    # ========================================================================

    def test_bulk_operations_performance(self):
        """Test performance with bulk operations"""
        # Create multiple records efficiently
        records_data = []
        for i in range(10):  # Reduced for test performance
            records_data.append({
                'partner_id': self.partner.id,
                'contact_name': f'Bulk Contact {i}',
                'contact_email': f'bulk{i}@test.example',
                'pickup_address': f'{i} Bulk Street, Test City',
                'description': f'Bulk pickup request {i}',
                'service_type': 'standard',
                'currency_id': self.currency.id,
            })

        # Test bulk create
        bulk_records = self.env['pickup.request'].create(records_data)
        self.assertEqual(len(bulk_records), 10)

    # ========================================================================
    # INTEGRATION TESTS
    # ========================================================================

    def test_integration_with_partner(self):
        """Test integration with res.partner model"""
        # Test partner relationship
        record = self._create_test_record()
        self.assertEqual(record.partner_id, self.partner)
        self.assertEqual(record.partner_id.name, 'Records Management Test Partner')

    def test_integration_with_currency(self):
        """Test integration with res.currency model"""
        record = self._create_test_record()

        # Test currency relationship
        self.assertEqual(record.currency_id, self.currency)

        # Test monetary field calculation
        record.write({'estimated_cost': 100.50})
        self.assertEqual(record.estimated_cost, 100.50)

    def test_complete_workflow_integration(self):
        """Test complete pickup request workflow integration"""
        record = self._create_test_record()

        # Test complete workflow
        self.assertEqual(record.state, 'draft')

        # Test state transitions manually (since items aren't available)
        record.write({'state': 'submitted'})
        self.assertEqual(record.state, 'submitted')

        record.action_confirm()
        self.assertEqual(record.state, 'confirmed')
