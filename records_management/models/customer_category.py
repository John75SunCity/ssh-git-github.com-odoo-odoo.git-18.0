# -*- coding: utf-8 -*-
# Customer Category Model for Records Management

from odoo import api, fields, models


class CustomerCategory(models.Model):
    """Customer categories for billing segmentation"""

    _name = "customer.category"
    _description = "Customer Category"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(string="Category Name", required=True)
    description = fields.Text(string="Description")
    default_billing_model = fields.Selection(
        [
            ("per_container", "Per Box"),
            ("per_cubic_foot", "Per Cubic Foot"),
            ("flat_rate", "Flat Rate"),
            ("tiered", "Tiered Pricing"),
            ("usage_based", "Usage Based"),
        ],
        string="Default Billing Model",
    )
    priority_level = fields.Selection(
        [
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("premium", "Premium"),
        ],
        string="Priority Level",
        default="normal",
    )
    sla_hours = fields.Integer(string="SLA Response Hours", default=24)
    active = fields.Boolean(string="Active", default=True)
