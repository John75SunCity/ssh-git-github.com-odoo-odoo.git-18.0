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
import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class RecordsAccessLog(models.Model):
    """Records Access Log
    
    Comprehensive access logging for documents with NAID compliance tracking,
    security monitoring, and automated audit trail generation.
    """
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
        help="Unique identifier for the access log entry"
    )
    
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )
    
    user_id = fields.Many2one(
        "res.users",
        string="Accessing User",
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        help="User who accessed the document"
    )
    
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Active status of the log entry"
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
        help="Document that was accessed"
    )
    
    container_id = fields.Many2one(
        "records.container",
        string="Container",
        related="document_id.container_id",
        store=True,
        help="Container holding the accessed document"
    )
    
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="document_id.customer_id",
        store=True,
        help="Customer who owns the document"
    )
    
    location_id = fields.Many2one(
        "records.location",
        string="Location",
        related="document_id.location_id",
        store=True,
        help="Physical location of the document"
    )

    # ============================================================================
    # ACCESS DETAILS AND TIMING
    # ============================================================================
    access_date = fields.Datetime(
        string="Access Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="Date and time when document was accessed"
    )
    
    access_type = fields.Selection([
        ("view", "View"),
        ("download", "Download"),
        ("print", "Print"),
        ("edit", "Edit"),
        ("delete", "Delete"),
        ("move", "Move"),
        ("scan", "Scan"),
        ("retrieve", "Physical Retrieval"),
    ], string="Access Type",
       required=True,
       tracking=True,
       help="Type of access performed on the document")
    
    access_method = fields.Selection([
        ("portal", "Customer Portal"),
        ("backend", "Backend System"),
        ("mobile", "Mobile App"),
        ("api", "API Access"),
        ("barcode", "Barcode Scan"),
        ("physical", "Physical Access"),
    ], string="Access Method",
       required=True,
       help="Method used to access the document")
    
    ip_address = fields.Char(
        string="IP Address",
        help="IP address of the accessing device"
    )
    
    user_agent = fields.Text(
        string="User Agent",
        help="Browser/device information"
    )
    
    session_id = fields.Char(
        string="Session ID",
        help="User session identifier"
    )

    # ============================================================================
    # ACCESS RESULT AND VALIDATION
    # ============================================================================
    access_result = fields.Selection([
        ("success", "Success"),
        ("denied", "Access Denied"),
        ("error", "Error"),
        ("partial", "Partial Access"),
    ], string="Access Result",
       default="success",
       required=True,
       tracking=True,
       help="Result of the access attempt")
    
    error_message = fields.Text(
        string="Error Message",
        help="Error message if access failed"
    )
    
    permission_level = fields.Selection([
        ("read", "Read Only"),
        ("write", "Read/Write"),
        ("admin", "Administrative"),
        ("owner", "Owner Access"),
    ], string="Permission Level",
       help="Permission level used for access")
    
    authorized_by_id = fields.Many2one(
        "res.users",
        string="Authorized By",
        help="User who authorized the access if different from accessing user"
    )

    # ============================================================================
    # AUDIT AND COMPLIANCE TRACKING
    # ============================================================================
    audit_trail_id = fields.Many2one(
        "naid.audit.log",
        string="NAID Audit Trail",
        help="Related NAID audit log entry"
    )
    
    compliance_required = fields.Boolean(
        string="Compliance Required",
        compute="_compute_compliance_flags",
        store=True,
        help="Whether this access requires compliance documentation"
    )
    
    security_level = fields.Selection(
        string="Security Level",
        related="document_id.security_level",
        store=True,
        help="Security level of the accessed document"
    )
    
    risk_score = fields.Integer(
        string="Risk Score",
        compute="_compute_risk_score",
        store=True,
        help="Risk score for this access event (0-100)"
    )

    # ============================================================================
    # DOCUMENTATION AND NOTES
    # ============================================================================
    description = fields.Text(
        string="Description",
        help="Description of the access event"
    )
    
    notes = fields.Text(
        string="Notes",
        help="Additional notes about the access"
    )
    
    business_justification = fields.Text(
        string="Business Justification",
        help="Business reason for accessing the document"
    )
    
    supervisor_notes = fields.Text(
        string="Supervisor Notes",
        help="Notes from supervisor regarding this access"
    )

    # ============================================================================
    # SYSTEM METADATA
    # ============================================================================
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Sequence for ordering log entries"
    )
    
    duration_seconds = fields.Integer(
        string="Access Duration (seconds)",
        help="How long the document was accessed"
    )
    
    file_size_accessed = fields.Integer(
        string="File Size Accessed (bytes)",
        help="Size of the file accessed"
    )
    
    checksum_verified = fields.Boolean(
        string="Checksum Verified",
        help="Whether document integrity was verified during access"
    )

    # ============================================================================
    # RELATIONSHIP COMPATIBILITY FIELDS
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        related="customer_id",
        store=True,
        help="Related partner field for One2many relationships compatibility"
    )

    # ============================================================================
    # WORKFLOW STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)]
    )
    
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)]
    )
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)]
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("document_id.security_level", "access_type")
    def _compute_compliance_flags(self):
        """Determine if compliance documentation is required"""
        for record in self:
            compliance_access_types = {"download", "print", "edit", "delete", "retrieve"}
            sensitive_levels = {"confidential", "restricted", "classified"}
            
            record.compliance_required = (
                record.access_type in compliance_access_types
                or record.security_level in sensitive_levels
            )

    @api.depends("access_type", "security_level", "access_result", "access_date")
    def _compute_risk_score(self):
        """Calculate risk score for access event"""
        for record in self:
            risk_score = 0
            
            # Risk by access type
            risk_by_type = {
                "view": 10, "download": 30, "print": 40, "edit": 60,
                "delete": 80, "move": 70, "scan": 20, "retrieve": 50
            }
            risk_score += risk_by_type.get(record.access_type, 10)
            
            # Risk by security level
            risk_by_security = {
                "public": 0, "internal": 10, "confidential": 30,
                "restricted": 50, "classified": 70
            }
            risk_score += risk_by_security.get(record.security_level, 0)
            
            # Access result impact
            if record.access_result == "denied":
                risk_score += 20
            elif record.access_result == "error":
                risk_score += 15
            
            # Time-based risk (outside business hours)
            if record.access_date:
                hour = record.access_date.hour
                if hour < 6 or hour > 22:  # Outside business hours
                    risk_score += 20
            
            record.risk_score = min(risk_score, 100)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence and audit trail"""
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("records.access.log") or _("New Log")
            
            # Create audit trail for compliance-required access
            if vals.get("compliance_required"):
                audit_vals = {
                    "event_type": "document_access",
                    "description": _("Document access: %s", vals.get('access_type', 'unknown')),
                    "user_id": vals.get("user_id"),
                    "document_id": vals.get("document_id"),
                }
                try:
                    audit_log = self.env["naid.audit.log"].sudo().create(audit_vals)
                    vals["audit_trail_id"] = audit_log.id
                except Exception as e:
                    _logger.warning(_("Could not create NAID audit log: %s", e))
        
        return super().create(vals_list)

    def write(self, vals):
        """Override write for audit trail updates"""
        res = super().write(vals)
        
        if any(key in vals for key in ["access_result", "error_message", "risk_score"]):
            for record in self:
                updates = ", ".join(["%s: %s" % (key, vals[key]) for key in vals if key in record._fields])
                record.message_post(body=_("Access log updated: %s", updates))
        
        return res

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    @api.model
    def log_document_access(self, document, access_type, access_method="backend", **kwargs):
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
            "access_method": "portal"
        }
        
        if request:
            vals.update({
                "ip_address": request.httprequest.remote_addr,
                "user_agent": request.httprequest.headers.get("User-Agent"),
                "session_id": request.session.sid,
            })
        
        return self.create(vals)

    def get_access_summary(self):
        """Get access summary for reporting"""
        self.ensure_one()
        return {
            "log_name": self.name,
            "document": self.document_id.display_name,
            "user": self.user_id.name,
            "access_date": self.access_date,
            "access_type": self.access_type,
            "access_result": self.access_result,
            "risk_score": self.risk_score,
            "compliance_required": self.compliance_required,
        }

    def generate_audit_report(self):
        """Generate audit report for this access log"""
        self.ensure_one()
        return self.env.ref('records_management.action_report_access_log_audit').report_action(self)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_reviewed(self):
        """Mark access log as reviewed"""
        self.ensure_one()
        self.message_post(body=_("Access log reviewed by %s", self.env.user.name))
        return True

    def action_flag_suspicious(self):
        """Flag access as suspicious for investigation"""
        self.ensure_one()
        
        try:
            activity_type = self.env.ref("mail.mail_activity_data_todo")
            manager_group = self.env.ref("records_management.group_records_manager")
            user_id = manager_group.users[0].id if manager_group.users else self.env.user.id
            
            self.activity_schedule(
                activity_type_id=activity_type.id,
                summary=_("Investigate Suspicious Access"),
                note=_("Access log flagged as suspicious: %s", self.name),
                user_id=user_id,
            )
            self.message_post(body=_("Access flagged as suspicious for investigation"))
        except Exception as e:
            _logger.warning(_("Could not schedule suspicious access activity: %s", e))
        
        return True

    def action_create_audit_trail(self):
        """Create formal audit trail entry"""
        self.ensure_one()
        
        if self.audit_trail_id:
            raise UserError(_("An audit trail already exists for this log."))
        
        try:
            # Determine risk level based on score
            risk_level = "low"
            if self.risk_score > 70:
                risk_level = "high"
            elif self.risk_score > 40:
                risk_level = "medium"
            
            audit_vals = {
                "event_type": "document_access",
                "description": _("Manual audit trail for access log %s", self.name),
                "user_id": self.user_id.id,
                "document_id": self.document_id.id,
                "access_log_id": self.id,
                "risk_level": risk_level,
            }
            
            audit_log = self.env["naid.audit.log"].create(audit_vals)
            self.write({"audit_trail_id": audit_log.id})
            self.message_post(body=_("Audit trail created: %s", audit_log.name))
        except Exception as e:
            raise UserError(_("Could not create audit trail entry: %s", e))
        
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
            if not 0 <= record.risk_score <= 100:
                raise ValidationError(_("Risk score must be between 0 and 100."))

    @api.constrains("duration_seconds")
    def _check_duration(self):
        """Validate access duration is reasonable"""
        for record in self:
            if record.duration_seconds and record.duration_seconds < 0:
                raise ValidationError(_("Access duration cannot be negative."))
            if record.duration_seconds and record.duration_seconds > 86400:  # 24 hours
                self.message_post(
                    body=_("Warning: Unusually long access duration detected: %s seconds", 
                          record.duration_seconds)
                )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = _("%(name)s (%(document)s) - %(access_type)s by %(user)s", {
                'name': record.name,
                'document': record.document_id.name,
                'access_type': record.access_type.title(),
                'user': record.user_id.name
            })
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        """Enhanced search by name, document, or user"""
        args = args or []
        domain = []
        
        if name:
            domain = [
                "|", "|", "|",
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
        
        if group_by not in ['access_type', 'user_id', 'risk_level', 'security_level']:
            raise UserError(_("Invalid group_by parameter."))
        
        if group_by == "risk_level":
            # Custom handling for risk levels based on score ranges
            low = self.search_count(domain + [('risk_score', '<=', 30)])
            medium = self.search_count(domain + [('risk_score', '>', 30), ('risk_score', '<=', 70)])
            high = self.search_count(domain + [('risk_score', '>', 70)])
            return {'low': low, 'medium': medium, 'high': high}
        
        # Use read_group for performance with other group_by options
        grouped_data = self.read_group(domain, [group_by], [group_by])
        return {
            (item[group_by][1] if isinstance(item[group_by], tuple) else item[group_by] or 'N/A'): 
            item["%s_count" % group_by]
            for item in grouped_data
        }

    @api.model
    def cleanup_old_logs(self, days=365):
        """Clean up old access logs based on retention policy"""
        _logger.info(_("Starting cleanup of old access logs older than %d days.", days))
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        
        # Only delete non-compliance-required logs
        domain = [
            ("access_date", "<", cutoff_date),
            ("compliance_required", "=", False)
        ]
        
        # Use search_count for performance, then search and unlink if necessary
        count = self.search_count(domain)
        if count > 0:
            old_logs = self.search(domain)
            old_logs.unlink()
            _logger.info(_("Successfully cleaned up %d old access logs.", count))
        else:
            _logger.info(_("No old access logs to clean up."))
        
        return count

    # ============================================================================
    # REPORTING METHODS
    # ============================================================================
    @api.model
    def generate_access_report(self, date_from=None, date_to=None, user_ids=None):
        """Generate comprehensive access report"""
        domain = []
        
        if date_from:
            domain.append(('access_date', '>=', date_from))
        if date_to:
            domain.append(('access_date', '<=', date_to))
        if user_ids:
            domain.append(('user_id', 'in', user_ids))
        
        access_logs = self.search(domain)
        
        # Compile statistics
        total_accesses = len(access_logs)
        successful_accesses = len(access_logs.filtered(lambda r: r.access_result == 'success'))
        denied_accesses = len(access_logs.filtered(lambda r: r.access_result == 'denied'))
        high_risk_accesses = len(access_logs.filtered(lambda r: r.risk_score > 70))
        
        # User access patterns
        user_stats = {}
        for log in access_logs:
            user_name = log.user_id.name
            if user_name not in user_stats:
                user_stats[user_name] = {'count': 0, 'risk_total': 0}
            user_stats[user_name]['count'] += 1
            user_stats[user_name]['risk_total'] += log.risk_score
        
        # Calculate average risk per user
        for user in user_stats:
            if user_stats[user]['count'] > 0:
                user_stats[user]['avg_risk'] = user_stats[user]['risk_total'] / user_stats[user]['count']
        
        return {
            'period': {'from': date_from, 'to': date_to},
            'summary': {
                'total_accesses': total_accesses,
                'successful_accesses': successful_accesses,
                'denied_accesses': denied_accesses,
                'high_risk_accesses': high_risk_accesses,
                'success_rate': (successful_accesses / total_accesses * 100) if total_accesses > 0 else 0,
            },
            'user_statistics': user_stats,
            'access_logs': access_logs.ids,
        }

    def action_export_audit_data(self):
        """Export audit data for compliance reporting"""
        self.ensure_one()
        
        export_data = {
            'log_reference': self.name,
            'document_name': self.document_id.name,
            'document_barcode': self.document_id.barcode,
            'access_user': self.user_id.name,
            'access_date': self.access_date.isoformat() if self.access_date else None,
            'access_type': self.access_type,
            'access_method': self.access_method,
            'access_result': self.access_result,
            'risk_score': self.risk_score,
            'compliance_required': self.compliance_required,
            'ip_address': self.ip_address,
            'session_id': self.session_id,
            'business_justification': self.business_justification,
            'audit_trail_reference': self.audit_trail_id.name if self.audit_trail_id else None,
        }
        
        return export_data

    @api.model
    def get_security_dashboard_data(self):
        """Get data for security monitoring dashboard"""
        today = fields.Date.today()
        
        # Recent high-risk access attempts
        high_risk_logs = self.search([
            ('risk_score', '>', 70),
            ('access_date', '>=', fields.Datetime.now() - timedelta(days=7))
        ], limit=10)
        
        # Failed access attempts today
        failed_today = self.search_count([
            ('access_result', '!=', 'success'),
            ('access_date', '>=', today)
        ])
        
        # Most active users this week
        user_activity = self.read_group(
            [('access_date', '>=', fields.Datetime.now() - timedelta(days=7))],
            ['user_id'],
            ['user_id']
        )
        
        return {
            'high_risk_accesses': [log.get_access_summary() for log in high_risk_logs],
            'failed_attempts_today': failed_today,
            'user_activity': user_activity,
            'compliance_logs': self.search_count([('compliance_required', '=', True)]),
        }