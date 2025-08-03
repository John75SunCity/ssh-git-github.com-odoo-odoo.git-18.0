# -*- coding: utf-8 -*-
# Supporting Models for NAID Compliance System

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class NaidComplianceAlert(models.Model):
    """Compliance alerts for NAID compliance management"""

    _name = "naid.compliance.alert"
    _description = "NAID Compliance Alert"
    _order = "compliance_id, severity desc, alert_date desc"

    compliance_id = fields.Many2one(
        "naid.compliance", string="Compliance Record", required=True, ondelete="cascade"
    )
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

    status = fields.Selection(
        [
            ("active", "Active"),
            ("acknowledged", "Acknowledged"),
            ("resolved", "Resolved"),
            ("dismissed", "Dismissed"),
        ],
        string="Status",
        default="active",
    )

    acknowledged_by = fields.Many2one("res.users", string="Acknowledged By")
    acknowledgment_date = fields.Datetime(string="Acknowledgment Date")
    resolution_date = fields.Datetime(string="Resolution Date")
    resolution_notes = fields.Text(string="Resolution Notes")

    due_date = fields.Datetime(string="Due Date")
    escalation_required = fields.Boolean(string="Escalation Required", default=False)
    notification_sent = fields.Boolean(string="Notification Sent", default=False)


class NaidComplianceChecklistItem(models.Model):
    """Compliance checklist items for NAID compliance"""

    _name = "naid.compliance.checklist.item"
    _description = "NAID Compliance Checklist Item"
    _order = "compliance_id, category, sequence"

    compliance_id = fields.Many2one(
        "naid.compliance", string="Compliance Record", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(string="Sequence", default=10)

    category = fields.Selection(
        [
            ("physical_security", "Physical Security"),
            ("personnel", "Personnel Requirements"),
            ("equipment", "Equipment Standards"),
            ("documentation", "Documentation"),
            ("processes", "Process Compliance"),
            ("environmental", "Environmental Standards"),
            ("quality", "Quality Control"),
            ("training", "Training Requirements"),
        ],
        string="Category",
        required=True,
    )

    name = fields.Char(string="Checklist Item", required=True)
    description = fields.Text(string="Description")
    requirement_level = fields.Selection(
        [
            ("mandatory", "Mandatory"),
            ("recommended", "Recommended"),
            ("optional", "Optional"),
        ],
        string="Requirement Level",
        default="mandatory",
    )

    completed = fields.Boolean(string="Completed", default=False)
    completion_date = fields.Date(string="Completion Date")
    completed_by = fields.Many2one("res.users", string="Completed By")
    verification_required = fields.Boolean(
        string="Verification Required", default=False
    )
    verified = fields.Boolean(string="Verified", default=False)
    verified_by = fields.Many2one("res.users", string="Verified By")
    verification_date = fields.Date(string="Verification Date")

    evidence_required = fields.Boolean(string="Evidence Required", default=False)
    evidence_provided = fields.Text(string="Evidence Provided")
    notes = fields.Text(string="Notes")

    non_compliance_reason = fields.Text(string="Non-Compliance Reason")
    corrective_action = fields.Text(string="Corrective Action")
    action_due_date = fields.Date(string="Action Due Date")
    action_owner = fields.Many2one("res.users", string="Action Owner")


class NaidComplianceAuditHistory(models.Model):
    """Audit history for NAID compliance"""

    _name = "naid.compliance.audit.history"
    _description = "NAID Compliance Audit History"
    _order = "compliance_id, audit_date desc"

    compliance_id = fields.Many2one(
        "naid.compliance", string="Compliance Record", required=True, ondelete="cascade"
    )
    audit_date = fields.Date(string="Audit Date", required=True)
    audit_type = fields.Selection(
        [
            ("internal", "Internal Audit"),
            ("external", "External Audit"),
            ("certification", "Certification Audit"),
            ("surveillance", "Surveillance Audit"),
            ("follow_up", "Follow-up Audit"),
        ],
        string="Audit Type",
        required=True,
    )

    auditor_name = fields.Char(string="Lead Auditor", required=True)
    audit_team = fields.Text(string="Audit Team")
    audit_scope = fields.Text(string="Audit Scope")

    audit_criteria = fields.Text(string="Audit Criteria")
    audit_methodology = fields.Text(string="Audit Methodology")

    # Audit Results
    overall_score = fields.Float(string="Overall Score (%)", digits=(5, 2))
    compliance_rating = fields.Selection(
        [
            ("excellent", "Excellent (95-100%)"),
            ("good", "Good (85-94%)"),
            ("satisfactory", "Satisfactory (75-84%)"),
            ("needs_improvement", "Needs Improvement (65-74%)"),
            ("unsatisfactory", "Unsatisfactory (<65%)"),
        ],
        string="Compliance Rating",
    )

    # Detailed Scores
    physical_security_score = fields.Float(
        string="Physical Security Score (%)", digits=(5, 2)
    )
    personnel_score = fields.Float(string="Personnel Score (%)", digits=(5, 2))
    equipment_score = fields.Float(string="Equipment Score (%)", digits=(5, 2))
    documentation_score = fields.Float(string="Documentation Score (%)", digits=(5, 2))
    process_score = fields.Float(string="Process Score (%)", digits=(5, 2))

    findings = fields.Text(string="Audit Findings")
    non_conformities = fields.Text(string="Non-Conformities")
    observations = fields.Text(string="Observations")
    recommendations = fields.Text(string="Recommendations")

    corrective_actions_required = fields.Text(string="Corrective Actions Required")
    action_plan = fields.Text(string="Action Plan")
    follow_up_required = fields.Boolean(string="Follow-up Required", default=False)
    follow_up_date = fields.Date(string="Follow-up Date")

    certificate_issued = fields.Boolean(string="Certificate Issued", default=False)
    certificate_number = fields.Char(string="Certificate Number")
    certificate_valid_until = fields.Date(string="Certificate Valid Until")

    audit_report_attachment = fields.Binary(string="Audit Report")
    audit_report_filename = fields.Char(string="Report Filename")


class NaidRiskAssessment(models.Model):
    """Risk assessment for NAID compliance"""

    _name = "naid.risk.assessment"
    _description = "NAID Risk Assessment"
    _order = "compliance_id, assessment_date desc"

    compliance_id = fields.Many2one(
        "naid.compliance", string="Compliance Record", required=True, ondelete="cascade"
    )
    assessment_date = fields.Date(
        string="Assessment Date", required=True, default=fields.Date.today
    )
    assessor = fields.Many2one(
        "res.users",
        string="Risk Assessor",
        required=True,
        default=lambda self: self.env.user,
    )

    risk_category = fields.Selection(
        [
            ("operational", "Operational Risk"),
            ("security", "Security Risk"),
            ("compliance", "Compliance Risk"),
            ("environmental", "Environmental Risk"),
            ("financial", "Financial Risk"),
            ("reputational", "Reputational Risk"),
            ("technological", "Technology Risk"),
        ],
        string="Risk Category",
        required=True,
    )

    risk_description = fields.Text(string="Risk Description", required=True)
    risk_source = fields.Text(string="Risk Source")

    probability = fields.Selection(
        [
            ("very_low", "Very Low (1-5%)"),
            ("low", "Low (6-25%)"),
            ("medium", "Medium (26-50%)"),
            ("high", "High (51-75%)"),
            ("very_high", "Very High (76-100%)"),
        ],
        string="Probability",
        required=True,
    )

    impact = fields.Selection(
        [
            ("negligible", "Negligible"),
            ("minor", "Minor"),
            ("moderate", "Moderate"),
            ("major", "Major"),
            ("catastrophic", "Catastrophic"),
        ],
        string="Impact",
        required=True,
    )

    risk_level = fields.Selection(
        [
            ("very_low", "Very Low"),
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("very_high", "Very High"),
        ],
        string="Risk Level",
        compute="_compute_risk_level",
        store=True,
    )

    current_controls = fields.Text(string="Current Controls")
    control_effectiveness = fields.Selection(
        [
            ("inadequate", "Inadequate"),
            ("partially_effective", "Partially Effective"),
            ("effective", "Effective"),
            ("very_effective", "Very Effective"),
        ],
        string="Control Effectiveness",
    )

    mitigation_strategy = fields.Text(string="Mitigation Strategy")
    mitigation_owner = fields.Many2one("res.users", string="Mitigation Owner")
    mitigation_deadline = fields.Date(string="Mitigation Deadline")

    residual_probability = fields.Selection(
        [
            ("very_low", "Very Low (1-5%)"),
            ("low", "Low (6-25%)"),
            ("medium", "Medium (26-50%)"),
            ("high", "High (51-75%)"),
            ("very_high", "Very High (76-100%)"),
        ],
        string="Residual Probability",
    )

    residual_impact = fields.Selection(
        [
            ("negligible", "Negligible"),
            ("minor", "Minor"),
            ("moderate", "Moderate"),
            ("major", "Major"),
            ("catastrophic", "Catastrophic"),
        ],
        string="Residual Impact",
    )

    residual_risk_level = fields.Selection(
        [
            ("very_low", "Very Low"),
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("very_high", "Very High"),
        ],
        string="Residual Risk Level",
        compute="_compute_residual_risk_level",
        store=True,
    )

    status = fields.Selection(
        [
            ("identified", "Identified"),
            ("assessed", "Assessed"),
            ("mitigation_planned", "Mitigation Planned"),
            ("mitigation_in_progress", "Mitigation In Progress"),
            ("mitigated", "Mitigated"),
            ("accepted", "Accepted"),
        ],
        string="Status",
        default="identified",
    )

    review_date = fields.Date(string="Review Date")
    next_review_date = fields.Date(string="Next Review Date")

    @api.depends("probability", "impact")
    def _compute_risk_level(self):
        """Compute risk level based on probability and impact matrix"""
        risk_matrix = {
            ("very_low", "negligible"): "very_low",
            ("very_low", "minor"): "very_low",
            ("very_low", "moderate"): "low",
            ("very_low", "major"): "low",
            ("very_low", "catastrophic"): "medium",
            ("low", "negligible"): "very_low",
            ("low", "minor"): "low",
            ("low", "moderate"): "low",
            ("low", "major"): "medium",
            ("low", "catastrophic"): "medium",
            ("medium", "negligible"): "low",
            ("medium", "minor"): "low",
            ("medium", "moderate"): "medium",
            ("medium", "major"): "medium",
            ("medium", "catastrophic"): "high",
            ("high", "negligible"): "low",
            ("high", "minor"): "medium",
            ("high", "moderate"): "medium",
            ("high", "major"): "high",
            ("high", "catastrophic"): "high",
            ("very_high", "negligible"): "medium",
            ("very_high", "minor"): "medium",
            ("very_high", "moderate"): "high",
            ("very_high", "major"): "high",
            ("very_high", "catastrophic"): "very_high",
        }

        for record in self:
            if record.probability and record.impact:
                record.risk_level = risk_matrix.get(
                    (record.probability, record.impact), "medium"
                )
            else:
                record.risk_level = False

    @api.depends("residual_probability", "residual_impact")
    def _compute_residual_risk_level(self):
        """Compute residual risk level based on residual probability and impact"""
        risk_matrix = {
            ("very_low", "negligible"): "very_low",
            ("very_low", "minor"): "very_low",
            ("very_low", "moderate"): "low",
            ("very_low", "major"): "low",
            ("very_low", "catastrophic"): "medium",
            ("low", "negligible"): "very_low",
            ("low", "minor"): "low",
            ("low", "moderate"): "low",
            ("low", "major"): "medium",
            ("low", "catastrophic"): "medium",
            ("medium", "negligible"): "low",
            ("medium", "minor"): "low",
            ("medium", "moderate"): "medium",
            ("medium", "major"): "medium",
            ("medium", "catastrophic"): "high",
            ("high", "negligible"): "low",
            ("high", "minor"): "medium",
            ("high", "moderate"): "medium",
            ("high", "major"): "high",
            ("high", "catastrophic"): "high",
            ("very_high", "negligible"): "medium",
            ("very_high", "minor"): "medium",
            ("very_high", "moderate"): "high",
            ("very_high", "major"): "high",
            ("very_high", "catastrophic"): "very_high",
        }

        for record in self:
            if record.residual_probability and record.residual_impact:
                record.residual_risk_level = risk_matrix.get(
                    (record.residual_probability, record.residual_impact), "medium"
                )
            else:
                record.residual_risk_level = False


class NaidComplianceActionPlan(models.Model):
    """Action plan for NAID compliance improvements"""

    _name = "naid.compliance.action.plan"
    _description = "NAID Compliance Action Plan"
    _order = "compliance_id, priority desc, due_date"

    compliance_id = fields.Many2one(
        "naid.compliance", string="Compliance Record", required=True, ondelete="cascade"
    )
    name = fields.Char(string="Action Item", required=True)
    description = fields.Text(string="Description")

    action_type = fields.Selection(
        [
            ("corrective", "Corrective Action"),
            ("preventive", "Preventive Action"),
            ("improvement", "Continuous Improvement"),
            ("maintenance", "Maintenance Action"),
        ],
        string="Action Type",
        required=True,
    )

    priority = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Priority",
        default="medium",
    )

    assigned_to = fields.Many2one("res.users", string="Assigned To", required=True)
    due_date = fields.Date(string="Due Date", required=True)

    status = fields.Selection(
        [
            ("not_started", "Not Started"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("overdue", "Overdue"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="not_started",
    )

    completion_date = fields.Date(string="Completion Date")
    completion_percentage = fields.Float(string="Completion %", digits=(5, 2))

    estimated_cost = fields.Monetary(
        string="Estimated Cost", currency_field="currency_id"
    )
    actual_cost = fields.Monetary(string="Actual Cost", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    resources_required = fields.Text(string="Resources Required")
    dependencies = fields.Text(string="Dependencies")
    success_criteria = fields.Text(string="Success Criteria")

    progress_notes = fields.Text(string="Progress Notes")
    attachments = fields.One2many(
        "ir.attachment",
        "res_id",
        string="Attachments",
        domain=[("res_model", "=", "naid.compliance.action.plan")],
    )

    effectiveness_rating = fields.Selection(
        [
            ("not_effective", "Not Effective"),
            ("partially_effective", "Partially Effective"),
            ("effective", "Effective"),
            ("very_effective", "Very Effective"),
        ],
        string="Effectiveness Rating",
    )

    follow_up_required = fields.Boolean(string="Follow-up Required", default=False)
    follow_up_date = fields.Date(string="Follow-up Date")
    lessons_learned = fields.Text(string="Lessons Learned")
