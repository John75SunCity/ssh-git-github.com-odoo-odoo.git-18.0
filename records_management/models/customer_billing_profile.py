from odoo import models, fields

class CustomerBillingProfile(models.Model):
    _name = 'customer.billing.profile'
    _description = 'Customer Billing Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Profile Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    active = fields.Boolean(string='Active', default=True)
    # Add other relevant fields as needed (e.g., billing preferences, rates)
