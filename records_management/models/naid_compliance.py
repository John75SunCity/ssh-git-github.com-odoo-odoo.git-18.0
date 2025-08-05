# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import timedelta


class NaidCompliance(models.Model):
    _name = "naid.compliance"
    _description = "NAID Compliance Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(
        string="Compliance Check", required=True, tracking=True, index=True
    )
    code = fields.Char(string="Compliance Code", index=True, tracking=True)
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
        "res.users", string="Compliance Manager", default=lambda self: self.env.user
    )

    # State Management
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("compliant", "Compliant"),
            ("non_compliant", "Non-Compliant"),
            ("under_review", "Under Review"),
        ],
        string="Compliance Status",
        default="pending",
        tracking=True,
    )

    # ============================================================================
    # NAID CERTIFICATION & COMPLIANCE
    # ============================================================================

    # NAID Certification Details
    naid_level = fields.Selection(
        [
            ("aaa", "NAID AAA"),
            ("aa", "NAID AA"),
            ("a", "NAID A"),
            ("pending", "Pending Certification"),
            ("expired", "Expired"),
        ],
        string="NAID Certification Level",
        required=True,
        tracking=True,
    )

    compliance_level = fields.Selection(
        [("aaa", "AAA Certified"), ("aa", "AA Certified"), ("a", "A Certified")],
        string="Current NAID Level",
        tracking=True,
    )

    certification_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("certified", "Certified"),
            ("expired", "Expired"),
            ("revoked", "Revoked"),
        ],
        string="Certification Status",
        default="pending",
        tracking=True,
    )

    # ============================================================================
    # DATES & SCHEDULING
    # ============================================================================

    check_date = fields.Date(string="Check Date", required=True, tracking=True)
    last_review_date = fields.Date(string="Last Review Date", tracking=True)
    next_review_date = fields.Date(string="Next Review Date", tracking=True)
    compliance_deadline = fields.Date(string="Compliance Deadline", tracking=True)
    certification_date = fields.Date(string="Certification Date", tracking=True)
    expiration_date = fields.Date(string="Expiration Date", tracking=True)

    # Computed Dates
    days_until_expiration = fields.Integer(
        string="Days Until Expiration",
        compute="_compute_days_until_expiration",
        store=True,
    )
    is_expired = fields.Boolean(
        string="Is Expired",
        compute="_compute_expiration_status",
        store=True,
    )

    # ============================================================================
    # AUDIT & ASSESSMENT
    # ============================================================================

    audit_results = fields.Text(string="Audit Results")
    corrective_actions = fields.Text(string="Corrective Actions")
    audit_findings = fields.Text(string="Audit Findings")
    remediation_plan = fields.Text(string="Remediation Plan")
    risk_assessment = fields.Text(string="Risk Assessment")

    # Audit Metrics
    audit_score = fields.Float(
        string="Audit Score (%)",
        digits=(5, 2),
        help="Overall audit score percentage",
    )
    compliance_percentage = fields.Float(
        string="Compliance Percentage",
        digits=(5, 2),
        compute="_compute_compliance_metrics",
        store=True,
    )

    # ============================================================================
    # DOCUMENTATION & REPORTING
    # ============================================================================

    # Documentation Standards
    documentation_standard = fields.Selection(
        [
            ("naid", "NAID Standard"),
            ("iso", "ISO Standard"),
            ("custom", "Custom Standard"),
        ],
        string="Documentation Standard",
        default="naid",
    )

    reporting_frequency = fields.Selection(
        [
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annually", "Annually"),
        ],
        string="Reporting Frequency",
        default="quarterly",
    )

    # Required Documentation
    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required", default=True
    )
    destruction_certificate_required = fields.Boolean(
        string="Destruction Certificate Required", default=True
    )
    audit_trail_required = fields.Boolean(string="Audit Trail Required", default=True)

    # ============================================================================
    # SECURITY & SAFETY
    # ============================================================================

    # Security Measures
    security_level = fields.Selection(
        [
            ("basic", "Basic Security"),
            ("enhanced", "Enhanced Security"),
            ("maximum", "Maximum Security"),
        ],
        string="Security Level",
        default="enhanced",
    )

    security_system_version = fields.Char(string="Security System Version")
    monitoring_tools = fields.Text(string="Monitoring Tools")
    backup_systems = fields.Boolean(string="Backup Systems", default=True)

    # Safety Protocols
    safety_protocols = fields.Text(string="Safety Protocols")
    emergency_procedures = fields.Text(string="Emergency Procedures")
    environmental_compliance = fields.Boolean(
        string="Environmental Compliance", default=True
    )

    # ============================================================================
    # INSURANCE & LIABILITY
    # ============================================================================

    # Currency Configuration
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Insurance Coverage
    insurance_coverage = fields.Monetary(
        string="Insurance Coverage", currency_field="currency_id"
    )
    liability_limit = fields.Monetary(
        string="Liability Limit", currency_field="currency_id"
    )
    bonding_amount = fields.Monetary(
        string="Bonding Amount", currency_field="currency_id"
    )

    # Legal Requirements
    legal_requirements = fields.Text(string="Legal Requirements")
    regulatory_compliance = fields.Boolean(string="Regulatory Compliance", default=True)

    # ============================================================================
    # PERFORMANCE METRICS
    # ============================================================================

    # Operational Metrics
    destruction_volume = fields.Float(
        string="Destruction Volume (tons)", digits=(10, 2)
    )
    processing_time = fields.Float(
        string="Average Processing Time (hours)", digits=(5, 2)
    )
    customer_satisfaction = fields.Float(
        string="Customer Satisfaction (%)", digits=(5, 2)
    )

    # Quality Metrics
    quality_management_system = fields.Boolean(
        string="Quality Management System", default=True
    )
    iso_certification = fields.Char(string="ISO Certification")
    quality_score = fields.Float(string="Quality Score (%)", digits=(5, 2))

    # ============================================================================
    # STAKEHOLDER MANAGEMENT
    # ============================================================================

    # Communication
    customer_notifications = fields.Boolean(
        string="Customer Notifications", default=True
    )
    stakeholder_communication = fields.Text(string="Stakeholder Communication")
    public_disclosure = fields.Boolean(string="Public Disclosure", default=False)

    # Vendor Management
    vendor_compliance = fields.Boolean(string="Vendor Compliance", default=True)
    supplier_audits = fields.Boolean(string="Supplier Audits", default=True)
    third_party_certifications = fields.Text(string="Third Party Certifications")

    # ============================================================================
    # CONTINUOUS IMPROVEMENT
    # ============================================================================

    improvement_plan = fields.Text(string="Improvement Plan")
    lessons_learned = fields.Text(string="Lessons Learned")
    best_practices = fields.Text(string="Best Practices")
    training_requirements = fields.Text(string="Training Requirements")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Core Relationships
    certificate_id = fields.Many2one("naid.certificate", string="Certificate")
    audit_log_ids = fields.One2many(
        "naid.audit.log", "compliance_id", string="Audit Logs"
    )
    checklist_ids = fields.One2many(
        "naid.compliance.checklist", "compliance_id", string="Compliance Checklists"
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

    @api.depends("expiration_date")
    def _compute_days_until_expiration(self):
        """Compute days until certification expires"""
        today = fields.Date.today()
        for record in self:
            if record.expiration_date:
                delta = record.expiration_date - today
                record.days_until_expiration = delta.days
            else:
                record.days_until_expiration = 0

    @api.depends("expiration_date")
    def _compute_expiration_status(self):
        """Compute if certification is expired"""
        today = fields.Date.today()
        for record in self:
            record.is_expired = (
                record.expiration_date and record.expiration_date < today
            )

    @api.depends("audit_score", "quality_score")
    def _compute_compliance_metrics(self):
        """Compute overall compliance percentage"""
        for record in self:
            scores = [
                score for score in [record.audit_score, record.quality_score] if score
            ]
            if scores:
                record.compliance_percentage = sum(scores) / len(scores)
            else:
                record.compliance_percentage = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_start_audit(self):
        """Start compliance audit process"""
        self.ensure_one()
        self.write(
            {
                "state": "under_review",
                "check_date": fields.Date.today(),
            }
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Audit Started"),
                "message": _("Compliance audit has been initiated."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_complete_audit(self):
        """Complete compliance audit"""
        self.ensure_one()
        if not self.audit_results:
            raise UserError(_("Please enter audit results before completing."))

        self.write(
            {
                "state": (
                    "compliant" if self.compliance_percentage >= 80 else "non_compliant"
                ),
                "last_review_date": fields.Date.today(),
                "next_review_date": fields.Date.today() + relativedelta(months=6),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Audit Completed"),
                "message": _("Compliance audit has been completed successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_audit_logs(self):
        """View related audit logs"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Audit Logs"),
            "res_model": "naid.audit.log",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("compliance_id", "=", self.id)],
        }

    def action_generate_certificate(self):
        """Generate compliance certificate"""
        self.ensure_one()
        if self.state != "compliant":
            raise UserError(_("Can only generate certificates for compliant records."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Generate Certificate"),
            "res_model": "naid.certificate",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_compliance_id": self.id,
                "default_partner_id": self.company_id.partner_id.id,
            },
        }

    def action_schedule_review(self):
        """Schedule next compliance review"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Review"),
            "res_model": "calendar.event",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_name": f"NAID Compliance Review - {self.name}",
                "default_description": f"Scheduled compliance review for {self.name}",
                "default_user_id": self.user_id.id,
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("check_date", "expiration_date")
    def _check_date_validity(self):
        """Ensure dates are logical"""
        for record in self:
            if (
                record.check_date
                and record.expiration_date
                and record.check_date > record.expiration_date
            ):
                raise ValidationError(_("Check date cannot be after expiration date."))

    @api.constrains("audit_score", "quality_score", "compliance_percentage")
    def _check_percentage_values(self):
        """Ensure percentage values are between 0 and 100"""
        for record in self:
            for field_name, field_value in [
                ("audit_score", record.audit_score),
                ("quality_score", record.quality_score),
                ("compliance_percentage", record.compliance_percentage),
            ]:
                if field_value and (field_value < 0 or field_value > 100):
                    raise ValidationError(
                        _(
                            f"{field_name.replace('_', ' ').title()} must be between 0 and 100."
                        )
                    )

    @api.constrains("insurance_coverage", "liability_limit")
    def _check_monetary_values(self):
        """Ensure monetary values are positive"""
        for record in self:
            if record.insurance_coverage and record.insurance_coverage < 0:
                raise ValidationError(_("Insurance coverage must be positive."))
            if record.liability_limit and record.liability_limit < 0:
                raise ValidationError(_("Liability limit must be positive."))

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model_create_multi
    def create(self, vals):
        """Override create to set defaults"""
        if not vals.get("name"):
            vals["name"] = self.env["ir.sequence"].next_by_code("naid.compliance") or _(
                "New"
            )
        return super().create(vals)

    def write(self, vals):
        """Override write to track important changes"""
        if "state" in vals:
            for record in self:
                record.message_post(
                    body=_("Compliance status changed from %s to %s")
                    % (
                        dict(record._fields["state"].selection).get(record.state),
                        dict(record._fields["state"].selection).get(vals["state"]),
                    )
                )
        return super().write(vals)
