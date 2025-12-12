from odoo import models, fields, api, _

class ScanbotBarcodeScannerWizard(models.TransientModel):
    _name = 'scanbot.barcode.scanner.wizard'
    _description = 'Scanbot SDK Barcode Scanner'

    scanned_barcode = fields.Char(string='Scanned Barcode', readonly=True)
    scan_mode = fields.Selection([
        ('single', 'Single Scan'),
        ('batch', 'Batch Scan'),
    ], default='single', string='Scan Mode')
    target_model = fields.Char(string='Target Model', readonly=True)  # e.g., 'work.order.shredding'
    target_id = fields.Integer(string='Target ID', readonly=True)  # ID of the record to update

    def action_open_scanbot_scanner(self):
        """Open the Scanbot SDK interface with resizable viewfinder."""
        # This would typically return an action to open a view with JS integration
        return {
            'type': 'ir.actions.client',
            'tag': 'scanbot_scanner',
            'params': {
                'mode': self.scan_mode,
                'target_model': self.target_model,
                'target_id': self.target_id,
            }
        }

    def process_scanned_barcodes(self, barcodes):
        """Process the scanned barcodes and update the target record."""
        target = self.env[self.target_model].browse(self.target_id)
        for barcode in barcodes:
            target.action_scan_barcode(barcode)  # Call the target's scan method
        return {'type': 'ir.actions.act_window_close'}