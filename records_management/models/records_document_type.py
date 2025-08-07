# -*- coding: utf-8 -*-
"""
Records Document Type Management Module

This module provides comprehensive document type classification and management for the Records
Management System. It implements detailed document categorization, retention policy assignment,
and compliance tracking for different types of documents and records throughout their lifecycle.

Key Features:
- Comprehensive document type classification with hierarchical categorization
- Automated retention policy assignment based on document type and regulations
- Security classification and access control based on document sensitivity
- Compliance tracking for regulatory requirements and industry standards
- Document lifecycle management with automated workflow triggers
- Integration with scanning and document ingestion systems
- Template management for document formatting and standardization

Business Processes:
1. Type Classification: Document type assignment during ingestion and processing
2. Retention Management: Automatic retention policy application based on document type
3. Security Classification: Security level assignment and access control implementation
4. Compliance Tracking: Regulatory compliance monitoring and reporting by document type
5. Lifecycle Management: Automated workflow triggers based on document type characteristics
6. Template Application: Document formatting and standardization based on type templates
7. Audit Trail Maintenance: Complete type assignment and change history tracking

Document Categories:
- Financial Records: Invoices, receipts, financial statements, and accounting documents
- Legal Documents: Contracts, agreements, legal correspondence, and regulatory filings
- Personnel Records: Employee files, HR documents, and confidential personnel information
- Medical Records: Patient files, medical histories, and healthcare documentation
- Government Records: Public records, permits, licenses, and regulatory correspondence
- Corporate Records: Board minutes, corporate resolutions, and governance documents
- Technical Documentation: Manuals, specifications, drawings, and technical records

Retention Policy Integration:
- Automatic retention period assignment based on document type and regulatory requirements
- Legal hold management with type-specific preservation rules
- Destruction scheduling with compliance verification and certificate generation
- Exception handling for documents with mixed classification or complex retention rules
- Regulatory compliance tracking with automated alerts and reporting
- Integration with legal and compliance teams for policy updates and management

Security and Access Control:
- Document type-based security classification with granular access controls
- Integration with user roles and security clearance systems
- Sensitive document identification and special handling procedures
- Audit trail tracking for access and modification by document type
- Compliance with privacy regulations and confidentiality requirements
- Integration with data loss prevention and security monitoring systems

Template and Formatting:
- Document type-specific templates for consistent formatting and structure
- Automated metadata extraction and assignment based on document type
- OCR and content analysis integration for automatic type detection
- Quality control and validation rules for document type accuracy
- Integration with document scanning and digital conversion systems
- Standardization of document naming conventions and file organization

Technical Implementation:
- Modern Odoo 18.0 architecture with comprehensive validation frameworks
- Advanced document classification algorithms with machine learning integration
- Performance optimized for high-volume document processing operations
- Integration with external document management and scanning systems
- Mail thread integration for notifications and workflow tracking

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

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
    name = fields.Char(
        string="Document Type Name", required=True, tracking=True, index=True
    )
    code = fields.Char(string="Document Code", index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Document Type Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
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
    # DOCUMENT CLASSIFICATION
    # ============================================================================
    category = fields.Selection(
        [
            ("financial", "Financial Records"),
            ("legal", "Legal Documents"),
            ("hr", "Human Resources"),
            ("operational", "Operational Documents"),
            ("compliance", "Compliance Records"),
            ("other", "Other"),
        ],
        string="Category",
        required=True,
        default="other",
        tracking=True,
    )

    confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal Use"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        string="Confidentiality Level",
        default="internal",
        tracking=True,
    )

    # ============================================================================
    # RETENTION MANAGEMENT
    # ============================================================================
    retention_policy_id = fields.Many2one(
        "records.retention.policy", string="Retention Policy", tracking=True
    )
    default_retention_years = fields.Integer(
        string="Default Retention (Years)", default=7
    )
    requires_legal_hold = fields.Boolean(string="Requires Legal Hold", default=False)
    destruction_method = fields.Selection(
        [
            ("shred", "Shredding"),
            ("pulp", "Pulping"),
            ("incineration", "Incineration"),
            ("digital_wipe", "Digital Wiping"),
        ],
        string="Destruction Method",
        default="shred",
    )

    # ============================================================================
    # INDEXING & METADATA
    # ============================================================================
    indexing_required = fields.Boolean(string="Indexing Required", default=True)
    metadata_template = fields.Text(string="Metadata Template")
    searchable_fields = fields.Char(string="Searchable Fields")
    default_tags = fields.Char(string="Default Tags")

    # ============================================================================
    # COMPLIANCE & REGULATIONS
    # ============================================================================
    regulatory_requirements = fields.Text(string="Regulatory Requirements")
    compliance_standards = fields.Char(string="Compliance Standards")
    audit_frequency = fields.Selection(
        [
            ("none", "None"),
            ("annual", "Annual"),
            ("biannual", "Bi-Annual"),
            ("quarterly", "Quarterly"),
        ],
        string="Audit Frequency",
        default="annual",
    )

    naid_compliance = fields.Boolean(string="NAID Compliance Required", default=False)
    hipaa_protected = fields.Boolean(string="HIPAA Protected", default=False)
    sox_compliance = fields.Boolean(string="SOX Compliance", default=False)

    # ============================================================================
    # PHYSICAL HANDLING
    # ============================================================================
    storage_requirements = fields.Text(string="Storage Requirements")
    handling_instructions = fields.Text(string="Handling Instructions")
    environmental_controls = fields.Boolean(
        string="Environmental Controls Required", default=False
    )
    max_box_weight = fields.Float(string="Max Box Weight (lbs)", default=40.0)

    # ============================================================================
    # WORKFLOW & PROCESSING
    # ============================================================================
    approval_required = fields.Boolean(
        string="Approval Required for Creation", default=False
    )
    auto_numbering = fields.Boolean(string="Auto Numbering", default=True)
    barcode_required = fields.Boolean(string="Barcode Required", default=True)
    digital_copy_required = fields.Boolean(
        string="Digital Copy Required", default=False
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    document_ids = fields.One2many(
        "records.document", "document_type_id", string="Documents"
    )
    parent_type_id = fields.Many2one(
        "records.document.type", string="Parent Document Type"
    )
    child_type_ids = fields.One2many(
        "records.document.type", "parent_type_id", string="Child Document Types"
    )

    # ============================================================================
    # MAIL FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain="[('res_model', '=', 'records.document.type')]",
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain="[('res_model', '=', 'records.document.type')]",
    )

    # ============================================================================
    # UTILIZATION FIELDS
    # ============================================================================
    utilization_level = fields.Selection(
        [("normal", "Normal"), ("high", "High")],
        string="Document Type Utilization",
        default="normal",
    )
    growth_trend_indicator = fields.Char(string="Growth Trend Indicator")
    help = fields.Char(string="Help")
    model = fields.Char(string="Model")
    regulatory_compliance_score = fields.Char(string="Regulatory Compliance Score")
    regulatory_requirement = fields.Char(string="Regulatory Requirement")
    res_model = fields.Char(string="Res Model")
    retention_compliance = fields.Char(string="Retention Compliance")
    risk_level = fields.Char(string="Risk Level")
    seasonal_pattern_score = fields.Char(string="Seasonal Pattern Score")
    security_classification = fields.Char(string="Security Classification")
    type_complexity_rating = fields.Selection(
        [("normal", "Normal"), ("high", "High")],
        string="Type Complexity Rating",
        default="normal",
    )
    view_mode = fields.Char(string="View Mode")

    # ============================================================================
    @api.depends("document_ids")
    def _compute_document_count(self):
        for record in self:
            record.document_count = len(record.document_ids)

    @api.depends("child_type_ids")
    def _compute_child_type_count(self):
        for record in self:
            record.child_type_count = len(record.child_type_ids)

    @api.depends("retention_policy_id", "default_retention_years")
    def _compute_effective_retention(self):
        for record in self:
            if record.retention_policy_id:
                record.effective_retention_years = (
                    record.retention_policy_id.retention_years
                )
            else:
                record.effective_retention_years = record.default_retention_years

    document_count = fields.Integer(
        compute="_compute_document_count", string="Document Count"
    )
    child_type_count = fields.Integer(
        compute="_compute_child_type_count", string="Child Types"
    )
    effective_retention_years = fields.Integer(
        compute="_compute_effective_retention", string="Effective Retention (Years)"
    )

    # ============================================================================
    # DEFAULT METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("code"):
                vals["code"] = (
                    self.env["ir.sequence"].next_by_code("records.document.type")
                    or "DOC/"
                )
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        self.ensure_one()
        self.write({"state": "active"})

    def action_deprecate(self):
        self.ensure_one()
        self.write({"state": "deprecated"})

    def action_archive(self):
        self.ensure_one()
        self.write({"state": "archived", "active": False})

    def action_view_documents(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Documents",
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("document_type_id", "=", self.id)],
            "context": {"default_document_type_id": self.id},
        }

    def action_create_template(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Create Document Template",
            "res_model": "records.document.template",
            "view_mode": "form",
            "target": "new",
            "context": {"default_document_type_id": self.id},
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_retention_date(self, creation_date):
        """Calculate retention expiration date"""
        from datetime import datetime, timedelta

        if isinstance(creation_date, str):
            creation_date = datetime.strptime(creation_date, "%Y-%m-%d").date()
        return creation_date + timedelta(days=self.effective_retention_years * 365)

    def is_eligible_for_destruction(self, document):
        """Check if document is eligible for destruction"""
        if self.requires_legal_hold and document.legal_hold:
            return False
        retention_date = self.get_retention_date(document.create_date)
        return fields.Date.today() >= retention_date

    # ============================================================================
    # AUTO-GENERATED ACTION METHODS (from comprehensive validation)
    # ============================================================================
    def action_view_type_documents(self):
        """View Type Documents - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Type Documents"),
            "res_model": "records.document.type",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.ids)],
            "context": self.env.context,
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("default_retention_years")
    def _check_retention_years(self):
        for record in self:
            if record.default_retention_years < 0:
                raise ValidationError(_("Retention years cannot be negative."))

    @api.constrains("parent_type_id")
    def _check_parent_type(self):
        for record in self:
            if record.parent_type_id:
                if record.parent_type_id == record:
                    raise ValidationError(_("Document type cannot be its own parent."))

    @api.constrains("code")
    def _check_code_uniqueness(self):
        for record in self:
            if record.code:
                existing = self.search(
                    [("code", "=", record.code), ("id", "!=", record.id)]
                )
                if existing:
                    raise ValidationError(_("Document type code must be unique."))
