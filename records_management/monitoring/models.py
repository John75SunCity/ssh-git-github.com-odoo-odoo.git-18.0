from odoo import models, fields, api
from datetime import datetime, timedelta


class RecordsManagementMonitor(models.Model):
    """
    Model for monitoring and logging system events, errors, and performance metrics
    """

    _name = "records.management.monitor"
    _description = "Records Management Monitoring System"
    _order = "create_date desc"
    _rec_name = "name"

    name = fields.Char(
        string="Event Name",
        required=True,
        help="Brief description of the monitored event",
    )

    monitor_type = fields.Selection(
        [
            ("error", "Error"),
            ("warning", "Warning"),
            ("info", "Information"),
            ("performance", "Performance"),
            ("security", "Security"),
            ("audit", "Audit"),
            ("health_check", "Health Check"),
        ],
        string="Monitor Type",
        required=True,
        default="info",
    )

    severity = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Severity",
        required=True,
        default="medium",
    )

    status = fields.Selection(
        [
            ("new", "New"),
            ("investigating", "Investigating"),
            ("resolved", "Resolved"),
            ("ignored", "Ignored"),
        ],
        string="Status",
        default="new",
        required=True,
    )

    description = fields.Text(
        string="Description", help="Detailed description of the event or issue"
    )

    technical_details = fields.Text(
        string="Technical Details", help="Technical information, stack traces, etc."
    )

    affected_model = fields.Char(
        string="Affected Model", help="The Odoo model involved in this event"
    )

    affected_method = fields.Char(
        string="Affected Method", help="The method or function involved"
    )

    affected_record_id = fields.Integer(
        string="Affected Record ID", help="The specific record ID if applicable"
    )

    user_id = fields.Many2one(
        "res.users",
        string="User",
        help="User who triggered the event",
        default=lambda self: self.env.user,
    )

    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    occurrence_count = fields.Integer(
        string="Occurrence Count", default=1, help="Number of times this event occurred"
    )

    first_occurrence = fields.Datetime(
        string="First Occurrence",
        default=fields.Datetime.now,
        help="When this event first occurred",
    )

    last_occurrence = fields.Datetime(
        string="Last Occurrence",
        default=fields.Datetime.now,
        help="When this event last occurred",
    )

    resolved_date = fields.Datetime(
        string="Resolved Date", help="When this issue was resolved"
    )

    resolved_by = fields.Many2one(
        "res.users", string="Resolved By", help="User who resolved this issue"
    )

    resolution_notes = fields.Text(
        string="Resolution Notes", help="Notes about how the issue was resolved"
    )

    tags = fields.Char(string="Tags", help="Comma-separated tags for categorization")

    @api.model
    def log_error(
        self,
        name,
        description=None,
        technical_details=None,
        affected_model=None,
        affected_method=None,
        affected_record_id=None,
        severity="high",
        tags=None,
    ):
        """
        Log an error event to the monitoring system
        """
        return self.create(
            {
                "name": name,
                "monitor_type": "error",
                "severity": severity,
                "description": description,
                "technical_details": technical_details,
                "affected_model": affected_model,
                "affected_method": affected_method,
                "affected_record_id": affected_record_id,
                "tags": tags,
            }
        )

    @api.model
    def log_warning(
        self,
        name,
        description=None,
        affected_model=None,
        affected_method=None,
        severity="medium",
        tags=None,
    ):
        """
        Log a warning event to the monitoring system
        """
        return self.create(
            {
                "name": name,
                "monitor_type": "warning",
                "severity": severity,
                "description": description,
                "affected_model": affected_model,
                "affected_method": affected_method,
                "tags": tags,
            }
        )

    @api.model
    def log_info(
        self,
        name,
        description=None,
        affected_model=None,
        affected_method=None,
        tags=None,
    ):
        """
        Log an information event to the monitoring system
        """
        return self.create(
            {
                "name": name,
                "monitor_type": "info",
                "severity": "low",
                "description": description,
                "affected_model": affected_model,
                "affected_method": affected_method,
                "tags": tags,
            }
        )

    @api.model
    def log_performance(
        self,
        name,
        description=None,
        technical_details=None,
        affected_model=None,
        affected_method=None,
        severity="low",
    ):
        """
        Log a performance monitoring event
        """
        return self.create(
            {
                "name": name,
                "monitor_type": "performance",
                "severity": severity,
                "description": description,
                "technical_details": technical_details,
                "affected_model": affected_model,
                "affected_method": affected_method,
                "tags": "performance",
            }
        )

    @api.model
    def health_check(self):
        """
        Perform system health check and log results
        """
        try:
            # Basic health checks
            checks = {
                "database": self._check_database_health(),
                "cache": self._check_cache_health(),
                "records": self._check_records_health(),
                "storage": self._check_storage_health(),
            }

            failed_checks = [k for k, v in checks.items() if not v]

            if failed_checks:
                self.log_warning(
                    f"Health Check Failed: {', '.join(failed_checks)}",
                    description=f"System health check identified issues in: {', '.join(failed_checks)}",
                    tags="health_check,system",
                )
                return False
            else:
                self.log_info(
                    "System Health Check Passed",
                    description="All system components are healthy",
                    tags="health_check,system",
                )
                return True

        except Exception as e:
            self.log_error(
                "Health Check Error",
                description="Error occurred during system health check",
                technical_details=str(e),
                severity="critical",
                tags="health_check,error",
            )
            return False

    def _check_database_health(self):
        """Check database connectivity and basic queries"""
        try:
            self.env.cr.execute("SELECT 1")
            return True
        except Exception:
            return False

    def _check_cache_health(self):
        """Check cache system health"""
        # Simple cache check - can be expanded
        return True

    def _check_records_health(self):
        """Check records management system health"""
        try:
            # Check if critical models are accessible
            self.env["records.management.record"].search_count([])
            return True
        except Exception:
            return False

    def _check_storage_health(self):
        """Check storage system health"""
        # Simple storage check - can be expanded
        return True

    @api.model
    def cleanup_old_logs(self):
        """
        Clean up old monitoring logs (called by cron job)
        Keep logs for 90 days, then archive/delete based on type
        """
        cutoff_date = fields.Datetime.now() - timedelta(days=90)

        # Delete old info and performance logs
        old_info_logs = self.search(
            [
                ("monitor_type", "in", ["info", "performance"]),
                ("create_date", "<", cutoff_date),
            ]
        )

        # Archive important logs (errors, warnings) instead of deleting
        old_important_logs = self.search(
            [
                ("monitor_type", "in", ["error", "warning", "security", "audit"]),
                ("create_date", "<", cutoff_date),
            ]
        )

        count_deleted = len(old_info_logs)
        count_archived = len(old_important_logs)

        old_info_logs.unlink()
        # For important logs, we could move them to an archive table
        # For now, just mark them as archived with a tag
        old_important_logs.write({"tags": "archived"})

        self.log_info(
            "Monitor Log Cleanup Completed",
            description=f"Deleted {count_deleted} info/performance logs, archived {count_archived} important logs",
            tags="cleanup,maintenance",
        )

        return True

    def action_resolve(self):
        """Mark monitoring entry as resolved"""
        self.write(
            {
                "status": "resolved",
                "resolved_date": fields.Datetime.now(),
                "resolved_by": self.env.user.id,
            }
        )

    def action_investigate(self):
        """Mark monitoring entry as under investigation"""
        self.write({"status": "investigating"})

    def action_ignore(self):
        """Mark monitoring entry as ignored"""
        self.write({"status": "ignored"})
