from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class FsmNotification(models.Model):
    _name = 'fsm.notification'
    _description = 'FSM Notification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    route_management_id = fields.Many2one()
    task_id = fields.Many2one()
    pickup_request_id = fields.Many2one()
    route_id = fields.Many2one()
    partner_id = fields.Many2one()
    notification_type = fields.Selection()
    subject = fields.Char()
    message = fields.Html()
    delivery_method = fields.Selection()
    state = fields.Selection()
    priority = fields.Selection()
    scheduled_datetime = fields.Datetime()
    sent_datetime = fields.Datetime()
    delivered_datetime = fields.Datetime()
    attempts = fields.Integer()
    max_attempts = fields.Integer()
    error_message = fields.Text()
    template_id = fields.Many2one()
    custom_data = fields.Json()
    can_retry = fields.Boolean()
    display_name = fields.Char()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    cutoff_date = fields.Datetime()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_can_retry(self):
            """Check if notification can be retried""":
            for record in self:
                record.can_retry = ()
                    record.state == 'failed' and
                    record.attempts < record.max_attempts



    def _compute_display_name(self):
            """Compute display name"""
            for record in self:
                if record.partner_id and record.notification_type:
                    type_label = dict(record._fields['notification_type'].selection).get()
                        record.notification_type, record.notification_type

                    record.display_name = _("%s - %s (%s)", record.name, type_label, record.partner_id.name)
                else:
                    record.display_name = record.name or _("New Notification")

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_send_now(self):
            """Send notification immediately"""
            self.ensure_one()

            if self.state not in ['draft', 'scheduled', 'failed']:
                raise UserError(_("Cannot send notification in %s state", self.state))

            # Update to scheduled and let the manager handle sending
            self.write({)}
                'state': 'scheduled',
                'scheduled_datetime': fields.Datetime.now()


            # Call the manager to process this notification
            manager = self.env['fsm.notification.manager']
            return manager._send_notification(self)


    def action_schedule(self, datetime_scheduled):
            """Schedule notification for later sending""":
            self.ensure_one()

            if self.state not in ['draft', 'failed']:
                raise UserError(_("Cannot schedule notification in %s state", self.state))

            self.write({)}
                'state': 'scheduled',
                'scheduled_datetime': datetime_scheduled


            return True


    def action_cancel(self):
            """Cancel notification"""
            self.ensure_one()

            if self.state in ['sent', 'delivered']:
                raise UserError(_("Cannot cancel notification that has already been sent"))

            self.state = 'cancelled'
            return True


    def action_retry(self):
            """Retry failed notification"""
            self.ensure_one()

            if not self.can_retry:
                raise UserError(_("Cannot retry this notification"))

            self.write({)}
                'state': 'scheduled',
                'scheduled_datetime': fields.Datetime.now(),
                'error_message': False


            return True

        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def mark_as_sent(self):
            """Mark notification as sent"""
            self.write({)}
                'state': 'sent',
                'sent_datetime': fields.Datetime.now(),
                'attempts': self.attempts + 1



    def mark_as_delivered(self):
            """Mark notification as delivered"""
            self.write({)}
                'state': 'delivered',
                'delivered_datetime': fields.Datetime.now()



    def mark_as_failed(self, error_message=None):
            """Mark notification as failed"""
            self.write({)}
                'state': 'failed',
                'attempts': self.attempts + 1,
                'error_message': error_message or _("Unknown error")


        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_scheduled_datetime(self):
            """Validate scheduled datetime"""
            for record in self:
                if record.scheduled_datetime and record.scheduled_datetime < fields.Datetime.now():
                    if record.state == 'draft':  # Allow past dates for already scheduled items:
                        raise ValidationError(_("Scheduled date/time must be in the future"))


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

    def create(self, vals_list):
            """Override create to set default name"""
            for vals in vals_list:
                if not vals.get('name'):
                    sequence = self.env['ir.sequence'].next_by_code('fsm.notification') or 'New'
                    vals['name'] = _("FSM-NOTIF-%s", sequence)
            return super().create(vals_list)

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def name_get(self):
            """Override name_get to show meaningful display names"""
            result = []
            for record in self:
                if record.route_id and record.route_id.name:
                    name = _("FSM Notification for Route %s", record.route_id.name):
                elif record.task_id and record.task_id.name:
                    name = _("FSM Notification for Task %s", record.task_id.name):
                elif record.pickup_request_id and record.pickup_request_id.name:
                    name = _("FSM Notification for Pickup %s", record.pickup_request_id.name):
                else:
                    name = record.name or _("FSM Notification")
                result.append((record.id, name))
            return result


    def get_notification_context(self):
            """Get context data for template rendering""":
            self.ensure_one()
            return {}
                'notification': self,
                'partner': self.partner_id,
                'task': self.task_id,
                'route': self.route_id,
                'pickup_request': self.pickup_request_id,
                'company': self.company_id,



    def get_notifications_for_processing(self):
            """Get notifications ready for processing""":
            return self.search([)]
                ('state', '=', 'scheduled'),
                ('scheduled_datetime', '<=', fields.Datetime.now()),



    def get_delivery_status_display(self):
            """Get user-friendly delivery status"""
            self.ensure_one()
            status_map = {}
                'draft': _('Not Sent'),
                'scheduled': _('Scheduled'),
                'sent': _('Sent'),
                'delivered': _('Delivered'),
                'failed': _('Failed'),
                'cancelled': _('Cancelled'),

            return status_map.get(self.state, self.state)

        # ============================================================================
            # CRON/AUTOMATION METHODS
        # ============================================================================

    def process_scheduled_notifications(self):
            """Process scheduled notifications (called by cron)"""
            notifications = self.get_notifications_for_processing()
            processed_count = 0
            failed_count = 0

            for notification in notifications:
                try:
                    manager = self.env['fsm.notification.manager']
                    result = manager._send_notification(notification)
                    if result:
                        processed_count += 1
                    else:
                        failed_count += 1
                except Exception as e
                    notification.mark_as_failed(str(e))
                    failed_count += 1

            return {}
                'processed': processed_count,
                'failed': failed_count,
                'total': len(notifications)



    def cleanup_old_notifications(self, days=30):
            """Cleanup old sent notifications"""

    def create_activity_reminder(self, summary=None, note=None, days_ahead=1):
            """Create follow-up activity for failed notifications""":
            self.ensure_one()

            if not summary:
                summary = _("Follow up on failed notification: %s", self.name)

            if not note:
                note = _("Notification failed with error: %s", self.error_message or _("Unknown error"))

            self.activity_schedule()
                'mail.mail_activity_data_todo',
                summary=summary,
                note=note,
                date_deadline=fields.Date.today() + fields.timedelta(days=days_ahead),
                user_id=self.env.user.id


            return True

