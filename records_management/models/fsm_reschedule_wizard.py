# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FsmRescheduleWizard(models.TransientModel):
    _name = "fsm.reschedule.wizard"
    _description = "FSM Reschedule Wizard"

    # Basic Information
    name = fields.Char(string="Name", required=True, default="Reschedule Request")
    task_id = fields.Many2one("fsm.task", string="Task", required=True)
    new_date = fields.Datetime(string="New Date", required=True)
    reason = fields.Text(string="Reason")

    # Missing fields from view analysis
    reschedule_reason = fields.Text(
        string="Reschedule Reason"
    )  # Alternative to reason field
    schedule_date = fields.Datetime(
        string="Schedule Date"
    )  # Alternative to new_date field
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([('draft', 'Draft'), ('processing', 'Processing'), ('completed', 'Completed')], string='State', default='draft')
    notes = fields.Text(string='Notes')
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    sequence = fields.Integer(string='Sequence', default=10)
    updated_date = fields.Datetime(string='Updated Date')


    def action_confirm_reschedule(self):
        """Reschedule the FSM task."""
        self.ensure_one()
        if not self.task_id:
            raise UserError(_("No task selected for rescheduling."))

        # Update task date
        self.task_id.write(
            {
                "date_start": self.new_date,
                "notes": (self.task_id.notes or "")
                + _("\nRescheduled on %s. Reason: %s")
                % (
                    fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    self.reason or "No reason provided",
                ),
            }
        )

        # Create activity
        self.task_id.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Task rescheduled: %s") % self.task_id.name,
            note=_("Task has been rescheduled to %s")
            % self.new_date.strftime("%Y-%m-%d %H:%M:%S"),
            user_id=self.env.user.id,
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Task Rescheduled"),
                "message": _("Task has been successfully rescheduled."),
                "type": "success",
                "sticky": False,
            },
        }
