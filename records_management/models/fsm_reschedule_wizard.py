# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    FSM Reschedule Wizard
    This wizard provides comprehensive FSM task rescheduling functionality with
integrated notifications, audit logging, and workflow management for the:
    pass
Records Management system.
    Key Features
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
    import logging
from datetime import timedelta
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    _logger = logging.getLogger(__name__)
    class FsmRescheduleWizard(models.TransientModel):

        Comprehensive FSM Task Reschedule Wizard

    Handles complete workflow for rescheduling field service tasks including""":"
        customer notifications, resource management, and compliance logging.""
""
    _name = "fsm.reschedule.wizard"
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "fsm.reschedule.wizard"
""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "fsm.reschedule.wizard"
""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "FSM Reschedule Wizard"
    _inherit = ['mail.thread', 'mail.activity.mixin']"
    _order = 'create_date desc'"
""
        # ============================================================================ """"
    # CORE IDENTIFICATION FIELDS"""""
        # ============================================================================ """"
    name = fields.Char("""""
        string="Reschedule Reference",
        required=True,""
        default="New Reschedule Request",
        tracking=True,""
        index=True,""
    ""
    company_id = fields.Many2one(""
        "res.company",
        default=lambda self: self.env.company,""
        required=True,""
        readonly=True""
    ""
    user_id = fields.Many2one(""
        "res.users",
        string="Requested By",
        default=lambda self: self.env.user,""
        tracking=True,""
        readonly=True""
    ""
    active = fields.Boolean(string="Active",,
    default=True)""
""
        # ============================================================================ """"
    # FSM TASK RELATIONSHIP"""""
        # ============================================================================ """"
    task_id = fields.Many2one("""""
        "fsm.task",
        string="FSM Task",
        required=True,""
        ,""
    default=lambda self: self.env.context.get('active_id'),"
        help="Field Service Management task to reschedule"
    ""
    partner_id = fields.Many2one(""
        "res.partner",
        string="Customer",
        related="task_id.partner_id",
        readonly=True,""
        store=True""
    ""
    project_id = fields.Many2one(""
        "project.project",
        string="Project",
        related="task_id.project_id",
        readonly=True,""
        store=True""
    ""
""
        # ============================================================================ """"
    # SCHEDULING DETAILS"""""
        # ============================================================================ """"
    current_date = fields.Datetime("""""
        string="Current Scheduled Date",
        related="task_id.planned_date_begin",
        readonly=True""
    ""
    new_date = fields.Datetime(""
        string="New Planned Date",
        required=True,""
        tracking=True,""
        help="New scheduled date and time for the task":
    ""
    new_date_end = fields.Datetime(""
        string="New End Date",
        ,""
    help="New scheduled end date and time (auto-calculated if not provided)":
    ""
    duration_hours = fields.Float(""
    string="Estimated Duration (Hours)",
        default=2.0,""
        help="Estimated duration for the rescheduled task":
    ""
""
        # ============================================================================ """"
    # RESCHEDULE REQUEST DETAILS"""""
        # ============================================================================ """"
    reason = fields.Selection([))"""""
        ('customer_request', 'Customer Request'),"
        ('weather', 'Weather Conditions'),"
        ('equipment_issue', 'Equipment Issue'),"
        ('technician_unavailable', 'Technician Unavailable'),"
        ('traffic_delay', 'Traffic/Access Issue'),"
        ('emergency', 'Emergency Priority Change'),"
        ('resource_conflict', 'Resource Conflict'),"
        ('other', 'Other')"
    ""
""
    reason_details = fields.Text(""
        string="Detailed Reason",
        required=True,""
        help="Detailed explanation for the reschedule request":
    ""
""
    ,""
    urgency = fields.Selection([))""
        ('low', 'Low'),"
        ('medium', 'Medium'),"
        ('high', 'High'),"
        ('urgent', 'Urgent')"
    ""
""
        # ============================================================================ """"
    # NOTIFICATION AND COMMUNICATION"""""
        # ============================================================================ """"
    notify_customer = fields.Boolean("""""
        string="Notify Customer",
        default=True,""
        help="Send notification to customer about reschedule"
    ""
    ,""
    notification_method = fields.Selection([))""
        ('email', 'Email'),"
        ('sms', 'SMS'),"
        ('both', 'Email + SMS'),"
        ('portal', 'Portal Notification'),"
        ('phone', 'Phone Call Required')"
    ""
""
    customer_message = fields.Text(""
        string="Customer Message",
        help="Custom message to include in customer notification"
    ""
""
    internal_notes = fields.Text(""
        string="Internal Notes",
        ,""
    help="Internal notes for team members (not sent to customer)":
    ""
""
        # ============================================================================ """"
    # APPROVAL AND WORKFLOW"""""
        # ============================================================================ """"
    requires_approval = fields.Boolean("""""
        string="Requires Manager Approval",
        compute="_compute_requires_approval",
        store=True,""
        help="Indicates if this reschedule requires manager approval":
    ""
    approved_by_id = fields.Many2one(""
        "res.users",
        string="Approved By",
        readonly=True,""
        tracking=True""
    ""
    approval_date = fields.Datetime(""
        string="Approval Date",
        readonly=True""
    ""
    approval_notes = fields.Text(""
        string="Approval Notes",
        readonly=True""
    ""
""
        # ============================================================================ """"
    # RESOURCE AND IMPACT ANALYSIS"""""
        # ============================================================================ """"
    technician_id = fields.Many2one("""""
        "res.users",
        string="Assigned Technician",
        related="task_id.user_ids",
        readonly=True""
    ""
    resource_available = fields.Boolean(""
        string="Resources Available",
        compute="_compute_resource_availability",
        help="Indicates if required resources are available for new date":
    ""
    route_impact = fields.Text(""
        string="Route Impact Analysis",
        compute="_compute_route_impact",
        help="Analysis of impact on other scheduled tasks and routes"
    
"
        # ============================================================================ """"
    # STATE MANAGEMENT"""""
        # ============================================================================ """"
    ,"""""
    state = fields.Selection([))""
        ('draft', 'Draft'),"
        ('submitted', 'Submitted'),"
        ('pending_approval', 'Pending Approval'),"
        ('approved', 'Approved'),"
        ('in_progress', 'In Progress'),"
        ('completed', 'Completed'),"
        ('cancelled', 'Cancelled'),"
        ('rejected', 'Rejected')"
    ""
""
        # ============================================================================ """"
    # COMPLIANCE AND AUDIT"""""
        # ============================================================================ """"
    reschedule_count = fields.Integer("""""
        string="Reschedule Count",
        compute="_compute_reschedule_count",
        help="Number of times this task has been rescheduled"
    ""
    compliance_notes = fields.Text(""
        string="Compliance Notes",
        help="Notes for compliance and audit purposes":
    ""
""
        # ============================================================================ """"
    # MAIL THREAD FRAMEWORK FIELDS"""""
        # ============================================================================ """"
    activity_ids = fields.One2many(""""mail.activity", "res_id",,
    string="Activities"),
    message_follower_ids = fields.One2many("mail.followers", "res_id",,
    string="Followers"),
    message_ids = fields.One2many("mail.message", "res_id",,
    string="Messages")
""
    reschedule_reason = fields.Text(string="Reschedule Reason",,
    required=True),""
    schedule_date = fields.Datetime(string="New Schedule Date",,
    required=True)""
        # ============================================================================ """"
    # COMPUTE METHODS"""""
        # ============================================================================ """"
    @api.depends('"""new_date', 'current_date', 'urgency', 'reason')"
    def _compute_requires_approval(self):""
        """Determine if reschedule requires manager approval"""
    """"
"""    def _compute_resource_availability(self):"
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        """Check if resources are available for the new date"""
"""                    ('planned_date_begin', '<= """
                    ('"""planned_date_end', '>= """
                    ('"""id', '!= """
                    ('"""stage_id.is_closed', '= """
    """    @api.depends('"""new_date', 'task_id')""
""""
        """Analyze impact on routes and other scheduled tasks"""
"""                    ('planned_date_begin', '>= """', record.new_date.replace(hour=0, minute=0, second=0)),""
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
                    ('""""
                    ('id', '!= """', record.task_id.id),"
                    ('"""stage_id.is_closed', '= """
    """"
""""""                    impact_notes.append(_("Found %d other tasks on the same day", len(same_day_tasks)))
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
                    if nearby_tasks:""
                        impact_notes.append(_("Route optimization possible with %d nearby tasks", len(nearby_tasks)))
""
            record.route_impact = "\n".join(impact_notes) if impact_notes else _("No significant route impact identified"):
    @api.depends('task_id')""
    def _compute_reschedule_count(self):""
        """Count how many times this task has been rescheduled"""
"""                    ('task_id', '= """
""""
                    ('"""state', '=', 'completed')"
                ""
                record.reschedule_count = reschedule_count""
            else:""
                record.reschedule_count = 0""
""
    # ============================================================================ """"
        # ONCHANGE METHODS""""""
    # ============================================================================ """"
    @api.onchange('"""new_date', 'duration_hours')"""
""""
        """Auto-calculate end date when start date or duration changes"""
    """"
"""    def _onchange_reason(self):"
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
""""
        """Set default messages based on reason"""
            'customer_request': _("Customer has requested to reschedule the service appointment."),
            'weather': _("Service rescheduled due to adverse weather conditions."),
            'equipment_issue': _("Equipment maintenance required - service rescheduled."),
            'technician_unavailable': _("Assigned technician unavailable - reassigning schedule."),
            'traffic_delay': _("Access or traffic issues require schedule adjustment."),
            'emergency': _("Emergency priority change requires immediate rescheduling."),
            'resource_conflict': _("Resource conflict identified - optimizing schedule."),
        ""
""
        if self.reason and self.reason in reason_messages:""
            self.customer_message = reason_messages[self.reason]""
""
    # ============================================================================ """"
        # ACTION METHODS""""""
    # ============================================================================""
    def action_submit_request(self):""
        """Submit the reschedule request"""
    """"
    """"
        """Approve the reschedule request (manager action)"""
    """"
"""            raise UserError(_("Only managers can approve reschedule requests."))"
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        """Reject the reschedule request"""
    """"
"""            raise UserError(_("Only managers can reject reschedule requests."))"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
""""
""""
            body=_("Reschedule request has been rejected by %s", self.env.user.name)
        ""
""
        return {'type': 'ir.actions.act_window_close'}""
""
    def action_execute_reschedule(self):""
        """Execute the approved reschedule"""
    """"
"""            raise UserError(_("Only approved requests can be executed."))"
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
            task_updates['reschedule_reason'] = _("%s: %s", reason_label, self.reason_details)
""
        self.task_id.write(task_updates)""
""
        # Create audit log""
        self._create_audit_log(original_date)""
""
        # Send notifications""
        if self.notify_customer:""
            self._send_customer_notification(original_date)""
""
        # Create FSM notification for tracking:""
        self._create_fsm_notification()""
""
        # Post message on task""
        reason_label = dict(self._fields['reason'].selection)[self.reason]""
        self.task_id.message_post()""
            body=_("Task rescheduled from %s to %s. Reason: %s - %s",
                original_date, self.new_date, reason_label, self.reason_details""
        ""
""
        self.write({'state': 'completed'})""
""
        return {'type': 'ir.actions.act_window_close'}""
""
    def action_cancel_request(self):""
        """Cancel the reschedule request"""
""""
""""
""""
        """Send notification to customer about the reschedule"""
""""
""""
    """        subject = _("Service Appointment Rescheduled - %s", self.task_id.name)"
""
        # Format dates properly for email:""
        original_date_str = original_date.strftime('%B %d, %Y at %I:%M %p') if original_date else _('N/A'):""
        new_date_str = self.new_date.strftime('%B %d, %Y at %I:%M %p')""
        reason_display = self.customer_message or dict(self._fields['reason'].selection)[self.reason]""
""
        body_html = _(""")"
        <p>Dear %(customer_name)s,</p>""
""
        <p>Your service appointment has been rescheduled:</p>""
""
        <ul>""
            <li><strong>Original Date:</strong> %(original_date)s</li>""
            <li><strong>New Date:</strong> %(new_date)s</li>""
            <li><strong>Service:</strong> %(service_name)s</li>""
            <li><strong>Reason:</strong> %(reason)s</li>""
        </ul>""
""
        <p>We apologize for any inconvenience this may cause. If you have any questions or concerns, please contact us immediately.</p>:""
        <p>Thank you for your understanding.</p>:""
        """, {}"
            'customer_name': self.partner_id.name,""
            'original_date': original_date_str,""
            'new_date': new_date_str,""
            'service_name': self.task_id.name,""
            'reason': reason_display""
        ""
""
        # Send email notification""
        if self.notification_method in ['email', 'both']:""
            self.task_id.message_post()""
                partner_ids=[self.partner_id.id],""
                subject=subject,""
                body=body_html,""
                message_type='email'""
            ""
""
        # Send SMS if configured:""
        if self.notification_method in ['sms', 'both'] and self.partner_id.mobile:""
            sms_body = _("Service appointment rescheduled to %s. Details: %s. Contact us with questions.",
                        self.new_date.strftime('%m/%d %I:%M %p'), self.task_id.name""
            self.partner_id._send_sms(sms_body)""
""
    def _create_fsm_notification(self):""
        """Create FSM notification record for tracking"""
    """"
"""            'name': _("Reschedule Notification - %s", self.task_id.name),"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
""""
            'delivery_method': self.notification_method,""
            'subject': _("Service Rescheduled - %s", self.task_id.name),
            'message_body': _("Your service appointment has been rescheduled to %s", self.new_date),
            'service_date': self.new_date.date(),""
            'state': 'sent',""
            'sent_datetime': fields.Datetime.now(),""
        ""
""
        self.env['fsm.notification.manager'].create(notification_data)""
""
    # ============================================================================""
        # AUDIT AND COMPLIANCE METHODS""
    # ============================================================================ """"
    def _create_audit_log(self, original_date):""""""
        """Create comprehensive audit log for the reschedule"""
""""
"""            'name': _("FSM Task Reschedule - %s", self.task_id.name),"
            'model_name': 'fsm.task',""
            'record_id': self.task_id.id,""
            'action_type': 'reschedule',""
            'user_id': self.env.user.id,""
            'partner_id': self.partner_id.id,""
            'description': _("Task rescheduled from %s to %s", original_date, self.new_date),
            'old_value': str(original_date) if original_date else '',:""
            'new_value': str(self.new_date),""
            'reason': _("%s: %s", reason_label, self.reason_details),
            'compliance_notes': self.compliance_notes,"
        ""
""
        # Create audit log if the model exists:""
        if hasattr(self.env, 'naid.audit.log'):""
            self.env['naid.audit.log'].create(audit_data)""
""
    def _create_approval_activity(self):""
        """Create activity for manager approval"""
""""
"""            note_content = _("""Reschedule request requires approval:)""
    From: %(current_date)s""
        To: %(new_date)s""
    Reason: %(reason)s""
        Details: %(details)s""", {}"
                'current_date': self.current_date,"
                'new_date': self.new_date,"
                'reason': reason_label,""
                'details': self.reason_details""
            ""
""
            self.activity_schedule()""
                'mail.mail_activity_data_todo',""
                summary=_("Approve FSM Reschedule: %s", self.task_id.name),
                note=note_content,""
                user_id=managers[0].id""
            ""
""
    def action_return_wizard(self):""
        """Return action to keep wizard open"""
""""
""""
"""    def _check_new_date_future(self):"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        """Validate new date is in the future"""
"""                raise ValidationError(_("The new planned date cannot be in the past."))"
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
""""
""""
""""
        """Validate new date is different from current"""
""""
""""
"""                raise ValidationError(_("The new date must be different from the current planned date."))"
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
    def _check_duration_positive(self):""
        """Validate duration is positive"""
"""                raise ValidationError(_("Duration must be greater than zero."))"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
""""
""""
        """Check if reschedule limit is exceeded"""
"""                raise ValidationError(_("This task has been rescheduled too many times. Please contact your manager."))"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
    def create(self, vals_list):""
        """Enhanced create with sequence number"""
""""
""""
    """"
        """Prevent deletion of completed reschedules for audit trail"""
"""                raise UserError(_("Cannot delete completed reschedule records. They are required for audit trail.")):"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""""
""""
""""
""""
        return super().unlink()""
        """_summary_"
        route_management_id = fields.Many2one('fsm.route.management',,""
    string='Route Management')""
))))))))))))))))))))""
""""
""""
""""
"""
""""