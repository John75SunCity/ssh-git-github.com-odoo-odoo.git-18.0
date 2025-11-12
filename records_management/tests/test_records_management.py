# -*- coding: utf-8 -*-

# Standard Odoo imports for test cases
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestRecordsManagement(TransactionCase):
    """Test cases for Records Management module."""

    @classmethod
    def setUpClass(cls):
        super(TestRecordsManagement, cls).setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
                "email": "records.test@company.example",
            }
        )
        cls.product_container = cls.env["product.product"].create(
            {
                "name": "Test Container",
                "detailed_type": "product",  # Odoo 18.0 compatibility
                "tracking": "lot",
            }
        )
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "TEST001",
                "product_id": cls.product_container.id,
                "customer_id": cls.partner.id,
            }
        )

    def test_pickup_request_creation(self):
        """Test creation of pickup request."""
        pickup_request = self.env["pickup.request"].create(
            {
                "customer_id": self.partner.id,
                "item_ids": [(6, 0, [self.lot.id])],
            }
        )
        self.assertEqual(pickup_request.customer_id, self.partner)
        self.assertIn(self.lot, pickup_request.item_ids)
        self.assertEqual(pickup_request.state, "draft")

    def test_search_records(self):
        """Test searching records.container records"""
        # GitHub Copilot Pattern: Search and read operations
        record = self.env['records.container'].create({
            'name': 'Searchable Record'
        })

        found_records = self.env['records.container'].search([
            ('name', '=', 'Searchable Record')
        ])

        self.assertIn(record, found_records)

    def test_update_records_management_fields(self):
        """Test updating records_management record fields"""
        # GitHub Copilot Pattern: Update operations
        record = self.env['records_management'].create({
            'name': 'Original Name'
        })

        record.write({'name': 'Updated Name'})

        self.assertEqual(record.name, 'Updated Name')

    def test_delete_records_management_record(self):
        """Test deleting records_management record"""
        # GitHub Copilot Pattern: Delete operations
        record = self.env['records_management'].create({
            'name': 'To Be Deleted'
        })

        record_id = record.id
        record.unlink()

        self.assertFalse(self.env['records_management'].browse(record_id).exists())

    def test_validation_records_management_constraints(self):
        """Test validation constraints for records_management"""
        # GitHub Copilot Pattern: Validation testing with assertRaises
        with self.assertRaises(ValidationError):
            self.env['records_management'].create({
                # Add invalid data that should trigger validation
            })

    def test_pickup_request_validation(self):
        """Test validation constraints."""
        # Test past date validation
        with self.assertRaises(ValidationError):
            self.env["pickup.request"].create(
                {
                    "customer_id": self.partner.id,
                    "request_date": "2020-01-01",
                    "item_ids": [(6, 0, [self.lot.id])],
                }
            )

    def test_shredding_service_creation(self):
        """Test shredding service creation."""
        service = self.env["shredding.service"].create(
            {
                "customer_id": self.partner.id,
                "service_type": "container",
                "container_quantity": 5,
            }
        )
        self.assertEqual(service.customer_id, self.partner)
        self.assertEqual(service.service_type, "container")
        self.assertEqual(service.total_charge, 25.0)  # 5 containers * 5.0

    def test_shredding_service_validation(self):
        """Test shredding service validation."""
        # Test container quantity validation
        with self.assertRaises(ValidationError):
            self.env["shredding.service"].create(
                {
                    "customer_id": self.partner.id,
                    "service_type": "container",
                    "container_quantity": 0,
                }
            )

        # Test latitude/longitude validation
        with self.assertRaises(ValidationError):
            self.env["shredding.service"].create(
                {
                    "customer_id": self.partner.id,
                    "service_type": "bin",
                    "latitude": 91.0,  # Invalid latitude
                }
            )

    def test_stock_lot_customer(self):
        """Test stock production lot customer relationship."""
        self.assertEqual(self.lot.customer_id, self.partner)

    def test_create_pickup_request_method(self):
        """Test the create_pickup_request method."""
        pickup_request = self.env["pickup.request"].create_pickup_request(
            self.partner, [self.lot.id]
        )
        self.assertEqual(pickup_request.customer_id, self.partner)
        self.assertIn(self.lot, pickup_request.item_ids)

        # Test with empty item_ids
        with self.assertRaises(ValidationError):
            self.env["pickup.request"].create_pickup_request(self.partner, [])

    def test_pickup_request_state_transitions(self):
        """Test pickup request state transitions."""
        pickup_request = self.env["pickup.request"].create(
            {
                "customer_id": self.partner.id,
                "item_ids": [(6, 0, [self.lot.id])],
            }
        )

        # Test confirm action
        pickup_request.action_confirm()
        self.assertEqual(pickup_request.state, "confirmed")

        # Test done action
        pickup_request.action_done()
        self.assertEqual(pickup_request.state, "done")

    def setUp(self):
        super(TestRecordsManagement, self).setUp()
        self.RecordsLocation = self.env['records.location']
        self.parent_location = self.RecordsLocation.create({
            'name': 'Parent Location',
            'max_capacity': 100,
        })

    def test_create_location(self):
        """Test creation of a new location."""
        location = self.RecordsLocation.create({
            'name': 'Test Location',
            'parent_location_id': self.parent_location.id,
            'max_capacity': 50,
        })
        self.assertEqual(location.parent_location_id, self.parent_location)
        self.assertEqual(location.max_capacity, 50)

    def test_recursive_location(self):
        """Test that recursive locations are not allowed."""
        with self.assertRaises(ValidationError):
            self.parent_location.write({'parent_location_id': self.parent_location.id})

    def test_negative_capacity(self):
        """Test that negative capacity is not allowed."""
        with self.assertRaises(ValidationError):
            self.RecordsLocation.create({
                'name': 'Invalid Location',
                'max_capacity': -10,
            })

    def test_utilization_percentage(self):
        """Test computation of utilization percentage."""
        location = self.RecordsLocation.create({
            'name': 'Utilization Test',
            'max_capacity': 100,
        })
        location.container_ids = [(0, 0, {'name': 'Container 1'})]
        self.assertEqual(location.utilization_percentage, 1)
