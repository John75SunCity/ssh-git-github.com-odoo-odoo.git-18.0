# -*- coding: utf-8 -*-
"""
Shredding Team Management Module

This module provides comprehensive team management for shredding operations within
the Records Management System. It handles team organization, capacity planning,
specialization tracking, and service assignment with complete workflow integration.
"""
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ShreddingTeam(models.Model):
    _name = "shredding.team"
    _description = "Shredding Team Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Team Name",
        required=True,
        tracking=True,
        index=True,
        help="Unique team identification name",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True,
        help="User who created this team",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record",
    )
    active = fields.Boolean(
        string="Active", default=True, help="Active status of the team"
    )
    sequence = fields.Integer(
        string="Sequence", default=10, help="Order sequence for sorting teams"
    )

    # ============================================================================
    # TEAM STATUS AND WORKFLOW
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("suspended", "Suspended"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current team status",
    )
    description = fields.Text(string="Description", help="Team description and notes")

    # ============================================================================
    # TEAM COMPOSITION
    # ============================================================================
    team_leader_id = fields.Many2one(
        "res.users",
        string="Team Leader",
        tracking=True,
        help="Primary team leader responsible for coordination",
    )
    supervisor_id = fields.Many2one(
        "res.users",
        string="Supervisor",
        help="Team supervisor for escalations",
    )
    member_ids = fields.Many2many(
        "res.users",
        string="Team Members",
        help="All team members including leader",
    )
    employee_ids = fields.Many2many(
        "hr.employee",
        string="Employees",
        help="HR employee records for team members",
    )
    member_count = fields.Integer(
        string="Member Count",
        compute="_compute_member_count",
        store=True,
        help="Total number of team members",
    )

    # ============================================================================
    # SPECIALIZATION AND CAPABILITIES
    # ============================================================================
    specialization = fields.Selection(
        [
            ("paper", "Paper Documents"),
            ("electronic", "Electronic Media"),
            ("hard_drives", "Hard Drives"),
            ("mixed", "Mixed Media"),
            ("confidential", "Confidential Documents"),
            ("medical", "Medical Records"),
            ("financial", "Financial Documents"),
            ("government", "Government Documents"),
        ],
        string="Primary Specialization",
        default="paper",
        required=True,
        help="Primary specialization of the team",
    )
    secondary_specialization_ids = fields.Many2many(
        "shredding.specialization",
        string="Secondary Specializations",
        help="Additional capabilities of the team",
    )
    certification_level = fields.Selection(
        [
            ("basic", "Basic"),
            ("standard", "Standard"),
            ("naid_aaa", "NAID AAA"),
            ("government", "Government Clearance"),
        ],
        string="Certification Level",
        default="standard",
        help="Team certification level",
    )
    security_clearance = fields.Boolean(
        string="Security Clearance",
        default=False,
        help="Team has security clearance for classified materials",
    )

    # ============================================================================
    # CAPACITY AND SCHEDULING
    # ============================================================================
    max_capacity_per_day = fields.Float(
        string="Max Capacity per Day (lbs)",
        digits="Stock Weight",
        default=0.0,
        help="Maximum daily processing capacity in pounds",
    )
    max_volume_per_day = fields.Float(
        string="Max Volume per Day (cubic feet)",
        digits="Stock Weight",
        default=0.0,
        help="Maximum daily processing volume",
    )
    working_hours_start = fields.Float(
        string="Working Hours Start",
        default=8.0,
        help="Daily working hours start time (24h format)",
    )
    working_hours_end = fields.Float(
        string="Working Hours End",
        default=17.0,
        help="Daily working hours end time (24h format)",
    )
    working_days = fields.Selection(
        [
            ("monday_friday", "Monday to Friday"),
            ("monday_saturday", "Monday to Saturday"),
            ("seven_days", "Seven Days"),
            ("custom", "Custom Schedule"),
        ],
        string="Working Days",
        default="monday_friday",
        help="Team working days schedule",
    )
    overtime_available = fields.Boolean(
        string="Overtime Available",
        default=True,
        help="Team available for overtime work",
    )

    # ============================================================================
    # EQUIPMENT AND RESOURCES
    # ============================================================================
    vehicle_ids = fields.Many2many(
        "records.vehicle",
        string="Assigned Vehicles",
        help="Vehicles assigned to this team",
    )
    equipment_ids = fields.Many2many(
        "maintenance.equipment",
        string="Assigned Equipment",
        help="Shredding equipment assigned to team",
    )
    primary_equipment_id = fields.Many2one(
        "maintenance.equipment",
        string="Primary Equipment",
        help="Primary shredding equipment for this team",
    )
    mobile_unit = fields.Boolean(
        string="Mobile Unit", default=False, help="Team operates mobile shredding unit"
    )

    # ============================================================================
    # PERFORMANCE METRICS
    # ============================================================================
    total_services_completed = fields.Integer(
        string="Total Services Completed",
        compute="_compute_performance_metrics",
        store=True,
        help="Total number of completed services",
    )
    total_weight_processed = fields.Float(
        string="Total Weight Processed (lbs)",
        compute="_compute_performance_metrics",
        store=True,
        help="Total weight processed by team",
    )
    average_service_time = fields.Float(
        string="Average Service Time (hours)",
        compute="_compute_performance_metrics",
        store=True,
        help="Average time per service completion",
    )
    efficiency_rating = fields.Float(
        string="Efficiency Rating (%)",
        compute="_compute_efficiency_rating",
        store=True,
        help="Team efficiency based on capacity utilization",
    )
    customer_satisfaction = fields.Float(
        string="Customer Satisfaction Score",
        compute="_compute_customer_satisfaction",
        store=True,
        help="Average customer satisfaction rating based on portal feedback (1.0-5.0 scale)",
    )
    total_ratings_received = fields.Integer(
        string="Total Ratings Received",
        compute="_compute_customer_satisfaction",
        store=True,
        help="Total number of customer ratings received via portal feedback",
    )
    satisfaction_percentage = fields.Float(
        string="Satisfaction Percentage",
        compute="_compute_customer_satisfaction",
        store=True,
        help="Percentage of satisfied customers (rating >= 4.0) from portal feedback",
    )
    latest_feedback_date = fields.Datetime(
        string="Latest Feedback Date",
        compute="_compute_customer_satisfaction",
        store=True,
        help="Date of most recent customer feedback",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    service_ids = fields.One2many(
        "shredding.service",
        "team_id",
        string="Shredding Services",
        help="Services assigned to this team",
    )
    service_count = fields.Integer(
        string="Service Count",
        compute="_compute_service_count",
        store=True,
        help="Total number of assigned services",
    )
    active_service_ids = fields.One2many(
        "shredding.service",
        "team_id",
        string="Active Services",
        domain=[("state", "in", ["scheduled", "in_progress"])],
        help="Currently active services",
    )
    completed_service_ids = fields.One2many(
        "shredding.service",
        "team_id",
        string="Completed Services",
        domain=[("state", "=", "completed")],
        help="Completed services",
    )
    feedback_ids = fields.One2many(
        "customer.feedback",
        "team_id",
        string="Customer Feedback",
        help="Customer feedback related to this team's services",
    )

    # ============================================================================
    # LOCATION AND AVAILABILITY
    # ============================================================================
    base_location_id = fields.Many2one(
        "records.location",
        string="Base Location",
        help="Team's base operating location",
    )
    service_area_ids = fields.Many2many(
        "records.location",
        string="Service Areas",
        help="Geographic areas this team can service",
    )
    travel_radius = fields.Float(
        string="Travel Radius (miles)",
        default=50.0,
        help="Maximum travel distance for services",
    )
    emergency_response = fields.Boolean(
        string="Emergency Response",
        default=False,
        help="Team available for emergency services",
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=[("res_model", "=", "shredding.team")],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=[("res_model", "=", "shredding.team")],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("res_model", "=", self._name)],
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("member_ids")
    def _compute_member_count(self):
        """Compute total number of team members"""
        for team in self:
            team.member_count = len(team.member_ids)

    @api.depends("service_ids")
    def _compute_service_count(self):
        """Compute total number of assigned services"""
        for team in self:
            team.service_count = len(team.service_ids)

    @api.depends(
        "service_ids.state",
        "service_ids.actual_weight",
        "service_ids.duration_hours",
    )
    def _compute_performance_metrics(self):
        """Compute team performance metrics"""
        for team in self:
            completed_services = team.service_ids.filtered(
                lambda s: s.state == "completed"
            )
            team.total_services_completed = len(completed_services)
            team.total_weight_processed = sum(
                completed_services.mapped("actual_weight")
            )
            if completed_services:
                total_duration = sum(
                    s.duration_hours
                    for s in completed_services
                    if s.duration_hours
                )
                team.average_service_time = (
                    (total_duration / len(completed_services))
                    if completed_services
                    else 0.0
                )
            else:
                team.average_service_time = 0.0

    @api.depends(
        "total_weight_processed",
        "max_capacity_per_day",
        "total_services_completed",
    )
    def _compute_efficiency_rating(self):
        """Compute team efficiency rating"""
        for team in self:
            if team.max_capacity_per_day > 0:
                days_active = max(1, team.total_services_completed // 5)
                theoretical_capacity = team.max_capacity_per_day * days_active
                team.efficiency_rating = (
                    (
                        (team.total_weight_processed / theoretical_capacity)
                        * 100
                    )
                    if theoretical_capacity > 0
                    else 0.0
                )
            else:
                team.efficiency_rating = 0.0

    @api.depends(
        "feedback_ids.rating",
        "feedback_ids.sentiment_score",
        "service_ids.state",
    )
    def _compute_customer_satisfaction(self):
        """Compute customer satisfaction metrics using portal feedback."""
        for team in self:
            team_feedback = team.feedback_ids.filtered(lambda f: f.rating > 0)
            service_feedback = self.env["customer.feedback"].search(
                [
                    ("service_id", "in", team.completed_service_ids.ids),
                    ("rating", ">", 0),
                ]
            )
            all_feedback = team_feedback | service_feedback
            if all_feedback:
                ratings = all_feedback.mapped("rating")
                if ratings:
                    team.total_ratings_received = len(ratings)
                    team.customer_satisfaction = sum(ratings) / len(ratings)
                    satisfied_count = len([r for r in ratings if r >= 4.0])
                    team.satisfaction_percentage = (
                        satisfied_count / len(ratings)
                    ) * 100
                    team.latest_feedback_date = all_feedback.sorted(
                        "create_date", reverse=True
                    )[0].create_date
                else:
                    team._set_default_satisfaction_metrics()
            else:
                team._set_default_satisfaction_metrics()

    def _set_default_satisfaction_metrics(self):
        """Set default satisfaction metrics when no data is available"""
        self.total_ratings_received = 0
        self.customer_satisfaction = 0.0
        self.satisfaction_percentage = 0.0
        self.latest_feedback_date = False

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate_team(self):
        """Activate the team for service assignment"""
        self.ensure_one()
        if not self.team_leader_id:
            raise UserError(_("Team leader is required to activate team"))
        if not self.member_ids:
            raise UserError(_("Team must have members to be activated"))
        self.write({"state": "active"})
        self.message_post(body=_("Team activated"))

    def action_deactivate_team(self):
        """Deactivate the team"""
        self.ensure_one()
        if self.active_service_ids:
            raise UserError(
                _(
                    "Cannot deactivate team with active services. Complete or reassign services first."
                )
            )
        self.write({"state": "inactive"})
        self.message_post(body=_("Team deactivated"))

    def action_suspend_team(self):
        """Suspend team operations temporarily"""
        self.ensure_one()
        self.write({"state": "suspended"})
        self.message_post(body=_("Team suspended"))

    def action_view_services(self):
        """View all services assigned to this team"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Team Services"),
            "res_model": "shredding.service",
            "view_mode": "tree,form",
            "domain": [("team_id", "=", self.id)],
            "context": {"default_team_id": self.id},
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_available_capacity(self, date=None):
        """Calculate available capacity for a given date"""
        self.ensure_one()
        if not date:
            date = fields.Date.today()
        scheduled_services = self.service_ids.filtered(
            lambda s: s.service_date == date
            and s.state in ["scheduled", "in_progress"]
        )
        scheduled_weight = sum(scheduled_services.mapped("estimated_weight"))
        available_capacity = max(
            0, self.max_capacity_per_day - scheduled_weight
        )
        return {
            "available_capacity": available_capacity,
            "scheduled_weight": scheduled_weight,
            "total_capacity": self.max_capacity_per_day,
            "utilization_percent": (
                (scheduled_weight / self.max_capacity_per_day * 100)
                if self.max_capacity_per_day > 0
                else 0
            ),
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("working_hours_start", "working_hours_end")
    def _check_working_hours(self):
        """Validate working hours"""
        for team in self:
            if team.working_hours_start >= team.working_hours_end:
                raise ValidationError(_("End time must be after start time"))
            if not 0 <= team.working_hours_start <= 24:
                raise ValidationError(_("Start time must be between 0 and 24"))
            if not 0 <= team.working_hours_end <= 24:
                raise ValidationError(_("End time must be between 0 and 24"))

    @api.constrains("max_capacity_per_day")
    def _check_capacity(self):
        """Validate daily capacity"""
        for team in self:
            if team.max_capacity_per_day < 0:
                raise ValidationError(_("Daily capacity cannot be negative"))

    @api.constrains("member_ids", "team_leader_id")
    def _check_team_composition(self):
        """Validate team composition"""
        for team in self:
            if team.team_leader_id and team.team_leader_id not in team.member_ids:
                raise ValidationError(_("Team leader must be included in team members"))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add team leader to members if not present."""
        teams = super().create(vals_list)
        for team in teams.filtered(
            lambda t: t.team_leader_id and t.team_leader_id not in t.member_ids
        ):
            team.member_ids = [(4, team.team_leader_id.id)]
        return teams

    def write(self, vals):
        """Override write to ensure team leader is always a member."""
        res = super().write(vals)
        if "team_leader_id" in vals or "member_ids" in vals:
            for team in self.filtered(
                lambda t: t.team_leader_id
                and t.team_leader_id not in t.member_ids
            ):
                team.write({"member_ids": [(4, team.team_leader_id.id)]})
        return res
