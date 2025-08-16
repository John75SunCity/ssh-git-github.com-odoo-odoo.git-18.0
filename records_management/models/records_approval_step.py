# -*- coding: utf-8 -*-
"""
Records Approval Step Management
"""

import logging

from odoo import models, fields, api, _



_logger = logging.getLogger(__name__)

class RecordsApprovalStep(models.Model):
    """
    Records Approval Step Management
    Manages approval workflow steps for records operations
    """

    _name = 'records.approval.step'
    _description = 'Records Approval Step'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Step Name', required=True, tracking=True)
    description = fields.Text(string='Step Description', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Step Manager', 
                            default=lambda self: self.env.user, tracking=True)

    # ==========================================
    # WORKFLOW CONFIGURATION
    # ==========================================
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    step_type = fields.Selection([
        ('approval', 'Approval Required'),
        ('notification', 'Notification Only'),
        ('verification', 'Verification Required'),
        ('documentation', 'Documentation Required')
    ], string='Step Type', required=True, tracking=True)

    # ==========================================
    # APPROVAL SETTINGS
    # ==========================================
    approver_user_id = fields.Many2one('res.users', string='Approver', tracking=True)
    approval_group_id = fields.Many2one('res.groups', string='Approval Group', tracking=True)

    # ==========================================
    # CONDITIONS
    # ==========================================
    condition_field = fields.Char(string='Condition Field', tracking=True)
    condition_operator = fields.Selection([
        ('=', 'Equal to'),
        ('!=', 'Not equal to'),
        ('>', 'Greater than'),
        ('<', 'Less than'),
        ('>=', 'Greater than or equal'),
        ('<=', 'Less than or equal'),
        ('in', 'In'),
        ('not in', 'Not in')
    ], string='Condition Operator', tracking=True)
    condition_value = fields.Char(string='Condition Value', tracking=True)

    # ==========================================
    # TIMING
    # ==========================================
    timeout_days = fields.Integer(string='Timeout (Days)', tracking=True)
    is_mandatory = fields.Boolean(string='Mandatory Step', default=True, tracking=True)

    # ==========================================
    # STATUS
    # ==========================================
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('skipped', 'Skipped')
    ], string='Status', default='pending', tracking=True, required=True)

    # ==========================================
    # NOTES
    # ==========================================
    notes = fields.Text(string='Notes', tracking=True)
    approval_notes = fields.Text(string='Approval Notes', tracking=True)
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')

    # ==========================================
    # WORKFLOW METHODS
    # ==========================================
    def action_approve(self):
        """Approve this step"""

        self.ensure_one()
        if self.state != 'pending':
            return

        self.write({'state': 'approved'})
        self.message_post(body=_('Step approved'))

    def action_reject(self):
        """Reject this step"""

        self.ensure_one()
        if self.state != 'pending':
            return

        self.write({'state': 'rejected'})
        self.message_post(body=_('Step rejected'))

    def action_skip(self):
        """Skip this step"""

        self.ensure_one()
        if self.is_mandatory:
            return

        self.write({'state': 'skipped'})
        self.message_post(body=_('Step skipped'))
