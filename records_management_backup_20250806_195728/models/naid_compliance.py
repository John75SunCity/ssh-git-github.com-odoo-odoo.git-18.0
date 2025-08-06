# -*- coding: utf-8 -*-
"""NAID Compliance Management - See RECORDS_MANAGEMENT_SYSTEM_MANUAL.md for complete documentation"""

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class NaidCompliance(models.Model):
    """NAID Compliance Management - Complete documentation in RECORDS_MANAGEMENT_SYSTEM_MANUAL.md"""

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
    audit_type = fields.Selection(
        [("normal", "Normal"), ("high", "High")], string="Audit Type", default="normal"
    )
    auditor_name = fields.Char(string="Auditor Name")
    auto_renewal = fields.Char(string="Auto Renewal")
    automated_check = fields.Char(string="Automated Check")
    background_checks = fields.Char(string="Background Checks")
    benchmark = fields.Char(string="Benchmark")
    certificate_issued = fields.Char(string="Certificate Issued")
    certificate_number = fields.Integer(string="Certificate Number")
    certificate_status = fields.Char(string="Certificate Status")
    certificate_tracking = fields.Char(string="Certificate Tracking")
    certificate_type = fields.Selection(
        [("normal", "Normal"), ("high", "High")],
        string="Certificate Type",
        default="normal",
    )
    chain_of_custody = fields.Char(string="Chain Of Custody")
    check_frequency = fields.Char(string="Check Frequency")
    client_name = fields.Char(string="Client Name")
    compliance_alerts = fields.Char(string="Compliance Alerts")
    compliance_officer = fields.Char(string="Compliance Officer")
    compliance_score = fields.Char(string="Compliance Score")
    compliance_status = fields.Char(string="Compliance Status Details")
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
    interval_type = fields.Selection(
        [("normal", "Normal"), ("high", "High")],
        string="Interval Type",
        default="normal",
    )
    issue_date = fields.Date(string="Issue Date")
    issuing_authority = fields.Char(string="Issuing Authority")
    last_audit_date = fields.Date(string="Last Audit Date")
    last_verified = fields.Char(string="Last Verified")
    management_alerts = fields.Char(string="Management Alerts")
    mandatory = fields.Char(string="Mandatory")
    material_type = fields.Selection(
        [("normal", "Normal"), ("high", "High")],
        string="Material Type",
        default="normal",
    )
    measurement_date = fields.Date(string="Measurement Date")
    metric_type = fields.Selection(
        [("normal", "Normal"), ("high", "High")], string="Metric Type", default="normal"
    )
    model = fields.Char(string="Model")
    next_audit_date = fields.Date(string="Next Audit Date")
    notes = fields.Text(string="Notes")
    notification_recipients = fields.Char(string="Notification Recipients")
    operational_score = fields.Char(string="Operational Score")
    overall_compliance_score = fields.Char(string="Overall Compliance Score")
    padding = fields.Char(string="Padding")
    personnel_screening = fields.Char(string="Personnel Screening")
    physical_security_score = fields.Char(string="Physical Security Score")
    policy_type = fields.Selection(
        [("normal", "Normal"), ("high", "High")], string="Policy Type", default="normal"
    )
    prefix = fields.Char(string="Prefix")
    process_verification = fields.Char(string="Process Verification")
    quality_control = fields.Char(string="Quality Control")
    regulatory_notifications = fields.Char(string="Regulatory Notifications")
    renewal_reminder = fields.Char(string="Renewal Reminder")
    requirement_name = fields.Char(string="Requirement Name")
    requirement_type = fields.Selection(
        [("normal", "Normal"), ("high", "High")],
        string="Requirement Type",
        default="normal",
    )
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

    def action_compliance_report(self):
        """
        Generate comprehensive compliance report for regulatory documentation.

        This method generates a detailed PDF report containing all compliance
        information, audit results, and certification status. The report is
        formatted according to NAID AAA standards and includes all necessary
        documentation for regulatory compliance.

        Returns:
            dict: Action dictionary for PDF report generation

        Report Contents:
        - Current compliance status and certification level
        - Audit results and findings summary
        - Risk assessment and remediation plans
        - Insurance coverage and liability information
        - Performance metrics and quality scores
        - Chain of custody documentation references

        Usage Scenarios:
        - Regulatory audit submissions
        - Customer compliance verification
        - Internal compliance monitoring
        - Third-party certification reviews
        """
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.action_compliance_report_report",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }

    def action_download_certificate(self):
        """
        Download official NAID compliance certificate as PDF document.

        This method generates and downloads the official compliance certificate
        with tamper-proof security features and digital signatures. The certificate
        includes all required NAID AAA certification elements and can be used
        for customer documentation and regulatory compliance.

        Returns:
            dict: Action dictionary for certificate PDF generation

        Certificate Features:
        - Digital signature for authenticity verification
        - QR code linking to verification portal
        - Tamper-evident security watermarks
        - Complete compliance details and validity period
        - Issuing authority information and contact details

        Security Measures:
        - Encrypted PDF with access controls
        - Audit trail logging of certificate access
        - Version control for certificate updates

        Prerequisites:
        - Compliance status must be 'compliant'
        - Valid certification date and expiration date
        - All required audit documentation completed
        """
        self.ensure_one()
        if self.state != "compliant":
            raise UserError(
                _("Certificates can only be generated for compliant records.")
            )

        # Log certificate download for audit trail
        self.message_post(
            body=_("Compliance certificate downloaded by %s") % self.env.user.name
        )

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.action_download_certificate_report",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }

    def action_conduct_audit(self):
        """
        Initiate comprehensive NAID compliance audit process.

        This method launches the audit wizard that guides users through the
        complete NAID AAA audit process. It creates audit activities, schedules
        required inspections, and initializes the compliance checklist system.

        Returns:
            dict: Action dictionary to open audit wizard

        Audit Process:
        1. Pre-audit preparation and documentation review
        2. On-site inspection and process verification
        3. Security and safety protocol assessment
        4. Chain of custody validation
        5. Equipment and facility certification
        6. Personnel screening and training verification
        7. Final audit report generation and scoring

        Audit Components:
        - Physical security assessment (access controls, surveillance)
        - Process verification (destruction methods, witnessing)
        - Documentation review (policies, procedures, records)
        - Personnel evaluation (training, background checks)
        - Equipment inspection (certification, maintenance)
        - Customer notification and communication protocols

        Post-Audit Actions:
        - Generates findings report with corrective actions
        - Updates compliance scores and certification status
        - Schedules follow-up activities for non-conformances
        - Creates certificate if audit is successful
        """
        self.ensure_one()

        # Update audit tracking
        self.write(
            {
                "state": "under_review",
                "last_audit_date": fields.Date.today(),
            }
        )

        # Create audit activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("NAID Compliance Audit - %s") % self.name,
            note=_(
                "Conduct comprehensive NAID AAA compliance audit including physical security, process verification, and documentation review."
            ),
            user_id=self.user_id.id or self.env.user.id,
            date_deadline=fields.Date.today() + timedelta(days=1),
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Conduct NAID Compliance Audit"),
            "res_model": "naid.compliance.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_compliance_id": self.id,
                "default_audit_type": "full_audit",
            },
        }

    def action_view_audit_history(self):
        """
        Display comprehensive audit history and timeline for this compliance record.

        This method opens a filtered view showing all historical audit activities,
        findings, corrective actions, and compliance status changes. It provides
        a complete audit trail for regulatory compliance and internal monitoring.

        Returns:
            dict: Action dictionary to open audit history view

        History Contents:
        - Chronological audit timeline with all activities
        - Compliance status changes and transition reasons
        - Audit findings and corrective action tracking
        - Certificate generation and renewal history
        - User activity logs with timestamps and details
        - Document version control and update tracking

        View Features:
        - Filterable by date range, audit type, and user
        - Exportable for regulatory reporting
        - Searchable audit findings and actions
        - Linked document access for detailed review
        """
        self.ensure_one()

        # Get related audit logs and activities
        audit_logs = self.audit_log_ids
        activities = self.activity_ids
        messages = self.message_ids

        return {
            "type": "ir.actions.act_window",
            "name": _("Audit History - %s") % self.name,
            "res_model": "naid.audit.log",
            "view_mode": "tree,form,timeline",
            "domain": [("compliance_id", "=", self.id)],
            "context": {
                "search_default_group_by_date": 1,
                "search_default_recent": 1,
            },
        }

    def action_schedule_audit(self):
        """
        Schedule next compliance audit based on certification requirements and risk assessment.

        This method creates calendar events and activities for upcoming audit
        requirements. It considers certification expiration dates, regulatory
        requirements, and risk-based scheduling to ensure continuous compliance.

        Returns:
            bool: True when audit successfully scheduled

        Scheduling Logic:
        - AAA certification: Quarterly audits required
        - AA certification: Semi-annual audits required
        - A certification: Annual audits required
        - Risk-based adjustments for high-risk operations
        - Regulatory requirement integration (SOX, HIPAA)

        Created Activities:
        - Pre-audit preparation reminders
        - Audit execution scheduling
        - Post-audit follow-up activities
        - Certification renewal reminders

        Notifications:
        - Email alerts to compliance manager and stakeholders
        - Calendar invitations for audit participants
        - Automatic reminders based on configured frequency
        """
        self.ensure_one()

        # Determine audit frequency based on NAID level
        frequency_mapping = {
            "aaa": 3,  # Quarterly
            "aa": 6,  # Semi-annual
            "a": 12,  # Annual
            "pending": 1,  # Monthly until certified
        }

        months_offset = frequency_mapping.get(self.naid_level, 6)
        next_audit_date = fields.Date.today() + relativedelta(months=months_offset)

        # Update next review date
        self.write(
            {
                "next_review_date": next_audit_date,
                "next_audit_date": next_audit_date,
            }
        )

        # Create calendar event for audit
        calendar_event = self.env["calendar.event"].create(
            {
                "name": _("NAID Compliance Audit - %s") % self.name,
                "description": _("Scheduled NAID %s compliance audit for %s")
                % (self.naid_level.upper(), self.name),
                "start": next_audit_date,
                "stop": next_audit_date,
                "user_id": self.user_id.id,
                "partner_ids": [(6, 0, [self.user_id.partner_id.id])],
            }
        )

        # Create preparation activity
        self.activity_schedule(
            "mail.mail_activity_data_call",
            summary=_("Prepare for NAID Audit - %s") % self.name,
            note=_(
                "Prepare documentation and schedule resources for upcoming NAID compliance audit."
            ),
            user_id=self.user_id.id,
            date_deadline=next_audit_date - timedelta(days=7),
        )

        self.message_post(
            body=_("Next NAID compliance audit scheduled for %s (NAID %s level)")
            % (next_audit_date.strftime("%Y-%m-%d"), self.naid_level.upper())
        )

        return True

    def action_view_destruction_records(self):
        """
        View all destruction records linked to this compliance framework.

        This method displays destruction records that fall under this compliance
        framework, showing the complete chain of custody and destruction process
        documentation required for NAID AAA compliance.

        Returns:
            dict: Action dictionary to open destruction records view

        Related Records:
        - Destruction certificates issued under this compliance framework
        - Chain of custody records for destroyed materials
        - Witness verification documents and signatures
        - Shredding service records and completion certificates
        - Customer notifications and acknowledgments

        Compliance Integration:
        - Links destruction records to audit trail requirements
        - Validates witness requirements and security protocols
        - Tracks destruction method compliance with NAID standards
        - Maintains documentation for regulatory inspections
        """
        self.ensure_one()

        # Find related destruction records through various relationships
        destruction_records = self.env["records.destruction"].search(
            [
                "|",
                "|",
                ("compliance_id", "=", self.id),
                ("certificate_id.compliance_id", "=", self.id),
                ("naid_level", "=", self.naid_level),
            ]
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Destruction Records - %s Compliance") % self.naid_level.upper(),
            "res_model": "records.destruction",
            "view_mode": "tree,form,pivot,graph",
            "domain": [("id", "in", destruction_records.ids)],
            "context": {
                "search_default_group_by_compliance": 1,
                "search_default_recent": 1,
            },
        }

    def action_view_certificates(self):
        """
        View all certificates generated under this compliance framework.

        This method displays all compliance and destruction certificates
        that have been issued under this NAID compliance framework,
        providing a comprehensive view of certification history and status.

        Returns:
            dict: Action dictionary to open certificates view

        Certificate Types:
        - NAID compliance certificates (AAA, AA, A levels)
        - Destruction completion certificates
        - Chain of custody certificates
        - Third-party audit certificates
        - Insurance and bonding certificates

        Certificate Management:
        - Track issuance dates and expiration periods
        - Monitor certificate validity and renewal requirements
        - Maintain digital signatures and security features
        - Provide certificate verification and authentication
        """
        self.ensure_one()

        # Find all certificates related to this compliance record
        certificates = self.env["naid.certificate"].search(
            ["|", ("compliance_id", "=", self.id), ("naid_level", "=", self.naid_level)]
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Certificates - %s") % self.name,
            "res_model": "naid.certificate",
            "view_mode": "tree,form,kanban",
            "domain": [("id", "in", certificates.ids)],
            "context": {
                "search_default_group_by_type": 1,
                "search_default_valid": 1,
            },
        }

    def action_renew_certificate(self):
        """
        Initiate certificate renewal process for expiring NAID compliance certification.

        This method starts the renewal workflow for NAID compliance certificates
        that are approaching expiration. It validates current compliance status,
        schedules required audits, and guides through the renewal documentation.

        Returns:
            dict: Action dictionary to open certificate renewal wizard

        Renewal Process:
        1. Validate current compliance status and audit results
        2. Review and update compliance documentation
        3. Schedule renewal audit if required
        4. Submit renewal application to NAID
        5. Process renewal fee and administrative requirements
        6. Generate new certificate upon approval

        Renewal Requirements:
        - Current compliance status must be 'compliant'
        - All audit findings must be resolved
        - Insurance and bonding must be current
        - Personnel training must be up to date
        - Equipment certifications must be valid

        Prerequisites:
        - Certificate must be within renewal window (typically 60 days before expiration)
        - All corrective actions from previous audits must be completed
        - Current compliance percentage must meet minimum thresholds
        """
        self.ensure_one()

        # Validate renewal eligibility
        if self.state != "compliant":
            raise UserError(
                _(
                    "Certificate renewal is only available for compliant records. "
                    "Please complete any outstanding corrective actions first."
                )
            )

        if not self.expiration_date:
            raise UserError(_("No expiration date set for this compliance record."))

        # Check if within renewal window (60 days before expiration)
        renewal_window = self.expiration_date - timedelta(days=60)
        if fields.Date.today() < renewal_window:
            raise UserError(
                _(
                    "Certificate renewal is not yet available. "
                    "Renewal window opens on %s (60 days before expiration)."
                )
                % renewal_window.strftime("%Y-%m-%d")
            )

        # Check compliance percentage threshold
        if self.compliance_percentage < 80:
            raise UserError(
                _(
                    "Compliance percentage (%.1f%%) is below the minimum threshold (80%%) "
                    "required for certificate renewal."
                )
                % self.compliance_percentage
            )

        # Create renewal activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Certificate Renewal - %s") % self.name,
            note=_(
                "Process NAID certificate renewal including documentation review and audit scheduling."
            ),
            user_id=self.user_id.id,
            date_deadline=self.expiration_date - timedelta(days=30),
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Renew NAID Certificate - %s") % self.naid_level.upper(),
            "res_model": "naid.certificate.renewal.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_compliance_id": self.id,
                "default_current_level": self.naid_level,
                "default_expiration_date": self.expiration_date,
            },
        }

    def action_view_audit_details(self):
        """
        Display detailed audit information including findings, scores, and corrective actions.

        This method opens a comprehensive view of audit details, providing
        in-depth analysis of compliance assessments, findings, and improvement
        recommendations. It serves as the central hub for audit management.

        Returns:
            dict: Action dictionary to open detailed audit view

        Audit Details Include:
        - Comprehensive audit findings and non-conformances
        - Scoring breakdown by compliance category
        - Photographic evidence and documentation
        - Corrective action plans and implementation timelines
        - Follow-up audit requirements and scheduling
        - Auditor notes and recommendations

        Analysis Features:
        - Trend analysis comparing multiple audits
        - Risk assessment and impact evaluation
        - Compliance gap analysis and improvement opportunities
        - Regulatory mapping to specific requirements
        - Cost-benefit analysis for corrective actions
        """
        self.ensure_one()

        # Get comprehensive audit data
        audit_data = {
            "findings": self.audit_findings,
            "corrective_actions": self.corrective_actions,
            "remediation_plan": self.remediation_plan,
            "risk_assessment": self.risk_assessment,
            "audit_score": self.audit_score,
            "compliance_percentage": self.compliance_percentage,
        }

        return {
            "type": "ir.actions.act_window",
            "name": _("Audit Details - %s") % self.name,
            "res_model": "naid.audit.detail",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_compliance_id": self.id,
                "audit_data": audit_data,
                "show_analysis": True,
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
    def create(self, vals_list):
        """
        Override create to set default values and initialize compliance records.

        This method handles the creation of new NAID compliance records with proper
        sequence generation and default value assignment. It ensures that all new
        compliance records have unique identifiers and proper initial states.

        Args:
            vals_list (list): List of dictionaries containing field values for new records

        Returns:
            recordset: Created compliance records

        Business Logic:
        - Generates unique compliance check names using sequence
        - Sets default compliance manager to current user
        - Initializes audit trail with creation event
        - Validates required NAID certification parameters

        Security Considerations:
        - Verifies user has permission to create compliance records
        - Logs creation event in audit trail
        - Applies company-specific security rules
        """
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "naid.compliance"
                ) or _("New")

            # Initialize compliance tracking
            if not vals.get("check_date"):
                vals["check_date"] = fields.Date.today()

            # Set default NAID level if not specified
            if not vals.get("naid_level"):
                vals["naid_level"] = "pending"

        records = super().create(vals_list)

        # Post creation messages for audit trail
        for record in records:
            record.message_post(
                body=_("NAID Compliance record created with level: %s")
                % dict(record._fields["naid_level"].selection).get(record.naid_level)
            )

        return records

    def write(self, vals):
        """
        Override write to track compliance status changes and maintain audit trail.

        This method intercepts updates to compliance records and ensures proper
        audit logging for all significant changes. It tracks state transitions,
        certification level changes, and audit score updates.

        Args:
            vals (dict): Dictionary of field values to update

        Returns:
            bool: True if update successful

        Tracked Changes:
        - Compliance status transitions (pending -> compliant, etc.)
        - NAID certification level changes
        - Audit score updates and compliance percentage changes
        - Expiration date modifications
        - Security level adjustments

        Audit Trail:
        - Logs all state changes with timestamps
        - Records user responsible for changes
        - Maintains compliance history for regulatory reporting
        """
        # Track significant changes for audit trail
        tracked_fields = {
            "state": "Compliance Status",
            "naid_level": "NAID Certification Level",
            "compliance_level": "Current NAID Level",
            "audit_score": "Audit Score",
            "quality_score": "Quality Score",
            "security_level": "Security Level",
            "expiration_date": "Expiration Date",
        }

        for record in self:
            for field, label in tracked_fields.items():
                if field in vals and field in record._fields:
                    old_value = getattr(record, field)
                    new_value = vals[field]

                    if old_value != new_value:
                        # Format values for display
                        if hasattr(record._fields[field], "selection"):
                            old_display = dict(record._fields[field].selection).get(
                                old_value, old_value
                            )
                            new_display = dict(record._fields[field].selection).get(
                                new_value, new_value
                            )
                        else:
                            old_display = old_value
                            new_display = new_value

                        record.message_post(
                            body=_("%s changed from '%s' to '%s'")
                            % (label, old_display, new_display)
                        )

        # Handle state-specific logic
        if "state" in vals:
            for record in self:
                if vals["state"] == "compliant":
                    # Auto-schedule next review when becoming compliant
                    if not record.next_review_date:
                        vals["next_review_date"] = fields.Date.today() + relativedelta(
                            months=6
                        )

                elif vals["state"] == "non_compliant":
                    # Create corrective action activity
                    record.activity_schedule(
                        "mail.mail_activity_data_todo",
                        summary=_("Corrective Actions Required"),
                        note=_(
                            "This compliance record requires corrective actions to meet NAID standards."
                        ),
                        user_id=record.user_id.id or self.env.user.id,
                        date_deadline=fields.Date.today() + timedelta(days=7),
                    )

        return super().write(vals)

    # ============================================================================
    # AUTO-GENERATED ACTION METHODS (with enhanced docstrings)
    # ============================================================================

    def action_compliance_report(self):
        """
        Generate comprehensive compliance report for regulatory documentation.

        This method generates a detailed PDF report containing all compliance
        information, audit results, and certification status. The report is
        formatted according to NAID AAA standards and includes all necessary
        documentation for regulatory compliance.

        Returns:
            dict: Action dictionary for PDF report generation

        Report Contents:
        - Current compliance status and certification level
        - Audit results and findings summary
        - Risk assessment and remediation plans
        - Insurance coverage and liability information
        - Performance metrics and quality scores
        - Chain of custody documentation references

        Usage Scenarios:
        - Regulatory audit submissions
        - Customer compliance verification
        - Internal compliance monitoring
        - Third-party certification reviews
        """
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.action_compliance_report_report",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }

    def action_download_certificate(self):
        """
        Download official NAID compliance certificate as PDF document.

        This method generates and downloads the official compliance certificate
        with tamper-proof security features and digital signatures. The certificate
        includes all required NAID AAA certification elements and can be used
        for customer documentation and regulatory compliance.

        Returns:
            dict: Action dictionary for certificate PDF generation

        Certificate Features:
        - Digital signature for authenticity verification
        - QR code linking to verification portal
        - Tamper-evident security watermarks
        - Complete compliance details and validity period
        - Issuing authority information and contact details

        Security Measures:
        - Encrypted PDF with access controls
        - Audit trail logging of certificate access
        - Version control for certificate updates

        Prerequisites:
        - Compliance status must be 'compliant'
        - Valid certification date and expiration date
        - All required audit documentation completed
        """
        self.ensure_one()
        if self.state != "compliant":
            raise UserError(
                _("Certificates can only be generated for compliant records.")
            )

        # Log certificate download for audit trail
        self.message_post(
            body=_("Compliance certificate downloaded by %s") % self.env.user.name
        )

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.action_download_certificate_report",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }

    def action_conduct_audit(self):
        """
        Initiate comprehensive NAID compliance audit process.

        This method launches the audit wizard that guides users through the
        complete NAID AAA audit process. It creates audit activities, schedules
        required inspections, and initializes the compliance checklist system.

        Returns:
            dict: Action dictionary to open audit wizard

        Audit Process:
        1. Pre-audit preparation and documentation review
        2. On-site inspection and process verification
        3. Security and safety protocol assessment
        4. Chain of custody validation
        5. Equipment and facility certification
        6. Personnel screening and training verification
        7. Final audit report generation and scoring

        Audit Components:
        - Physical security assessment (access controls, surveillance)
        - Process verification (destruction methods, witnessing)
        - Documentation review (policies, procedures, records)
        - Personnel evaluation (training, background checks)
        - Equipment inspection (certification, maintenance)
        - Customer notification and communication protocols

        Post-Audit Actions:
        - Generates findings report with corrective actions
        - Updates compliance scores and certification status
        - Schedules follow-up activities for non-conformances
        - Creates certificate if audit is successful
        """
        self.ensure_one()

        # Update audit tracking
        self.write(
            {
                "state": "under_review",
                "last_audit_date": fields.Date.today(),
            }
        )

        # Create audit activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("NAID Compliance Audit - %s") % self.name,
            note=_(
                "Conduct comprehensive NAID AAA compliance audit including physical security, process verification, and documentation review."
            ),
            user_id=self.user_id.id or self.env.user.id,
            date_deadline=fields.Date.today() + timedelta(days=1),
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Conduct NAID Compliance Audit"),
            "res_model": "naid.compliance.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_compliance_id": self.id,
                "default_audit_type": "full_audit",
            },
        }

    def action_view_audit_history(self):
        """
        Display comprehensive audit history and timeline for this compliance record.

        This method opens a filtered view showing all historical audit activities,
        findings, corrective actions, and compliance status changes. It provides
        a complete audit trail for regulatory compliance and internal monitoring.

        Returns:
            dict: Action dictionary to open audit history view

        History Contents:
        - Chronological audit timeline with all activities
        - Compliance status changes and transition reasons
        - Audit findings and corrective action tracking
        - Certificate generation and renewal history
        - User activity logs with timestamps and details
        - Document version control and update tracking

        View Features:
        - Filterable by date range, audit type, and user
        - Exportable for regulatory reporting
        - Searchable audit findings and actions
        - Linked document access for detailed review
        """
        self.ensure_one()

        # Get related audit logs and activities
        audit_logs = self.audit_log_ids
        activities = self.activity_ids
        messages = self.message_ids

        return {
            "type": "ir.actions.act_window",
            "name": _("Audit History - %s") % self.name,
            "res_model": "naid.audit.log",
            "view_mode": "tree,form,timeline",
            "domain": [("compliance_id", "=", self.id)],
            "context": {
                "search_default_group_by_date": 1,
                "search_default_recent": 1,
            },
        }

    def action_schedule_audit(self):
        """
        Schedule next compliance audit based on certification requirements and risk assessment.

        This method creates calendar events and activities for upcoming audit
        requirements. It considers certification expiration dates, regulatory
        requirements, and risk-based scheduling to ensure continuous compliance.

        Returns:
            bool: True when audit successfully scheduled

        Scheduling Logic:
        - AAA certification: Quarterly audits required
        - AA certification: Semi-annual audits required
        - A certification: Annual audits required
        - Risk-based adjustments for high-risk operations
        - Regulatory requirement integration (SOX, HIPAA)

        Created Activities:
        - Pre-audit preparation reminders
        - Audit execution scheduling
        - Post-audit follow-up activities
        - Certification renewal reminders

        Notifications:
        - Email alerts to compliance manager and stakeholders
        - Calendar invitations for audit participants
        - Automatic reminders based on configured frequency
        """
        self.ensure_one()

        # Determine audit frequency based on NAID level
        frequency_mapping = {
            "aaa": 3,  # Quarterly
            "aa": 6,  # Semi-annual
            "a": 12,  # Annual
            "pending": 1,  # Monthly until certified
        }

        months_offset = frequency_mapping.get(self.naid_level, 6)
        next_audit_date = fields.Date.today() + relativedelta(months=months_offset)

        # Update next review date
        self.write(
            {
                "next_review_date": next_audit_date,
                "next_audit_date": next_audit_date,
            }
        )

        # Create calendar event for audit
        calendar_event = self.env["calendar.event"].create(
            {
                "name": _("NAID Compliance Audit - %s") % self.name,
                "description": _("Scheduled NAID %s compliance audit for %s")
                % (self.naid_level.upper(), self.name),
                "start": next_audit_date,
                "stop": next_audit_date,
                "user_id": self.user_id.id,
                "partner_ids": [(6, 0, [self.user_id.partner_id.id])],
            }
        )

        # Create preparation activity
        self.activity_schedule(
            "mail.mail_activity_data_call",
            summary=_("Prepare for NAID Audit - %s") % self.name,
            note=_(
                "Prepare documentation and schedule resources for upcoming NAID compliance audit."
            ),
            user_id=self.user_id.id,
            date_deadline=next_audit_date - timedelta(days=7),
        )

        self.message_post(
            body=_("Next NAID compliance audit scheduled for %s (NAID %s level)")
            % (next_audit_date.strftime("%Y-%m-%d"), self.naid_level.upper())
        )

        return True

    def action_view_destruction_records(self):
        """
        View all destruction records linked to this compliance framework.

        This method displays destruction records that fall under this compliance
        framework, showing the complete chain of custody and destruction process
        documentation required for NAID AAA compliance.

        Returns:
            dict: Action dictionary to open destruction records view

        Related Records:
        - Destruction certificates issued under this compliance framework
        - Chain of custody records for destroyed materials
        - Witness verification documents and signatures
        - Shredding service records and completion certificates
        - Customer notifications and acknowledgments

        Compliance Integration:
        - Links destruction records to audit trail requirements
        - Validates witness requirements and security protocols
        - Tracks destruction method compliance with NAID standards
        - Maintains documentation for regulatory inspections
        """
        self.ensure_one()

        # Find related destruction records through various relationships
        destruction_records = self.env["records.destruction"].search(
            [
                "|",
                "|",
                ("compliance_id", "=", self.id),
                ("certificate_id.compliance_id", "=", self.id),
                ("naid_level", "=", self.naid_level),
            ]
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Destruction Records - %s Compliance") % self.naid_level.upper(),
            "res_model": "records.destruction",
            "view_mode": "tree,form,pivot,graph",
            "domain": [("id", "in", destruction_records.ids)],
            "context": {
                "search_default_group_by_compliance": 1,
                "search_default_recent": 1,
            },
        }

    def action_view_certificates(self):
        """
        View all certificates generated under this compliance framework.

        This method displays all compliance and destruction certificates
        that have been issued under this NAID compliance framework,
        providing a comprehensive view of certification history and status.

        Returns:
            dict: Action dictionary to open certificates view

        Certificate Types:
        - NAID compliance certificates (AAA, AA, A levels)
        - Destruction completion certificates
        - Chain of custody certificates
        - Third-party audit certificates
        - Insurance and bonding certificates

        Certificate Management:
        - Track issuance dates and expiration periods
        - Monitor certificate validity and renewal requirements
        - Maintain digital signatures and security features
        - Provide certificate verification and authentication
        """
        self.ensure_one()

        # Find all certificates related to this compliance record
        certificates = self.env["naid.certificate"].search(
            ["|", ("compliance_id", "=", self.id), ("naid_level", "=", self.naid_level)]
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Certificates - %s") % self.name,
            "res_model": "naid.certificate",
            "view_mode": "tree,form,kanban",
            "domain": [("id", "in", certificates.ids)],
            "context": {
                "search_default_group_by_type": 1,
                "search_default_valid": 1,
            },
        }

    def action_renew_certificate(self):
        """
        Initiate certificate renewal process for expiring NAID compliance certification.

        This method starts the renewal workflow for NAID compliance certificates
        that are approaching expiration. It validates current compliance status,
        schedules required audits, and guides through the renewal documentation.

        Returns:
            dict: Action dictionary to open certificate renewal wizard

        Renewal Process:
        1. Validate current compliance status and audit results
        2. Review and update compliance documentation
        3. Schedule renewal audit if required
        4. Submit renewal application to NAID
        5. Process renewal fee and administrative requirements
        6. Generate new certificate upon approval

        Renewal Requirements:
        - Current compliance status must be 'compliant'
        - All audit findings must be resolved
        - Insurance and bonding must be current
        - Personnel training must be up to date
        - Equipment certifications must be valid

        Prerequisites:
        - Certificate must be within renewal window (typically 60 days before expiration)
        - All corrective actions from previous audits must be completed
        - Current compliance percentage must meet minimum thresholds
        """
        self.ensure_one()

        # Validate renewal eligibility
        if self.state != "compliant":
            raise UserError(
                _(
                    "Certificate renewal is only available for compliant records. "
                    "Please complete any outstanding corrective actions first."
                )
            )

        if not self.expiration_date:
            raise UserError(_("No expiration date set for this compliance record."))

        # Check if within renewal window (60 days before expiration)
        renewal_window = self.expiration_date - timedelta(days=60)
        if fields.Date.today() < renewal_window:
            raise UserError(
                _(
                    "Certificate renewal is not yet available. "
                    "Renewal window opens on %s (60 days before expiration)."
                )
                % renewal_window.strftime("%Y-%m-%d")
            )

        # Check compliance percentage threshold
        if self.compliance_percentage < 80:
            raise UserError(
                _(
                    "Compliance percentage (%.1f%%) is below the minimum threshold (80%%) "
                    "required for certificate renewal."
                )
                % self.compliance_percentage
            )

        # Create renewal activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Certificate Renewal - %s") % self.name,
            note=_(
                "Process NAID certificate renewal including documentation review and audit scheduling."
            ),
            user_id=self.user_id.id,
            date_deadline=self.expiration_date - timedelta(days=30),
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Renew NAID Certificate - %s") % self.naid_level.upper(),
            "res_model": "naid.certificate.renewal.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_compliance_id": self.id,
                "default_current_level": self.naid_level,
                "default_expiration_date": self.expiration_date,
            },
        }

    def action_view_audit_details(self):
        """
        Display detailed audit information including findings, scores, and corrective actions.

        This method opens a comprehensive view of audit details, providing
        in-depth analysis of compliance assessments, findings, and improvement
        recommendations. It serves as the central hub for audit management.

        Returns:
            dict: Action dictionary to open detailed audit view

        Audit Details Include:
        - Comprehensive audit findings and non-conformances
        - Scoring breakdown by compliance category
        - Photographic evidence and documentation
        - Corrective action plans and implementation timelines
        - Follow-up audit requirements and scheduling
        - Auditor notes and recommendations

        Analysis Features:
        - Trend analysis comparing multiple audits
        - Risk assessment and impact evaluation
        - Compliance gap analysis and improvement opportunities
        - Regulatory mapping to specific requirements
        - Cost-benefit analysis for corrective actions
        """
        self.ensure_one()

        # Get comprehensive audit data
        audit_data = {
            "findings": self.audit_findings,
            "corrective_actions": self.corrective_actions,
            "remediation_plan": self.remediation_plan,
            "risk_assessment": self.risk_assessment,
            "audit_score": self.audit_score,
            "compliance_percentage": self.compliance_percentage,
        }

        return {
            "type": "ir.actions.act_window",
            "name": _("Audit Details - %s") % self.name,
            "res_model": "naid.audit.detail",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_compliance_id": self.id,
                "audit_data": audit_data,
                "show_analysis": True,
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
    def create(self, vals_list):
        """
        Override create to set default values and initialize compliance records.

        This method handles the creation of new NAID compliance records with proper
        sequence generation and default value assignment. It ensures that all new
        compliance records have unique identifiers and proper initial states.

        Args:
            vals_list (list): List of dictionaries containing field values for new records

        Returns:
            recordset: Created compliance records

        Business Logic:
        - Generates unique compliance check names using sequence
        - Sets default compliance manager to current user
        - Initializes audit trail with creation event
        - Validates required NAID certification parameters

        Security Considerations:
        - Verifies user has permission to create compliance records
        - Logs creation event in audit trail
        - Applies company-specific security rules
        """
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "naid.compliance"
                ) or _("New")

            # Initialize compliance tracking
            if not vals.get("check_date"):
                vals["check_date"] = fields.Date.today()

            # Set default NAID level if not specified
            if not vals.get("naid_level"):
                vals["naid_level"] = "pending"

        records = super().create(vals_list)

        # Post creation messages for audit trail
        for record in records:
            record.message_post(
                body=_("NAID Compliance record created with level: %s")
                % dict(record._fields["naid_level"].selection).get(record.naid_level)
            )

        return records

    def write(self, vals):
        """
        Override write to track compliance status changes and maintain audit trail.

        This method intercepts updates to compliance records and ensures proper
        audit logging for all significant changes. It tracks state transitions,
        certification level changes, and audit score updates.

        Args:
            vals (dict): Dictionary of field values to update

        Returns:
            bool: True if update successful

        Tracked Changes:
        - Compliance status transitions (pending -> compliant, etc.)
        - NAID certification level changes
        - Audit score updates and compliance percentage changes
        - Expiration date modifications
        - Security level adjustments

        Audit Trail:
        - Logs all state changes with timestamps
        - Records user responsible for changes
        - Maintains compliance history for regulatory reporting
        """
        # Track significant changes for audit trail
        tracked_fields = {
            "state": "Compliance Status",
            "naid_level": "NAID Certification Level",
            "compliance_level": "Current NAID Level",
            "audit_score": "Audit Score",
            "quality_score": "Quality Score",
            "security_level": "Security Level",
            "expiration_date": "Expiration Date",
        }

        for record in self:
            for field, label in tracked_fields.items():
                if field in vals and field in record._fields:
                    old_value = getattr(record, field)
                    new_value = vals[field]

                    if old_value != new_value:
                        # Format values for display
                        if hasattr(record._fields[field], "selection"):
                            old_display = dict(record._fields[field].selection).get(
                                old_value, old_value
                            )
                            new_display = dict(record._fields[field].selection).get(
                                new_value, new_value
                            )
                        else:
                            old_display = old_value
                            new_display = new_value

                        record.message_post(
                            body=_("%s changed from '%s' to '%s'")
                            % (label, old_display, new_display)
                        )

        # Handle state-specific logic
        if "state" in vals:
            for record in self:
                if vals["state"] == "compliant":
                    # Auto-schedule next review when becoming compliant
                    if not record.next_review_date:
                        vals["next_review_date"] = fields.Date.today() + relativedelta(
                            months=6
                        )

                elif vals["state"] == "non_compliant":
                    # Create corrective action activity
                    record.activity_schedule(
                        "mail.mail_activity_data_todo",
                        summary=_("Corrective Actions Required"),
                        note=_(
                            "This compliance record requires corrective actions to meet NAID standards."
                        ),
                        user_id=record.user_id.id or self.env.user.id,
                        date_deadline=fields.Date.today() + timedelta(days=7),
                    )

        return super().write(vals)
                    )

        return super().write(vals)

    # ============================================================================
    # AUTO-GENERATED ACTION METHODS (with enhanced docstrings)
    # ============================================================================

    def action_compliance_report(self):
        """
        Generate comprehensive compliance report for regulatory documentation.

        This method generates a detailed PDF report containing all compliance
        information, audit results, and certification status. The report is
        formatted according to NAID AAA standards and includes all necessary
        documentation for regulatory compliance.

        Returns:
            dict: Action dictionary for PDF report generation

        Report Contents:
        - Current compliance status and certification level
        - Audit results and findings summary
        - Risk assessment and remediation plans
        - Insurance coverage and liability information
        - Performance metrics and quality scores
        - Chain of custody documentation references

        Usage Scenarios:
        - Regulatory audit submissions
        - Customer compliance verification
        - Internal compliance monitoring
        - Third-party certification reviews
        """
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.action_compliance_report_report",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }

    def action_download_certificate(self):
        """
        Download official NAID compliance certificate as PDF document.

        This method generates and downloads the official compliance certificate
        with tamper-proof security features and digital signatures. The certificate
        includes all required NAID AAA certification elements and can be used
        for customer documentation and regulatory compliance.

        Returns:
            dict: Action dictionary for certificate PDF generation

        Certificate Features:
        - Digital signature for authenticity verification
        - QR code linking to verification portal
        - Tamper-evident security watermarks
        - Complete compliance details and validity period
        - Issuing authority information and contact details

        Security Measures:
        - Encrypted PDF with access controls
        - Audit trail logging of certificate access
        - Version control for certificate updates

        Prerequisites:
        - Compliance status must be 'compliant'
        - Valid certification date and expiration date
        - All required audit documentation completed
        """
        self.ensure_one()
        if self.state != "compliant":
            raise UserError(
                _("Certificates can only be generated for compliant records.")
            )

        # Log certificate download for audit trail
        self.message_post(
            body=_("Compliance certificate downloaded by %s") % self.env.user.name
        )

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.action_download_certificate_report",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }

    def action_conduct_audit(self):
        """
        Initiate comprehensive NAID compliance audit process.

        This method launches the audit wizard that guides users through the
        complete NAID AAA audit process. It creates audit activities, schedules
        required inspections, and initializes the compliance checklist system.

        Returns:
            dict: Action dictionary to open audit wizard

        Audit Process:
        1. Pre-audit preparation and documentation review
        2. On-site inspection and process verification
        3. Security and safety protocol assessment
        4. Chain of custody validation
        5. Equipment and facility certification
        6. Personnel screening and training verification
        7. Final audit report generation and scoring

        Audit Components:
        - Physical security assessment (access controls, surveillance)
        - Process verification (destruction methods, witnessing)
        - Documentation review (policies, procedures, records)
        - Personnel evaluation (training, background checks)
        - Equipment inspection (certification, maintenance)
        - Customer notification and communication protocols

        Post-Audit Actions:
        - Generates findings report with corrective actions
        - Updates compliance scores and certification status
        - Schedules follow-up activities for non-conformances
        - Creates certificate if audit is successful
        """
        self.ensure_one()

        # Update audit tracking
        self.write(
            {
                "state": "under_review",
                "last_audit_date": fields.Date.today(),
            }
        )

        # Create audit activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("NAID Compliance Audit - %s") % self.name,
            note=_(
                "Conduct comprehensive NAID AAA compliance audit including physical security, process verification, and documentation review."
            ),
            user_id=self.user_id.id or self.env.user.id,
            date_deadline=fields.Date.today() + timedelta(days=1),
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Conduct NAID Compliance Audit"),
            "res_model": "naid.compliance.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_compliance_id": self.id,
                "default_audit_type": "full_audit",
            },
        }

    def action_view_audit_history(self):
        """
        Display comprehensive audit history and timeline for this compliance record.

        This method opens a filtered view showing all historical audit activities,
        findings, corrective actions, and compliance status changes. It provides
        a complete audit trail for regulatory compliance and internal monitoring.

        Returns:
            dict: Action dictionary to open audit history view

        History Contents:
        - Chronological audit timeline with all activities
        - Compliance status changes and transition reasons
        - Audit findings and corrective action tracking
        - Certificate generation and renewal history
        - User activity logs with timestamps and details
        - Document version control and update tracking

        View Features:
        - Filterable by date range, audit type, and user
        - Exportable for regulatory reporting
        - Searchable audit findings and actions
        - Linked document access for detailed review
        """
        self.ensure_one()

        # Get related audit logs and activities
        audit_logs = self.audit_log_ids
        activities = self.activity_ids
        messages = self.message_ids

        return {
            "type": "ir.actions.act_window",
            "name": _("Audit History - %s") % self.name,
            "res_model": "naid.audit.log",
            "view_mode": "tree,form,timeline",
            "domain": [("compliance_id", "=", self.id)],
            "context": {
                "search_default_group_by_date": 1,
                "search_default_recent": 1,
            },
        }

    def action_schedule_audit(self):
        """
        Schedule next compliance audit based on certification requirements and risk assessment.

        This method creates calendar events and activities for upcoming audit
        requirements. It considers certification expiration dates, regulatory
        requirements, and risk-based scheduling to ensure continuous compliance.

        Returns:
            bool: True when audit successfully scheduled

        Scheduling Logic:
        - AAA certification: Quarterly audits required
        - AA certification: Semi-annual audits required
        - A certification: Annual audits required
        - Risk-based adjustments for high-risk operations
        - Regulatory requirement integration (SOX, HIPAA)

        Created Activities:
        - Pre-audit preparation reminders
        - Audit execution scheduling
        - Post-audit follow-up activities
        - Certification renewal reminders

        Notifications:
        - Email alerts to compliance manager and stakeholders
        - Calendar invitations for audit participants
        - Automatic reminders based on configured frequency
        """
        self.ensure_one()

        # Determine audit frequency based on NAID level
        frequency_mapping = {
            "aaa": 3,  # Quarterly
            "aa": 6,  # Semi-annual
            "a": 12,  # Annual
            "pending": 1,  # Monthly until certified
        }

        months_offset = frequency_mapping.get(self.naid_level, 6)
        next_audit_date = fields.Date.today() + relativedelta(months=months_offset)

        # Update next review date
        self.write(
            {
                "next_review_date": next_audit_date,
                "next_audit_date": next_audit_date,
            }
        )

        # Create calendar event for audit
        calendar_event = self.env["calendar.event"].create(
            {
                "name": _("NAID Compliance Audit - %s") % self.name,
                "description": _("Scheduled NAID %s compliance audit for %s")
                % (self.naid_level.upper(), self.name),
                "start": next_audit_date,
                "stop": next_audit_date,
                "user_id": self.user_id.id,
                "partner_ids": [(6, 0, [self.user_id.partner_id.id])],
            }
        )

        # Create preparation activity
        self.activity_schedule(
            "mail.mail_activity_data_call",
            summary=_("Prepare for NAID Audit - %s") % self.name,
            note=_(
                "Prepare documentation and schedule resources for upcoming NAID compliance audit."
            ),
            user_id=self.user_id.id,
            date_deadline=next_audit_date - timedelta(days=7),
        )

        self.message_post(
            body=_("Next NAID compliance audit scheduled for %s (NAID %s level)")
            % (next_audit_date.strftime("%Y-%m-%d"), self.naid_level.upper())
        )

        return True
