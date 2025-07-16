from odoo import models, fields, api
from odoo.exceptions import UserError

class Load(models.Model):
    _name = 'records_management.load'
    _description = 'Paper Load'
    _inherit = ['stock.picking', 'mail.thread']

    bale_ids = fields.One2many('records_management.bale', 'load_id')
    bale_count = fields.Integer(compute='_compute_bale_count')
    weight_total = fields.Float(compute='_compute_weight_total')
    invoice_id = fields.Many2one('account.move')
    driver_signature = fields.Binary()

    @api.depends('bale_ids')
    def _compute_bale_count(self):
        for load in self:
            load.bale_count = len(load.bale_ids)

    @api.depends('bale_ids.weight')
    def _compute_weight_total(self):
        for load in self:
            load.weight_total = sum(b.weight for b in load.bale_ids)

    def action_sign_and_invoice(self):
        # Wizard for driver sign-off, auto-create invoice
        self.ensure_one()
        if self.bale_count > 28:
            raise UserError('Trailer overload!')
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {'name': f'Load {self.name}', 'quantity': 1, 'price_unit': self.weight_total * self._get_market_rate()})]
        }
        self.invoice_id = self.env['account.move'].create(invoice_vals)
        self.state = 'done'
        
    def _get_market_rate(self):
        # Placeholder; add cron to update from API
        return 0.05  # $ per lb; innovative: fetch from recycling API via external