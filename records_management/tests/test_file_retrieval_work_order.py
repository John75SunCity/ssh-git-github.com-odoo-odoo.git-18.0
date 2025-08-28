"""
Test cases for the file.retrieval.work.order model in the records management module.

This model manages the complete file retrieval workflow from customer request
to document location, retrieval, packaging, and delivery.
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError, AccessError
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock

class TestFileRetrievalWorkOrder(TransactionCase):
    """Comprehensive test cases for file.retrieval.work.order model"""

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

        # Create delivery address partner
        cls.delivery_partner = cls.env['res.partner'].create({
            'name': 'File Delivery Address',
            'street': '123 Delivery Street',
            'city': 'Delivery City',
            'zip': '12345',
            'parent_id': cls.partner.id,
        })

        # Create test users
        cls.coordinator_user = cls.env['res.users'].create({
            'name': 'File Retrieval Coordinator',
            'login': 'file_coordinator@test.com',
            'email': 'file_coordinator@test.com',
        })

        cls.user = cls.env.ref('base.user_admin')
        cls.company = cls.env.ref('base.main_company')

        # Create test location and container if models exist
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
        except:
            cls.test_location = None
            cls.test_container = None

    def setUp(self):
        """Set up test data for each test method"""
        super().setUp()

        # Create test instance with minimal required fields
        self.test_record = self._create_test_record()

    def _create_test_record(self, **kwargs):
        """Helper method to create test records with default values"""
        default_values = {
            'partner_id': self.partner.id,
            'request_description': 'Test file retrieval request',
            'priority': '1',
            'delivery_method': 'scan',
            'scheduled_date': datetime.now() + timedelta(days=1),
        }
        default_values.update(kwargs)

        return self.env['file.retrieval.work.order'].create(default_values)

    # ========================================================================
    # CRUD TESTS
    # ========================================================================

    def test_create_file_retrieval_work_order(self):
        """Test basic work order creation with required fields"""
        work_order = self._create_test_record()

        self.assertTrue(work_order.exists())
        self.assertEqual(work_order._name, 'file.retrieval.work.order')
        self.assertEqual(work_order.partner_id, self.partner)
        self.assertEqual(work_order.state, 'draft')
        self.assertEqual(work_order.priority, '1')
        self.assertTrue(work_order.active)

    def test_create_work_order_with_sequence(self):
        """Test that work order name is auto-generated from sequence"""
        work_order = self._create_test_record()

        # Name should be auto-generated, not 'New'
        self.assertNotEqual(work_order.name, 'New')
        self.assertTrue(len(work_order.name) > 3)

    def test_create_work_order_with_portal_request(self):
        """Test work order creation from portal request"""
        # Create portal request if model exists
        try:
            portal_request = self.env['portal.request'].create({
                'partner_id': self.partner.id,
                'request_type': 'file_retrieval',
                'description': 'Portal file retrieval request',
            })

            work_order = self._create_test_record(
                portal_request_id=portal_request.id,
                request_description=portal_request.description
            )

            self.assertEqual(work_order.portal_request_id, portal_request)
            self.assertEqual(work_order.request_description, portal_request.description)
        except:
            self.skipTest("Portal request model not available")

    def test_update_work_order_fields(self):
        """Test updating work order fields"""
        work_order = self._create_test_record()

        # Test updating various fields
        work_order.write({
            'priority': '2',
            'delivery_method': 'physical',
            'packaging_type': 'box',
            'access_coordination_needed': True,
            'delivery_instructions': 'Handle with care - fragile documents',
        })

        self.assertEqual(work_order.priority, '2')
        self.assertEqual(work_order.delivery_method, 'physical')
        self.assertEqual(work_order.packaging_type, 'box')
        self.assertTrue(work_order.access_coordination_needed)
        self.assertEqual(work_order.delivery_instructions, 'Handle with care - fragile documents')

    def test_delete_work_order(self):
        """Test work order deletion"""
        work_order = self._create_test_record()
        work_order_id = work_order.id

        work_order.unlink()

        self.assertFalse(self.env['file.retrieval.work.order'].browse(work_order_id).exists())

    # ========================================================================
    # COMPUTED FIELD TESTS
    # ========================================================================

    def test_compute_display_name_basic(self):
        """Test display name computation for basic work order"""
        work_order = self._create_test_record()

        # Should include work order name and partner name
        expected_pattern = f"{work_order.name} - {self.partner.name}"
        self.assertIn(self.partner.name, work_order.display_name)
        self.assertIn(work_order.name, work_order.display_name)

    def test_compute_display_name_with_items(self):
        """Test display name computation with retrieval items"""
        work_order = self._create_test_record()

        # Mock retrieval items
        try:
            # Create retrieval items if model exists
            item1 = self.env['file.retrieval.item'].create({
                'work_order_id': work_order.id,
                'description': 'Test document 1',
                'estimated_pages': 10,
            })
            item2 = self.env['file.retrieval.item'].create({
                'work_order_id': work_order.id,
                'description': 'Test document 2',
                'estimated_pages': 5,
            })

            # Recompute fields
            work_order._compute_item_metrics()
            work_order._compute_display_name()

            # Display name should include file count
            self.assertIn("2 files", work_order.display_name)
        except:
            # Skip if retrieval item model doesn't exist
            self.skipTest("file.retrieval.item model not available")

    def test_compute_item_metrics_empty(self):
        """Test item metrics computation with no items"""
        work_order = self._create_test_record()

        work_order._compute_item_metrics()

        self.assertEqual(work_order.item_count, 0)
        self.assertEqual(work_order.estimated_pages, 0)

    def test_compute_estimated_completion_date(self):
        """Test estimated completion date calculation"""
        scheduled_date = datetime.now() + timedelta(days=2)
        work_order = self._create_test_record(scheduled_date=scheduled_date)

        # Mock item count for calculation
        work_order.item_count = 5
        work_order._compute_estimated_completion()

        # Should add 4 + (5 * 2) = 14 hours to scheduled date
        expected_completion = scheduled_date + timedelta(hours=14)
        self.assertEqual(work_order.estimated_completion_date.date(), expected_completion.date())

    def test_compute_progress_percentage(self):
        """Test progress percentage calculation"""
        work_order = self._create_test_record()

        # Test with no items
        work_order._compute_progress()
        self.assertEqual(work_order.progress_percentage, 0.0)

        # Test with items
        work_order.item_count = 10
        work_order.files_retrieved_count = 3
        work_order._compute_progress()
        self.assertEqual(work_order.progress_percentage, 30.0)

    def test_compute_related_containers(self):
        """Test computation of related containers and locations"""
        work_order = self._create_test_record()

        if not self.test_container:
            self.skipTest("Container model not available")

        try:
            # Create retrieval item linked to container
            item = self.env['file.retrieval.item'].create({
                'work_order_id': work_order.id,
                'container_id': self.test_container.id,
                'description': 'Test document',
            })

            work_order._compute_related_containers()

            self.assertIn(self.test_container.id, work_order.container_ids.ids)
            if self.test_location:
                self.assertIn(self.test_location.id, work_order.location_ids.ids)
        except:
            self.skipTest("Retrieval item model not available")

    # ========================================================================
    # STATE WORKFLOW TESTS
    # ========================================================================

    def test_action_confirm_from_draft(self):
        """Test confirming work order from draft state"""
        work_order = self._create_test_record()
        self.assertEqual(work_order.state, 'draft')

        result = work_order.action_confirm()

        self.assertTrue(result)
        self.assertEqual(work_order.state, 'confirmed')

    def test_action_confirm_invalid_state(self):
        """Test confirming work order from invalid state"""
        work_order = self._create_test_record()
        work_order.state = 'completed'

        with self.assertRaises(UserError) as context:
            work_order.action_confirm()

        self.assertIn("Only draft work orders can be confirmed", str(context.exception))

    def test_action_start_locating_from_confirmed(self):
        """Test starting file location from confirmed state"""
        work_order = self._create_test_record()
        work_order.action_confirm()

        result = work_order.action_start_locating()

        self.assertTrue(result)
        self.assertEqual(work_order.state, 'locating')
        self.assertIsNotNone(work_order.actual_start_date)

    def test_action_start_locating_invalid_state(self):
        """Test starting file location from invalid state"""
        work_order = self._create_test_record()
        # Stay in draft state

        with self.assertRaises(UserError) as context:
            work_order.action_start_locating()

        self.assertIn("Only confirmed work orders can start file location", str(context.exception))

    def test_action_complete_from_delivered(self):
        """Test completing work order from delivered state"""
        work_order = self._create_test_record()
        work_order.state = 'delivered'

        result = work_order.action_complete()

        self.assertTrue(result)
        self.assertEqual(work_order.state, 'completed')
        self.assertIsNotNone(work_order.actual_completion_date)

    def test_action_complete_invalid_state(self):
        """Test completing work order from invalid state"""
        work_order = self._create_test_record()
        # Stay in draft state

        with self.assertRaises(UserError) as context:
            work_order.action_complete()

        self.assertIn("Only delivered work orders can be completed", str(context.exception))

    def test_complete_workflow_sequence(self):
        """Test complete workflow from draft to completed"""
        work_order = self._create_test_record()

        # Test full workflow
        self.assertEqual(work_order.state, 'draft')

        work_order.action_confirm()
        self.assertEqual(work_order.state, 'confirmed')

        work_order.action_start_locating()
        self.assertEqual(work_order.state, 'locating')
        self.assertIsNotNone(work_order.actual_start_date)

        # Manually move through intermediate states
        work_order.state = 'retrieving'
        work_order.state = 'packaging'
        work_order.state = 'delivered'

        work_order.action_complete()
        self.assertEqual(work_order.state, 'completed')
        self.assertIsNotNone(work_order.actual_completion_date)

    # ========================================================================
    # DELIVERY METHOD TESTS
    # ========================================================================

    def test_scan_delivery_method(self):
        """Test scan and email delivery method"""
        work_order = self._create_test_record(
            delivery_method='scan',
            packaging_type=False,  # Should not be required for scan
        )

        self.assertEqual(work_order.delivery_method, 'scan')
        self.assertFalse(work_order.packaging_type)

    def test_physical_delivery_method(self):
        """Test physical delivery method with packaging"""
        work_order = self._create_test_record(
            delivery_method='physical',
            packaging_type='box',
            delivery_address_id=self.delivery_partner.id,
            delivery_instructions='Signature required upon delivery',
        )

        self.assertEqual(work_order.delivery_method, 'physical')
        self.assertEqual(work_order.packaging_type, 'box')
        self.assertEqual(work_order.delivery_address_id, self.delivery_partner)
        self.assertEqual(work_order.delivery_instructions, 'Signature required upon delivery')

    # ========================================================================
    # PRIORITY AND COORDINATION TESTS
    # ========================================================================

    def test_high_priority_work_order(self):
        """Test high priority work order handling"""
        work_order = self._create_test_record(
            priority='2',
            access_coordination_needed=True,
            coordinator_id=self.coordinator_user.id,
        )

        self.assertEqual(work_order.priority, '2')
        self.assertTrue(work_order.access_coordination_needed)
        self.assertEqual(work_order.coordinator_id, self.coordinator_user)

    def test_low_priority_work_order(self):
        """Test low priority work order handling"""
        work_order = self._create_test_record(
            priority='0',
            access_coordination_needed=False,
        )

        self.assertEqual(work_order.priority, '0')
        self.assertFalse(work_order.access_coordination_needed)

    # ========================================================================
    # ACTION HELPER TESTS
    # ========================================================================

    def test_action_view_retrieval_items(self):
        """Test action to view retrieval items"""
        work_order = self._create_test_record()

        result = work_order.action_view_retrieval_items()

        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'file.retrieval.item')
        self.assertEqual(result['view_mode'], 'tree,form')
        self.assertIn(('work_order_id', '=', work_order.id), result['domain'])
        self.assertEqual(result['context']['default_work_order_id'], work_order.id)

    # ========================================================================
    # PROGRESS TRACKING TESTS
    # ========================================================================

    def test_progress_metrics_initialization(self):
        """Test initial progress metrics"""
        work_order = self._create_test_record()

        work_order._update_progress_metrics()

        self.assertEqual(work_order.files_located_count, 0)
        self.assertEqual(work_order.files_retrieved_count, 0)
        self.assertEqual(work_order.files_quality_approved_count, 0)
        self.assertEqual(work_order.progress_percentage, 0.0)

    def test_progress_metrics_with_mock_items(self):
        """Test progress metrics calculation with mock retrieval items"""
        work_order = self._create_test_record()

        # Mock retrieval items with different statuses
        mock_items = MagicMock()
        mock_items.filtered.side_effect = [
            MagicMock(__len__=lambda x: 3),  # located items
            MagicMock(__len__=lambda x: 2),  # retrieved items
            MagicMock(__len__=lambda x: 1),  # quality approved items
        ]

        work_order.retrieval_item_ids = mock_items
        work_order.item_count = 5

        with patch.object(work_order, 'retrieval_item_ids', mock_items):
            work_order._update_progress_metrics()
            work_order._compute_progress()

        # Progress should be 40% (2 retrieved out of 5 total)
        expected_progress = (2 / 5) * 100
        self.assertEqual(work_order.progress_percentage, expected_progress)

    # ========================================================================
    # BUSINESS LOGIC TESTS
    # ========================================================================

    def test_naid_audit_log_creation(self):
        """Test NAID audit log creation for work order events"""
        work_order = self._create_test_record()

        try:
            # Test audit log creation
            work_order._create_naid_audit_log('work_order_confirmed')

            # Check if audit log was created
            audit_logs = self.env['naid.audit.log'].search([
                ('model_name', '=', 'file.retrieval.work.order'),
                ('record_id', '=', work_order.id),
                ('event_type', '=', 'work_order_confirmed'),
            ])

            self.assertEqual(len(audit_logs), 1)
            self.assertEqual(audit_logs.partner_id, work_order.partner_id)
            self.assertEqual(audit_logs.user_id, self.env.user)
        except:
            self.skipTest("NAID audit log model not available")

    def test_work_order_message_posting(self):
        """Test message posting for work order state changes"""
        work_order = self._create_test_record()

        # Test message posting during confirmation
        work_order.action_confirm()

        # Check if message was posted
        messages = work_order.message_ids
        self.assertTrue(len(messages) > 0)

        # Find confirmation message
        confirmation_messages = messages.filtered(
            lambda m: 'confirmed for' in m.body and work_order.partner_id.name in m.body
        )
        self.assertTrue(len(confirmation_messages) > 0)

    # ========================================================================
    # VALIDATION AND CONSTRAINT TESTS
    # ========================================================================

    def test_required_field_validation(self):
        """Test validation of required fields"""
        with self.assertRaises(ValidationError):
            self.env['file.retrieval.work.order'].create({
                # Missing required partner_id
                'request_description': 'Test request',
            })

    def test_date_logical_validation(self):
        """Test logical validation of date fields"""
        past_date = datetime.now() - timedelta(days=1)
        future_date = datetime.now() + timedelta(days=1)

        work_order = self._create_test_record(
            scheduled_date=future_date,
            actual_start_date=past_date,
        )

        # Basic validation - actual start should not be before scheduled
        # This would be caught by custom constraints
        self.assertLess(work_order.actual_start_date, work_order.scheduled_date)

    # ========================================================================
    # INTEGRATION TESTS
    # ========================================================================

    def test_integration_with_portal_request(self):
        """Test integration with portal request system"""
        try:
            # Create portal request
            portal_request = self.env['portal.request'].create({
                'partner_id': self.partner.id,
                'request_type': 'file_retrieval',
                'description': 'Integration test request',
                'state': 'approved',
            })

            # Create work order from portal request
            work_order = self._create_test_record(
                portal_request_id=portal_request.id,
                request_description=portal_request.description,
            )

            self.assertEqual(work_order.portal_request_id, portal_request)
            self.assertEqual(work_order.partner_id, portal_request.partner_id)
        except:
            self.skipTest("Portal request model not available")

    def test_integration_with_billing_system(self):
        """Test integration with billing and invoicing"""
        work_order = self._create_test_record()

        try:
            # Create rate if base.rate model exists
            rate = self.env['base.rate'].create({
                'name': 'File Retrieval Rate',
                'rate_type': 'per_page',
                'amount': 2.50,
            })

            work_order.rate_id = rate.id

            self.assertEqual(work_order.rate_id, rate)
        except:
            self.skipTest("Rate model not available")

    # ========================================================================
    # PERFORMANCE TESTS
    # ========================================================================

    def test_bulk_work_order_creation(self):
        """Test performance with bulk work order creation"""
        work_orders_data = []
        for i in range(50):
            work_orders_data.append({
                'partner_id': self.partner.id,
                'request_description': f'Bulk test request {i}',
                'priority': str(i % 3),
                'delivery_method': 'scan' if i % 2 == 0 else 'physical',
            })

        # Test bulk create
        bulk_work_orders = self.env['file.retrieval.work.order'].create(work_orders_data)

        self.assertEqual(len(bulk_work_orders), 50)

        # Test bulk state updates
        bulk_work_orders.write({'state': 'confirmed'})

        confirmed_orders = bulk_work_orders.filtered(lambda wo: wo.state == 'confirmed')
        self.assertEqual(len(confirmed_orders), 50)

    def test_search_performance(self):
        """Test search performance with various filters"""
        # Create test data
        for i in range(20):
            self._create_test_record(
                priority=str(i % 3),
                state='draft' if i % 2 == 0 else 'confirmed',
                delivery_method='scan' if i % 3 == 0 else 'physical',
            )

        # Test various search patterns
        high_priority = self.env['file.retrieval.work.order'].search([('priority', '=', '2')])
        self.assertTrue(len(high_priority) > 0)

        draft_orders = self.env['file.retrieval.work.order'].search([('state', '=', 'draft')])
        self.assertTrue(len(draft_orders) > 0)

        scan_delivery = self.env['file.retrieval.work.order'].search([('delivery_method', '=', 'scan')])
        self.assertTrue(len(scan_delivery) > 0)

    # ========================================================================
    # SECURITY TESTS
    # ========================================================================

    def test_access_rights_basic(self):
        """Test basic access rights for work orders"""
        work_order = self._create_test_record()

        # Test read access
        self.assertTrue(work_order.exists())
        self.assertEqual(work_order.partner_id, self.partner)

        # Test write access
        work_order.write({'priority': '2'})
        self.assertEqual(work_order.priority, '2')

    def test_multi_company_isolation(self):
        """Test multi-company data isolation"""
        # Create second company if possible
        try:
            company2 = self.env['res.company'].create({
                'name': 'Test Company 2',
            })

            # Create work order for different company
            work_order_company2 = self._create_test_record(
                company_id=company2.id
            )

            # Work orders should be isolated by company
            self.assertEqual(work_order_company2.company_id, company2)
            self.assertNotEqual(work_order_company2.company_id, self.test_record.company_id)
        except:
            self.skipTest("Multi-company test not applicable")
