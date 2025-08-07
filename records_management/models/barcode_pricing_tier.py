# -*- coding: utf-8 -*-

from odoo import models, fields, api

class BarcodePricingTier(models.Model):
    _name = "barcode.pricing.tier"
    _description = "Barcode Pricing Tier"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Tier Name", required=True, tracking=True, index=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("inactive", "Inactive")],
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # PRICING CONFIGURATION
    # ============================================================================
    product_id = fields.Many2one("barcode.product", string="Product", required=True)
    tier_level = fields.Selection(
        [
            ("basic", "Basic"),
            ("standard", "Standard"),
            ("premium", "Premium"),
            ("enterprise", "Enterprise"),
        ],
        string="Tier Level",
        default="standard",
    )

    # ============================================================================
    # PRICING DETAILS
    # ============================================================================
    base_price = fields.Float(string="Base Price", digits="Product Price", default=0.0)
    volume_discount = fields.Float(
        string="Volume Discount (%)", digits="Discount", default=0.0
    )
    minimum_quantity = fields.Integer(string="Minimum Quantity", default=1)
    maximum_quantity = fields.Integer(string="Maximum Quantity", default=9999)

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # ============================================================================
    # VALIDITY PERIOD
    # ============================================================================
    valid_from = fields.Date(string="Valid From", default=fields.Date.today)
    valid_to = fields.Date(string="Valid To")

    # ============================================================================
    # TIER FEATURES
    # ============================================================================
    includes_setup = fields.Boolean(string="Includes Setup", default=False)
    includes_support = fields.Boolean(string="Includes Support", default=False)
    support_level = fields.Selection(
        [
            ("none", "No Support"),
            ("basic", "Basic Support"),
            ("premium", "Premium Support"),
            ("enterprise", "Enterprise Support"),
        ],
        string="Support Level",
        default="none",
    )

    # ============================================================================
    # NOTES & DOCUMENTATION
    # ============================================================================
    description = fields.Text(string="Description")
    terms_conditions = fields.Text(string="Terms & Conditions")

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)        "mail.followers", "res_id", string="Followers"
    )    @api.depends("base_price", "volume_discount")
    def _compute_discounted_price(self):
        for tier in self:
            if tier.volume_discount > 0:
                discount_amount = tier.base_price * (tier.volume_discount / 100)
                tier.discounted_price = tier.base_price - discount_amount
            else:
                tier.discounted_price = tier.base_price

    discounted_price = fields.Float(
        string="Discounted Price",
        compute="_compute_discounted_price",
        digits="Product Price",
        store=True,
    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate pricing tier"""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate pricing tier"""
        self.write({"state": "inactive"})
