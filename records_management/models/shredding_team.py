# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ShreddingTeam(models.Model):
    _name = "shredding.team"
    _description = "Shredding Team"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Team Name", required=True, tracking=True, index=True),
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("inactive", "Inactive")],
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # TEAM DETAILS
    # ============================================================================
    description = fields.Text(string="Description")
    team_leader_id = fields.Many2one("res.users", string="Team Leader")
    member_ids = fields.Many2many("res.users", string="Team Members")
    specialization = fields.Selection(
        [
            ("paper", "Paper Documents"),
            ("electronic", "Electronic Media"),
            ("mixed", "Mixed Media"),
            ("confidential", "Confidential Documents"),
        ],
        string="Specialization",
        default="paper",
    )

    # ============================================================================
    # CAPACITY & SCHEDULING
    # ============================================================================
    max_capacity_per_day = fields.Float(
        string="Max Capacity per Day (lbs)", digits="Stock Weight", default=0.0
    working_hours_start = fields.Float(string="Working Hours Start", default=8.0)
    working_hours_end = fields.Float(string="Working Hours End", default=17.0)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    service_ids = fields.One2many(
        "shredding.service", "team_id", string="Shredding Services"
    service_count = fields.Integer(
        string="Service Count", compute="_compute_service_count", store=True
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)        "mail.followers", "res_id", string="Followers"
    ))