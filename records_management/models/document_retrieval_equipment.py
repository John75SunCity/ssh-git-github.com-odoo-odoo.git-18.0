# -*- coding: utf-8 -*-
"""
Document Retrieval Equipment Model

Equipment used for document retrieval operations including scanners,
carts, tablets, and maintenance tracking.
"""

from odoo import models, fields


class DocumentRetrievalEquipment(models.Model):
    """Equipment used for document retrieval operations"""

    _name = "document.retrieval.equipment"
    _description = "Document Retrieval Equipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Equipment Name", required=True, tracking=True, index=True
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
    # EQUIPMENT TYPE FIELDS
    # ============================================================================
    equipment_type = fields.Selection(
        [
            ("scanner", "Document Scanner"),
            ("cart", "Transport Cart"),
            ("ladder", "Storage Ladder"),
            ("tablet", "Mobile Tablet"),
            ("camera", "Digital Camera"),
            ("vehicle", "Transport Vehicle"),
            ("tools", "Hand Tools"),
            ("safety", "Safety Equipment"),
        ],
        string="Equipment Type",
        required=True,
    )

    # ============================================================================
    # STATUS AND AVAILABILITY FIELDS
    # ============================================================================
    status = fields.Selection(
        [
            ("available", "Available"),
            ("in_use", "In Use"),
            ("maintenance", "Under Maintenance"),
            ("retired", "Retired"),
        ],
        string="Status",
        default="available",
        tracking=True,
    )

    location_id = fields.Many2one("records.location", string="Current Location")
    assigned_to_id = fields.Many2one("hr.employee", string="Assigned To")

    # ============================================================================
    # SPECIFICATION FIELDS
    # ============================================================================
    model = fields.Char(string="Model")
    serial_number = fields.Char(string="Serial Number", tracking=True)
    purchase_date = fields.Date(string="Purchase Date")
    warranty_expiry = fields.Date(string="Warranty Expiry")

    # ============================================================================
    # MAINTENANCE FIELDS
    # ============================================================================
    last_maintenance = fields.Date(string="Last Maintenance")
    next_maintenance = fields.Date(string="Next Maintenance")
    maintenance_notes = fields.Text(string="Maintenance Notes")

    # ============================================================================
    # USAGE TRACKING FIELDS
    # ============================================================================
    usage_hours = fields.Float(string="Total Usage Hours", digits=(10, 2))
    current_work_order_id = fields.Many2one(
        "document.retrieval.work.order", string="Current Work Order"
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
