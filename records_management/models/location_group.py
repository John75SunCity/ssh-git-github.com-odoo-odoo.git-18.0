from odoo import models, fields, api, _

class LocationGroup(models.Model):
    _name = 'location.group'
    _description = 'Location Group'
    _order = 'name'

    name = fields.Char(string='Group Name', required=True)
    code = fields.Char(string='Group Code')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    location_ids = fields.One2many('records.location', 'group_id', string='Locations')
    manager_id = fields.Many2one('res.users', string='Group Manager')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
