# -*- coding: utf-8 -*-
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsDocument(models.Model):
    _name = "records.document"
    _description = "Records Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Document Name", required=True, tracking=True, index=True)
    document_number = fields.Char(string="Document Number", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Document Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("active", "Active"),
            ("archived", "Archived"),
            ("destroyed", "Destroyed"),
            ("pending", "Pending"),
            ("pending_destruction", "Pending Destruction"),
        ],
        string="Document Status",
        default="active",
        tracking=True,
    )

    # ============================================================================
    # DOCUMENT CLASSIFICATION & METADATA
    # ============================================================================
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

    # ============================================================================
    # DOCUMENT PROPERTIES
    # ============================================================================
    file_format = fields.Char(string="File Format")
    file_size_mb = fields.Float(string="File Size (MB)", tracking=True)
    page_count = fields.Integer(string="Page Count")
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
    # DATES & LIFECYCLE
    # ============================================================================
    document_date = fields.Date(string="Document Date", tracking=True)
    received_date = fields.Date(string="Received Date", tracking=True)
    scanned_date = fields.Date(string="Scanned Date", tracking=True)
    last_accessed = fields.Datetime(string="Last Accessed")

    # ============================================================================
    # RETENTION & DESTRUCTION
    # ============================================================================
    retention_policy_id = fields.Many2one(
        "records.retention.policy", string="Retention Policy", tracking=True
    )
    retention_period = fields.Integer(
        string="Retention Period (Years)", help="Retention period in years"
    )
    destruction_date = fields.Date(string="Scheduled Destruction Date", tracking=True)
    actual_destruction_date = fields.Date(string="Actual Destruction Date")
    retention_end_date = fields.Date(
        string="Retention End Date", compute="_compute_retention_end_date", store=True
    )
    days_until_destruction = fields.Integer(
        string="Days Until Destruction", compute="_compute_days_until_destruction"
    )

    # ============================================================================
    # LOCATION & STORAGE
    # ============================================================================
    location_id = fields.Many2one(
        "records.location", string="Storage Location", tracking=True
    )
    container_id = fields.Many2one(
        "records.container", string="Container", tracking=True
    )
    shelf_position = fields.Char(string="Shelf Position")
    storage_location = fields.Char(
        string="Storage Location Details",
        compute="_compute_storage_location",
        store=True,
    )

    # ============================================================================
    # OWNERSHIP & ACCESS
    # ============================================================================
    partner_id = fields.Many2one("res.partner", string="Document Owner", tracking=True)
    author_id = fields.Many2one("res.partner", string="Document Author")
    custodian_id = fields.Many2one("res.users", string="Document Custodian")
    responsible_person = fields.Char(string="Responsible Person")
    department_id = fields.Many2one("records.department", string="Department")
    access_level = fields.Selection(
        [
            ("public", "Public Access"),
            ("restricted", "Restricted Access"),
            ("confidential", "Confidential"),
            ("classified", "Classified"),
        ],
        string="Access Level",
        default="restricted",
    )

    # ============================================================================
    # COMPLIANCE & AUDIT
    # ============================================================================
    naid_compliant = fields.Boolean(string="NAID Compliant", default=True)
    naid_destruction_verified = fields.Boolean(
        string="NAID Destruction Verified", default=False
    )
    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required", default=True
    )
    audit_trail_required = fields.Boolean(string="Audit Trail Required", default=True)
    compliance_notes = fields.Text(string="Compliance Notes")
    last_audit_date = fields.Date(string="Last Audit Date")

    # ============================================================================
    # LEGAL HOLD
    # ============================================================================
    legal_hold = fields.Boolean(string="Legal Hold", default=False, tracking=True)
    legal_hold_reason = fields.Text(string="Legal Hold Reason")
    legal_hold_date = fields.Date(string="Legal Hold Date")

    # ============================================================================
    # DIGITIZATION & TECHNOLOGY
    # ============================================================================
    digitized = fields.Boolean(
        string="Digitized", default=False, help="Document has been digitally scanned"
    )
    scan_quality = fields.Selection(
        [
            ("draft", "Draft Quality"),
            ("standard", "Standard Quality"),
            ("high", "High Quality"),
            ("archival", "Archival Quality"),
        ],
        string="Scan Quality",
        default="standard",
    )
    ocr_processed = fields.Boolean(string="OCR Processed", default=False)
    searchable_text = fields.Text(string="Searchable Text")

    # ============================================================================
    # WORKFLOW & STATUS FLAGS
    # ============================================================================
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
    parent_document_id = fields.Many2one("records.document", string="Parent Document")
    child_document_ids = fields.One2many(
        "records.document", "parent_document_id", string="Related Documents"
    )
    chain_of_custody_ids = fields.One2many(
        "records.chain.of.custody", "document_id", string="Chain of Custody"
    )
    access_log_ids = fields.One2many(
        "records.access.log", "document_id", string="Access Log"
    )
    digital_scan_ids = fields.One2many(
        "records.digital.scan", "document_id", string="Digital Scans"
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many(
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=[('res_model', '=', 'records.document')],
    )
        domain=[("res_model", "=", "records.document")],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=[("model", "=", "records.document")],
    )
        "mail.followers", "res_id", string="Followers"
    )

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
                ) + relativedelta(years=record.retention_period)
    @api.depends("retention_end_date")
    def _compute_days_until_destruction(self):
        """Compute days remaining until scheduled destruction"""
        from datetime import datetime

        for record in self:
            if record.retention_end_date:
                today = fields.Date.today()
                # Convert to date objects if necessary
                end_date = record.retention_end_date
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                if isinstance(today, str):
                    today = datetime.strptime(today, "%Y-%m-%d").date()
                delta = end_date - today
                record.days_until_destruction = delta.days
            else:
                record.days_until_destruction = 0
                record.days_until_destruction = 0

    @api.depends(
        "location_id",
        "location_id.name",
        "container_id",
        "container_id.name",
        "shelf_position",
    )
    def _compute_storage_location(self):
        """Compute full storage location details"""
        for record in self:
            location_parts = []
            if record.location_id and record.location_id.name:
                location_parts.append(record.location_id.name)
            if record.container_id and record.container_id.name:
                location_parts.append(f"Container: {record.container_id.name}")
            if record.shelf_position:
                location_parts.append(f"Shelf: {record.shelf_position}")
            record.storage_location = (
                " / ".join(location_parts) if location_parts else ""
            )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_digitize_document(self):
        """Initiate document digitization process"""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active documents can be digitized"))

        self.write(
            {
                "digitized": True,
                "scanned_date": fields.Date.today(),
                "processing_status": "in_progress",
            }
        )
        self.message_post(body=_("Document digitization initiated"))

    def action_request_retrieval(self):
        """Create document retrieval request"""
        self.ensure_one()
        retrieval_wizard = self.env["document.retrieval.wizard"].create(
            {
                "document_id": self.id,
                "urgency": self.retrieval_priority,
                "requester_id": self.env.user.id,
            }
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": "document.retrieval.wizard",
            "res_id": retrieval_wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_schedule_destruction(self):
        """Schedule document for destruction"""
        self.ensure_one()
        if self.legal_hold:
            raise UserError(
                _("Documents under legal hold cannot be scheduled for destruction")
            )

        if not self.destruction_date:
            if self.retention_end_date:
                self.destruction_date = self.retention_end_date
            else:
                raise UserError(
                    _("Cannot schedule destruction without retention end date")
                )

        self.write({"state": "pending_destruction"})
        self.message_post(
            body=_("Document scheduled for destruction on %s") % self.destruction_date
        )

    def action_view_chain_of_custody(self):
        """View document chain of custody"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Chain of Custody"),
            "res_model": "records.chain.of.custody",
            "view_mode": "tree,form",
            "domain": [("document_id", "=", self.id)],
            "context": {"default_document_id": self.id},
        }

    def action_view_access_log(self):
        """View document access history"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Access Log"),
            "res_model": "records.access.log",
            "view_mode": "tree,form",
            "domain": [("document_id", "=", self.id)],
            "context": {"default_document_id": self.id},
        }

    def action_archive_document(self):
        """Archive the document"""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active documents can be archived"))

        self.write({"state": "archived"})
        self.message_post(body=_("Document has been archived"))

    def action_restore_document(self):
        """Restore archived document to active state"""
        self.ensure_one()
        if self.state != "archived":
            raise UserError(_("Only archived documents can be restored"))

        self.write({"state": "active"})
        self.message_post(body=_("Document has been restored to active status"))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("document_date", "destruction_date")
    def _check_date_validity(self):
        """Ensure destruction date is after document date"""
        for record in self:
            if record.document_date and record.destruction_date:
                if record.destruction_date <= record.document_date:
                    raise ValidationError(
                        _("Destruction date must be after document date")
                    )

    @api.constrains("retention_period")
    def _check_retention_period(self):
        """Validate retention period is positive"""
        for record in self:
            if record.retention_period and record.retention_period <= 0:
                raise ValidationError(_("Retention period must be positive"))

    @api.constrains("file_size_mb", "weight_kg")
    def _check_numeric_values(self):
        """Validate numeric values are non-negative"""
        for record in self:
            if record.file_size_mb and record.file_size_mb < 0:
                raise ValidationError(_("File size cannot be negative"))
            if record.weight_kg and record.weight_kg < 0:
                raise ValidationError(_("Weight cannot be negative"))
    @api.model_create_multi
    def create(self, vals_list):
        """Enhanced create with automatic numbering"""
        for vals in vals_list:
            if not vals.get("document_number"):
                vals["document_number"] = (
                    self.env["ir.sequence"].next_by_code("records.document") or "NEW"
                )
        return super(RecordsDocument, self).create(vals_list)
            if not vals.get("document_number"):
                vals["document_number"] = (
                    self.env["ir.sequence"].next_by_code("records.document") or "NEW"
                )
        return super().create(vals_list)

    def write(self, vals):
        """Enhanced write with audit logging"""
        if "state" in vals:
            for record in self:
                if record.audit_trail_required:
                    record.message_post(
                        body=_("Document state changed from %s to %s")
                        % (record.state, vals["state"])
                    )
        return super(RecordsDocument, self).write(vals)

    def unlink(self):
        """Enhanced unlink with compliance check"""
        for record in self:
            if record.naid_compliant and not record.naid_destruction_verified:
                raise UserError(
                    _("NAID compliant documents require verified destruction process")
                )
        return super(RecordsDocument, self).unlink()

    # ============================================================================
    # AUTO-GENERATED FIELDS (Batch 2)
    # ============================================================================
    # ============================================================================
    # AUTO-GENERATED ACTION METHODS (Batch 2)
    # ============================================================================
    def action_audit_trail(self):
        """Audit Trail - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Audit Trail"),
            "res_model": "records.document",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_download(self):
        """Download - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Download"),
            "res_model": "records.document",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_mark_permanent(self):
        """Mark Permanent - Update field"""
        self.ensure_one()
        self.write({"permanent_flag": True})
        self.message_post(body=_("Mark Permanent"))
        return True

    def action_scan_document(self):
        """Scan Document - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Scan Document"),
            "res_model": "records.document",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_type(self):
        """Type - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Type"),
            "res_model": "records.document",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_unmark_permanent(self):
        """Unmark Permanent - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Unmark Permanent"),
            "res_model": "records.document",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
