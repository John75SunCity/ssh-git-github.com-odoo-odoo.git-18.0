# -*- coding: utf-8 -*-
"""
Signed Document Audit Trail Model

This module provides comprehensive audit trail functionality for signed documents within
the Records Management System. It tracks all actions performed on signed documents with
detailed logging for compliance, security monitoring, and legal requirements.

Key Features:
- Complete action tracking with timestamps and user identification
- IP address logging for security monitoring
- Integration with NAID AAA compliance framework
- Real-time audit trail for legal document workflows
- Partner association for customer-facing document processes

Business Processes:
1. Action Logging: Automatic tracking of all document interactions
2. User Authentication: Complete user identification and authorization tracking
3. Security Monitoring: IP address and session tracking for compliance
4. Compliance Reporting: Generate audit reports for regulatory requirements
5. Legal Documentation: Maintain immutable audit records for legal proceedings

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SignedDocumentAudit(models.Model):
    """Signed Document Audit Trail
    
    Comprehensive audit trail tracking for all signed document actions
    with complete compliance logging and security monitoring.
    """
    _name = "signed.document.audit"
    _description = "Signed Document Audit Trail"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "timestamp desc, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Audit Entry Name",
        required=True,
        tracking=True,
        index=True,
        help="Unique identifier for this audit entry"
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True
    )

    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this audit entry"
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether this audit entry is active"
    )

    # ============================================================================
    # DOCUMENT AND ACTION TRACKING
    # ============================================================================
    document_id = fields.Many2one(
        "signed.document",
        string="Signed Document",
        required=True,
        ondelete="cascade",
        tracking=True,
        help="The signed document this audit entry relates to"
    )

    action = fields.Selection([
        ("created", "Document Created"),
        ("signed", "Document Signed"),
        ("viewed", "Document Viewed"),
        ("downloaded", "Document Downloaded"),
        ("shared", "Document Shared"),
        ("modified", "Document Modified"),
        ("cancelled", "Signature Cancelled"),
        ("completed", "Process Completed"),
        ("voided", "Document Voided"),
        ("archived", "Document Archived"),
    ], string="Action Performed",
       required=True,
       tracking=True,
       help="Type of action performed on the document")

    action_description = fields.Char(
        string="Action Description",
        help="Brief description of the action performed"
    )

    # ============================================================================
    # USER AND SESSION TRACKING
    # ============================================================================
    performing_user_id = fields.Many2one(
        "res.users",
        string="Performing User",
        required=True,
        help="User who performed the action"
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Associated Partner",
        help="Partner associated with this audit entry"
    )

    ip_address = fields.Char(
        string="IP Address",
        help="IP address from which the action was performed"
    )

    user_agent = fields.Text(
        string="User Agent",
        help="Browser/device information from the session"
    )

    session_id = fields.Char(
        string="Session ID",
        help="User session identifier"
    )

    # ============================================================================
    # TIMESTAMP AND LOCATION TRACKING
    # ============================================================================
    timestamp = fields.Datetime(
        string="Action Timestamp",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        index=True,
        help="When the action was performed"
    )

    timezone = fields.Char(
        string="Timezone",
        help="Timezone where the action was performed"
    )

    geolocation = fields.Char(
        string="Geolocation",
        help="Geographic location information if available"
    )

    # ============================================================================
    # AUDIT DETAILS AND COMPLIANCE
    # ============================================================================
    details = fields.Text(
        string="Action Details",
        help="Detailed information about the action performed"
    )

    before_state = fields.Text(
        string="State Before Action",
        help="Document state before the action was performed"
    )

    after_state = fields.Text(
        string="State After Action",
        help="Document state after the action was performed"
    )

    compliance_required = fields.Boolean(
        string="Compliance Required",
        default=True,
        help="Whether this action requires compliance documentation"
    )

    naid_compliant = fields.Boolean(
        string="NAID Compliant",
        default=True,
        help="Whether this audit entry meets NAID AAA standards"
    )

    # ============================================================================
    # SECURITY AND VERIFICATION
    # ============================================================================
    verification_hash = fields.Char(
        string="Verification Hash",
        help="Hash for verifying audit entry integrity"
    )

    signature_verification = fields.Boolean(
        string="Signature Verified",
        help="Whether the document signature was verified during this action"
    )

    certificate_id = fields.Many2one(
        "digital.certificate",
        string="Digital Certificate",
        help="Digital certificate used for verification"
    )

    risk_level = fields.Selection([
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ], string="Risk Level",
       default="low",
       help="Risk level associated with this action")

    # ============================================================================
    # WORKFLOW STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('logged', 'Logged'),
        ('verified', 'Verified'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the audit entry')

    # ============================================================================
    # BUSINESS RELATIONSHIPS
    # ============================================================================
    request_id = fields.Many2one(
        "portal.request",
        string="Portal Request",
        help="Portal request that initiated this action"
    )

    workflow_instance_id = fields.Many2one(
        "workflow.instance",
        string="Workflow Instance",
        help="Workflow instance associated with this action"
    )

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
    @api.depends("action", "performing_user_id", "timestamp")
    def _compute_audit_summary(self):
        """Compute audit summary for reporting"""
        for record in self:
            if record.performing_user_id and record.timestamp:
                record.audit_summary = _("%(action)s by %(user)s at %(time)s", {
                    'action': dict(record._fields['action'].selection).get(record.action, record.action),
                    'user': record.performing_user_id.name,
                    'time': record.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                })
            else:
                record.audit_summary = _("Incomplete audit entry")

    audit_summary = fields.Char(
        string="Audit Summary",
        compute="_compute_audit_summary",
        store=True,
        help="Brief summary of the audit entry"
    )

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add auto-numbering and validation"""
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("signed.document.audit") or _("New")
            
            # Set performing user if not specified
            if not vals.get("performing_user_id"):
                vals["performing_user_id"] = self.env.user.id
            
            # Generate verification hash
            if not vals.get("verification_hash"):
                vals["verification_hash"] = self._generate_verification_hash(vals)
        
        records = super().create(vals_list)
        
        # Create NAID audit log entry for compliance
        for record in records:
            if record.naid_compliant:
                record._create_naid_audit_log()
        
        return records

    def write(self, vals):
        """Override write to track changes"""
        result = super().write(vals)
        
        # Log state changes
        if "state" in vals:
            for record in self:
                record.message_post(
                    body=_("Audit entry state changed to %s", vals["state"])
                )
        
        return result

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_verify_audit(self):
        """Verify the integrity of this audit entry"""
        self.ensure_one()
        
        # Verify hash integrity
        current_hash = self._generate_verification_hash({
            'document_id': self.document_id.id,
            'action': self.action,
            'performing_user_id': self.performing_user_id.id,
            'timestamp': self.timestamp,
        })
        
        if current_hash != self.verification_hash:
            raise UserError(_("Audit entry integrity verification failed"))
        
        self.write({'state': 'verified'})
        self.message_post(body=_("Audit entry verified successfully"))

    def action_archive_audit(self):
        """Archive this audit entry"""
        self.ensure_one()
        
        if self.state != 'verified':
            raise UserError(_("Only verified audit entries can be archived"))
        
        self.write({'state': 'archived'})
        self.message_post(body=_("Audit entry archived"))

    def action_view_document(self):
        """View the related signed document"""
        self.ensure_one()
        
        if not self.document_id:
            raise UserError(_("No document associated with this audit entry"))
        
        return {
            "type": "ir.actions.act_window",
            "res_model": "signed.document",
            "view_mode": "form",
            "res_id": self.document_id.id,
            "target": "current",
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    @api.model
    def log_document_action(self, document, action, details=None, **kwargs):
        """Log an action performed on a document"""
        vals = {
            'document_id': document.id,
            'action': action,
            'details': details or '',
            'performing_user_id': kwargs.get('user_id', self.env.user.id),
            'partner_id': kwargs.get('partner_id'),
            'ip_address': kwargs.get('ip_address'),
            'user_agent': kwargs.get('user_agent'),
            'session_id': kwargs.get('session_id'),
            'before_state': kwargs.get('before_state'),
            'after_state': kwargs.get('after_state'),
        }
        
        return self.create(vals)

    def _generate_verification_hash(self, vals):
        """Generate verification hash for audit entry integrity"""
        import hashlib
        import json
        
        # Create a deterministic hash from key audit data
        hash_data = {
            'document_id': vals.get('document_id'),
            'action': vals.get('action'),
            'user_id': vals.get('performing_user_id'),
            'timestamp': str(vals.get('timestamp', fields.Datetime.now())),
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()[:32]

    def _create_naid_audit_log(self):
        """Create NAID audit log entry for compliance"""
        self.ensure_one()
        
        try:
            self.env['naid.audit.log'].create({
                'event_type': 'document_action',
                'description': _("Signed document action: %s", self.action),
                'user_id': self.performing_user_id.id,
                'document_id': self.document_id.id,
                'audit_entry_id': self.id,
                'compliance_level': 'aaa',
            })
        except Exception as e:
            # Log error but don't fail the audit entry creation
            self.message_post(
                body=_("Warning: Could not create NAID audit log: %s", str(e)),
                message_type='comment'
            )

    def get_audit_summary_data(self):
        """Get audit summary data for reporting"""
        self.ensure_one()
        
        return {
            'entry_name': self.name,
            'document_name': self.document_id.name if self.document_id else '',
            'action': self.action,
            'action_display': dict(self._fields['action'].selection).get(self.action, self.action),
            'performing_user': self.performing_user_id.name,
            'timestamp': self.timestamp,
            'ip_address': self.ip_address or '',
            'partner': self.partner_id.name if self.partner_id else '',
            'risk_level': self.risk_level,
            'compliance_status': 'Compliant' if self.naid_compliant else 'Non-Compliant',
            'state': self.state,
        }

    # ============================================================================
    # REPORTING METHODS
    # ============================================================================
    @api.model
    def generate_audit_report(self, date_from=None, date_to=None, document_ids=None):
        """Generate comprehensive audit report"""
        domain = []
        
        if date_from:
            domain.append(('timestamp', '>=', date_from))
        if date_to:
            domain.append(('timestamp', '<=', date_to))
        if document_ids:
            domain.append(('document_id', 'in', document_ids))
        
        audit_entries = self.search(domain, order='timestamp desc')
        
        # Compile statistics
        total_entries = len(audit_entries)
        by_action = {}
        by_user = {}
        risk_summary = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        for entry in audit_entries:
            # By action
            if entry.action not in by_action:
                by_action[entry.action] = 0
            by_action[entry.action] += 1
            
            # By user
            user_name = entry.performing_user_id.name
            if user_name not in by_user:
                by_user[user_name] = 0
            by_user[user_name] += 1
            
            # Risk level
            if entry.risk_level in risk_summary:
                risk_summary[entry.risk_level] += 1
        
        return {
            'period': {'from': date_from, 'to': date_to},
            'total_entries': total_entries,
            'by_action': by_action,
            'by_user': by_user,
            'risk_summary': risk_summary,
            'entries': [entry.get_audit_summary_data() for entry in audit_entries],
            'compliance_rate': len(audit_entries.filtered('naid_compliant')) / total_entries * 100 if total_entries > 0 else 0,
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("timestamp")
    def _check_timestamp(self):
        """Validate timestamp is not in the future"""
        for record in self:
            if record.timestamp and record.timestamp > fields.Datetime.now():
                raise ValidationError(_("Audit timestamp cannot be in the future"))

    @api.constrains("verification_hash")
    def _check_hash_integrity(self):
        """Validate hash integrity"""
        for record in self:
            if record.verification_hash and len(record.verification_hash) != 32:
                raise ValidationError(_("Invalid verification hash format"))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = _("%(name)s - %(action)s (%(user)s)", {
                'name': record.name,
                'action': dict(record._fields['action'].selection).get(record.action, record.action),
                'user': record.performing_user_id.name
            })
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        """Enhanced search by name, action, or user"""
        args = args or []
        domain = []
        
        if name:
            domain = [
                "|", "|", "|",
                ("name", operator, name),
                ("action", operator, name),
                ("performing_user_id.name", operator, name),
                ("document_id.name", operator, name),
            ]
        
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def cleanup_old_audits(self, days=365):
        """Clean up old audit entries based on retention policy"""
        from datetime import timedelta
        
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        
        # Only delete non-critical, archived entries
        domain = [
            ("timestamp", "<", cutoff_date),
            ("state", "=", "archived"),
            ("risk_level", "in", ["low", "medium"])
        ]
        
        old_audits = self.search(domain)
        if old_audits:
            count = len(old_audits)
            old_audits.unlink()
            return count
        
        return 0

    @api.model
    def get_security_dashboard_data(self):
        """Get security monitoring dashboard data"""
        today = fields.Date.today()
        
        return {
            'total_audits_today': self.search_count([
                ('timestamp', '>=', today)
            ]),
            'high_risk_actions': self.search_count([
                ('risk_level', 'in', ['high', 'critical']),
                ('timestamp', '>=', today)
            ]),
            'failed_verifications': self.search_count([
                ('state', '=', 'draft'),
                ('timestamp', '>=', today)
            ]),
            'top_actions': self.read_group(
                [('timestamp', '>=', today)],
                ['action'],
                ['action']
            ),
            'compliance_rate': self._calculate_compliance_rate(),
        }

    def _calculate_compliance_rate(self):
        """Calculate overall compliance rate"""
        total_audits = self.search_count([])
        compliant_audits = self.search_count([('naid_compliant', '=', True)])
        
        if total_audits > 0:
            return round((compliant_audits / total_audits) * 100, 2)
        return 100.0
