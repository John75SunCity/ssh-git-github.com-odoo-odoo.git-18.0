# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class NaidComplianceAlert(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    """Compliance alerts for NAID compliance management"""

    _name = "naid.compliance.alert"
    _description = "NAID Compliance Alert"
    _order = "compliance_id, severity desc, alert_date desc"

    # ============================================================================
    # CORE RELATIONSHIPS
    # ============================================================================
    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    active = fields.Boolean(string="Active", default=True)

    compliance_id = fields.Many2one(
        "naid.compliance", string="Compliance Record", required=True, ondelete="cascade"
    )

    # ============================================================================
    # ALERT DETAILS
    # ============================================================================

    alert_date = fields.Datetime(
        string="Alert Date", required=True, default=fields.Datetime.now
    )
    alert_type = fields.Selection(
        [
            ("certificate_expiry", "Certificate Expiry"),
            ("audit_due", "Audit Due"),
            ("non_compliance", "Non-Compliance Issue"),
            ("security_breach", "Security Breach"),
            ("equipment_failure", "Equipment Failure"),
            ("documentation_missing", "Documentation Missing"),
            ("training_overdue", "Training Overdue"),
            ("risk_escalation", "Risk Escalation"),
        ],
        string="Alert Type",
        required=True,
    )
    severity = fields.Selection(
        [("info", "Information"), ("warning", "Warning"), ("critical", "Critical")],
        string="Severity",
        required=True,
        default="warning",
    )
    title = fields.Char(string="Alert Title", required=True)
    description = fields.Text(string="Alert Description")

    # ============================================================================
    # STATUS MANAGEMENT
    # ============================================================================

    status = fields.Selection(
        [
            ("active", "Active"),
            ("acknowledged", "Acknowledged"),
            ("resolved", "Resolved"),
            ("dismissed", "Dismissed"),
        ],
        string="Status",
        required=True,
        default="active",
    )
    resolved_date = fields.Datetime(string="Resolved Date")
    resolved_by = fields.Many2one("res.users", string="Resolved By")
    resolution_notes = fields.Text(string="Resolution Notes")

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================

    def action_acknowledge(self):
        self.status = "acknowledged"

    def action_resolve(self):
        self.write(
            {
                "status": "resolved",
                "resolved_date": fields.Datetime.now(),
                "resolved_by": self.env.user.id,
            }
        )

class NaidComplianceChecklistItem(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    """Individual checklist items for NAID compliance"""

    _name = "naid.compliance.checklist.item"
    _description = "NAID Compliance Checklist Item"
    _order = "sequence, name"

    # ============================================================================
    # CORE IDENTIFICATION
    # ============================================================================

    name = fields.Char(string="Item Name", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    description = fields.Text(string="Item Description")

    # ============================================================================
    # CHECKLIST RELATIONSHIPS
    # ============================================================================

    checklist_id = fields.Many2one(
        "naid.compliance.checklist",
        string="Checklist",
        required=True,
        ondelete="cascade",
    )
    category = fields.Selection(
        [
            ("security", "Security"),
            ("operations", "Operations"),
            ("training", "Training"),
            ("documentation", "Documentation"),
            ("equipment", "Equipment"),
        ],
        string="Category",
        required=True,
    )

    # ============================================================================
    # COMPLIANCE TRACKING
    # ============================================================================

    is_compliant = fields.Boolean(string="Compliant", default=False)
    compliance_date = fields.Date(string="Compliance Date")
    verified_by = fields.Many2one("res.users", string="Verified By")
    evidence_attachment = fields.Binary(string="Evidence")
    notes = fields.Text(string="Notes")

    # ============================================================================
    # REQUIREMENTS
    # ============================================================================

    is_mandatory = fields.Boolean(string="Mandatory", default=True)
    risk_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Risk Level",
        default="medium",
    )
    deadline = fields.Date(string="Deadline")

class NaidComplianceAuditHistory(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    """Historical audit records for NAID compliance"""

    _name = "naid.compliance.audit.history"
    _description = "NAID Compliance Audit History"
    _order = "audit_date desc, compliance_id"

    # ============================================================================
    # CORE RELATIONSHIPS
    # ============================================================================

    compliance_id = fields.Many2one(
        "naid.compliance", string="Compliance Record", required=True, ondelete="cascade"
    )

    # ============================================================================
    # AUDIT DETAILS
    # ============================================================================

    audit_date = fields.Date(string="Audit Date", required=True)
    audit_type = fields.Selection(
        [
            ("internal", "Internal Audit"),
            ("external", "External Audit"),
            ("naid_official", "NAID Official Audit"),
            ("customer", "Customer Audit"),
        ],
        string="Audit Type",
        required=True,
    )
    auditor_name = fields.Char(string="Auditor Name", required=True)
    audit_scope = fields.Text(string="Audit Scope")

    # ============================================================================
    # RESULTS
    # ============================================================================

    overall_rating = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("satisfactory", "Satisfactory"),
            ("needs_improvement", "Needs Improvement"),
            ("unsatisfactory", "Unsatisfactory"),
        ],
        string="Overall Rating",
        required=True,
    )
    findings = fields.Text(string="Audit Findings")
    recommendations = fields.Text(string="Recommendations")
    corrective_actions = fields.Text(string="Corrective Actions Required")

    # ============================================================================
    # FOLLOW-UP
    # ============================================================================

    follow_up_required = fields.Boolean(string="Follow-up Required", default=False)
    follow_up_date = fields.Date(string="Follow-up Date")
    follow_up_completed = fields.Boolean(string="Follow-up Completed", default=False)

class NaidRiskAssessment(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    """Risk assessment for NAID compliance"""

    _name = "naid.risk.assessment"
    _description = "NAID Risk Assessment"
    _order = "assessment_date desc, compliance_id"

    # ============================================================================
    # CORE RELATIONSHIPS
    # ============================================================================

    compliance_id = fields.Many2one(
        "naid.compliance", string="Compliance Record", required=True, ondelete="cascade"
    )

    # ============================================================================
    # ASSESSMENT DETAILS
    # ============================================================================

    assessment_date = fields.Date(
        string="Assessment Date", required=True, default=fields.Date.today
    )
    assessor_id = fields.Many2one("res.users", string="Assessor", required=True)
    risk_category = fields.Selection(
        [
            ("operational", "Operational Risk"),
            ("security", "Security Risk"),
            ("compliance", "Compliance Risk"),
            ("financial", "Financial Risk"),
            ("reputational", "Reputational Risk"),
        ],
        string="Risk Category",
        required=True,
    )

    # ============================================================================
    # RISK EVALUATION
    # ============================================================================

    risk_description = fields.Text(string="Risk Description", required=True)
    impact_level = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Impact Level",
        required=True,
    )
    probability = fields.Selection(
        [
            ("rare", "Rare"),
            ("unlikely", "Unlikely"),
            ("possible", "Possible"),
            ("likely", "Likely"),
            ("certain", "Certain"),
        ],
        string="Probability",
        required=True,
    )

    # ============================================================================
    # COMPUTED RISK
    # ============================================================================

    risk_score = fields.Integer(
        string="Risk Score", compute="_compute_risk_score", store=True
    )
    risk_level = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Risk Level",
        compute="_compute_risk_level",
        store=True,
    )

    # ============================================================================
    # MITIGATION
    # ============================================================================

    mitigation_measures = fields.Text(string="Mitigation Measures")
    responsible_person = fields.Many2one("res.users", string="Responsible Person")
    target_completion_date = fields.Date(string="Target Completion Date")
    status = fields.Selection(
        [
            ("identified", "Identified"),
            ("in_progress", "In Progress"),
            ("mitigated", "Mitigated"),
            ("accepted", "Accepted"),
        ],
        string="Status",
        default="identified",
    )

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================

    @api.depends("impact_level", "probability")
    def _compute_risk_score(self):
        impact_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        probability_scores = {
            "rare": 1,
            "unlikely": 2,
            "possible": 3,
            "likely": 4,
            "certain": 5,
        }

        for record in self:
            impact = impact_scores.get(record.impact_level, 0)
            prob = probability_scores.get(record.probability, 0)
            record.risk_score = impact * prob

    @api.depends("risk_score")
    def _compute_risk_level(self):
        for record in self:
            if record.risk_score >= 15:
                record.risk_level = "critical"
            elif record.risk_score >= 9:
                record.risk_level = "high"
            elif record.risk_score >= 4:
                record.risk_level = "medium"
            else:
                record.risk_level = "low"

class NaidComplianceActionPlan(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    """Action plans for NAID compliance improvements"""

    _name = "naid.compliance.action.plan"
    _description = "NAID Compliance Action Plan"
    _order = "priority desc, due_date, compliance_id"

    # ============================================================================
    # CORE RELATIONSHIPS
    # ============================================================================

    compliance_id = fields.Many2one(
        "naid.compliance", string="Compliance Record", required=True, ondelete="cascade"
    )

    # ============================================================================
    # ACTION DETAILS
    # ============================================================================

    name = fields.Char(string="Action Title", required=True)
    description = fields.Text(string="Action Description", required=True)
    action_type = fields.Selection(
        [
            ("corrective", "Corrective Action"),
            ("preventive", "Preventive Action"),
            ("improvement", "Improvement Action"),
        ],
        string="Action Type",
        required=True,
    )

    # ============================================================================
    # PRIORITY & SCHEDULING
    # ============================================================================

    priority = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority",
        required=True,
        default="medium",
    )
    due_date = fields.Date(string="Due Date", required=True)
    start_date = fields.Date(string="Start Date")
    completion_date = fields.Date(string="Completion Date")

    # ============================================================================
    # RESPONSIBILITY
    # ============================================================================

    responsible_user_id = fields.Many2one(
        "res.users", string="Responsible Person", required=True
    )
    approval_required = fields.Boolean(string="Approval Required", default=False)
    approved_by = fields.Many2one("res.users", string="Approved By")
    approval_date = fields.Date(string="Approval Date")

    # ============================================================================
    # STATUS TRACKING
    # ============================================================================

    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
    )
    progress_percentage = fields.Float(string="Progress %", default=0.0)
    completion_notes = fields.Text(string="Completion Notes")

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================

    def action_approve(self):
        """Approve action plan"""
        self.write(
            {
                "status": "approved",
                "approved_by": self.env.user.id,
                "approval_date": fields.Date.today(),
            }
        )

    def action_start(self):
        """Start action plan execution"""
        self.write(
            {
                "status": "in_progress",
                "start_date": fields.Date.today(),
            }
        )

    def action_complete(self):
        """Mark action plan as completed"""
        self.write(
            {
                "status": "completed",
                "completion_date": fields.Date.today(),
                "progress_percentage": 100.0,
            }
        )

class NaidComplianceEnhanced(models.Model):
    """Enhanced NAID Compliance Policy Management"""

    _name = "naid.compliance.enhanced"
    _description = "NAID Compliance Enhanced Policies"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Policy Name", required=True, tracking=True, index=True)
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    # ============================================================================
    # POLICY DETAILS
    # ============================================================================
    policy_type = fields.Selection(
        [
            ("access_control", "Access Control"),
            ("document_handling", "Document Handling"),
            ("destruction_process", "Destruction Process"),
            ("employee_screening", "Employee Screening"),
            ("facility_security", "Facility Security"),
            ("equipment_maintenance", "Equipment Maintenance"),
            ("audit_requirements", "Audit Requirements"),
        ],
        string="Policy Type",
        required=True,
        tracking=True,
    )

    description = fields.Text(string="Policy Description")
    mandatory = fields.Boolean(string="Mandatory", default=True, tracking=True)
    automated_check = fields.Boolean(string="Automated Check", default=False)

    check_frequency = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("yearly", "Yearly"),
        ],
        string="Check Frequency",
        default="monthly",
    )

    implementation_notes = fields.Text(string="Implementation Notes")
    violation_consequences = fields.Text(string="Violation Consequences")
    review_frequency_months = fields.Integer(
        string="Review Frequency (Months)", default=12
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================        "mail.followers", "res_id", string="Followers"
    )