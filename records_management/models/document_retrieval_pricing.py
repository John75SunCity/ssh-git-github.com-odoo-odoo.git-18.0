# -*- coding: utf-8 -*-
"""
Document Retrieval Pricing Model

Pricing rules for document retrieval services with volume discounts,
priority multipliers, and customer-specific rates.
"""

from odoo import models, fields




class DocumentRetrievalPricing(models.Model):
    """Pricing rules for document retrieval services"""

    _name = "document.retrieval.pricing"
    _description = "Document Retrieval Pricing"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "service_type, priority_level"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Pricing Rule Name", required=True, tracking=True, index=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # SERVICE TYPE FIELDS
    # ============================================================================
    service_type = fields.Selection(
        [
            ("permanent", "Permanent Retrieval"),
            ("temporary", "Temporary Retrieval"),
            ("copy", "Copy Request"),
            ("scan", "Scan to Digital"),
            ("rush", "Rush Service"),
        ],
        string="Service Type",
        required=True,
    )

    # ============================================================================
    # PRICING STRUCTURE FIELDS
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    base_fee = fields.Monetary(string="Base Fee", currency_field="currency_id")
    per_document_fee = fields.Monetary(
        string="Per Document Fee", currency_field="currency_id"
    )
    per_hour_fee = fields.Monetary(string="Per Hour Fee", currency_field="currency_id")
    per_box_fee = fields.Monetary(string="Per Box Fee", currency_field="currency_id")

    # ============================================================================
    # VOLUME DISCOUNT FIELDS
    # ============================================================================
    volume_threshold = fields.Integer(string="Volume Threshold")
    volume_discount_percent = fields.Float(string="Volume Discount (%)", digits=(5, 2))

    # ============================================================================
    # PRIORITY PRICING FIELDS
    # ============================================================================
    priority_level = fields.Selection(
        [
            ("standard", "Standard"),
            ("expedited", "Expedited"),
            ("urgent", "Urgent"),
            ("critical", "Critical"),
        ],
        string="Priority Level",
        default="standard",
    )
    priority_multiplier = fields.Float(
        string="Priority Multiplier", default=1.0, digits=(3, 2)
    )

    # ============================================================================
    # DELIVERY PRICING FIELDS
    # ============================================================================
    delivery_included = fields.Boolean(string="Delivery Included", default=False)
    delivery_fee = fields.Monetary(string="Delivery Fee", currency_field="currency_id")
    delivery_radius_km = fields.Float(string="Delivery Radius (km)", digits=(5, 2))

    # ============================================================================
    # DIGITAL SERVICES PRICING FIELDS
    # ============================================================================
    scanning_fee = fields.Monetary(string="Scanning Fee", currency_field="currency_id")
    ocr_fee = fields.Monetary(string="OCR Fee", currency_field="currency_id")
    digital_delivery_fee = fields.Monetary(
        string="Digital Delivery Fee", currency_field="currency_id"
    )

    # ============================================================================
    # TIME-BASED PRICING FIELDS
    # ============================================================================
    same_day_multiplier = fields.Float(
        string="Same Day Multiplier", default=2.0, digits=(3, 2)
    )
    next_day_multiplier = fields.Float(
        string="Next Day Multiplier", default=1.5, digits=(3, 2)
    )

    # ============================================================================
    # VALIDITY FIELDS
    # ============================================================================
    valid_from = fields.Date(string="Valid From", default=fields.Date.today)
    valid_to = fields.Date(string="Valid To")

    # ============================================================================
    # CUSTOMER SPECIFIC FIELDS
    # ============================================================================
    partner_id = fields.Many2one("res.partner", string="Specific Customer")
    customer_tier = fields.Selection(
        [
            ("bronze", "Bronze"),
            ("silver", "Silver"),
            ("gold", "Gold"),
            ("platinum", "Platinum"),
        ],
        string="Customer Tier",
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
