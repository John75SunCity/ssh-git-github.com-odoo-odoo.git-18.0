# -*- coding: utf-8 -*-
"""
FSM Reschedule Wizard

This wizard provides comprehensive FSM task rescheduling functionality with
integrated notifications, audit logging, and workflow management for the
Records Management system.

Key Features:
- Complete FSM task rescheduling with date validation
- Automated customer notifications via email/SMS
- Integration with FSM notification system
- Comprehensive audit logging and compliance tracking
- Multi-stakeholder approval workflow
- Resource availability checking and optimization
- Route impact analysis and updates

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FsmRescheduleWizard(models.TransientModel):
    """
    Comprehensive FSM Task Reschedule Wizard

    Handles complete workflow for rescheduling field service tasks including
    customer notifications, resource management, and compliance logging.
    """
    _name = "fsm.reschedule.wizard"
    _description = "FSM Reschedule Wizard"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Reschedule Reference",
        required=True,
        default="New Reschedule Request",
        tracking=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
        readonly=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="Requested By",
        default=lambda self: self.env.user,
        tracking=True,
        readonly=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # FSM TASK RELATIONSHIP
    # ============================================================================
    task_id = fields.Many2one(
        "fsm.task",
        string="FSM Task",
        required=True,
        default=lambda self: self.env.context.get('active_id'),
        help="Field Service Management task to reschedule"
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="task_id.partner_id",
        readonly=True,
        store=True
    )
    project_id = fields.Many2one(
        "project.project",
        string="Project",
        related="task_id.project_id",
        readonly=True,
        store=True
    )

    # ============================================================================
    # SCHEDULING DETAILS
    # ============================================================================
    current_date = fields.Datetime(
        string="Current Scheduled Date",
        related="task_id.planned_date_begin",
        readonly=True
    )
    new_date = fields.Datetime(
        string="New Planned Date",
        required=True,
        tracking=True,
        help="New scheduled date and time for the task"
    )
    new_date_end = fields.Datetime(
        string="New End Date",
        help="New scheduled end date and time (auto-calculated if not provided)"
    )
    duration_hours = fields.Float(
        string="Estimated Duration (Hours)",
        default=2.0,
        help="Estimated duration for the rescheduled task"
    )

    # ============================================================================
    # RESCHEDULE REQUEST DETAILS
    # ============================================================================
    reason = fields.Selection([
        ('customer_request', 'Customer Request'),
        ('weather', 'Weather Conditions'),
        ('equipment_issue', 'Equipment Issue'),
        ('technician_unavailable', 'Technician Unavailable'),
        ('traffic_delay', 'Traffic/Access Issue'),
        ('emergency', 'Emergency Priority Change'),
        ('resource_conflict', 'Resource Conflict'),
        ('other', 'Other')
    ], string="Reschedule Reason", required=True, tracking=True)

    reason_details = fields.Text(
        string="Detailed Reason",
        required=True,
        help="Detailed explanation for the reschedule request"
    )

    urgency = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string="Urgency Level", default='medium', tracking=True)

    # ============================================================================
    # NOTIFICATION AND COMMUNICATION
    # ============================================================================
    notify_customer = fields.Boolean(
        string="Notify Customer",
        default=True,
        help="Send notification to customer about reschedule"
    )
    notification_method = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Email + SMS'),
        ('portal', 'Portal Notification'),
        ('phone', 'Phone Call Required')
    ], string="Notification Method", default='email')

    customer_message = fields.Text(
        string="Customer Message",
        help="Custom message to include in customer notification"
    )

    internal_notes = fields.Text(
        string="Internal Notes",
        help="Internal notes for team members (not sent to customer)"
    )

    # ============================================================================
    # APPROVAL AND WORKFLOW
    # ============================================================================
    requires_approval = fields.Boolean(
        string="Requires Manager Approval",
        compute="_compute_requires_approval",
        store=True,
        help="Indicates if this reschedule requires manager approval"
    )
    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        readonly=True,
        tracking=True
    )
    approval_date = fields.Datetime(
        string="Approval Date",
        readonly=True
    )
    approval_notes = fields.Text(
        string="Approval Notes",
        readonly=True
    )

    # ============================================================================
    # RESOURCE AND IMPACT ANALYSIS
    # ============================================================================
    technician_id = fields.Many2one(
        "res.users",
        string="Assigned Technician",
        related="task_id.user_ids",
        readonly=True
    )
    resource_available = fields.Boolean(
        string="Resources Available",
        compute="_compute_resource_availability",
        help="Indicates if required resources are available for new date"
    )
    route_impact = fields.Text(
        string="Route Impact Analysis",
        compute="_compute_route_impact",
        help="Analysis of impact on other scheduled tasks and routes"
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rejected', 'Rejected')
    ], string="Status", default='draft', tracking=True, readonly=True)

    # ============================================================================
    # COMPLIANCE AND AUDIT
    # ============================================================================
    reschedule_count = fields.Integer(
        string="Reschedule Count",
        compute="_compute_reschedule_count",
        help="Number of times this task has been rescheduled"
    )
    compliance_notes = fields.Text(
        string="Compliance Notes",
        help="Notes for compliance and audit purposes"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    reschedule_reason = fields.Text(string="Reschedule Reason", required=True)
    schedule_date = fields.Datetime(string="New Schedule Date", required=True)
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('new_date', 'current_date', 'urgency', 'reason')
    def _compute_requires_approval(self):
        """Determine if reschedule requires manager approval"""
        for record in self:
            requires_approval = False

            if record.current_date and record.new_date:
                # Calculate time difference
                time_diff = record.new_date - record.current_date

                # Require approval for significant changes
                if abs(time_diff.days) > 7:  # More than a week change
                    requires_approval = True
                elif record.urgency == 'urgent':
                    requires_approval = True
                elif record.reason in ['emergency', 'equipment_issue']:
                    requires_approval = True

            record.requires_approval = requires_approval

    @api.depends('new_date', 'technician_id', 'duration_hours')
    def _compute_resource_availability(self):
        """Check if resources are available for the new date"""
        for record in self:
            available = True

            if record.new_date and record.technician_id:
                # Check for conflicting tasks
                conflicting_tasks = self.env['fsm.task'].search([
                    ('user_ids', 'in', record.technician_id.ids),
                    ('planned_date_begin', '<=', record.new_date + timedelta(hours=record.duration_hours)),
                    ('planned_date_end', '>=', record.new_date),
                    ('id', '!=', record.task_id.id),
                    ('stage_id.is_closed', '=', False)
                ])

                if conflicting_tasks:
                    available = False

            record.resource_available = available

    @api.depends('new_date', 'task_id')
    def _compute_route_impact(self):
        """Analyze impact on routes and other scheduled tasks"""
        for record in self:
            impact_notes = []

            if record.new_date and record.task_id:
                # Find other tasks on the same day
                same_day_tasks = self.env['fsm.task'].search([
                    ('planned_date_begin', '>=', record.new_date.replace(hour=0, minute=0, second=0)),
                    ('planned_date_begin', '<', record.new_date.replace(hour=23, minute=59, second=59)),
                    ('id', '!=', record.task_id.id),
                    ('stage_id.is_closed', '=', False)
                ])

                if same_day_tasks:
                    impact_notes.append(_("Found %d other tasks on the same day", len(same_day_tasks)))

                # Check for route optimization impact
                if record.task_id.partner_id:
                    nearby_tasks = same_day_tasks.filtered(
                        lambda t: t.partner_id and t.partner_id.city == record.task_id.partner_id.city
                    )
                    if nearby_tasks:
                        impact_notes.append(_("Route optimization possible with %d nearby tasks", len(nearby_tasks)))

            record.route_impact = "\n".join(impact_notes) if impact_notes else _("No significant route impact identified")

    @api.depends('task_id')
    def _compute_reschedule_count(self):
        """Count how many times this task has been rescheduled"""
        for record in self:
            if record.task_id:
                reschedule_count = self.search_count([
                    ('task_id', '=', record.task_id.id),
                    ('state', '=', 'completed')
                ])
                record.reschedule_count = reschedule_count
            else:
                record.reschedule_count = 0

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('new_date', 'duration_hours')
    def _onchange_new_date(self):
        """Auto-calculate end date when start date or duration changes"""
        if self.new_date and self.duration_hours:
            self.new_date_end = self.new_date + timedelta(hours=self.duration_hours)

    @api.onchange('reason')
    def _onchange_reason(self):
        """Set default messages based on reason"""
        reason_messages = {
            'customer_request': _("Customer has requested to reschedule the service appointment."),
            'weather': _("Service rescheduled due to adverse weather conditions."),
            'equipment_issue': _("Equipment maintenance required - service rescheduled."),
            'technician_unavailable': _("Assigned technician unavailable - reassigning schedule."),
            'traffic_delay': _("Access or traffic issues require schedule adjustment."),
            'emergency': _("Emergency priority change requires immediate rescheduling."),
            'resource_conflict': _("Resource conflict identified - optimizing schedule."),
        }

        if self.reason and self.reason in reason_messages:
            self.customer_message = reason_messages[self.reason]

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_submit_request(self):
        """Submit the reschedule request"""

        self.ensure_one()

        if self.requires_approval:
            self.write({'state': 'pending_approval'})
            self._create_approval_activity()
        else:
            self.write({'state': 'approved'})
            return self.action_execute_reschedule()

        return self.action_return_wizard()

    def action_approve_request(self):
        """Approve the reschedule request (manager action)"""

        self.ensure_one()

        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_("Only managers can approve reschedule requests."))

        self.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now()
        })

        return self.action_execute_reschedule()

    def action_reject_request(self):
        """Reject the reschedule request"""

        self.ensure_one()

        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_("Only managers can reject reschedule requests."))

        self.write({'state': 'rejected'})

        # Notify requester of rejection
        self.message_post(
            body=_("Reschedule request has been rejected by %s", self.env.user.name)
        )

        return {'type': 'ir.actions.act_window_close'}

    def action_execute_reschedule(self):
        """Execute the approved reschedule"""

        self.ensure_one()

        if self.state != 'approved':
            raise UserError(_("Only approved requests can be executed."))

        self.write({'state': 'in_progress'})

        # Store original date for logging
        original_date = self.current_date

        # Update the FSM task
        task_updates = {
            'planned_date_begin': self.new_date,
            'planned_date_end': self.new_date_end or self.new_date,
        }

        # Add custom field if it exists
        if hasattr(self.task_id, 'reschedule_reason'):
            reason_label = dict(self._fields['reason'].selection)[self.reason]
            task_updates['reschedule_reason'] = _("%s: %s", reason_label, self.reason_details)

        self.task_id.write(task_updates)

        # Create audit log
        self._create_audit_log(original_date)

        # Send notifications
        if self.notify_customer:
            self._send_customer_notification(original_date)

        # Create FSM notification for tracking
        self._create_fsm_notification()

        # Post message on task
        reason_label = dict(self._fields['reason'].selection)[self.reason]
        self.task_id.message_post(
            body=_("Task rescheduled from %s to %s. Reason: %s - %s",
                original_date, self.new_date, reason_label, self.reason_details)
        )

        self.write({'state': 'completed'})

        return {'type': 'ir.actions.act_window_close'}

    def action_cancel_request(self):
        """Cancel the reschedule request"""

        self.ensure_one()
        self.write({'state': 'cancelled'})
        return {'type': 'ir.actions.act_window_close'}

    # ============================================================================
    # NOTIFICATION METHODS
    # ============================================================================
    def _send_customer_notification(self, original_date):
        """Send notification to customer about the reschedule"""
        self.ensure_one()

        if not self.partner_id:
            return

        subject = _("Service Appointment Rescheduled - %s", self.task_id.name)

        # Format dates properly for email
        original_date_str = original_date.strftime('%B %d, %Y at %I:%M %p') if original_date else _('N/A')
        new_date_str = self.new_date.strftime('%B %d, %Y at %I:%M %p')
        reason_display = self.customer_message or dict(self._fields['reason'].selection)[self.reason]

        body_html = _("""
        <p>Dear %(customer_name)s,</p>

        <p>Your service appointment has been rescheduled:</p>

        <ul>
            <li><strong>Original Date:</strong> %(original_date)s</li>
            <li><strong>New Date:</strong> %(new_date)s</li>
            <li><strong>Service:</strong> %(service_name)s</li>
            <li><strong>Reason:</strong> %(reason)s</li>
        </ul>

        <p>We apologize for any inconvenience this may cause. If you have any questions or concerns, please contact us immediately.</p>

        <p>Thank you for your understanding.</p>
        """, {
            'customer_name': self.partner_id.name,
            'original_date': original_date_str,
            'new_date': new_date_str,
            'service_name': self.task_id.name,
            'reason': reason_display
        })

        # Send email notification
        if self.notification_method in ['email', 'both']:
            self.task_id.message_post(
                partner_ids=[self.partner_id.id],
                subject=subject,
                body=body_html,
                message_type='email'
            )

        # Send SMS if configured
        if self.notification_method in ['sms', 'both'] and self.partner_id.mobile:
            sms_body = _("Service appointment rescheduled to %s. Details: %s. Contact us with questions.",
                        self.new_date.strftime('%m/%d %I:%M %p'), self.task_id.name)
            self.partner_id._send_sms(sms_body)

    def _create_fsm_notification(self):
        """Create FSM notification record for tracking"""
        self.ensure_one()

        if not hasattr(self.env, 'fsm.notification.manager'):
            return

        notification_data = {
            'name': _("Reschedule Notification - %s", self.task_id.name),
            'notification_type': 'reschedule',
            'partner_id': self.partner_id.id,
            'task_id': self.task_id.id,
            'delivery_method': self.notification_method,
            'subject': _("Service Rescheduled - %s", self.task_id.name),
            'message_body': _("Your service appointment has been rescheduled to %s", self.new_date),
            'service_date': self.new_date.date(),
            'state': 'sent',
            'sent_datetime': fields.Datetime.now(),
        }

        self.env['fsm.notification.manager'].create(notification_data)

    # ============================================================================
    # AUDIT AND COMPLIANCE METHODS
    # ============================================================================
    def _create_audit_log(self, original_date):
        """Create comprehensive audit log for the reschedule"""
        self.ensure_one()

        reason_label = dict(self._fields['reason'].selection)[self.reason]
        audit_data = {
            'name': _("FSM Task Reschedule - %s", self.task_id.name),
            'model_name': 'fsm.task',
            'record_id': self.task_id.id,
            'action_type': 'reschedule',
            'user_id': self.env.user.id,
            'partner_id': self.partner_id.id,
            'description': _("Task rescheduled from %s to %s", original_date, self.new_date),
            'old_value': str(original_date) if original_date else '',
            'new_value': str(self.new_date),
            'reason': _("%s: %s", reason_label, self.reason_details),
            'compliance_notes': self.compliance_notes,
        }

        # Create audit log if the model exists
        if hasattr(self.env, 'naid.audit.log'):
            self.env['naid.audit.log'].create(audit_data)

    def _create_approval_activity(self):
        """Create activity for manager approval"""
        self.ensure_one()

        managers = self.env['res.users'].search([
            ('groups_id', 'in', self.env.ref('records_management.group_records_manager').id)
        ])

        if managers:
            reason_label = dict(self._fields['reason'].selection)[self.reason]
            note_content = _("""Reschedule request requires approval:
From: %(current_date)s
To: %(new_date)s
Reason: %(reason)s
Details: %(details)s""", {
                'current_date': self.current_date,
                'new_date': self.new_date,
                'reason': reason_label,
                'details': self.reason_details
            })

            self.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_("Approve FSM Reschedule: %s", self.task_id.name),
                note=note_content,
                user_id=managers[0].id
            )

    def action_return_wizard(self):
        """Return action to keep wizard open"""

        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('new_date')
    def _check_new_date_future(self):
        """Validate new date is in the future"""
        for record in self:
            if record.new_date and record.new_date < fields.Datetime.now():
                raise ValidationError(_("The new planned date cannot be in the past."))

    @api.constrains('new_date', 'task_id')
    def _check_new_date_different(self):
        """Validate new date is different from current"""
        for record in self:
            if (record.task_id and record.new_date and
                record.task_id.planned_date_begin and
                record.new_date == record.task_id.planned_date_begin):
                raise ValidationError(_("The new date must be different from the current planned date."))

    @api.constrains('duration_hours')
    def _check_duration_positive(self):
        """Validate duration is positive"""
        for record in self:
            if record.duration_hours and record.duration_hours <= 0:
                raise ValidationError(_("Duration must be greater than zero."))

    @api.constrains('reschedule_count')
    def _check_reschedule_limit(self):
        """Check if reschedule limit is exceeded"""
        for record in self:
            if record.reschedule_count > 5:  # Business rule: max 5 reschedules
                raise ValidationError(_("This task has been rescheduled too many times. Please contact your manager."))

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Enhanced create with sequence number"""
        for vals in vals_list:
            if vals.get('name', _('New Reschedule Request')) == _('New Reschedule Request'):
                vals['name'] = self.env['ir.sequence'].next_by_code('fsm.reschedule.wizard') or _('New Reschedule Request')
        return super().create(vals_list)

    def unlink(self):
        """Prevent deletion of completed reschedules for audit trail"""
        for record in self:
            if record.state == 'completed':
                raise UserError(_("Cannot delete completed reschedule records. They are required for audit trail."))
        return super().unlink()
        """_summary_
        """

    route_management_id = fields.Many2one('fsm.route.management', string='Route Management')