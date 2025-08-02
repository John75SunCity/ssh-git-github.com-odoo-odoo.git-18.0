# -*- coding: utf-8 -*-
# FSM Task Extensions - Field Service Management Integration

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class FsmTask(models.Model):
    _name = "fsm.task"
    _description = "FSM Task - Field Service Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Task Name", required=True, tracking=True)
    description = fields.Text(string="Description")

    # Task Status
    task_status = fields.Selection(
        [
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Task Status",
        default="scheduled",
        tracking=True,
    )

    # Customer Information
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)
    customer_balance = fields.Monetary(
        string="Customer Balance",
        compute="_compute_customer_balance",
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Timing and Scheduling
    date_start = fields.Datetime(string="Start Date")
    date_end = fields.Datetime(string="End Date")
    reschedule_reason = fields.Text(string="Reschedule Reason")

    # Company and Currency
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    company_currency_id = fields.Many2one(
        related="company_id.currency_id", string="Company Currency"
    )

    # Invoice and Payment Status
    invoice_payment_status = fields.Selection(
        [("unpaid", "Unpaid"), ("partial", "Partially Paid"), ("paid", "Fully Paid")],
        string="Payment Status",
        default="unpaid",
    )

    # Control Fields
    active = fields.Boolean(string="Active", default=True)
    user_id = fields.Many2one(
        "res.users", string="Assigned Technician", default=lambda self: self.env.user
    )

    @api.depends("partner_id")
    def _compute_customer_balance(self):
        """Compute customer balance from partner."""
        for record in self:
            if record.partner_id:
                record.customer_balance = (
                    record.partner_id.credit - record.partner_id.debit
                )
            else:
                record.customer_balance = 0.0

    # =============================================================================
    # FSM TASK ACTION METHODS
    # =============================================================================

    def action_complete_task(self):
        """Mark task as complete."""
        self.ensure_one()
        if self.task_status != "in_progress":
            raise UserError(_("Only tasks in progress can be completed."))
        self.write({"task_status": "completed", "date_end": fields.Datetime.now()})
        self.message_post(body=_("Task completed successfully."))
        return True

    def action_contact_customer(self):
        """Contact customer about this task."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Contact Customer"),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model": "fsm.task",
                "default_res_id": self.id,
                "default_partner_ids": (
                    [(6, 0, [self.partner_id.id])] if self.partner_id else []
                ),
                "default_use_template": False,
                "default_composition_mode": "comment",
            },
        }

    def action_mobile_app(self):
        """Open mobile app for this task."""
        self.ensure_one()
        # Return action to open mobile app or redirect
        return {
            "type": "ir.actions.act_url",
            "url": f"/web#id={self.id}&model=fsm.task&view_type=form",
            "target": "new",
        }

    def action_pause_task(self):
        """Pause the current task."""
        self.ensure_one()
        if self.task_status != "in_progress":
            raise UserError(_("Only tasks in progress can be paused."))
        self.write({"task_status": "scheduled"})
        self.message_post(body=_("Task paused."))
        return True

    def action_reschedule(self):
        """Reschedule the task."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Reschedule Task"),
            "res_model": "fsm.reschedule.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_task_id": self.id,
                "default_current_date": self.date_start,
            },
        }

    def action_reschedule_remaining_tasks(self):
        """Reschedule all remaining tasks for this customer."""
        self.ensure_one()
        domain = [
            ("partner_id", "=", self.partner_id.id),
            ("task_status", "in", ["scheduled", "in_progress"]),
            ("id", "!=", self.id),
        ]
        remaining_tasks = self.search(domain)

        return {
            "type": "ir.actions.act_window",
            "name": _("Reschedule Remaining Tasks"),
            "res_model": "fsm.reschedule.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_task_ids": [(6, 0, remaining_tasks.ids)],
                "default_bulk_reschedule": True,
            },
        }

    def action_reschedule_wizard(self):
        """Open reschedule wizard."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Reschedule Wizard"),
            "res_model": "fsm.reschedule.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_task_id": self.id,
            },
        }

    def action_start_task(self):
        """Start the task."""
        self.ensure_one()
        if self.task_status != "scheduled":
            raise UserError(_("Only scheduled tasks can be started."))
        self.write({"task_status": "in_progress", "date_start": fields.Datetime.now()})
        self.message_post(body=_("Task started."))
        return True

    def action_view_location(self):
        """View task location details."""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("No customer assigned to view location."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Customer Location"),
            "res_model": "res.partner",
            "res_id": self.partner_id.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_view_materials(self):
        """View materials used for this task."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Task Materials"),
            "res_model": "stock.move",
            "view_mode": "tree,form",
            "domain": [("reference", "ilike", self.name)],
            "context": {
                "search_default_reference": self.name,
            },
        }

    def action_view_time_logs(self):
        """View time logs for this task."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Task Time Logs"),
            "res_model": "account.analytic.line",
            "view_mode": "tree,form",
            "domain": [("task_id", "=", self.id)],
            "context": {
                "default_task_id": self.id,
                "search_default_task_id": self.id,
            },
        }
