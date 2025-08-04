# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class RecordsRetentionPolicy(models.Model):
    _name = "records.retention.policy"
    _description = "Records Retention Policy"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Policy Name", required=True, tracking=True, index=True)
    code = fields.Char(string="Policy Code", index=True, tracking=True)
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
        string="Policy Owner",
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
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # RETENTION CONFIGURATION
    # ============================================================================
    retention_years = fields.Integer(string="Retention Period (Years)", required=True, default=7)
    retention_months = fields.Integer(string="Additional Months", default=0)
    retention_days = fields.Integer(string="Additional Days", default=0)

    # Trigger events
    trigger_event = fields.Selection(
        [
            ("creation", "Document Creation"),
            ("closure", "Document Closure"),
            ("last_access", "Last Access"),
            ("fiscal_year_end", "Fiscal Year End"),
            ("contract_end", "Contract End"),
            ("custom", "Custom Event"),
        ],
        string="Trigger Event",
        default="creation",
        required=True,
    )

    # ============================================================================
    # POLICY SCOPE
    # ============================================================================
    policy_type = fields.Selection(
        [
            ("general", "General Policy"),
            ("legal", "Legal Requirements"),
            ("regulatory", "Regulatory Compliance"),
            ("business", "Business Policy"),
            ("tax", "Tax Requirements"),
            ("custom", "Custom Policy"),
        ],
        string="Policy Type",
        default="general",
        tracking=True,
    )

    document_types = fields.Many2many("records.document.type", string="Applicable Document Types")
    record_categories = fields.Char(string="Record Categories")
    exclusions = fields.Text(string="Exclusions")

    # ============================================================================
    # COMPLIANCE & REGULATIONS
    # ============================================================================
    regulatory_basis = fields.Text(string="Regulatory Basis")
    legal_requirements = fields.Text(string="Legal Requirements")
    compliance_standards = fields.Char(string="Compliance Standards")

    # Regulatory flags
    sox_requirement = fields.Boolean(string="SOX Requirement", default=False)
    hipaa_requirement = fields.Boolean(string="HIPAA Requirement", default=False)
    gdpr_requirement = fields.Boolean(string="GDPR Requirement", default=False)
    industry_specific = fields.Boolean(string="Industry Specific", default=False)

    # ============================================================================
    # DESTRUCTION RULES
    # ============================================================================
    destruction_required = fields.Boolean(string="Destruction Required", default=True)
    destruction_method = fields.Selection(
        [
            ("shred", "Shredding"),
            ("pulp", "Pulping"),
            ("incineration", "Incineration"),
            ("digital_wipe", "Digital Wiping"),
            ("secure_delete", "Secure Deletion"),
        ],
        string="Destruction Method",
        default="shred",
    )

    auto_destruction = fields.Boolean(string="Auto Destruction", default=False)
    destruction_approval_required = fields.Boolean(string="Destruction Approval Required", default=True)
    certificate_required = fields.Boolean(string="Certificate of Destruction Required", default=True)

    # ============================================================================
    # LEGAL HOLD PROVISIONS
    # ============================================================================
    legal_hold_override = fields.Boolean(string="Legal Hold Can Override", default=True)
    litigation_hold_period = fields.Integer(string="Litigation Hold Period (Years)", default=0)
    hold_notification_required = fields.Boolean(string="Hold Notification Required", default=True)

    # ============================================================================
    # REVIEW & MAINTENANCE
    # ============================================================================
    review_frequency = fields.Selection(
        [
            ("annual", "Annual"),
            ("biannual", "Bi-Annual"),
            ("quarterly", "Quarterly"),
            ("as_needed", "As Needed"),
        ],
        string="Review Frequency",
        default="annual",
    )

    last_review_date = fields.Date(string="Last Review Date")
    next_review_date = fields.Date(string="Next Review Date", compute="_compute_next_review_date", store=True)
    review_notes = fields.Text(string="Review Notes")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    policy_rules = fields.One2many("records.retention.rule", "policy_id", string="Retention Rules")
    affected_documents = fields.One2many("records.document", "retention_policy_id", string="Affected Documents")

    # Mail framework fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("last_review_date", "review_frequency")
    def _compute_next_review_date(self):
        for record in self:
            if record.last_review_date and record.review_frequency:
                if record.review_frequency == "annual":
                    record.next_review_date = record.last_review_date + relativedelta(years=1)
                elif record.review_frequency == "biannual":
                    record.next_review_date = record.last_review_date + relativedelta(months=6)
                elif record.review_frequency == "quarterly":
                    record.next_review_date = record.last_review_date + relativedelta(months=3)
                else:
                    record.next_review_date = False
            else:
                record.next_review_date = False

    @api.depends("retention_years", "retention_months", "retention_days")
    def _compute_total_retention_days(self):
        for record in self:
            total_days = record.retention_years * 365 + record.retention_months * 30 + record.retention_days
            record.total_retention_days = total_days

    @api.depends("policy_rules")
    def _compute_rule_count(self):
        for record in self:
            record.rule_count = len(record.policy_rules)

    @api.depends("affected_documents")
    def _compute_document_count(self):
        for record in self:
            record.document_count = len(record.affected_documents)

    total_retention_days = fields.Integer(compute="_compute_total_retention_days", string="Total Retention (Days)")
    rule_count = fields.Integer(compute="_compute_rule_count", string="Rules")
    document_count = fields.Integer(compute="_compute_document_count", string="Documents")

    # ============================================================================
    # DEFAULT METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("code"):
                vals["code"] = self.env["ir.sequence"].next_by_code("records.retention.policy") or "RRP/"
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        self.ensure_one()
        self.write({"state": "active"})

    def action_deactivate(self):
        self.ensure_one()
        self.write({"state": "inactive"})

    def action_review(self):
        self.ensure_one()
        self.write({"last_review_date": fields.Date.today(), "review_notes": ""})

    def action_view_affected_documents(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Affected Documents",
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("retention_policy_id", "=", self.id)],
            "context": {"default_retention_policy_id": self.id},
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def calculate_destruction_date(self, reference_date):
        """Calculate destruction date based on policy"""
        if not reference_date:
            return False

        if isinstance(reference_date, str):
            reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()

        return reference_date + relativedelta(
            years=self.retention_years,
            months=self.retention_months,
            days=self.retention_days,
        )

    def is_eligible_for_destruction(self, document):
        """Check if document is eligible for destruction"""
        if not self.destruction_required:
            return False

        if document.legal_hold:
            return False

        destruction_date = self.calculate_destruction_date(document.create_date)
        return fields.Date.today() >= destruction_date

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("retention_years", "retention_months", "retention_days")
    def _check_retention_period(self):
        for record in self:
            if record.retention_years < 0 or record.retention_months < 0 or record.retention_days < 0:
                raise ValidationError(_("Retention periods cannot be negative."))

            if record.retention_years == 0 and record.retention_months == 0 and record.retention_days == 0:
                raise ValidationError(_("At least one retention period must be specified."))

    @api.constrains("code")
    def _check_code_uniqueness(self):
        for record in self:
            if record.code:
                existing = self.search([("code", "=", record.code), ("id", "!=", record.id)])
                if existing:
                    raise ValidationError(_("Policy code must be unique."))
