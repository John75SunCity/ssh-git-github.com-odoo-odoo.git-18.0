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
    retention_policy_id = fields.Many2one("records.retention.policy", string="Retention Policy", tracking=True)
    default_retention_years = fields.Integer(string="Default Retention (Years)", default=7)
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
    environmental_controls = fields.Boolean(string="Environmental Controls Required", default=False)
    max_box_weight = fields.Float(string="Max Box Weight (lbs)", default=40.0)

    # ============================================================================
    # WORKFLOW & PROCESSING
    # ============================================================================
    approval_required = fields.Boolean(string="Approval Required for Creation", default=False)
    auto_numbering = fields.Boolean(string="Auto Numbering", default=True)
    barcode_required = fields.Boolean(string="Barcode Required", default=True)
    digital_copy_required = fields.Boolean(string="Digital Copy Required", default=False)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    document_ids = fields.One2many("records.document", "document_type_id", string="Documents")
    parent_type_id = fields.Many2one("records.document.type", string="Parent Document Type")
    child_type_ids = fields.One2many("records.document.type", "parent_type_id", string="Child Document Types")

    # Mail framework fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTED FIELDS
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
                record.effective_retention_years = record.retention_policy_id.retention_years
            else:
                record.effective_retention_years = record.default_retention_years

    document_count = fields.Integer(compute="_compute_document_count", string="Document Count")
    child_type_count = fields.Integer(compute="_compute_child_type_count", string="Child Types")
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
                vals["code"] = self.env["ir.sequence"].next_by_code("records.document.type") or "DOC/"
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
                existing = self.search([("code", "=", record.code), ("id", "!=", record.id)])
                if existing:
                    raise ValidationError(_("Document type code must be unique."))
