# Stub model for res.branch to allow Odoo to load
from odoo import models, fields

class ResBranch(models.Model):
    _name = 'res.branch'
    _description = 'Branch (Stub)'
    name = fields.Char(string='Branch Name', required=True)
