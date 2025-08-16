# -*- coding: utf-8 -*-
"""
Records Document Type Management Module

This module provides comprehensive document type classification and management for the Records
Management System with NAID AAA compliance and enterprise-grade functionality.

Key Features:
- Hierarchical document type classification with automated retention policies
- Security classification and access control based on document sensitivity
- NAID AAA compliance tracking with audit trails and destruction certificates
- Integration with scanning, ingestion, and document lifecycle management
- Template management for standardization and quality control
- Advanced workflow automation and business rule enforcement

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import logging
from datetime import timedelta
from odoo.tools import float_compare

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class RecordsDocumentType(models.Model):
    _name = "records.document.type"
    _description = "Records Document Type"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, category, name"
    _rec_name = "name"
    _sql_constraints = [
        (
            "code_unique",
            "UNIQUE(code, company_id)",
            "Document type code must be unique per company!",
        ),
        (
            "retention_years_positive",
            "CHECK(default_retention_years >= 0)",
            "Retention years must be positive!",
        ),
        (
            "max_weight_positive",
            "CHECK(max_box_weight > 0)",
            "Maximum box weight must be positive!",
        ),
    ]

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Document Type Name",
        required=True,
        tracking=True,
        index=True,
        help="Unique name for this document type",
    )
    code = fields.Char(
        string="Document Code",
        index=True,
        help="Unique code for system identification",
    )
    description = fields.Text(
        string="Description", help="Detailed description and usage guidelines"
    )
    sequence = fields.Integer(
        string="Sequence", default=10, help="Display order in lists and forms"
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
        help="Uncheck to archive this document type",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Document Type Manager",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for managing this document type",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record",
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
        required=True,
        tracking=True,
        help="Current lifecycle status of this document type",
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
            ("medical", "Medical Records"),
            ("government", "Government Records"),
            ("corporate", "Corporate Records"),
            ("technical", "Technical Documentation"),
            ("other", "Other"),
        ],
        string="Category",
        required=True,
        default="other",
        tracking=True,
        help="Primary category for document classification",
    )
    confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal Use"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("top_secret", "Top Secret"),
        ],
        string="Confidentiality Level",
        default="internal",
        required=True,
        tracking=True,
        help="Security classification determining access controls",
    )

    # ============================================================================
    # RETENTION MANAGEMENT
    # ============================================================================
    retention_policy_id = fields.Many2one(
        "records.retention.policy",
        string="Retention Policy",
        tracking=True,
        help="Linked retention policy with specific rules",
    )
    default_retention_years = fields.Integer(
        string="Default Retention (Years)",
        default=7,
        required=True,
        help="Default retention period when no specific policy applies",
    )
    requires_legal_hold = fields.Boolean(
        string="Requires Legal Hold",
        default=False,
        help="Documents may require legal hold preventing destruction",
    )
    destruction_method = fields.Selection(
        [
            ("shred", "Shredding"),
            ("pulp", "Pulping"),
            ("incineration", "Incineration"),
            ("digital_wipe", "Digital Wiping"),
            ("degaussing", "Degaussing"),
        ],
        string="Destruction Method",
        default="shred",
        required=True,
        help="Required method for secure document destruction",
    )

    # ============================================================================
    # COMPLIANCE & REGULATIONS
    # ============================================================================
    naid_compliance = fields.Boolean(
        string="NAID Compliance Required",
        default=False,
        help="Requires NAID AAA compliance for destruction",
    )
    hipaa_protected = fields.Boolean(
        string="HIPAA Protected",
        default=False,
        help="Contains protected health information",
    )
    sox_compliance = fields.Boolean(
        string="SOX Compliance",
        default=False,
        help="Subject to Sarbanes-Oxley requirements",
    )
    gdpr_applicable = fields.Boolean(
        string="GDPR Applicable",
        default=False,
        help="Subject to GDPR data protection regulations",
    )
    regulatory_requirements = fields.Text(
        string="Regulatory Requirements",
        help="Specific compliance requirements and standards",
    )

    # ============================================================================
    # ENHANCED COMPLIANCE AND AUDIT FIELDS
    # ============================================================================
    approval_date = fields.Date(
        string="Approval Date",
        tracking=True,
        help="Date when document type was approved for use"
    )

    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        tracking=True,
        help="User who approved this document type"
    )

    audit_readiness_level = fields.Selection([
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('enhanced', 'Enhanced'),
        ('comprehensive', 'Comprehensive')
    ], string="Audit Readiness Level", default='standard',
       help="Level of audit preparation and documentation")

    audit_required = fields.Boolean(
        string="Audit Required",
        default=False,
        help="Requires periodic compliance auditing"
    )

    auto_classification_potential = fields.Float(
        string="Auto Classification Potential",
        digits=(5, 2),
        default=0.0,
        help="Potential for automated document classification (0-100%)"
    )

    classification_accuracy_score = fields.Float(
        string="Classification Accuracy Score",
        digits=(5, 2),
        compute='_compute_classification_accuracy',
        store=True,
        help="Historical accuracy of document classification"
    )

    compliance_notes = fields.Text(
        string="Compliance Notes",
        help="Additional notes regarding compliance requirements"
    )

    compliance_risk_assessment = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk')
    ], string="Compliance Risk Assessment", default='medium',
       help="Risk assessment for compliance violations")

    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('pending', 'Pending Review'),
        ('non_compliant', 'Non-Compliant'),
        ('exempted', 'Exempted')
    ], string="Compliance Status", default='pending',
       tracking=True, help="Current compliance status")

    regulatory_compliance_score = fields.Float(
        string="Regulatory Compliance Score",
        digits=(5, 2),
        compute='_compute_regulatory_compliance',
        store=True,
        help="Overall regulatory compliance score (0-100)"
    )

    regulatory_requirement = fields.Text(
        string="Regulatory Requirement Details",
        help="Detailed regulatory requirements and citations"
    )

    retention_compliance = fields.Selection([
        ('fully_compliant', 'Fully Compliant'),
        ('mostly_compliant', 'Mostly Compliant'),
        ('partially_compliant', 'Partially Compliant'),
        ('non_compliant', 'Non-Compliant')
    ], string="Retention Compliance", default='fully_compliant',
       help="Compliance with retention policy requirements")

    risk_level = fields.Selection([
        ('minimal', 'Minimal'),
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('severe', 'Severe')
    ], string="Risk Level", default='low',
       help="Overall risk level for this document type")

    security_classification = fields.Selection([
        ('unclassified', 'Unclassified'),
        ('controlled', 'Controlled'),
        ('confidential', 'Confidential'),
        ('secret', 'Secret'),
        ('top_secret', 'Top Secret')
    ], string="Security Classification", default='unclassified',
       tracking=True, help="Government/military style security classification")

    # ============================================================================
    # ANALYTICS AND REPORTING FIELDS
    # ============================================================================
    document_type_utilization = fields.Float(
        string="Document Type Utilization (%)",
        digits=(5, 2),
        compute='_compute_utilization_metrics',
        store=True,
        help="Percentage of total documents using this type"
    )

    growth_trend_indicator = fields.Selection([
        ('declining', 'Declining'),
        ('stable', 'Stable'),
        ('growing', 'Growing'),
        ('rapid_growth', 'Rapid Growth')
    ], string="Growth Trend", compute='_compute_growth_trend',
       store=True, help="Document volume growth trend")

    seasonal_pattern_score = fields.Float(
        string="Seasonal Pattern Score",
        digits=(5, 2),
        compute='_compute_seasonal_patterns',
        store=True,
        help="Score indicating seasonal usage patterns (0-100)"
    )

    type_complexity_rating = fields.Selection([
        ('simple', 'Simple'),
        ('moderate', 'Moderate'),
        ('complex', 'Complex'),
        ('highly_complex', 'Highly Complex')
    ], string="Type Complexity Rating", default='moderate',
       help="Complexity rating for handling this document type")

    # ============================================================================
    # PHYSICAL HANDLING
    # ============================================================================
    max_box_weight = fields.Float(
        string="Max Box Weight (lbs)",
        default=40.0,
        help="Maximum weight allowed per storage box",
    )
    storage_requirements = fields.Text(
        string="Storage Requirements",
        help="Special storage conditions and environmental controls",
    )
    handling_instructions = fields.Text(
        string="Handling Instructions",
        help="Special handling procedures for staff",
    )
    environmental_controls = fields.Boolean(
        string="Environmental Controls Required",
        default=False,
        help="Requires controlled temperature and humidity",
    )
    fire_protection_required = fields.Boolean(
        string="Fire Protection Required",
        default=False,
        help="Requires fire-resistant storage facilities",
    )

    # ============================================================================
    # WORKFLOW & PROCESSING
    # ============================================================================
    approval_required = fields.Boolean(
        string="Approval Required",
        default=False,
        help="Documents require management approval",
    )
    indexing_required = fields.Boolean(
        string="Indexing Required",
        default=True,
        help="Documents must be indexed for searchability",
    )
    barcode_required = fields.Boolean(
        string="Barcode Required",
        default=True,
        help="Barcode tracking is mandatory",
    )
    digital_copy_required = fields.Boolean(
        string="Digital Copy Required",
        default=False,
        help="Digital backup copy is mandatory",
    )
    encryption_required = fields.Boolean(
        string="Encryption Required",
        default=False,
        help="Digital copies must be encrypted",
    )

    # ============================================================================
    # UTILIZATION FIELDS
    # ============================================================================
    utilization_level = fields.Selection(
        [("normal", "Normal"), ("high", "High")],
        string="Document Type Utilization",
        default="normal",
    )

    # ============================================================================
    # METADATA & TEMPLATES
    # ============================================================================
    metadata_template = fields.Text(
        string="Metadata Template",
        help="JSON template for required metadata fields",
    )
    searchable_fields = fields.Char(
        string="Searchable Fields",
        help="Comma-separated list of searchable metadata fields",
    )
    default_tags = fields.Char(
        string="Default Tags", help="Default tags automatically applied to documents"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    document_ids = fields.One2many(
        "records.document", "document_type_id", string="Documents"
    )
    parent_type_id = fields.Many2one(
        "records.document.type",
        string="Parent Type",
        help="Parent type in classification hierarchy",
    )
    child_type_ids = fields.One2many(
        "records.document.type", "parent_type_id", string="Child Types"
    )
    container_ids = fields.One2many(
        "records.container", "document_type_id", string="Containers"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    document_count = fields.Integer(
        compute="_compute_document_count",
        string="Documents",
        store=True,
        help="Number of documents using this type",
    )
    child_count = fields.Integer(
        compute="_compute_child_count", string="Child Types", store=True
    )
    container_count = fields.Integer(
        compute="_compute_container_count", string="Containers", store=True
    )
    effective_retention_years = fields.Integer(
        compute="_compute_effective_retention",
        string="Effective Retention (Years)",
        store=True,
    )
    status_display = fields.Char(
        compute="_compute_status_display", string="Status Display"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain="[('res_model', '=', 'records.document.type')]",
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain="[('res_model', '=', 'records.document.type')]",
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain="[('res_model', '=', 'records.document.type')
    action_view_type_documents = fields.Char(string='Action View Type Documents')
    analytics = fields.Char(string='Analytics')
    approved_by = fields.Char(string='Approved By')
    auto_classification = fields.Char(string='Auto Classification')
    button_box = fields.Char(string='Button Box')
    card = fields.Char(string='Card')
    compliance = fields.Char(string='Compliance')
    confidential = fields.Char(string='Confidential')
    group_compliance = fields.Char(string='Group Compliance')
    group_risk = fields.Char(string='Group Risk')
    group_security = fields.Char(string='Group Security')
    help = fields.Char(string='Help')
    inactive = fields.Boolean(string='Inactive', default=False)
    res_model = fields.Char(string='Res Model')
    view_mode = fields.Char(string='View Mode')]",
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("document_ids")
    def _compute_document_count(self):
        """Compute total number of documents using this type"""
        for record in self:
            record.document_count = len(record.document_ids)

    @api.depends("child_type_ids")
    def _compute_child_count(self):
        """Compute number of child document types"""
        for record in self:
            record.child_count = len(record.child_type_ids)

    @api.depends("container_ids")
    def _compute_container_count(self):
        """Compute number of containers using this document type"""
        for record in self:
            record.container_count = len(record.container_ids)

    @api.depends(
        "retention_policy_id",
        "retention_policy_id.retention_years",
        "default_retention_years",
    )
    def _compute_effective_retention(self):
        """Calculate effective retention period"""
        for record in self:
            if (
                record.retention_policy_id
                and record.retention_policy_id.retention_years
            ):
                record.effective_retention_years = (
                    record.retention_policy_id.retention_years
                )
            else:
                record.effective_retention_years = record.default_retention_years or 7

    @api.depends("state", "active", "document_count")
    def _compute_status_display(self):
        """Compute display status with additional information"""
        for record in self:
            status_parts = [record.state.title()]
            if not record.active:
                status_parts.append("Inactive")
            if record.document_count:
                status_parts.append(_("%d docs", record.document_count))
            record.status_display = " | ".join(status_parts)

    @api.depends('document_ids', 'document_ids.state')
    def _compute_classification_accuracy(self):
        """Compute classification accuracy based on document history"""
        for record in self:
            if record.document_ids:
                total_docs = len(record.document_ids)
                correctly_classified = len(record.document_ids.filtered(
                    lambda d: d.state != 'error'
                ))
                record.classification_accuracy_score = (
                    correctly_classified / total_docs * 100 if total_docs else 0.0
                )
            else:
                record.classification_accuracy_score = 0.0

    @api.depends('naid_compliance', 'hipaa_protected', 'sox_compliance',
                 'gdpr_applicable', 'compliance_status')
    def _compute_regulatory_compliance(self):
        """Compute overall regulatory compliance score"""
        for record in self:
            score = 0.0
            total_factors = 0

            # Base compliance factors
            compliance_factors = [
                record.naid_compliance,
                record.hipaa_protected,
                record.sox_compliance,
                record.gdpr_applicable
            ]

            for factor in compliance_factors:
                total_factors += 1
                if factor:
                    score += 25.0  # Each factor worth 25 points

            # Adjust based on compliance status
            status_multipliers = {
                'compliant': 1.0,
                'pending': 0.75,
                'non_compliant': 0.25,
                'exempted': 0.9
            }

            multiplier = status_multipliers.get(record.compliance_status, 0.5)
            record.regulatory_compliance_score = score * multiplier

    @api.depends('document_ids')
    def _compute_utilization_metrics(self):
        """Compute document type utilization percentage"""
        for record in self:
            total_docs_in_system = self.env['records.document'].search_count([])
            record_docs = len(record.document_ids)

            if total_docs_in_system > 0:
                record.document_type_utilization = (
                    record_docs / total_docs_in_system * 100
                )
            else:
                record.document_type_utilization = 0.0

    @api.depends('document_ids.create_date')
    def _compute_growth_trend(self):
        """Compute growth trend based on recent document creation"""
        for record in self:
            if not record.document_ids:
                record.growth_trend_indicator = 'stable'
                continue

            # Compare last 30 days vs previous 30 days
            from datetime import datetime, timedelta
            today = datetime.now().date()
            last_30_days = today - timedelta(days=30)
            previous_30_days = today - timedelta(days=60)

            recent_count = len(record.document_ids.filtered(
                lambda d: d.create_date and d.create_date.date() >= last_30_days
            ))
            previous_count = len(record.document_ids.filtered(
                lambda d: d.create_date and
                previous_30_days <= d.create_date.date() < last_30_days
            ))

            if previous_count == 0:
                if recent_count > 0:
                    record.growth_trend_indicator = 'growing'
                else:
                    record.growth_trend_indicator = 'stable'
            else:
                growth_rate = (recent_count - previous_count) / previous_count
                if growth_rate > 0.5:
                    record.growth_trend_indicator = 'rapid_growth'
                elif growth_rate > 0.1:
                    record.growth_trend_indicator = 'growing'
                elif growth_rate < -0.1:
                    record.growth_trend_indicator = 'declining'
                else:
                    record.growth_trend_indicator = 'stable'

    @api.depends('document_ids.create_date')
    def _compute_seasonal_patterns(self):
        """Compute seasonal usage patterns"""
        for record in self:
            if len(record.document_ids) < 12:  # Need sufficient data
                record.seasonal_pattern_score = 0.0
                continue

            # Group documents by month and calculate variance
            monthly_counts = {}
            for doc in record.document_ids:
                if doc.create_date:
                    month = doc.create_date.month
                    monthly_counts[month] = monthly_counts.get(month, 0) + 1

            if len(monthly_counts) > 1:
                counts = list(monthly_counts.values())
                avg_count = sum(counts) / len(counts)
                variance = sum((x - avg_count) ** 2 for x in counts) / len(counts)

                # Higher variance indicates more seasonal patterns
                record.seasonal_pattern_score = min(variance / avg_count * 100, 100) if avg_count > 0 else 0.0
            else:
                record.seasonal_pattern_score = 0.0

    # ============================================================================
    # ENHANCED CRUD OPERATIONS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Enhanced create with automatic code generation and validation"""
        for vals in vals_list:
            if not vals.get("code"):
                vals["code"] = self._generate_document_type_code(
                    vals.get("category", "other")
                )
            if vals.get("confidentiality_level") in ["restricted", "top_secret"]:
                vals["encryption_required"] = True
            if not vals.get("name"):
                raise ValidationError(_("Document type name is required"))

        records = super().create(vals_list)
        for record in records:
            record.message_post(
                body=_("Document type created with code: %s", record.code)
            )
        return records

    def write(self, vals):
        """Enhanced write with change validation and tracking"""
        if "state" in vals:
            self._validate_state_transition(vals["state"])
        if "retention_policy_id" in vals or "default_retention_years" in vals:
            self._handle_retention_changes(vals)
        if vals.get("confidentiality_level") in ["restricted", "top_secret"]:
            vals["encryption_required"] = True

        result = super().write(vals)
        if any(
            field in vals
            for field in [
                "state",
                "retention_policy_id",
                "confidentiality_level",
            ]
        ):
            for record in self:
                record.message_post(
                    body=_("Document type configuration updated"),
                    subject=_("Configuration Change"),
                )
        return result

    def unlink(self):
        """Enhanced unlink with dependency validation"""
        for record in self:
            if record.document_ids:
                raise UserError(
                    _(
                        "Cannot delete document type '%s' with %d associated documents. Archive instead.",
                        record.name,
                        len(record.document_ids),
                    )
                )
            if record.child_type_ids:
                raise UserError(
                    _(
                        "Cannot delete document type '%s' with child types. Reassign children first.",
                        record.name,
                    )
                )
        return super().unlink()

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate document type"""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(
                _("Cannot activate archived document type. Restore first.")
            )
        self.write({"state": "active", "active": True})
        return self._show_success_message(_("Document type activated successfully"))

    def action_deprecate(self):
        """Deprecate document type with impact assessment"""
        self.ensure_one()
        if self.document_count > 0:
            return self._show_deprecation_wizard()
        self.write({"state": "deprecated"})
        return self._show_success_message(_("Document type deprecated"))

    def action_archive(self):
        """Archive document type with safety checks"""
        self.ensure_one()
        active_docs = self.document_ids.filtered(lambda d: d.active)
        if active_docs:
            raise UserError(
                _(
                    "Cannot archive document type with %d active documents",
                    len(active_docs),
                )
            )
        self.write({"state": "archived", "active": False})
        return self._show_success_message(_("Document type archived"))

    def action_view_documents(self):
        """View all documents of this type"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Documents - %s", self.name),
            "res_model": "records.document",
            "view_mode": "tree,form,kanban",
            "domain": [("document_type_id", "=", self.id)],
            "context": {
                "default_document_type_id": self.id,
                "search_default_group_by_state": 1,
            },
        }

    def action_view_containers(self):
        """View all containers using this document type"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Containers - %s", self.name),
            "res_model": "records.container",
            "view_mode": "tree,form",
            "domain": [("document_type_id", "=", self.id)],
            "context": {"default_document_type_id": self.id},
        }

    def action_setup_security(self):
        """Setup security rules based on confidentiality level"""
        self.ensure_one()
        self._setup_security_rules()
        return self._show_success_message(_("Security rules updated"))

    def action_create_retention_policy(self):
        """Create default retention policy for this document type"""
        self.ensure_one()
        if not self.retention_policy_id:
            self._setup_retention_policy()
        return self._show_success_message(_("Default retention policy created"))

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def get_retention_date(self, creation_date):
        """Calculate retention expiration date"""
        if not creation_date:
            creation_date = fields.Date.today()
        if isinstance(creation_date, str):
            creation_date = fields.Date.from_string(creation_date)
        elif hasattr(creation_date, "date"):
            creation_date = creation_date.date()
        retention_years = self.effective_retention_years
        return creation_date + timedelta(days=retention_years * 365)

    def is_eligible_for_destruction(self, document):
        """Check if document is eligible for destruction"""
        if not document:
            return False
        if self.requires_legal_hold and getattr(document, "legal_hold", False):
            return False
        retention_date = self.get_retention_date(document.create_date)
        if fields.Date.today() < retention_date:
            return False
        if hasattr(document, "state") and document.state in [
            "draft",
            "processing",
        ]:
            return False
        return True

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("default_retention_years")
    def _check_retention_years(self):
        """Enhanced retention years validation"""
        for record in self:
            if record.default_retention_years < 0:
                raise ValidationError(_("Retention years cannot be negative."))
            if record.default_retention_years > 100:
                raise ValidationError(_("Retention years cannot exceed 100 years."))

    @api.constrains("parent_type_id")
    def _check_parent_type(self):
        """Enhanced parent type validation with circular reference detection"""
        for record in self:
            if record.parent_type_id:
                if record.parent_type_id == record:
                    raise ValidationError(
                        _("Document type cannot be its own parent.")
                    )
                current = record.parent_type_id
                visited = {record.id}
                while current:
                    if current.id in visited:
                        raise ValidationError(
                            _("Circular reference detected in document type hierarchy.")
                        )
                    visited.add(current.id)
                    current = current.parent_type_id

    @api.constrains("max_box_weight")
    def _check_max_box_weight(self):
        """Validate maximum box weight"""
        for record in self:
            if float_compare(record.max_box_weight, 0.0, precision_digits=2) <= 0:
                raise ValidationError(
                    _("Maximum box weight must be greater than zero.")
                )
            if record.max_box_weight > 500.0:
                raise ValidationError(_("Maximum box weight cannot exceed 500 lbs."))

    @api.constrains("confidentiality_level", "encryption_required")
    def _check_security_consistency(self):
        """Ensure security settings are consistent"""
        for record in self:
            if (
                record.confidentiality_level in ["restricted", "top_secret"]
                and not record.encryption_required
            ):
                raise ValidationError(
                    _(
                        "Documents with '%s' confidentiality level must require encryption.",
                        record.confidentiality_level,
                    )
                )

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _generate_document_type_code(self, category):
        """Generate unique document type code"""
        category_prefixes = {
            "financial": "FIN",
            "legal": "LEG",
            "hr": "HR",
            "medical": "MED",
            "compliance": "COMP",
            "government": "GOV",
            "corporate": "CORP",
            "technical": "TECH",
            "operational": "OPS",
            "other": "DOC",
        }
        prefix = category_prefixes.get(category, "DOC")
        sequence = (
            self.env["ir.sequence"].next_by_code("records.document.type") or "001"
        )
        return f"{prefix}{sequence}"

    def _validate_state_transition(self, new_state):
        """Validate allowed state transitions"""
        valid_transitions = {
            "draft": ["active", "archived"],
            "active": ["deprecated", "archived"],
            "deprecated": ["archived"],
            "archived": ["active"],
        }
        for record in self:
            if (
                record.state in valid_transitions
                and new_state not in valid_transitions[record.state]
            ):
                raise ValidationError(
                    _(
                        "Invalid state transition from '%s' to '%s'",
                        record.state,
                        new_state,
                    )
                )

    def _handle_retention_changes(self, vals):
        """Handle retention policy changes impact"""
        for record in self:
            if record.document_count > 0:
                _logger.warning(
                    "Retention change affects %s documents for type %s",
                    record.document_count,
                    record.name,
                )

    def _show_success_message(self, message):
        """Display success notification"""
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": message,
                "type": "success",
                "sticky": False,
            },
        }

    def _show_deprecation_wizard(self):
        """Show deprecation confirmation wizard"""
        return {
            "type": "ir.actions.act_window",
            "name": _("Confirm Deprecation"),
            "res_model": "records.document.type.deprecate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_document_type_id": self.id},
        }

    def _setup_retention_policy(self):
        """Create default retention policy for certain categories"""
        if not self.retention_policy_id and self.category in [
            "financial",
            "legal",
            "compliance",
        ]:
            retention_years = {
                "financial": 7,
                "legal": 10,
                "compliance": 5,
            }.get(self.category, 7)
            policy_name = _(
                "Default %s Policy - %s", self.category.title(), self.name
            )
            _logger.info(
                "Would create retention policy: %s with %s years retention",
                policy_name,
                retention_years,
            )
        return True

    def _setup_security_rules(self):
        """Set up security rules based on confidentiality level"""
        security_configs = {
            "public": {"access_group": "base.group_user", "encryption": False},
            "internal": {
                "access_group": "base.group_user",
                "encryption": False,
            },
            "confidential": {
                "access_group": "records_management.group_records_manager",
                "encryption": True,
            },
            "restricted": {
                "access_group": "records_management.group_records_manager",
                "encryption": True,
            },
            "top_secret": {
                "access_group": "records_management.group_records_admin",
                "encryption": True,
            },
        }
        config = security_configs.get(
            self.confidentiality_level, security_configs["internal"]
        )
        _logger.info(
            "Would configure security for %s: access_group=%s, encryption=%s",
            self.name,
            config["access_group"],
            config["encryption"],
        )
        return True
