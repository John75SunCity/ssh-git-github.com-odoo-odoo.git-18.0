# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestRecordsManagement(TransactionCase):
    """Test cases for Records Management module."""

    def setUpClass(cls):
        super(TestRecordsManagement, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'test@example.com',
        })
        cls.product_box = cls.env.ref('records_management.product_box')
        cls.lot = cls.env['stock.lot'].create({
            'name': 'TEST001',
            'product_id': cls.product_box.id,
            'customer_id': cls.partner.id,
        })

    def test_pickup_request_creation(self):
        """Test creation of pickup request."""
        pickup_request = self.env['pickup.request'].create({
            'customer_id': self.partner.id,
            'item_ids': [(6, 0, [self.lot.id])],
        })
        self.assertEqual(pickup_request.customer_id, self.partner)
        self.assertIn(self.lot, pickup_request.item_ids)
        self.assertEqual(pickup_request.state, 'draft')

    def test_pickup_request_validation(self):
        """Test validation constraints."""
        # Test past date validation
        with self.assertRaises(ValidationError):
            self.env['pickup.request'].create({
                'customer_id': self.partner.id,
                'request_date': '2020-01-01',
                'item_ids': [(6, 0, [self.lot.id])],
            })

    def test_shredding_service_creation(self):
        """Test shredding service creation."""
        service = self.env['shredding.service'].create({
            'customer_id': self.partner.id,
            'service_type': 'box',
            'box_quantity': 5,
        })
        self.assertEqual(service.customer_id, self.partner)
        self.assertEqual(service.service_type, 'box')
        self.assertEqual(service.total_charge, 25.0)  # 5 boxes * 5.0

    def test_shredding_service_validation(self):
        """Test shredding service validation."""
        # Test box quantity validation
        with self.assertRaises(ValidationError):
            self.env['shredding.service'].create({
                'customer_id': self.partner.id,
                'service_type': 'box',
                'box_quantity': 0,
            })

        # Test latitude/longitude validation
        with self.assertRaises(ValidationError):
            self.env['shredding.service'].create({
                'customer_id': self.partner.id,
                'service_type': 'bin',
                'latitude': 91.0,  # Invalid latitude
            })

    def test_stock_lot_customer(self):
        """Test stock production lot customer relationship."""
        self.assertEqual(self.lot.customer_id, self.partner)

    def test_create_pickup_request_method(self):
        """Test the create_pickup_request method."""
        pickup_request = self.env['pickup.request'].create_pickup_request(
            self.partner, [self.lot.id]
        )
        self.assertEqual(pickup_request.customer_id, self.partner)
        self.assertIn(self.lot, pickup_request.item_ids)

        # Test with empty item_ids
        with self.assertRaises(ValidationError):
            self.env['pickup.request'].create_pickup_request(self.partner, [])

    def test_pickup_request_state_transitions(self):
        """Test pickup request state transitions."""
        pickup_request = self.env['pickup.request'].create({
            'customer_id': self.partner.id,
            'item_ids': [(6, 0, [self.lot.id])],
        })
        
        # Test confirm action
        pickup_request.action_confirm()
        self.assertEqual(pickup_request.state, 'confirmed')
        
        # Test done action
        pickup_request.action_done()
        self.assertEqual(pickup_request.state, 'done')
