from odoo import fields, models

class ChainOfCustody(models.Model):
    _name = 'chain.of.custody'
    _description = 'Chain of Custody'

    name = fields.Char(string='Name', required=True)
