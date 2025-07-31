# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class FsmRescheduleWizard(models.TransientModel):
    _name = "fsm.reschedule.wizard"
    _description = "FSM Reschedule Wizard"

    task_id = fields.Many2one("fsm.task", string="Task", required=True)
    reschedule_reason = fields.Text(string="Reason for Rescheduling", required=True)
    schedule_date = fields.Date(string="New Schedule Date", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super(FsmRescheduleWizard, self).default_get(fields_list)
        if self.env.context.get("active_id"):
            res["task_id"] = self.env.context.get("active_id")
        return res

    def action_confirm_reschedule(self):
        self.ensure_one()
        self.task_id.write(
            {
                "schedule_date": self.schedule_date,
                "reschedule_reason": self.reschedule_reason,
            }
        )
        return {"type": "ir.actions.act_window_close"}
