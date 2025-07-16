# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class TrailerLoad(models.Model):
    """Model for trailer loads in recycling workflow."""
    _name = 'trailer.load'
    _description = 'Trailer Load'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic fields structure - ready for your code
    name = fields.Char(string='Load Reference', required=True, default='New', tracking=True)
    trailer_id = fields.Many2one('fleet.vehicle', string='Trailer', tracking=True)
    total_weight = fields.Float(string='Total Weight (lbs)', tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('loaded', 'Loaded'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ], default='draft', string='Status', tracking=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('trailer.load') or 'New'
        return super().create(vals_list)
