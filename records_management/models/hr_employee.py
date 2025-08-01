# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Hr Employee"
    _order = "name"
    _rec_name = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Assigned User", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)

    # State management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Records Status",
        default="draft",
        tracking=True,
    )

    # Documentation
    notes = fields.Text(string="Notes")

    # Computed fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )

    @api.depends("name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name or "New"

    # Action methods
    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        self.write({"state": "draft"})

    @api.model
    def check_expiring_credentials(self):
        """Scheduled method to check expiring employee credentials"""
        # Check for employees with credentials expiring soon
        from datetime import timedelta

        warning_days = 30  # Alert 30 days before expiration
        cutoff_date = fields.Date.add(fields.Date.today(), days=warning_days)

        # For now, just create activity for HR manager to check credentials
        # In a full implementation, this would check actual credential fields
        employees = self.search([("active", "=", True)])

        hr_manager = self.env.ref("hr.group_hr_manager", raise_if_not_found=False)
        if hr_manager and hr_manager.users:
            for employee in employees:
                # Check if employee needs credential review (simplified logic)
                if not employee.user_id:
                    continue

                # Create activity for periodic credential review
                employee.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary=f"Credential Review: {employee.name}",
                    note=f"Please review and update credentials for {employee.name}",
                    user_id=hr_manager.users[0].id,
                )

        return True
