# -*- coding: utf-8 -*-

from odoo import models, fields, api

class RecordsContainerType(models.Model):
    _name = "records.container.type"
    _description = "Records Container Type"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Container Type Name", required=True, tracking=True, index=True
    ),
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    ),
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("archived", "Archived")],
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # CONTAINER SPECIFICATIONS
    # ============================================================================
    )
    code = fields.Char(string="Container Code", required=True, index=True),
    description = fields.Text(string="Description")
    dimensions = fields.Char(string="Standard Dimensions"),
    weight_capacity = fields.Float(
        string="Weight Capacity (lbs)", digits="Stock Weight", default=0.0
    )
    )
    volume_capacity = fields.Float(
        string="Volume Capacity (cubic feet)", digits="Stock Weight", default=0.0
    )

    # ============================================================================
    # BUSINESS FIELDS
    # ============================================================================
    standard_rate = fields.Float(
        string="Standard Monthly Rate", digits="Product Price", default=0.0
    )
    )
    setup_fee = fields.Float(string="Setup Fee", digits="Product Price", default=0.0)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    container_ids = fields.One2many(
        "records.container", "container_type_id", string="Containers"
    )
    )
    container_count = fields.Integer(
        string="Container Count", compute="_compute_container_count", store=True
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)        "mail.followers", "res_id", string="Followers"
    self.write({"state": "archived", "active": False})