# -*- coding: utf-8 -*-
"""
Portal Feedback Resolution Model

Resolution records and actions taken for customer feedback.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PortalFeedbackResolution(models.Model):
    """Portal Feedback Resolution"""

    _name = "portal.feedback.resolution"
    _description = "Portal Feedback Resolution"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "create_date desc"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Resolution Summary",
        required=True,
        tracking=True,
        index=True,
        help="Brief summary of the resolution"
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this resolution"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    feedback_id = fields.Many2one(
        "customer.feedback",
        string="Related Feedback",
        required=True,
        ondelete="cascade",
        help="The feedback this resolution addresses"
    )

    resolved_by_id = fields.Many2one(
        "res.users",
        string="Resolved By",
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        help="User who provided this resolution"
    )

    # ============================================================================
    # RESOLUTION DETAILS
    # ============================================================================
    resolution_date = fields.Datetime(
        string="Resolution Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="Date and time when resolution was provided"
    )

    resolution_type = fields.Selection([
        ('explanation', 'Explanation Provided'),
        ('corrective_action', 'Corrective Action Taken'),
        ('process_improvement', 'Process Improvement'),
        ('policy_change', 'Policy Change'),
        ('training', 'Training Provided'),
        ('escalation', 'Escalated to Management'),
        ('no_action', 'No Action Required'),
        ('other', 'Other')
    ], string='Resolution Type', required=True, tracking=True)

    description = fields.Html(
        string="Resolution Description",
        required=True,
        help="Detailed description of the resolution"
    )

    internal_notes = fields.Text(
        string="Internal Notes",
        help="Internal notes not visible to customer"
    )

    # ============================================================================
    # STATUS AND TRACKING
    # ============================================================================
    status = fields.Selection([
        ('draft', 'Draft'),
        ('implemented', 'Implemented'),
        ('verified', 'Verified'),
        ('customer_notified', 'Customer Notified'),
        ('closed', 'Closed')
    ], string='Status', default='draft', required=True, tracking=True)

    customer_satisfaction = fields.Selection([
        ('very_satisfied', 'Very Satisfied'),
        ('satisfied', 'Satisfied'),
        ('neutral', 'Neutral'),
        ('dissatisfied', 'Dissatisfied'),
        ('very_dissatisfied', 'Very Dissatisfied')
    ], string='Customer Satisfaction', tracking=True)

    # ============================================================================
    # FOLLOW-UP FIELDS
    # ============================================================================
    follow_up_required = fields.Boolean(
        string="Follow-up Required",
        default=False,
        tracking=True,
        help="Whether this resolution requires follow-up"
    )

    follow_up_date = fields.Date(
        string="Follow-up Date",
        help="Date for follow-up action"
    )

    follow_up_notes = fields.Text(
        string="Follow-up Notes",
        help="Notes for follow-up actions"
    )

    # ============================================================================
    # METRICS
    # ============================================================================
    resolution_time_hours = fields.Float(
        string="Resolution Time (Hours)",
        compute='_compute_resolution_time',
        help="Time taken to resolve the feedback"
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('feedback_id.create_date', 'resolution_date')
    def _compute_resolution_time(self):
        """Calculate resolution time in hours"""
        for record in self:
            if record.feedback_id and record.feedback_id.create_date and record.resolution_date:
                delta = record.resolution_date - record.feedback_id.create_date
                record.resolution_time_hours = delta.total_seconds() / 3600
            else:
                record.resolution_time_hours = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_implement_resolution(self):
        """Mark resolution as implemented"""
        self.ensure_one()
        if self.status != 'draft':
            raise UserError(_('Can only implement draft resolutions'))
        
        self.write({'status': 'implemented'})
        self.message_post(body=_('Resolution implemented'))

    def action_verify_resolution(self):
        """Mark resolution as verified"""
        self.ensure_one()
        if self.status != 'implemented':
            raise UserError(_('Can only verify implemented resolutions'))
        
        self.write({'status': 'verified'})
        self.message_post(body=_('Resolution verified'))

    def action_notify_customer(self):
        """Notify customer of resolution"""
        self.ensure_one()
        if self.status not in ('implemented', 'verified'):
            raise UserError(_('Can only notify customer after implementation'))
        
        # Send notification to customer
        self.feedback_id.partner_id.message_post(
            body=_('Your feedback has been addressed: %s') % self.name,
            subject=_('Feedback Resolution: %s') % self.feedback_id.name
        )
        
        self.write({'status': 'customer_notified'})
        self.message_post(body=_('Customer notified of resolution'))

    def action_close_resolution(self):
        """Close the resolution"""
        self.ensure_one()
        if self.status != 'customer_notified':
            raise UserError(_('Must notify customer before closing'))
        
        self.write({'status': 'closed'})
        self.message_post(body=_('Resolution closed'))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('follow_up_date')
    def _check_follow_up_date(self):
        """Validate follow-up date"""
        for record in self:
            if record.follow_up_required and not record.follow_up_date:
                raise ValidationError(_('Follow-up date is required when follow-up is needed'))
            if record.follow_up_date and record.follow_up_date <= fields.Date.today():
                raise ValidationError(_('Follow-up date must be in the future'))

    @api.onchange('follow_up_required')
    def _onchange_follow_up_required(self):
        """Clear follow-up fields when not required"""
        if not self.follow_up_required:
            self.follow_up_date = False
            self.follow_up_notes = False
