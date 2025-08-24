from odoo import models, fields, api, _

class InventoryItem(models.Model):
    _name = 'inventory.item'
    _description = 'Inventory Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Item Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    product_id = fields.Many2one('product.product', string='Product', required=True)
    serial_number = fields.Char(string='Serial Number')
    location_id = fields.Many2one('records.location', string='Location')
    status = fields.Selection([
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Maintenance'),
        ('retired', 'Retired'),
        ('lost', 'Lost')
    ], string='Status', default='available', tracking=True)
    acquisition_date = fields.Date(string='Acquisition Date')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('inventory.item') or _('New')
        return super().create(vals)
