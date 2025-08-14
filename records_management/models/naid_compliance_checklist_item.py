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

    name = fields.Char(string="Item Name", required=True, tracking=True,),

    sequence = fields.Integer(string="Sequence", default=10),

    description = fields.Text(string="Item Description"),

    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # CHECKLIST RELATIONSHIPS
    # ============================================================================

    checklist_id = fields.Many2one(

        "mail.message", "res_id", string="Messages", groups="base.group_user"
    )

    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')
