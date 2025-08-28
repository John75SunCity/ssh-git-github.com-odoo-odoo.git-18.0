"""
Test cases for the account.move.line model in the records management module.
"""

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError

class TestAccountMoveLine(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.user = self.env.ref('base.user_admin')
        self.container = self.env['records.container'].create({'name': 'Box 1', 'container_type': 'TYPE 01'})
        self.location = self.env['records.location'].create({'name': 'Main Storage'})
        self.work_order = self.env['document.retrieval.work.order'].create({
            'name': 'WO-001',
            'partner_id': self.partner.id,
            'container_ids': [(6, 0, [self.container.id])],
        })
        self.pickup_request = self.env['pickup.request'].create({
            'name': 'PR-001',
            'pickup_date': '2024-08-01',
            'container_ids': [(6, 0, [self.container.id])],
        })
        self.destruction_service = self.env['shredding.service'].create({
            'name': 'DS-001',
            'total_weight': 100.0,
            'destruction_method': 'cross_cut',
        })
        self.move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })

    def test_onchange_work_order_id_sets_fields(self):
        line = self.env['account.move.line'].new({
            'move_id': self.move.id,
            'work_order_id': self.work_order.id,
        })
        line._onchange_work_order_id()
        self.assertTrue(line.records_related)
        self.assertEqual(line.records_service_type, 'retrieval')
        self.assertEqual(line.partner_id, self.partner)
        self.assertEqual(line.work_order_reference, self.work_order.name)

    def test_onchange_destruction_service_id_sets_fields(self):
        line = self.env['account.move.line'].new({
            'move_id': self.move.id,
            'destruction_service_id': self.destruction_service.id,
            'records_related': True,
            'records_service_type': 'destruction',
        })
        line._onchange_destruction_service_id()
        self.assertEqual(line.records_service_type, 'destruction')
        self.assertEqual(line.shredding_weight_lbs, 100.0)
        self.assertEqual(line.destruction_method, 'cross_cut')
        self.assertTrue(line.naid_audit_required)
        line = self.env['account.move.line'].new({
            'move_id': self.move.id,
            'pickup_request_id': self.pickup_request.id,
            'records_related': True,
            'records_service_type': 'pickup',
        })
        line._onchange_pickup_request_id()
        self.assertEqual(line.records_service_type, 'pickup')
        self.assertEqual(line.pickup_date, self.pickup_request.pickup_date)
        self.assertEqual(line.container_count, 1)
        self.assertEqual(line.pickup_date, self.pickup_request.pickup_date)
        self.assertEqual(line.container_count, 1)

    def test_check_shredding_weight_constraint(self):
        line = self.env['account.move.line'].create({
            'move_id': self.move.id,
            'shredding_weight_lbs': 10,
        })
        with self.assertRaises(ValidationError):
            line.write({'shredding_weight_lbs': -5})

    def test_check_container_count_constraint(self):
        line = self.env['account.move.line'].create({
            'move_id': self.move.id,
            'container_count': 1,
        })
        with self.assertRaises(ValidationError):
            line.write({'container_count': -1})

    def test_check_storage_dates_constraint(self):
        line = self.env['account.move.line'].create({
            'move_id': self.move.id,
            'storage_start_date': '2024-08-10',
            'storage_end_date': '2024-08-01',
        })
        with self.assertRaises(ValidationError):
            line._check_storage_dates()

    def test_check_pickup_delivery_dates_constraint(self):
        line = self.env['account.move.line'].create({
            'move_id': self.move.id,
            'pickup_date': '2024-08-10',
            'delivery_date': '2024-08-01',
        })
        with self.assertRaises(ValidationError):
            line._check_pickup_delivery_dates()

    def test_action_create_audit_trail(self):
        line = self.env['account.move.line'].create({
            'move_id': self.move.id,
            'records_related': True,
            'records_service_type': 'retrieval',
            'naid_compliant': True,
        })
        line.action_create_audit_trail()
        self.assertTrue(line.audit_trail_created)

        with self.assertRaises(UserError):
            line.action_create_audit_trail()  # Should not allow double creation

    def test_name_get_records_related(self):
        line = self.env['account.move.line'].create({
            'move_id': self.move.id,
            'records_related': True,
            'records_service_type': 'retrieval',
            'name': 'Test Service',
            'container_count': 2,
        })
        name = line.name_get()[0][1]
        self.assertIn('Retrieval Services', name)
        self.assertIn('Test Service', name)
        self.assertIn('2 containers', name)

    def test_get_service_summary(self):
        line = self.env['account.move.line'].create({
            'move_id': self.move.id,
            'records_service_type': 'destruction',
            'service_category': 'onsite',
            'container_count': 3,
            'document_count': 10,
            'shredding_weight_lbs': 50,
            'service_duration_hours': 2.0,
            'naid_compliant': True,
            'audit_trail_created': True,
            'customer_satisfaction_rating': '5',
        })
        summary = line.get_service_summary()
        self.assertEqual(summary['service_type'], 'destruction')
        self.assertEqual(summary['container_count'], 3)
        self.assertEqual(summary['weight_processed'], 50)
        self.assertTrue(summary['naid_compliant'])
        self.assertTrue(summary['audit_trail_created'])
    def test_generate_billing_report_data(self):
        self.move.action_post()  # Ensure move.name is set
        line = self.env['account.move.line'].create({
            'move_id': self.move.id,
            'partner_id': self.partner.id,
            'records_service_type': 'pickup',
            'pickup_date': '2024-08-01',
            'container_count': 1,
            'shredding_weight_lbs': 0,
            'unit_rate': 10.0,
            'price_total': 10.0,
            'naid_compliant': True,
            'audit_trail_created': False,
            'customer_satisfaction_rating': '3',
        })
        data = line.generate_billing_report_data()
        self.assertEqual(data['invoice_number'], self.move.name)
        self.assertEqual(data['customer'], self.partner.name)
        self.assertEqual(data['service_type'], 'pickup')
        self.assertEqual(data['container_count'], 1)
        self.assertEqual(data['unit_rate'], 10.0)
        self.assertEqual(data['total_amount'], 10.0)
        self.assertTrue(data['naid_compliant'])
        self.assertFalse(data['audit_trail_created'])
        self.assertEqual(data['customer_satisfaction'], '3')
        self.assertFalse(data['audit_trail_created'])
        self.assertEqual(data['customer_satisfaction'], '3')
