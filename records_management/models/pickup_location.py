from odoo import models, fields, api, _

class PickupLocation(models.Model):
    _name = 'pickup.location'
    _description = 'Pickup Location'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Location Name', required=True, tracking=True)
    address = fields.Char(string='Address')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip = fields.Char(string='ZIP')
    country_id = fields.Many2one('res.country', string='Country')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Location Manager', default=lambda self: self.env.user)
    notes = fields.Text(string='Notes')
