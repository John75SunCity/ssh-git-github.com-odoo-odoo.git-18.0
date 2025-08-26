from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta


class FsmNotificationManager(models.Model):
    _name = 'fsm.notification.manager'
    _description = 'FSM Notification Manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Name", default="FSM Notification Manager", readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    # ============================================================================
    # BUSINESS METHODS - Creating Notifications
    # ============================================================================
    @api.model
    def create_and_send_notification(self, related_record, notification_type, partner_id, delivery_method='email', custom_vals=None):
        """
        High-level method to create and schedule a notification.
        This is the primary entry point for other models to create notifications.
        """
        if not partner_id:
            raise UserError(_("A recipient (partner) is required to create a notification."))

        vals = {
            'partner_id': partner_id.id,
            'notification_type': notification_type,
            'delivery_method': delivery_method,
            'state': 'draft',
        }

        # Link the related document
        if related_record:
            if related_record._name == 'project.task':
                vals['task_id'] = related_record.id
            elif related_record._name == 'pickup.request':
                vals['pickup_request_id'] = related_record.id
            elif related_record._name == 'fsm.route':
                vals['route_id'] = related_record.id

        # Populate subject and message from a template or defaults
        template_vals = self._get_template_content(notification_type, related_record)
        vals.update(template_vals)

        if custom_vals:
            vals.update(custom_vals)

        notification = self.env['fsm.notification'].create(vals)
        notification.action_send_now()
        return notification

    @api.model
    def _get_template_content(self, notification_type, record):
        """Gets subject and body based on notification type and a related record."""
        # In a real implementation, this would use mail.template rendering
        # For now, we use simple f-strings for demonstration
        subject = "Notification"
        message = "<p>Dear Customer,</p><p>This is a notification from our FSM service.</p>"

        if notification_type == 'appointment_reminder' and record:
            subject = _("Appointment Reminder for %s") % record.name
            message = _("<p>This is a reminder for your upcoming service appointment for <strong>%s</strong> scheduled on %s.</p>") % (record.name, record.scheduled_date_start)
        elif notification_type == 'service_completion' and record:
            subject = _("Service Completed: %s") % record.name
            message = _("<p>Your service for <strong>%s</strong> has been successfully completed.</p>") % record.name
        elif notification_type == 'delay_alert' and record:
            subject = _("Service Delay Alert: %s") % record.name
            message = _("<p>We are experiencing a delay for your service <strong>%s</strong>. We apologize for any inconvenience.</p>") % record.name

        return {'subject': subject, 'message': message}

    # ============================================================================
    # CRON JOB METHODS - Processing Notifications
    # ============================================================================
    @api.model
    def _process_scheduled_notifications(self):
        """
        Finds and processes all notifications that are scheduled to be sent.
        This method is intended to be called by a system cron job.
        """
        notifications_to_send = self.env['fsm.notification'].search([
            ('state', '=', 'scheduled'),
            ('scheduled_datetime', '<=', fields.Datetime.now()),
            ('attempts', '<', 'max_attempts')
        ])

        processed_count = 0
        for notification in notifications_to_send:
            try:
                notification.write({'state': 'sending'})
                self._send_notification(notification)
                processed_count += 1
            except Exception as e:
                notification.write({
                    'state': 'failed',
                    'error_message': str(e),
                    'attempts': notification.attempts + 1
                })
        return processed_count

    @api.model
    def _send_notification(self, notification):
        """
        Private method to handle the actual sending logic based on delivery method.
        This would integrate with email servers, SMS gateways, etc.
        """
        # Placeholder for actual sending logic
        # For demonstration, we'll just mark it as sent.
        if notification.delivery_method == 'email':
            # In a real scenario: mail_server.send_email(...)
            pass
        elif notification.delivery_method == 'sms':
            # In a real scenario: sms_gateway.send(...)
            pass

        notification.write({
            'state': 'sent',
            'sent_datetime': fields.Datetime.now(),
            'attempts': notification.attempts + 1
        })
        notification.message_post(body=_("Notification sent via %s.") % notification.delivery_method)

    @api.model
    def _cleanup_old_notifications(self, days=90):
        """Clean up old, successfully delivered or cancelled notifications."""
        if days <= 0:
            return 0
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_notifications = self.env['fsm.notification'].search([
            ('state', 'in', ['delivered', 'cancelled', 'failed']),
            ('create_date', '<', cutoff_date),
            '|', ('state', '!=', 'failed'), ('attempts', '>=', 'max_attempts')
        ])
        count = len(old_notifications)
        if old_notifications:
            old_notifications.unlink()
        return count
