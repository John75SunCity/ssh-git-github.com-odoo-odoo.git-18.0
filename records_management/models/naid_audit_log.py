# -*- coding: utf-8 -*-
"""
NAID Audit Log - Comprehensive audit tracking for NAID AAA compliance

NOTE: Per Odoo standards, this file should be renamed to 'naidaudit_log.py'
for the class name 'NAIDAuditLog'
"""

# ============================================================================
# IMPORTS - Proper Odoo import order: 1) Python stdlib, 2) Odoo core, 3) Odoo addons
# ============================================================================
import hashlib
import json

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class NAIDAuditLog(models.Model):
    """
    NAID Audit Log - Complete audit trail for all NAID compliance activities
    Tracks all document lifecycle events, access attempts, and compliance actions
    """

    _name = "naid.audit.log"
    _description = "NAID Audit Log"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "timestamp desc, id desc"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Audit Reference",
        required=True,
        tracking=True,
        index=True,
        default=lambda self: _("New Audit Log"),
    )
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="User Who Performed Action",
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)

    # ============================================================================
    # AUDIT EVENT DETAILS
    # ============================================================================
    event_type = fields.Selection(
        [
            # Document lifecycle events
            ("document_created", "Document Created"),
            ("document_accessed", "Document Accessed"),
            ("document_modified", "Document Modified"),
            ("document_moved", "Document Moved"),
            ("document_destroyed", "Document Destroyed"),
            # Container events
            ("container_created", "Container Created"),
            ("container_moved", "Container Moved"),
            ("container_accessed", "Container Accessed"),
            ("container_sealed", "Container Sealed"),
            ("container_destroyed", "Container Destroyed"),
            # Compliance events
            ("compliance_check", "Compliance Check"),
            ("audit_review", "Audit Review"),
            ("policy_violation", "Policy Violation"),
            ("access_denied", "Access Denied"),
            # Service events
            ("pickup_requested", "Pickup Requested"),
            ("pickup_completed", "Pickup Completed"),
            ("shredding_service", "Shredding Service"),
            ("destruction_certificate", "Destruction Certificate Issued"),
            # Security events
            ("key_issued", "Key Issued"),
            ("key_returned", "Key Returned"),
            ("unlock_service", "Unlock Service"),
            ("security_breach", "Security Breach"),
            # System events
            ("system_backup", "System Backup"),
            ("data_export", "Data Export"),
            ("configuration_change", "Configuration Change"),
            ("user_login", "User Login"),
            ("user_logout", "User Logout"),
        ],
        string="Event Type",
        required=True,
        tracking=True,
        index=True,
    )

    timestamp = fields.Datetime(
        string="Event Timestamp",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        index=True,
    )

    severity = fields.Selection(
        [
            ("info", "Information"),
            ("warning", "Warning"),
            ("error", "Error"),
            ("critical", "Critical"),
        ],
        string="Severity Level",
        default="info",
        required=True,
        tracking=True,
    )

    # ============================================================================
    # RELATIONSHIP FIELDS (with existing models)
    # ============================================================================
    # Core Records Management relationships
    container_id = fields.Many2one(
        "records.container",
        string="Related Container",
        ondelete="set null",
        index=True,
    )
    document_id = fields.Many2one(
        "records.document",
        string="Related Document",
        ondelete="set null",
        index=True,
    )
    location_id = fields.Many2one(
        "records.location", string="Related Location", ondelete="set null"
    )

    # Compliance and service relationships
    compliance_id = fields.Many2one(
        "naid.compliance", string="NAID Compliance Record", ondelete="cascade"
    )
    pickup_request_id = fields.Many2one(
        "pickup.request", string="Related Pickup Request", ondelete="set null"
    )
    shredding_service_id = fields.Many2one(
        "shredding.service",
        string="Related Shredding Service",
        ondelete="set null",
    )
    
    # Task relationships
    task_id = fields.Many2one(
        "project.task", 
        string="Related Task", 
        ondelete="set null",
        help="Project task associated with this audit event"
    )

    # Portal and customer relationships
    portal_request_id = fields.Many2one(
        "portal.request", string="Related Portal Request", ondelete="set null"
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Related Customer",
        ondelete="set null",
        index=True,
    )

    # Security relationships
    bin_key_id = fields.Many2one(
        "bin.key", string="Related Bin Key", ondelete="set null"
    )
    unlock_service_id = fields.Many2one(
        "bin.key.unlock.service",
        string="Related Unlock Service",
        ondelete="set null",
    )

    # ============================================================================
    # AUDIT DATA FIELDS
    # ============================================================================
    description = fields.Text(
        string="Event Description",
        required=True,
        help="Detailed description of the audit event",
    )

    before_values = fields.Text(
        string="Before Values (JSON)",
        help="JSON representation of field values before the change",
    )

    after_values = fields.Text(
        string="After Values (JSON)",
        help="JSON representation of field values after the change",
    )

    metadata = fields.Text(
        string="Additional Metadata (JSON)",
        help="Additional context data in JSON format",
    )

    ip_address = fields.Char(
        string="IP Address",
        help="IP address from which the action was performed",
    )

    user_agent = fields.Char(
        string="User Agent", help="Browser/client information"
    )

    session_id = fields.Char(
        string="Session ID", help="User session identifier"
    )

    # ============================================================================
    # NAID COMPLIANCE FIELDS
    # ============================================================================
    chain_of_custody_verified = fields.Boolean(
        string="Chain of Custody Verified",
        default=False,
        tracking=True,
        help="Indicates if chain of custody is properly maintained",
    )

    compliance_status = fields.Selection(
        [
            ("compliant", "Compliant"),
            ("non_compliant", "Non-Compliant"),
            ("under_review", "Under Review"),
            ("remediated", "Remediated"),
        ],
        string="Compliance Status",
        default="compliant",
        tracking=True,
    )

    audit_hash = fields.Char(
        string="Audit Hash",
        help="Cryptographic hash for tamper detection",
        readonly=True,
    )

    previous_log_hash = fields.Char(
        string="Previous Log Hash",
        help="Hash of the previous audit log entry for chain verification",
        readonly=True,
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("validated", "Validated"),
            ("archived", "Archived"),
            ("flagged", "Flagged for Review"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        required=True,
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("event_type", "timestamp", "user_id")
    def _compute_display_name(self):
        """Compute user-friendly display name"""
        for record in self:
            if record.event_type and record.timestamp:
                event_label = dict(record._fields["event_type"].selection).get(
                    record.event_type, record.event_type
                )
                timestamp_str = (
                    record.timestamp.strftime("%Y-%m-%d %H:%M")
                    if record.timestamp
                    else "Unknown"
                )
                user_name = (
                    record.user_id.name if record.user_id else "Unknown"
                )
                record.display_name = (
                    f"{event_label} - {timestamp_str} ({user_name})"
                )
            else:
                record.display_name = record.name or "Audit Log Entry"

    event_level = fields.Selection([("info", "Info"), ("warning", "Warning"), ("error", "Error"), ("critical", "Critical")], string="Event Level")
    res_id = fields.Integer(string="Related Record ID")
    chain_of_custody_id = fields.Many2one("records.chain.of.custody", string="Chain of Custody")
    naid_compliance_id = fields.Many2one("naid.compliance", string="NAID Compliance Record")
    event_date = fields.Datetime(string="Event Date", default=lambda self: fields.Datetime.now())
    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("timestamp")
    def _check_timestamp(self):
        """Ensure timestamp is not in the future"""
        for record in self:
            if record.timestamp and record.timestamp > fields.Datetime.now():
                raise ValidationError(
                    _("Audit timestamp cannot be in the future")
                )

    @api.constrains("before_values", "after_values", "metadata")
    def _check_json_fields(self):
        """Validate JSON format in text fields"""
        for record in self:
            for field_name in ["before_values", "after_values", "metadata"]:
                field_value = getattr(record, field_name)
                if field_value:
                    try:
                        json.loads(field_value)
                    except json.JSONDecodeError as exc:
                        raise ValidationError(
                            _(
                                "Invalid JSON format in field '%s'",
                                record._fields[field_name].string,
                            )
                        ) from exc

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_validate(self):
        """Validate audit log entry"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft audit logs can be validated"))

        # Generate audit hash for tamper detection
        self._generate_audit_hash()

        self.write(
            {"state": "validated", "name": self._generate_audit_reference()}
        )

        # Create activity for critical events
        if self.severity in ["error", "critical"]:
            self.activity_schedule(
                "records_management.mail_activity_audit_review",
                summary=_("Critical audit event requires review"),
                note=self.description,
                user_id=self.env.ref("base.user_admin").id,
            )

    def action_flag_for_review(self):
        """Flag audit log for manual review"""
        self.ensure_one()
        self.write({"state": "flagged"})

        # Notify compliance officers
        compliance_users = self.env.ref(
            "records_management.group_records_manager"
        ).users
        for user in compliance_users:
            self.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Audit log flagged for review"),
                note=self.description,
                user_id=user.id,
            )

    def action_archive(self):
        """Archive audit log"""
        self.ensure_one()
        if self.state not in ["validated", "flagged"]:
            raise UserError(
                _("Only validated or flagged audit logs can be archived")
            )

        self.write({"state": "archived"})

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model
    def create_audit_log(self, event_type, description, **kwargs):
        """Utility method to create audit log entries from other models"""
        vals = {
            "event_type": event_type,
            "description": description,
            "timestamp": fields.Datetime.now(),
            "user_id": self.env.user.id,
            "company_id": self.env.company.id,
        }

        # Add any additional fields from kwargs
        for key, value in kwargs.items():
            if key in self._fields:
                vals[key] = value

        # Auto-generate name
        vals["name"] = self._generate_audit_reference(event_type)

        audit_log = self.create(vals)

        # Auto-validate non-critical events
        if audit_log.severity in ["info", "warning"]:
            audit_log.action_validate()

        return audit_log

    def _generate_audit_reference(self, event_type=None):
        """Generate unique audit reference"""
        event_type = event_type or self.event_type or "general"
        timestamp = fields.Datetime.now().strftime("%Y%m%d%H%M%S")
        sequence = (
            self.env["ir.sequence"].next_by_code("naid.audit.log") or "001"
        )
        return f"AUDIT-{event_type.upper()}-{timestamp}-{sequence}"

    def _generate_audit_hash(self):
        """Generate cryptographic hash for tamper detection"""
        # Get previous log hash for chaining
        previous_log = self.search(
            [("id", "<", self.id), ("company_id", "=", self.company_id.id)],
            order="id desc",
            limit=1,
        )

        previous_hash = previous_log.audit_hash if previous_log else "GENESIS"

        # Create hash input string
        hash_input = f"{self.timestamp}{self.event_type}{self.user_id.id}{self.description}{previous_hash}"

        # Generate SHA-256 hash
        audit_hash = hashlib.sha256(hash_input.encode()).hexdigest()

        self.write(
            {"audit_hash": audit_hash, "previous_log_hash": previous_hash}
        )

    @api.model
    def verify_audit_chain(self):
        """Verify the integrity of the audit log chain"""
        logs = self.search(
            [
                ("company_id", "=", self.env.company.id),
                ("state", "=", "validated"),
            ],
            order="id",
        )

        errors = []
        for i, log in enumerate(logs):
            if i == 0:
                # First log should have GENESIS as previous hash
                if log.previous_log_hash != "GENESIS":
                    errors.append(_("Log %s: Invalid genesis hash", log.id))
            else:
                # Subsequent logs should reference the previous log's hash
                previous_log = logs[i - 1]
                if log.previous_log_hash != previous_log.audit_hash:
                    errors.append(_("Log %s: Broken chain link", log.id))

        return errors

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS (REQUIRED)
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities"
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    filter_this_week = fields.Char(string='Filter This Week')
    filter_today = fields.Char(string='Filter Today')
    group_by_date = fields.Date(string='Group By Date')
    group_by_event_type = fields.Selection([], string='Group By Event Type')  # TODO: Define selection options
    group_by_level = fields.Char(string='Group By Level')
    group_by_model = fields.Char(string='Group By Model')
    group_by_user = fields.Char(string='Group By User')
    help = fields.Char(string='Help')
    level_critical = fields.Char(string='Level Critical')
    level_info = fields.Char(string='Level Info')
    level_warning = fields.Char(string='Level Warning')
    res_model = fields.Char(string='Res Model')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')
