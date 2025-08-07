# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProcessingLog(models.Model):
    _name = "processing.log"
    _description = "Processing Log"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "timestamp desc"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Log Entry", required=True, tracking=True, index=True),
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    ),
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # LOG DETAILS
    # ============================================================================
    timestamp = fields.Datetime(
        string="Timestamp", default=fields.Datetime.now, required=True, index=True
    ),
    process_type = fields.Selection(
        [
            ("pickup", "Pickup Process"),
            ("shredding", "Shredding Process"),
            ("destruction", "Destruction Process"),
            ("retrieval", "Document Retrieval"),
            ("storage", "Storage Process"),
            ("transport", "Transport Process"),
            ("scanning", "Barcode Scanning"),
            ("system", "System Process"),
        ]),
        string="Process Type",
        required=True,
        index=True,
    )

    log_level = fields.Selection(
        [
            ("debug", "Debug"),
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
            ("critical", "Critical"),
        ]),
        string="Log Level",
        default="info",
        required=True,
    )

    # ============================================================================
    # PROCESS REFERENCES
    # ============================================================================
    )
    res_model = fields.Char(string="Related Model"),
    res_id = fields.Integer(string="Related Record ID")
    res_name = fields.Char(string="Related Record Name")

    # ============================================================================
    # LOG CONTENT
    # ============================================================================
    message = fields.Text(string="Log Message", required=True),
    details = fields.Text(string="Additional Details")
    error_code = fields.Char(string="Error Code"),
    stack_trace = fields.Text(string="Stack Trace")

    # ============================================================================
    # PROCESSING CONTEXT
    # ============================================================================
    session_id = fields.Char(string="Session ID", index=True),
    request_id = fields.Char(string="Request ID", index=True)
    ip_address = fields.Char(string="IP Address"),
    user_agent = fields.Char(string="User Agent")

    # ============================================================================
    # PERFORMANCE METRICS
    # ============================================================================
    processing_time = fields.Float(string="Processing Time (ms)", default=0.0)
    memory_usage = fields.Float(string="Memory Usage (MB)", default=0.0)
    cpu_usage = fields.Float(string="CPU Usage (%)", default=0.0)

    # ============================================================================
    # STATUS & WORKFLOW
    # ============================================================================
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ]),
        string="Status",
        default="pending",
        tracking=True,
    )

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    )
    records_container_id = fields.Many2one(
        "records.container", string="Related Container"
    ),
    pickup_request_id = fields.Many2one("pickup.request", string="Related Pickup")
    shredding_service_id = fields.Many2one(
        "shredding.service", string="Related Shredding"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    # Note: Removed pos_wizard_id field - Model to TransientModel relationships are forbidden

    # # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)        "mail.followers", "res_id", string="Followers"
    )    @api.depends("res_model", "res_id")
    def _compute_reference(self):
        for log in self:
            if log.res_model and log.res_id:
                try:
                    record = self.env[log.res_model].browse(log.res_id)
                    if record.exists():
                        log.res_name = record.display_name or record.name
                    else:
                        log.res_name = f"Deleted {log.res_model}({log.res_id})"
                except:
                    log.res_name = f"Invalid {log.res_model}({log.res_id})"
            else:
                log.res_name = ""

    )

    reference = fields.Char(
        string="Reference", compute="_compute_reference", store=True
    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_resolved(self):
        """Mark log entry as resolved"""
        self.write({"status": "completed"})

    def action_escalate(self):
        """Escalate log entry for review"""
        self.write({"log_level": "critical"})
        # Create activity for manager review
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=f"Review Critical Log: {self.name}",
            note=f"Log entry escalated for review: {self.message}",
        )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model
    def create_log(self, process_type, message, log_level="info", **kwargs):
        """Utility method to create log entries"""
        vals = {
            "name": f"{process_type.title()} - {fields.Datetime.now()}",
            "process_type": process_type,
            "message": message,
            "log_level": log_level,
            **kwargs,
        }
        return self.create(vals)