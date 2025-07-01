from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PickupRequest(models.Model):
    _name = 'pickup.request'
    _description = 'Pickup Request'

    name = fields.Char(string='Name', required=True, default='New')
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.context_today, required=True)
    request_item_ids = fields.One2many('pickup.request.item', 'pickup_id', string='Request Items')  # canonical one2many
    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('pickup.request') or 'New'
        return super().create(vals_list)
