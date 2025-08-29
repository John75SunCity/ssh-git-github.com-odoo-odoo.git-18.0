from odoo import models, fields

class RecordsCenterLocation(models.Model):
    _name = 'records.center.location'
    _description = 'Records Center Location'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(string='Location Name', required=True, tracking=True)
    code = fields.Char(string='Location Code', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    address = fields.Char(string='Address')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip = fields.Char(string='ZIP')
    country_id = fields.Many2one('res.country', string='Country')
    manager_id = fields.Many2one('res.users', string='Manager')
    capacity_cubic_feet = fields.Float(string='Capacity (Cubic Feet)')
    notes = fields.Text(string='Notes')
