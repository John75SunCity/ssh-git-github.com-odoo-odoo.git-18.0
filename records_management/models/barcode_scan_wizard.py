# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BarcodeScanWizard(models.TransientModel):
    """
    Simple wizard for scanning barcodes into work orders.
    Appears as a popup with a single input field.
    Works with USB scanners, mobile camera, or manual entry.
    """
    _name = 'barcode.scan.wizard'
    _description = 'Barcode Scanner'

    barcode_input = fields.Char(
        string='Scan Barcode',
        help="Scan with USB scanner, tap camera icon (mobile), or type manually"
    )
    work_order_model = fields.Char(string='Work Order Model', required=True)
    work_order_id = fields.Integer(string='Work Order ID', required=True)
    scan_result = fields.Html(string='Scan Result', readonly=True)
    
    def action_scan(self):
        """Process the scanned barcode."""
        self.ensure_one()
        
        if not self.barcode_input:
            raise UserError(_('Please scan or enter a barcode'))
        
        # Get the work order
        work_order = self.env[self.work_order_model].browse(self.work_order_id)
        if not work_order.exists():
            raise UserError(_('Work order not found'))
        
        # Call the work order's scan method
        result = work_order.action_scan_barcode(self.barcode_input)
        
        if result.get('success'):
            # Format success message
            self.scan_result = '''
                <div class="alert alert-success">
                    <i class="fa fa-check-circle"/> <strong>Success!</strong><br/>
                    %s<br/>
                    <small>Total scanned: %s</small>
                </div>
            ''' % (result.get('message', 'Scanned'), result.get('total_scanned', 0))
            
            # Clear input for next scan
            self.barcode_input = ''
            
            # Return to keep wizard open for continuous scanning
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
        else:
            # Format error/warning message
            msg_class = 'warning' if result.get('warning') else 'danger'
            self.scan_result = '''
                <div class="alert alert-%s">
                    <i class="fa fa-exclamation-triangle"/> <strong>%s</strong><br/>
                    %s
                </div>
            ''' % (msg_class, 'Warning' if result.get('warning') else 'Error', result.get('message', 'Scan failed'))
            
            # Clear input for retry
            self.barcode_input = ''
            
            # Keep wizard open
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
