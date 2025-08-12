# -*- coding: utf-8 -*-
"""
NAID Risk Assessment Model

Model for risk assessment for NAID compliance.
"""

from odoo import api, fields, models


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

    responsible_person_id = fields.Many2one(
        "res.users", string="Responsible Person"
    )

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
