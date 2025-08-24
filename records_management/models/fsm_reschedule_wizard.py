from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class FsmRescheduleWizard(models.TransientModel):
    _name = 'fsm.reschedule.wizard'
    _description = 'FSM Task Reschedule Wizard'

    # ============================================================================
    # WIZARD FIELDS
    # ============================================================================
    task_id = fields.Many2one('fsm.task', string='FSM Task', required=True, readonly=True)
    
    current_scheduled_date_start = fields.Datetime(string="Current Start Time", related='task_id.scheduled_date_start', readonly=True)
    
    new_scheduled_date_start = fields.Datetime(string="New Scheduled Start Time", required=True)
    new_scheduled_date_end = fields.Datetime(string="New Scheduled End Time", required=True)
    
    reschedule_reason = fields.Selection([
        ('customer_request', 'Customer Request'),
        ('technician_unavailable', 'Technician Unavailable'),
        ('equipment_issue', 'Equipment Issue'),
        ('logistical_delay', 'Logistical Delay'),
        ('other', 'Other')
    ], string="Reason for Reschedule", required=True)
    
    reason_details = fields.Text(string="Reason Details")
    
    notify_customer = fields.Boolean(string="Notify Customer", default=True)
    customer_notification_message = fields.Text(string="Message to Customer", help="This message will be sent to the customer if 'Notify Customer' is checked.")
    
    internal_notes = fields.Text(string="Internal Notes", help="Internal notes for logging and auditing purposes.")

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('new_scheduled_date_start', 'new_scheduled_date_end')
    def _check_dates(self):
        for wizard in self:
            if wizard.new_scheduled_date_start and wizard.new_scheduled_date_end:
                if wizard.new_scheduled_date_end < wizard.new_scheduled_date_start:
                    raise ValidationError(_("The new end date cannot be before the new start date."))
            if wizard.new_scheduled_date_start < fields.Datetime.now():
                raise ValidationError(_("The new scheduled start date cannot be in the past."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_reschedule_task(self):
        """
        Main action to apply the reschedule to the FSM task.
        """
        self.ensure_one()
        
        original_date_str = self.task_id.scheduled_date_start.strftime('%Y-%m-%d %H:%M') if self.task_id.scheduled_date_start else _('N/A')
        new_date_str = self.new_scheduled_date_start.strftime('%Y-%m-%d %H:%M')
        
        # Update the FSM task
        self.task_id.write({
            'scheduled_date_start': self.new_scheduled_date_start,
            'scheduled_date_end': self.new_scheduled_date_end,
        })
        
        # Post a message on the task's chatter
        reason_label = dict(self._fields['reschedule_reason'].selection).get(self.reschedule_reason)
        body = _(
            "Task has been rescheduled from <strong>%s</strong> to <strong>%s</strong>.<br/>"
            "<strong>Reason:</strong> %s<br/>"
            "<strong>Details:</strong> %s",
            original_date_str, new_date_str, reason_label, self.reason_details or _('No details provided.')
        )
        if self.internal_notes:
            body += _("<br/><strong>Internal Notes:</strong> %s", self.internal_notes)
        
        self.task_id.message_post(body=body)
        
        # Create a notification for the customer if requested
        if self.notify_customer:
            self._create_customer_notification()
            
        return {'type': 'ir.actions.act_window_close'}

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _create_customer_notification(self):
        """
        Creates a notification record for the customer.
        This leverages the fsm.notification.manager for centralized handling.
        """
        self.ensure_one()
        notification_manager = self.env['fsm.notification.manager']
        
        subject = _("Your Service Task '%s' has been Rescheduled", self.task_id.name)
        message = self.customer_notification_message or _(
            "<p>Dear %s,</p>"
            "<p>Please be advised that your service task <strong>%s</strong> has been rescheduled.</p>"
            "<p>Your new appointment is scheduled for: <strong>%s</strong>.</p>"
            "<p>We apologize for any inconvenience this may cause.</p>",
            self.task_id.partner_id.name,
            self.task_id.name,
            self.new_scheduled_date_start.strftime('%A, %B %d, %Y at %I:%M %p')
        )
        
        custom_vals = {
            'subject': subject,
            'message': message,
        }
        
        notification_manager.create_and_send_notification(
            related_record=self.task_id,
            notification_type='custom', # Or a new 'reschedule_alert' type
            partner_id=self.task_id.partner_id,
            **custom_vals
        )
