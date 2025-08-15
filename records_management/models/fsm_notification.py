# -*- coding: utf-8 -*-
"""
FSM Notification Record

Individual notification records for FSM routes and tasks.
Separated from the manager for better organization and following Odoo standards.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FsmNotification(models.Model):
    """
    FSM Notification
    
    Individual notification record for FSM routes and tasks.
    Managed by fsm.notification.manager for operations.
    """

    _name = "fsm.notification"
    _description = "FSM Notification"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Notification Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the notification"
    )

    company_id = fields.Many2one(
        "res.company", 
        string="Company", 
        default=lambda self: self.env.company,
        required=True
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    route_management_id = fields.Many2one(
        "fsm.route.management",
        string="Route Management",
        help="Related route management record"
    )

    task_id = fields.Many2one(
        "project.task",
        string="FSM Task",
        help="Related FSM task"
    )

    pickup_request_id = fields.Many2one(
        "pickup.request",
        string="Pickup Request",
        help="Related pickup request"
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Recipient",
        required=True,
        help="Recipient of the notification"
    )

    # ============================================================================
    # NOTIFICATION CONTENT FIELDS
    # ============================================================================
    notification_type = fields.Selection([
        ('day_of_service', 'Day of Service'),
        ('driver_proximity', 'Driver Proximity'),
        ('task_status', 'Task Status Update'),
        ('route_optimization', 'Route Optimization'),
        ('completion', 'Service Completion'),
        ('delay', 'Service Delay'),
        ('cancellation', 'Service Cancellation'),
    ], string='Notification Type', required=True, default='day_of_service')

    subject = fields.Char(
        string="Subject",
        required=True,
        help="Notification subject line"
    )

    message = fields.Html(
        string="Message Content",
        required=True,
        help="HTML formatted notification message"
    )

    delivery_method = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('portal', 'Portal Notification'),
        ('push', 'Push Notification'),
    ], string='Delivery Method', required=True, default='email')

    # ============================================================================
    # STATUS AND SCHEDULING FIELDS
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='1')

    scheduled_datetime = fields.Datetime(
        string="Scheduled Send Time",
        help="When the notification should be sent"
    )
    
    sent_datetime = fields.Datetime(
        string="Sent Date/Time",
        readonly=True,
        help="When the notification was actually sent"
    )

    delivered_datetime = fields.Datetime(
        string="Delivered Date/Time",
        readonly=True,
        help="When delivery was confirmed"
    )

    # ============================================================================
    # TRACKING FIELDS
    # ============================================================================
    attempts = fields.Integer(
        string="Send Attempts",
        default=0,
        readonly=True,
        help="Number of send attempts"
    )

    max_attempts = fields.Integer(
        string="Max Attempts",
        default=3,
        help="Maximum number of send attempts"
    )

    error_message = fields.Text(
        string="Error Message",
        readonly=True,
        help="Last error message if send failed"
    )

    # ============================================================================
    # TEMPLATE AND CUSTOMIZATION
    # ============================================================================
    template_id = fields.Many2one(
        "mail.template",
        string="Email Template",
        help="Email template used for this notification"
    )

    custom_data = fields.Json(
        string="Custom Data",
        help="Additional data for template rendering"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    can_retry = fields.Boolean(
        string="Can Retry",
        compute="_compute_can_retry",
        help="Whether this notification can be retried"
    )

    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('attempts', 'max_attempts', 'state')
    def _compute_can_retry(self):
        """Check if notification can be retried"""
        for record in self:
            record.can_retry = (
                record.state == 'failed' and 
                record.attempts < record.max_attempts
            )

    @api.depends('name', 'notification_type', 'partner_id')
    def _compute_display_name(self):
        """Compute display name"""
        for record in self:
            if record.partner_id and record.notification_type:
                type_label = dict(record._fields['notification_type'].selection).get(
                    record.notification_type, record.notification_type
                )
                record.display_name = f"{record.name} - {type_label} ({record.partner_id.name})"
            else:
                record.display_name = record.name or "New Notification"

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_send_now(self):
        """Send notification immediately"""
        self.ensure_one()
        if self.state not in ['draft', 'scheduled', 'failed']:
            raise UserError(_("Cannot send notification in %s state", self.state))
        
        # Update to scheduled and let the manager handle sending
        self.write({
            'state': 'scheduled',
            'scheduled_datetime': fields.Datetime.now()
        })
        
        # Call the manager to process this notification
        manager = self.env['fsm.notification.manager']
        return manager._send_notification(self)

    def action_schedule(self, datetime_scheduled):
        """Schedule notification for later sending"""
        self.ensure_one()
        if self.state not in ['draft', 'failed']:
            raise UserError(_("Cannot schedule notification in %s state", self.state))
        
        self.write({
            'state': 'scheduled',
            'scheduled_datetime': datetime_scheduled
        })

    def action_cancel(self):
        """Cancel notification"""
        for record in self:
            if record.state in ['sent', 'delivered']:
                raise UserError(_("Cannot cancel notification that has already been sent"))
            record.state = 'cancelled'

    def action_retry(self):
        """Retry failed notification"""
        self.ensure_one()
        if not self.can_retry:
            raise UserError(_("Cannot retry this notification"))
        
        self.write({
            'state': 'scheduled',
            'scheduled_datetime': fields.Datetime.now(),
            'error_message': False
        })

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.write({
            'state': 'sent',
            'sent_datetime': fields.Datetime.now(),
            'attempts': self.attempts + 1
        })

    def mark_as_delivered(self):
        """Mark notification as delivered"""
        self.write({
            'state': 'delivered',
            'delivered_datetime': fields.Datetime.now()
        })

    def mark_as_failed(self, error_message=None):
        """Mark notification as failed"""
        self.write({
            'state': 'failed',
            'attempts': self.attempts + 1,
            'error_message': error_message or "Unknown error"
        })

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('scheduled_datetime')
    def _check_scheduled_datetime(self):
        """Validate scheduled datetime"""
        for record in self:
            if record.scheduled_datetime and record.scheduled_datetime < fields.Datetime.now():
                if record.state == 'draft':  # Allow past dates for already scheduled items
                    raise ValidationError(_("Scheduled date/time must be in the future"))

    @api.constrains('attempts', 'max_attempts')
    def _check_attempts(self):
        """Validate attempt counts"""
        for record in self:
            if record.max_attempts < 1:
                raise ValidationError(_("Max attempts must be at least 1"))
            if record.attempts < 0:
                raise ValidationError(_("Attempts cannot be negative"))

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model
    def create(self, vals):
        """Override create to set default name"""
        if not vals.get('name'):
            sequence = self.env['ir.sequence'].next_by_code('fsm.notification') or 'New'
            vals['name'] = f"FSM-NOTIF-{sequence}"
        return super().create(vals)
