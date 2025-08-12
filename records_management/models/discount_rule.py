# -*- coding: utf-8 -*-
# Discount Rule Model

from odoo import api, fields, models




class DiscountRule(models.Model):
    """Discount rules for billing configurations"""

    _name = "discount.rule"
    _description = "Discount Rule"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "config_id, priority"

    config_id = fields.Many2one(
        "records.billing.config",
        string="Billing Config",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(string="Rule Name", required=True)
    rule_type = fields.Selection(
        [
            ("volume", "Volume Discount"),
            ("loyalty", "Loyalty Discount"),
            ("seasonal", "Seasonal Discount"),
            ("promotional", "Promotional Discount"),
        ],
        string="Rule Type",
        required=True,
    )
    threshold = fields.Float(string="Threshold", digits=(10, 2))
    discount_percentage = fields.Float(string="Discount %", digits=(5, 2))
    discount_amount = fields.Monetary(
        string="Discount Amount", currency_field="currency_id"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    active = fields.Boolean(string="Active", default=True)
    priority = fields.Integer(string="Priority", default=10)
