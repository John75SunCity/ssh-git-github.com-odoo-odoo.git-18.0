from odoo import models, fields, api, _

class BillingPeriod(models.Model):
    _name = 'billing.period'
    _description = 'Billing Period'
    _order = 'start_date desc'

    name = fields.Char(string='Period Name', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    active = fields.Boolean(default=True)
    note = fields.Text(string='Notes')
    # Add any other fields as needed
