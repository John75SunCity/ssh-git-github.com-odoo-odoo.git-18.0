# -*- coding: utf-8 -*-
"""
Document Retrieval Team Model

Teams responsible for document retrieval operations with performance tracking
and workload management capabilities.
"""

from odoo import models, fields, api


class DocumentRetrievalTeam(models.Model):
    """Teams responsible for document retrieval operations"""

    _name = "document.retrieval.team"
    _description = "Document Retrieval Team"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Team Name", required=True, tracking=True, index=True)
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
    # TEAM STRUCTURE FIELDS
    # ============================================================================
    team_lead_id = fields.Many2one("hr.employee", string="Team Lead")
    member_ids = fields.Many2many(
        "hr.employee",
        "document_retrieval_team_member_alt_rel",
        "team_id",
        "employee_id",
        string="Team Members"
    )

    # ============================================================================
    # SPECIALIZATION FIELDS
    # ============================================================================
    specialization = fields.Selection(
        [
            ("general", "General Retrieval"),
            ("legal", "Legal Documents"),
            ("medical", "Medical Records"),
            ("financial", "Financial Documents"),
            ("digital", "Digital Conversion"),
            ("urgent", "Urgent Requests"),
        ],
        string="Specialization",
        default="general",
    )

    # ============================================================================
    # PERFORMANCE METRICS FIELDS
    # ============================================================================
    active_orders_count = fields.Integer(
        string="Active Orders", compute="_compute_order_counts", store=True
    )
    completed_orders_count = fields.Integer(
        string="Completed Orders", compute="_compute_order_counts", store=True
    )
    average_completion_time = fields.Float(
        string="Avg Completion Time (days)",
        digits=(5, 2),
        compute="_compute_performance",
        store=True,
    )
    efficiency_rating = fields.Float(
        string="Efficiency Rating (%)",
        digits=(5, 2),
        compute="_compute_performance",
        store=True,
    )

    # ============================================================================
    # CAPACITY MANAGEMENT FIELDS
    # ============================================================================
    max_concurrent_orders = fields.Integer(string="Max Concurrent Orders", default=10)
    current_workload = fields.Float(
        string="Current Workload (%)", compute="_compute_workload", store=True
    )

    # ============================================================================
    # AVAILABILITY FIELDS
    # ============================================================================
    available_from = fields.Float(
        string="Available From (Hours)",
        help="Available from time in 24-hour format (e.g., 9.5 for 9:30 AM)",
    )
    available_to = fields.Float(
        string="Available To (Hours)",
        help="Available to time in 24-hour format (e.g., 17.5 for 5:30 PM)",
    )
    working_days = fields.Selection(
        [
            ("weekdays", "Monday to Friday"),
            ("all_days", "All Days"),
            ("custom", "Custom Schedule"),
        ],
        string="Working Days",
        default="weekdays",
    )

    # Document Retrieval Metrics (inverse relationship)
    retrieval_metrics_ids = fields.One2many(
        "document.retrieval.metrics", "team_id",
        string="Team Performance Metrics",
        help="Performance metrics for this retrieval team"
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("member_ids")
    def _compute_order_counts(self):
        """Compute order counts for the team"""
        for team in self:
            team_member_ids = team.member_ids.mapped("user_id.id")
            # Count active work orders
            active_count = self.env["file.retrieval.work.order"].search_count(
                [
                    ("state", "in", ["draft", "in_progress"]),
                    ("team_id", "=", team.id),
                ]
            )
            completed_count = self.env[
                "file.retrieval.work.order"
            ].search_count(
                [
                    ("user_id", "in", team_member_ids),
                    ("state", "=", "inactive"),
                ]
            )

            team.active_orders_count = active_count
            team.completed_orders_count = completed_count

    @api.depends("member_ids")
    def _compute_performance(self):
        """Compute performance metrics"""
        for team in self:
            if team.member_ids:
                team_member_ids = team.member_ids.mapped("user_id.id")
                completed_orders = self.env[
                    "file.retrieval.work.order"
                ].search(
                    [
                        ("user_id", "in", team_member_ids),
                        ("state", "=", "inactive"),
                        ("completion_date", "!=", False),
                    ]
                )

                if completed_orders:
                    total_days = 0
                    efficiency_scores = []

                    for order in completed_orders:
                        if order.requested_date and order.completion_date:
                            completion_days = (
                                order.completion_date.date() - order.requested_date
                            ).days
                            total_days += completion_days

                        if order.estimated_hours and order.actual_hours:
                            efficiency = (
                                order.estimated_hours / order.actual_hours
                            ) * 100
                            efficiency_scores.append(
                                min(efficiency, 200)
                            )  # Cap at 200%

                    team.average_completion_time = total_days / len(completed_orders)
                    team.efficiency_rating = (
                        sum(efficiency_scores) / len(efficiency_scores)
                        if efficiency_scores
                        else 0
                    )
                else:
                    team.average_completion_time = 0
                    team.efficiency_rating = 0
            else:
                team.average_completion_time = 0
                team.efficiency_rating = 0

    @api.depends("active_orders_count", "max_concurrent_orders")
    def _compute_workload(self):
        """Compute current workload percentage"""
        for team in self:
            if team.max_concurrent_orders > 0:
                team.current_workload = (
                    team.active_orders_count / team.max_concurrent_orders
                ) * 100
            else:
                team.current_workload = 0
