# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestDocumentTempBarcodeSequence(TransactionCase):
    def test_unique_temp_barcodes_concurrency_simulation(self):
        Document = self.env['records.document']
        partner = self.env['res.partner'].create({'name': 'Seq Test Customer'})
        created = Document.create([
            {'name': 'Doc %s' % i, 'partner_id': partner.id} for i in range(25)
        ])
        temps = created.mapped('temp_barcode')
        # All should have values and start with TF
        self.assertTrue(all(t and t.startswith('TF') for t in temps))
        # Uniqueness
        self.assertEqual(len(temps), len(set(temps)))
