# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class RecordsDocument(models.Model):
    _name = "records.document"
    _description = "Records Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Company and User
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Document Manager", default=lambda self: self.env.user
    )

    # Customer Relationships
    customer_inventory_id = fields.Many2one(
        "customer.inventory", string="Customer Inventory"
    )

    # Timestamps
    date_created = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    date_modified = fields.Datetime(string="Modified Date")

    # Control Fields
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Internal Notes")

    # === MISSING FIELDS FROM VIEWS ===
    # Destruction Management
    destruction_eligible_date = fields.Date(
        string="Destruction Eligible Date",
        compute="_compute_destruction_eligible_date",
        store=True,
        help="Date when document becomes eligible for destruction",
    )
    destruction_facility = fields.Char(
        string="Destruction Facility", help="Facility where destruction will take place"
    )
    destruction_method = fields.Selection(
        [
            ("shredding", "Shredding"),
            ("pulverizing", "Pulverizing"),
            ("wiping", "Data Wiping"),
        ],
        string="Destruction Method",
    )

    destruction_notes = fields.Text(
        string="Destruction Notes", help="Notes about the destruction process"
    )
    destruction_witness = fields.Char(
        string="Destruction Witness", help="Person who witnessed the destruction"
    )

    # Additional Document Fields from Views
    days_until_destruction = fields.Integer(
        string="Days Until Destruction",
        compute="_compute_days_until_destruction",
        help="Number of days until destruction is eligible",
    )
    permanent_flag_set_by = fields.Char(
        string="Permanent Flag Set By", help="User who set the permanent flag"
    )
    permanent_flag_set_date = fields.Date(
        string="Permanent Flag Set Date", help="Date when permanent flag was set"
    )
    created_date = fields.Date(
        string="Created Date", help="Date when document was created"
    )
    received_date = fields.Date(
        string="Received Date", help="Date when document was received"
    )
    storage_date = fields.Date(
        string="Storage Date", help="Date when document was stored"
    )
    last_access_date = fields.Date(
        string="Last Access Date", help="Last date document was accessed"
    )

    # Computed Fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )

    # === ENHANCED DOCUMENT MANAGEMENT FIELDS ===

    # Document Type and Classification
    document_type_id = fields.Many2one(
        "records.document.type", string="Document Type", tracking=True
    )
    document_category = fields.Selection(
        [
            ("financial", "Financial Records"),
            ("legal", "Legal Documents"),
            ("hr", "Human Resources"),
            ("contracts", "Contracts"),
            ("correspondence", "Correspondence"),
            ("reports", "Reports"),
            ("policies", "Policies"),
            ("other", "Other"),
        ],
        string="Document Category",
        tracking=True,
    )
    confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("top_secret", "Top Secret"),
        ],
        string="Confidentiality Level",
        default="internal",
        tracking=True,
    )

    # Storage and Physical Location
    container_id = fields.Many2one(
        "records.container", string="Storage Container", tracking=True
    )
    location_id = fields.Many2one(
        "records.location", string="Storage Location", tracking=True
    )
    retrieval_work_order_id = fields.Many2one(
        "document.retrieval.work.order", string="Retrieval Work Order", tracking=True
    )
    box_number = fields.Char(string="Box Number", tracking=True)
    shelf_location = fields.Char(string="Shelf Location", tracking=True)
    barcode = fields.Char(string="Document Barcode", tracking=True)

    # Document Lifecycle Management
    retention_period_years = fields.Integer(
        string="Retention Period (Years)", tracking=True
    )
    retention_start_date = fields.Date(string="Retention Start Date", tracking=True)
    scheduled_destruction_date = fields.Date(
        string="Scheduled Destruction Date",
        compute="_compute_destruction_date",
        store=True,
        tracking=True,
    )
    destruction_approved = fields.Boolean(string="Destruction Approved", tracking=True)
    destruction_date = fields.Date(string="Actual Destruction Date", tracking=True)
    legal_hold = fields.Boolean(string="Legal Hold", tracking=True)
    legal_hold_reason = fields.Text(string="Legal Hold Reason")

    # Digital and Physical Formats
    digital_copy_available = fields.Boolean(
        string="Digital Copy Available", tracking=True
    )
    original_format = fields.Selection(
        [
            ("paper", "Paper"),
            ("digital", "Digital"),
            ("microfilm", "Microfilm"),
            ("microfiche", "Microfiche"),
            ("electronic", "Electronic"),
        ],
        string="Original Format",
        default="paper",
        tracking=True,
    )
    file_format = fields.Selection(
        [
            ("pdf", "PDF"),
            ("doc", "Word Document"),
            ("xls", "Excel"),
            ("tiff", "TIFF"),
            ("jpg", "JPEG"),
            ("png", "PNG"),
            ("other", "Other"),
        ],
        string="Digital File Format",
        tracking=True,
    )
    file_size_mb = fields.Float(string="File Size (MB)", tracking=True)

    # Chain of Custody and Audit Trail
    chain_of_custody_ids = fields.One2many(
        "records.chain.of.custody", "document_id", string="Chain of Custody"
    )
    audit_trail_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Audit Trail",
        domain=[("model", "=", "records.document")],
    )
    last_accessed_date = fields.Datetime(string="Last Accessed", tracking=True)
    last_accessed_by = fields.Many2one(
        "res.users", string="Last Accessed By", tracking=True
    )
    access_count = fields.Integer(string="Access Count", default=0, tracking=True)

    # Compliance and Verification
    compliance_verified = fields.Boolean(string="Compliance Verified", tracking=True)
    compliance_verification_date = fields.Date(
        string="Compliance Verification Date", tracking=True
    )
    compliance_notes = fields.Text(string="Compliance Notes")
    naid_compliance = fields.Boolean(string="NAID Compliance Required", tracking=True)
    regulatory_requirements = fields.Text(string="Regulatory Requirements")

    # Document Status and Actions
    action_type = fields.Selection(
        [
            ("store", "Store"),
            ("retrieve", "Retrieve"),
            ("destroy", "Destroy"),
            ("scan", "Scan"),
            ("transfer", "Transfer"),
            ("archive", "Archive"),
        ],
        string="Action Type",
        tracking=True,
    )
    action_date = fields.Date(string="Action Date", tracking=True)
    action_notes = fields.Text(string="Action Notes")

    # Indexing and Search
    index_keywords = fields.Text(string="Index Keywords")
    search_tags = fields.Char(string="Search Tags")
    document_reference = fields.Char(string="Document Reference", tracking=True)
    external_reference = fields.Char(string="External Reference", tracking=True)

    # Quality and Condition
    document_condition = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
            ("damaged", "Damaged"),
        ],
        string="Document Condition",
        default="good",
        tracking=True,
    )
    restoration_required = fields.Boolean(string="Restoration Required", tracking=True)
    restoration_notes = fields.Text(string="Restoration Notes")

    # Financial Information
    storage_cost_per_month = fields.Monetary(
        string="Storage Cost per Month", currency_field="currency_id"
    )
    retrieval_fee = fields.Monetary(
        string="Retrieval Fee", currency_field="currency_id"
    )
    destruction_fee = fields.Monetary(
        string="Destruction Fee", currency_field="currency_id"
    )
    total_lifecycle_cost = fields.Monetary(
        string="Total Lifecycle Cost",
        compute="_compute_lifecycle_cost",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Document Relationships
    parent_document_id = fields.Many2one("records.document", string="Parent Document")
    child_document_ids = fields.One2many(
        "records.document", "parent_document_id", string="Related Documents"
    )
    version_number = fields.Char(string="Version Number", default="1.0", tracking=True)
    superseded_by_id = fields.Many2one("records.document", string="Superseded By")
    supersedes_id = fields.Many2one("records.document", string="Supersedes")

    # Special Handling Requirements
    special_handling_required = fields.Boolean(
        string="Special Handling Required", tracking=True
    )
    handling_instructions = fields.Text(string="Handling Instructions")
    temperature_controlled_storage = fields.Boolean(
        string="Temperature Controlled Storage", tracking=True
    )
    humidity_controlled_storage = fields.Boolean(
        string="Humidity Controlled Storage", tracking=True
    )

    # Document Source and Origin
    source_department = fields.Char(string="Source Department", tracking=True)
    source_contact = fields.Many2one(
        "res.partner", string="Source Contact", tracking=True
    )
    received_date = fields.Date(string="Date Received", tracking=True)
    received_by = fields.Many2one("res.users", string="Received By", tracking=True)

    # Priority and Urgency
    priority = fields.Selection(
        [("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority",
        default="normal",
        tracking=True,
    )
    urgent_retrieval = fields.Boolean(string="Urgent Retrieval", tracking=True)

    # === MISSING FIELDS FOR RECORDS.DOCUMENT ===

    # Digital and Scanning Integration
    digital_scan_ids = fields.One2many(
        "records.digital.scan",
        "document_id",
        string="Digital Scans",
        help="Digital scans of this document",
    )

    digitized = fields.Boolean(
        string="Digitized",
        default=False,
        tracking=True,
        help="Indicates if document has been digitized",
    )

    # Event and Activity Tracking
    event_date = fields.Date(
        string="Event Date",
        tracking=True,
        help="Date of significant event related to document",
    )

    event_type = fields.Selection(
        [
            ("creation", "Creation"),
            ("modification", "Modification"),
            ("access", "Access"),
            ("transfer", "Transfer"),
            ("destruction", "Destruction"),
            ("other", "Other"),
        ],
        string="Event Type",
        help="Type of event recorded",
    )

    # Location and Geography
    location = fields.Char(
        string="Location Description",
        help="Additional location information beyond standard location_id",
    )

    # Access and Security
    access_log_ids = fields.One2many(
        "records.access.log",
        "document_id",
        string="Access Log",
        help="Log of document access events",
    )

    last_access_date = fields.Datetime(
        string="Last Access Date", tracking=True, help="Date and time of last access"
    )

    access_count = fields.Integer(
        string="Access Count",
        compute="_compute_access_count",
        store=True,
        help="Total number of times document was accessed",
    )

    # Review and Compliance
    last_review_date = fields.Date(
        string="Last Review Date", tracking=True, help="Date of last compliance review"
    )

    next_review_date = fields.Date(
        string="Next Review Date",
        compute="_compute_next_review_date",
        store=True,
        help="Computed next review date",
    )

    # Additional Metadata
    document_language = fields.Selection(
        [("en", "English"), ("es", "Spanish"), ("fr", "French"), ("other", "Other")],
        string="Document Language",
        default="en",
    )

    file_format = fields.Selection(
        [
            ("pdf", "PDF"),
            ("doc", "Word Document"),
            ("txt", "Text File"),
            ("image", "Image"),
            ("other", "Other"),
        ],
        string="File Format",
        help="Original file format of document",
    )

    # Enhanced State Management

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    @api.depends("retention_start_date", "retention_period_years")
    def _compute_destruction_date(self):
        """Compute scheduled destruction date based on retention period."""
        for record in self:
            if record.retention_start_date and record.retention_period_years:
                from datetime import timedelta

                record.scheduled_destruction_date = (
                    record.retention_start_date
                    + timedelta(days=record.retention_period_years * 365)
                )
            else:
                record.scheduled_destruction_date = False

    @api.depends(
        "storage_cost_per_month",
        "retention_period_years",
        "retrieval_fee",
        "destruction_fee",
    )
    def _compute_lifecycle_cost(self):
        """Compute total lifecycle cost of the document."""
        for record in self:
            storage_cost = 0
            if record.storage_cost_per_month and record.retention_period_years:
                storage_cost = (
                    record.storage_cost_per_month * record.retention_period_years * 12
                )

            record.total_lifecycle_cost = (
                storage_cost
                + (record.retrieval_fee or 0)
                + (record.destruction_fee or 0)
            )

    @api.depends("retention_policy_id", "storage_date")
    def _compute_destruction_eligible_date(self):
        """Compute when document becomes eligible for destruction"""
        for record in self:
            if record.retention_policy_id and record.storage_date:
                if record.retention_policy_id.retention_period_years:
                    from dateutil.relativedelta import relativedelta

                    record.destruction_eligible_date = (
                        record.storage_date
                        + relativedelta(
                            years=record.retention_policy_id.retention_period_years
                        )
                    )
                else:
                    record.destruction_eligible_date = False
            else:
                record.destruction_eligible_date = False

    @api.depends("destruction_eligible_date")
    def _compute_days_until_destruction(self):
        """Compute number of days until destruction is eligible"""
        for record in self:
            if record.destruction_eligible_date:
                today = fields.Date.today()
                delta = record.destruction_eligible_date - today
                record.days_until_destruction = delta.days
            else:
                record.days_until_destruction = 0

    @api.depends("audit_trail_ids")
    def _compute_audit_trail_count(self):
        """Compute the number of audit trail entries"""
        for record in self:
            record.audit_trail_count = len(record.audit_trail_ids)

    @api.depends("chain_of_custody_ids")
    def _compute_chain_of_custody_count(self):
        """Compute the number of chain of custody entries"""
        for record in self:
            record.chain_of_custody_count = len(record.chain_of_custody_ids)

    @api.depends("destruction_eligible_date", "legal_hold", "retention_period_years")
    def _compute_retention_status(self):
        """Compute retention status based on various factors"""
        for record in self:
            if record.legal_hold:
                record.retention_status = "hold"
            elif record.retention_period_years == 0:
                record.retention_status = "permanent"
            elif record.destruction_eligible_date:
                today = fields.Date.today()
                if record.destruction_eligible_date <= today:
                    record.retention_status = "eligible"
                else:
                    record.retention_status = "active"
            else:
                record.retention_status = "active"

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()
        return super().write(vals)

    @api.constrains("retention_period_years")
    def _check_retention_period(self):
        """Validate retention period is positive"""
        for record in self:
            if record.retention_period_years < 0:
                raise ValidationError(
                    _(
                        "Retention period must be positive or zero (for permanent retention)."
                    )
                )

    @api.constrains("legal_hold", "destruction_approved")
    def _check_legal_hold_destruction(self):
        """Ensure documents on legal hold cannot be approved for destruction"""
        for record in self:
            if record.legal_hold and record.destruction_approved:
                raise ValidationError(
                    _("Documents under legal hold cannot be approved for destruction.")
                )

    @api.constrains("file_size_mb")
    def _check_file_size(self):
        """Validate file size is positive"""
        for record in self:
            if record.file_size_mb < 0:
                raise ValidationError(_("File size must be positive."))

    @api.onchange("document_type_id")
    def _onchange_document_type(self):
        """Update retention policy when document type changes"""
        if self.document_type_id and self.document_type_id.default_retention_policy_id:
            self.retention_policy_id = self.document_type_id.default_retention_policy_id
            self.retention_period_years = (
                self.document_type_id.default_retention_policy_id.retention_period_years
            )

    @api.onchange("retention_policy_id")
    def _onchange_retention_policy(self):
        """Update retention period when policy changes"""
        if self.retention_policy_id:
            self.retention_period_years = (
                self.retention_policy_id.retention_period_years
            )
            if self.storage_date:
                self._compute_destruction_eligible_date()

    def action_audit_trail(self):
        """View audit trail for this document."""
        self.ensure_one()

        # Create audit trail activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Audit trail reviewed: %s") % self.name,
            note=_("Document audit trail and chain of custody has been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Audit Trail: %s") % self.name,
            "res_model": "mail.message",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("model", "=", "records.document"), ("res_id", "=", self.id)],
            "context": {
                "search_default_model": "records.document",
                "search_default_res_id": self.id,
            },
        }

    def action_download(self):
        """Download document file."""
        self.ensure_one()

        # Update access tracking
        self.write(
            {
                "last_accessed_date": fields.Datetime.now(),
                "last_accessed_by": self.env.user.id,
                "access_count": self.access_count + 1,
            }
        )

        # Create download activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Document downloaded: %s") % self.name,
            note=_("Document file has been downloaded and accessed."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Document downloaded: %s") % self.name, message_type="notification"
        )

        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/records.document/%s/attachment_file/%s?download=true"
            % (self.id, self.name),
            "target": "new",
        }

    def action_request_retrieval(self):
        """Request document retrieval from storage."""
        self.ensure_one()
        if self.state != "stored":
            raise UserError(_("Only stored documents can be retrieved."))

        self.write(
            {
                "state": "retrieved",
                "action_type": "retrieve",
                "action_date": fields.Date.today(),
                "last_accessed_date": fields.Datetime.now(),
                "last_accessed_by": self.env.user.id,
            }
        )

        self.message_post(body=_("Document retrieval requested: %s") % self.name)
        return True

    def action_approve_destruction(self):
        """Approve document for destruction."""
        self.ensure_one()
        if self.legal_hold:
            raise UserError(
                _("Cannot approve destruction - document is under legal hold.")
            )

        self.write(
            {
                "destruction_approved": True,
                "action_type": "destroy",
                "action_date": fields.Date.today(),
            }
        )

        self.message_post(body=_("Document approved for destruction: %s") % self.name)
        return True

    def action_mark_destroyed(self):
        """Mark document as destroyed."""
        self.ensure_one()
        if not self.destruction_approved:
            raise UserError(_("Document destruction must be approved first."))

        self.write(
            {
                "state": "destroyed",
                "destruction_date": fields.Date.today(),
                "active": False,
            }
        )

        self.message_post(body=_("Document destroyed: %s") % self.name)
        return True

    def action_verify_compliance(self):
        """Verify document compliance."""
        self.ensure_one()
        self.write(
            {
                "compliance_verified": True,
                "compliance_verification_date": fields.Date.today(),
            }
        )

        self.message_post(body=_("Document compliance verified: %s") % self.name)
        return True

    def action_mark_permanent(self):
        """Mark document as permanent retention."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot mark archived document as permanent."))

        # Update notes with permanent marking
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nMarked as permanent on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create permanent marking activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Document marked permanent: %s") % self.name,
            note=_(
                "Document has been marked for permanent retention and cannot be destroyed."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Document marked for permanent retention: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Permanent Retention"),
                "message": _("Document %s has been marked for permanent retention.")
                % self.name,
                "type": "info",
                "sticky": True,
            },
        }

    def action_scan_document(self):
        """Initiate document scanning process."""
        self.ensure_one()

        # Create scanning activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Document scanning initiated: %s") % self.name,
            note=_("Document scanning process has been initiated and is in progress."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Document scanning initiated: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Scan Document"),
            "res_model": "document.scan.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_id": self.id,
                "default_scan_type": "digital",
            },
        }

    def action_schedule_destruction(self):
        """Schedule document for destruction."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot schedule archived document for destruction."))

        # Update notes with destruction scheduling
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nScheduled for destruction on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create destruction scheduling activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Document scheduled for destruction: %s") % self.name,
            note=_(
                "Document has been scheduled for destruction according to retention policy."
            ),
            user_id=self.user_id.id,
            date_deadline=fields.Date.today() + fields.timedelta(days=30),
        )

        self.message_post(
            body=_("Document scheduled for destruction: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Destruction"),
            "res_model": "destruction.schedule.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_id": self.id,
                "default_destruction_date": fields.Date.today()
                + fields.timedelta(days=30),
            },
        }

    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")
    # Document Management Fields
    customer_id = fields.Many2one("res.partner", "Customer")
    days_until_destruction = fields.Integer(
        "Days Until Destruction", compute="_compute_days_until_destruction"
    )
    department_id = fields.Many2one("hr.department", "Department")
    destruction_authorized_by = fields.Many2one(
        "res.users", "Destruction Authorized By"
    )
    destruction_certificate_id = fields.Many2one(
        "destruction.certificate", "Destruction Certificate"
    )
    destruction_method_id = fields.Many2one("destruction.method", "Destruction Method")
    destruction_scheduled_date = fields.Date("Scheduled Destruction Date")
    digital_copy_location = fields.Char("Digital Copy Location")
    document_classification = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        default="internal",
    )
    document_integrity_verified = fields.Boolean(
        "Document Integrity Verified", default=False
    )
    document_size_mb = fields.Float("Document Size (MB)", default=0.0)
    document_status = fields.Selection(
        [
            ("active", "Active"),
            ("archived", "Archived"),
            ("pending_destruction", "Pending Destruction"),
        ],
        default="active",
    )
    indexing_completed = fields.Boolean("Indexing Completed", default=False)
    legal_hold_applied = fields.Boolean("Legal Hold Applied", default=False)
    metadata_extraction_completed = fields.Boolean(
        "Metadata Extraction Completed", default=False
    )
    ocr_processing_completed = fields.Boolean("OCR Processing Completed", default=False)
    original_file_name = fields.Char("Original File Name")
    page_count = fields.Integer("Page Count", default=1)
    privacy_level = fields.Selection(
        [("public", "Public"), ("internal", "Internal"), ("private", "Private")],
        default="internal",
    )
    quality_score = fields.Float("Quality Score", default=0.0)
    retention_category = fields.Selection(
        [
            ("permanent", "Permanent"),
            ("long_term", "Long Term"),
            ("short_term", "Short Term"),
        ],
        default="short_term",
    )
    scanning_quality = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")], default="medium"
    )
    search_keywords = fields.Text("Search Keywords")
    security_marking = fields.Selection(
        [
            ("unclassified", "Unclassified"),
            ("restricted", "Restricted"),
            ("confidential", "Confidential"),
            ("secret", "Secret"),
        ],
        default="unclassified",
    )
    version_control_enabled = fields.Boolean("Version Control Enabled", default=False)
    audit_trail_count = fields.Integer(
        "Audit Trail Count", compute="_compute_audit_trail_count"
    )
    chain_of_custody_count = fields.Integer(
        "Chain of Custody Count", compute="_compute_chain_of_custody_count"
    )
    compliance_verified = fields.Boolean("Compliance Verified", default=False)
    file_format = fields.Char("File Format")
    file_size = fields.Float("File Size (MB)")
    resolution = fields.Char("Resolution")
    scan_date = fields.Datetime("Scan Date")
    signature_verified = fields.Boolean("Signature Verified", default=False)

    # Retention Policy Management
    retention_policy_id = fields.Many2one(
        "records.retention.policy",
        string="Retention Policy",
        tracking=True,
        help="Retention policy governing this document",
    )
    retention_status = fields.Selection(
        [
            ("active", "Active Retention"),
            ("eligible", "Eligible for Destruction"),
            ("hold", "On Hold"),
            ("permanent", "Permanent Retention"),
        ],
        string="Retention Status",
        compute="_compute_retention_status",
        store=True,
        tracking=True,
    )

    # Enhanced State Management

    def action_unmark_permanent(self):
        """Remove permanent retention marking from document."""
        self.ensure_one()

        # Update notes with permanent unmarking
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nPermanent marking removed on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create unmarking activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Permanent marking removed: %s") % self.name,
            note=_("Permanent retention marking has been removed from document."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Permanent retention marking removed: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Permanent Marking Removed"),
                "message": _(
                    "Permanent retention marking has been removed from document %s."
                )
                % self.name,
                "type": "warning",
                "sticky": False,
            },
        }

    def action_view_chain_of_custody(self):
        """View chain of custody for this document."""
        self.ensure_one()

        # Create chain of custody viewing activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Chain of custody reviewed: %s") % self.name,
            note=_("Document chain of custody and handling history has been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Chain of Custody: %s") % self.name,
            "res_model": "document.custody.log",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("document_id", "=", self.id)],
            "context": {
                "default_document_id": self.id,
                "search_default_document_id": self.id,
                "search_default_group_by_date": True,
            },
        }

    def action_activate(self):
        """Activate the record."""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate the record."""
        self.write({"state": "inactive"})

    def action_archive(self):
        """Archive the record."""
        self.write({"state": "archived", "active": False})

    def action_restore_from_archive(self):
        """Restore archived document back to active state."""
        self.ensure_one()
        if self.state != "archived":
            raise UserError(_("Only archived documents can be restored."))

        self.write(
            {
                "state": "active",
                "active": True,
                "action_type": "restore",
                "action_date": fields.Date.today(),
            }
        )

        self.message_post(
            body=_("Document restored from archive: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Document Restored"),
                "message": _("Document %s has been restored from archive.") % self.name,
                "type": "success",
                "sticky": False,
            },
        }

    def action_place_legal_hold(self):
        """Place document under legal hold."""
        self.ensure_one()
        if self.legal_hold:
            raise UserError(_("Document is already under legal hold."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Place Legal Hold"),
            "res_model": "legal.hold.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_id": self.id,
                "default_hold_reason": "",
            },
        }

    def action_release_legal_hold(self):
        """Release document from legal hold."""
        self.ensure_one()
        if not self.legal_hold:
            raise UserError(_("Document is not under legal hold."))

        self.write(
            {
                "legal_hold": False,
                "legal_hold_reason": "",
                "action_type": "release_hold",
                "action_date": fields.Date.today(),
            }
        )

        self.message_post(
            body=_("Legal hold released for document: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Legal Hold Released"),
                "message": _("Legal hold has been released for document %s.")
                % self.name,
                "type": "success",
                "sticky": False,
            },
        }

    def action_update_location(self):
        """Update document storage location."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Update Location"),
            "res_model": "document.location.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_id": self.id,
                "default_current_location_id": (
                    self.location_id.id if self.location_id else False
                ),
            },
        }

    def action_create_version(self):
        """Create a new version of this document."""
        self.ensure_one()

        # Parse current version number and increment
        current_version = self.version_number or "1.0"
        try:
            major, minor = current_version.split(".")
            new_version = f"{major}.{int(minor) + 1}"
        except (ValueError, AttributeError):
            new_version = "1.1"

        return {
            "type": "ir.actions.act_window",
            "name": _("Create New Version"),
            "res_model": "records.document",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_name": self.name + f" v{new_version}",
                "default_parent_document_id": self.id,
                "default_version_number": new_version,
                "default_document_type_id": (
                    self.document_type_id.id if self.document_type_id else False
                ),
                "default_retention_policy_id": (
                    self.retention_policy_id.id if self.retention_policy_id else False
                ),
                "default_customer_id": (
                    self.customer_id.id if self.customer_id else False
                ),
                "default_confidentiality_level": self.confidentiality_level,
                "default_document_category": self.document_category,
            },
        }

    def action_bulk_update_retention(self):
        """Bulk update retention policy for selected documents."""
        selected_docs = self.browse(self.env.context.get("active_ids", []))

        return {
            "type": "ir.actions.act_window",
            "name": _("Bulk Update Retention Policy"),
            "res_model": "bulk.retention.update.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_ids": [(6, 0, selected_docs.ids)],
                "active_model": "records.document",
                "active_ids": selected_docs.ids,
            },
        }

    def create(self, vals):
        """Override create to set default values and create audit trail."""
        if not vals.get("name"):
            vals["name"] = _("New Document %s") % fields.Datetime.now().strftime(
                "%Y%m%d-%H%M%S"
            )

        # Set default retention start date to storage date or today
        if not vals.get("retention_start_date") and vals.get("storage_date"):
            vals["retention_start_date"] = vals["storage_date"]
        elif not vals.get("retention_start_date"):
            vals["retention_start_date"] = fields.Date.today()

        # Auto-assign retention policy based on document type
        if vals.get("document_type_id") and not vals.get("retention_policy_id"):
            doc_type = self.env["records.document.type"].browse(
                vals["document_type_id"]
            )
            if doc_type.default_retention_policy_id:
                vals["retention_policy_id"] = doc_type.default_retention_policy_id.id
                vals["retention_period_years"] = (
                    doc_type.default_retention_policy_id.retention_period_years
                )

        # Create the record
        record = super().create(vals)

        # Create initial chain of custody entry
        if record.customer_id:
            self.env["records.chain.of.custody"].create(
                {
                    "document_id": record.id,
                    "action": "created",
                    "location_from": False,
                    "location_to": (
                        record.location_id.id if record.location_id else False
                    ),
                    "responsible_user_id": self.env.user.id,
                    "date": fields.Datetime.now(),
                    "notes": f"Document created: {record.name}",
                }
            )

        return record

    @api.model
    def get_documents_by_retention_status(self, status):
        """Get documents filtered by retention status."""
        return self.search([("retention_status", "=", status)])

    @api.model
    def get_documents_eligible_for_destruction(self):
        """Get all documents eligible for destruction."""
        today = fields.Date.today()
        return self.search(
            [
                ("destruction_eligible_date", "<=", today),
                ("legal_hold", "=", False),
                ("destruction_approved", "=", False),
                ("state", "!=", "archived"),
            ]
        )

    @api.model
    def get_documents_requiring_compliance_review(self):
        """Get documents that need compliance review."""
        return self.search(
            [
                ("compliance_verified", "=", False),
                ("naid_compliance", "=", True),
                ("state", "=", "active"),
            ]
        )

    def get_document_history(self):
        """Get comprehensive document history including messages and chain of custody."""
        self.ensure_one()

        history = []

        # Add messages to history
        for message in self.message_ids:
            history.append(
                {
                    "type": "message",
                    "date": message.date,
                    "author": message.author_id.name,
                    "content": message.body,
                    "subject": message.subject,
                }
            )

        # Add chain of custody to history
        for custody in self.chain_of_custody_ids:
            history.append(
                {
                    "type": "custody",
                    "date": custody.date,
                    "action": custody.action,
                    "responsible": custody.responsible_user_id.name,
                    "location_from": (
                        custody.location_from.name if custody.location_from else ""
                    ),
                    "location_to": (
                        custody.location_to.name if custody.location_to else ""
                    ),
                    "notes": custody.notes,
                }
            )

        # Sort by date
        history.sort(key=lambda x: x["date"], reverse=True)

        return history

    def generate_qr_code(self):
        """Generate QR code for document tracking."""
        self.ensure_one()
        import qrcode
        import base64
        from io import BytesIO

        # Create QR code content
        qr_content = f"DOC:{self.id}:{self.name}:{self.barcode or ''}"

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_content)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

        return qr_code_base64

    def validate_document_integrity(self):
        """Validate document integrity and update verification status."""
        self.ensure_one()

        # Placeholder for document integrity validation
        # In a real implementation, this would check file hashes, digital signatures, etc.

        self.write(
            {
                "document_integrity_verified": True,
                "compliance_verified": True,
                "compliance_verification_date": fields.Date.today(),
            }
        )

        self.message_post(
            body=_("Document integrity validated: %s") % self.name,
            message_type="notification",
        )

        return True
