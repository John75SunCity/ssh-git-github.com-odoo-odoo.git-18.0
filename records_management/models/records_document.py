# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class RecordsDocument(models.Model):
    _name = "records.document"
    _description = "Records Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Document Name", required=True, tracking=True, index=True)
    document_number = fields.Char(string="Document Number", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)

    # Framework Required Fields
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # State Management
    state = fields.Selection(
        [
            ("active", "Active"),
            ("archived", "Archived"),
            ("destroyed", "Destroyed"),
            ("pending", "Pending"),
        ],
        string="Document Status",
        default="active",
        tracking=True,
    )

    # ============================================================================
    # DOCUMENT CLASSIFICATION & METADATA
    # ============================================================================

    # Document Type & Classification
    document_type_id = fields.Many2one(
        "records.document.type", string="Document Type", required=True, tracking=True
    )
    category = fields.Selection(
        [
            ("financial", "Financial"),
            ("legal", "Legal"),
            ("medical", "Medical"),
            ("personal", "Personal"),
            ("business", "Business"),
            ("government", "Government"),
        ],
        string="Document Category",
        tracking=True,
    )
    classification = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        string="Classification Level",
        default="internal",
        tracking=True,
    )

    # Document Properties
    media_type = fields.Selection(
        [
            ("paper", "Paper"),
            ("digital", "Digital"),
            ("microfilm", "Microfilm"),
            ("mixed", "Mixed Media"),
        ],
        string="Media Type",
        default="paper",
        tracking=True,
    )
    file_format = fields.Char(string="File Format")
    file_size_mb = fields.Float(string="File Size (MB)", tracking=True)
    page_count = fields.Integer(string="Page Count")

    # ============================================================================
    # DATES & LIFECYCLE
    # ============================================================================

    # Core Dates
    document_date = fields.Date(string="Document Date", tracking=True)
    received_date = fields.Date(string="Received Date", tracking=True)
    scanned_date = fields.Date(string="Scanned Date", tracking=True)
    last_accessed = fields.Datetime(string="Last Accessed")

    # Retention & Destruction
    retention_policy_id = fields.Many2one(
        "records.retention.policy",
        string="Retention Policy",
        tracking=True,
        help="Applicable retention policy for this document",
    )
    retention_period = fields.Integer(
        string="Retention Period (Years)", default=7, tracking=True
    )
    destruction_date = fields.Date(string="Scheduled Destruction Date", tracking=True)
    actual_destruction_date = fields.Date(string="Actual Destruction Date")

    # Computed Dates
    retention_end_date = fields.Date(
        string="Retention End Date",
        compute="_compute_retention_end_date",
        store=True,
    )
    days_until_destruction = fields.Integer(
        string="Days Until Destruction",
        compute="_compute_days_until_destruction",
        store=True,
    )

    # ============================================================================
    # LOCATION & STORAGE
    # ============================================================================

    # Storage Location
    location_id = fields.Many2one(
        "records.location", string="Storage Location", tracking=True
    )
    container_id = fields.Many2one(
        "records.container", string="Container", tracking=True
    )
    shelf_position = fields.Char(string="Shelf Position")
    storage_location = fields.Char(
        string="Storage Description", help="Additional location information"
    )

    # Physical Properties
    weight_kg = fields.Float(string="Weight (kg)", digits=(8, 3))
    dimensions = fields.Char(string="Dimensions")
    condition = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
            ("damaged", "Damaged"),
        ],
        string="Physical Condition",
        default="good",
    )

    # ============================================================================
    # STAKEHOLDER RELATIONSHIPS
    # ============================================================================

    # Core Stakeholders
    partner_id = fields.Many2one("res.partner", string="Document Owner", tracking=True)
    author_id = fields.Many2one("res.partner", string="Document Author")
    custodian_id = fields.Many2one("res.users", string="Document Custodian")
    responsible_person = fields.Char(string="Responsible Person")

    # Department & Access
    department_id = fields.Many2one("records.department", string="Department")
    access_level = fields.Selection(
        [
            ("public", "Public Access"),
            ("department", "Department Only"),
            ("restricted", "Restricted Access"),
            ("confidential", "Confidential"),
        ],
        string="Access Level",
        default="department",
    )

    # ============================================================================
    # COMPLIANCE & AUDIT
    # ============================================================================

    # NAID Compliance
    naid_compliant = fields.Boolean(string="NAID Compliant", default=True)
    naid_destruction_verified = fields.Boolean(
        string="NAID Destruction Verified", default=False
    )
    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required", default=True
    )

    # Audit Trail
    audit_trail_required = fields.Boolean(string="Audit Trail Required", default=True)
    compliance_notes = fields.Text(string="Compliance Notes")
    last_audit_date = fields.Date(string="Last Audit Date")

    # Legal Hold
    legal_hold = fields.Boolean(string="Legal Hold", default=False, tracking=True)
    legal_hold_reason = fields.Text(string="Legal Hold Reason")
    legal_hold_date = fields.Date(string="Legal Hold Date")

    # ============================================================================
    # DIGITIZATION & SCANNING
    # ============================================================================

    # Digital Status
    digitized = fields.Boolean(
        string="Digitized",
        default=False,
        tracking=True,
        help="Indicates if document has been digitized",
    )
    scan_quality = fields.Selection(
        [
            ("draft", "Draft Quality"),
            ("standard", "Standard Quality"),
            ("high", "High Quality"),
            ("archive", "Archive Quality"),
        ],
        string="Scan Quality",
    )
    ocr_processed = fields.Boolean(string="OCR Processed", default=False)
    searchable_text = fields.Text(string="Searchable Text")

    # ============================================================================
    # WORKFLOW & STATUS FLAGS
    # ============================================================================

    # Workflow Flags
    permanent_flag = fields.Boolean(
        string="Permanent Record", default=False, tracking=True
    )
    urgent_retrieval = fields.Boolean(string="Urgent Retrieval", tracking=True)
    retrieval_priority = fields.Selection(
        [
            ("low", "Low Priority"),
            ("normal", "Normal Priority"),
            ("high", "High Priority"),
            ("urgent", "Urgent"),
        ],
        string="Retrieval Priority",
        default="normal",
    )

    # Processing Status
    processing_status = fields.Selection(
        [
            ("pending", "Pending Processing"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("on_hold", "On Hold"),
        ],
        string="Processing Status",
        default="pending",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Document Hierarchy
    parent_document_id = fields.Many2one("records.document", string="Parent Document")
    child_document_ids = fields.One2many(
        "records.document", "parent_document_id", string="Related Documents"
    )

    # Audit & Compliance
    chain_of_custody_ids = fields.One2many(
        "records.chain.of.custody", "document_id", string="Chain of Custody"
    )
    access_log_ids = fields.One2many(
        "records.access.log", "document_id", string="Access Log"
    )
    digital_scan_ids = fields.One2many(
        "records.digital.scan", "document_id", string="Digital Scans"
    )

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("document_date", "retention_period")
    def _compute_retention_end_date(self):
        """Compute when document retention period ends"""
        for record in self:
            if record.document_date and record.retention_period:
                record.retention_end_date = fields.Date.from_string(
                    str(record.document_date)
                ) + timedelta(days=record.retention_period * 365)
            else:
                record.retention_end_date = False

    @api.depends("retention_end_date")
    def _compute_days_until_destruction(self):
        """Compute days until destruction date"""
        today = fields.Date.today()
        for record in self:
            if record.retention_end_date:
                delta = record.retention_end_date - today
                record.days_until_destruction = delta.days
            else:
                record.days_until_destruction = 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_digitize_document(self):
        """Start document digitization process"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Digitize Document"),
            "res_model": "records.digital.scan",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_id": self.id,
                "default_name": f"Scan - {self.name}",
            },
        }

    def action_request_retrieval(self):
        """Request document retrieval"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Request Retrieval"),
            "res_model": "document.retrieval.work.order",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_id": self.id,
                "default_partner_id": self.partner_id.id,
            },
        }

    def action_schedule_destruction(self):
        """Schedule document for destruction"""
        self.ensure_one()
        if self.legal_hold:
            raise UserError(
                _("Cannot schedule destruction for documents on legal hold.")
            )

        if self.permanent_flag:
            raise UserError(_("Cannot schedule destruction for permanent records."))

        self.write(
            {
                "destruction_date": self.retention_end_date,
                "state": "pending",
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Destruction Scheduled"),
                "message": _("Document has been scheduled for destruction."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_chain_of_custody(self):
        """View chain of custody records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Chain of Custody"),
            "res_model": "records.chain.of.custody",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("document_id", "=", self.id)],
            "context": {
                "default_document_id": self.id,
            },
        }

    def action_view_access_log(self):
        """View document access log"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Access Log"),
            "res_model": "records.access.log",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("document_id", "=", self.id)],
            "context": {
                "default_document_id": self.id,
            },
        }

    def action_archive_document(self):
        """Archive the document"""
        self.ensure_one()
        self.write(
            {
                "state": "archived",
                "active": False,
            }
        )
        self.message_post(body=_("Document has been archived."))

    def action_restore_document(self):
        """Restore archived document"""
        self.ensure_one()
        self.write(
            {
                "state": "active",
                "active": True,
            }
        )
        self.message_post(body=_("Document has been restored from archive."))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("document_date", "destruction_date")
    def _check_date_validity(self):
        """Ensure dates are logical"""
        for record in self:
            if (
                record.document_date
                and record.destruction_date
                and record.document_date > record.destruction_date
            ):
                raise ValidationError(
                    _("Document date cannot be after destruction date.")
                )

    @api.constrains("retention_period")
    def _check_retention_period(self):
        """Ensure retention period is positive"""
        for record in self:
            if record.retention_period and record.retention_period < 0:
                raise ValidationError(_("Retention period must be positive."))

    @api.constrains("file_size_mb", "weight_kg")
    def _check_numeric_values(self):
        """Ensure numeric values are positive"""
        for record in self:
            if record.file_size_mb and record.file_size_mb < 0:
                raise ValidationError(_("File size must be positive."))
            if record.weight_kg and record.weight_kg < 0:
                raise ValidationError(_("Weight must be positive."))

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set defaults"""
        for vals in vals_list:
            if not vals.get("document_number"):
                vals["document_number"] = self.env["ir.sequence"].next_by_code(
                    "records.document"
                ) or _("New")

            # Set received date if not provided
            if not vals.get("received_date"):
                vals["received_date"] = fields.Date.today()

        return super().create(vals_list)

    def write(self, vals):
        """Override write to track important changes"""
        if "state" in vals:
            for record in self:
                record.message_post(
                    body=_("Document status changed from %s to %s")
                    % (
                        dict(record._fields["state"].selection).get(record.state),
                        dict(record._fields["state"].selection).get(vals["state"]),
                    )
                )
        return super().write(vals)

    def unlink(self):
        """Override unlink to prevent deletion of documents with chain of custody"""
        for record in self:
            if record.chain_of_custody_ids:
                raise UserError(
                    _("Cannot delete document '%s' as it has chain of custody records.")
                    % record.name
                )
        return super().unlink()
