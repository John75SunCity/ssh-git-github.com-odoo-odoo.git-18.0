# -*- coding: utf-8 -*-
"""
Processing Log Management Module
This module provides comprehensive logging and monitoring capabilities
for all Records Management System processes. It tracks processing activities, performance
metrics, error handling, and audit trails with real-time status monitoring.

Key Features:
- Comprehensive process logging with contextual information
- Performance monitoring with CPU, memory, and timing metrics
- Multi-level logging (debug, info, warning, error, critical)
- Session and request tracking for audit trails
- Integration with all core Records Management processes
- Real-time status monitoring and escalation workflows

Business Processes:
1. Process Monitoring: Real-time tracking of all system processes
2. Error Management: Comprehensive error logging with stack traces
3. Performance Analytics: CPU, memory, and timing analysis
4. Audit Trail: Complete activity logging for compliance
5. Session Management: User session and request tracking
6. Escalation Workflow: Automated escalation for critical issues

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

# Standard library imports first
import logging
import os
from datetime import datetime, timedelta

import traceback



# Third-party imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Odoo imports
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ProcessingLog(models.Model):
    _name = "processing.log"
    _description = "Processing Log"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "timestamp desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Log Entry",
    )
        required=True,
        tracking=True,
        index=True,

    help="Unique identifier for log entry",

        )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    ),
    user_id = fields.Many2one(
        "res.users",
        string="User",
    )
        default=lambda self: self.env.user,
        tracking=True,

    help="User who initiated the process",

        )
    active = fields.Boolean(
        string="Active", default=True, help="Active status of log entry"
    )

    # Partner Relationship
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
    )
        help="Associated partner for this record",
    )

    # ============================================================================
    # LOG TIMING AND CLASSIFICATION
    # ============================================================================
    timestamp = fields.Datetime(
        string="Timestamp",
    )
    default=fields.Datetime.now,
        required=True,
        index=True,

        help="When the log entry was created",

        )
    process_type = fields.Selection(
        [
            ("pickup", "Pickup Process"),
            ("shredding", "Shredding Process"),
            ("destruction", "Destruction Process"),
            ("retrieval", "Document Retrieval"),
            ("storage", "Storage Process"),
            ("transport", "Transport Process"),
            ("scanning", "Barcode Scanning"),
            ("billing", "Billing Process"),
            ("reporting", "Report Generation"),
            ("compliance", "Compliance Check"),
            ("portal", "Portal Activity"),
            ("system", "System Process"),
        ],
        string="Process Type",
        required=True,
        index=True,

    help="Type of process being logged",
)

        )
    log_level = fields.Selection(
        [
            ("debug", "Debug"),
            ("info", "Info"),
            ("warning", "Warning"),
            ("error", "Error"),
            ("critical", "Critical"),
        ],
        string="Log Level",
    )
        default="info",
        required=True,
        index=True,
        help="Severity level of log entry",
    )

    # ============================================================================
    # PROCESS REFERENCES
    # ============================================================================
    res_model = fields.Char(
        string="Related Model", index=True, help="Model name of related record"
    ),
    res_id = fields.Integer(string="Related Record ID", help="ID of related record"),
    res_name = fields.Char(
        string="Related Record Name",
    )
        compute="_compute_reference",
        store=True,

    help="Name of related record",

        )
    reference = fields.Char(
        string="Reference",
    )
        compute="_compute_reference",
        store=True,

    help="Full reference to related record",

        )

    # ============================================================================
    # LOG CONTENT
    # ============================================================================
    message = fields.Text(
        string="Log Message", required=True, help="Main log message content"
    ),
    details = fields.Text(
        string="Additional Details", help="Additional details about the process"
    ),
    error_code = fields.Char(
        string="Error Code", index=True, help="System error code if applicable"
    ),
    stack_trace = fields.Text(string="Stack Trace", help="Full stack trace for errors")

    # ============================================================================
    # PROCESSING CONTEXT
    # ============================================================================
    session_id = fields.Char(
        string="Session ID", index=True, help="User session identifier"
    ),
    request_id = fields.Char(
        string="Request ID", index=True, help="HTTP request identifier"
    ),
    ip_address = fields.Char(string="IP Address", help="Client IP address"),
    user_agent = fields.Char(string="User Agent", help="Client browser/application")

    # ============================================================================
    # PERFORMANCE METRICS
    # ============================================================================
    processing_time = fields.Float(
        string="Processing Time (ms)",
    )
        default=0.0,

        help="Time taken to complete process in milliseconds",

        )
    memory_usage = fields.Float(
        string="Memory Usage (MB)",
    )
        default=0.0,

        help="Memory usage during process in megabytes",

        )
    cpu_usage = fields.Float(
        string="CPU Usage (%)", default=0.0, help="CPU usage percentage during process"
    )

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
            ("retrying", "Retrying"),
        ],
        string="Status",
    )
        default="pending",
        tracking=True,
        help="Current status of the process",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    records_container_id = fields.Many2one(
        "records.container",
        string="Related Container",

        help="Related records container",

        )
    pickup_request_id = fields.Many2one(
        "pickup.request", string="Related Pickup", help="Related pickup request"
    ),
    shredding_service_id = fields.Many2one(
        "shredding.service",
        string="Related Shredding",
    )

        help="Related shredding service",

        )
    portal_request_id = fields.Many2one(
        "portal.request", string="Related Portal Request", help="Related portal request"
    )

    # ============================================================================
    # ESCALATION AND RESOLUTION
    # ============================================================================
    escalated = fields.Boolean(
        string="Escalated",
    )
        default=False,
        tracking=True,

    help="Whether this log has been escalated",

        )
    escalated_date = fields.Datetime(
        string="Escalated Date", help="When the log was escalated"
    ),
    resolved = fields.Boolean(
        string="Resolved",
    )
        default=False,
        tracking=True,

    help="Whether this log has been resolved",

        )
    resolved_date = fields.Datetime(
        string="Resolved Date", help="When the log was resolved"
    ),
    resolution_notes = fields.Text(
        string="Resolution Notes", help="Notes about how the issue was resolved"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
    )
        domain=[("res_model", "=", "processing.log")],
    ),
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
    )
        domain=[("res_model", "=", "processing.log")],
    ),
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
    )
        domain=[("model", "=", "processing.log")],
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    severity_score = fields.Integer(
        string="Severity Score",
    )
        compute="_compute_severity_score",
        store=True,

    help="Numeric severity score for sorting",

        )
    display_name = fields.Char(
        string="Display Name",
    )
        compute="_compute_display_name",
        store=True,

    help="Display name for log entry",

        )
    is_pickup_task = fields.Boolean(
        string="Is Pickup Task",
    )
        compute="_compute_is_pickup_task",
        store=True,

    help="Whether the related task is a pickup task",

        )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("res_model", "res_id")
    def _compute_reference(self):
        """Compute reference to related record"""
        for log in self:
            log.res_name = ""
            log.reference = ""
            if log.res_model and log.res_id:
                try:
                    if log.res_model in self.env:
                        record = self.env[log.res_model].browse(log.res_id)
                        if record.exists():
                            log.res_name = getattr(record, "display_name", None) or getattr(record, "name", "Unknown")
                            log.reference = f"{log.res_model}({log.res_id}): {log.res_name}"
                        else:
                            log.res_name = _("Deleted %s(%s)", log.res_model, log.res_id)
                            log.reference = log.res_name
                    else:
                        log.res_name = _("Unknown Model %s(%s)", log.res_model, log.res_id)
                        log.reference = log.res_name
                except Exception:
                    log.res_name = _("Error accessing %s(%s)", log.res_model, log.res_id)
                    log.reference = log.res_name

    @api.depends("log_level")
    def _compute_severity_score(self):
        """Compute numeric severity score for sorting"""
        severity_map = {
            "debug": 1,
            "info": 2,
            "warning": 3,
            "error": 4,
            "critical": 5,
        }
        for log in self:
            log.severity_score = severity_map.get(log.log_level, 2)

    @api.depends("name", "process_type", "log_level", "timestamp")
    def _compute_display_name(self):
        """Compute display name for log entry"""
        for log in self:
            if log.name and log.process_type and log.timestamp:
                timestamp_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                level_str = log.log_level.upper() if log.log_level else "INFO"
                log.display_name = _("[%s] %s (%s)", level_str, log.name, timestamp_str)
            else:
                log.display_name = log.name or "Processing Log"

    @api.depends("process_type")
    def _compute_is_pickup_task(self):
        """Determine if task is a pickup task"""
        for record in self:
            record.is_pickup_task = record.process_type == 'pickup'

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence numbers and capture metrics"""
        for vals in vals_list:
            if not vals.get("name"):
                process_type = vals.get("process_type", "system"),
    timestamp = fields.Datetime.to_string(datetime.now())
        vals["name"] = _("%s-%s", process_type, timestamp)
            # Capture performance metrics if not provided
            if "memory_usage" not in vals and PSUTIL_AVAILABLE:
                try:
                    current_process = psutil.Process(os.getpid())
                    vals["memory_usage"] = current_process.memory_info().rss / 1024 / 1024  # MB
                    vals["cpu_usage"] = current_process.cpu_percent()
                except Exception:
                    pass
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_resolved(self):
        """Mark log entry as resolved"""

        self.ensure_one()
        self.write(
            {
                "resolved": True,
                "resolved_date": fields.Datetime.now(),
                "status": "completed",
            }
        )
        self.message_post(body=_("Log entry marked as resolved"))

    def action_escalate(self):
        """Escalate log entry for review"""

        self.ensure_one()
        self.write(
            {
                "escalated": True,
                "escalated_date": fields.Datetime.now(),
                "log_level": "critical",
            }
        )

        # Create activity for manager review
        try:
            manager_group = self.env.ref("records_management.group_records_manager")
            manager_user = (
                manager_group.users[0] if manager_group.users else self.env.user
            )

            self.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=f"Review Critical Log: {self.name}",
                note=f"Log entry escalated for review:\n{self.message}",
                user_id=manager_user.id,
            )
        except Exception:
            # Fallback if group doesn't exist
            self.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=f"Review Critical Log: {self.name}",
                note=f"Log entry escalated for review:\n{self.message}",
                user_id=self.env.user.id,
            )

    self.message_post(body=_("Log entry escalated for management review"))

    def action_retry_process(self):
        """Retry failed process"""

        self.ensure_one()
        if self.status != "failed":
            raise UserError(_("Only failed processes can be retried"))
        self.write({"status": "retrying", "resolved": False})
        self.message_post(body=_("Process retry initiated"))

    def action_cancel_process(self):
        """Cancel pending or processing entry"""

        self.ensure_one()
        if self.status in ["completed", "cancelled"]:
            raise UserError(_("Cannot cancel completed or already cancelled processes"))
        self.write({"status": "cancelled"})
        self.message_post(body=_("Process cancelled"))

    def action_view_related_record(self):
        """View the related record"""

        self.ensure_one()
        if not self.res_model or not self.res_id:
            raise UserError(_("No related record to display"))
        return {
            "type": "ir.actions.act_window",
            "name": _("Related Record"),
            "res_model": self.res_model,
            "res_id": self.res_id,
            "view_mode": "form",
        }

    def action_add_resolution_notes(self):
        """Add resolution notes wizard"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Add Resolution Notes"),
            "res_model": "processing.log.resolution.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_log_id": self.id},
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model
    def create_log(self, process_type, message, log_level="info", **kwargs):
        """Utility method to create log entries"""
        vals = {
            "process_type": process_type,
            "message": message,
            "log_level": log_level,
            **kwargs,
        }
        return self.create(vals)

    @api.model
    def log_process_start(self, process_type, message, **kwargs):
        """Log process start with timing"""
        log = self.create_log(
            process_type=process_type,
            message=f"Process started: {message}",
            status="processing",
            **kwargs,
        )
        return log

    @api.model
    def log_process_end(self, log_id, success=True, message=None, **kwargs):
        """Log process completion"""
        if isinstance(log_id, int):
            log = self.browse(log_id)
        else:
            log = log_id
        if log.exists():
            vals = {"status": "completed" if success else "failed", **kwargs}
            if message:
                vals["message"] = f"{log.message} - {message}"
            log.write(vals)

    @api.model
    def log_error(self, process_type, message, error=None, **kwargs):
        """Log error with stack trace"""
        vals = {
            "process_type": process_type,
            "message": message,
            "log_level": "error",
            "status": "failed",
            **kwargs,
        }
        if error:
            vals["error_code"] = str(type(error).__name__)
            vals["stack_trace"] = traceback.format_exc()
        return self.create_log(**vals)

    @api.model
    def get_system_health(self):
        """Get system health metrics"""
        if not PSUTIL_AVAILABLE:
            return {
                "memory_usage": 0,
                "cpu_usage": 0,
                "disk_usage": 0,
                "active_processes": 0,
                "error": "psutil not available"
            }
        try:
            current_process = psutil.Process(os.getpid())
            return {
                "memory_usage": current_process.memory_info().rss / 1024 / 1024,  # MB
                "cpu_usage": current_process.cpu_percent(),
                "disk_usage": psutil.disk_usage("/").percent,
                "active_processes": len(psutil.pids()),
            }
        except Exception:
            return {
                "memory_usage": 0,
                "cpu_usage": 0,
                "disk_usage": 0,
                "active_processes": 0,
                "error": "Failed to get system metrics"
            }

    # ============================================================================
    # REPORTING METHODS
    # ============================================================================
    @api.model
    def get_error_summary(self, days=7):
        """Get error summary for last N days"""
        domain = [
            ("timestamp", ">=", fields.Datetime.now() - timedelta(days=days)),
            ("log_level", "in", ["error", "critical"]),
        ]
        logs = self.search(domain)
        summary = {}
        for log in logs:
            key = f"{log.process_type}_{log.error_code or 'unknown'}"
            if key not in summary:
                summary[key] = {
                    "count": 0,
                    "process_type": log.process_type,
                    "error_code": log.error_code,
                    "latest_message": "",
                }
            summary[key]["count"] += 1
            summary[key]["latest_message"] = log.message
        return list(summary.values())

    @api.model
    def get_performance_metrics(self, process_type=None, days=1):
        """Get performance metrics for processes"""
        domain = [
            ("timestamp", ">=", fields.Datetime.now() - timedelta(days=days)),
            ("processing_time", ">", 0),
        ]
        if process_type:
            domain.append(("process_type", "=", process_type))
        logs = self.search(domain)
        if not logs:
            return {}
        processing_times = logs.mapped("processing_time")
        memory_usage = logs.mapped("memory_usage")
        cpu_usage = logs.mapped("cpu_usage")
        return {
            "total_processes": len(logs),
            "avg_processing_time": sum(processing_times) / len(processing_times),
            "max_processing_time": max(processing_times),
            "avg_memory_usage": (
                sum(memory_usage) / len(memory_usage) if memory_usage else 0
            ),
            "avg_cpu_usage": sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("processing_time", "memory_usage", "cpu_usage")
    def _check_metrics(self):
        """Validate performance metrics"""
        for record in self:
            if record.processing_time < 0:
                raise ValidationError(_("Processing time cannot be negative"))
            if record.memory_usage < 0:
                raise ValidationError(_("Memory usage cannot be negative"))
            if record.cpu_usage < 0 or record.cpu_usage > 100:
                raise ValidationError(_("CPU usage must be between 0 and 100"))

    @api.constrains("res_model", "res_id")
    def _check_reference(self):
        """Validate record reference"""
        for record in self:
            if record.res_model and not record.res_id:
                raise ValidationError(
                    _("Record ID is required when model is specified")
                )
            if record.res_id and not record.res_model:
                raise ValidationError(
                    _("Model is required when record ID is specified")
                )

    # ============================================================================
    # CLEANUP METHODS
    # ============================================================================
    @api.model
    def cleanup_old_logs(self, days=30):
        """Cleanup old log entries"""
    cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_logs = self.search(
            [
                ("timestamp", "<", cutoff_date),
                ("log_level", "in", ["debug", "info"]),
                ("resolved", "=", True),
            ]
        )
        count = len(old_logs)
        old_logs.unlink()
        # Log the cleanup
        self.create_log(
            process_type="system",
            message=f"Cleaned up {count} old log entries older than {days} days (cutoff: {cutoff_date})",
            log_level="info",
        )
        return count

    @api.model
    def archive_critical_logs(self, days=90):
        """Archive critical logs to prevent deletion"""
    cutoff_date = fields.Datetime.now() - timedelta(days=days)
        critical_logs = self.search(
            [
                ("timestamp", "<", cutoff_date),
                ("log_level", "=", "critical"),
                ("active", "=", True),
            ]
        )
        critical_logs.write({"active": False})
        return len(critical_logs)

class ProcessingLogResolutionWizard(models.TransientModel):
    """Wizard for adding resolution notes to log entries"""

    _name = "processing.log.resolution.wizard"
    _description = "Processing Log Resolution Wizard"

    log_id = fields.Many2one("processing.log", string="Log Entry", required=True),
    resolution_notes = fields.Text(
        string="Resolution Notes",
        required=True,

        help="Describe how the issue was resolved",

        )
    mark_resolved = fields.Boolean(
        string="Mark as Resolved", default=True, help="Mark the log entry as resolved"
    )

    def action_add_notes(self):
        """Add resolution notes to log entry"""

        self.ensure_one()
        vals = {"resolution_notes": self.resolution_notes}
        if self.mark_resolved:
            vals.update(
                {
                    "resolved": True,
                    "resolved_date": fields.Datetime.now(),
                    "status": "completed",
                }
            )
        self.log_id.write(vals)
        self.log_id.message_post(
            body=_("Resolution notes added: %s", self.resolution_notes)
        )
        return {"type": "ir.actions.act_window_close"}
