from odoo import models, fields


class AdvancedBillingServiceLine(models.Model):
    _name = "advanced.billing.service.line"
    _description = "Advanced Billing Service Line"

    name = fields.Char(required=True)
    billing_id = fields.Many2one("advanced.billing", string="Billing", ondelete="cascade", index=True, required=True)
    currency_id = fields.Many2one(related="billing_id.currency_id", comodel_name="res.currency", store=True, readonly=True)
    amount = fields.Monetary(currency_field="currency_id", required=True, default=0.0)
    sequence = fields.Integer(default=10)
