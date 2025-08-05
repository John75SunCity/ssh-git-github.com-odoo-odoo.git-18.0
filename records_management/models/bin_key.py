# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BinKey(models.Model):
    _name = "bin.key"
    _description = "Bin Access Key"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Key Number", required=True, tracking=True, index=True)
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
            ("lost", "Lost"),
            ("damaged", "Damaged"),
            ("retired", "Retired"),
        ],
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # KEY SPECIFICATIONS
    # ============================================================================
    key_code = fields.Char(string="Key Code", index=True, tracking=True)
    description = fields.Text(string="Description")
    key_type = fields.Selection(
        [
            ("physical", "Physical Key"),
            ("electronic", "Electronic Key"),
            ("master", "Master Key"),
            ("backup", "Backup Key"),
        ],
        string="Key Type",
        default="physical",
    )

    # ============================================================================
    # ACCESS CONTROL
    # ============================================================================
    access_level = fields.Selection(
        [
            ("basic", "Basic Access"),
            ("supervisor", "Supervisor Access"),
            ("manager", "Manager Access"),
            ("admin", "Admin Access"),
        ],
        string="Access Level",
        default="basic",
    )

    valid_from = fields.Date(string="Valid From", default=fields.Date.today)
    valid_to = fields.Date(string="Valid To")

    # ============================================================================
    # OWNERSHIP & ASSIGNMENT
    # ============================================================================
    assigned_to = fields.Many2one("res.partner", string="Assigned To")
    current_holder = fields.Many2one("res.users", string="Current Holder")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    unlock_service_ids = fields.One2many(
        "bin.unlock.service", "key_id", string="Unlock Services"
    )
    bin_ids = fields.Many2many("records.bin", string="Accessible Bins")

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate key for use"""
        self.write({"state": "active"})

    def action_report_lost(self):
        """Report key as lost"""
        self.write({"state": "lost"})

    def action_retire(self):
        """Retire key from service"""
        self.write({"state": "retired", "active": False})
