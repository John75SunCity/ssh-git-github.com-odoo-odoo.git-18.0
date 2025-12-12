from odoo import models, fields, api, _

class BarcodeSheetWizard(models.TransientModel):
    _name = 'barcode.sheet.wizard'
    _description = 'Generate Barcode Sheets'

    sheet_count = fields.Integer(string='Number of Sheets', default=1)
    barcodes_per_sheet = fields.Integer(string='Barcodes per Sheet', default=10)

    def action_generate_sheets(self):
        """Generate PDF with printable barcodes."""
        barcodes = [self.env['ir.sequence'].next_by_code('records.container') for _ in range(self.sheet_count * self.barcodes_per_sheet)]
        return self.env.ref('records_management.action_report_barcode_sheets').report_action(self, data={'barcodes': barcodes})