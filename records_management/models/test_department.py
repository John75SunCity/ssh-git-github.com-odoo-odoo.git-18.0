# Test model to isolate the partner_id field issue

from odoo import api, fields, models

class TestDepartment(models.Model):
    _name = 'test.department'
    _description = 'Test Department'
    
    name = fields.Char(string='Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
