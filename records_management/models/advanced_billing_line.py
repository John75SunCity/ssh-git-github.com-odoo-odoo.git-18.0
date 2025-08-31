from odoo import models, fields


class AdvancedBillingLine(models.Model):
    _name = "advanced.billing.line"
    _description = "Advanced Billing Line"

    name = fields.Char(required=True)
    billing_id = fields.Many2one(
        comodel_name="advanced.billing", string="Billing", ondelete="cascade", index=True, required=True
    )
    billing_profile_id = fields.Many2one(
        comodel_name="advanced.billing.profile", string="Billing Profile", ondelete="cascade", index=True
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency", store=True, readonly=True, related="billing_id.currency_id"
    )
    amount = fields.Monetary(currency_field="currency_id", required=True, default=0.0)
    sequence = fields.Integer(default=10)
