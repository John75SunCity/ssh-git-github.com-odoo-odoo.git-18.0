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
    # AUTO-GENERATED FIELDS (from view analysis)
    # ============================================================================
    access_control_verified = fields.Char(string="Access Control Verified")
    arch = fields.Char(string="Arch")
    audit_date = fields.Date(string="Audit Date")
    audit_frequency = fields.Char(string="Audit Frequency")
    audit_reminder = fields.Char(string="Audit Reminder")
    audit_required = fields.Char(string="Audit Required")
    audit_result = fields.Char(string="Audit Result")
    audit_scope = fields.Char(string="Audit Scope")
    audit_type = fields.Selection([("normal", "Normal"), ("high", "High")], string="Audit Type", default="normal")
    auditor_name = fields.Char(string="Auditor Name")
    auto_renewal = fields.Char(string="Auto Renewal")
    automated_check = fields.Char(string="Automated Check")
    background_checks = fields.Char(string="Background Checks")
    benchmark = fields.Char(string="Benchmark")
    certificate_issued = fields.Char(string="Certificate Issued")
    certificate_number = fields.Integer(string="Certificate Number")
    certificate_status = fields.Char(string="Certificate Status")
    certificate_tracking = fields.Char(string="Certificate Tracking")
    certificate_type = fields.Selection([("normal", "Normal"), ("high", "High")], string="Certificate Type", default="normal")
    chain_of_custody = fields.Char(string="Chain Of Custody")
    check_frequency = fields.Char(string="Check Frequency")
    client_name = fields.Char(string="Client Name")
    compliance_alerts = fields.Char(string="Compliance Alerts")
    compliance_officer = fields.Char(string="Compliance Officer")
    compliance_score = fields.Char(string="Compliance Score")
    compliance_status = fields.Char(string="Compliance Status")
    compliance_trend = fields.Char(string="Compliance Trend")
    compliance_verified = fields.Char(string="Compliance Verified")
    context = fields.Char(string="Context")
    days_since_last_audit = fields.Char(string="Days Since Last Audit")
    days_until_expiry = fields.Char(string="Days Until Expiry")
    destruction_date = fields.Date(string="Destruction Date")
    destruction_method = fields.Char(string="Destruction Method")
    destruction_verification = fields.Char(string="Destruction Verification")
    documentation_score = fields.Char(string="Documentation Score")
    equipment_certification = fields.Char(string="Equipment Certification")
    escalation_contacts = fields.Char(string="Escalation Contacts")
    expiry_date = fields.Date(string="Expiry Date")
    expiry_notification = fields.Char(string="Expiry Notification")
    facility_manager = fields.Char(string="Facility Manager")
    facility_name = fields.Char(string="Facility Name")
    findings_count = fields.Integer(string="Findings Count")
    help = fields.Char(string="Help")
    implementation_notes = fields.Text(string="Implementation Notes")
    information_handling = fields.Char(string="Information Handling")
    interval_number = fields.Integer(string="Interval Number")
    interval_type = fields.Selection([("normal", "Normal"), ("high", "High")], string="Interval Type", default="normal")
    issue_date = fields.Date(string="Issue Date")
    issuing_authority = fields.Char(string="Issuing Authority")
    last_audit_date = fields.Date(string="Last Audit Date")
    last_verified = fields.Char(string="Last Verified")
    management_alerts = fields.Char(string="Management Alerts")
    mandatory = fields.Char(string="Mandatory")
    material_type = fields.Selection([("normal", "Normal"), ("high", "High")], string="Material Type", default="normal")
    measurement_date = fields.Date(string="Measurement Date")
    metric_type = fields.Selection([("normal", "Normal"), ("high", "High")], string="Metric Type", default="normal")
    model = fields.Char(string="Model")
    next_audit_date = fields.Date(string="Next Audit Date")
    notes = fields.Text(string="Notes")
    notification_recipients = fields.Char(string="Notification Recipients")
    operational_score = fields.Char(string="Operational Score")
    overall_compliance_score = fields.Char(string="Overall Compliance Score")
    padding = fields.Char(string="Padding")
    personnel_screening = fields.Char(string="Personnel Screening")
    physical_security_score = fields.Char(string="Physical Security Score")
    policy_type = fields.Selection([("normal", "Normal"), ("high", "High")], string="Policy Type", default="normal")
    prefix = fields.Char(string="Prefix")
    process_verification = fields.Char(string="Process Verification")
    quality_control = fields.Char(string="Quality Control")
    regulatory_notifications = fields.Char(string="Regulatory Notifications")
    renewal_reminder = fields.Char(string="Renewal Reminder")
    requirement_name = fields.Char(string="Requirement Name")
    requirement_type = fields.Selection([("normal", "Normal"), ("high", "High")], string="Requirement Type", default="normal")
    res_model = fields.Char(string="Res Model")
    responsible_person = fields.Char(string="Responsible Person")
    review_frequency_months = fields.Char(string="Review Frequency Months")
    risk_level = fields.Char(string="Risk Level")
    score = fields.Char(string="Score")
    secure_storage = fields.Char(string="Secure Storage")
    security_clearance = fields.Char(string="Security Clearance")
    security_officer = fields.Char(string="Security Officer")
    security_score = fields.Char(string="Security Score")
    surveillance_system = fields.Char(string="Surveillance System")
    third_party_auditor = fields.Char(string="Third Party Auditor")
    training_completed = fields.Char(string="Training Completed")
    trend = fields.Char(string="Trend")
    variance = fields.Char(string="Variance")
    verification_method = fields.Char(string="Verification Method")
    view_mode = fields.Char(string="View Mode")
    violation_consequences = fields.Integer(string="Violation Consequences")
    witness_present = fields.Char(string="Witness Present")
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
