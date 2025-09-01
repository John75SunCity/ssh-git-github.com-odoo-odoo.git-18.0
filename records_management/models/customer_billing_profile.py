from odoo import models, fields

class CustomerBillingProfile(models.Model):
    _name = 'customer.billing.profile'
    _description = 'Customer Billing Profile'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    active = fields.Boolean(string='Active', default=True)
    # Add other relevant fields as needed (e.g., billing preferences, rates)
