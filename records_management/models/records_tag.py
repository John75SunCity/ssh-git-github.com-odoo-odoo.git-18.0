from odoo import models, fields, api, _

class RecordsTag(models.Model):
    _name = 'records.tag'
    _description = 'Records Management Tag'

    name = fields.Char(string='Name', required=True)
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(default=True)
    
    # Optional: add a description field
    description = fields.Text(string='Description')
    
    # Optional: add a company_id field if you need multi-company support
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
