# -*- coding: utf-8 -*-

Container Access Activity Model

Individual activities performed during container access visits.


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ContainerAccessActivity(models.Model):
    """Container Access Activity"""

    _name = "container.access.activity"
    _description = "Container Access Activity"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "activity_time desc"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Activity Description",
        required=True,
        tracking=True,
        index=True,
        help="Brief description of the activity"


    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True


    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this activity record"


        # ============================================================================
    # RELATIONSHIP FIELDS
        # ============================================================================
    visitor_id = fields.Many2one(
        "container.access.visitor",
        string="Visitor",
        required=True,
        ondelete="cascade",
        help="Visitor who performed this activity"


    work_order_id = fields.Many2one(
        "container.access.work.order",
        string="Work Order",
        help="Related container access work order"


    container_id = fields.Many2one(
        "records.container",
        string="Container",
        help="Container involved in this activity"


    location_id = fields.Many2one(
        "records.location",
        string="Location",
        help="Location where activity occurred"


        # ============================================================================
    # ACTIVITY DETAILS
        # ============================================================================
    ,
    activity_type = fields.Selection([))
        ('inspection', 'Inspection'),
        ('retrieval', 'Document Retrieval'),
        ('addition', 'Document Addition'),
        ('maintenance', 'Maintenance'),
        ('audit', 'Audit'),
        ('inventory', 'Inventory Check'),
        ('photography', 'Photography'),
        ('sampling', 'Sampling'),
        ('other', 'Other')


    activity_time = fields.Datetime(
        string="Activity Time",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="When this activity was performed"


    duration_minutes = fields.Integer(
        ,
    string="Duration (Minutes)",
        help="How long this activity took"


    description = fields.Text(
        string="Detailed Description",
        help="Detailed description of what was done"


        # ============================================================================
    # RESULTS AND FINDINGS
        # ============================================================================
    findings = fields.Text(
        string="Findings",
        help="Any findings or observations from this activity"


    issues_found = fields.Boolean(
        string="Issues Found",
        default=False,
        tracking=True,
        help="Whether any issues were discovered"


    issue_description = fields.Text(
        string="Issue Description",
        help="Description of issues found"


        # ============================================================================
    # APPROVAL AND AUTHORIZATION
        # ============================================================================
    authorized_by_id = fields.Many2one(
        "res.users",
        string="Authorized By",
        help="Who authorized this activity"


    supervised_by_id = fields.Many2one(
        "hr.employee",
        string="Supervised By",
        help="Employee who supervised this activity"


    approval_required = fields.Boolean(
        string="Approval Required",
        default=False,
        help="Whether this activity requires approval"


    approved = fields.Boolean(
        string="Approved",
        default=False,
        tracking=True,
        help="Whether this activity has been approved"


    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        help="Who approved this activity"


    approval_date = fields.Datetime(
        string="Approval Date",
        help="When this activity was approved"


        # ============================================================================
    # DOCUMENTATION
        # ============================================================================
    photo_taken = fields.Boolean(
        string="Photos Taken",
        default=False,
        help="Whether photos were taken during this activity"


    documents_created = fields.Boolean(
        string="Documents Created",
        default=False,
        help="Whether any documents were created"


    report_generated = fields.Boolean(
        string="Report Generated",
        default=False,
        help="Whether a report was generated"


        # ============================================================================
    # STATUS
        # ============================================================================
    ,
    status = fields.Selection([))
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('pending_approval', 'Pending Approval')


        # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance):
            pass
    activity_ids = fields.One2many("mail.activity", "res_id",,
    string="Activities"),
    message_follower_ids = fields.One2many("mail.followers", "res_id",,
    string="Followers"),
    message_ids = fields.One2many("mail.message", "res_id",,
    string="Messages")

        # ============================================================================
    # ACTION METHODS
        # ============================================================================
    def action_start_activity(self):
        """Start the activity"""
        self.ensure_one()
        if self.status != 'planned':
            raise UserError(_('Can only start planned activities'))

        self.write({)}
            'status': 'in_progress',
            'activity_time': fields.Datetime.now()

        self.message_post(body=_('Activity started'))

    def action_complete_activity(self):
        """Complete the activity"""
        self.ensure_one()
        if self.status != 'in_progress':
            raise UserError(_('Can only complete activities in progress'))

        if self.approval_required:
            self.write({'status': 'pending_approval'})
            self.message_post(body=_('Activity completed, pending approval'))
        else:
            self.write({'status': 'completed'})
            self.message_post(body=_('Activity completed'))

    def action_approve_activity(self):
        """Approve the activity"""
        self.ensure_one()
        if self.status != 'pending_approval':
            raise UserError(_('Can only approve activities pending approval'))

        self.write({)}
            'status': 'completed',
            'approved': True,
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now()

        self.message_post(body=_('Activity approved and completed'))

    def action_cancel_activity(self):
        """Cancel the activity"""
        self.ensure_one()
        if self.status in ('completed', 'cancelled'):
            raise UserError(_('Cannot cancel completed or already cancelled activities'))

        self.write({'status': 'cancelled'})
        self.message_post(body=_('Activity cancelled'))

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains('approval_required', 'approved')
    def _check_approval(self):
        """Validate approval requirements"""
        for record in self:
            if record.approval_required and record.status == 'completed' and not record.approved:
                raise ValidationError(_('Activity requiring approval must be approved before completion'))

    @api.constrains('issues_found', 'issue_description')
    def _check_issue_description(self):
        """Validate issue description when issues are found"""
        for record in self:
            if record.issues_found and not record.issue_description:
                raise ValidationError(_('Issue description is required when issues are found'))

    @api.onchange('approval_required')
    def _onchange_approval_required(self):
        """Clear approval fields when not required"""
        if not self.approval_required:
            self.approved = False
            self.approved_by_id = False
            self.approval_date = False

    @api.onchange('issues_found')
    def _onchange_issues_found(self):
        """Clear issue description when no issues"""
        if not self.issues_found:
            self.issue_description = False
))))))))))))))))))))
