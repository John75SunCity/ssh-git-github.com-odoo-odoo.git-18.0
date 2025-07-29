# -*- coding: utf-8 -*-
"""
Live Error Monitoring System for Records Management
====================================================

This module provides real-time error monitoring and logging without affecting
the main module loading or performance. It sends live updates about errors,
warnings, and system status directly from Odoo.

Features:
- Non-blocking error monitoring
- Real-time log streaming
- HTTP webhook notifications
- Email alerts for critical errors
- Performance monitoring
- Module health checks
"""

import logging
import json
import threading
import time
import traceback
from datetime import datetime, timedelta
from odoo import models, fields, api, tools, http
from odoo.exceptions import UserError
import requests
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

_logger = logging.getLogger(__name__)


class RecordsManagementMonitor(models.Model):
    """
    Live monitoring system for Records Management module
    This model tracks errors, performance, and system health
    """

    _name = "records.management.monitor"
    _description = "Records Management Live Monitor"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # Core monitoring fields
    name = fields.Char("Monitor Entry", required=True, tracking=True)
    monitor_type = fields.Selection(
        [
            ("error", "Error"),
            ("warning", "Warning"),
            ("info", "Information"),
            ("performance", "Performance"),
            ("health_check", "Health Check"),
            ("user_action", "User Action"),
            ("system_status", "System Status"),
        ],
        string="Type",
        required=True,
        default="info",
        tracking=True,
    )

    severity = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
            ("emergency", "Emergency"),
        ],
        string="Severity",
        default="low",
        tracking=True,
    )

    # Error details
    error_message = fields.Text("Error Message")
    error_traceback = fields.Text("Stack Trace")
    error_context = fields.Text("Error Context (JSON)")

    # Performance tracking
    execution_time = fields.Float("Execution Time (seconds)")
    memory_usage = fields.Float("Memory Usage (MB)")
    cpu_usage = fields.Float("CPU Usage (%)")

    # User and environment info
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    session_id = fields.Char("Session ID")
    ip_address = fields.Char("IP Address")
    user_agent = fields.Char("User Agent")

    # Module specific info
    affected_model = fields.Char("Affected Model")
    affected_method = fields.Char("Affected Method")
    affected_record_id = fields.Integer("Affected Record ID")

    # Status and resolution
    status = fields.Selection(
        [
            ("new", "New"),
            ("investigating", "Investigating"),
            ("resolved", "Resolved"),
            ("ignored", "Ignored"),
        ],
        string="Status",
        default="new",
        tracking=True,
    )

    resolution_notes = fields.Text("Resolution Notes")
    resolved_by = fields.Many2one("res.users", string="Resolved By")
    resolved_date = fields.Datetime("Resolved Date")

    # Notification settings
    notification_sent = fields.Boolean("Notification Sent", default=False)
    webhook_sent = fields.Boolean("Webhook Sent", default=False)
    email_sent = fields.Boolean("Email Sent", default=False)

    # Timestamps
    first_occurrence = fields.Datetime("First Occurrence", default=fields.Datetime.now)
    last_occurrence = fields.Datetime("Last Occurrence", default=fields.Datetime.now)
    occurrence_count = fields.Integer("Occurrence Count", default=1)

    active = fields.Boolean("Active", default=True)

    @api.model
    def log_error(
        self,
        error_msg,
        traceback_str=None,
        context=None,
        severity="medium",
        model=None,
        method=None,
        record_id=None,
    ):
        """
        Log an error without affecting system performance
        This method is called asynchronously to avoid blocking operations
        """
        try:
            # Create monitor entry
            vals = {
                "name": (
                    f"Error: {error_msg[:50]}..."
                    if len(error_msg) > 50
                    else f"Error: {error_msg}"
                ),
                "monitor_type": "error",
                "severity": severity,
                "error_message": error_msg,
                "error_traceback": traceback_str,
                "error_context": json.dumps(context) if context else None,
                "affected_model": model,
                "affected_method": method,
                "affected_record_id": record_id,
                "session_id": self.env.context.get("session_id", ""),
                "ip_address": self.env.context.get("request_ip", ""),
                "user_agent": self.env.context.get("request_user_agent", ""),
            }

            # Check if this error already exists (avoid spam)
            existing = self.search(
                [
                    ("error_message", "=", error_msg),
                    ("affected_model", "=", model),
                    ("affected_method", "=", method),
                    ("create_date", ">=", fields.Datetime.now() - timedelta(minutes=5)),
                ]
            )

            if existing:
                # Update existing record
                existing[0].write(
                    {
                        "last_occurrence": fields.Datetime.now(),
                        "occurrence_count": existing[0].occurrence_count + 1,
                    }
                )
                monitor_record = existing[0]
            else:
                # Create new record
                monitor_record = self.create(vals)

            # Send notifications asynchronously
            if severity in ["high", "critical", "emergency"]:
                threading.Thread(
                    target=self._send_notifications, args=(monitor_record,)
                ).start()

            return monitor_record

        except Exception as e:
            # Fallback logging - don't let monitoring break the system
            _logger.error(f"Monitor system error: {e}")
            return False

    def _send_notifications(self, monitor_record):
        """Send notifications asynchronously"""
        try:
            # Send webhook notification
            self._send_webhook_notification(monitor_record)

            # Send email notification
            self._send_email_notification(monitor_record)

            # Update notification flags
            monitor_record.write(
                {"notification_sent": True, "webhook_sent": True, "email_sent": True}
            )

        except Exception as e:
            _logger.error(f"Notification sending failed: {e}")

    def _send_webhook_notification(self, monitor_record):
        """Send webhook notification to external monitoring service"""
        try:
            # Configure your webhook URL here
            webhook_url = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("records_management.monitoring_webhook_url", "")
            )

            if not webhook_url:
                return

            payload = {
                "timestamp": monitor_record.create_date.isoformat(),
                "severity": monitor_record.severity,
                "type": monitor_record.monitor_type,
                "message": monitor_record.error_message,
                "model": monitor_record.affected_model,
                "method": monitor_record.affected_method,
                "user": monitor_record.user_id.name,
                "company": monitor_record.company_id.name,
                "traceback": monitor_record.error_traceback,
                "context": monitor_record.error_context,
                "occurrence_count": monitor_record.occurrence_count,
            }

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Odoo-Records-Management-Monitor/1.0",
            }

            # Send with timeout to avoid blocking
            response = requests.post(
                webhook_url, json=payload, headers=headers, timeout=5
            )
            response.raise_for_status()

            _logger.info(
                f"Webhook notification sent successfully: {response.status_code}"
            )

        except Exception as e:
            _logger.error(f"Webhook notification failed: {e}")

    def _send_email_notification(self, monitor_record):
        """Send email notification for critical errors"""
        try:
            if monitor_record.severity not in ["critical", "emergency"]:
                return

            # Get notification email from settings
            notification_email = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("records_management.monitoring_email", "")
            )

            if not notification_email:
                return

            # Create email content
            subject = f"🚨 CRITICAL ERROR - Records Management - {monitor_record.severity.upper()}"

            body = f"""
            <h2>Critical Error Alert - Records Management Module</h2>
            
            <p><strong>Timestamp:</strong> {monitor_record.create_date}</p>
            <p><strong>Severity:</strong> {monitor_record.severity.upper()}</p>
            <p><strong>Type:</strong> {monitor_record.monitor_type}</p>
            <p><strong>User:</strong> {monitor_record.user_id.name}</p>
            <p><strong>Company:</strong> {monitor_record.company_id.name}</p>
            
            <h3>Error Details:</h3>
            <p><strong>Message:</strong> {monitor_record.error_message}</p>
            
            {f'<p><strong>Model:</strong> {monitor_record.affected_model}</p>' if monitor_record.affected_model else ''}
            {f'<p><strong>Method:</strong> {monitor_record.affected_method}</p>' if monitor_record.affected_method else ''}
            {f'<p><strong>Record ID:</strong> {monitor_record.affected_record_id}</p>' if monitor_record.affected_record_id else ''}
            
            <h3>Stack Trace:</h3>
            <pre>{monitor_record.error_traceback or 'No traceback available'}</pre>
            
            <h3>Context:</h3>
            <pre>{monitor_record.error_context or 'No context available'}</pre>
            
            <p><strong>Occurrence Count:</strong> {monitor_record.occurrence_count}</p>
            <p><strong>First Occurrence:</strong> {monitor_record.first_occurrence}</p>
            <p><strong>Last Occurrence:</strong> {monitor_record.last_occurrence}</p>
            
            <hr>
            <p><em>This is an automated alert from the Records Management monitoring system.</em></p>
            """

            # Send via Odoo's mail system
            mail_values = {
                "subject": subject,
                "body_html": body,
                "email_to": notification_email,
                "email_from": self.env.user.email or "noreply@odoo.com",
                "auto_delete": True,
            }

            mail = self.env["mail.mail"].create(mail_values)
            mail.send()

            _logger.info(f"Email notification sent to {notification_email}")

        except Exception as e:
            _logger.error(f"Email notification failed: {e}")

    @api.model
    def log_performance(
        self, operation, execution_time, memory_usage=None, cpu_usage=None, context=None
    ):
        """Log performance metrics"""
        try:
            vals = {
                "name": f"Performance: {operation}",
                "monitor_type": "performance",
                "severity": "low",
                "execution_time": execution_time,
                "memory_usage": memory_usage,
                "cpu_usage": cpu_usage,
                "error_context": json.dumps(context) if context else None,
            }

            # Only create if execution time is significantly high
            if execution_time > 2.0:  # 2 seconds threshold
                vals["severity"] = "medium" if execution_time > 5.0 else "low"
                return self.create(vals)

        except Exception as e:
            _logger.error(f"Performance logging error: {e}")
            return False

    @api.model
    def health_check(self):
        """Perform system health check"""
        try:
            health_data = {
                "timestamp": datetime.now().isoformat(),
                "status": "healthy",
                "checks": [],
            }

            # Check database connectivity
            try:
                self.env.cr.execute("SELECT 1")
                health_data["checks"].append({"name": "database", "status": "ok"})
            except Exception as e:
                health_data["checks"].append(
                    {"name": "database", "status": "error", "message": str(e)}
                )
                health_data["status"] = "unhealthy"

            # Check critical models
            critical_models = [
                "records.container",
                "records.document",
                "shredding.service",
                "pickup.request",
                "customer.inventory",
            ]

            for model_name in critical_models:
                try:
                    self.env[model_name].search([], limit=1)
                    health_data["checks"].append(
                        {"name": f"model_{model_name}", "status": "ok"}
                    )
                except Exception as e:
                    health_data["checks"].append(
                        {
                            "name": f"model_{model_name}",
                            "status": "error",
                            "message": str(e),
                        }
                    )
                    health_data["status"] = "unhealthy"

            # Log health check result
            severity = "low" if health_data["status"] == "healthy" else "high"

            self.create(
                {
                    "name": f"Health Check - {health_data['status'].title()}",
                    "monitor_type": "health_check",
                    "severity": severity,
                    "error_context": json.dumps(health_data),
                }
            )

            return health_data

        except Exception as e:
            _logger.error(f"Health check error: {e}")
            return {"status": "error", "message": str(e)}

    @api.model
    def cleanup_old_logs(self, days=30):
        """Clean up old monitoring logs to prevent database bloat"""
        try:
            cutoff_date = fields.Datetime.now() - timedelta(days=days)
            old_logs = self.search(
                [
                    ("create_date", "<", cutoff_date),
                    (
                        "severity",
                        "in",
                        ["low", "medium"],
                    ),  # Keep high/critical logs longer
                    ("status", "=", "resolved"),
                ]
            )

            deleted_count = len(old_logs)
            old_logs.unlink()

            _logger.info(f"Cleaned up {deleted_count} old monitoring logs")
            return deleted_count

        except Exception as e:
            _logger.error(f"Log cleanup error: {e}")
            return 0

    def action_resolve(self):
        """Mark error as resolved"""
        self.write(
            {
                "status": "resolved",
                "resolved_by": self.env.user.id,
                "resolved_date": fields.Datetime.now(),
            }
        )

    def action_ignore(self):
        """Mark error as ignored"""
        self.write({"status": "ignored"})

    def action_investigate(self):
        """Mark error as under investigation"""
        self.write({"status": "investigating"})


class RecordsManagementMonitoringHelper:
    """
    Helper class for easy monitoring integration
    Use this in your models to add monitoring without affecting performance
    """

    @staticmethod
    def monitor_method(func):
        """
        Decorator to automatically monitor method execution
        Usage: @RecordsManagementMonitoringHelper.monitor_method
        """

        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            method_name = f"{self._name}.{func.__name__}"

            try:
                result = func(self, *args, **kwargs)
                execution_time = time.time() - start_time

                # Log performance if needed
                if execution_time > 1.0:  # Only log slow operations
                    self.env["records.management.monitor"].log_performance(
                        operation=method_name,
                        execution_time=execution_time,
                        context={"args": len(args), "kwargs": list(kwargs.keys())},
                    )

                return result

            except Exception as e:
                execution_time = time.time() - start_time

                # Log error
                self.env["records.management.monitor"].log_error(
                    error_msg=str(e),
                    traceback_str=traceback.format_exc(),
                    severity="high",
                    model=self._name,
                    method=func.__name__,
                    context={
                        "execution_time": execution_time,
                        "args_count": len(args),
                        "kwargs": list(kwargs.keys()),
                    },
                )

                # Re-raise the error
                raise

        return wrapper

    @staticmethod
    def log_user_action(env, action, context=None):
        """Log important user actions"""
        try:
            env["records.management.monitor"].create(
                {
                    "name": f"User Action: {action}",
                    "monitor_type": "user_action",
                    "severity": "low",
                    "error_context": json.dumps(context) if context else None,
                }
            )
        except Exception as e:
            _logger.error(f"User action logging failed: {e}")
