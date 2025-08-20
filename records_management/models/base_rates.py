from odoo import fields, models

class BaseRates(models.Model):
    _name = 'base.rates'
    _description = 'Base Rates'

    name = fields.Char(string='Name', required=True)
