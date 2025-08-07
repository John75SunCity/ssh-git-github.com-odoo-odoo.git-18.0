# -*- coding: utf-8 -*-

from odoo import models, fields, api

class BarcodeStorageBox(models.Model):
    _name = "barcode.storage.box"
    _description = "Barcode Storage Box"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Box Name", required=True, tracking=True, index=True),
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("full", "Full"),
            ("archived", "Archived"),
        ],
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # BARCODE MANAGEMENT
    # ============================================================================
    barcode = fields.Char(string="Box Barcode", required=True, index=True)
    barcode_product_ids = fields.One2many(
        "barcode.product", "storage_box_id", string="Barcode Products"
    )

    # ============================================================================
    # PHYSICAL SPECIFICATIONS
    # ============================================================================
    location_id = fields.Many2one("records.location", string="Storage Location")
    box_type = fields.Selection(
        [
            ("standard", "Standard Box"),
            ("large", "Large Box"),
            ("small", "Small Box"),
            ("custom", "Custom Size"),
        ],
        string="Box Type",
        default="standard",
    )

    capacity = fields.Integer(string="Storage Capacity", default=100)
    current_count = fields.Integer(
        string="Current Count", compute="_compute_current_count", store=True
    available_space = fields.Integer(
        string="Available Space", compute="_compute_available_space", store=True
    )

    # ============================================================================
    # PHYSICAL DIMENSIONS
    # ============================================================================
    length = fields.Float(string="Length (cm)", default=30.0)
    width = fields.Float(string="Width (cm)", default=20.0)
    height = fields.Float(string="Height (cm)", default=15.0)
    weight_empty = fields.Float(string="Empty Weight (kg)", default=0.5)
    weight_current = fields.Float(
        string="Current Weight (kg)", compute="_compute_current_weight", store=True
    )

    # ============================================================================
    # STATUS & TRACKING
    # ============================================================================
    is_full = fields.Boolean(string="Is Full", compute="_compute_is_full", store=True)
    last_accessed = fields.Datetime(string="Last Accessed")
    created_date = fields.Date(string="Created Date", default=fields.Date.today)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one("res.partner", string="Customer")
    department_id = fields.Many2one("records.department", string="Department")

    # ============================================================================
    # NOTES & DOCUMENTATION
    # ============================================================================
    description = fields.Text(string="Description")
    notes = fields.Text(string="Internal Notes")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    # Missing inverse field for barcode.product One2many relationship
    product_id = fields.Many2one("barcode.product", string="Product")

    # # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)        "mail.followers", "res_id", string="Followers"
    )    @api.depends("capacity", "current_count")
    def _compute_available_space(self):
        for box in self:
            box.available_space = max(0, box.capacity - box.current_count)

    @api.depends("current_count", "capacity")
    def _compute_is_full(self):
        for box in self:
            box.is_full = box.current_count >= box.capacity

    @api.depends("barcode_product_ids", "barcode_product_ids.weight", "weight_empty")
    def _compute_current_weight(self):
        for box in self:
            product_weight = sum(box.barcode_product_ids.mapped("weight"))
            box.weight_current = box.weight_empty + product_weight

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_full(self):
        """Mark storage box as full"""
        self.write({"state": "full"})

    def action_archive_box(self):
        """Archive storage box"""
        self.write({"state": "archived"})

    def action_add_barcode_product(self):
        """Open wizard to add barcode product to this box"""
        return {
            "type": "ir.actions.act_window",
            "name": "Add Barcode Product",
            "res_model": "barcode.product",
            "view_mode": "form",
            "target": "new",
            "context": {"default_storage_box_id": self.id},
        })
