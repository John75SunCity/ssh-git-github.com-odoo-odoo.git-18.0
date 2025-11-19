from odoo import models, fields, api, _

class InventoryItemLocationTransfer(models.Model):
    _name = 'inventory.item.location.transfer'
    _description = 'Inventory Item Location Transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'transfer_date desc, id desc'
    _rec_name = 'display_name'

    name = fields.Char(string='Transfer Reference', required=True, default=lambda self: "New")
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    item_id = fields.Many2one(comodel_name='customer.inventory', string='Inventory Item', required=True)
    from_location_id = fields.Many2one(comodel_name='stock.location', string='From Location', required=True)
    to_location_id = fields.Many2one(comodel_name='stock.location', string='To Location', required=True)
    transfer_date = fields.Date(string='Transfer Date', required=True, default=fields.Date.context_today)
    user_id = fields.Many2one(comodel_name='res.users', string='Transferred By', default=lambda self: self.env.user)
    notes = fields.Text(string='Notes')

    @api.depends('name', 'item_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name or ''} - {rec.item_id.display_name if rec.item_id else ''}"
