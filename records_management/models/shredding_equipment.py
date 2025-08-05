# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ShreddingEquipment(models.Model):
    _name = "shredding.equipment"
    _description = "Shredding Equipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Equipment Name", required=True, tracking=True, index=True
    )
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
            ("available", "Available"),
            ("in_use", "In Use"),
            ("maintenance", "Maintenance"),
            ("retired", "Retired"),
        ],
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # EQUIPMENT SPECIFICATIONS
    # ============================================================================
    equipment_type = fields.Selection(
        [
            ("paper_shredder", "Paper Shredder"),
            ("hard_drive_crusher", "Hard Drive Crusher"),
            ("media_destroyer", "Media Destroyer"),
            ("industrial_shredder", "Industrial Shredder"),
        ],
        string="Equipment Type",
        required=True,
    )

    manufacturer = fields.Char(string="Manufacturer")
    model = fields.Char(string="Model")
    serial_number = fields.Char(string="Serial Number", index=True)
    capacity_per_hour = fields.Float(
        string="Capacity per Hour (lbs)", digits="Stock Weight", default=0.0
    )
    security_level = fields.Selection(
        [
            ("level_1", "Level 1"),
            ("level_2", "Level 2"),
            ("level_3", "Level 3"),
            ("level_4", "Level 4"),
            ("level_5", "Level 5"),
            ("level_6", "Level 6"),
        ],
        string="Security Level",
        default="level_3",
    )

    # ============================================================================
    # MAINTENANCE TRACKING
    # ============================================================================
    purchase_date = fields.Date(string="Purchase Date")
    last_maintenance_date = fields.Date(string="Last Maintenance Date")
    next_maintenance_date = fields.Date(string="Next Maintenance Date")
    maintenance_notes = fields.Text(string="Maintenance Notes")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    service_ids = fields.Many2many("shredding.service", string="Shredding Services")

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_make_available(self):
        """Make equipment available"""
        self.write({"state": "available"})

    def action_start_maintenance(self):
        """Start maintenance"""
        self.write({"state": "maintenance"})

    def action_complete_maintenance(self):
        """Complete maintenance"""
        self.write({"state": "available", "last_maintenance_date": fields.Date.today()})
