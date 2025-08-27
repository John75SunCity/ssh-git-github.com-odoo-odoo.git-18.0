from odoo import models, fields, api, _

class FullCustomizationName(models.Model):
    _name = 'full_customization_name'
    _description = 'Full Customization Name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    create_date = fields.Datetime(string='Created On', readonly=True)
    write_date = fields.Datetime(string='Last Updated', readonly=True)
    user_id = fields.Many2one('res.users', string='Customization Owner', default=lambda self: self.env.user)
