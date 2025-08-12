# -*- coding: utf-8 -*-
"""
FSM Notification Manager

This module provides comprehensive FSM notification functionality for managing
field service communications including day-of-service notifications, driver
proximity alerts, task status updates, and route optimization notifications.

Key Features:
- Automated day of service notifications to customers
- Real-time driver proximity alerts based on GPS location
- Task status update notifications throughout service lifecycle  
- Route optimization notifications for efficiency improvements
- Integration with pickup requests and container management
- Multi-channel delivery (email, SMS, portal notifications)

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import logging
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FsmNotificationManager(models.Model):
    """
    FSM Notification Manager
    
    Manages all field service notifications including customer communications,
    driver alerts, task updates, and route optimization notifications.
    Provides automated and manual notification capabilities with multi-channel
    delivery support.
    """

    _name = "fsm.notification.manager"
    _description = "FSM Notification Manager"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Notification Reference", 
        required=True,
        tracking=True,
        index=True,
        help="Unique reference for this notification"
    )
    company_id = fields.Many2one(
        "res.company", 
        string="Company",
        default=lambda self: self.env.company, 
        required=True,
        help="Company context for FSM operations"
    )
    user_id = fields.Many2one(
        "res.users", 
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for managing this notification"
    )
    active = fields.Boolean(
        string="Active", 
        default=True,
        help="Whether this notification is active"
    )

    # ============================================================================
    # NOTIFICATION TYPE AND CONFIGURATION
    # ============================================================================
    notification_type = fields.Selection([
        ('day_of_service', 'Day of Service Notification'),
        ('driver_proximity', 'Driver Proximity Alert'),
        ('task_status', 'Task Status Update'),
        ('route_optimization', 'Route Optimization Alert'),
        ('pickup_reminder', 'Pickup Reminder'),
        ('service_completion', 'Service Completion'),
        ('delay_notification', 'Service Delay Notification'),
        ('reschedule_confirmation', 'Reschedule Confirmation'),
    ], string="Notification Type", required=True, tracking=True,
    help="Type of FSM notification to send")

    delivery_method = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('portal', 'Portal Notification'),
        ('all', 'All Methods'),
    ], string="Delivery Method", default='email', required=True,
    help="Method for delivering the notification")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    pickup_request_id = fields.Many2one(
        'pickup.request',
        string='Related Pickup Request',
        help="Pickup request associated with this notification"
    )
    container_ids = fields.Many2many(
        'records.container',
        string='Related Containers',
        help="Containers involved in the service notification"
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        help="Customer receiving the notification"
    )
    technician_id = fields.Many2one(
        'hr.employee',
        string='Assigned Technician',
        help="Field technician assigned to the service"
    )

    # ============================================================================
    # NOTIFICATION CONTENT AND TIMING
    # ============================================================================
    subject = fields.Char(
        string="Subject",
        required=True,
        help="Notification subject line"
    )
    message_body = fields.Html(
        string="Message Content",
        required=True,
        help="Main notification message content"
    )
    scheduled_datetime = fields.Datetime(
        string="Scheduled Send Time",
        help="When to send this notification automatically"
    )
    sent_datetime = fields.Datetime(
        string="Sent At",
        readonly=True,
        help="When the notification was actually sent"
    )

    # ============================================================================
    # SERVICE DETAILS
    # ============================================================================
    service_date = fields.Date(
        string="Service Date",
        help="Date when field service is scheduled"
    )
    service_time_window = fields.Char(
        string="Service Time Window",
        help="Estimated time window for service (e.g., '9:00 AM - 11:00 AM')"
    )
    driver_location = fields.Char(
        string="Driver Current Location",
        help="Current location of assigned driver/technician"
    )
    estimated_arrival = fields.Datetime(
        string="Estimated Arrival Time",
        help="Estimated arrival time at customer location"
    )
    proximity_radius = fields.Float(
        string="Proximity Radius (miles)",
        default=5.0,
        help="Distance threshold for proximity notifications"
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', tracking=True,
    help="Current status of the notification")

    # ============================================================================
    # ADDITIONAL TRACKING FIELDS
    # ============================================================================
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string="Priority", default='normal',
    help="Notification priority level")

    delivery_status = fields.Text(
        string="Delivery Status",
        readonly=True,
        help="Status details of notification delivery attempt"
    )
    retry_count = fields.Integer(
        string="Retry Count",
        default=0,
        help="Number of delivery retry attempts"
    )
    max_retries = fields.Integer(
        string="Max Retries",
        default=3,
        help="Maximum number of delivery retry attempts"
    )

    # ============================================================================
    # AUTOMATION AND TEMPLATE FIELDS
    # ============================================================================
    auto_send = fields.Boolean(
        string="Automatic Send",
        default=True,
        help="Whether to send this notification automatically"
    )
    template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        help="Email template to use for notification"
    )
    sms_template = fields.Text(
        string="SMS Template",
        help="SMS message template"
    )

    # Mail Thread Framework Fields (inherited)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('pickup_request_id', 'notification_type', 'service_date')
    def _compute_name(self):
        """Generate notification reference name"""
        for record in self:
            if record.pickup_request_id:
                base_name = f"FSM-{record.pickup_request_id.name}"
            else:
                base_name = f"FSM-{record.id or 'NEW'}"

            type_abbrev = {
                'day_of_service': 'DOS',
                'driver_proximity': 'PROX',
                'task_status': 'STATUS',
                'route_optimization': 'ROUTE',
                'pickup_reminder': 'REMIND',
                'service_completion': 'COMP',
                'delay_notification': 'DELAY',
                'reschedule_confirmation': 'RESCHED',
            }.get(record.notification_type, 'GEN')

            record.name = f"{base_name}-{type_abbrev}"

    @api.depends('estimated_arrival', 'proximity_radius')
    def _compute_proximity_status(self):
        """Compute if driver is within proximity radius"""
        for record in self:
            # This would integrate with GPS tracking when available
            record.is_driver_nearby = False  # Placeholder for GPS integration

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_send_notification(self):
        """Send the notification using configured delivery method"""
        self.ensure_one()

        if self.state == 'sent':
            raise UserError(_("This notification has already been sent."))

        try:
            success = False

            if self.delivery_method in ['email', 'all']:
                success = self._send_email_notification() or success

            if self.delivery_method in ['sms', 'all']:
                success = self._send_sms_notification() or success

            if self.delivery_method in ['portal', 'all']:
                success = self._send_portal_notification() or success

            if success:
                self.write({
                    'state': 'sent',
                    'sent_datetime': fields.Datetime.now(),
                    'delivery_status': _('Notification sent successfully')
                })
                self._log_notification_sent()
            else:
                self._handle_send_failure()

        except Exception as e:
            _logger.error(f"Failed to send notification {self.name}: {str(e)}")
            self._handle_send_failure(str(e))

        return True

    def action_schedule_notification(self):
        """Schedule notification for automatic sending"""
        self.ensure_one()

        if not self.scheduled_datetime:
            raise UserError(_("Please set a scheduled send time first."))

        self.write({'state': 'scheduled'})

        # Create scheduled action for automatic sending
        self._create_scheduled_action()

        self.message_post(
            body=_("Notification scheduled for %s", self.scheduled_datetime)
        )

        return True

    def action_cancel_notification(self):
        """Cancel the notification"""
        self.ensure_one()

        self.write({'state': 'cancelled'})
        self.message_post(body=_("Notification cancelled by user"))

        return True

    def action_retry_send(self):
        """Retry sending failed notification"""
        self.ensure_one()

        if self.retry_count >= self.max_retries:
            raise UserError(_("Maximum retry attempts reached."))

        self.write({
            'retry_count': self.retry_count + 1,
            'state': 'draft'
        })

        return self.action_send_notification()

    # ============================================================================
    # NOTIFICATION DELIVERY METHODS
    # ============================================================================
    def _send_email_notification(self):
        """Send email notification"""
        try:
            if self.template_id:
                self.template_id.send_mail(self.id, force_send=True)
            else:
                # Send simple email
                mail_values = {
                    'subject': self.subject,
                    'body_html': self.message_body,
                    'email_to': self.partner_id.email,
                    'auto_delete': False,
                }
                mail = self.env['mail.mail'].create(mail_values)
                mail.send()
            return True
        except Exception as e:
            _logger.error(f"Email send failed: {str(e)}")
            return False

    def _send_sms_notification(self):
        """Send SMS notification"""
        try:
            if not self.partner_id.mobile:
                _logger.warning(f"No mobile number for partner {self.partner_id.name}")
                return False

            sms_content = self.sms_template or self.subject

            # Use SMS gateway if available
            sms_composer = self.env['sms.composer'].create({
                'numbers': self.partner_id.mobile,
                'body': sms_content,
                'res_model': self._name,
                'res_id': self.id,
            })
            sms_composer.action_send_sms()
            return True
        except Exception as e:
            _logger.error(f"SMS send failed: {str(e)}")
            return False

    def _send_portal_notification(self):
        """Send portal notification"""
        try:
            # Create portal message/activity
            self.env['mail.message'].create({
                'subject': self.subject,
                'body': self.message_body,
                'model': 'res.partner',
                'res_id': self.partner_id.id,
                'message_type': 'notification',
                'partner_ids': [(6, 0, [self.partner_id.id])],
            })
            return True
        except Exception as e:
            _logger.error(f"Portal notification failed: {str(e)}")
            return False

    # ============================================================================
    # FSM INTEGRATION METHODS
    # ============================================================================
    @api.model
    def send_day_of_service_notification(self, pickup_request):
        """Send day of service notification for pickup request"""
        notification = self.create({
            'notification_type': 'day_of_service',
            'pickup_request_id': pickup_request.id,
            'partner_id': pickup_request.partner_id.id,
            'service_date': pickup_request.pickup_date,
            'subject': _('Service Scheduled for Tomorrow'),
            'message_body': self._get_day_of_service_template(pickup_request),
            'scheduled_datetime': pickup_request.pickup_date - timedelta(days=1, hours=18),  # 6 PM day before
        })

        if notification.auto_send:
            notification.action_schedule_notification()

        return notification

    @api.model
    def send_driver_nearby_notification(self, pickup_request, driver_location):
        """Send driver proximity alert"""
        notification = self.create({
            'notification_type': 'driver_proximity',
            'pickup_request_id': pickup_request.id,
            'partner_id': pickup_request.partner_id.id,
            'driver_location': driver_location,
            'subject': _('Your driver is nearby'),
            'message_body': self._get_proximity_template(pickup_request, driver_location),
            'priority': 'high',
        })

        notification.action_send_notification()
        return notification

    @api.model
    def send_task_completion_notification(self, pickup_request):
        """Send task completion notification"""
        notification = self.create({
            'notification_type': 'service_completion',
            'pickup_request_id': pickup_request.id,
            'partner_id': pickup_request.partner_id.id,
            'subject': _('Service Completed Successfully'),
            'message_body': self._get_completion_template(pickup_request),
        })

        notification.action_send_notification()
        return notification

    # ============================================================================
    # TEMPLATE METHODS
    # ============================================================================
    def _get_day_of_service_template(self, pickup_request):
        """Get day of service notification template"""
        return f"""
        <p>Dear {pickup_request.partner_id.name},</p>
        
        <p>This is a reminder that your records service is scheduled for tomorrow, 
        {pickup_request.pickup_date.strftime('%B %d, %Y')}.</p>
        
        <p><strong>Service Details:</strong></p>
        <ul>
            <li>Service Type: {pickup_request.service_type or 'Records Pickup'}</li>
            <li>Estimated Time: {pickup_request.time_window or 'Business hours'}</li>
            <li>Contact: {pickup_request.contact_person or 'Main contact'}</li>
        </ul>
        
        <p>Our technician will contact you when they are on their way.</p>
        
        <p>Thank you for choosing our records management services.</p>
        """

    def _get_proximity_template(self, pickup_request, location):
        """Get proximity notification template"""
        return f"""
        <p>Dear {pickup_request.partner_id.name},</p>
        
        <p>Your assigned technician is now nearby and will arrive shortly for your 
        scheduled service.</p>
        
        <p><strong>Current Status:</strong></p>
        <ul>
            <li>Technician Location: {location}</li>
            <li>Estimated Arrival: Within 15-20 minutes</li>
            <li>Service: {pickup_request.service_type or 'Records Service'}</li>
        </ul>
        
        <p>Please ensure someone is available to meet our technician.</p>
        """

    def _get_completion_template(self, pickup_request):
        """Get service completion template"""
        return f"""
        <p>Dear {pickup_request.partner_id.name},</p>
        
        <p>Your records service has been completed successfully.</p>
        
        <p><strong>Service Summary:</strong></p>
        <ul>
            <li>Service Date: {fields.Date.today().strftime('%B %d, %Y')}</li>
            <li>Technician: {pickup_request.assigned_technician or 'Field Team'}</li>
            <li>Items Processed: {len(pickup_request.pickup_item_ids)} items</li>
        </ul>
        
        <p>Thank you for your business. You will receive detailed documentation shortly.</p>
        """

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _handle_send_failure(self, error_msg=None):
        """Handle notification send failure"""
        self.write({
            'state': 'failed',
            'delivery_status': error_msg or _('Notification send failed'),
        })

        # Create activity for manual follow-up
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Failed Notification Needs Attention"),
            note=_(
                "Notification send failed: %s", error_msg or "Unknown error"
            ),
            user_id=self.user_id.id,
        )

    def _log_notification_sent(self):
        """Log successful notification send"""
        self.message_post(
            body=_(
                "Notification sent via %s to %s",
                self.delivery_method,
                self.partner_id.name,
            )
        )

    def _create_scheduled_action(self):
        """Create scheduled action for automatic notification"""
        # This would create ir.cron record for scheduled sending
        # Implementation depends on specific requirements
        pass

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('scheduled_datetime')
    def _check_scheduled_datetime(self):
        """Validate scheduled datetime is in future"""
        for record in self:
            if record.scheduled_datetime and record.scheduled_datetime <= fields.Datetime.now():
                raise ValidationError(_("Scheduled send time must be in the future."))

    @api.constrains('proximity_radius')
    def _check_proximity_radius(self):
        """Validate proximity radius is positive"""
        for record in self:
            if record.proximity_radius and record.proximity_radius <= 0:
                raise ValidationError(_("Proximity radius must be greater than zero."))

    # ============================================================================
    # CRON/SCHEDULED METHODS
    # ============================================================================
    @api.model
    def _process_scheduled_notifications(self):
        """Process notifications scheduled for sending (called by cron)"""
        notifications = self.search([
            ('state', '=', 'scheduled'),
            ('scheduled_datetime', '<=', fields.Datetime.now()),
        ])

        for notification in notifications:
            try:
                notification.action_send_notification()
            except Exception as e:
                _logger.error(f"Failed to send scheduled notification {notification.name}: {str(e)}")

    @api.model
    def _cleanup_old_notifications(self, days=90):
        """Clean up old sent notifications (called by cron)"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_notifications = self.search([
            ('state', '=', 'sent'),
            ('sent_datetime', '<', cutoff_date),
        ])
        old_notifications.unlink()

        return len(old_notifications)
