# -*- coding: utf-8 -*-
"""
NAID Compliance Support Models

Supporting models for the NAID Compliance Management System including alerts,
checklists, audit history, risk assessment, and action plans.

This file is deprecated and its models have been moved to their respective files.
It can be safely removed.
"""
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class NaidComplianceAlert(models.Model):
    """Compliance alerts for NAID compliance management"""

    _name = "naid.compliance.alert"
    _description = "NAID Compliance Alert"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "alert_date desc, severity desc"
    _rec_name = "title"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(
        string="Alert Reference",
        required=True,
        tracking=True,
        index=True,
        default=lambda self: _("New Alert"),
    )

    title = fields.Char(string="Alert Title", required=True, tracking=True)

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # ALERT RELATIONSHIPS
    # ============================================================================

    compliance_id = fields.Many2one(
        "naid.compliance",
        string="Compliance Record",
        required=True,
        ondelete="cascade",
        tracking=True,
    )

    # ============================================================================
    # ALERT DETAILS
    # ============================================================================

    alert_date = fields.Datetime(
        string="Alert Date", required=True, default=fields.Datetime.now, tracking=True
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
        tracking=True,
    )

    severity = fields.Selection(
        [("info", "Information"), ("warning", "Warning"), ("critical", "Critical")],
        string="Severity",
        required=True,
        default="warning",
        tracking=True,
    )

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
        tracking=True,
    )

    resolved_date = fields.Datetime(string="Resolved Date")

    resolved_by = fields.Many2one("res.users", string="Resolved By")

    resolution_notes = fields.Text(string="Resolution Notes")

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================

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
    # ACTION METHODS
    # ============================================================================

    def action_acknowledge(self):
        """Acknowledge alert"""
        self.ensure_one()
        self.write({"status": "acknowledged"})
        self.message_post(body=_("Alert acknowledged by %s", self.env.user.name))

    def action_resolve(self):
        """Resolve alert"""
        self.ensure_one()
        self.write(
            {
                "status": "resolved",
                "resolved_date": fields.Datetime.now(),
                "resolved_by": self.env.user.id,
            }
        )
        self.message_post(body=_("Alert resolved by %s", self.env.user.name))

    def action_dismiss(self):
        """Dismiss alert"""
        self.ensure_one()
        self.write({"status": "dismissed"})
        self.message_post(body=_("Alert dismissed by %s", self.env.user.name))


class NaidComplianceChecklistItem(models.Model):
    """Individual checklist items for NAID compliance"""

    _name = "naid.compliance.checklist.item"
    _description = "NAID Compliance Checklist Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Item Name", required=True, tracking=True)

    sequence = fields.Integer(string="Sequence", default=10)

    description = fields.Text(string="Item Description")

    active = fields.Boolean(string="Active", default=True)

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

    is_compliant = fields.Boolean(string="Compliant", default=False, tracking=True)

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

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================

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


class NaidRiskAssessment(models.Model):
    """Risk assessment for NAID compliance"""

    _name = "naid.risk.assessment"
    _description = "NAID Risk Assessment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "assessment_date desc"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(
        string="Risk Assessment Reference", required=True, tracking=True, index=True
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # ASSESSMENT RELATIONSHIPS
    # ============================================================================

    compliance_id = fields.Many2one(
        "naid.compliance", string="Compliance Record", required=True, ondelete="cascade"
    )

    # ============================================================================
    # ASSESSMENT DETAILS
    # ============================================================================

    assessment_date = fields.Date(
        string="Assessment Date",
        required=True,
        default=fields.Date.today,
        tracking=True,
    )

    assessor_id = fields.Many2one(
        "res.users",
        string="Assessor",
        required=True,
        default=lambda self: self.env.user,
    )

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
    # COMPUTED RISK FIELDS
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
    # MITIGATION FIELDS
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
        tracking=True,
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================

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

    @api.depends("impact_level", "probability")
    def _compute_risk_score(self):
        """Compute risk score based on impact and probability"""
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
        """Compute risk level based on risk score"""
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
    """Action plans for NAID compliance improvements"""

    _name = "naid.compliance.action.plan"
    _description = "NAID Compliance Action Plan"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, due_date"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Action Title", required=True, tracking=True)

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # ACTION RELATIONSHIPS
    # ============================================================================

    compliance_id = fields.Many2one(
        "naid.compliance", string="Compliance Record", required=True, ondelete="cascade"
    )

    # ============================================================================
    # ACTION DETAILS
    # ============================================================================

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
        tracking=True,
    )

    due_date = fields.Date(string="Due Date", required=True, tracking=True)

    start_date = fields.Date(string="Start Date")

    completion_date = fields.Date(string="Completion Date")

    # ============================================================================
    # RESPONSIBILITY
    # ============================================================================

    responsible_user_id = fields.Many2one(
        "res.users", string="Responsible Person", required=True, tracking=True
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
        tracking=True,
    )

    progress_percentage = fields.Float(string="Progress %", default=0.0)

    completion_notes = fields.Text(string="Completion Notes")

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================

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
    # ACTION METHODS
    # ============================================================================

    def action_approve(self):
        """Approve action plan"""
        self.ensure_one()
        self.write(
            {
                "status": "approved",
                "approved_by": self.env.user.id,
                "approval_date": fields.Date.today(),
            }
        )
        self.message_post(body=_("Action plan approved by %s", self.env.user.name))

    def action_start(self):
        """Start action plan execution"""
        self.ensure_one()
        self.write(
            {
                "status": "in_progress",
                "start_date": fields.Date.today(),
            }
        )
        self.message_post(body=_("Action plan started by %s", self.env.user.name))

    def action_complete(self):
        """Mark action plan as completed"""
        self.ensure_one()
        self.write(
            {
                "status": "completed",
                "completion_date": fields.Date.today(),
                "progress_percentage": 100.0,
            }
        )
        self.message_post(body=_("Action plan completed by %s", self.env.user.name))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("progress_percentage")
    def _check_progress_percentage(self):
        """Validate progress percentage is between 0 and 100"""
        for record in self:
            if record.progress_percentage < 0 or record.progress_percentage > 100:
                raise ValidationError(
                    _("Progress percentage must be between 0 and 100.")
                )

    @api.constrains("due_date", "start_date")
    def _check_dates(self):
        """Validate date logic"""
        for record in self:
            if record.start_date and record.due_date:
                if record.start_date > record.due_date:
                    raise ValidationError(_("Start date cannot be after due date."))
                if record.start_date > record.due_date:
                    raise ValidationError(_("Start date cannot be after due date."))
