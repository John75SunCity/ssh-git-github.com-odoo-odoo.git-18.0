# -*- coding: utf-8 -*-
"""
Records Billing Rate Model

This model manages billing rates and pricing tiers for the Records Management module.
"""

from odoo import _, api, fields, models


class RecordsBillingRate(models.Model):
    """
    Records Billing Rate

    Manages different rate structures and pricing tiers for billing configurations.
    """

    _name = "records.billing.rate"
    _description = "Records Billing Rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Parent relationship
    config_id = fields.Many2one("records.billing.config", string="Billing Config", required=True, ondelete="cascade")

    # Rate details
    service_type = fields.Selection(
        [
            ("storage", "Storage"),
            ("retrieval", "Retrieval"),
            ("destruction", "Destruction"),
            ("digital", "Digital Services"),
        ],
        string="Service Type",
        required=True,
    )

    rate_type = fields.Selection(
        [
            ("fixed", "Fixed Rate"),
            ("tiered", "Tiered Rate"),
            ("percentage", "Percentage"),
        ],
        string="Rate Type",
        default="fixed",
        required=True,
    )

    base_rate = fields.Float(string="Base Rate", digits=(10, 2), required=True)
    unit_of_measure = fields.Char(string="Unit of Measure")
    tier_threshold = fields.Float(string="Tier Threshold", digits=(10, 2))
    discount_percentage = fields.Float(string="Discount %", digits=(5, 2))
    effective_date = fields.Date(string="Effective Date")
    active = fields.Boolean(default=True, tracking=True)
