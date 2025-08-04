# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsDocumentType(models.Model):
    _name = "records.document.type"
    _description = "Records Document Type"
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
        "res.users", string="Assigned User", default=lambda self: self.env.user
    )

    # Timestamps
    date_created = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    date_modified = fields.Datetime(string="Modified Date")

    # Control Fields
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Internal Notes")

    # New Fields for Compliance and Analytics
    approval_date = fields.Date(
        "Approval Date", tracking=True, help="Date of last approval."
    )
    approval_required = fields.Boolean(
        "Approval Required",
        default=False,
        tracking=True,
        help="Is approval required for this document type?",
    )
    approved_by = fields.Many2one(
        "res.users",
        "Approved By",
        tracking=True,
        help="User who approved this document type.",
    )
    audit_readiness_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        "Audit Readiness Level",
        tracking=True,
        help="Level of audit readiness.",
    )
    audit_required = fields.Boolean(
        "Audit Required",
        default=False,
        tracking=True,
        help="Is an audit required for this document type?",
    )
    auto_classification_potential = fields.Float(
        "Auto-Classification Potential",
        digits=(3, 2),
        tracking=True,
        help="Potential for auto-classification.",
    )
    classification_accuracy_score = fields.Float(
        "Classification Accuracy Score",
        tracking=True,
        help="Accuracy score of classification.",
    )
    compliance_notes = fields.Text(
        "Compliance Notes", tracking=True, help="Notes on compliance."
    )
    compliance_risk_assessment = fields.Text(
        "Compliance Risk Assessment",
        tracking=True,
        help="Assessment of compliance risk.",
    )
    compliance_status = fields.Selection(
        [
            ("compliant", "Compliant"),
            ("non_compliant", "Non-Compliant"),
            ("under_review", "Under Review"),
        ],
        "Compliance Status",
        tracking=True,
        help="Current compliance status.",
    )
    document_count = fields.Integer(
        "Document Count",
        compute="_compute_document_count",
        store=True,
        help="Number of documents of this type.",
    )
    document_type_utilization = fields.Float(
        "Document Type Utilization",
        compute="_compute_document_type_utilization",
        store=True,
        help="Utilization of this document type.",
    )
    growth_trend_indicator = fields.Selection(
        [("up", "Up"), ("down", "Down"), ("stable", "Stable")],
        "Growth Trend",
        tracking=True,
        help="Growth trend of this document type.",
    )
    regulatory_compliance_score = fields.Float(
        "Regulatory Compliance Score",
        tracking=True,
        help="Score for regulatory compliance.",
    )
    regulatory_requirement = fields.Text(
        "Regulatory Requirement",
        tracking=True,
        help="Regulatory requirements for this document type.",
    )
    retention_compliance = fields.Float(
        "Retention Compliance",
        tracking=True,
        help="Compliance with retention policies.",
    )
    risk_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        "Risk Level",
        tracking=True,
        help="Risk level associated with this document type.",
    )
    seasonal_pattern_score = fields.Float(
        "Seasonal Pattern Score", tracking=True, help="Score for seasonal patterns."
    )
    security_classification = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        "Security Classification",
        tracking=True,
        help="Security classification of the document type.",
    )
    type_complexity_rating = fields.Integer(
        "Type Complexity Rating",
        tracking=True,
        help="Rating of the complexity of this document type.",
    )

    # === ENHANCED DOCUMENT TYPE MANAGEMENT ===

    # Default Configuration
    default_retention_policy_id = fields.Many2one(
        "records.retention.policy",
        string="Default Retention Policy",
        tracking=True,
        help="Default retention policy for documents of this type",
    )
    default_confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("top_secret", "Top Secret"),
        ],
        string="Default Confidentiality Level",
        default="internal",
        tracking=True,
        help="Default confidentiality level for documents of this type",
    )

    # Document Processing Configuration
    requires_digital_copy = fields.Boolean(
        string="Requires Digital Copy",
        default=False,
        tracking=True,
        help="Whether documents of this type must have a digital copy",
    )
    auto_index_enabled = fields.Boolean(
        string="Auto-Index Enabled",
        default=True,
        tracking=True,
        help="Enable automatic indexing for documents of this type",
    )
    ocr_processing_required = fields.Boolean(
        string="OCR Processing Required",
        default=False,
        tracking=True,
        help="Whether OCR processing is required for documents of this type",
    )
    quality_check_required = fields.Boolean(
        string="Quality Check Required",
        default=False,
        tracking=True,
        help="Whether quality checks are required for documents of this type",
    )

    # Storage and Location Configuration
    preferred_storage_location_id = fields.Many2one(
        "records.location",
        string="Preferred Storage Location",
        tracking=True,
        help="Preferred location for storing documents of this type",
    )
    climate_controlled_storage = fields.Boolean(
        string="Climate Controlled Storage",
        default=False,
        tracking=True,
        help="Whether documents of this type require climate controlled storage",
    )
    fireproof_storage_required = fields.Boolean(
        string="Fireproof Storage Required",
        default=False,
        tracking=True,
        help="Whether documents of this type require fireproof storage",
    )

    # Compliance and Legal Requirements
    naid_compliance_required = fields.Boolean(
        string="NAID Compliance Required",
        default=False,
        tracking=True,
        help="Whether NAID compliance is required for documents of this type",
    )
    destruction_witness_required = fields.Boolean(
        string="Destruction Witness Required",
        default=False,
        tracking=True,
        help="Whether destruction witness is required for documents of this type",
    )
    legal_review_required = fields.Boolean(
        string="Legal Review Required",
        default=False,
        tracking=True,
        help="Whether legal review is required before destruction",
    )
    customer_notification_required = fields.Boolean(
        string="Customer Notification Required",
        default=True,
        tracking=True,
        help="Whether customer notification is required for destruction",
    )

    # Document Lifecycle Configuration
    minimum_retention_years = fields.Integer(
        string="Minimum Retention Years",
        default=1,
        tracking=True,
        help="Minimum number of years documents must be retained",
    )
    maximum_retention_years = fields.Integer(
        string="Maximum Retention Years",
        default=7,
        tracking=True,
        help="Maximum number of years documents should be retained",
    )
    permanent_retention_allowed = fields.Boolean(
        string="Permanent Retention Allowed",
        default=False,
        tracking=True,
        help="Whether permanent retention is allowed for this document type",
    )

    # Processing and Workflow Configuration
    approval_workflow_id = fields.Many2one(
        "records.approval.workflow",
        string="Approval Workflow",
        tracking=True,
        help="Default approval workflow for documents of this type",
    )
    scanning_resolution_dpi = fields.Integer(
        string="Scanning Resolution (DPI)",
        default=300,
        tracking=True,
        help="Default scanning resolution for documents of this type",
    )
    file_format_preference = fields.Selection(
        [
            ("pdf", "PDF"),
            ("tiff", "TIFF"),
            ("jpg", "JPEG"),
            ("png", "PNG"),
            ("doc", "Word Document"),
            ("xls", "Excel"),
        ],
        string="File Format Preference",
        default="pdf",
        tracking=True,
        help="Preferred file format for digital copies",
    )

    # Analytics and Reporting Fields
    average_processing_time = fields.Float(
        string="Average Processing Time (Hours)",
        compute="_compute_average_processing_time",
        store=True,
        help="Average time to process documents of this type",
    )
    total_storage_cost = fields.Monetary(
        string="Total Storage Cost",
        compute="_compute_total_storage_cost",
        store=True,
        currency_field="currency_id",
        help="Total storage cost for all documents of this type",
    )
    average_retrieval_time = fields.Float(
        string="Average Retrieval Time (Hours)",
        compute="_compute_average_retrieval_time",
        store=True,
        help="Average time to retrieve documents of this type",
    )

    # Financial Configuration
    storage_rate_per_month = fields.Monetary(
        string="Storage Rate per Month",
        currency_field="currency_id",
        tracking=True,
        help="Monthly storage rate for documents of this type",
    )
    retrieval_fee = fields.Monetary(
        string="Retrieval Fee",
        currency_field="currency_id",
        tracking=True,
        help="Fee for retrieving documents of this type",
    )
    destruction_fee = fields.Monetary(
        string="Destruction Fee",
        currency_field="currency_id",
        tracking=True,
        help="Fee for destroying documents of this type",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        tracking=True,
    )

    # Template and Format Configuration
    # (Removed document_template_ids - model doesn't exist)
    required_metadata_fields = fields.Text(
        string="Required Metadata Fields",
        help="JSON list of required metadata fields for documents of this type",
    )
    index_keywords = fields.Text(
        string="Index Keywords",
        help="Keywords used for automatic indexing of documents of this type",
    )

    # Usage Statistics
    documents_created_this_month = fields.Integer(
        string="Documents Created This Month",
        compute="_compute_monthly_statistics",
        help="Number of documents created this month",
    )
    documents_destroyed_this_month = fields.Integer(
        string="Documents Destroyed This Month",
        compute="_compute_monthly_statistics",
        help="Number of documents destroyed this month",
    )
    monthly_growth_rate = fields.Float(
        string="Monthly Growth Rate (%)",
        compute="_compute_monthly_growth_rate",
        help="Monthly growth rate for documents of this type",
    )

    # Computed Fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    def _compute_document_count(self):
        """Computes the number of documents for this type."""
        for record in self:
            record.document_count = self.env["records.document"].search_count(
                [("document_type_id", "=", record.id)]
            )

    @api.depends("document_count", "document_type_utilization")
    def _compute_document_type_utilization(self):
        """Computes the utilization of this document type across all documents."""
        for record in self:
            total_docs = self.env["records.document"].search_count([])
            if total_docs > 0:
                record.document_type_utilization = (
                    record.document_count / total_docs
                ) * 100
            else:
                record.document_type_utilization = 0.0

    @api.depends("document_count")
    def _compute_average_processing_time(self):
        """Compute average processing time for documents of this type."""
        for record in self:
            documents = self.env["records.document"].search(
                [
                    ("document_type_id", "=", record.id),
                    ("date_created", "!=", False),
                    ("date_modified", "!=", False),
                ]
            )
            if documents:
                total_time = 0
                count = 0
                for doc in documents:
                    if doc.date_created and doc.date_modified:
                        delta = doc.date_modified - doc.date_created
                        total_time += delta.total_seconds() / 3600  # Convert to hours
                        count += 1
                record.average_processing_time = (
                    total_time / count if count > 0 else 0.0
                )
            else:
                record.average_processing_time = 0.0

    @api.depends("document_count", "storage_rate_per_month")
    def _compute_total_storage_cost(self):
        """Compute total storage cost for all documents of this type."""
        for record in self:
            if record.storage_rate_per_month and record.document_count:
                record.total_storage_cost = (
                    record.storage_rate_per_month * record.document_count
                )
            else:
                record.total_storage_cost = 0.0

    @api.depends("document_count")
    def _compute_average_retrieval_time(self):
        """Compute average retrieval time for documents of this type."""
        for record in self:
            # This would typically be computed from actual retrieval logs
            # For now, we'll use a placeholder calculation
            if record.document_count > 0:
                # Base retrieval time with factors for document type complexity
                base_time = 2.0  # hours
                complexity_factor = (record.type_complexity_rating or 1) * 0.5
                record.average_retrieval_time = base_time + complexity_factor
            else:
                record.average_retrieval_time = 0.0

    def _compute_monthly_statistics(self):
        """Compute monthly statistics for document creation and destruction."""
        today = fields.Date.today()
        first_day = today.replace(day=1)

        for record in self:
            # Documents created this month
            record.documents_created_this_month = self.env[
                "records.document"
            ].search_count(
                [
                    ("document_type_id", "=", record.id),
                    ("date_created", ">=", first_day),
                    ("date_created", "<=", today),
                ]
            )

            # Documents destroyed this month
            record.documents_destroyed_this_month = self.env[
                "records.document"
            ].search_count(
                [
                    ("document_type_id", "=", record.id),
                    ("destruction_date", ">=", first_day),
                    ("destruction_date", "<=", today),
                ]
            )

    @api.depends("documents_created_this_month")
    def _compute_monthly_growth_rate(self):
        """Compute monthly growth rate."""
        for record in self:
            # Get previous month's creation count
            today = fields.Date.today()
            if today.month == 1:
                prev_month = today.replace(year=today.year - 1, month=12, day=1)
                prev_month_end = today.replace(day=1) - fields.timedelta(days=1)
            else:
                prev_month = today.replace(month=today.month - 1, day=1)
                prev_month_end = today.replace(day=1) - fields.timedelta(days=1)

            prev_month_count = self.env["records.document"].search_count(
                [
                    ("document_type_id", "=", record.id),
                    ("date_created", ">=", prev_month),
                    ("date_created", "<=", prev_month_end),
                ]
            )

            if prev_month_count > 0:
                growth = (
                    (record.documents_created_this_month - prev_month_count)
                    / prev_month_count
                ) * 100
                record.monthly_growth_rate = growth
            else:
                record.monthly_growth_rate = (
                    100.0 if record.documents_created_this_month > 0 else 0.0
                )

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()
        return super().write(vals)

    @api.constrains("minimum_retention_years", "maximum_retention_years")
    def _check_retention_years(self):
        """Validate retention year settings."""
        for record in self:
            if record.minimum_retention_years < 0:
                raise ValidationError(_("Minimum retention years must be positive."))
            if record.maximum_retention_years < 0:
                raise ValidationError(_("Maximum retention years must be positive."))
            if record.minimum_retention_years > record.maximum_retention_years:
                raise ValidationError(
                    _("Minimum retention years cannot exceed maximum retention years.")
                )

    @api.constrains("scanning_resolution_dpi")
    def _check_scanning_resolution(self):
        """Validate scanning resolution."""
        for record in self:
            if record.scanning_resolution_dpi and record.scanning_resolution_dpi < 75:
                raise ValidationError(_("Scanning resolution must be at least 75 DPI."))

    @api.constrains("type_complexity_rating")
    def _check_complexity_rating(self):
        """Validate complexity rating."""
        for record in self:
            if record.type_complexity_rating and (
                record.type_complexity_rating < 1 or record.type_complexity_rating > 10
            ):
                raise ValidationError(_("Complexity rating must be between 1 and 10."))

    @api.onchange("default_retention_policy_id")
    def _onchange_default_retention_policy(self):
        """Update retention years when default policy changes."""
        if self.default_retention_policy_id:
            self.minimum_retention_years = (
                self.default_retention_policy_id.retention_period_years
            )
            self.maximum_retention_years = (
                self.default_retention_policy_id.retention_period_years
            )

    @api.onchange("naid_compliance_required")
    def _onchange_naid_compliance(self):
        """Update related settings when NAID compliance is required."""
        if self.naid_compliance_required:
            self.destruction_witness_required = True
            self.audit_required = True
            self.security_classification = "confidential"

    @api.onchange("security_classification")
    def _onchange_security_classification(self):
        """Update storage requirements based on security classification."""
        if self.security_classification in ["confidential", "restricted"]:
            self.climate_controlled_storage = True
            self.fireproof_storage_required = True
            self.legal_review_required = True

    def action_view_type_documents(self):
        """View all documents of this type."""
        self.ensure_one()

        # Create activity to track document viewing
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Documents viewed for type: %s") % self.name,
            note=_("All documents of this type have been reviewed and analyzed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Documents of Type: %s") % self.name,
            "res_model": "records.document",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("document_type_id", "=", self.id)],
            "context": {
                "default_document_type_id": self.id,
                "search_default_document_type_id": self.id,
                "search_default_group_by_state": True,
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

    def action_create_document_template(self):
        """Create a new document template for this type."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Create Document Template"),
            "res_model": "document.template",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_type_id": self.id,
                "default_name": f"{self.name} Template",
                "default_file_format": self.file_format_preference,
                "default_scanning_resolution": self.scanning_resolution_dpi,
            },
        }

    def action_analyze_document_trends(self):
        """Analyze document trends for this type."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Document Trends Analysis: %s") % self.name,
            "res_model": "document.trend.analysis.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_type_id": self.id,
                "default_analysis_period": "12_months",
            },
        }

    def action_bulk_update_retention_policy(self):
        """Bulk update retention policy for all documents of this type."""
        self.ensure_one()

        document_count = self.env["records.document"].search_count(
            [("document_type_id", "=", self.id)]
        )

        if document_count == 0:
            raise UserError(_("No documents found for this document type."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Bulk Update Retention Policy"),
            "res_model": "bulk.retention.update.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_type_id": self.id,
                "default_new_retention_policy_id": (
                    self.default_retention_policy_id.id
                    if self.default_retention_policy_id
                    else False
                ),
                "document_count": document_count,
            },
        }

    def action_configure_compliance_settings(self):
        """Configure compliance settings for this document type."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Configure Compliance Settings"),
            "res_model": "document.type.compliance.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_type_id": self.id,
                "default_naid_compliance_required": self.naid_compliance_required,
                "default_legal_review_required": self.legal_review_required,
                "default_destruction_witness_required": self.destruction_witness_required,
            },
        }

    def action_export_document_list(self):
        """Export list of all documents of this type."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_url",
            "url": f"/records/export/documents?document_type_id={self.id}",
            "target": "new",
        }

    def action_view_storage_locations(self):
        """View storage locations for documents of this type."""
        self.ensure_one()

        document_ids = (
            self.env["records.document"]
            .search([("document_type_id", "=", self.id), ("location_id", "!=", False)])
            .mapped("location_id.id")
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Storage Locations: %s") % self.name,
            "res_model": "records.location",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("id", "in", document_ids)],
            "context": {
                "search_default_group_by_location_type": True,
            },
        }

    def action_compliance_audit(self):
        """Initiate compliance audit for this document type."""
        self.ensure_one()

        # Create audit activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Compliance audit initiated: %s") % self.name,
            note=_(
                "Compliance audit has been initiated for document type: %s. Review all documents and ensure compliance with regulations."
            )
            % self.name,
            user_id=self.user_id.id,
            date_deadline=fields.Date.today() + fields.timedelta(days=7),
        )

        self.write(
            {
                "compliance_status": "under_review",
                "audit_required": True,
            }
        )

        self.message_post(
            body=_("Compliance audit initiated for document type: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Compliance Audit Initiated"),
                "message": _(
                    "Compliance audit has been initiated for document type %s."
                )
                % self.name,
                "type": "info",
                "sticky": False,
            },
        }

    def get_type_statistics(self):
        """Get comprehensive statistics for this document type."""
        self.ensure_one()

        documents = self.env["records.document"].search(
            [("document_type_id", "=", self.id)]
        )

        stats = {
            "total_documents": len(documents),
            "active_documents": len(documents.filtered(lambda d: d.state == "active")),
            "archived_documents": len(
                documents.filtered(lambda d: d.state == "archived")
            ),
            "documents_on_legal_hold": len(documents.filtered(lambda d: d.legal_hold)),
            "documents_eligible_for_destruction": len(
                documents.filtered(
                    lambda d: d.destruction_eligible_date
                    and d.destruction_eligible_date <= fields.Date.today()
                )
            ),
            "average_document_age_days": 0,
            "total_storage_cost": self.total_storage_cost,
            "compliance_rate": 0,
        }

        if documents:
            # Calculate average document age
            current_date = fields.Datetime.now()
            total_age = 0
            count = 0
            for doc in documents:
                if doc.date_created:
                    age = (current_date - doc.date_created).days
                    total_age += age
                    count += 1
            stats["average_document_age_days"] = total_age / count if count > 0 else 0

            # Calculate compliance rate
            compliant_docs = len(documents.filtered(lambda d: d.compliance_verified))
            stats["compliance_rate"] = (compliant_docs / len(documents)) * 100

        return stats

    def create(self, vals):
        """Override create to set default values and initialize configuration."""
        if not vals.get("name"):
            vals["name"] = _("New Document Type %s") % fields.Datetime.now().strftime(
                "%Y%m%d-%H%M%S"
            )

        # Set default complexity rating if not provided
        if not vals.get("type_complexity_rating"):
            vals["type_complexity_rating"] = 5  # Medium complexity

        # Set default scanning resolution if not provided
        if not vals.get("scanning_resolution_dpi"):
            vals["scanning_resolution_dpi"] = 300  # Standard resolution

        # Auto-configure security settings based on classification
        if vals.get("security_classification") in ["confidential", "restricted"]:
            vals.update(
                {
                    "climate_controlled_storage": True,
                    "fireproof_storage_required": True,
                    "legal_review_required": True,
                    "naid_compliance_required": True,
                }
            )

        # Auto-configure retention settings based on compliance requirements
        if vals.get("naid_compliance_required"):
            vals.update(
                {
                    "destruction_witness_required": True,
                    "audit_required": True,
                    "customer_notification_required": True,
                }
            )

        # Create the record
        record = super().create(vals)

        # Log creation activity
        record.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Document type created: %s") % record.name,
            note=_(
                "New document type has been created with default configuration settings."
            ),
            user_id=record.user_id.id,
        )

        return record

    @api.model
    def get_most_used_document_types(self, limit=10):
        """Get the most frequently used document types."""
        types = self.search(
            [("state", "=", "active")], order="document_count desc", limit=limit
        )
        return types

    @api.model
    def get_compliance_summary(self):
        """Get compliance summary across all document types."""
        types = self.search([("state", "=", "active")])

        summary = {
            "total_types": len(types),
            "compliant_types": len(
                types.filtered(lambda t: t.compliance_status == "compliant")
            ),
            "non_compliant_types": len(
                types.filtered(lambda t: t.compliance_status == "non_compliant")
            ),
            "under_review_types": len(
                types.filtered(lambda t: t.compliance_status == "under_review")
            ),
            "naid_required_types": len(
                types.filtered(lambda t: t.naid_compliance_required)
            ),
            "high_risk_types": len(types.filtered(lambda t: t.risk_level == "high")),
        }

        return summary

    def name_get(self):
        """Custom name_get to show additional information."""
        result = []
        for record in self:
            name = record.name
            if record.document_count:
                name += f" ({record.document_count} docs)"
            if record.compliance_status:
                status_map = {
                    "compliant": "✓",
                    "non_compliant": "✗",
                    "under_review": "⚠",
                }
                name += f" {status_map.get(record.compliance_status, '')}"
            result.append((record.id, name))
        return result
