# -*- coding: utf-8 -*-
"""
NAID Compliance Management Module

This module provides comprehensive NAID (National Association for Information Destruction)
compliance management for the Records Management System. It implements complete audit trails,
certification tracking, and compliance monitoring with enterprise-grade security features.
"""

import datetime
from datetime import timedelta

try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    # Fallback for systems without dateutil
    def relativedelta(months=0):
        return timedelta(days=months * 30)

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class NaidCompliance(models.Model):
    """
    NAID Compliance Management - Enterprise Records Management System

    Comprehensive NAID (National Association for Information Destruction) compliance
    management system providing complete audit trails, certification tracking, and
    regulatory compliance monitoring for enterprise document destruction services.
    """

    _name = "naid.compliance"
    _description = "NAID Compliance Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "certification_date desc, name"
    _rec_name = "name"
    _check_company_auto = True

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(
        string="Compliance Reference",
        required=True,
        tracking=True,
        index=True,
        default="New",
        help="Unique reference identifier for this compliance record",
    )

    code = fields.Char(
        string="Compliance Code",
        index=True,
        tracking=True,
        help="Internal compliance code for easy reference",
    )

    description = fields.Text(
        string="Description",
        help="Detailed description of this compliance framework and requirements",
    )

    sequence = fields.Integer(
        string="Sequence", default=10, help="Sequence for ordering compliance records"
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
        help="Uncheck to archive this compliance record",
    )

    # ============================================================================
    # COMPANY & USER MANAGEMENT
    # ============================================================================

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        help="Company this compliance framework applies to",
    )

    user_id = fields.Many2one(
        "res.users",
        string="Compliance Manager",
        default=lambda self: self.env.user,
        tracking=True,
        help="Primary compliance manager responsible for this record",
    )

    compliance_officer_id = fields.Many2one(
        "res.users",
        string="Compliance Officer",
        tracking=True,
        help="Designated compliance officer for oversight and reporting",
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending Review"),
            ("under_review", "Under Review"),
            ("compliant", "Compliant"),
            ("non_compliant", "Non-Compliant"),
            ("expired", "Expired"),
            ("suspended", "Suspended"),
        ],
        string="Compliance Status",
        default="draft",
        required=True,
        tracking=True,
        help="Current compliance status of this record",
    )

    # ============================================================================
    # NAID CERTIFICATION MANAGEMENT
    # ============================================================================

    naid_level = fields.Selection(
        [
            ("aaa", "NAID AAA Certified"),
            ("aa", "NAID AA Certified"),
            ("a", "NAID A Certified"),
            ("pending", "Certification Pending"),
            ("expired", "Certification Expired"),
            ("revoked", "Certification Revoked"),
        ],
        string="NAID Certification Level",
        required=True,
        default="pending",
        tracking=True,
        help="Current NAID certification level and status",
    )

    certification_number = fields.Char(
        string="Certification Number",
        tracking=True,
        help="Official NAID certification number",
    )

    certification_date = fields.Date(
        string="Certification Date",
        tracking=True,
        help="Date when NAID certification was issued",
    )

    expiration_date = fields.Date(
        string="Expiration Date",
        required=True,
        tracking=True,
        help="Date when current certification expires",
    )

    renewal_date = fields.Date(
        string="Renewal Date", help="Date when certification renewal is due"
    )

    # ============================================================================
    # AUDIT SCHEDULING & TRACKING
    # ============================================================================

    audit_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annual", "Semi-Annual"),
            ("annual", "Annual"),
            ("on_demand", "On Demand"),
        ],
        string="Audit Frequency",
        default="quarterly",
        required=True,
        help="Required frequency for compliance audits",
    )

    last_audit_date = fields.Date(
        string="Last Audit Date",
        tracking=True,
        help="Date of most recent compliance audit",
    )

    next_audit_date = fields.Date(
        string="Next Audit Date",
        tracking=True,
        help="Scheduled date for next compliance audit",
    )

    audit_due_days = fields.Integer(
        string="Days Until Audit",
        compute="_compute_audit_timing",
        store=True,
        help="Number of days until next audit is due",
    )

    # ============================================================================
    # COMPLIANCE SCORING & METRICS
    # ============================================================================

    overall_score = fields.Float(
        string="Overall Compliance Score (%)",
        digits=(5, 2),
        compute="_compute_compliance_scores",
        store=True,
        help="Overall compliance percentage based on all audit categories",
    )

    security_score = fields.Float(
        string="Security Score (%)",
        digits=(5, 2),
        help="Physical and information security compliance score",
    )

    process_score = fields.Float(
        string="Process Score (%)",
        digits=(5, 2),
        help="Destruction process compliance score",
    )

    documentation_score = fields.Float(
        string="Documentation Score (%)",
        digits=(5, 2),
        help="Documentation and record-keeping compliance score",
    )

    personnel_score = fields.Float(
        string="Personnel Score (%)",
        digits=(5, 2),
        help="Personnel training and screening compliance score",
    )

    equipment_score = fields.Float(
        string="Equipment Score (%)",
        digits=(5, 2),
        help="Equipment certification and maintenance compliance score",
    )

    # ============================================================================
    # AUDIT RESULTS & FINDINGS
    # ============================================================================

    audit_findings = fields.Text(
        string="Audit Findings", help="Detailed findings from compliance audits"
    )

    corrective_actions = fields.Text(
        string="Corrective Actions",
        help="Required corrective actions to address findings",
    )

    remediation_plan = fields.Text(
        string="Remediation Plan", help="Detailed plan for addressing compliance gaps"
    )

    risk_assessment = fields.Text(
        string="Risk Assessment",
        help="Assessment of compliance risks and mitigation strategies",
    )

    findings_count = fields.Integer(
        string="Open Findings",
        compute="_compute_findings_metrics",
        store=True,
        help="Number of open audit findings requiring attention",
    )

    # ============================================================================
    # SECURITY & FACILITY REQUIREMENTS
    # ============================================================================

    security_level = fields.Selection(
        [
            ("basic", "Basic Security"),
            ("enhanced", "Enhanced Security"),
            ("maximum", "Maximum Security"),
        ],
        string="Required Security Level",
        default="enhanced",
        required=True,
        help="Minimum security level required for this compliance framework",
    )

    facility_requirements = fields.Text(
        string="Facility Requirements",
        help="Physical facility requirements for compliance",
    )

    access_control_verified = fields.Boolean(
        string="Access Control Verified",
        help="Physical access controls have been verified and approved",
    )

    surveillance_system_verified = fields.Boolean(
        string="Surveillance System Verified",
        help="Video surveillance system meets compliance requirements",
    )

    # ============================================================================
    # INSURANCE & BONDING
    # ============================================================================

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    insurance_coverage = fields.Monetary(
        string="Insurance Coverage",
        currency_field="currency_id",
        help="Required insurance coverage amount",
    )

    liability_limit = fields.Monetary(
        string="Liability Limit",
        currency_field="currency_id",
        help="Maximum liability limit for compliance",
    )

    bonding_amount = fields.Monetary(
        string="Bonding Amount",
        currency_field="currency_id",
        help="Required bonding amount for personnel",
    )

    insurance_verified = fields.Boolean(
        string="Insurance Verified",
        help="Insurance coverage has been verified and is current",
    )

    # ============================================================================
    # PERSONNEL & TRAINING
    # ============================================================================

    personnel_screening_required = fields.Boolean(
        string="Personnel Screening Required",
        default=True,
        help="Background screening is required for personnel",
    )

    training_completed = fields.Boolean(
        string="Training Completed",
        help="All required personnel training has been completed",
    )

    certification_training_current = fields.Boolean(
        string="Certification Training Current",
        help="Personnel certification training is up to date",
    )

    # ============================================================================
    # DOCUMENTATION & REPORTING
    # ============================================================================

    documentation_standard = fields.Selection(
        [
            ("naid", "NAID Standard"),
            ("iso_15489", "ISO 15489"),
            ("custom", "Custom Standard"),
        ],
        string="Documentation Standard",
        default="naid",
        required=True,
        help="Documentation standard to follow for compliance",
    )

    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required",
        default=True,
        help="Chain of custody documentation is required",
    )

    destruction_certificate_required = fields.Boolean(
        string="Destruction Certificate Required",
        default=True,
        help="Destruction certificates must be issued",
    )

    witness_required = fields.Boolean(
        string="Witness Required",
        default=True,
        help="Witnessed destruction is required for compliance",
    )

    # ============================================================================
    # REGULATORY & LEGAL
    # ============================================================================

    regulatory_requirements = fields.Text(
        string="Regulatory Requirements",
        help="Specific regulatory requirements that must be met",
    )

    legal_compliance_verified = fields.Boolean(
        string="Legal Compliance Verified",
        help="Legal and regulatory compliance has been verified",
    )

    sox_compliance = fields.Boolean(
        string="SOX Compliance", help="Sarbanes-Oxley compliance requirements apply"
    )

    hipaa_compliance = fields.Boolean(
        string="HIPAA Compliance", help="HIPAA privacy and security requirements apply"
    )

    gdpr_compliance = fields.Boolean(
        string="GDPR Compliance", help="GDPR data protection requirements apply"
    )

    # ============================================================================
    # PERFORMANCE MONITORING
    # ============================================================================

    destruction_volume_ytd = fields.Float(
        string="Destruction Volume YTD (lbs)",
        digits=(12, 2),
        help="Year-to-date destruction volume in pounds",
    )

    customer_satisfaction_score = fields.Float(
        string="Customer Satisfaction (%)",
        digits=(5, 2),
        help="Customer satisfaction percentage from surveys",
    )

    processing_time_avg = fields.Float(
        string="Average Processing Time (hours)",
        digits=(8, 2),
        help="Average time from pickup to destruction completion",
    )

    compliance_incidents = fields.Integer(
        string="Compliance Incidents YTD",
        help="Number of compliance incidents year-to-date",
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================

    is_expired = fields.Boolean(
        string="Is Expired",
        compute="_compute_expiration_status",
        store=True,
        help="True if certification has expired",
    )

    days_until_expiration = fields.Integer(
        string="Days Until Expiration",
        compute="_compute_expiration_status",
        store=True,
        help="Number of days until certification expires",
    )

    compliance_status_color = fields.Integer(
        string="Status Color",
        compute="_compute_status_indicators",
        help="Color indicator for compliance status",
    )

    audit_status_display = fields.Char(
        string="Audit Status",
        compute="_compute_status_indicators",
        help="Human readable audit status display",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Core NAID relationships
    certificate_ids = fields.One2many(
        "naid.certificate",
        "naid_compliance_id",
        string="Certificates",
        help="NAID certificates issued under this compliance framework",
    )

    audit_log_ids = fields.One2many(
        "naid.audit.log",
        "compliance_id",
        string="Audit Logs",
        help="Detailed audit logs for this compliance record",
    )

    checklist_ids = fields.One2many(
        "naid.compliance.checklist",
        "compliance_id",
        string="Compliance Checklists",
        help="Compliance checklists and assessments",
    )

    # Extended relationships
    destruction_record_ids = fields.One2many(
        "records.destruction",
        "compliance_id",
        string="Destruction Records",
        help="Destruction records under this compliance framework",
    )

    chain_custody_ids = fields.One2many(
        "records.chain.of.custody",
        "compliance_id",
        string="Chain of Custody Records",
        help="Chain of custody records for compliance tracking",
    )

    # Mail Thread Framework Fields (REQUIRED)
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        auto_join=True,
        groups="base.group_user",
    )

    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers", groups="base.group_user"
    )

    message_ids = fields.One2many(
        "mail.message", "res_id", string="Messages", groups="base.group_user"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("expiration_date")
    def _compute_expiration_status(self):
        """Compute expiration status and days until expiration"""
        today = fields.Date.today()
        for record in self:
            if record.expiration_date:
                delta = record.expiration_date - today
                record.days_until_expiration = delta.days
                record.is_expired = record.expiration_date < today
            else:
                record.days_until_expiration = 0
                record.is_expired = False

    @api.depends("next_audit_date")
    def _compute_audit_timing(self):
        """Compute days until next audit is due"""
        today = fields.Date.today()
        for record in self:
            if record.next_audit_date:
                delta = record.next_audit_date - today
                record.audit_due_days = delta.days
            else:
                record.audit_due_days = 0

    @api.depends(
        "security_score",
        "process_score",
        "documentation_score",
        "personnel_score",
        "equipment_score",
    )
    def _compute_compliance_scores(self):
        """Compute overall compliance score from individual category scores.
        Includes all scores that are not None, including zero, as zero may be a valid assessment.
        """
        for record in self:
            scores = [
                record.security_score,
                record.process_score,
                record.documentation_score,
                record.personnel_score,
                record.equipment_score,
            ]
            # Include all scores that are not None (including zero)
            valid_scores = [score for score in scores if score is not None]
            if valid_scores:
                record.overall_score = sum(valid_scores) / len(valid_scores)
            else:
                record.overall_score = 0.0

    @api.depends("audit_log_ids.state")
    def _compute_findings_metrics(self):
        """Compute count of open findings from audit logs"""
        for record in self:
            open_findings = record.audit_log_ids.filtered(
                lambda log: log.state in ["open", "in_progress"]
            )
            record.findings_count = len(open_findings)

    @api.depends("state", "overall_score", "is_expired")
    def _compute_status_indicators(self):
        """Compute status display indicators and colors"""
        for record in self:
            # Color coding: 1=red, 2=orange, 3=yellow, 10=green, 4=blue
            if record.is_expired or record.state == "expired":
                record.compliance_status_color = 1  # Red
                record.audit_status_display = "Expired - Renewal Required"
            elif record.state == "non_compliant":
                record.compliance_status_color = 1  # Red
                record.audit_status_display = "Non-Compliant - Action Required"
            elif record.state == "under_review":
                record.compliance_status_color = 2  # Orange
                record.audit_status_display = "Under Review"
            elif record.state == "compliant":
                if record.overall_score >= 95:
                    record.compliance_status_color = 10  # Green
                    record.audit_status_display = "Excellent Compliance"
                elif record.overall_score >= 85:
                    record.compliance_status_color = 3  # Yellow
                    record.audit_status_display = "Good Compliance"
                else:
                    record.compliance_status_color = 2  # Orange
                    record.audit_status_display = "Marginal Compliance"
            else:
                record.compliance_status_color = 4  # Blue
                record.audit_status_display = "Pending Review"

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_complete_audit(self):
        """Complete audit process and update compliance status"""

        self.ensure_one()

        if not self.audit_findings:
            raise UserError(
                _("Please enter audit findings before completing the audit.")
            )

        # Determine new state based on overall score
        if self.overall_score >= 80:
            new_state = "compliant"
            message = _("Audit completed successfully. Compliance status: COMPLIANT")
        else:
            new_state = "non_compliant"
            message = _(
                "Audit completed. Compliance status: NON-COMPLIANT. Corrective action required."
            )

        # Calculate next audit date based on frequency
        frequency_map = {
            "monthly": 1,
            "quarterly": 3,
            "semi_annual": 6,
            "annual": 12,
            "on_demand": 6,  # Default to 6 months
        }
        months = frequency_map.get(self.audit_frequency, 6)
        next_audit = fields.Date.today() + relativedelta(months=months)

        self.write(
            {
                "state": new_state,
                "next_audit_date": next_audit,
            }
        )

        # Post completion message
        self.message_post(body=message)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Audit Completed"),
                "message": message,
                "type": "success" if new_state == "compliant" else "warning",
            },
        }

    def action_schedule_next_audit(self):
        """Schedule the next compliance audit based on requirements"""

        self.ensure_one()

        if not self.next_audit_date:
            raise UserError(
                _("Next audit date is not set. Please complete current audit first.")
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Audit Scheduled"),
                "message": _("Next audit scheduled for %s", self.next_audit_date),
                "type": "success",
            },
        }

    def action_generate_certificate(self):
        """Generate NAID compliance certificate for compliant records"""

        self.ensure_one()

        if self.state != "compliant":
            raise UserError(
                _("Certificates can only be generated for compliant records.")
            )
        if not self.certification_date:
            raise UserError(
                _("Certification date must be set before generating certificate.")
            )

        return {
            "type": "ir.actions.act_window",
            "name": _("Generate NAID Certificate"),
            "res_model": "naid.certificate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_compliance_id": self.id,
                "default_certification_level": self.naid_level,
                "default_certification_date": self.certification_date,
                "default_expiration_date": self.expiration_date,
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("certification_date", "expiration_date")
    def _check_certification_dates(self):
        """Validate certification date logic"""
        for record in self:
            if record.certification_date and record.expiration_date:
                if record.certification_date >= record.expiration_date:
                    raise ValidationError(
                        _("Certification date must be before expiration date.")
                    )

    @api.constrains(
        "overall_score",
        "security_score",
        "process_score",
        "documentation_score",
        "personnel_score",
        "equipment_score",
    )
    def _check_score_ranges(self):
        """Ensure all scores are within valid percentage ranges"""
        for record in self:
            score_fields = {
                "Overall Score": record.overall_score,
                "Security Score": record.security_score,
                "Process Score": record.process_score,
                "Documentation Score": record.documentation_score,
                "Personnel Score": record.personnel_score,
                "Equipment Score": record.equipment_score,
            }
            for field_name, score in score_fields.items():
                if score is not None and (score < 0 or score > 100):
                    raise ValidationError(
                        _("%s must be between 0 and 100 percent.", field_name)
                    )

    @api.constrains("insurance_coverage", "liability_limit", "bonding_amount")
    def _check_monetary_amounts(self):
        """Ensure monetary amounts are positive"""
        for record in self:
            if record.insurance_coverage and record.insurance_coverage < 0:
                raise ValidationError(
                    _("Insurance coverage must be a positive amount.")
                )
            if record.liability_limit and record.liability_limit < 0:
                raise ValidationError(_("Liability limit must be a positive amount."))
            if record.bonding_amount and record.bonding_amount < 0:
                raise ValidationError(_("Bonding amount must be a positive amount."))

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence and set defaults"""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "naid.compliance"
                ) or _("New")

            # Set default next audit date based on frequency
            if not vals.get("next_audit_date") and vals.get("audit_frequency"):
                frequency_map = {
                    "monthly": 1,
                    "quarterly": 3,
                    "semi_annual": 6,
                    "annual": 12,
                }
                months = frequency_map.get(vals["audit_frequency"], 3)
                vals["next_audit_date"] = fields.Date.today() + relativedelta(
                    months=months
                )

        records = super().create(vals_list)

        # Create initial audit activity
        for record in records:
            record.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Initial NAID Compliance Setup - %s", record.name),
                note=_(
                    "Complete initial compliance setup and documentation for NAID %s certification.",
                    record.naid_level,
                ),
                user_id=record.user_id.id,
                date_deadline=fields.Date.today() + timedelta(days=30),
            )

            naid_level_display = (
                record.naid_level.upper() if record.naid_level else _("Unknown")
            )
            record.message_post(
                body=_(
                    "NAID Compliance record created for %s certification level.",
                    naid_level_display,
                )
            )

        return records

    def write(self, vals):
        """Override write to track important changes"""
        # Track state changes
        if "state" in vals:
            for record in self:
                old_state = record.state
                new_state = vals["state"]
                if old_state != new_state:
                    old_state_display = dict(record._fields["state"].selection).get(
                        old_state, old_state
                    )
                    new_state_display = dict(record._fields["state"].selection).get(
                        new_state, new_state
                    )
                    record.message_post(
                        body=_(
                            "Compliance status changed from %s to %s",
                            old_state_display,
                            new_state_display,
                        )
                    )

        # Track NAID level changes
        if "naid_level" in vals:
            for record in self:
                if record.naid_level != vals["naid_level"]:
                    old_level_display = dict(
                        record._fields["naid_level"].selection
                    ).get(record.naid_level, record.naid_level)
                    new_level_display = dict(
                        record._fields["naid_level"].selection
                    ).get(vals["naid_level"], vals["naid_level"])
                    record.message_post(
                        body=_(
                            "NAID certification level changed from %s to %s",
                            old_level_display,
                            new_level_display,
                        )
                    )

        # Update renewal date when expiration changes
        if "expiration_date" in vals and vals["expiration_date"]:
            expiration_date = vals["expiration_date"]
            if isinstance(expiration_date, str):
                expiration_date = datetime.datetime.strptime(
                    expiration_date, "%Y-%m-%d"
                ).date()
            vals["renewal_date"] = expiration_date - timedelta(days=60)

        return super().write(vals)

    def unlink(self):
        """Override unlink to prevent deletion of active compliance records"""
        for record in self:
            if record.state == "compliant":
                raise UserError(
                    _("Cannot delete compliant certification records. Archive instead.")
                )
        return super().unlink()

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def _get_audit_requirements(self):
        """Get specific audit requirements based on NAID level"""
        self.ensure_one()

        base_requirements = {
            "security": [
                "Physical access controls",
                "Surveillance systems",
                "Personnel screening",
            ],
            "process": [
                "Destruction methods",
                "Chain of custody",
                "Witness procedures",
            ],
            "documentation": [
                "Policy compliance",
                "Record keeping",
                "Reporting procedures",
            ],
            "personnel": [
                "Training records",
                "Background checks",
                "Certification status",
            ],
            "equipment": [
                "Equipment certification",
                "Maintenance records",
                "Calibration status",
            ],
        }

        # Add specific requirements based on NAID level
        if self.naid_level == "aaa":
            base_requirements["security"].extend(["Biometric access", "Armed security"])
            base_requirements["process"].extend(["Dual witness", "Video recording"])
        elif self.naid_level == "aa":
            base_requirements["security"].extend(["Badge access", "Security guard"])
            base_requirements["process"].extend(["Single witness required"])

        return base_requirements

    def _calculate_compliance_risk(self):
        """Calculate compliance risk score based on various factors"""
        self.ensure_one()

        risk_factors = []

        # Expiration risk
        if self.days_until_expiration <= 30:
            risk_factors.append(25)
        elif self.days_until_expiration <= 60:
            risk_factors.append(15)

        # Score-based risk
        if self.overall_score < 70:
            risk_factors.append(30)
        elif self.overall_score < 85:
            risk_factors.append(15)

        # Findings risk
        if self.findings_count > 5:
            risk_factors.append(20)
        elif self.findings_count > 0:
            risk_factors.append(10)

        # Audit overdue risk
        if self.audit_due_days < 0:
            risk_factors.append(25)

        risk_score = sum(risk_factors)

        if risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 25:
            risk_level = "medium"
        else:
            risk_level = "low"

        return risk_score, risk_level
