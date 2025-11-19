# -*- coding: utf-8 -*-
"""
Container Access Activity Model

Track individual container access activities for audit compliance, security
monitoring, and operational oversight within the Records Management system.
Provides comprehensive logging of who accessed containers, when, why, and what was done.

Author: Records Management System
Version: 18.0.0.2.29
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ContainerAccessActivity(models.Model):
    """
    Container Access Activity Management

    Tracks individual container access events for audit compliance, security
    monitoring, and operational oversight. Essential for NAID AAA compliance
    and maintaining detailed chain of custody records.
    """

    _name = "container.access.activity"
    _description = "Container Access Activity"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "activity_time desc, id desc"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Activity Reference",
        required=True,
        tracking=True,
        index=True,
        default=lambda self: "New Activity",
        help="Unique reference for this access activity"
    )

    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        store=True,
        help="Formatted display name for the activity"
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True
    )

    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True,
        help="User who created this activity record"
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this activity"
    )

    # ============================================================================
    # PERSONNEL AND AUTHORIZATION
    # ============================================================================
    visitor_id = fields.Many2one(
        "hr.employee",
        string="Visitor/Accessor",
        required=True,
        tracking=True,
        help="Employee or visitor who accessed the container"
    )

    authorized_by_id = fields.Many2one(
        "hr.employee",
        string="Authorized By",
        tracking=True,
        help="Employee who authorized this access"
    )

    supervised_by_id = fields.Many2one(
        "hr.employee",
        string="Supervised By",
        help="Supervising employee present during access"
    )

    approved_by_id = fields.Many2one(
        "hr.employee",
        string="Approved By",
        readonly=True,
        help="Employee who approved the completed activity"
    )

    # ============================================================================
    # CONTAINER AND LOCATION DETAILS
    # ============================================================================
    work_order_id = fields.Many2one(
        "container.access.work.order",
        string="Work Order",
        help="Related work order for this access activity"
    )

    container_id = fields.Many2one(
        "records.container",
        string="Container",
        required=True,
        index=True,
        tracking=True,
        help="Container being accessed"
    )

    location_id = fields.Many2one(
        "stock.location",
        string="Location",
        related="container_id.location_id",
        readonly=True,
        store=True,
        help="Current location of the container"
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="container_id.partner_id",
        readonly=True,
        store=True,
        help="Customer who owns the container"
    )

    container_barcode = fields.Char(
        string="Container Barcode",
        related="container_id.barcode",
        readonly=True,
        help="Barcode of the accessed container"
    )

    # Reflect the container type name from the linked container's type
    container_type = fields.Char(
        related="container_id.container_type_id.name",
        readonly=True,
        store=True,
        string="Container Type",
        help="Type of container accessed"
    )

    # ============================================================================
    # ACTIVITY DETAILS
    # ============================================================================
    activity_type = fields.Selection([
        ('inspection', 'Container Inspection'),
        ('document_retrieval', 'Document Retrieval'),
        ('inventory_check', 'Inventory Verification'),
        ('maintenance', 'Container Maintenance'),
        ('audit', 'Compliance Audit'),
        ('emergency_access', 'Emergency Access'),
        ('relocation', 'Container Relocation'),
        ('destruction_prep', 'Destruction Preparation')
    ], string="Activity Type", required=True, tracking=True,
       help="Type of activity performed on the container")

    activity_time = fields.Datetime(
        string="Activity Start Time",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        index=True,
        help="Date and time when activity started"
    )

    completion_time = fields.Datetime(
        string="Activity Completion Time",
        tracking=True,
        help="Date and time when activity was completed"
    )

    duration_minutes = fields.Integer(
        string="Duration (Minutes)",
        compute='_compute_duration_minutes',
        store=True,
        help="Total duration of the activity in minutes"
    )

    description = fields.Text(
        string="Activity Description",
        required=True,
        help="Detailed description of the activity performed"
    )

    # ============================================================================
    # FINDINGS AND ISSUES
    # ============================================================================
    findings = fields.Text(
        string="Activity Findings",
        help="What was found or observed during the activity"
    )

    issues_found = fields.Boolean(
        string="Issues Found",
        default=False,
        help="Whether any issues were discovered during the activity"
    )

    issue_description = fields.Text(
        string="Issue Description",
        help="Detailed description of any issues found"
    )

    corrective_action_taken = fields.Text(
        string="Corrective Action Taken",
        help="Description of any corrective actions performed"
    )

    follow_up_required = fields.Boolean(
        string="Follow-up Required",
        default=False,
        help="Whether follow-up action is needed"
    )

    # ============================================================================
    # APPROVAL AND AUTHORIZATION
    # ============================================================================
    approval_required = fields.Boolean(
        string="Approval Required",
        default=False,
        help="Whether supervisor approval is required"
    )

    approved = fields.Boolean(
        string="Approved",
        default=False,
        readonly=True,
        help="Whether the activity has been approved"
    )

    approval_date = fields.Datetime(
        string="Approval Date",
        readonly=True,
        help="Date and time when activity was approved"
    )

    approval_notes = fields.Text(
        string="Approval Notes",
        help="Notes from the approving supervisor"
    )

    # ============================================================================
    # DOCUMENTATION AND EVIDENCE
    # ============================================================================
    photo_taken = fields.Boolean(
        string="Photos Taken",
        default=False,
        help="Whether photos were taken during the activity"
    )

    photo_ids = fields.One2many(
        "container.access.photo",
        "activity_id",
        string="Photos",
        help="Photos taken during the activity"
    )

    documents_created = fields.Boolean(
        string="Documents Created",
        default=False,
        help="Whether additional documents were created"
    )

    document_ids = fields.One2many(
        "container.access.document",
        "activity_id",
        string="Documents",
        help="Documents created during the activity"
    )

    report_generated = fields.Boolean(
        string="Report Generated",
        default=False,
        help="Whether a formal report was generated"
    )

    report_id = fields.Many2one(
        "container.access.report",
        string="Generated Report",
        help="Formal report generated for this activity"
    )

    # ============================================================================
    # STATUS AND WORKFLOW
    # ============================================================================
    status = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft', required=True, tracking=True,
       help="Current status of the activity")

    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string="Priority", default='normal', help="Activity priority level")

    # ============================================================================
    # COMPLIANCE AND AUDIT
    # ============================================================================
    naid_compliant = fields.Boolean(
        string="NAID Compliant",
        default=True,
        help="Whether this activity meets NAID standards"
    )

    audit_trail_created = fields.Boolean(
        string="Audit Trail Created",
        default=False,
        readonly=True,
        help="Whether audit trail entry was created"
    )

    chain_of_custody_id = fields.Many2one(
        "chain.of.custody",
        string="Chain of Custody",
        help="Chain of custody record for this activity"
    )

    compliance_notes = fields.Text(
        string="Compliance Notes",
        help="Notes regarding compliance requirements"
    )

    # ============================================================================
    # SECURITY AND ACCESS CONTROL
    # ============================================================================
    access_level_required = fields.Selection([
        ('standard', 'Standard Access'),
        ('restricted', 'Restricted Access'),
        ('confidential', 'Confidential Access'),
        ('secure_vault', 'Secure Vault Access')
    ], string="Access Level Required", default='standard')

    security_clearance_verified = fields.Boolean(
        string="Security Clearance Verified",
        default=False,
        help="Whether security clearance was verified"
    )

    access_granted_time = fields.Datetime(
        string="Access Granted Time",
        help="When physical access was granted"
    )

    access_revoked_time = fields.Datetime(
        string="Access Revoked Time",
        help="When physical access was revoked"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)]
    )

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)]
    )

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)]
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'container_id', 'activity_type', 'visitor_id')
    def _compute_display_name(self):
        """Compute display name with activity details"""
        for activity in self:
            parts = []
            if activity.name and activity.name != _("New Activity"):
                parts.append(activity.name)
            if activity.activity_type:
                parts.append(dict(activity._fields['activity_type'].selection)[activity.activity_type])
            if activity.container_id:
                parts.append(activity.container_id.name)
            if activity.visitor_id:
                parts.append(_("by %s") % activity.visitor_id.name)

            activity.display_name = " - ".join(parts) if parts else _("New Activity")

    @api.depends('activity_time', 'completion_time')
    def _compute_duration_minutes(self):
        """Calculate activity duration in minutes"""
        for activity in self:
            if activity.activity_time and activity.completion_time:
                delta = activity.completion_time - activity.activity_time
                activity.duration_minutes = int(delta.total_seconds() / 60)
            else:
                activity.duration_minutes = 0

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('container_id')
    def _onchange_container_id(self):
        """Update fields when container changes"""
        if self.container_id:
            # Set default activity name
            if not self.name or self.name == _("New Activity"):
                self.name = _("Access: %s") % self.container_id.name

            # Set access level based on container
            if hasattr(self.container_id, 'access_level'):
                self.access_level_required = self.container_id.access_level

    @api.onchange('approval_required')
    def _onchange_approval_required(self):
        """Clear approval fields when not required"""
        if not self.approval_required:
            self.approved = False
            self.approved_by_id = False
            self.approval_date = False
            self.approval_notes = False

    @api.onchange('issues_found')
    def _onchange_issues_found(self):
        """Clear issue description when no issues"""
        if not self.issues_found:
            self.issue_description = False
            self.corrective_action_taken = False
            self.follow_up_required = False

    @api.onchange('activity_type')
    def _onchange_activity_type(self):
        """Update fields based on activity type"""
        if self.activity_type in ['audit', 'inspection']:
            self.approval_required = True
        elif self.activity_type == 'emergency_access':
            self.priority = 'urgent'
            self.approval_required = True

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_activity(self):
        """Start the activity"""
        self.ensure_one()
        if self.status not in ['draft', 'planned']:
            raise UserError(_("Can only start draft or planned activities"))

        # Verify access permissions
        if not self._check_access_permissions():
            raise UserError(_("Insufficient access permissions for this activity"))

        self.write({
            'status': 'in_progress',
            'activity_time': fields.Datetime.now(),
            'access_granted_time': fields.Datetime.now()
        })
        self._create_audit_log('activity_started')
        self.message_post(body=_("Activity started by %s") % self.visitor_id.name)

    def action_complete_activity(self):
        """Complete the activity"""
        self.ensure_one()
        if self.status != 'in_progress':
            raise UserError(_("Can only complete activities in progress"))

        # Validate required fields
        if not self.findings:
            raise UserError(_("Please provide activity findings before completing"))

        completion_time = fields.Datetime.now()

        if self.approval_required:
            self.write({
                'status': 'pending_approval',
                'completion_time': completion_time,
                'access_revoked_time': completion_time
            })
            self.message_post(body=_("Activity completed, pending approval"))
        else:
            self.write({
                'status': 'completed',
                'completion_time': completion_time,
                'access_revoked_time': completion_time
            })
            self.message_post(body=_("Activity completed"))

        self._create_audit_log('activity_completed')

        # Create chain of custody record if needed
        if self.naid_compliant:
            self._create_chain_of_custody()

    def action_approve_activity(self):
        """Approve the activity"""
        self.ensure_one()
        if self.status != 'pending_approval':
            raise UserError(_("Can only approve activities pending approval"))

        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_("Only managers can approve activities"))

        self.write({
            'status': 'approved',
            'approved': True,
            'approved_by_id': self.env.user.employee_id.id if self.env.user.employee_id else False,
            'approval_date': fields.Datetime.now()
        })
        self._create_audit_log('activity_approved')
        self.message_post(body=_("Activity approved by %s") % self.env.user.name)

    def action_cancel_activity(self):
        """Cancel the activity"""
        self.ensure_one()
        if self.status in ('completed', 'approved', 'cancelled'):
            raise UserError(_("Cannot cancel completed, approved, or already cancelled activities"))

        self.write({
            'status': 'cancelled',
            'access_revoked_time': fields.Datetime.now()
        })
        self._create_audit_log('activity_cancelled')
        self.message_post(body=_("Activity cancelled"))

    def action_create_follow_up(self):
        """Create follow-up activity"""
        self.ensure_one()

        follow_up_vals = {
            "name": _("Follow-up: %s") % self.name,
            "container_id": self.container_id.id,
            "visitor_id": self.visitor_id.id,
            "activity_type": self.activity_type,
            "description": _("Follow-up to activity %s") % self.name,
            "priority": "high",
        }

        follow_up = self.create(follow_up_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Follow-up Activity'),
            'res_model': 'container.access.activity',
            'res_id': follow_up.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('approval_required', 'status', 'approved')
    def _check_approval(self):
        """Validate approval requirements"""
        for record in self:
            if (record.approval_required and
                record.status == 'completed' and
                not record.approved):
                raise ValidationError(_(
                    "Activity requiring approval must be approved before completion"
                ))

    @api.constrains('issues_found', 'issue_description')
    def _check_issue_description(self):
        """Validate issue description when issues are found"""
        for record in self:
            if record.issues_found and not record.issue_description:
                raise ValidationError(_(
                    "Issue description is required when issues are found"
                ))

    @api.constrains('activity_time', 'completion_time')
    def _check_activity_times(self):
        """Validate activity time sequence"""
        for record in self:
            if (record.activity_time and record.completion_time and
                record.activity_time > record.completion_time):
                raise ValidationError(_(
                    "Activity start time cannot be after completion time"
                ))

    @api.constrains('access_granted_time', 'access_revoked_time')
    def _check_access_times(self):
        """Validate access time sequence"""
        for record in self:
            if (record.access_granted_time and record.access_revoked_time and
                record.access_granted_time > record.access_revoked_time):
                raise ValidationError(_(
                    "Access granted time cannot be after access revoked time"
                ))

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def _check_access_permissions(self):
        """Check if user has permission for the required access level"""
        self.ensure_one()

        user_groups = self.env.user.groups_id.mapped('name')

        access_requirements = {
            'standard': ['Records User'],
            'restricted': ['Records User', 'Records Manager'],
            'confidential': ['Records Manager'],
            'secure_vault': ['Records Manager', 'Compliance Officer']
        }

        required_groups = access_requirements.get(self.access_level_required, [])
        return any(group in user_groups for group in required_groups)

    def _create_audit_log(self, action_type):
        """Create NAID audit log entry"""
        self.ensure_one()

        if 'naid.audit.log' in self.env:
            audit_vals = {
                "action_type": action_type,
                "user_id": self.env.user.id,
                "timestamp": fields.Datetime.now(),
                "description": _("Container access activity: %s") % action_type,
                "container_id": self.container_id.id,
                "access_activity_id": self.id,
                "visitor_id": self.visitor_id.id if self.visitor_id else False,
                "naid_compliant": self.naid_compliant,
            }
            self.env['naid.audit.log'].create(audit_vals)
            self.audit_trail_created = True

    def _create_chain_of_custody(self):
        """Create chain of custody record"""
        self.ensure_one()

        if 'chain.of.custody' in self.env:
            custody_vals = {
                "name": _("Container Access: %s") % self.name,
                "event_type": "container_access",
                "responsible_user_id": self.visitor_id.user_id.id if self.visitor_id.user_id else self.env.user.id,
                "event_date": self.activity_time,
                "container_id": self.container_id.id,
                "description": self.description,
                "access_activity_id": self.id,
            }
            custody_record = self.env['chain.of.custody'].create(custody_vals)
            self.chain_of_custody_id = custody_record.id

    def get_activity_summary(self):
        """Get activity summary for reporting"""
        self.ensure_one()

        return {
            'activity_reference': self.name,
            'container': self.container_id.name,
            'customer': self.partner_id.name if self.partner_id else 'Unknown',
            'activity_type': dict(self._fields['activity_type'].selection)[self.activity_type],
            'visitor': self.visitor_id.name,
            'start_time': self.activity_time,
            'duration_minutes': self.duration_minutes,
            'issues_found': self.issues_found,
            'status': dict(self._fields['status'].selection)[self.status],
            'naid_compliant': self.naid_compliant,
        }

    @api.model
    def get_access_statistics(self, date_from=None, date_to=None):
        """Get container access statistics"""
        domain = []
        if date_from:
            domain.append(('activity_time', '>=', date_from))
        if date_to:
            domain.append(('activity_time', '<=', date_to))

        activities = self.search(domain)

        stats = {
            'total_activities': len(activities),
            'completed_activities': len(activities.filtered(lambda a: a.status in ['completed', 'approved'])),
            'issues_found': len(activities.filtered('issues_found')),
            'average_duration': sum(activities.mapped('duration_minutes')) / len(activities) if activities else 0,
            'by_type': {},
            'by_container_type': {},
        }

        # Activity type breakdown
        for activity_type in activities.mapped('activity_type'):
            if activity_type:
                # capture loop var in default arg to avoid late-binding
                type_activities = activities.filtered(lambda a, activity_type=activity_type: a.activity_type == activity_type)
                stats['by_type'][activity_type] = {
                    'count': len(type_activities),
                    'issues_rate': len(type_activities.filtered('issues_found')) / len(type_activities) * 100
                }

        # Container type breakdown
        for container_type in activities.mapped('container_type'):
            if container_type:
                # capture loop var in default arg to avoid late-binding
                type_activities = activities.filtered(lambda a, container_type=container_type: a.container_type == container_type)
                stats['by_container_type'][container_type] = {
                    'count': len(type_activities),
                    'avg_duration': sum(type_activities.mapped('duration_minutes')) / len(type_activities)
                }

        return stats

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set defaults and create audit logs"""
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _("New Activity"):
                sequence = self.env['ir.sequence'].next_by_code('container.access.activity')
                vals["name"] = sequence or _("Activity %s") % fields.Datetime.now().strftime("%Y%m%d-%H%M%S")

        activities = super().create(vals_list)

        for activity in activities:
            activity._create_audit_log('activity_created')

        return activities

    def write(self, vals):
        """Override write to track status changes"""
        result = super().write(vals)

        if 'status' in vals:
            for activity in self:
                status_label = dict(activity._fields['status'].selection)[activity.status]
                activity.message_post(body=_("Status changed to %s") % status_label)

        return result

    # Deprecated name_get: rely on computed display_name

    # ============================================================================
    # INTEGRATION METHODS
    # ============================================================================
    def action_view_container(self):
        """View the accessed container"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Container Details'),
            'res_model': 'records.container',
            'res_id': self.container_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_chain_of_custody(self):
        """View chain of custody record"""
        self.ensure_one()
        if not self.chain_of_custody_id:
            raise UserError(_("No chain of custody record available"))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Chain of Custody'),
            'res_model': 'chain.of.custody',
            'res_id': self.chain_of_custody_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_generate_report(self):
        """Generate activity report"""
        self.ensure_one()
        return {
            'type': 'ir.actions.report',
            'report_name': 'records_management.container_access_activity_report',
            'report_type': 'qweb-pdf',
            'data': {'activity_id': self.id},
            'context': self.env.context
        }
