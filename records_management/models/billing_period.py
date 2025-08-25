from odoo import models, fields


class BillingPeriod(models.Model):
    _name = "billing.period"
    _description = "Billing Period"

    name = fields.Char(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    active = fields.Boolean(default=True)
    note = fields.Text()
