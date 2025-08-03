# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class NaidCompliance(models.Model):
    _name = "naid.compliance"
    _description = "NAID Compliance Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Compliance Check", required=True, tracking=True)
    check_date = fields.Date(string="Check Date", required=True)
    compliance_level = fields.Selection(
        [("aaa", "AAA Certified"), ("aa", "AA Certified"), ("a", "A Certified")],
        string="NAID Level",
    )
    certificate_id = fields.Many2one("naid.certificate", string="Certificate")
    audit_results = fields.Text(string="Audit Results")
    corrective_actions = fields.Text(string="Corrective Actions")
    next_review_date = fields.Date(string="Next Review Date")
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("compliant", "Compliant"),
            ("non_compliant", "Non-Compliant"),
        ],
        default="pending",
    )

    # Essential NAID Compliance Fields (from view analysis)
    naid_level = fields.Selection(
        [
            ("aaa", "NAID AAA"),
            ("pending", "Pending Certification"),
            ("expired", "Expired"),
        ],
        string="NAID Certification Level",
        required=True,
        tracking=True,
    )

    compliance_status = fields.Selection(
        [
            ("compliant", "Compliant"),
            ("non_compliant", "Non-Compliant"),
            ("pending_review", "Pending Review"),
            ("remediation_required", "Remediation Required"),
            ("under_audit", "Under Audit"),
        ],
        string="Compliance Status",
        default="pending_review",
        tracking=True,
    )

    # Certification Dates
    certification_date = fields.Date(string="Certification Date", tracking=True)
    expiry_date = fields.Date(string="Expiry Date", tracking=True)

    # Audit Management
    audit_required = fields.Boolean(string="Audit Required", default=True)
    audit_date = fields.Date(string="Audit Date")
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

    # Certificate Management
    certificate_valid = fields.Boolean(
        string="Certificate Valid", compute="_compute_certificate_status"
    )
    certificate_number = fields.Char(string="Certificate Number")

    # Facility Information
    facility_name = fields.Char(string="Facility Name", required=True)
    facility_address = fields.Text(string="Facility Address")
    facility_contact = fields.Many2one("res.partner", string="Facility Contact")

    # Compliance Requirements
    physical_security_verified = fields.Boolean(
        string="Physical Security Verified", default=False
    )
    access_control_verified = fields.Boolean(
        string="Access Control Verified", default=False
    )
    personnel_screening_verified = fields.Boolean(
        string="Personnel Screening Verified", default=False
    )
    destruction_process_verified = fields.Boolean(
        string="Destruction Process Verified", default=False
    )

    # Documentation
    compliance_documentation = fields.Text(string="Compliance Documentation")
    audit_trail_enabled = fields.Boolean(string="Audit Trail Enabled", default=True)
    chain_of_custody_maintained = fields.Boolean(
        string="Chain of Custody Maintained", default=True
    )

    # Reporting and Analytics
    compliance_score = fields.Float(
        string="Compliance Score (%)",
        digits=(5, 2),
        compute="_compute_compliance_score",
    )
    risk_level = fields.Selection(
        [
            ("low", "Low Risk"),
            ("medium", "Medium Risk"),
            ("high", "High Risk"),
            ("critical", "Critical Risk"),
        ],
        string="Risk Level",
        compute="_compute_risk_level",
    )

    # Audit History
    audit_history_ids = fields.One2many(
        "naid.audit.log", "compliance_id", string="Audit History"
    )
    last_audit_date = fields.Date(
        string="Last Audit Date", compute="_compute_last_audit"
    )

    # Reminder and Notifications
    audit_reminder = fields.Date(string="Audit Reminder Date")
    notification_sent = fields.Boolean(string="Notification Sent", default=False)

    # Related Records
    employee_ids = fields.Many2many("hr.employee", string="Certified Employees")
    equipment_ids = fields.Many2many(
        "maintenance.equipment", string="Certified Equipment"
    )

    # === COMPREHENSIVE NAID COMPLIANCE FIELDS ===

    # Enhanced NAID Configuration
    naid_member_id = fields.Char(string="NAID Member ID", tracking=True)
    auto_renewal = fields.Boolean(string="Auto Renewal", default=False, tracking=True)

    # Enhanced Audit Management
    next_audit_date = fields.Date(
        string="Next Audit Date", compute="_compute_next_audit_date", store=True
    )

    # Compliance Team
    compliance_officer = fields.Many2one(
        "hr.employee", string="Compliance Officer", tracking=True
    )
    facility_manager = fields.Many2one(
        "hr.employee", string="Facility Manager", tracking=True
    )
    security_officer = fields.Many2one(
        "hr.employee", string="Security Officer", tracking=True
    )
    third_party_auditor = fields.Many2one(
        "res.partner", string="Third Party Auditor", tracking=True
    )

    # Physical Security Standards
    physical_security_score = fields.Float(
        string="Physical Security Score", digits=(3, 1)
    )
    surveillance_system = fields.Boolean(string="Surveillance System", default=False)
    secure_storage = fields.Boolean(string="Secure Storage", default=False)

    # Personnel Security
    personnel_screening = fields.Boolean(string="Personnel Screening", default=False)
    background_checks = fields.Boolean(string="Background Checks", default=False)
    training_completed = fields.Boolean(string="Training Completed", default=False)
    security_clearance = fields.Boolean(string="Security Clearance", default=False)

    # Information Security
    information_handling = fields.Boolean(string="Information Handling", default=False)
    chain_of_custody = fields.Boolean(string="Chain of Custody", default=False)
    destruction_verification = fields.Boolean(
        string="Destruction Verification", default=False
    )
    certificate_tracking = fields.Boolean(string="Certificate Tracking", default=False)

    # Operational Security
    equipment_certification = fields.Boolean(
        string="Equipment Certification", default=False
    )
    process_verification = fields.Boolean(string="Process Verification", default=False)
    quality_control = fields.Boolean(string="Quality Control", default=False)
    incident_management = fields.Boolean(string="Incident Management", default=False)

    # Count Fields for Stat Buttons
    audit_count = fields.Integer(
        string="Audit Count", compute="_compute_counts", store=True
    )
    certificate_count = fields.Integer(
        string="Certificate Count", compute="_compute_counts", store=True
    )
    destruction_count = fields.Integer(
        string="Destruction Count", compute="_compute_counts", store=True
    )

    # Audit Records and History
    certificate_ids = fields.One2many(
        "naid.certificate", "compliance_id", string="Certificates"
    )

    # Risk Assessment
    risk_assessment_date = fields.Date(string="Risk Assessment Date")
    mitigation_plans = fields.Text(string="Mitigation Plans")

    # Compliance Scoring
    security_score = fields.Float(string="Security Score (%)", digits=(5, 2))
    operational_score = fields.Float(string="Operational Score (%)", digits=(5, 2))

    # Training and Certification
    training_program_id = fields.Many2one("hr.training", string="Training Program")
    training_records = fields.Text(string="Training Records")
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

    # Insurance and Legal
    insurance_coverage = fields.Monetary(
        string="Insurance Coverage", currency_field="currency_id"
    )
    liability_limit = fields.Monetary(
        string="Liability Limit", currency_field="currency_id"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    legal_requirements = fields.Text(string="Legal Requirements")

    # Environmental and Safety
    environmental_compliance = fields.Boolean(
        string="Environmental Compliance", default=True
    )
    safety_protocols = fields.Text(string="Safety Protocols")
    emergency_procedures = fields.Text(string="Emergency Procedures")

    # Quality Management
    quality_management_system = fields.Boolean(
        string="Quality Management System", default=False
    )
    iso_certification = fields.Char(string="ISO Certification")
    quality_metrics = fields.Text(string="Quality Metrics")

    # Technology and Systems
    security_system_version = fields.Char(string="Security System Version")
    monitoring_tools = fields.Text(string="Monitoring Tools")
    backup_systems = fields.Boolean(string="Backup Systems", default=False)

    # Customer and Stakeholder Management
    customer_notifications = fields.Boolean(
        string="Customer Notifications", default=True
    )
    stakeholder_communication = fields.Text(string="Stakeholder Communication")
    public_disclosure = fields.Boolean(string="Public Disclosure", default=False)

    # Continuous Improvement
    improvement_plan = fields.Text(string="Improvement Plan")
    lessons_learned = fields.Text(string="Lessons Learned")
    best_practices = fields.Text(string="Best Practices")

    # Vendor and Supplier Management
    vendor_compliance = fields.Boolean(string="Vendor Compliance", default=False)
    supplier_audits = fields.Boolean(string="Supplier Audits", default=False)
    third_party_certifications = fields.Text(string="Third Party Certifications")

    # Reporting and Documentation
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
    documentation_standard = fields.Selection(
        [
            ("naid", "NAID Standard"),
            ("iso", "ISO Standard"),
            ("custom", "Custom Standard"),
        ],
        string="Documentation Standard",
        default="naid",
    )

    # Performance Metrics
    destruction_volume = fields.Float(
        string="Destruction Volume (tons)", digits=(10, 2)
    )
    processing_time = fields.Float(
        string="Average Processing Time (hours)", digits=(5, 2)
    )
    customer_satisfaction = fields.Float(
        string="Customer Satisfaction (%)", digits=(5, 2)
    )

    # Compliance Dates and Deadlines
    last_review_date = fields.Date(string="Last Review Date")
    compliance_deadline = fields.Date(string="Compliance Deadline")

    # Geographic and Regional
    region = fields.Selection(
        [
            ("north", "North Region"),
            ("south", "South Region"),
            ("east", "East Region"),
            ("west", "West Region"),
            ("central", "Central Region"),
        ],
        string="Region",
    )
    jurisdiction = fields.Char(string="Jurisdiction")
    regulatory_body = fields.Char(string="Regulatory Body")

    @api.depends("certification_date", "expiry_date")
    def _compute_certificate_status(self):
        """Compute if certificate is valid"""
        for record in self:
            if record.certification_date and record.expiry_date:
                today = fields.Date.today()
                record.certificate_valid = record.expiry_date >= today
            else:
                record.certificate_valid = False

    @api.depends(
        "physical_security_verified",
        "access_control_verified",
        "personnel_screening_verified",
        "destruction_process_verified",
    )
    def _compute_compliance_score(self):
        """Compute compliance score based on verification checks"""
        for record in self:
            checks = [
                record.physical_security_verified,
                record.access_control_verified,
                record.personnel_screening_verified,
                record.destruction_process_verified,
            ]
            score = (sum(checks) / len(checks)) * 100 if checks else 0
            record.compliance_score = score

    @api.depends("compliance_score", "certificate_valid")
    def _compute_risk_level(self):
        """Compute risk level based on compliance score and certificate status"""
        for record in self:
            if not record.certificate_valid:
                record.risk_level = "critical"
            elif record.compliance_score < 50:
                record.risk_level = "high"
            elif record.compliance_score < 75:
                record.risk_level = "medium"
            else:
                record.risk_level = "low"

    @api.depends("audit_history_ids")
    def _compute_last_audit(self):
        """Compute last audit date from audit history"""
        for record in self:
            if record.audit_history_ids:
                record.last_audit_date = max(
                    record.audit_history_ids.mapped("audit_date")
                )
            else:
                record.last_audit_date = False

    @api.depends("last_audit_date", "audit_frequency")
    def _compute_next_audit_date(self):
        """Compute next audit date based on frequency."""
        for record in self:
            if record.last_audit_date and record.audit_frequency:
                if record.audit_frequency == "monthly":
                    record.next_audit_date = fields.Date.add(
                        record.last_audit_date, days=30
                    )
                elif record.audit_frequency == "quarterly":
                    record.next_audit_date = fields.Date.add(
                        record.last_audit_date, days=90
                    )
                elif record.audit_frequency == "semi_annual":
                    record.next_audit_date = fields.Date.add(
                        record.last_audit_date, days=180
                    )
                elif record.audit_frequency == "annual":
                    record.next_audit_date = fields.Date.add(
                        record.last_audit_date, days=365
                    )
                else:
                    record.next_audit_date = False
            else:
                record.next_audit_date = False

    @api.depends("audit_history_ids", "certificate_ids")
    def _compute_counts(self):
        """Compute counts for stat buttons."""
        for record in self:
            record.audit_count = len(record.audit_history_ids)
            record.certificate_count = len(record.certificate_ids)
            # Count related destruction records
            record.destruction_count = self.env["shredding.service"].search_count(
                [("naid_compliance_id", "=", record.id)]
            )

    @api.depends("physical_security_score", "security_score", "operational_score")
    def _compute_compliance_score(self):
        """Compute overall compliance score."""
        for record in self:
            scores = [
                record.physical_security_score or 0,
                record.security_score or 0,
                record.operational_score or 0,
            ]
            record.compliance_score = (
                sum(scores) / len([s for s in scores if s > 0]) if any(scores) else 0
            )

    @api.depends("last_review_date", "reporting_frequency")
    def _compute_next_review_date(self):
        """Compute next review date based on frequency."""
        for record in self:
            if record.last_review_date and record.reporting_frequency:
                if record.reporting_frequency == "weekly":
                    record.next_review_date = fields.Date.add(
                        record.last_review_date, days=7
                    )
                elif record.reporting_frequency == "monthly":
                    record.next_review_date = fields.Date.add(
                        record.last_review_date, days=30
                    )
                elif record.reporting_frequency == "quarterly":
                    record.next_review_date = fields.Date.add(
                        record.last_review_date, days=90
                    )
                elif record.reporting_frequency == "annually":
                    record.next_review_date = fields.Date.add(
                        record.last_review_date, days=365
                    )
                else:
                    record.next_review_date = False
            else:
                record.next_review_date = False

    # Additional fields for comprehensive compliance management
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Compliance Manager", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)

    # =============================================================================
    # NAID COMPLIANCE ACTION METHODS
    # =============================================================================

    def action_compliance_report(self):
        """Generate compliance report."""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.naid_compliance_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        }

    def action_conduct_audit(self):
        """Conduct NAID compliance audit."""
        self.ensure_one()
        # Create audit activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=f"NAID Compliance Audit: {self.name}",
            note="Conduct comprehensive NAID compliance audit including documentation review, facility inspection, and process verification.",
            user_id=self.user_id.id,
        )
        self.message_post(body="NAID compliance audit scheduled and initiated.")
        return True

    def action_download_certificate(self):
        """Download NAID certificate."""
        self.ensure_one()
        if not self.certificate_id:
            raise UserError("No certificate associated with this compliance record.")

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/naid.certificate/{self.certificate_id.id}/certificate_file?download=true",
            "target": "new",
        }

    def action_generate_certificate(self):
        """Generate new NAID certificate."""
        self.ensure_one()
        # Create new certificate record
        certificate_vals = {
            "name": f"NAID Certificate - {self.name}",
            "compliance_id": self.id,
            "issue_date": fields.Date.today(),
            "expiry_date": fields.Date.today().replace(
                year=fields.Date.today().year + 1
            ),
            "certification_level": self.compliance_level,
        }

        certificate = self.env["naid.certificate"].create(certificate_vals)
        self.certificate_id = certificate.id
        self.message_post(body=f"New NAID certificate generated: {certificate.name}")

        return {
            "type": "ir.actions.act_window",
            "name": "Generated Certificate",
            "res_model": "naid.certificate",
            "res_id": certificate.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_renew_certificate(self):
        """Renew existing NAID certificate."""
        self.ensure_one()
        if not self.certificate_id:
            raise UserError(
                "No certificate to renew. Please generate a new certificate first."
            )

        # Update certificate expiry date
        new_expiry = fields.Date.today().replace(year=fields.Date.today().year + 1)
        self.certificate_id.write(
            {
                "expiry_date": new_expiry,
                "renewal_date": fields.Date.today(),
            }
        )

        self.message_post(body=f"NAID certificate renewed until {new_expiry}")
        return True

    def action_schedule_audit(self):
        """Schedule next compliance audit."""
        self.ensure_one()

        # Calculate next audit date (typically annual)

    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    sequence = fields.Integer(string="Sequence", default=10)
    notes = fields.Text(string="Notes")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")
    # === COMPREHENSIVE MISSING FIELDS ===
    workflow_state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], string='Workflow State', default='draft')
    next_action_date = fields.Date(string='Next Action Date')
    deadline_date = fields.Date(string='Deadline')
    completion_date = fields.Datetime(string='Completion Date')
    responsible_user_id = fields.Many2one('res.users', string='Responsible User')
    assigned_team_id = fields.Many2one('hr.department', string='Assigned Team')
    supervisor_id = fields.Many2one('res.users', string='Supervisor')
    quality_checked = fields.Boolean(string='Quality Checked')
    quality_score = fields.Float(string='Quality Score', digits=(3, 2))
    validation_required = fields.Boolean(string='Validation Required')
    validated_by_id = fields.Many2one('res.users', string='Validated By')
    validation_date = fields.Datetime(string='Validation Date')
    reference_number = fields.Char(string='Reference Number')
    external_reference = fields.Char(string='External Reference')
    documentation_complete = fields.Boolean(string='Documentation Complete')
    attachment_ids = fields.One2many('ir.attachment', 'res_id', string='Attachments')
    performance_score = fields.Float(string='Performance Score', digits=(5, 2))
    efficiency_rating = fields.Selection([('poor', 'Poor'), ('fair', 'Fair'), ('good', 'Good'), ('excellent', 'Excellent')], string='Efficiency Rating')
    # NAID Compliance Management Fields
    audit_result = fields.Selection([('pass', 'Pass'), ('fail', 'Fail'), ('conditional', 'Conditional')], 'Audit Result')
    audit_scope = fields.Selection([('full', 'Full Audit'), ('partial', 'Partial'), ('focused', 'Focused')], default='full')
    audit_type = fields.Selection([('initial', 'Initial'), ('surveillance', 'Surveillance'), ('recertification', 'Recertification')], default='surveillance')
    auditor_name = fields.Char('Auditor Name')
    benchmark = fields.Selection([('aaa', 'NAID AAA'), ('aa', 'NAID AA'), ('a', 'NAID A')], default='aaa')
    certificate_expiration_date = fields.Date('Certificate Expiration Date')
    certificate_issue_date = fields.Date('Certificate Issue Date')
    certificate_status = fields.Selection([('active', 'Active'), ('expired', 'Expired'), ('suspended', 'Suspended'), ('revoked', 'Revoked')], default='active')
    compliance_documentation_complete = fields.Boolean('Compliance Documentation Complete', default=False)
    compliance_manager_id = fields.Many2one('hr.employee', 'Compliance Manager')
    compliance_officer_id = fields.Many2one('hr.employee', 'Compliance Officer')
    compliance_review_date = fields.Date('Compliance Review Date')
    compliance_training_completed = fields.Boolean('Compliance Training Completed', default=False)
    corrective_action_plan = fields.Text('Corrective Action Plan')
    corrective_actions_required = fields.Boolean('Corrective Actions Required', default=False)
    destruction_method_approved = fields.Boolean('Destruction Method Approved', default=False)
    documentation_retention_period = fields.Integer('Documentation Retention Period (Years)', default=7)
    employee_training_records = fields.Text('Employee Training Records')
    equipment_certification_current = fields.Boolean('Equipment Certification Current', default=False)
    facility_security_assessment = fields.Text('Facility Security Assessment')
    internal_audit_frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')], default='quarterly')
    next_audit_due_date = fields.Date('Next Audit Due Date')
    non_conformance_count = fields.Integer('Non-conformance Count', default=0)
    operational_procedures_current = fields.Boolean('Operational Procedures Current', default=False)
    regulatory_compliance_verified = fields.Boolean('Regulatory Compliance Verified', default=False)
    risk_assessment_completed = fields.Boolean('Risk Assessment Completed', default=False)
    security_clearance_level = fields.Selection([('public', 'Public'), ('secret', 'Secret'), ('top_secret', 'Top Secret')], default='public')
    staff_background_checks_current = fields.Boolean('Staff Background Checks Current', default=False)
    surveillance_audit_frequency = fields.Selection([('quarterly', 'Quarterly'), ('semi_annual', 'Semi-annual'), ('annual', 'Annual')], default='annual')


    def schedule_next_audit(self):
        """Schedule next audit."""
        # Create new compliance record for next audit
        next_audit_vals = {
            "name": f"Scheduled Audit - {fields.Date.today().year + 1}",
            "check_date": self.next_audit_date,
            "compliance_level": self.compliance_level,
            "state": "pending",
        }

        next_audit = self.create(next_audit_vals)

        # Schedule activity for next audit
        next_audit.activity_schedule(
            "mail.mail_activity_data_todo",
            date_deadline=self.next_audit_date,
            summary="Annual NAID Compliance Audit Due",
            note="Annual NAID compliance audit is due. Please conduct comprehensive review and documentation.",
            user_id=self.user_id.id,
        )

        self.message_post(body=f"Next NAID audit scheduled for {self.next_audit_date}")
        return True

    def action_view_audit_details(self):
        """View detailed audit information."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Audit Details",
            "res_model": "naid.compliance",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_view_audit_history(self):
        """View compliance audit history."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "NAID Audit History",
            "res_model": "naid.compliance",
            "view_mode": "tree,form",
            "domain": [("company_id", "=", self.company_id.id)],
            "context": {"search_default_company_id": self.company_id.id},
        }

    def action_view_certificates(self):
        """View all NAID certificates."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "NAID Certificates",
            "res_model": "naid.certificate",
            "view_mode": "tree,form",
            "domain": [("compliance_id", "=", self.id)],
            "context": {
                "default_compliance_id": self.id,
                "search_default_compliance_id": self.id,
            },
        }

    def action_view_destruction_records(self):
        """View destruction records related to this compliance."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Destruction Records",
            "res_model": "naid.destruction.record",
            "view_mode": "tree,form",
            "domain": [("compliance_id", "=", self.id)],
            "context": {
                "default_compliance_id": self.id,
                "search_default_compliance_id": self.id,
            },
        }
