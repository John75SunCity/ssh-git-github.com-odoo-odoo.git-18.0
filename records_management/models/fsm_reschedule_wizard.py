# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FsmRescheduleWizard(models.TransientModel):
    _name = "fsm.reschedule.wizard"
    _description = "FSM Reschedule Wizard"

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(string="Name", required=True, default="Reschedule Request")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    task_id = fields.Many2one("fsm.task", string="Task", required=True)
    new_date = fields.Datetime(string="New Date", required=True)
    reason = fields.Text(string="Reason")
    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(string="Sequence", default=10)

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [("draft", "Draft"), ("processing", "Processing"), ("completed", "Completed")],
        string="State",
        default="draft",
    )

    # ============================================================================
    # ADDITIONAL FIELDS
    # ============================================================================
    reschedule_reason = fields.Text(string="Reschedule Reason")
    schedule_date = fields.Datetime(string="Schedule Date")
    notes = fields.Text(string="Notes")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)

    # Mail framework fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_reschedule(self):
        """Execute the reschedule operation"""
        self.ensure_one()
        if not self.task_id:
            raise UserError(_("Task is required for rescheduling."))

        self.task_id.write(
            {
                "planned_date_begin": self.new_date,
                "reschedule_reason": self.reason,
            }
        )

        self.write({"state": "completed"})

        return {"type": "ir.actions.act_window_close"}

    def action_cancel(self):
        """Cancel the reschedule operation"""
        return {"type": "ir.actions.act_window_close"}

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("new_date")
    def _check_new_date(self):
        for record in self:
            if record.new_date and record.new_date < fields.Datetime.now():
                raise ValidationError(_("New date cannot be in the past."))
