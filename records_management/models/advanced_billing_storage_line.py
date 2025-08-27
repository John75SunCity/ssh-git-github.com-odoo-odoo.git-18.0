from odoo import models, fields


class AdvancedBillingStorageLine(models.Model):
    _name = "advanced.billing.storage.line"
    _description = "Advanced Billing Storage Line"

    name = fields.Char(required=True)
    billing_id = fields.Many2one("advanced.billing", string="Billing", ondelete="cascade", index=True, required=True)
    currency_id = fields.Many2one(related="billing_id.currency_id", store=True, readonly=True)
    amount = fields.Monetary(currency_field="currency_id", required=True, default=0.0, digits=(16, 2))
    # Default sequence is set to 10 for consistency with other sequence fields in the project.
    sequence = fields.Integer(default=10)
