# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError




class TestHardDriveScanning(TransactionCase):
    """Test cases for hard drive serial number scanning workflow"""

    def setUp(self):
        super().setUp()

        # Create test customer
        self.customer = self.env['res.partner'].create({
            'name': 'Test Customer',
            'is_company': True,
        })

        # Create test shredding service
        self.shredding_service = self.env['shredding.service'].create({
            'name': 'TEST-SHRED-001',
            'customer_id': self.customer.id,
            'service_type': 'hard_drive',
            'destruction_method': 'shred',
            'quantity': 5,
            'rate': 25.00,
            'scheduled_date': datetime.now() + timedelta(days=1),
        })

    def test_hard_drive_creation_from_scan(self):
        """Test creating hard drive records from scanning"""
        # Test customer location scan
        hard_drive = self.env['shredding.hard_drive'].create_from_scan(
            service_id=self.shredding_service.id,
            serial_number='HD123456789',
            scan_location='customer'
        )

        self.assertEqual(hard_drive.serial_number, 'HD123456789')
        self.assertTrue(hard_drive.scanned_at_customer)
        self.assertFalse(hard_drive.verified_before_destruction)
        self.assertIsNotNone(hard_drive.scanned_at_customer_date)
        self.assertEqual(hard_drive.scanned_at_customer_by, self.env.user)

    def test_hard_drive_facility_verification(self):
        """Test facility verification workflow"""
        # Create hard drive record
        hard_drive = self.env['shredding.hard_drive'].create({
            'service_id': self.shredding_service.id,
            'serial_number': 'HD987654321',
            'scanned_at_customer': True,
            'scanned_at_customer_date': datetime.now(),
        })

        # Mark as verified at facility
        hard_drive.action_mark_facility_verified()

        self.assertTrue(hard_drive.verified_before_destruction)
        self.assertIsNotNone(hard_drive.verified_at_facility_date)
        self.assertEqual(hard_drive.verified_at_facility_by, self.env.user)

    def test_hard_drive_destruction_workflow(self):
        """Test complete destruction workflow"""
        # Create and verify hard drive
        hard_drive = self.env['shredding.hard_drive'].create({
            'service_id': self.shredding_service.id,
            'serial_number': 'HD555666777',
            'scanned_at_customer': True,
            'verified_before_destruction': True,
            'destruction_method': 'shred',
        })

        # Mark as destroyed
        hard_drive.action_mark_destroyed()

        self.assertTrue(hard_drive.destroyed)
        self.assertIsNotNone(hard_drive.destruction_date)

    def test_computed_counts(self):
        """Test computed count fields on shredding service"""
        # Create multiple hard drives
        for i in range(3):
            self.env['shredding.hard_drive'].create({
                'service_id': self.shredding_service.id,
                'serial_number': f'HD{str(i).zfill(9)}',
                'scanned_at_customer': True,
            })

        # Create one more verified drive
        self.env['shredding.hard_drive'].create({
            'service_id': self.shredding_service.id,
            'serial_number': 'HD999888777',
            'scanned_at_customer': True,
            'verified_before_destruction': True,
        })

        # Trigger computation
        self.shredding_service._compute_hard_drive_counts()

        self.assertEqual(self.shredding_service.hard_drive_scanned_count, 4)
        self.assertEqual(self.shredding_service.hard_drive_verified_count, 1)

    def test_billing_calculation_with_scanned_drives(self):
        """Test that billing uses actual scanned count when available"""
        # Create 3 scanned drives (more than manual quantity of 5)
        for i in range(7):
            self.env['shredding.hard_drive'].create({
                'service_id': self.shredding_service.id,
                'serial_number': f'HD{str(i).zfill(9)}',
                'scanned_at_customer': True,
            })

        # Trigger computation
        self.shredding_service._compute_total_cost()

        # Should use scanned count (7) instead of manual quantity (5)
        expected_cost = 7 * 25.00  # 7 drives * $25 rate
        self.assertEqual(self.shredding_service.total_cost, expected_cost)

    def test_certificate_line_generation(self):
        """Test certificate line text generation"""
        hard_drive = self.env['shredding.hard_drive'].create({
            'service_id': self.shredding_service.id,
            'serial_number': 'HD111222333',
            'destruction_method': 'shred',
            'destruction_date': datetime.now(),
        })

        # Trigger computation
        hard_drive._compute_certificate_line()

        self.assertIn('HD111222333', hard_drive.certificate_line_text)
        self.assertIn('Physical Shredding', hard_drive.certificate_line_text)

    def test_hashed_serial_computation(self):
        """Test serial number hashing for integrity"""
        hard_drive = self.env['shredding.hard_drive'].create({
            'service_id': self.shredding_service.id,
            'serial_number': 'HD123TEST',
        })

        # Trigger computation
        hard_drive._compute_hashed_serial()

        self.assertIsNotNone(hard_drive.hashed_serial)
        self.assertEqual(len(hard_drive.hashed_serial), 64)  # SHA256 hex length

    def test_scan_wizard_single_scan(self):
        """Test the scanning wizard single scan functionality"""
        wizard = self.env['hard_drive.scan.wizard'].create({
            'service_id': self.shredding_service.id,
            'scan_location': 'customer',
            'serial_number': 'WIZARD-TEST-001',
        })

        # Perform scan
        result = wizard.action_scan_serial()

        # Check hard drive was created
        hard_drive = self.env['shredding.hard_drive'].search([
            ('service_id', '=', self.shredding_service.id),
            ('serial_number', '=', 'WIZARD-TEST-001')
        ])

        self.assertEqual(len(hard_drive), 1)
        self.assertTrue(hard_drive.scanned_at_customer)

    def test_scan_wizard_bulk_scan(self):
        """Test the scanning wizard bulk scan functionality"""
        bulk_serials = "BULK-001\nBULK-002\nBULK-003"

        wizard = self.env['hard_drive.scan.wizard'].create({
            'service_id': self.shredding_service.id,
            'scan_location': 'customer',
            'bulk_serial_input': bulk_serials,
        })

        # Perform bulk scan
        wizard.action_bulk_scan()

        # Check all hard drives were created
        hard_drives = self.env['shredding.hard_drive'].search([
            ('service_id', '=', self.shredding_service.id),
            ('serial_number', 'in', ['BULK-001', 'BULK-002', 'BULK-003'])
        ])

        self.assertEqual(len(hard_drives), 3)
        self.assertTrue(all(hd.scanned_at_customer for hd in hard_drives))

    def test_duplicate_serial_handling(self):
        """Test handling of duplicate serial numbers"""
        # Create initial hard drive
        self.env['shredding.hard_drive'].create({
            'service_id': self.shredding_service.id,
            'serial_number': 'DUPLICATE-TEST',
            'scanned_at_customer': True,
        })

        # Try to scan same serial again via wizard
        wizard = self.env['hard_drive.scan.wizard'].create({
            'service_id': self.shredding_service.id,
            'scan_location': 'customer',
            'serial_number': 'DUPLICATE-TEST',
        })

        # Should raise error for duplicate
        with self.assertRaises(UserError):
            wizard.action_scan_serial()

    def test_service_action_methods(self):
        """Test service-level action methods for scanning"""
        # Test customer scanning action
        result = self.shredding_service.action_scan_hard_drives_customer()
        self.assertEqual(result['res_model'], 'hard_drive.scan.wizard')
        self.assertEqual(result['context']['default_scan_location'], 'customer')

        # Test facility verification action
        result = self.shredding_service.action_scan_hard_drives_facility()
        self.assertEqual(result['res_model'], 'hard_drive.scan.wizard')
        self.assertEqual(result['context']['default_scan_location'], 'facility')

        # Test view hard drives action
        result = self.shredding_service.action_view_hard_drives()
        self.assertEqual(result['res_model'], 'shredding.hard_drive')
        self.assertEqual(result['domain'], [('service_id', '=', self.shredding_service.id)])
