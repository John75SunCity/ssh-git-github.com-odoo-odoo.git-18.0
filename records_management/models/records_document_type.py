# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsDocumentType(models.Model):
    _name = "records.document.type"
    _description = "Records Document Type"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Document Type Name", required=True, tracking=True, index=True)
    code = fields.Char(string="Document Code", index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True, tracking=True)

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
            ("draft", "Draft"),
            ("active", "Active"),
            ("deprecated", "Deprecated"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # DOCUMENT TYPE CLASSIFICATION
    # ============================================================================

    # Document Category
    category_id = fields.Many2one(
        "records.document.category",
        string="Document Category",
        required=True,
    )

    document_class = fields.Selection(
        [
            ("financial", "Financial Records"),
            ("legal", "Legal Documents"),
            ("personnel", "Personnel Records"),
            ("medical", "Medical Records"),
            ("tax", "Tax Documents"),
            ("contracts", "Contracts"),
            ("correspondence", "Correspondence"),
            ("technical", "Technical Documentation"),
            ("compliance", "Compliance Records"),
            ("operational", "Operational Documents"),
        ],
        string="Document Class",
        required=True,
    )

    # Security and Compliance
    confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("secret", "Secret"),
        ],
        string="Confidentiality Level",
        default="internal",
        required=True,
    )

    security_classification = fields.Selection(
        [
            ("unclassified", "Unclassified"),
            ("sensitive", "Sensitive"),
            ("classified", "Classified"),
            ("top_secret", "Top Secret"),
        ],
        string="Security Classification",
        default="unclassified",
    )

    # ============================================================================
    # RETENTION & LIFECYCLE MANAGEMENT
    # ============================================================================

    # Retention Policy
    retention_policy_id = fields.Many2one(
        "records.retention.policy",
        string="Retention Policy",
        required=True,
    )

    default_retention_years = fields.Integer(
        string="Default Retention (Years)",
        default=7,
        help="Default retention period in years",
    )

    permanent_retention = fields.Boolean(
        string="Permanent Retention",
        default=False,
        help="Documents of this type are kept permanently",
    )

    # Destruction Requirements
    destruction_method = fields.Selection(
        [
            ("standard_shred", "Standard Shredding"),
            ("cross_cut_shred", "Cross-Cut Shredding"),
            ("incineration", "Incineration"),
            ("pulping", "Pulping"),
            ("digital_wipe", "Digital Secure Wipe"),
        ],
        string="Destruction Method",
        default="cross_cut_shred",
    )

    certificate_required = fields.Boolean(
        string="Destruction Certificate Required",
        default=True,
    )

    # ============================================================================
    # STORAGE & HANDLING REQUIREMENTS
    # ============================================================================

    # Storage Requirements
    climate_controlled = fields.Boolean(
        string="Climate Controlled Storage",
        default=False,
    )

    fireproof_storage = fields.Boolean(
        string="Fireproof Storage Required",
        default=False,
    )

    special_handling = fields.Boolean(
        string="Special Handling Required",
        default=False,
    )

    handling_instructions = fields.Text(string="Special Handling Instructions")

    # Access Requirements
    restricted_access = fields.Boolean(
        string="Restricted Access",
        default=False,
    )

    authorized_roles = fields.Many2many(
        "res.groups",
        string="Authorized Roles",
        help="User groups authorized to access this document type",
    )

    # ============================================================================
    # PROCESSING & WORKFLOW
    # ============================================================================

    # Processing Requirements
    requires_indexing = fields.Boolean(
        string="Requires Indexing",
        default=True,
    )

    requires_scanning = fields.Boolean(
        string="Requires Scanning",
        default=False,
    )

    requires_approval = fields.Boolean(
        string="Requires Approval",
        default=False,
    )

    approval_workflow_id = fields.Many2one(
        "workflow.definition",
        string="Approval Workflow",
    )

    # Metadata Requirements
    mandatory_metadata = fields.Text(
        string="Mandatory Metadata Fields",
        help="JSON list of required metadata fields",
    )

    optional_metadata = fields.Text(
        string="Optional Metadata Fields",
        help="JSON list of optional metadata fields",
    )

    # ============================================================================
    # OPERATIONAL METRICS
    # ============================================================================

    # Document Statistics
    document_count = fields.Integer(
        string="Document Count",
        compute="_compute_document_statistics",
        store=True,
    )

    total_storage_volume = fields.Float(
        string="Total Storage Volume (Cubic Ft)",
        compute="_compute_document_statistics",
        store=True,
        digits=(10, 2),
    )

    average_processing_time = fields.Float(
        string="Average Processing Time (Days)",
        compute="_compute_processing_metrics",
        store=True,
        digits=(5, 2),
    )

    average_retrieval_time = fields.Float(
        string="Average Retrieval Time (Hours)",
        compute="_compute_processing_metrics",
        store=True,
        digits=(5, 2),
    )

    # Utilization Metrics
    monthly_intake = fields.Integer(
        string="Monthly Document Intake",
        compute="_compute_utilization_metrics",
        store=True,
    )

    monthly_destruction = fields.Integer(
        string="Monthly Destruction Count",
        compute="_compute_utilization_metrics",
        store=True,
    )

    utilization_rate = fields.Float(
        string="Utilization Rate (%)",
        compute="_compute_utilization_metrics",
        store=True,
        digits=(5, 2),
    )

    # ============================================================================
    # COST & BILLING
    # ============================================================================

    # Currency Configuration
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Cost Information
    storage_cost_per_box = fields.Monetary(
        string="Storage Cost per Box/Month",
        currency_field="currency_id",
    )

    processing_cost_per_document = fields.Monetary(
        string="Processing Cost per Document",
        currency_field="currency_id",
    )

    destruction_cost_per_box = fields.Monetary(
        string="Destruction Cost per Box",
        currency_field="currency_id",
    )

    # Total Costs
    total_storage_cost = fields.Monetary(
        string="Total Storage Cost",
        compute="_compute_cost_metrics",
        store=True,
        currency_field="currency_id",
    )

    monthly_cost = fields.Monetary(
        string="Monthly Cost",
        compute="_compute_cost_metrics",
        store=True,
        currency_field="currency_id",
    )

    # ============================================================================
    # COMPLIANCE & REPORTING
    # ============================================================================

    # Regulatory Compliance
    regulatory_requirements = fields.Text(
        string="Regulatory Requirements",
        help="Specific regulatory requirements for this document type",
    )

    compliance_notes = fields.Text(string="Compliance Notes")

    audit_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annual", "Semi-Annual"),
            ("annual", "Annual"),
        ],
        string="Audit Frequency",
        default="annual",
    )

    last_audit_date = fields.Date(string="Last Audit Date")
    next_audit_date = fields.Date(string="Next Audit Date")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Related Documents
    document_ids = fields.One2many(
        "records.document",
        "document_type_id",
        string="Documents",
    )

    # Templates and Configurations
    template_ids = fields.One2many(
        "document.template",
        "document_type_id",
        string="Document Templates",
    )

    # Quality Control
    quality_control_id = fields.Many2one(
        "quality.control.plan",
        string="Quality Control Plan",
    )

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # TIMESTAMPS
    # ============================================================================

    date_created = fields.Datetime(
        string="Created Date",
        default=fields.Datetime.now,
        readonly=True,
    )
    date_modified = fields.Datetime(string="Last Modified")
    last_review_date = fields.Date(string="Last Review Date")
    next_review_date = fields.Date(string="Next Review Date")

    # Notes
    notes = fields.Text(string="Internal Notes")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("document_ids")
    def _compute_document_statistics(self):
        """Compute document count and storage volume"""
        for record in self:
            record.document_count = len(record.document_ids)
            
            # Calculate total storage volume
            total_volume = 0.0
            for doc in record.document_ids:
                if hasattr(doc, 'storage_volume') and doc.storage_volume:
                    total_volume += doc.storage_volume
            record.total_storage_volume = total_volume

    @api.depends("document_ids", "document_ids.processing_time", "document_ids.retrieval_time")
    def _compute_processing_metrics(self):
        """Compute average processing and retrieval times"""
        for record in self:
            docs_with_processing = record.document_ids.filtered(lambda d: d.processing_time)
            if docs_with_processing:
                record.average_processing_time = sum(docs_with_processing.mapped('processing_time')) / len(docs_with_processing)
            else:
                record.average_processing_time = 0.0
            
            docs_with_retrieval = record.document_ids.filtered(lambda d: d.retrieval_time)
            if docs_with_retrieval:
                record.average_retrieval_time = sum(docs_with_retrieval.mapped('retrieval_time')) / len(docs_with_retrieval)
            else:
                record.average_retrieval_time = 0.0

    @api.depends("document_ids")
    def _compute_utilization_metrics(self):
        """Compute utilization metrics"""
        for record in self:
            current_month = fields.Date.today().replace(day=1)
            
            # Monthly intake (documents created this month)
            monthly_docs = record.document_ids.filtered(
                lambda d: d.create_date and d.create_date.date() >= current_month
            )
            record.monthly_intake = len(monthly_docs)
            
            # Monthly destruction (documents destroyed this month)
            destroyed_docs = record.document_ids.filtered(
                lambda d: hasattr(d, 'destruction_date') and d.destruction_date and d.destruction_date >= current_month
            )
            record.monthly_destruction = len(destroyed_docs)
            
            # Utilization rate (active documents vs total capacity)
            active_docs = record.document_ids.filtered(lambda d: d.active)
            if record.document_count > 0:
                record.utilization_rate = (len(active_docs) / record.document_count) * 100
            else:
                record.utilization_rate = 0.0

    @api.depends("document_count", "storage_cost_per_box", "processing_cost_per_document")
    def _compute_cost_metrics(self):
        """Compute cost metrics"""
        for record in self:
            # Estimate boxes needed (assuming 100 documents per box)
            estimated_boxes = record.document_count / 100 if record.document_count else 0
            
            # Total storage cost (monthly)
            if record.storage_cost_per_box:
                record.total_storage_cost = estimated_boxes * record.storage_cost_per_box
            else:
                record.total_storage_cost = 0.0
            
            # Monthly processing cost
            processing_cost = 0.0
            if record.processing_cost_per_document and record.monthly_intake:
                processing_cost = record.monthly_intake * record.processing_cost_per_document
            
            record.monthly_cost = record.total_storage_cost + processing_cost

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_activate(self):
        """Activate document type"""
        self.ensure_one()
        if not self.retention_policy_id:
            raise UserError(_("Retention policy must be set before activation."))
        
        self.write({"state": "active"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Document Type Activated"),
                "message": _("Document type is now active and available for use."),
                "type": "success",
            },
        }

    def action_deprecate(self):
        """Deprecate document type"""
        self.ensure_one()
        self.write({"state": "deprecated"})
        
        # Notify users about deprecation
        self.message_post(
            body=_("Document type %s has been deprecated. No new documents should use this type.") % self.name
        )
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Document Type Deprecated"),
                "message": _("Document type has been deprecated."),
                "type": "warning",
            },
        }

    def action_view_documents(self):
        """View documents of this type"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Documents"),
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("document_type_id", "=", self.id)],
            "context": {"default_document_type_id": self.id},
        }

    def action_generate_report(self):
        """Generate document type utilization report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.document_type_report",
            "report_type": "qweb-pdf",
            "data": {"document_type_id": self.id},
            "context": self.env.context,
        }

    def action_schedule_audit(self):
        """Schedule next audit"""
        self.ensure_one()
        
        # Calculate next audit date based on frequency
        frequency_days = {
            "monthly": 30,
            "quarterly": 90,
            "semi_annual": 180,
            "annual": 365,
        }
        
        days = frequency_days.get(self.audit_frequency, 365)
        next_date = fields.Date.today() + fields.timedelta(days=days)
        
        self.write({
            "last_audit_date": fields.Date.today(),
            "next_audit_date": next_date,
        })
        
        # Create calendar event
        self.env["calendar.event"].create({
            "name": f"Document Type Audit - {self.name}",
            "start": next_date,
            "allday": True,
            "user_id": self.user_id.id,
            "description": f"Scheduled audit for document type {self.name}",
        })
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Audit Scheduled"),
                "message": _("Next audit scheduled for %s") % next_date,
                "type": "success",
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("default_retention_years")
    def _check_retention_years(self):
        """Ensure retention years is positive"""
        for record in self:
            if record.default_retention_years and record.default_retention_years < 0:
                raise ValidationError(_("Retention years must be positive."))

    @api.constrains("permanent_retention", "default_retention_years")
    def _check_retention_logic(self):
        """Ensure retention logic is consistent"""
        for record in self:
            if record.permanent_retention and record.default_retention_years:
                raise ValidationError(_("Cannot set retention years for permanent retention documents."))

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model
    def create(self, vals):
        """Override create to set defaults"""
        if not vals.get("code"):
            vals["code"] = self.env["ir.sequence"].next_by_code("records.document.type") or "RDT"
        
        # Set next review date
        if not vals.get("next_review_date"):
            vals["next_review_date"] = fields.Date.today() + fields.timedelta(days=365)  # Annual review
        
        return super().create(vals)

    def write(self, vals):
        """Override write to track changes"""
        # Update modification timestamp
        vals["date_modified"] = fields.Datetime.now()
        
        # Track state changes
        if "state" in vals:
            for record in self:
                old_state = dict(record._fields["state"].selection).get(record.state)
                new_state = dict(record._fields["state"].selection).get(vals["state"])
                record.message_post(
                    body=_("Document type status changed from %s to %s") % (old_state, new_state)
                )
        
        return super().write(vals)
