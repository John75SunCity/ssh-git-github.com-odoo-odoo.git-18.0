# -*- coding: utf-8 -*-
"""
Records Retention Policy Management Module

This module provides comprehensive retention policy management for the Records Management
System. It implements enterprise-grade policy configuration with automated compliance
tracking, regulatory alignment, and document lifecycle management.

Key Features:
- Configurable retention periods with multiple time units (years, months, days)
- Regulatory compliance tracking (SOX, HIPAA, GDPR, industry-specific)
- Automated destruction scheduling with approval workflows
- Legal hold integration and override capabilities
- Policy review and maintenance scheduling
- Document type and category-specific rules
- Chain of custody integration for NAID AAA compliance

Business Processes:
1. Policy Creation: Define retention rules with regulatory basis
2. Document Assignment: Apply policies to document types and categories
3. Compliance Monitoring: Track regulatory requirements and deadlines
4. Automated Scheduling: Calculate destruction dates and trigger workflows
5. Review Cycles: Schedule regular policy reviews and updates
6. Exception Handling: Manage legal holds and special circumstances

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

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
    name = fields.Char(
        string="Policy Name", 
        required=True, 
        tracking=True, 
        index=True,
        help="Name of the retention policy"
    )
    code = fields.Char(
        string="Policy Code", 
        index=True, 
        tracking=True,
        help="Unique policy identifier code"
    )
    description = fields.Text(
        string="Description",
        help="Detailed description of policy purpose and scope"
    )
    sequence = fields.Integer(
        string="Sequence", 
        default=10,
        help="Display order for policies"
    )
    active = fields.Boolean(
        string="Active", 
        default=True,
        tracking=True
    )
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
    state = fields.Selection([
        ("draft", "Draft"),
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("archived", "Archived"),
    ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current policy status"
    )

    # ============================================================================
    # RETENTION CONFIGURATION
    # ============================================================================
    retention_years = fields.Integer(
        string="Retention Period (Years)", 
        required=True, 
        default=7,
        help="Primary retention period in years"
    )
    retention_months = fields.Integer(
        string="Additional Months", 
        default=0,
        help="Additional retention period in months"
    )
    retention_days = fields.Integer(
        string="Additional Days", 
        default=0,
        help="Additional retention period in days"
    )

    # Trigger events
    trigger_event = fields.Selection([
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
        tracking=True,
        help="Event that triggers the retention period"
    )

    # ============================================================================
    # POLICY SCOPE
    # ============================================================================
    policy_type = fields.Selection([
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
        help="Category of retention policy"
    )
    document_type_ids = fields.Many2many(
        "records.document.type", 
        string="Applicable Document Types",
        help="Document types this policy applies to"
    )
    record_categories = fields.Char(
        string="Record Categories",
        help="Comma-separated list of record categories"
    )
    exclusions = fields.Text(
        string="Exclusions",
        help="Documents or conditions excluded from this policy"
    )

    # ============================================================================
    # COMPLIANCE & REGULATIONS
    # ============================================================================
    regulatory_basis = fields.Text(
        string="Regulatory Basis",
        help="Legal or regulatory foundation for this policy"
    )
    legal_requirements = fields.Text(
        string="Legal Requirements",
        help="Specific legal requirements this policy addresses"
    )
    compliance_standards = fields.Char(
        string="Compliance Standards",
        help="Standards this policy helps meet (ISO, NIST, etc.)"
    )

    # Regulatory flags
    sox_requirement = fields.Boolean(
        string="SOX Requirement", 
        default=False,
        help="Subject to Sarbanes-Oxley requirements"
    )
    hipaa_requirement = fields.Boolean(
        string="HIPAA Requirement", 
        default=False,
        help="Subject to HIPAA requirements"
    )
    gdpr_requirement = fields.Boolean(
        string="GDPR Requirement", 
        default=False,
        help="Subject to GDPR requirements"
    )
    industry_specific = fields.Boolean(
        string="Industry Specific", 
        default=False,
        help="Industry-specific regulatory requirements"
    )

    # ============================================================================
    # DESTRUCTION RULES
    # ============================================================================
    destruction_required = fields.Boolean(
        string="Destruction Required", 
        default=True,
        help="Whether documents must be destroyed after retention period"
    )
    destruction_method = fields.Selection([
        ("shred", "Shredding"),
        ("pulp", "Pulping"),
        ("incineration", "Incineration"),
        ("digital_wipe", "Digital Wiping"),
        ("secure_delete", "Secure Deletion"),
    ],
        string="Destruction Method",
        default="shred",
        help="Method for document destruction"
    )
    auto_destruction = fields.Boolean(
        string="Auto Destruction", 
        default=False,
        help="Automatically schedule destruction when eligible"
    )
    destruction_approval_required = fields.Boolean(
        string="Destruction Approval Required", 
        default=True,
        help="Require approval before destruction"
    )
    certificate_required = fields.Boolean(
        string="Certificate of Destruction Required", 
        default=True,
        help="Generate destruction certificate"
    )

    # ============================================================================
    # LEGAL HOLD PROVISIONS
    # ============================================================================
    legal_hold_override = fields.Boolean(
        string="Legal Hold Can Override", 
        default=True,
        help="Legal holds can suspend this policy"
    )
    litigation_hold_period = fields.Integer(
        string="Litigation Hold Period (Years)", 
        default=0,
        help="Extended retention during litigation"
    )
    hold_notification_required = fields.Boolean(
        string="Hold Notification Required", 
        default=True,
        help="Notify stakeholders when hold is applied"
    )

    # ============================================================================
    # REVIEW & MAINTENANCE
    # ============================================================================
    review_frequency = fields.Selection([
        ("annual", "Annual"),
        ("biannual", "Bi-Annual"),
        ("quarterly", "Quarterly"),
        ("as_needed", "As Needed"),
    ],
        string="Review Frequency",
        default="annual",
        help="How often this policy should be reviewed"
    )
    last_review_date = fields.Date(
        string="Last Review Date",
        tracking=True,
        help="Date of last policy review"
    )
    next_review_date = fields.Date(
        string="Next Review Date", 
        compute="_compute_next_review_date", 
        store=True,
        help="Calculated next review date"
    )
    review_notes = fields.Text(
        string="Review Notes",
        help="Notes from the last policy review"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    policy_rules = fields.One2many(
        "records.retention.rule", 
        "policy_id", 
        string="Retention Rules",
        help="Specific rules within this policy"
    )
    affected_documents = fields.One2many(
        "records.document", 
        "retention_policy_id", 
        string="Affected Documents",
        help="Documents governed by this policy"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    total_retention_days = fields.Integer(
        compute="_compute_total_retention_days", 
        string="Total Retention (Days)",
        help="Total retention period in days"
    )
    rule_count = fields.Integer(
        compute="_compute_rule_count", 
        string="Rules",
        help="Number of rules in this policy"
    )
    document_count = fields.Integer(
        compute="_compute_document_count", 
        string="Documents",
        help="Number of documents using this policy"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("last_review_date", "review_frequency")
    def _compute_next_review_date(self):
        """Calculate next review date based on frequency"""
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
        """Calculate total retention period in days"""
        for record in self:
            total_days = (
                record.retention_years * 365
                + record.retention_months * 30
                + record.retention_days
            )
            record.total_retention_days = total_days

    @api.depends("policy_rules")
    def _compute_rule_count(self):
        """Count policy rules"""
        for record in self:
            record.rule_count = len(record.policy_rules)

    @api.depends("affected_documents")
    def _compute_document_count(self):
        """Count affected documents"""
        for record in self:
            record.document_count = len(record.affected_documents)

    # ============================================================================
    # ODOO FRAMEWORK METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set policy code"""
        for vals in vals_list:
            if not vals.get("code"):
                sequence = self.env["ir.sequence"].next_by_code("records.retention.policy")
                vals["code"] = sequence or f"RRP-{fields.Date.today().strftime('%Y%m%d')}"
        return super().create(vals_list)

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    )

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.name
            if record.code:
                name = f"[{record.code}] {name}"
            result.append((record.id, name))
        return result

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate the policy"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft policies can be activated"))
        
        self.write({"state": "active"})
        self.message_post(body=_("Policy activated"))

    def action_deactivate(self):
        """Deactivate the policy"""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active policies can be deactivated"))
        
        self.write({"state": "inactive"})
        self.message_post(body=_("Policy deactivated"))

    def action_review(self):
        """Mark policy as reviewed"""
        self.ensure_one()
        self.write({
            "last_review_date": fields.Date.today(),
            "review_notes": ""
        })
        self.message_post(body=_("Policy reviewed on %s") % fields.Date.today())

    def action_view_affected_documents(self):
        """View documents affected by this policy"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Affected Documents"),
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("retention_policy_id", "=", self.id)],
            "context": {"default_retention_policy_id": self.id},
        }

    def action_view_rules(self):
        """View policy rules"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Policy Rules"),
            "res_model": "records.retention.rule",
            "view_mode": "tree,form",
            "domain": [("policy_id", "=", self.id)],
            "context": {"default_policy_id": self.id},
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def calculate_destruction_date(self, reference_date):
        """Calculate destruction date based on policy"""
        self.ensure_one()
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
        self.ensure_one()
        if not self.destruction_required:
            return False

        if document.legal_hold:
            return False

        destruction_date = self.calculate_destruction_date(document.created_date)
        return destruction_date and fields.Date.today() >= destruction_date

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("retention_years", "retention_months", "retention_days")
    def _check_retention_period(self):
        """Validate retention periods"""
        for record in self:
            if (record.retention_years < 0 or 
                record.retention_months < 0 or 
                record.retention_days < 0):
                raise ValidationError(_("Retention periods cannot be negative"))
            
            if (record.retention_years == 0 and 
                record.retention_months == 0 and 
                record.retention_days == 0):
                raise ValidationError(_("At least one retention period must be specified"))

    @api.constrains("code")
    def _check_code_uniqueness(self):
        """Ensure policy codes are unique"""
        for record in self:
            if record.code:
                existing = self.search([
                    ("code", "=", record.code),
                    ("id", "!=", record.id),
                    ("company_id", "=", record.company_id.id)
                ])
                if existing:
                    raise ValidationError(_("Policy code must be unique within the company"))

    # ============================================================================
    # CRON METHODS
    # ============================================================================
    @api.model
    def check_review_dates(self):
        """Cron job to check for policies due for review"""
        overdue_policies = self.search([
            ("state", "=", "active"),
            ("next_review_date", "<=", fields.Date.today()),
            ("review_frequency", "!=", "as_needed")
        ])
        
        for policy in overdue_policies:
            policy.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Policy Review Due: %s") % policy.name,
                note=_("This retention policy is due for review according to the scheduled frequency."),
                user_id=policy.user_id.id,
                date_deadline=fields.Date.today(),
            )


class RecordsRetentionRule(models.Model):
    """Individual retention rules within a policy"""
    _name = "records.retention.rule"
    _description = "Records Retention Rule"
    _order = "sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(
        string="Rule Name", 
        required=True,
        help="Name of this retention rule"
    )
    sequence = fields.Integer(
        string="Sequence", 
        default=10,
        help="Order of rule evaluation"
    )
    active = fields.Boolean(
        string="Active", 
        default=True,
        help="Whether this rule is active"
    )

    # ============================================================================
    # POLICY RELATIONSHIP
    # ============================================================================
    policy_id = fields.Many2one(
        "records.retention.policy",
        string="Retention Policy",
        required=True,
        ondelete="cascade",
        help="Parent retention policy"
    )

    # ============================================================================
    # RULE CONFIGURATION
    # ============================================================================
    document_type_ids = fields.Many2many(
        "records.document.type", 
        string="Applicable Document Types",
        help="Document types this rule applies to"
    )
    condition_type = fields.Selection([
        ("all_documents", "All Documents"),
        ("by_type", "By Document Type"),
        ("by_tag", "By Tag"),
        ("by_location", "By Location"),
        ("by_criteria", "Custom Criteria"),
    ],
        string="Condition Type",
        default="all_documents",
        required=True,
        help="How to identify documents for this rule"
    )
    
    # Override retention periods
    retention_years = fields.Integer(
        string="Retention Years", 
        default=0,
        help="Years to retain (overrides policy default)"
    )
    retention_months = fields.Integer(
        string="Retention Months", 
        default=0,
        help="Months to retain (overrides policy default)"
    )
    retention_days = fields.Integer(
        string="Retention Days", 
        default=0,
        help="Days to retain (overrides policy default)"
    )
    
    action_after_retention = fields.Selection([
        ("destroy", "Destroy"),
        ("archive", "Archive"),
        ("review", "Manual Review"),
        ("transfer", "Transfer to Archive"),
    ],
        string="Action After Retention",
        default="review",
        required=True,
        help="Action to take when retention period expires"
    )
    
    # Rule criteria
    criteria_domain = fields.Text(
        string="Selection Criteria",
        help="Domain filter for document selection (JSON format)"
    )
    notes = fields.Text(
        string="Notes",
        help="Additional notes about this rule"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    total_retention_days = fields.Integer(
        compute="_compute_total_retention_days",
        string="Total Retention (Days)",
        help="Total retention period for this rule in days"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("retention_years", "retention_months", "retention_days")
    def _compute_total_retention_days(self):
        """Calculate total retention period in days"""
        for record in self:
            total_days = (
                record.retention_years * 365
                + record.retention_months * 30
                + record.retention_days
            )
            record.total_retention_days = total_days

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("retention_years", "retention_months", "retention_days")
    def _check_retention_periods(self):
        """Validate retention periods are not negative"""
        for record in self:
            if (record.retention_years < 0 or 
                record.retention_months < 0 or 
                record.retention_days < 0):
                raise ValidationError(_("Retention periods cannot be negative"))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_effective_retention_period(self):
        """Get the effective retention period for this rule"""
        self.ensure_one()
        # If rule specifies retention periods, use them; otherwise use policy defaults
        if (self.retention_years or self.retention_months or self.retention_days):
            return {
                'years': self.retention_years,
                'months': self.retention_months,
                'days': self.retention_days,
            }
        else:
            return {
                'years': self.policy_id.retention_years,
                'months': self.policy_id.retention_months,
                'days': self.policy_id.retention_days,
            }

    def applies_to_document(self, document):
        """Check if this rule applies to a given document"""
        self.ensure_one()
        
        if self.condition_type == "all_documents":
            return True
        elif self.condition_type == "by_type" and self.document_type_ids:
            return document.document_type_id in self.document_type_ids
        elif self.condition_type == "by_criteria" and self.criteria_domain:
            try:
                # Parse and evaluate domain criteria
                import json
                domain = json.loads(self.criteria_domain)
                return document.filtered_domain(domain)
            except (json.JSONDecodeError, Exception):
                return False
        
        return False