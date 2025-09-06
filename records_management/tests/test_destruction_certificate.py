from odoo.tests import TransactionCase, tagged
from odoo import fields


@tagged('-at_install', 'post_install')
class TestDestructionCertificate(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Customer'})
        self.configurator = self.env['rm.module.configurator']

    def _create_certificate(self, **kwargs):
        vals = {
            'name': 'New',
            'partner_id': self.partner.id,
            'destruction_type': 'on_site',
        }
        vals.update(kwargs)
        return self.env['destruction.certificate'].create(vals)

    def test_generation_on_confirm(self):
        cert = self._create_certificate()
        cert.action_confirm_destruction()
        self.assertTrue(cert.certificate_attachment_id, 'Attachment should be generated on confirmation')

    def test_skip_when_exists(self):
        cert = self._create_certificate()
        cert.action_confirm_destruction()
        first_attachment = cert.certificate_attachment_id
        cert.generate_certificate_document()  # should skip regeneration
        self.assertEqual(cert.certificate_attachment_id.id, first_attachment.id, 'Should not regenerate without force')

    def test_force_regenerate(self):
        cert = self._create_certificate()
        cert.action_confirm_destruction()
        first_attachment = cert.certificate_attachment_id
        cert.action_force_regenerate_certificate()
        self.assertNotEqual(cert.certificate_attachment_id.id, first_attachment.id, 'Force regenerate should replace attachment')

    def test_auto_generate_on_invoice_paid(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {'name': 'Service', 'quantity': 1, 'price_unit': 10})]
        })
        cert = self._create_certificate(invoice_id=invoice.id)
        # simulate payment by setting payment_state manually (simplified for test context)
        invoice.payment_state = 'paid'
        cert._auto_generate_on_invoice_paid()
        self.assertTrue(cert.certificate_attachment_id, 'Attachment should be generated when invoice marked paid')

    def test_disabled_toggle(self):
        # Disable feature via direct parameter (bypassing UI) for test
        self.env['ir.config_parameter'].sudo().set_param('destruction_certificate_enabled', False)
        cert = self._create_certificate()
        cert.action_confirm_destruction()
        self.assertFalse(cert.certificate_attachment_id, 'Attachment should not generate when feature disabled')
