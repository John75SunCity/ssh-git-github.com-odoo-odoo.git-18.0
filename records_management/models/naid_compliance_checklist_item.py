# -*- coding: utf-8 -*-
"""
NAID Compliance Checklist Item Model

Model for individual checklist items for NAID compliance.
"""

from odoo import fields, models




class NaidComplianceChecklistItem(models.Model):
    """Individual checklist items for NAID compliance"""

    _name = "naid.compliance.checklist.item"
    _description = "NAID Compliance Checklist Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Item Name", required=True, tracking=True)

    sequence = fields.Integer(string="Sequence", default=10)

    description = fields.Text(string="Item Description")

    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # CHECKLIST RELATIONSHIPS
    # ============================================================================

    checklist_id = fields.Many2one(
        "naid.compliance.checklist",
        string="Checklist",
        required=True,
        ondelete="cascade",
    )

    category = fields.Selection(
        [
            ("security", "Security"),
            ("operations", "Operations"),
            ("training", "Training"),
            ("documentation", "Documentation"),
            ("equipment", "Equipment"),
        ],
        string="Category",
        required=True,
    )

    # ============================================================================
    # COMPLIANCE TRACKING
    # ============================================================================

    is_compliant = fields.Boolean(string="Compliant", default=False, tracking=True)

    compliance_date = fields.Date(string="Compliance Date")

    verified_by_id = fields.Many2one("res.users", string="Verified By")

    evidence_attachment = fields.Binary(string="Evidence")

    notes = fields.Text(string="Notes")

    # ============================================================================
    # REQUIREMENTS
    # ============================================================================

    is_mandatory = fields.Boolean(string="Mandatory", default=True)

    risk_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Risk Level",
        default="medium",
    )

    deadline = fields.Date(string="Deadline")

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================

    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        auto_join=True,
        groups="base.group_user",
    )

    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers", groups="base.group_user"
    )

    message_ids = fields.One2many(

    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')
        "mail.message", "res_id", string="Messages", groups="base.group_user"
    )
