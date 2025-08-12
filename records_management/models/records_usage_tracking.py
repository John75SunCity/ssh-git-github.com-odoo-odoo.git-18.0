# -*- coding: utf-8 -*-
# Records Usage Tracking Model

from odoo import fields, models


class RecordsUsageTracking(models.Model):
    """Usage tracking for billing configuration"""

    _name = "records.usage.tracking"
    _description = "Records Usage Tracking"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "config_id, date desc"

    config_id = fields.Many2one(
        "records.billing.config",
        string="Billing Config",
        required=True,
        ondelete="cascade",
    )
    date = fields.Date(string="Usage Date", required=True, default=fields.Date.today)
    service_type = fields.Selection(
        [
            ("storage", "Storage"),
            ("retrieval", "Retrieval"),
            ("destruction", "Destruction"),
            ("scanning", "Scanning"),
            ("pickup", "Pickup"),
            ("delivery", "Delivery"),
        ],
        string="Service Type",
        required=True,
    )
    quantity = fields.Float(string="Quantity", digits=(10, 2), required=True)
    unit = fields.Char(string="Unit of Measure", default="boxes")
    cost = fields.Monetary(string="Cost", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    notes = fields.Text(string="Notes")
