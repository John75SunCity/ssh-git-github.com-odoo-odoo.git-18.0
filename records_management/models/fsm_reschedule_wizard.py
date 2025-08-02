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
