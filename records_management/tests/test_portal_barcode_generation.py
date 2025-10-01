from odoo.tests import TransactionCase


class TestPortalBarcodeGeneration(TransactionCase):
    def test_generate_portal_barcode(self):
        model = self.env['portal.barcode']
        rec1 = model.generate_portal_barcode()
        rec2 = model.generate_portal_barcode()
        self.assertTrue(rec1.name and rec2.name, 'Barcodes should have names')
        self.assertNotEqual(rec1.name, rec2.name, 'Generated barcodes must be unique')
        self.assertEqual(rec1.barcode_type, 'generic')
        self.assertEqual(rec1.barcode_format, 'code128')
