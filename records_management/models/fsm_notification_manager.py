# -*- coding: utf-8 -*-

FSM Notification Manager

This module provides comprehensive FSM notification functionality for managing:
    pass
field service communications including day-of-service notifications, driver
proximity alerts, task status updates, and route optimization notifications.

Key Features
- Automated day of service notifications to customers
- Real-time driver proximity alerts based on GPS location
- Task status update notifications throughout service lifecycle
- Route optimization notifications for efficiency improvements:
- Integration with pickup requests and container management
- Multi-channel delivery (email, SMS, portal notifications)

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FsmNotificationManager(models.Model):

        FSM Notification Manager

    Manages all field service notifications including customer communications,
        driver alerts, task updates, and route optimization notifications.
    Provides automated and manual notification capabilities with multi-channel
        delivery support.


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
        help="Unique reference for this notification":
    

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        help="Company context for FSM operations":
    

    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for managing this notification":
    

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether this notification is active"
    

        # ============================================================================
    # NOTIFICATION TYPE AND CONFIGURATION
        # ============================================================================
    ,
    notification_type = fields.Selection([))
        ('day_of_service', 'Day of Service Notification'),
        ('driver_proximity', 'Driver Proximity Alert'),
        ('task_status', 'Task Status Update'),
        ('route_optimization', 'Route Optimization Alert'),
        ('pickup_reminder', 'Pickup Reminder'),
        ('service_completion', 'Service Completion'),
        ('delay_notification', 'Service Delay Notification'),
        ('reschedule_confirmation', 'Reschedule Confirmation'),
    
        help="Type of FSM notification to send"

    delivery_method = fields.Selection([))
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('portal', 'Portal Notification'),
        ('all', 'All Methods'),
    
        help="Method for delivering the notification"
    # ============================================================================
        # RELATIONSHIP FIELDS
    # ============================================================================
    pickup_request_id = fields.Many2one(
        'pickup.request',
        string='Related Pickup Request',
        help="Pickup request associated with this notification"
    

    container_ids = fields.Many2many(
        'records.container',
        string='Related Containers',
        help="Containers involved in the service notification"
    

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        help="Customer receiving the notification"
    

    technician_id = fields.Many2one(
        'hr.employee',
        string='Assigned Technician',
        help="Field technician assigned to the service"
    

        # ============================================================================
    # NOTIFICATION CONTENT AND TIMING
        # ============================================================================
    subject = fields.Char(
        string="Subject",
        required=True,
        help="Notification subject line"
    

    message_body = fields.Html(
        string="Message Content",
        required=True,
        help="Main notification message content"
    

    scheduled_datetime = fields.Datetime(
        string="Scheduled Send Time",
        help="When to send this notification automatically"
    

    sent_datetime = fields.Datetime(
        string="Sent At",
        readonly=True,
        help="When the notification was actually sent"
    

        # ============================================================================
    # SERVICE DETAILS
        # ============================================================================
    service_date = fields.Date(
        string="Service Date",
        help="Date when field service is scheduled"
    

    service_time_window = fields.Char(
        string="Service Time Window",
        ,
    help="Estimated time window for service (e.g., '9:0 AM - 11:0 AM')"
    

    driver_location = fields.Char(
        string="Driver Current Location",
        help="Current location of assigned driver/technician"
    

    estimated_arrival = fields.Datetime(
        string="Estimated Arrival Time",
        help="Estimated arrival time at customer location"
    

    proximity_radius = fields.Float(
        ,
    string="Proximity Radius (miles)",
        default=5.0,
        help="Distance threshold for proximity notifications":
    

        # ============================================================================
    # STATE MANAGEMENT
        # ============================================================================
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    
        help="Current status of the notification"

    # ============================================================================
        # ADDITIONAL TRACKING FIELDS
    # ============================================================================
    priority = fields.Selection([))
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    
        help="Notification priority level"

    delivery_status = fields.Text(
        string="Delivery Status",
        readonly=True,
        help="Status details of notification delivery attempt"
    

    retry_count = fields.Integer(
        string="Retry Count",
        default=0,
        help="Number of delivery retry attempts"
    

    max_retries = fields.Integer(
        string="Max Retries",
        default=3,
        help="Maximum number of delivery retry attempts"
    

        # ============================================================================
    # AUTOMATION AND TEMPLATE FIELDS
        # ============================================================================
    auto_send = fields.Boolean(
        string="Automatic Send",
        default=True,
        help="Whether to send this notification automatically"
    

    template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        help="Email template to use for notification":
    

    sms_template = fields.Text(
        string="SMS Template",
        help="SMS message template"
    

        # ============================================================================
    # COMPUTED FIELDS
        # ============================================================================
    is_driver_nearby = fields.Boolean(
        string="Driver Nearby",
        compute='_compute_proximity_status',
        help="Whether driver is within proximity radius"
    

        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
        # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        ,
    domain=lambda self: [("res_model", "=", self._name))
    

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        ,
    domain=lambda self: [("res_model", "=", self._name))
    

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        ,
    domain=lambda self: [("model", "=", self._name))
    

        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends('pickup_request_id', 'notification_type', 'service_date')
    def _compute_name(self):
        """Generate notification reference name"""
        for record in self:
            if record.pickup_request_id:
                base_name = _("FSM-%s", record.pickup_request_id.name)
            else:
                base_name = _("FSM-%s", record.id or 'NEW')

            type_abbrev = {}
                'day_of_service': 'DOS',
                'driver_proximity': 'PROX',
                'task_status': 'STATUS',
                'route_optimization': 'ROUTE',
                'pickup_reminder': 'REMIND',
                'service_completion': 'COMP',
                'delay_notification': 'DELAY',
                'reschedule_confirmation': 'RESCHED',
            

            record.name = _("%s-%s", base_name, type_abbrev)

    @api.depends('estimated_arrival', 'proximity_radius')
    def _compute_proximity_status(self):
        """Compute if driver is within proximity radius""":
        for record in self:
            # This would integrate with GPS tracking when available
            record.is_driver_nearby = False  # Placeholder for GPS integration:
    # ============================================================================
        # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code()
                    'fsm.notification.manager'
                ) or _('New'
        return super().create(vals_list)

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
                self.write({)}
                    'state': 'sent',
                    'sent_datetime': fields.Datetime.now(),
                    'delivery_status': _('Notification sent successfully')
                
                self._log_notification_sent()
            else:
                self._handle_send_failure()

        except Exception as e
            _logger.error("Failed to send notification %s: %s", self.name, str(e))
            self._handle_send_failure(str(e))

        return True

    def action_schedule_notification(self):
        """Schedule notification for automatic sending""":
        self.ensure_one()

        if not self.scheduled_datetime:
            raise UserError(_("Please set a scheduled send time first."))

        self.write({'state': 'scheduled'})

        # Create scheduled action for automatic sending:
        self.action_create_scheduled_action()

        self.message_post()
            body=_("Notification scheduled for %s", self.scheduled_datetime):
        

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

        self.write({)}
            'retry_count': self.retry_count + 1,
            'state': 'draft'
        

        return self.action_send_notification()

    def action_create_scheduled_action(self):
        """Create scheduled action for automatic notification""":
        self.ensure_one()

        # Create ir.cron record for scheduled sending:
        cron_vals = {}
            'name': _('FSM Notification: %s', self.name),
            'model_id': self.env.ref('base.model_fsm_notification_manager').id,
            'state': 'code',
            'code': 'model.browse([%d]).action_send_notification()' % self.id,
            'interval_number': 1,
            'interval_type': 'minutes',
            'nextcall': self.scheduled_datetime,
            'doall': False,
            'active': True,
        

        cron_job = self.env['ir.cron'].create(cron_vals)
        return cron_job

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
                mail_values = {}
                    'subject': self.subject,
                    'body_html': self.message_body,
                    'email_to': self.partner_id.email,
                    'auto_delete': False,
                
                mail = self.env['mail.mail'].create(mail_values)
                mail.send()
            return True
        except Exception as e
            _logger.error("Email send failed: %s", str(e))
            return False

    def _send_sms_notification(self):
        """Send SMS notification"""
        try:
            if not self.partner_id.mobile:
                _logger.warning("No mobile number for partner %s", self.partner_id.name):
                return False

            sms_content = self.sms_template or self.subject

            # Use SMS gateway if available:
            sms_composer = self.env['sms.composer'].create({)}
                'numbers': self.partner_id.mobile,
                'body': sms_content,
                'res_model': self._name,
                'res_id': self.id,
            
            sms_composer.action_send_sms()
            return True
        except Exception as e
            _logger.error("SMS send failed: %s", str(e))
            return False

    def _send_portal_notification(self):
        """Send portal notification"""
        try:
            # Create portal message/activity
            self.env['mail.message'].create({)}
                'subject': self.subject,
                'body': self.message_body,
                'model': 'res.partner',
                'res_id': self.partner_id.id,
                'message_type': 'notification',
                'partner_ids': [(6, 0, [self.partner_id.id])],
            
            return True
        except Exception as e
            _logger.error("Portal notification failed: %s", str(e))
            return False

    # ============================================================================
        # FSM INTEGRATION METHODS
    # ============================================================================
    @api.model
    def send_day_of_service_notification(self, pickup_request):
        """Send day of service notification for pickup request""":
        notification = self.create({)}
            'notification_type': 'day_of_service',
            'pickup_request_id': pickup_request.id,
            'partner_id': pickup_request.partner_id.id,
            'service_date': pickup_request.pickup_date,
            'subject': _('Service Scheduled for Tomorrow'),:
            'message_body': self._get_day_of_service_template(pickup_request),
            'scheduled_datetime': pickup_request.pickup_date - timedelta(days=1, hours=18),  # 6 PM day before
        

        if notification.auto_send:
            notification.action_schedule_notification()

        return notification

    @api.model
    def send_driver_nearby_notification(self, pickup_request, driver_location):
        """Send driver proximity alert"""
        notification = self.create({)}
            'notification_type': 'driver_proximity',
            'pickup_request_id': pickup_request.id,
            'partner_id': pickup_request.partner_id.id,
            'driver_location': driver_location,
            'subject': _('Your driver is nearby'),
            'message_body': self._get_proximity_template(pickup_request, driver_location),
            'priority': 'high',
        

        notification.action_send_notification()
        return notification

    @api.model
    def send_task_completion_notification(self, pickup_request):
        """Send task completion notification"""
        notification = self.create({)}
            'notification_type': 'service_completion',
            'pickup_request_id': pickup_request.id,
            'partner_id': pickup_request.partner_id.id,
            'subject': _('Service Completed Successfully'),
            'message_body': self._get_completion_template(pickup_request),
        

        notification.action_send_notification()
        return notification

    # ============================================================================
        # TEMPLATE METHODS
    # ============================================================================
    def _get_day_of_service_template(self, pickup_request):
        """Get day of service notification template"""
        service_date = pickup_request.pickup_date.strftime('%B %d, %Y') if pickup_request.pickup_date else _('(Date TBD)'):
        service_type = pickup_request.service_type or _('Records Pickup')
        time_window = pickup_request.time_window or _('Business hours')
        contact_person = pickup_request.contact_person or _('Main contact')

        return _(""")"
        <p>Dear %(customer)s,</p>

        <p>This is a reminder that your records service is scheduled for tomorrow,:
        %(date)s.</p>

        <p><strong>Service Details:</strong></p>
        <ul>
            <li>Service Type: %(service)s</li>
            <li>Estimated Time: %(time)s</li>
            <li>Contact: %(contact)s</li>
        </ul>

        <p>Our technician will contact you when they are on their way.</p>

        <p>Thank you for choosing our records management services.</p>:
        """, {}"
            'customer': pickup_request.partner_id.name,
            'date': service_date,
            'service': service_type,
            'time': time_window,
            'contact': contact_person,
        

    def _get_proximity_template(self, pickup_request, location):
        """Get proximity notification template"""
        service_type = pickup_request.service_type or _('Records Service')

        return _(""")"
        <p>Dear %(customer)s,</p>

        <p>Your assigned technician is now nearby and will arrive shortly for your:
        scheduled service.</p>

        <p><strong>Current Status:</strong></p>
        <ul>
            <li>Technician Location: %(location)s</li>
            <li>Estimated Arrival: Within 15-20 minutes</li>
            <li>Service: %(service)s</li>
        </ul>

        <p>Please ensure someone is available to meet our technician.</p>
        """, {}"
            'customer': pickup_request.partner_id.name,
            'location': location,
            'service': service_type,
        

    def _get_completion_template(self, pickup_request):
        """Get service completion template"""
    today = fields.Date.today().strftime('%B %d, %Y')
        technician = pickup_request.assigned_technician or _('Field Team')
        item_count = len(pickup_request.pickup_item_ids) if hasattr(pickup_request, 'pickup_item_ids') else 0:
        return _(""")"
        <p>Dear %(customer)s,</p>

        <p>Your records service has been completed successfully.</p>

        <p><strong>Service Summary:</strong></p>
        <ul>
            <li>Service Date: %(date)s</li>
            <li>Technician: %(technician)s</li>
            <li>Items Processed: %(items)d items</li>
        </ul>

        <p>Thank you for your business. You will receive detailed documentation shortly.</p>:
        """, {}"
            'customer': pickup_request.partner_id.name,
            'date': today,
            'technician': technician,
            'items': item_count,
        

    # ============================================================================
        # HELPER METHODS
    # ============================================================================
    def _handle_send_failure(self, error_msg=None):
        """Handle notification send failure"""
        self.write({)}
            'state': 'failed',
            'delivery_status': error_msg or _('Notification send failed'),
        

        # Create activity for manual follow-up:
        self.activity_schedule()
            "mail.mail_activity_data_todo",
            summary=_("Failed Notification Needs Attention"),
            note=_("Notification send failed: %s", error_msg or "Unknown error"),
            user_id=self.user_id.id,
        

    def _log_notification_sent(self):
        """Log successful notification send"""
        self.message_post()
            body=_("Notification sent via %s to %s", self.delivery_method, self.partner_id.name)
        

    # ============================================================================
        # BUSINESS METHODS
    # ============================================================================
    def get_notification_summary(self):
        """Get notification summary for reporting""":
        self.ensure_one()
        return {}
            'name': self.name,
            'type': self.notification_type,
            'status': self.state,
            'customer': self.partner_id.name,
            'delivery_method': self.delivery_method,
            'scheduled_datetime': self.scheduled_datetime,
            'sent_datetime': self.sent_datetime,
            'priority': self.priority,
        

    @api.model
    def get_notification_statistics(self):
        """Get notification statistics for dashboard""":
        stats = {}

        # Count by status
        for status in ["draft", "scheduled", "sent", "failed", "cancelled"]:
            stats[status] = self.search_count([("state", "=", status)])

        # Count by type
        stats['by_type'] = {}
        for notification_type, label in self._fields['notification_type'].selection:
            stats['by_type'][label] = self.search_count([("notification_type", "=", notification_type)])

        # Success rate
        total_sent = stats["sent"] + stats["failed"]
        if total_sent > 0:
            stats["success_rate"] = round((stats["sent"] / total_sent) * 100, 2)
        else:
            stats["success_rate"] = 0.0

        return stats

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

    @api.constrains('partner_id')
    def _check_partner_contact_info(self):
        """Validate partner has required contact information"""
        for record in self:
            if record.delivery_method == 'email' and not record.partner_id.email:
                raise ValidationError(_("Customer must have an email address for email notifications")):
            if record.delivery_method == 'sms' and not record.partner_id.mobile:
                raise ValidationError(_("Customer must have a mobile number for SMS notifications")):
    # ============================================================================
        # CRON/SCHEDULED METHODS
    # ============================================================================
    @api.model
    def _process_scheduled_notifications(self):
        """Process notifications scheduled for sending (called by cron)""":
        notifications = self.search([)]
            ('state', '=', 'scheduled'),
            ('scheduled_datetime', '<=', fields.Datetime.now()),
        

        processed_count = 0
        failed_count = 0

        for notification in notifications:
            try:
                notification.action_send_notification()
                processed_count += 1
            except Exception as e
                _logger.error("Failed to send scheduled notification %s: %s", notification.name, str(e))
                failed_count += 1

        return {}
            'processed': processed_count,
            'failed': failed_count
        

    @api.model
    def _cleanup_old_notifications(self, days=90):
        """Clean up old sent notifications (called by cron)"""
    cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_notifications = self.search([)]
            ('state', '=', 'sent'),
            ('sent_datetime', '<', cutoff_date),
        

        count = len(old_notifications)
        old_notifications.unlink()

        _logger.info("Cleaned up %d old FSM notifications", count)
        return count

    # ============================================================================
        # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom display name"""
        result = []
        for record in self:
            name_parts = [record.name]

            if record.notification_type:
                type_label = dict(record._fields['notification_type'].selection).get()
                    record.notification_type, record.notification_type
                
                name_parts.append(_("(%s)", type_label))

            if record.partner_id:
                name_parts.append(_("- %s", record.partner_id.name))

            result.append((record.id, " ".join(name_parts)))
        return result

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        """Enhanced search by name, customer, or type"""
        args = args or []
        domain = []

        if name:
            domain = []
                "|", "|", "|",
                ("name", operator, name),
                ("partner_id.name", operator, name),
                ("subject", operator, name),
                ("notification_type", operator, name),
            

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
))))))))))))))))))))