# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FsmTask(models.Model):
    _inherit = "fsm.task"

    # === Billing and Payment Fields ===
    customer_balance = fields.Monetary(
        compute="_compute_customer_balance",
        string="Customer Balance",
        currency_field="company_currency_id",
        help="Shows the customer's current account balance.",
    )
    invoice_payment_status = fields.Selection(
        related="sale_order_id.invoice_ids.payment_state",
        string="Payment Status",
        store=True,
        readonly=True,
        help="The payment status of the invoice associated with this task.",
    )
    company_currency_id = fields.Many2one(
        related="company_id.currency_id", string="Company Currency", readonly=True
    )

    # === Rescheduling Fields ===
    reschedule_reason = fields.Text(
        string="Reschedule Reason", help="Reason for rescheduling this task."
    )

    @api.depends("partner_id")
    def _compute_customer_balance(self):
        for task in self:
            if task.partner_id:
                # This computes the balance from the partner's journal items.
                # It's a standard way to get the due balance in Odoo.
                balance = 0.0
                domain = [
                    ("partner_id", "=", task.partner_id.id),
                    (
                        "account_id.account_type",
                        "in",
                        ["asset_receivable", "liability_payable"],
                    ),
                ]
                account_move_lines = self.env["account.move.line"].search(domain)
                for line in account_move_lines:
                    balance += line.debit - line.credit
                task.customer_balance = balance
            else:
                task.customer_balance = 0.0

    # === Action Methods for Buttons ===
    def action_reschedule_wizard(self):
        """Opens a wizard to reschedule the task."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Reschedule Task"),
            "res_model": "fsm.reschedule.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_task_id": self.id,
            },
        }

    def action_reschedule_remaining_tasks(self):
        """Reschedules all remaining tasks for the current driver for the next business day."""
        self.ensure_one()
        # This action will be handled by the fsm.route.management model
        self.env["fsm.route.management"].reschedule_remaining_for_driver(
            self.employee_id
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Tasks Rescheduled"),
                "message": _(
                    "All remaining tasks have been moved to the next business day."
                ),
                "type": "success",
            },
        }
