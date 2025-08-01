# -*- coding: utf-8 -*-
"""
NAID Audit Log
"""

from odoo import models, fields, api, _


class NAIDAuditLog(models.Model):
    """
    NAID Audit Log
    """

    _name = "naid.audit.log"
    _description = "NAID Audit Log"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Done")],
        string="State",
        default="draft",
        tracking=True,
    )

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)

    def action_confirm(self):
        """Confirm the record"""
        self.write({"state": "confirmed"})

    def action_done(self):
        """Mark as done"""
        self.write({"state": "done"})

    @api.model
    def cleanup_old_logs(self):
        """Scheduled method to cleanup old audit logs (older than 7 years)"""
        # NAID compliance requires keeping audit logs for 7 years
        cutoff_date = fields.Date.subtract(fields.Date.today(), years=7)

        # Find old completed logs
        old_logs = self.search([("state", "=", "done"), ("date", "<", cutoff_date)])

        if old_logs:
            # Archive instead of delete for compliance
            old_logs.write({"active": False})

            # Log the cleanup action
            self.create(
                {
                    "name": f"Audit Log Cleanup - {len(old_logs)} records archived",
                    "description": f"Archived {len(old_logs)} audit logs older than {cutoff_date}",
                    "date": fields.Date.today(),
                    "state": "done",
                }
            )

        return True
