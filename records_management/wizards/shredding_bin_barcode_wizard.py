from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ShreddingBinBarcodeWizard(models.TransientModel):
    """
    Wizard for fixing bad barcode scans or manual barcode entry.
    """

    _name = 'shredding.bin.barcode.wizard'
    _description = 'Shredding Bin Barcode Fix Wizard'

    bin_id = fields.Many2one(
        comodel_name='shredding.service.bin',
        string="Bin",
        required=True
    )

    current_barcode = fields.Char(
        string="Current Barcode",
        readonly=True,
        help="The current problematic barcode"
    )

    scan_issue = fields.Selection([
        ('invalid_characters', 'Invalid Characters (contains %, etc.)'),
        ('wrong_length', 'Wrong Length'),
        ('manual_entry', 'Manual Entry'),
        ('unreadable', 'Unreadable')
    ], string="Scan Issue", readonly=True)

    new_barcode = fields.Char(
        string="Corrected Barcode",
        help="Enter the correct 10-digit barcode"
    )

    use_manual_override = fields.Boolean(
        string="Use Manual Size Override",
        help="Check this if barcode is completely unreadable and you want to manually select bin size"
    )

    manual_bin_size = fields.Selection([
        ('23', '23 Gallon Shredinator'),
        ('32g', '32 Gallon Bin'),
        ('32c', '32 Gallon Console'),
        ('64', '64 Gallon Bin'),
        ('96', '96 Gallon Bin'),
    ], string="Manual Bin Size")

    def action_apply_fix(self):
        """Apply the barcode fix to the bin."""
        self.ensure_one()

        if self.use_manual_override:
            if not self.manual_bin_size:
                raise UserError(_("Please select a bin size when using manual override"))

            self.bin_id.write({
                'manual_size_override': True,
                'bin_size': self.manual_bin_size,
                'barcode_scan_status': 'unreadable'
            })

            message = _("Manual override applied with bin size: %s", dict(self._fields['manual_bin_size'].selection).get(self.manual_bin_size))

        else:
            if not self.new_barcode:
                raise UserError(_("Please enter a corrected barcode"))

            # Validate new barcode
            new_barcode = self.new_barcode.strip()
            if len(new_barcode) != 10 or not new_barcode.isdigit():
                raise UserError(_("Barcode must be exactly 10 digits"))

            self.bin_id.write({
                'barcode': new_barcode,
                'manual_size_override': False
            })

            message = _("Barcode corrected to: %s", new_barcode)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': message,
                'type': 'success',
            }
        }

    @api.onchange('current_barcode')
    def _onchange_current_barcode(self):
        """Auto-suggest fixes for common scan issues."""
        if self.current_barcode and self.scan_issue == 'invalid_characters':
            # Try to clean common scan issues
            cleaned = self.current_barcode.replace('%', '').replace(' ', '').replace('-', '')
            if len(cleaned) == 10 and cleaned.isdigit():
                self.new_barcode = cleaned


class ShreddingBinScanWizard(models.TransientModel):
    _name = 'shredding.bin.scan.wizard'
    _description = 'Bin Scan Wizard'

    barcode = fields.Char(string='Barcode', required=True)
    work_order_id = fields.Many2one('work.order.shredding', string='Work Order', default=lambda self: self.env.context.get('active_id'))

    def action_confirm_scan(self):
        self.ensure_one()
        return self.work_order_id.action_scan_barcode(self.barcode)
