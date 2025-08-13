# -*- coding: utf-8 -*-
"""
Document Retrieval Metric Model

Performance metrics for document retrieval operations including efficiency
tracking, cost analysis, and quality metrics.
"""

from odoo import models, fields, api


class DocumentRetrievalMetric(models.Model):
    """Performance metrics for document retrieval operations"""

    _name = "document.retrieval.metric"
    _description = "Document Retrieval Metric"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Metric Name", required=True, tracking=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # METRIC DATE AND REFERENCE FIELDS
    # ============================================================================
    date = fields.Date(
        string="Retrieval Date", required=True, default=fields.Date.today, tracking=True
    )
    work_order_id = fields.Many2one(
        "file.retrieval.work.order", string="Work Order"
    )
    team_id = fields.Many2one("document.retrieval.team", string="Team")
    employee_id = fields.Many2one("hr.employee", string="Employee")

    # ============================================================================
    # PERFORMANCE METRICS FIELDS
    # ============================================================================
    documents_retrieved = fields.Integer(string="Documents Retrieved")
    hours_worked = fields.Float(string="Hours Worked", digits=(5, 2))
    accuracy_rate = fields.Float(string="Accuracy Rate (%)", digits=(5, 2))
    customer_satisfaction = fields.Float(
        string="Customer Satisfaction (%)", digits=(5, 2)
    )

    # ============================================================================
    # EFFICIENCY METRICS FIELDS
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    documents_per_hour = fields.Float(
        string="Documents per Hour",
        digits=(5, 2),
        compute="_compute_efficiency",
        store=True,
    )
    cost_per_document = fields.Monetary(
        string="Cost per Document", currency_field="currency_id"
    )
    revenue_generated = fields.Monetary(
        string="Revenue Generated", currency_field="currency_id"
    )
    profit_margin = fields.Float(string="Profit Margin (%)", digits=(5, 2))

    # ============================================================================
    # QUALITY METRICS FIELDS
    # ============================================================================
    errors_count = fields.Integer(string="Errors Count")
    rework_required = fields.Integer(string="Rework Required")
    on_time_delivery = fields.Boolean(string="On Time Delivery", default=True)

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("documents_retrieved", "hours_worked")
    def _compute_efficiency(self):
        """Compute documents per hour efficiency"""
        for metric in self:
            if metric.hours_worked > 0:
                metric.documents_per_hour = (
                    metric.documents_retrieved / metric.hours_worked
                )
            else:
                metric.documents_per_hour = 0
