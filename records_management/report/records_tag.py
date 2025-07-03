from odoo import models, fields

class RecordsTag(models.Model):
    _name = 'records.tag'
    _description = 'Records Management Tag'
    
    name = fields.Char('Name', required=True)
    color = fields.Integer('Color Index')
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]
