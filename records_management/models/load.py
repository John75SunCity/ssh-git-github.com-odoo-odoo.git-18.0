from odoo import models, fields, api
from odoo.exceptions import UserError

class Load(models.Model):
    _name = 'records_management.load'
    _description = 'Paper Load'
    _inherit = ['stock.picking', 'mail.thread']

    name = fields.Char(default=lambda self: self.env['ir.sequence'].next_by_code('records_management.load'))
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

    def action_prepare_load(self):
        """Prepare load for shipping"""
        self.write({'state': 'ready'})
        self.message_post(body=_('Load prepared by %s') % self.env.user.name)

    def action_start_loading(self):
        """Start loading process"""
        self.write({'state': 'loading'})
        self.message_post(body=_('Loading started by %s') % self.env.user.name)

    def action_ship_load(self):
        """Ship the load"""
        self.write({'state': 'shipped'})
        self.message_post(body=_('Load shipped by %s') % self.env.user.name)

    def action_mark_sold(self):
        """Mark load as sold"""
        self.write({'state': 'sold'})
        self.message_post(body=_('Load marked as sold by %s') % self.env.user.name)

    def action_cancel(self):
        """Cancel the load"""
        self.write({'state': 'cancelled'})
        self.message_post(body=_('Load cancelled by %s') % self.env.user.name)

    def action_view_bales(self):
        """View bales in this load"""
        self.ensure_one()
        return {
            'name': _('Bales in Load: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.bale',
            'view_mode': 'tree,form',
            'domain': [('load_id', '=', self.id)],
            'context': {'default_load_id': self.id},
        }

    def action_view_revenue_report(self):
        """View revenue report for this load"""
        self.ensure_one()
        return {
            'name': _('Revenue Report: %s') % self.name,
            'type': 'ir.actions.report',
            'report_name': 'records_management.load_revenue_report',
            'report_type': 'qweb-pdf',
            'report_file': 'records_management.load_revenue_report',
            'context': {'active_ids': [self.id]},
        }

    def action_view_weight_tickets(self):
        """View weight tickets for this load"""
        self.ensure_one()
        return {
            'name': _('Weight Tickets: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('origin', '=', self.name)],
            'context': {'default_origin': self.name},
        }