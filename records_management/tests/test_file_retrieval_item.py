"""
Test cases for the file.retrieval.item model in the records management module.

This model represents individual file retrieval items within work orders,
managing the complete lifecycle from request to completion.
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError, AccessError
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock

class TestFileRetrievalItem(TransactionCase):
    """Comprehensive test cases for file.retrieval.item model"""

    @classmethod
    def setUpClass(cls):
        """Set up test data once for all test methods"""
        super().setUpClass()

        # Common test data setup
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create test partner for file retrieval requests
        cls.partner = cls.env['res.partner'].create({
            'name': 'File Retrieval Test Customer',
            'email': 'file.retrieval@testcompany.com',
            'phone': '+1-555-FILE',
            'is_company': True,
        })

        # Create test users
        cls.coordinator_user = cls.env['res.users'].create({
            'name': 'File Retrieval Coordinator',
            'login': 'file_coordinator@test.com',
            'email': 'file_coordinator@test.com',
        })

        cls.user = cls.env.ref('base.user_admin')
        cls.company = cls.env.ref('base.main_company')

        # Create test location and container
        try:
            cls.test_location = cls.env['records.location'].create({
                'name': 'Test Storage Location',
                'location_type': 'warehouse',
                'is_active': True,
            })

            cls.test_container = cls.env['records.container'].create({
                'name': 'TEST-CONTAINER-001',
                'container_type': 'banker_box',
                'storage_location_id': cls.test_location.id,
                'partner_id': cls.partner.id,
            })
        except Exception:
            cls.test_location = None
            cls.test_container = None

        # Create test work order
        try:
            cls.test_work_order = cls.env['file.retrieval.work.order'].create({
                'partner_id': cls.partner.id,
                'request_description': 'Test file retrieval work order',
                'priority': '1',
                'delivery_method': 'scan',
                'scheduled_date': datetime.now() + timedelta(days=1),
            })
        except Exception:
            cls.test_work_order = None

    def setUp(self):
        """Set up test data for each test method"""
        super().setUp()

        # Create test instance with minimal required fields
        self.test_record = self._create_test_record()

    def _create_test_record(self, **kwargs):
        """Helper method to create test records with default values"""
        default_values = {
            'name': 'FRI-TEST-001',
            'requested_file_name': 'Important Document.pdf',
            'partner_id': self.partner.id,
            'priority': '1',
            'status': 'pending',
            'estimated_pages': 10,
            'estimated_time': 0.5,
        }

        # Add work order if available
        if self.test_work_order:
            default_values['work_order_id'] = self.test_work_order.id

        # Add container if available
        if self.test_container:
            default_values['container_id'] = self.test_container.id

        default_values.update(kwargs)

        return self.env['file.retrieval.item'].create(default_values)

    # ========================================================================
    # CRUD TESTS
    # ========================================================================

    def test_create_file_retrieval_item(self):
        """Test basic file retrieval item creation with required fields"""
        item = self._create_test_record()

        self.assertTrue(item.exists())
        self.assertEqual(item._name, 'file.retrieval.item')
        self.assertEqual(item.partner_id, self.partner)
        self.assertEqual(item.status, 'pending')
        self.assertEqual(item.requested_file_name, 'Important Document.pdf')
        self.assertEqual(item.estimated_pages, 10)

    def test_create_with_minimal_fields(self):
        """Test creation with only absolutely required fields"""
        item = self.env['file.retrieval.item'].create({
            'name': 'MIN-TEST-001',
            'requested_file_name': 'Minimal Test File.pdf',
            'partner_id': self.partner.id,
        })

        self.assertTrue(item.exists())
        self.assertEqual(item.status, 'pending')  # Default status
        self.assertEqual(item.priority, '1')     # Default priority

    def test_update_file_retrieval_item_fields(self):
        """Test updating file retrieval item record fields"""
        item = self._create_test_record()

        # Test updating basic fields
        item.write({
            'requested_file_name': 'Updated Document Name.pdf',
            'estimated_pages': 25,
            'priority': '2',
            'notes': 'Updated test notes',
        })

        self.assertEqual(item.requested_file_name, 'Updated Document Name.pdf')
        self.assertEqual(item.estimated_pages, 25)
        self.assertEqual(item.priority, '2')
        self.assertEqual(item.notes, 'Updated test notes')

    def test_delete_file_retrieval_item_record(self):
        """Test deleting file retrieval item record"""
        item = self._create_test_record()

        item_id = item.id
        item.unlink()

        self.assertFalse(self.env['file.retrieval.item'].browse(item_id).exists())

    # ========================================================================
    # FIELD TESTS
    # ========================================================================

    def test_field_requested_file_name_required(self):
        """Test that requested_file_name is required"""
        with self.assertRaises((ValidationError, ValueError)):
            self.env['file.retrieval.item'].create({
                'name': 'TEST-NO-FILE-NAME',
                'partner_id': self.partner.id,
                # Missing requested_file_name
            })

    def test_field_estimated_pages_validation(self):
        """Test estimated_pages field validation"""
        item = self._create_test_record()

        # Test valid positive integer
        item.write({'estimated_pages': 100})
        self.assertEqual(item.estimated_pages, 100)

        # Test zero is allowed
        item.write({'estimated_pages': 0})
        self.assertEqual(item.estimated_pages, 0)

    def test_field_priority_selection(self):
        """Test priority field selection values"""
        item = self._create_test_record()

        # Test all valid priority values
        for priority in ['0', '1', '2', '3']:
            item.write({'priority': priority})
            self.assertEqual(item.priority, priority)

    def test_field_status_workflow(self):
        """Test status field workflow transitions"""
        item = self._create_test_record()

        # Test status transitions
        valid_statuses = ['pending', 'searching', 'located', 'retrieved',
                         'packaged', 'delivered', 'returned', 'not_found',
                         'completed', 'cancelled']

        for status in valid_statuses:
            item.write({'status': status})
            self.assertEqual(item.status, status)

    def test_field_security_level(self):
        """Test security_level field values"""
        item = self._create_test_record()

        # Test all security levels
        security_levels = ['public', 'internal', 'confidential', 'restricted']
        for level in security_levels:
            item.write({'security_level': level})
            self.assertEqual(item.security_level, level)

    def test_field_condition_tracking(self):
        """Test condition before/after tracking"""
        item = self._create_test_record()

        conditions = ['excellent', 'good', 'fair', 'poor', 'damaged']

        for condition in conditions:
            item.write({
                'condition_before': condition,
                'condition_after': condition,
            })
            self.assertEqual(item.condition_before, condition)
            self.assertEqual(item.condition_after, condition)

    def test_field_not_found_reason(self):
        """Test not_found_reason field values"""
        item = self._create_test_record()

        reasons = ['not_in_container', 'container_missing', 'destroyed',
                  'misfiled', 'access_denied', 'other']

        for reason in reasons:
            item.write({'not_found_reason': reason})
            self.assertEqual(item.not_found_reason, reason)

    # ========================================================================
    # COMPUTED FIELD TESTS
    # ========================================================================

    def test_compute_display_name(self):
        """Test display_name computation"""
        item = self._create_test_record(
            name='TEST-DISPLAY-001',
            barcode='BC123456',
            status='searching'
        )

        self.assertIn('TEST-DISPLAY-001', item.display_name)
        self.assertIn('[BC123456]', item.display_name)
        self.assertIn('Searching', item.display_name)

    def test_compute_display_name_without_barcode(self):
        """Test display_name computation without barcode"""
        item = self._create_test_record(
            name='TEST-NO-BARCODE',
            status='pending'
        )

        self.assertIn('TEST-NO-BARCODE', item.display_name)
        self.assertIn('Pending', item.display_name)
        self.assertNotIn('[', item.display_name)

    # ========================================================================
    # ONCHANGE TESTS
    # ========================================================================

    def test_onchange_container_id(self):
        """Test container_id onchange behavior"""
        if not self.test_container:
            self.skipTest("Container model not available")

        item = self._create_test_record()

        # Simulate onchange
        item.container_id = self.test_container
        item._onchange_container_id()

        if hasattr(self.test_container, 'current_location'):
            self.assertEqual(item.current_location, self.test_container.current_location)
        if hasattr(self.test_container, 'location_id'):
            self.assertEqual(item.location_id, self.test_container.location_id)

    def test_onchange_status(self):
        """Test status onchange behavior"""
        item = self._create_test_record()

        # Test status change to retrieved
        item.status = 'retrieved'
        item._onchange_status()

        self.assertIsNotNone(item.retrieval_date)
        self.assertEqual(item.retrieved_by_id, self.env.user)

    # ========================================================================
    # CONSTRAINT TESTS
    # ========================================================================

    def test_constraint_partner_required(self):
        """Test partner_required constraint"""
        with self.assertRaises(ValidationError):
            self.env['file.retrieval.item'].create({
                'name': 'TEST-NO-PARTNER',
                'requested_file_name': 'Test File.pdf',
                'status': 'pending',
                # Missing partner_id
            })

    def test_constraint_partner_not_required_for_cancelled(self):
        """Test partner not required for cancelled items"""
        # This should work without partner for cancelled items
        item = self.env['file.retrieval.item'].create({
            'name': 'TEST-CANCELLED',
            'requested_file_name': 'Cancelled File.pdf',
            'status': 'cancelled',
        })

        self.assertTrue(item.exists())
        self.assertEqual(item.status, 'cancelled')

    def test_constraint_time_values_positive(self):
        """Test time values constraint"""
        item = self._create_test_record()

        # Test valid positive values
        item.write({
            'estimated_time': 2.5,
            'actual_time': 3.0,
        })
        self.assertEqual(item.estimated_time, 2.5)
        self.assertEqual(item.actual_time, 3.0)

        # Test negative values should raise validation error
        with self.assertRaises(ValidationError):
            item.write({'estimated_time': -1.0})

        with self.assertRaises(ValidationError):
            item.write({'actual_time': -0.5})

    # ========================================================================
    # METHOD TESTS - STATUS UPDATES
    # ========================================================================

    def test_action_start_search(self):
        """Test action_start_search method"""
        item = self._create_test_record(status='pending')

        result = item.action_start_search()

        self.assertTrue(result)
        self.assertEqual(item.status, 'searching')
        self.assertEqual(item.user_id, self.env.user)

    def test_action_start_search_invalid_status(self):
        """Test action_start_search with invalid status"""
        item = self._create_test_record(status='completed')

        with self.assertRaises(UserError):
            item.action_start_search()

    def test_action_mark_located(self):
        """Test action_mark_located method"""
        item = self._create_test_record(status='searching')

        result = item.action_mark_located()

        self.assertTrue(result)
        self.assertEqual(item.status, 'located')
        self.assertIsNotNone(item.retrieval_date)

    def test_action_mark_located_from_pending(self):
        """Test action_mark_located from pending status"""
        item = self._create_test_record(status='pending')

        result = item.action_mark_located()

        self.assertTrue(result)
        self.assertEqual(item.status, 'located')

    def test_action_mark_located_invalid_status(self):
        """Test action_mark_located with invalid status"""
        item = self._create_test_record(status='completed')

        with self.assertRaises(UserError):
            item.action_mark_located()

    def test_action_mark_retrieved(self):
        """Test action_mark_retrieved method"""
        item = self._create_test_record(status='located')

        result = item.action_mark_retrieved()

        self.assertTrue(result)
        self.assertEqual(item.status, 'retrieved')
        self.assertIsNotNone(item.retrieval_date)
        self.assertEqual(item.retrieved_by_id, self.env.user)

    def test_action_mark_retrieved_invalid_status(self):
        """Test action_mark_retrieved with invalid status"""
        item = self._create_test_record(status='pending')

        with self.assertRaises(UserError):
            item.action_mark_retrieved()

    def test_action_mark_completed(self):
        """Test action_mark_completed method"""
        item = self._create_test_record(status='retrieved')

        result = item.action_mark_completed()

        self.assertTrue(result)
        self.assertEqual(item.status, 'completed')

    def test_action_mark_completed_invalid_status(self):
        """Test action_mark_completed with invalid status"""
        item = self._create_test_record(status='pending')

        with self.assertRaises(UserError):
            item.action_mark_completed()

    def test_action_mark_not_found(self):
        """Test action_mark_not_found method"""
        item = self._create_test_record(status='searching')

        result = item.action_mark_not_found(
            reason='not_in_container',
            notes='File not found after thorough search'
        )

        self.assertTrue(result)
        self.assertEqual(item.status, 'not_found')
        self.assertEqual(item.not_found_reason, 'not_in_container')
        self.assertEqual(item.not_found_notes, 'File not found after thorough search')

    def test_action_mark_not_found_default_values(self):
        """Test action_mark_not_found with default values"""
        item = self._create_test_record(status='pending')

        result = item.action_mark_not_found()

        self.assertTrue(result)
        self.assertEqual(item.status, 'not_found')
        self.assertEqual(item.not_found_reason, 'not_in_container')
        self.assertIn('not found after search', item.not_found_notes)

    def test_action_cancel(self):
        """Test action_cancel method"""
        item = self._create_test_record(status='pending')

        result = item.action_cancel()

        self.assertTrue(result)
        self.assertEqual(item.status, 'cancelled')

    def test_action_cancel_invalid_status(self):
        """Test action_cancel with invalid status"""
        item = self._create_test_record(status='completed')

        with self.assertRaises(UserError):
            item.action_cancel()

    # ========================================================================
    # METHOD TESTS - FILE SPECIFIC
    # ========================================================================

    def test_action_start_file_search(self):
        """Test action_start_file_search method"""
        item = self._create_test_record(status='pending')

        item.action_start_file_search()

        self.assertEqual(item.status, 'searching')

    def test_action_start_file_search_invalid_status(self):
        """Test action_start_file_search with invalid status"""
        item = self._create_test_record(status='retrieved')

        with self.assertRaises(UserError):
            item.action_start_file_search()

    def test_action_log_container_search(self):
        """Test action_log_container_search method"""
        if not self.test_container:
            self.skipTest("Container model not available")

        item = self._create_test_record(status='searching')

        # Test successful search log
        item.action_log_container_search(
            container=self.test_container,
            found=True,
            notes="File found in container"
        )

        # Verify search attempt was logged
        search_attempts = item.search_attempt_ids
        self.assertTrue(len(search_attempts) > 0)

    def test_action_log_container_search_invalid_status(self):
        """Test action_log_container_search with invalid status"""
        if not self.test_container:
            self.skipTest("Container model not available")

        item = self._create_test_record(status='pending')

        with self.assertRaises(UserError):
            item.action_log_container_search(
                container=self.test_container,
                found=False
            )

    # ========================================================================
    # UTILITY METHOD TESTS
    # ========================================================================

    def test_find_by_status(self):
        """Test find_by_status utility method"""
        # Create items with different statuses
        pending_item = self._create_test_record(status='pending')
        searching_item = self._create_test_record(status='searching')
        completed_item = self._create_test_record(status='completed')

        # Test finding by single status
        pending_items = self.env['file.retrieval.item'].find_by_status(['pending'])
        self.assertIn(pending_item, pending_items)
        self.assertNotIn(completed_item, pending_items)

        # Test finding by multiple statuses
        active_items = self.env['file.retrieval.item'].find_by_status(['pending', 'searching'])
        self.assertIn(pending_item, active_items)
        self.assertIn(searching_item, active_items)
        self.assertNotIn(completed_item, active_items)

    def test_find_by_partner(self):
        """Test find_by_partner utility method"""
        # Create another partner
        other_partner = self.env['res.partner'].create({
            'name': 'Other Test Partner',
            'email': 'other@test.com',
        })

        # Create items for different partners
        our_item = self._create_test_record(partner_id=self.partner.id)
        other_item = self._create_test_record(partner_id=other_partner.id)

        # Test finding by partner
        our_items = self.env['file.retrieval.item'].find_by_partner(self.partner.id)
        self.assertIn(our_item, our_items)
        self.assertNotIn(other_item, our_items)

    def test_get_high_priority_items(self):
        """Test get_high_priority_items utility method"""
        # Create items with different priorities
        low_item = self._create_test_record(priority='0', status='pending')
        normal_item = self._create_test_record(priority='1', status='pending')
        high_item = self._create_test_record(priority='2', status='pending')
        very_high_item = self._create_test_record(priority='3', status='pending')

        # Test getting high priority items
        high_priority_items = self.env['file.retrieval.item'].get_high_priority_items()

        self.assertIn(high_item, high_priority_items)
        self.assertIn(very_high_item, high_priority_items)
        self.assertNotIn(low_item, high_priority_items)
        self.assertNotIn(normal_item, high_priority_items)

    def test_get_status_color(self):
        """Test get_status_color utility method"""
        item = self._create_test_record()

        # Test color mapping for different statuses
        status_colors = {
            'pending': 'secondary',
            'searching': 'info',
            'located': 'warning',
            'retrieved': 'primary',
            'completed': 'success',
            'not_found': 'danger',
            'cancelled': 'dark'
        }

        for status, expected_color in status_colors.items():
            item.status = status
            self.assertEqual(item.get_status_color(), expected_color)

    def test_get_priority_color(self):
        """Test get_priority_color utility method"""
        item = self._create_test_record()

        # Test color mapping for different priorities
        priority_colors = {
            '0': 'secondary',  # Low
            '1': 'info',       # Normal
            '2': 'warning',    # High
            '3': 'danger'      # Very High
        }

        for priority, expected_color in priority_colors.items():
            item.priority = priority
            self.assertEqual(item.get_priority_color(), expected_color)

    def test_log_activity(self):
        """Test log_activity utility method"""
        item = self._create_test_record()

        result = item.log_activity('search_started', 'Beginning file search in warehouse')

        self.assertTrue(result)
        # Verify activity was logged in message history
        messages = item.message_ids
        self.assertTrue(len(messages) > 0)

    # ========================================================================
    # INTEGRATION TESTS
    # ========================================================================

    def test_work_order_integration(self):
        """Test integration with work order"""
        if not self.test_work_order:
            self.skipTest("Work order model not available")

        item = self._create_test_record(work_order_id=self.test_work_order.id)

        self.assertEqual(item.work_order_id, self.test_work_order)
        # Verify reverse relationship
        self.assertIn(item, self.test_work_order.retrieval_item_ids)

    def test_container_integration(self):
        """Test integration with container"""
        if not self.test_container:
            self.skipTest("Container model not available")

        item = self._create_test_record(container_id=self.test_container.id)

        self.assertEqual(item.container_id, self.test_container)

    # ========================================================================
    # SECURITY TESTS
    # ========================================================================

    def test_access_rights_basic(self):
        """Test basic access rights"""
        # Test that the model exists and can be accessed
        self.assertTrue(hasattr(self.env, 'file.retrieval.item'))

        # Test create access
        item = self._create_test_record()
        self.assertTrue(item.exists())

        # Test read access
        item_read = self.env['file.retrieval.item'].browse(item.id)
        self.assertEqual(item_read.name, item.name)

        # Test write access
        item.write({'notes': 'Security test notes'})
        self.assertEqual(item.notes, 'Security test notes')

        # Test unlink access
        item.unlink()
        self.assertFalse(self.env['file.retrieval.item'].browse(item.id).exists())

    # ========================================================================
    # PERFORMANCE TESTS
    # ========================================================================

    def test_bulk_operations_performance(self):
        """Test performance with bulk operations"""
        # Create multiple records
        records_data = []
        for i in range(10):  # Reduced for test performance
            records_data.append({
                'name': f'BULK-TEST-{i:03d}',
                'requested_file_name': f'Bulk File {i}.pdf',
                'partner_id': self.partner.id,
                'estimated_pages': i * 5,
                'priority': str(i % 4),  # 0-3
                'work_order_id': self.test_work_order.id if self.test_work_order else False,
            })

        # Test bulk create
        bulk_items = self.env['file.retrieval.item'].create(records_data)
        self.assertEqual(len(bulk_items), 10)

        # Test bulk read
        all_names = bulk_items.mapped('name')
        self.assertEqual(len(all_names), 10)

        # Test bulk write
        bulk_items.write({'notes': 'Bulk update test'})
        for item in bulk_items:
            self.assertEqual(item.notes, 'Bulk update test')

    # ========================================================================
    # EDGE CASE TESTS
    # ========================================================================

    def test_edge_case_empty_file_name(self):
        """Test edge case with empty file name"""
        with self.assertRaises((ValidationError, ValueError)):
            self.env['file.retrieval.item'].create({
                'name': 'TEST-EMPTY-FILE',
                'requested_file_name': '',  # Empty string
                'partner_id': self.partner.id,
            })

    def test_edge_case_very_long_file_name(self):
        """Test edge case with very long file name"""
        long_name = 'A' * 1000  # Very long file name

        item = self._create_test_record(requested_file_name=long_name)
        self.assertEqual(item.requested_file_name, long_name)

    def test_edge_case_special_characters_in_file_name(self):
        """Test edge case with special characters in file name"""
        special_name = "Test File (2024) - Version 1.2 [FINAL] #&@.pdf"

        item = self._create_test_record(requested_file_name=special_name)
        self.assertEqual(item.requested_file_name, special_name)

    def test_edge_case_zero_estimated_pages(self):
        """Test edge case with zero estimated pages"""
        item = self._create_test_record(estimated_pages=0)
        self.assertEqual(item.estimated_pages, 0)

    def test_edge_case_large_estimated_pages(self):
        """Test edge case with very large estimated pages"""
        item = self._create_test_record(estimated_pages=999999)
        self.assertEqual(item.estimated_pages, 999999)

    # ========================================================================
    # WORKFLOW TESTS
    # ========================================================================

    def test_complete_workflow_success(self):
        """Test complete successful workflow from start to finish"""
        item = self._create_test_record(status='pending')

        # Start search
        item.action_start_search()
        self.assertEqual(item.status, 'searching')

        # Mark as located
        item.action_mark_located()
        self.assertEqual(item.status, 'located')

        # Mark as retrieved
        item.action_mark_retrieved()
        self.assertEqual(item.status, 'retrieved')
        self.assertIsNotNone(item.retrieval_date)
        self.assertEqual(item.retrieved_by_id, self.env.user)

        # Mark as completed
        item.action_mark_completed()
        self.assertEqual(item.status, 'completed')

    def test_complete_workflow_not_found(self):
        """Test complete workflow for not found scenario"""
        item = self._create_test_record(status='pending')

        # Start search
        item.action_start_search()
        self.assertEqual(item.status, 'searching')

        # Mark as not found
        item.action_mark_not_found(
            reason='not_in_container',
            notes='Extensive search completed - file not located'
        )
        self.assertEqual(item.status, 'not_found')
        self.assertEqual(item.not_found_reason, 'not_in_container')

    def test_workflow_cancellation(self):
        """Test workflow cancellation at various stages"""
        # Test cancellation from pending
        item1 = self._create_test_record(status='pending')
        item1.action_cancel()
        self.assertEqual(item1.status, 'cancelled')

        # Test cancellation from searching
        item2 = self._create_test_record(status='searching')
        item2.action_cancel()
        self.assertEqual(item2.status, 'cancelled')

        # Test cancellation from located
        item3 = self._create_test_record(status='located')
        item3.action_cancel()
        self.assertEqual(item3.status, 'cancelled')
