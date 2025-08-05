# -*- coding: utf-8 -*-

from odoo import models, fields, api


class IntegrationError(models.Model):
    _name = "integration.error"
    _description = "Integration Error Log"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "timestamp desc"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Error Message", required=True, tracking=True, index=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # ERROR DETAILS
    # ============================================================================
    timestamp = fields.Datetime(
        string="Timestamp", default=fields.Datetime.now, required=True, index=True
    )
    error_type = fields.Selection(
        [
            ("api", "API Error"),
            ("sync", "Sync Error"),
            ("validation", "Validation Error"),
            ("connection", "Connection Error"),
            ("timeout", "Timeout Error"),
            ("auth", "Authentication Error"),
            ("other", "Other"),
        ],
        string="Error Type",
        default="other",
        required=True,
        tracking=True,
    )
    error_code = fields.Char(string="Error Code", tracking=True)
    error_details = fields.Text(string="Error Details", tracking=True)
    stack_trace = fields.Text(string="Stack Trace")

    # ============================================================================
    # INTEGRATION CONTEXT
    # ============================================================================
    integration_system = fields.Char(string="Integration System", tracking=True)
    endpoint = fields.Char(string="API Endpoint")
    request_data = fields.Text(string="Request Data")
    response_data = fields.Text(string="Response Data")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    pos_wizard_id = fields.Many2one(
        "visitor.pos.wizard", string="POS Wizard", ondelete="cascade"
    )

    # ============================================================================
    # STATUS FIELDS
    # ============================================================================
    resolved = fields.Boolean(string="Resolved", default=False, tracking=True)
    resolution_notes = fields.Text(string="Resolution Notes")
    resolution_date = fields.Datetime(string="Resolution Date")
    priority = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Priority",
        default="medium",
        tracking=True,
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("name", "error_type", "timestamp")
    def _compute_display_name(self):
        for record in self:
            if record.name and record.error_type:
                record.display_name = (
                    f"[{record.error_type.upper()}] {record.name[:50]}"
                )
            else:
                record.display_name = record.name or "Integration Error"

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_resolved(self):
        """Mark error as resolved"""
        self.write(
            {
                "resolved": True,
                "resolution_date": fields.Datetime.now(),
            }
        )

    def action_mark_unresolved(self):
        """Mark error as unresolved"""
        self.write(
            {
                "resolved": False,
                "resolution_date": False,
            }
        )

    @api.model
    def create_error_log(self, error_message, error_type="other", **kwargs):
        """Helper method to create error logs programmatically"""
        vals = {
            "name": error_message,
            "error_type": error_type,
            "timestamp": fields.Datetime.now(),
        }
        vals.update(kwargs)
        return self.create(vals)
