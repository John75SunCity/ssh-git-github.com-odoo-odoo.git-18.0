# -*- coding: utf-8 -*-

from odoo import models, fields, api

class RecordsBin(models.Model):
    _name = "records.bin"
    _description = "Records Storage Bin"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Bin Number", required=True, tracking=True, index=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("locked", "Locked"),
            ("maintenance", "Maintenance"),
            ("retired", "Retired"),
        ],
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # BIN SPECIFICATIONS
    # ============================================================================
    barcode = fields.Char(string="Barcode", index=True, tracking=True)
    description = fields.Text(string="Description")
    location_id = fields.Many2one("records.location", string="Location")
    bin_type = fields.Selection(
        [
            ("document", "Document Storage"),
            ("file", "File Storage"),
            ("archive", "Archive Storage"),
            ("temporary", "Temporary Storage"),
        ],
        string="Bin Type",
        default="document",
    )

    capacity = fields.Float(
        string="Capacity (Cubic Feet)", digits="Stock Weight", default=0.0
    )
    current_usage = fields.Float(
        string="Current Usage (%)", digits="Stock Weight", default=0.0
    )

    # ============================================================================
    # SECURITY & ACCESS
    # ============================================================================
    requires_key = fields.Boolean(string="Requires Key Access", default=True)
    security_level = fields.Selection(
        [
            ("low", "Low Security"),
            ("medium", "Medium Security"),
            ("high", "High Security"),
            ("maximum", "Maximum Security"),
        ],
        string="Security Level",
        default="medium",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    unlock_service_ids = fields.One2many(
        "bin.unlock.service", "bin_id", string="Unlock Services"
    )
    partner_id = fields.Many2one("res.partner", string="Customer")

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)        "mail.followers", "res_id", string="Followers"
    )