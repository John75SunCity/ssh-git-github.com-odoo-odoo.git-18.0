# -*- coding: utf-8 -*-
"""
Portal Feedback Analytics Model
"""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PortalFeedbackAnalytic(models.Model):
    _name = "portal.feedback.analytic"
    _description = "Portal Feedback Analytics"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "period_start desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Analytics Period", required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # PERIOD DEFINITION
    # ============================================================================
    period_start = fields.Date(string="Period Start", required=True)
    period_end = fields.Date(string="Period End", required=True)

    # ============================================================================
    # COMPUTED ANALYTICS FIELDS
    # ============================================================================
    total_feedback_count = fields.Integer(
        string="Total Feedback", compute="_compute_analytics", store=True
    )
    positive_feedback_count = fields.Integer(
        string="Positive Feedback", compute="_compute_analytics", store=True
    )
    negative_feedback_count = fields.Integer(
        string="Negative Feedback", compute="_compute_analytics", store=True
    )
    average_rating = fields.Float(
        string="Average Rating", digits=(3, 2), compute="_compute_analytics", store=True
    )
    average_response_time = fields.Float(
        string="Avg Response Time (Hours)",
        digits=(8, 2),
        compute="_compute_analytics",
        store=True,
    )
    average_resolution_time = fields.Float(
        string="Avg Resolution Time (Hours)",
        digits=(8, 2),
        compute="_compute_analytics",
        store=True,
    )
    sla_compliance_rate = fields.Float(
        string="SLA Compliance Rate (%)",
        digits=(5, 2),
        compute="_compute_analytics",
        store=True,
    )
    nps_score = fields.Float(
        string="Net Promoter Score",
        digits=(5, 2),
        compute="_compute_analytics",
        store=True,
    )
    customer_satisfaction_index = fields.Float(
        string="Customer Satisfaction Index",
        digits=(5, 2),
        compute="_compute_analytics",
        store=True,
    )
    escalation_rate = fields.Float(
        string="Escalation Rate (%)",
        digits=(5, 2),
        compute="_compute_analytics",
        store=True,
    )
    repeat_feedback_rate = fields.Float(
        string="Repeat Feedback Rate (%)",
        digits=(5, 2),
        compute="_compute_analytics",
        store=True,
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("period_start", "period_end")
    def _compute_analytics(self):
        """Compute analytics for the specified period"""
        for record in self:
            if not record.period_start or not record.period_end:
                record._reset_analytics()
                continue

            domain = [
                ("create_date", ">=", record.period_start),
                ("create_date", "<=", record.period_end),
                ("company_id", "=", record.company_id.id),
            ]
            feedback_records = self.env["portal.feedback"].search(domain)

            if not feedback_records:
                record._reset_analytics()
                continue

            record.total_feedback_count = len(feedback_records)
            record.positive_feedback_count = len(
                feedback_records.filtered(lambda f: f.sentiment_category == "positive")
            )
            record.negative_feedback_count = len(
                feedback_records.filtered(lambda f: f.sentiment_category == "negative")
            )

            # This is a simplified placeholder for the rest of the logic
            rated_feedback = feedback_records.filtered(lambda f: f.rating and f.rating != '0')
            if rated_feedback:
                ratings = [int(f.rating) for f in rated_feedback]
                record.average_rating = sum(ratings) / len(ratings) if ratings else 0.0
            else:
                record.average_rating = 0.0

            record.average_response_time = 0.0
            record.average_resolution_time = 0.0
            record.sla_compliance_rate = 0.0
            record.nps_score = 0.0
            record.customer_satisfaction_index = 0.0
            record.escalation_rate = 0.0
            record.repeat_feedback_rate = 0.0


    def _reset_analytics(self):
        """Reset all analytics metrics to zero"""
        self.write({
            "total_feedback_count": 0,
            "positive_feedback_count": 0,
            "negative_feedback_count": 0,
            "average_rating": 0.0,
            "average_response_time": 0.0,
            "average_resolution_time": 0.0,
            "sla_compliance_rate": 0.0,
            "nps_score": 0.0,
            "customer_satisfaction_index": 0.0,
            "escalation_rate": 0.0,
            "repeat_feedback_rate": 0.0,
        })

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_refresh_analytics(self):
        """Manually refresh analytics data"""
        self.ensure_one()
        self._compute_analytics()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": _("Analytics refreshed successfully"),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_period_feedback(self):
        """View feedback records for this analytics period"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Period Feedback"),
            "res_model": "portal.feedback",
            "view_mode": "tree,form",
            "domain": [
                ("create_date", ">=", self.period_start),
                ("create_date", "<=", self.period_end),
                ("company_id", "=", self.company_id.id),
            ],
            "target": "current",
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("period_start", "period_end")
    def _check_period_dates(self):
        """Validate period dates"""
        for record in self:
            if record.period_start and record.period_end:
                if record.period_start >= record.period_end:
                    raise ValidationError(
                        _("Period start date must be before end date.")
                    )
