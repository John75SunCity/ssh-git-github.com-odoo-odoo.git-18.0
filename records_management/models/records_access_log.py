# -*- coding: utf-8 -*-
"""
Records Access Log Module

This module provides comprehensive access logging functionality for the Records Management System.
It tracks all document access events with detailed audit trails, user tracking, and compliance
reporting to support NAID AAA requirements and document security monitoring.

Key Features:
- Complete document access logging with user identification
- Detailed audit trails for compliance and security monitoring
- Real-time access tracking with timestamps and IP logging
- Integration with document lifecycle management
- NAID AAA compliance with encrypted audit signatures
- Automated reporting and alerting for suspicious access patterns

Business Processes:
1. Access Event Capture: Automatic logging of all document access events
2. User Authentication: Integration with Odoo security for user identification
3. Audit Trail Creation: Complete audit trail with timestamps and metadata
4. Compliance Reporting: Generate reports for regulatory compliance
5. Security Monitoring: Real-time monitoring for unauthorized access attempts
6. Data Retention: Automated log retention according to compliance requirements

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta


class RecordsAccessLog(models.Model):
    _name = "records.access.log"
    _description = "Records Access Log"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "access_date desc, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Log Entry Name",
        required=True,
        tracking=True,
        index=True,
        help="Unique identifier for the access log entry",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Accessing User",
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        help="User who accessed the document",
    )
    active = fields.Boolean(
        string="Active", default=True, help="Active status of the log entry"
    )

    # ============================================================================
    # DOCUMENT AND ACCESS INFORMATION
    # ============================================================================
    document_id = fields.Many2one(
        "records.document",
        string="Document",
        required=True,
        ondelete="cascade",
        tracking=True,
        help="Document that was accessed",
    )
    container_id = fields.Many2one(
        "records.container",
        string="Container",
        related="document_id.container_id",
        store=True,
        help="Container holding the accessed document",
    )
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="document_id.customer_id",
        store=True,
        help="Customer who owns the document",
    )
    location_id = fields.Many2one(
        "records.location",
        string="Location",
        related="document_id.location_id",
        store=True,
        help="Physical location of the document",
    )

    # ============================================================================
    # ACCESS DETAILS AND TIMING
    # ============================================================================
    access_date = fields.Datetime(
        string="Access Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="Date and time when document was accessed",
    )
    access_type = fields.Selection(
        [
            ("view", "View"),
            ("download", "Download"),
            ("print", "Print"),
            ("edit", "Edit"),
            ("delete", "Delete"),
            ("move", "Move"),
            ("scan", "Scan"),
            ("retrieve", "Physical Retrieval"),
        ],
        string="Access Type",
        required=True,
        tracking=True,
        help="Type of access performed on the document",
    )
    access_method = fields.Selection(
        [
            ("portal", "Customer Portal"),
            ("backend", "Backend System"),
            ("mobile", "Mobile App"),
            ("api", "API Access"),
            ("barcode", "Barcode Scan"),
            ("physical", "Physical Access"),
        ],
        string="Access Method",
        required=True,
        help="Method used to access the document",
    )
    ip_address = fields.Char(
        string="IP Address", help="IP address of the accessing device"
    )
    user_agent = fields.Text(string="User Agent", help="Browser/device information")
    session_id = fields.Char(string="Session ID", help="User session identifier")

    # ============================================================================
    # ACCESS RESULT AND VALIDATION
    # ============================================================================
    access_result = fields.Selection(
        [
            ("success", "Success"),
            ("denied", "Access Denied"),
            ("error", "Error"),
            ("partial", "Partial Access"),
        ],
        string="Access Result",
        default="success",
        required=True,
        tracking=True,
        help="Result of the access attempt",
    )
    error_message = fields.Text(
        string="Error Message", help="Error message if access failed"
    )
    permission_level = fields.Selection(
        [
            ("read", "Read Only"),
            ("write", "Read/Write"),
            ("admin", "Administrative"),
            ("owner", "Owner Access"),
        ],
        string="Permission Level",
        help="Permission level used for access",
    )
    authorized_by = fields.Many2one(
        "res.users",
        string="Authorized By",
        help="User who authorized the access if different from accessing user",
    )

    # ============================================================================
    # AUDIT AND COMPLIANCE TRACKING
    # ============================================================================
    audit_trail_id = fields.Many2one(
        "naid.audit.log", string="NAID Audit Trail", help="Related NAID audit log entry"
    )
    compliance_required = fields.Boolean(
        string="Compliance Required",
        compute="_compute_compliance_flags",
        store=True,
        help="Whether this access requires compliance documentation",
    )
    security_level = fields.Selection(
        string="Security Level",
        related="document_id.security_level",
        store=True,
        help="Security level of the accessed document",
    )
    risk_score = fields.Integer(
        string="Risk Score",
        compute="_compute_risk_score",
        store=True,
        help="Risk score for this access event (0-100)",
    )

    # ============================================================================
    # DOCUMENTATION AND NOTES
    # ============================================================================
    description = fields.Text(
        string="Description", help="Description of the access event"
    )
    notes = fields.Text(string="Notes", help="Additional notes about the access")
    business_justification = fields.Text(
        string="Business Justification",
        help="Business reason for accessing the document",
    )
    supervisor_notes = fields.Text(
        string="Supervisor Notes", help="Notes from supervisor regarding this access"
    )

    # ============================================================================
    # SYSTEM METADATA
    # ============================================================================
    sequence = fields.Integer(
        string="Sequence", default=10, help="Sequence for ordering log entries"
    )
    duration_seconds = fields.Integer(
        string="Access Duration (seconds)", help="How long the document was accessed"
    )
    file_size_accessed = fields.Integer(
        string="File Size Accessed (bytes)", help="Size of the file accessed"
    )
    checksum_verified = fields.Boolean(
        string="Checksum Verified",
        help="Whether document integrity was verified during access",
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("document_id", "access_type", "security_level")
    def _compute_compliance_flags(self):
        """Determine if compliance documentation is required"""
        for record in self:
            # Compliance required for sensitive documents or certain access types
            compliance_access_types = [
                "download",
                "print",
                "edit",
                "delete",
                "retrieve",
            ]
            sensitive_levels = ["confidential", "restricted", "classified"]

            record.compliance_required = (
                record.access_type in compliance_access_types
                or (record.security_level and record.security_level in sensitive_levels)
            )

    @api.depends("access_type", "security_level", "access_result", "user_id")
    def _compute_risk_score(self):
        """Calculate risk score for access event"""
        for record in self:
            risk_score = 0

            # Base risk by access type
            risk_by_type = {
                "view": 10,
                "download": 30,
                "print": 40,
                "edit": 60,
                "delete": 80,
                "move": 70,
                "scan": 20,
                "retrieve": 50,
            }
            risk_score += risk_by_type.get(record.access_type, 10)

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner", 
        related="customer_id",
        store=True,
        help="Related partner field for One2many relationships compatibility"
    )

            # Risk by security level
            risk_by_security = {
                "public": 0,
                "internal": 10,
                "confidential": 30,
                "restricted": 50,
                "classified": 70,
            }
            risk_score += risk_by_security.get(record.security_level, 0)

            # Risk by result
            if record.access_result == "denied":
                risk_score += 20
            elif record.access_result == "error":
                risk_score += 15

            # Risk by time (after hours = higher risk)
            if record.access_date:
                hour = None
                if hasattr(record.access_date, "hour"):
                    hour = record.access_date.hour
                elif isinstance(record.access_date, str):
                    try:
                        dt = fields.Datetime.from_string(record.access_date)
                        hour = dt.hour
                    except Exception:
                        hour = None

                if hour is not None and (hour < 6 or hour > 22):  # After hours access
                    risk_score += 20

            record.risk_score = min(risk_score, 100)  # Cap at 100

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence and audit trail"""
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("records.access.log")
                    or "LOG-NEW"
                )

            # Create audit trail for compliance-required access
            if vals.get("compliance_required"):
                audit_vals = {
                    "event_type": "document_access",
                    "description": f"Document access: {vals.get('access_type', 'unknown')}",
                    "user_id": vals.get("user_id"),
                    "document_id": vals.get("document_id"),
                }
                try:
                    audit_log = self.env["naid.audit.log"].sudo().create(audit_vals)
                    vals["audit_trail_id"] = audit_log.id
                except Exception:
                    # Continue without audit trail if NAID module not available
                    pass

        return super().create(vals_list)

    def write(self, vals):
        """Override write for audit trail updates"""
        result = super().write(vals)

        # Log significant changes
        if any(key in vals for key in ["access_result", "error_message", "risk_score"]):
            self.message_post(
                body=_("Access log updated: %s")
                % ", ".join(f"{k}: {v}" for k, v in vals.items())
            )

        return result

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def log_document_access(
        self, document, access_type, access_method="backend", **kwargs
    ):
        """Log a document access event"""
        vals = {
            "document_id": document.id,
            "access_type": access_type,
            "access_method": access_method,
            "ip_address": kwargs.get("ip_address"),
            "user_agent": kwargs.get("user_agent"),
            "session_id": kwargs.get("session_id"),
            "business_justification": kwargs.get("justification"),
        }

        return self.create(vals)

    @api.model
    def log_portal_access(self, document_id, access_type, request=None):
        """Log document access from customer portal"""
        vals = {
            "document_id": document_id,
            "access_type": access_type,
            "access_method": "portal",
        }

        if request:
            vals.update(
                {
                    "ip_address": request.httprequest.remote_addr,
                    "user_agent": request.httprequest.headers.get("User-Agent"),
                    "session_id": request.session.sid,
                }
            )

        return self.create(vals)

    def get_access_summary(self):
        """Get access summary for reporting"""
        self.ensure_one()
        return {
            "log_name": self.name,
            "document": self.document_id.name if self.document_id else None,
            "user": self.user_id.name if self.user_id else None,
            "access_date": self.access_date,
            "access_type": self.access_type,
            "access_result": self.access_result,
            "risk_score": self.risk_score,
            "compliance_required": self.compliance_required,
        }

    def generate_audit_report(self):
        """Generate audit report for this access log"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.report_access_log_audit",
            "report_type": "qweb-pdf",
            "data": {"log_id": self.id},
            "context": self.env.context,
        }

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_reviewed(self):
        """Mark access log as reviewed"""
        self.ensure_one()
        self.message_post(
            body=_("Access log reviewed by %s") % self.env.user.name,
            message_type="comment",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Access Log Reviewed"),
                "message": _("Access log has been marked as reviewed."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_flag_suspicious(self):
        """Flag access as suspicious for investigation"""
        self.ensure_one()

        # Create investigation activity
        try:
            activity_type = self.env.ref("mail.mail_activity_data_todo")
            manager_group = self.env.ref("records_management.group_records_manager")

            user_id = self.env.user.id
            if manager_group and manager_group.users:
                user_id = manager_group.users[0].id

            self.activity_schedule(
                activity_type_id=activity_type.id,
                summary=_("Investigate Suspicious Access"),
                note=_("Access log flagged as suspicious: %s") % self.name,
                user_id=user_id,
            )
        except Exception:
            # Continue without activity if references not available
            pass

        self.message_post(
            body=_("Access flagged as suspicious for investigation"),
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )

        return True

    def action_create_audit_trail(self):
        """Create formal audit trail entry"""
        self.ensure_one()

        if not self.audit_trail_id:
            audit_vals = {
                "event_type": "document_access",
                "description": f"Document access audit trail for {self.name}",
                "user_id": self.user_id.id,
                "document_id": self.document_id.id,
                "access_log_id": self.id,
                "risk_level": (
                    "high"
                    if self.risk_score > 70
                    else "medium" if self.risk_score > 40 else "low"
                ),
            }

            try:
                audit_log = self.env["naid.audit.log"].create(audit_vals)
                self.write({"audit_trail_id": audit_log.id})

                self.message_post(body=_("Audit trail created: %s") % audit_log.name)

                return {
                    "type": "ir.actions.act_window",
                    "name": _("Audit Trail"),
                    "res_model": "naid.audit.log",
                    "res_id": self.audit_trail_id.id,
                    "view_mode": "form",
                    "target": "current",
                }
            except Exception:
                # Return notification if audit trail creation fails
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Audit Trail Error"),
                        "message": _("Could not create audit trail entry."),
                        "type": "warning",
                        "sticky": False,
                    },
                }

        return True

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("access_date")
    def _check_access_date(self):
        """Validate access date is not in the future"""
        for record in self:
            if record.access_date and record.access_date > fields.Datetime.now():
                raise ValidationError(_("Access date cannot be in the future."))

    @api.constrains("risk_score")
    def _check_risk_score(self):
        """Validate risk score is within valid range"""
        for record in self:
            if record.risk_score < 0 or record.risk_score > 100:
                raise ValidationError(_("Risk score must be between 0 and 100."))

    @api.constrains("duration_seconds")
    def _check_duration(self):
        """Validate access duration is reasonable"""
        for record in self:
            if record.duration_seconds and record.duration_seconds < 0:
                raise ValidationError(_("Access duration cannot be negative."))

            # Flag unusually long access times (>24 hours)
            if record.duration_seconds and record.duration_seconds > 86400:
                record.message_post(
                    body=_(
                        "Warning: Unusually long access duration detected: %d seconds"
                    )
                    % record.duration_seconds,
                    message_type="comment",
                )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name_parts = [record.name]

            if record.document_id:
                name_parts.append(f"({record.document_id.name})")

            if record.access_type:
                name_parts.append(f"- {record.access_type.title()}")

            if record.user_id:
                name_parts.append(f"by {record.user_id.name}")

            result.append((record.id, " ".join(name_parts)))
        return result

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Enhanced search by name, document, or user"""
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                "|",
                ("name", operator, name),
                ("document_id.name", operator, name),
                ("user_id.name", operator, name),
                ("description", operator, name),
            ]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def get_access_statistics(self, domain=None, group_by="access_type"):
        """Get access statistics for reporting"""
        domain = domain or []
        logs = self.search(domain)

        if group_by == "access_type":
            stats = {}
            for access_type in [
                "view",
                "download",
                "print",
                "edit",
                "delete",
                "retrieve",
            ]:
                count = logs.filtered(lambda l: l.access_type == access_type)
                stats[access_type] = len(count)
            return stats

        elif group_by == "user":
            stats = {}
            for log in logs:
                user_name = log.user_id.name or "Unknown"
                stats[user_name] = stats.get(user_name, 0) + 1
            return stats

        elif group_by == "risk_level":
            stats = {"low": 0, "medium": 0, "high": 0}
            for log in logs:
                if log.risk_score <= 30:
                    stats["low"] += 1
                elif log.risk_score <= 70:
                    stats["medium"] += 1
                else:
                    stats["high"] += 1
            return stats

        return {}

    @api.model
    def cleanup_old_logs(self, days=365):
        """Clean up old access logs based on retention policy"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_logs = self.search(
            [
                ("access_date", "<", cutoff_date),
                ("compliance_required", "=", False),  # Keep compliance logs longer
            ]
        )

        if old_logs:
            count = len(old_logs)
            old_logs.unlink()
            return count
        return 0
