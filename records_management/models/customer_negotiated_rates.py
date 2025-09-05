from odoo import fields, models

class CustomerNegotiatedRates(models.Model):
    _name = 'customer.negotiated.rates'
    _description = 'Customer Negotiated Rates'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
