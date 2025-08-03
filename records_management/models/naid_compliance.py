# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


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

    # === COMPREHENSIVE NAID COMPLIANCE MISSING FIELDS ===

    # Certificate Management
    certificate_issued = fields.Boolean(string="Certificate Issued", default=False)
    certificate_type = fields.Selection(
        [
            ("plant_certificate", "Plant Certificate"),
            ("mobile_certificate", "Mobile Certificate"),
            ("employee_certificate", "Employee Certificate"),
            ("hard_drive_certificate", "Hard Drive Certificate"),
        ],
        string="Certificate Type",
        required=True,
    )

    # Client and Project Information
    client_name = fields.Char(string="Client Name", required=True)
    client_contact = fields.Many2one("res.partner", string="Client Contact")
    project_reference = fields.Char(string="Project Reference")
    service_location = fields.Char(string="Service Location")

    # Compliance Alerts and Monitoring
    compliance_alerts = fields.One2many(
        "naid.compliance.alert", "compliance_id", string="Compliance Alerts"
    )
    alert_count = fields.Integer(string="Alert Count", compute="_compute_alert_count")
    critical_alerts_count = fields.Integer(
        string="Critical Alerts", compute="_compute_critical_alerts"
    )

    # Compliance Checklist Integration
    compliance_checklist_ids = fields.One2many(
        "naid.compliance.checklist.item", "compliance_id", string="Compliance Checklist"
    )
    checklist_completion_rate = fields.Float(
        string="Checklist Completion (%)", compute="_compute_checklist_completion"
    )

    # Audit and Review Management
    audit_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annually", "Semi-Annually"),
            ("annually", "Annually"),
        ],
        string="Audit Frequency",
        default="quarterly",
    )

    last_audit_date = fields.Date(string="Last Audit Date")
    next_audit_date = fields.Date(
        string="Next Audit Date", compute="_compute_next_audit_date"
    )
    audit_due = fields.Boolean(string="Audit Due", compute="_compute_audit_due")
    auditor_name = fields.Char(string="Auditor Name")
    audit_score = fields.Float(string="Audit Score (%)", digits=(5, 2))

    # Risk Assessment and Management
    risk_level = fields.Selection(
        [
            ("low", "Low Risk"),
            ("medium", "Medium Risk"),
            ("high", "High Risk"),
            ("critical", "Critical Risk"),
        ],
        string="Risk Level",
        default="low",
    )

    risk_factors = fields.Text(string="Identified Risk Factors")
    mitigation_plans = fields.Text(string="Risk Mitigation Plans")
    risk_assessment_date = fields.Date(string="Risk Assessment Date")

    # Facility and Equipment Compliance
    facility_certification = fields.Boolean(string="Facility Certified", default=False)
    equipment_certification = fields.Boolean(
        string="Equipment Certified", default=False
    )
    security_certification = fields.Boolean(string="Security Certified", default=False)
    personnel_certification = fields.Boolean(
        string="Personnel Certified", default=False
    )

    # Chain of Custody Integration
    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required", default=True
    )
    custody_documentation = fields.Boolean(
        string="Custody Documentation Complete", default=False
    )
    witness_requirements = fields.Boolean(
        string="Witness Requirements Met", default=False
    )
    destruction_verification = fields.Boolean(
        string="Destruction Verified", default=False
    )

    # Environmental and Operational Standards
    environmental_compliance = fields.Boolean(
        string="Environmental Compliance", default=False
    )
    operational_procedures = fields.Boolean(
        string="Operational Procedures Verified", default=False
    )
    quality_standards = fields.Boolean(string="Quality Standards Met", default=False)
    safety_protocols = fields.Boolean(
        string="Safety Protocols Implemented", default=False
    )

    # Documentation and Record Keeping
    documentation_complete = fields.Boolean(
        string="Documentation Complete", default=False
    )
    record_retention_compliance = fields.Boolean(
        string="Record Retention Compliance", default=False
    )
    policy_documentation = fields.Boolean(
        string="Policy Documentation Current", default=False
    )
    training_records = fields.Boolean(string="Training Records Complete", default=False)

    # Compliance Tracking and Metrics
    compliance_score = fields.Float(
        string="Overall Compliance Score (%)",
        digits=(5, 2),
        compute="_compute_compliance_score",
    )
    improvement_areas = fields.Text(string="Areas for Improvement")
    corrective_action_plan = fields.Text(string="Corrective Action Plan")
    action_items_count = fields.Integer(
        string="Action Items Count", compute="_compute_action_items"
    )

    # Integration with Records Management
    records_count = fields.Integer(
        string="Related Records Count", compute="_compute_records_count"
    )
    destruction_count = fields.Integer(
        string="Destruction Records Count", compute="_compute_destruction_count"
    )
    storage_compliance = fields.Boolean(string="Storage Compliance", default=False)
    retrieval_compliance = fields.Boolean(string="Retrieval Compliance", default=False)

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

    # === COMPREHENSIVE COMPUTE METHODS FOR NEW FIELDS ===

    @api.depends("compliance_alerts")
    def _compute_alert_count(self):
        """Compute total number of compliance alerts"""
        for record in self:
            record.alert_count = len(record.compliance_alerts)

    @api.depends("compliance_alerts", "compliance_alerts.severity")
    def _compute_critical_alerts(self):
        """Compute number of critical alerts"""
        for record in self:
            record.critical_alerts_count = len(
                record.compliance_alerts.filtered(lambda a: a.severity == "critical")
            )

    @api.depends("compliance_checklist_ids", "compliance_checklist_ids.completed")
    def _compute_checklist_completion(self):
        """Compute checklist completion percentage"""
        for record in self:
            if record.compliance_checklist_ids:
                completed_items = len(
                    record.compliance_checklist_ids.filtered(lambda c: c.completed)
                )
                total_items = len(record.compliance_checklist_ids)
                record.checklist_completion_rate = (
                    (completed_items / total_items) * 100 if total_items > 0 else 0
                )
            else:
                record.checklist_completion_rate = 0

    @api.depends("last_audit_date", "audit_frequency")
    def _compute_next_audit_date(self):
        """Compute next audit date based on frequency"""
        for record in self:
            if record.last_audit_date and record.audit_frequency:
                days_to_add = {
                    "monthly": 30,
                    "quarterly": 90,
                    "semi_annually": 180,
                    "annually": 365,
                }.get(record.audit_frequency, 365)

                record.next_audit_date = fields.Date.add(
                    record.last_audit_date, days=days_to_add
                )
            else:
                record.next_audit_date = False

    @api.depends("next_audit_date")
    def _compute_audit_due(self):
        """Compute if audit is due"""
        for record in self:
            if record.next_audit_date:
                today = fields.Date.today()
                record.audit_due = record.next_audit_date <= today
            else:
                record.audit_due = False

    @api.depends(
        "facility_certification",
        "equipment_certification",
        "security_certification",
        "personnel_certification",
        "environmental_compliance",
        "operational_procedures",
        "quality_standards",
        "safety_protocols",
    )
    def _compute_compliance_score(self):
        """Compute overall compliance score based on all certification factors"""
        for record in self:
            # Count certified components
            certifications = [
                record.facility_certification,
                record.equipment_certification,
                record.security_certification,
                record.personnel_certification,
                record.environmental_compliance,
                record.operational_procedures,
                record.quality_standards,
                record.safety_protocols,
            ]

            certified_count = sum(1 for cert in certifications if cert)
            total_count = len(certifications)

            record.compliance_score = (
                (certified_count / total_count) * 100 if total_count > 0 else 0
            )

    @api.depends("corrective_action_plan")
    def _compute_action_items(self):
        """Compute number of action items from corrective action plan"""
        for record in self:
            if record.corrective_action_plan:
                # Simple count based on line breaks - could be enhanced with proper parsing
                lines = record.corrective_action_plan.split("\n")
                action_lines = [
                    line
                    for line in lines
                    if line.strip() and not line.strip().startswith("#")
                ]
                record.action_items_count = len(action_lines)
            else:
                record.action_items_count = 0

    @api.depends("client_name")
    def _compute_records_count(self):
        """Compute count of related records"""
        for record in self:
            if record.client_name:
                # Count records related to this compliance check
                related_records = self.env["records.document"].search_count(
                    [("partner_id.name", "ilike", record.client_name)]
                )
                record.records_count = related_records
            else:
                record.records_count = 0

    @api.depends("client_name")
    def _compute_destruction_count(self):
        """Compute count of destruction records"""
        for record in self:
            if record.client_name:
                # Count destruction services related to this compliance
                destruction_records = self.env["shredding.service"].search_count(
                    [("customer_id.name", "ilike", record.client_name)]
                )
                record.destruction_count = destruction_records
            else:
                record.destruction_count = 0

    @api.depends("compliance_alerts")
    def _compute_alert_count(self):
        """Compute total number of compliance alerts"""
        for record in self:
            record.alert_count = len(record.compliance_alerts)

    @api.depends("compliance_alerts")
    def _compute_critical_alerts(self):
        """Compute number of critical alerts"""
        for record in self:
            critical_alerts = record.compliance_alerts.filtered(
                lambda alert: alert.severity == "critical"
            )
            record.critical_alerts_count = len(critical_alerts)

    @api.depends("compliance_checklist_ids")
    def _compute_checklist_completion(self):
        """Compute checklist completion percentage"""
        for record in self:
            if record.compliance_checklist_ids:
                completed_items = record.compliance_checklist_ids.filtered("completed")
                total_items = len(record.compliance_checklist_ids)
                record.checklist_completion_rate = (
                    (len(completed_items) / total_items) * 100 if total_items > 0 else 0
                )
            else:
                record.checklist_completion_rate = 0

    @api.depends("last_audit_date", "audit_frequency")
    def _compute_next_audit_date(self):
        """Compute next audit date based on frequency and last audit"""
        for record in self:
            if record.last_audit_date and record.audit_frequency:
                if record.audit_frequency == "monthly":
                    days_to_add = 30
                elif record.audit_frequency == "quarterly":
                    days_to_add = 90
                elif record.audit_frequency == "semi_annually":
                    days_to_add = 180
                elif record.audit_frequency == "annually":
                    days_to_add = 365
                else:
                    days_to_add = 365  # Default to annual

                record.next_audit_date = fields.Date.add(
                    record.last_audit_date, days=days_to_add
                )
            else:
                record.next_audit_date = False

    @api.depends("next_audit_date")
    def _compute_audit_due(self):
        """Compute if audit is due"""
        for record in self:
            if record.next_audit_date:
                today = fields.Date.today()
                record.audit_due = record.next_audit_date <= today
            else:
                record.audit_due = False

    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Compliance Manager", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)

    # === MISSING FIELDS FROM VIEW ANALYSIS ===

    # Compliance Trends and Analytics
    compliance_trend = fields.Selection(
        [
            ("improving", "Improving"),
            ("stable", "Stable"),
            ("declining", "Declining"),
            ("critical", "Critical"),
        ],
        string="Compliance Trend",
        compute="_compute_compliance_trend",
    )

    compliance_verified = fields.Boolean(
        string="Compliance Verified", default=False, tracking=True
    )

    # Time-based Analytics
    days_since_last_audit = fields.Integer(
        string="Days Since Last Audit", compute="_compute_days_since_audit"
    )
    days_until_expiry = fields.Integer(
        string="Days Until Expiry", compute="_compute_days_until_expiry"
    )

    # Destruction and Processing
    destruction_date = fields.Date(string="Destruction Date", tracking=True)
    destruction_facility = fields.Char(string="Destruction Facility")
    destruction_witness = fields.Many2one("hr.employee", string="Destruction Witness")
    destruction_notes = fields.Text(string="Destruction Notes")

    # Advanced Compliance Fields
    archive_date = fields.Date(string="Archive Date")
    assessment_frequency = fields.Selection(
        [
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annually", "Annually"),
        ],
        string="Assessment Frequency",
        default="quarterly",
    )

    authorization_level = fields.Selection(
        [
            ("basic", "Basic"),
            ("advanced", "Advanced"),
            ("executive", "Executive"),
            ("administrator", "Administrator"),
        ],
        string="Authorization Level",
        default="basic",
    )

    certificate_valid_until = fields.Date(
        string="Certificate Valid Until", tracking=True
    )
    certification_body = fields.Char(string="Certification Body", default="NAID")

    # Customer and Partner Information
    customer_notification_date = fields.Date(string="Customer Notification Date")
    customer_representative = fields.Many2one(
        "res.partner", string="Customer Representative"
    )

    # Documentation and Evidence
    evidence_collected = fields.Boolean(string="Evidence Collected", default=False)
    evidence_storage_location = fields.Char(string="Evidence Storage Location")

    # Workflow and Processing
    follow_up_date = fields.Date(string="Follow-up Date")
    follow_up_required = fields.Boolean(string="Follow-up Required", default=False)

    # Integration and Systems
    integration_status = fields.Selection(
        [
            ("not_integrated", "Not Integrated"),
            ("partially_integrated", "Partially Integrated"),
            ("fully_integrated", "Fully Integrated"),
        ],
        string="Integration Status",
        default="not_integrated",
    )

    # Notification and Communication
    notification_frequency = fields.Selection(
        [
            ("immediate", "Immediate"),
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        string="Notification Frequency",
        default="weekly",
    )

    # Record Management
    record_type = fields.Selection(
        [
            ("physical", "Physical Records"),
            ("digital", "Digital Records"),
            ("hybrid", "Hybrid Records"),
        ],
        string="Record Type",
        default="physical",
    )

    retention_schedule = fields.Char(string="Retention Schedule")

    # Review and Approval
    review_cycle = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annually", "Semi-Annually"),
            ("annually", "Annually"),
        ],
        string="Review Cycle",
        default="quarterly",
    )

    reviewer_id = fields.Many2one("hr.employee", string="Reviewer")

    # Security and Access
    security_clearance_required = fields.Boolean(
        string="Security Clearance Required", default=False
    )

    # Service and Support
    service_level_agreement = fields.Text(string="Service Level Agreement")
    support_contact = fields.Many2one("res.partner", string="Support Contact")

    # Validation and Quality
    validation_notes = fields.Text(string="Validation Notes")

    # Computed Analytics Fields
    compliance_percentage = fields.Float(
        string="Compliance Percentage (%)",
        digits=(5, 2),
        compute="_compute_compliance_percentage",
    )

    @api.depends("last_audit_date")
    def _compute_days_since_audit(self):
        """Compute days since last audit"""
        for record in self:
            if record.last_audit_date:
                today = fields.Date.today()
                delta = today - record.last_audit_date
                record.days_since_last_audit = delta.days
            else:
                record.days_since_last_audit = 0

    @api.depends("certificate_valid_until", "expiry_date")
    def _compute_days_until_expiry(self):
        """Compute days until certificate expiry"""
        for record in self:
            expiry_date = record.certificate_valid_until or record.expiry_date
            if expiry_date:
                today = fields.Date.today()
                delta = expiry_date - today
                record.days_until_expiry = delta.days
            else:
                record.days_until_expiry = 0

    @api.depends(
        "compliance_score", "audit_score", "security_score", "operational_score"
    )
    def _compute_compliance_trend(self):
        """Compute compliance trend based on historical scores"""
        for record in self:
            # Simple trend analysis - could be enhanced with historical data
            current_score = record.compliance_score or 0

            if current_score >= 90:
                record.compliance_trend = "improving"
            elif current_score >= 75:
                record.compliance_trend = "stable"
            elif current_score >= 50:
                record.compliance_trend = "declining"
            else:
                record.compliance_trend = "critical"

    @api.depends("compliance_score", "checklist_completion_rate", "audit_score")
    def _compute_compliance_percentage(self):
        """Compute overall compliance percentage"""
        for record in self:
            scores = []

            if record.compliance_score:
                scores.append(record.compliance_score)
            if record.checklist_completion_rate:
                scores.append(record.checklist_completion_rate)
            if record.audit_score:
                scores.append(record.audit_score)

            if scores:
                record.compliance_percentage = sum(scores) / len(scores)
            else:
                record.compliance_percentage = 0.0

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
    workflow_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Workflow State",
        default="draft",
    )
    next_action_date = fields.Date(string="Next Action Date")
    deadline_date = fields.Date(string="Deadline")
    completion_date = fields.Datetime(string="Completion Date")
    responsible_user_id = fields.Many2one("res.users", string="Responsible User")
    assigned_team_id = fields.Many2one("hr.department", string="Assigned Team")
    supervisor_id = fields.Many2one("res.users", string="Supervisor")
    quality_checked = fields.Boolean(string="Quality Checked")
    quality_score = fields.Float(string="Quality Score", digits=(3, 2))
    validation_required = fields.Boolean(string="Validation Required")
    validated_by_id = fields.Many2one("res.users", string="Validated By")
    validation_date = fields.Datetime(string="Validation Date")
    reference_number = fields.Char(string="Reference Number")
    external_reference = fields.Char(string="External Reference")
    documentation_complete = fields.Boolean(string="Documentation Complete")
    attachment_ids = fields.One2many("ir.attachment", "res_id", string="Attachments")
    performance_score = fields.Float(string="Performance Score", digits=(5, 2))
    efficiency_rating = fields.Selection(
        [
            ("poor", "Poor"),
            ("fair", "Fair"),
            ("good", "Good"),
            ("excellent", "Excellent"),
        ],
        string="Efficiency Rating",
    )
    # NAID Compliance Management Fields
    audit_result = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail"), ("conditional", "Conditional")],
        "Audit Result",
    )
    audit_scope = fields.Selection(
        [("full", "Full Audit"), ("partial", "Partial"), ("focused", "Focused")],
        default="full",
    )
    audit_type = fields.Selection(
        [
            ("initial", "Initial"),
            ("surveillance", "Surveillance"),
            ("recertification", "Recertification"),
        ],
        default="surveillance",
    )
    auditor_name = fields.Char("Auditor Name")
    benchmark = fields.Selection(
        [("aaa", "NAID AAA"), ("aa", "NAID AA"), ("a", "NAID A")], default="aaa"
    )
    certificate_expiration_date = fields.Date("Certificate Expiration Date")
    certificate_issue_date = fields.Date("Certificate Issue Date")
    certificate_status = fields.Selection(
        [
            ("active", "Active"),
            ("expired", "Expired"),
            ("suspended", "Suspended"),
            ("revoked", "Revoked"),
        ],
        default="active",
    )
    compliance_documentation_complete = fields.Boolean(
        "Compliance Documentation Complete", default=False
    )
    compliance_manager_id = fields.Many2one("hr.employee", "Compliance Manager")
    compliance_officer_id = fields.Many2one("hr.employee", "Compliance Officer")
    compliance_review_date = fields.Date("Compliance Review Date")
    compliance_training_completed = fields.Boolean(
        "Compliance Training Completed", default=False
    )
    corrective_action_plan = fields.Text("Corrective Action Plan")
    corrective_actions_required = fields.Boolean(
        "Corrective Actions Required", default=False
    )
    destruction_method_approved = fields.Boolean(
        "Destruction Method Approved", default=False
    )
    documentation_retention_period = fields.Integer(
        "Documentation Retention Period (Years)", default=7
    )
    employee_training_records = fields.Text("Employee Training Records")
    equipment_certification_current = fields.Boolean(
        "Equipment Certification Current", default=False
    )
    facility_security_assessment = fields.Text("Facility Security Assessment")
    internal_audit_frequency = fields.Selection(
        [("monthly", "Monthly"), ("quarterly", "Quarterly"), ("annual", "Annual")],
        default="quarterly",
    )
    next_audit_due_date = fields.Date("Next Audit Due Date")
    non_conformance_count = fields.Integer("Non-conformance Count", default=0)
    operational_procedures_current = fields.Boolean(
        "Operational Procedures Current", default=False
    )
    regulatory_compliance_verified = fields.Boolean(
        "Regulatory Compliance Verified", default=False
    )
    risk_assessment_completed = fields.Boolean(
        "Risk Assessment Completed", default=False
    )
    security_clearance_level = fields.Selection(
        [("public", "Public"), ("secret", "Secret"), ("top_secret", "Top Secret")],
        default="public",
    )
    staff_background_checks_current = fields.Boolean(
        "Staff Background Checks Current", default=False
    )
    surveillance_audit_frequency = fields.Selection(
        [
            ("quarterly", "Quarterly"),
            ("semi_annual", "Semi-annual"),
            ("annual", "Annual"),
        ],
        default="annual",
    )

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

    def action_schedule_audit(self):
        """Schedule next NAID compliance audit"""
        self.ensure_one()
        wizard = self.env["naid.audit.scheduler.wizard"].create(
            {
                "compliance_id": self.id,
                "audit_type": "surveillance",
                "proposed_date": self.next_audit_date or fields.Date.today(),
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Schedule NAID Audit",
            "res_model": "naid.audit.scheduler.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_create_corrective_action(self):
        """Create corrective action plan"""
        self.ensure_one()
        action_plan = self.env["naid.compliance.action.plan"].create(
            {
                "compliance_id": self.id,
                "name": "Corrective Action Required",
                "action_type": "corrective",
                "priority": "high",
                "assigned_to": self.compliance_officer.user_id.id or self.env.user.id,
                "due_date": fields.Date.today() + relativedelta(days=30),
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Corrective Action Plan",
            "res_model": "naid.compliance.action.plan",
            "res_id": action_plan.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_generate_compliance_report(self):
        """Generate comprehensive compliance status report"""
        self.ensure_one()
        return self.env.ref(
            "records_management.action_report_naid_compliance_status"
        ).report_action(self)

    def action_renew_certificate(self):
        """Initiate certificate renewal process"""
        self.ensure_one()
        if not self.certificate_issued:
            raise UserError(_("No certificate issued to renew."))

        # Create renewal request
        renewal_request = self.env["naid.certificate.renewal"].create(
            {
                "compliance_id": self.id,
                "current_certificate_number": self.certificate_number,
                "current_expiry_date": self.certificate_valid_until,
                "renewal_type": "standard",
                "requested_by": self.env.user.id,
                "request_date": fields.Date.today(),
            }
        )

        return {
            "type": "ir.actions.act_window",
            "name": "Certificate Renewal",
            "res_model": "naid.certificate.renewal",
            "res_id": renewal_request.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_submit_compliance_evidence(self):
        """Submit compliance evidence and documentation"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Submit Compliance Evidence",
            "res_model": "naid.compliance.evidence.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_compliance_id": self.id,
                "default_evidence_type": "documentation",
            },
        }

    def action_escalate_non_compliance(self):
        """Escalate non-compliance issues to management"""
        self.ensure_one()
        escalation = self.env["naid.compliance.escalation"].create(
            {
                "compliance_id": self.id,
                "escalation_level": "management",
                "escalation_reason": "Non-compliance identified requiring immediate attention",
                "escalated_by": self.env.user.id,
                "escalation_date": fields.Datetime.now(),
                "status": "open",
            }
        )

        # Send notification email
        self.message_post(
            body=_("Non-compliance issue escalated to management. Escalation ID: %s")
            % escalation.name,
            subject=_("NAID Compliance Escalation - %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": "Compliance Escalation",
            "res_model": "naid.compliance.escalation",
            "res_id": escalation.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_update_risk_assessment(self):
        """Update compliance risk assessment"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Update Risk Assessment",
            "res_model": "naid.risk.assessment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_compliance_id": self.id,
                "default_assessment_type": "periodic_review",
            },
        }

    def action_archive_compliance_record(self):
        """Archive compliance record with proper documentation"""
        self.ensure_one()
        if self.state != "expired":
            raise UserError(_("Only expired compliance records can be archived."))

        # Create archive record
        archive_record = self.env["naid.compliance.archive"].create(
            {
                "original_compliance_id": self.id,
                "archive_date": fields.Date.today(),
                "archived_by": self.env.user.id,
                "archive_reason": "Certificate expired - routine archival",
                "retention_period_years": 7,  # NAID requirement
            }
        )

        self.write({"active": False})
        self.message_post(
            body=_("Compliance record archived. Archive ID: %s") % archive_record.name,
            subject=_("NAID Compliance Record Archived"),
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": _("Compliance record successfully archived."),
                "type": "success",
            },
        }
