from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta

class FsmNotification(models.Model):
    _name = 'fsm.notification'
    _description = 'FSM Notification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Reference", required=True, index=True, copy=False, default=lambda self: _('New'))
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    # Related Document Links
    task_id = fields.Many2one('project.task', string='FSM Task', ondelete='cascade')
    pickup_request_id = fields.Many2one('pickup.request', string='Pickup Request', ondelete='cascade')
    route_id = fields.Many2one('pickup.route', string='Pickup Route', ondelete='cascade')

    partner_id = fields.Many2one('res.partner', string='Recipient', required=True)

    notification_type = fields.Selection([
        ('appointment_reminder', 'Appointment Reminder'),
        ('service_start', 'Service Started'),
        ('service_completion', 'Service Completed'),
        ('delay_alert', 'Delay Alert'),
        ('custom', 'Custom Notification')
    ], string='Type', required=True, default='custom')

    subject = fields.Char(string='Subject', required=True)
    message = fields.Html(string='Message Body')

    delivery_method = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('portal', 'Portal Notification')
    ], string='Delivery Method', required=True, default='email')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')], string='Priority', default='1')

    scheduled_datetime = fields.Datetime(string='Scheduled Time')
    sent_datetime = fields.Datetime(string='Sent Time', readonly=True)
    delivered_datetime = fields.Datetime(string='Delivered Time', readonly=True)

    attempts = fields.Integer(string='Attempts', default=0, readonly=True)
    max_attempts = fields.Integer(string='Max Attempts', default=3)
    error_message = fields.Text(string='Last Error', readonly=True)

    template_id = fields.Many2one('mail.template', string='Email Template', domain="[('model', '=', 'fsm.notification')]")
    custom_data = fields.Json(string='Custom Data')
    can_retry = fields.Boolean(string='Can Retry', compute='_compute_can_retry')

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('state', 'attempts', 'max_attempts')
    def _compute_can_retry(self):
        for record in self:
            record.can_retry = record.state == 'failed' and record.attempts < record.max_attempts

    @api.depends('name', 'partner_id.name', 'notification_type')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id and record.notification_type:
                type_label = dict(record._fields['notification_type'].selection).get(record.notification_type, record.notification_type)
                record.display_name = _("%s - %s (%s)") % (record.name, type_label, record.partner_id.name)
            else:
                record.display_name = record.name or _("New Notification")

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('scheduled_datetime', 'state')
    def _check_scheduled_datetime(self):
        for record in self:
            if record.state == 'draft' and record.scheduled_datetime and record.scheduled_datetime < fields.Datetime.now():
                raise ValidationError(_("Scheduled date/time must be in the future for new notifications."))

    @api.constrains('max_attempts', 'attempts')
    def _check_attempts(self):
        for record in self:
            if record.max_attempts < 1:
                raise ValidationError(_("Max attempts must be at least 1."))
            if record.attempts < 0:
                raise ValidationError(_("Attempts cannot be negative."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_send_now(self):
        self.ensure_one()
        # Only allow sending from draft or failed state
        if self.state not in ['draft', 'failed']:
            raise UserError(_("Cannot send notification in '%s' state.") % self.state)
        self.write({
            'state': 'scheduled',
            'scheduled_datetime': fields.Datetime.now()
        })
        # The cron job will pick it up in the next run
        return True

    def action_cancel(self):
        for record in self.filtered(lambda r: r.state in ['draft', 'scheduled']):
            record.write({'state': 'cancelled'})
        return True

    def action_retry(self):
        for record in self:
            if not record.can_retry:
                raise UserError(_("Cannot retry notification '%s'.") % record.name)
            record.write({
                'state': 'scheduled',
                'scheduled_datetime': fields.Datetime.now(),
                'error_message': False
            })
        return True

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('fsm.notification') or _('New')
        return super(FsmNotification, self).create(vals_list)

    # ============================================================================
    # CRON/AUTOMATION METHODS
    # ============================================================================
    @api.model
    def _process_scheduled_notifications(self):
        """Process scheduled notifications (intended to be called by a cron job)."""
        notifications_to_send = self.search([
            ('state', '=', 'scheduled'),
            ('scheduled_datetime', '<=', fields.Datetime.now()),
        ])

        for notification in notifications_to_send:
            try:
                notification.write({'state': 'sending'})
                # In a real scenario, you would call a manager or service to handle the actual sending
                # For example: self.env['fsm.notification.sender'].send(notification)
                # Here we simulate a successful send for demonstration.
                notification.write({
                    'state': 'sent',
                    'sent_datetime': fields.Datetime.now(),
                    'attempts': notification.attempts + 1
                })
            except Exception as e:
                notification.write({
                    'state': 'failed',
                    'error_message': str(e),
                    'attempts': notification.attempts + 1
                })
        return len(notifications_to_send)

    @api.model
    def _cleanup_old_notifications(self, days=90):
        """Cleanup old, successfully delivered notifications."""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_notifications = self.search([
            ('state', 'in', ['delivered', 'cancelled']),
            ('create_date', '<', cutoff_date)
        ])
        count = len(old_notifications)
        old_notifications.unlink()
        return count

