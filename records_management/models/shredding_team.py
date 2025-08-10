# -*- coding: utf-8 -*-
"""
Shredding Team Management Module

This module provides comprehensive team management for shredding operations within
the Records Management System. It handles team organization, capacity planning,
specialization tracking, and service assignment with complete workflow integration.

Key Features:
- Team composition and leadership management
- Specialization tracking (paper, electronic, mixed, confidential)
- Capacity planning with scheduling constraints
- Service assignment and workload tracking
- Performance monitoring and reporting
- Integration with shredding services and equipment

Business Processes:
1. Team Setup: Create teams with members and specializations
2. Capacity Planning: Define working hours and daily capacity limits
3. Service Assignment: Assign teams to shredding services based on specialization
4. Performance Tracking: Monitor service completion and team efficiency
5. Resource Management: Optimize team utilization and scheduling

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
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
        "res.users", string="Supervisor", help="Team supervisor for escalations"
    )
    member_ids = fields.Many2many(
        "res.users", string="Team Members", help="All team members including leader"
    )
    employee_ids = fields.Many2many(
        "hr.employee", string="Employees", help="HR employee records for team members"
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
    secondary_specializations = fields.Many2many(
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
    # New rating tracking fields integrated with existing portal feedback
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
    # Integration with existing portal feedback system
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
    service_areas = fields.Many2many(
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

    @api.depends("service_ids", "service_ids.state", "service_ids.actual_weight")
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
                    s.duration_hours for s in completed_services if s.duration_hours
                )
                team.average_service_time = (
                    total_duration / len(completed_services)
                    if completed_services
                    else 0.0
                )
            else:
                team.average_service_time = 0.0

    @api.depends("total_weight_processed", "max_capacity_per_day")
    def _compute_efficiency_rating(self):
        """Compute team efficiency rating"""
        for team in self:
            if team.max_capacity_per_day > 0:
                # Calculate based on capacity utilization
                days_active = max(
                    1, team.total_services_completed // 5
                )  # Rough estimate
                theoretical_capacity = team.max_capacity_per_day * days_active
                team.efficiency_rating = (
                    (team.total_weight_processed / theoretical_capacity) * 100
                    if theoretical_capacity > 0
                    else 0.0
                )
            else:
                team.efficiency_rating = 0.0

    @api.depends("service_ids", "service_ids.customer_signature")
    def _compute_customer_satisfaction(self):
        """
        Compute customer satisfaction metrics using existing portal feedback system

        Integration with Portal Feedback System:
        - Uses existing customer.feedback model for comprehensive rating data
        - Leverages portal feedback sentiment analysis and rating system
        - Integrates with AI-powered feedback categorization
        - Links team performance to actual customer portal interactions

        Rating Sources (in priority order):
        1. Direct team feedback via customer.feedback model
        2. Service-related feedback linked to team's completed services
        3. Portal request feedback for services assigned to this team
        4. Fallback estimation based on service completion patterns

        Calculation Method:
        - Primary: Average of numerical ratings from customer.feedback
        - Secondary: Sentiment scores converted to 1-5 scale
        - Tertiary: Service completion rate as satisfaction proxy
        """
        for team in self:
            # Get direct team feedback from existing portal feedback system
            team_feedback = team.feedback_ids.filtered(
                lambda f: f.rating and f.rating > 0
            )

            # Get service-related feedback for team's completed services
            service_feedback = self.env["customer.feedback"].search(
                [
                    (
                        "service_id",
                        "in",
                        team.service_ids.filtered(lambda s: s.state == "completed").ids,
                    ),
                    ("rating", ">", 0),
                ]
            )

            # Combine all relevant feedback
            all_feedback = team_feedback | service_feedback

            if all_feedback:
                # Calculate metrics from actual portal feedback
                ratings = all_feedback.mapped("rating")
                ratings = [r for r in ratings if r and r > 0]  # Filter valid ratings

                if ratings:
                    team.total_ratings_received = len(ratings)
                    team.customer_satisfaction = sum(ratings) / len(ratings)

                    # Calculate satisfaction percentage (ratings >= 4.0 considered satisfied)
                    satisfied_count = len([r for r in ratings if r >= 4.0])
                    team.satisfaction_percentage = (
                        satisfied_count / len(ratings)
                    ) * 100

                    # Get latest feedback date
                    latest_feedback = all_feedback.sorted("create_date", reverse=True)
                    team.latest_feedback_date = (
                        latest_feedback[0].create_date if latest_feedback else False
                    )
                else:
                    # Use sentiment scores as fallback
                    sentiment_scores = all_feedback.mapped("sentiment_score")
                    valid_sentiments = [s for s in sentiment_scores if s is not False]

                    if valid_sentiments:
                        # Convert sentiment (-1 to 1) to rating scale (1 to 5)
                        avg_sentiment = sum(valid_sentiments) / len(valid_sentiments)
                        team.customer_satisfaction = 3.0 + (
                            avg_sentiment * 2.0
                        )  # Maps -1→1, 0→3, 1→5
                        team.total_ratings_received = len(valid_sentiments)

                        # Estimate satisfaction based on positive sentiment
                        positive_sentiments = len(
                            [s for s in valid_sentiments if s > 0.2]
                        )
                        team.satisfaction_percentage = (
                            positive_sentiments / len(valid_sentiments)
                        ) * 100

                        latest_feedback = all_feedback.sorted(
                            "create_date", reverse=True
                        )
                        team.latest_feedback_date = (
                            latest_feedback[0].create_date if latest_feedback else False
                        )
                    else:
                        team._set_default_satisfaction_metrics()

            else:
                # Fallback: Check for service completion patterns
                completed_services = team.service_ids.filtered(
                    lambda s: s.state == "completed"
                )

                if completed_services:
                    # Estimate satisfaction based on service completion and timeliness
                    on_time_services = (
                        completed_services.filtered(
                            lambda s: hasattr(s, "scheduled_date")
                            and hasattr(s, "completion_date")
                            and s.scheduled_date
                            and s.completion_date
                            and fields.Datetime.from_string(
                                str(s.completion_date)
                            ).date()
                            <= s.scheduled_date
                        )
                        if hasattr(completed_services, "scheduled_date")
                        else completed_services
                    )

                    completion_rate = len(on_time_services) / len(completed_services)

                    # Estimate satisfaction: 3.0-4.5 range based on performance
                    estimated_satisfaction = 3.0 + (
                        completion_rate * 1.5
                    )  # 3.0 to 4.5 scale

                    team.total_ratings_received = 0  # No actual ratings
                    team.customer_satisfaction = estimated_satisfaction
                    team.satisfaction_percentage = completion_rate * 100
                    team.latest_feedback_date = False

                    # Log estimation for transparency
                    team.message_post(
                        body=_(
                            "Customer satisfaction estimated at %.1f based on service completion rate (%.1f%%). "
                            "Actual customer feedback via portal recommended for accurate metrics."
                        )
                        % (team.customer_satisfaction, team.satisfaction_percentage)
                    )
                else:
                    # No data available - reset metrics
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

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    )
        self.message_post(body=_("Team activated"))

    def action_deactivate_team(self):
        """Deactivate the team"""
        self.ensure_one()

        # Check for active services
        active_services = self.service_ids.filtered(
            lambda s: s.state in ["scheduled", "in_progress"]
        )
        if active_services:
            raise UserError(
                _(
                    "Cannot deactivate team with active services. "
                    "Complete or reassign services first."
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

    def action_view_active_services(self):
        """View active services for this team"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Active Services"),
            "res_model": "shredding.service",
            "view_mode": "tree,form",
            "domain": [
                ("team_id", "=", self.id),
                ("state", "in", ["scheduled", "in_progress"]),
            ],
            "context": {"default_team_id": self.id},
        }

    def action_assign_equipment(self):
        """Assign equipment to this team"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Assign Equipment"),
            "res_model": "maintenance.equipment",
            "view_mode": "tree,form",
            "domain": [("equipment_assign_to", "=", "other")],
            "context": {"default_team_id": self.id},
        }

    def action_schedule_service(self):
        """Create new service for this team"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Service"),
            "res_model": "shredding.service",
            "view_mode": "form",
            "target": "new",
            "context": {"default_team_id": self.id},
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_available_capacity(self, date=None):
        """Calculate available capacity for given date"""
        self.ensure_one()
        if not date:
            date = fields.Date.today()

        # Get scheduled services for the date
        scheduled_services = self.service_ids.filtered(
            lambda s: s.service_date == date and s.state in ["scheduled", "in_progress"]
        )

        scheduled_weight = sum(scheduled_services.mapped("estimated_weight"))
        available_capacity = max(0, self.max_capacity_per_day - scheduled_weight)

        return {
            "available_capacity": available_capacity,
            "scheduled_weight": scheduled_weight,
            "total_capacity": self.max_capacity_per_day,
            "utilization_percent": (
                (scheduled_weight / self.max_capacity_per_day) * 100
                if self.max_capacity_per_day > 0
                else 0
            ),
        }

    def get_team_schedule(self, start_date=None, end_date=None):
        """Get team schedule for date range"""
        self.ensure_one()
        if not start_date:
            start_date = fields.Date.today()
        if not end_date:
            end_date = start_date + timedelta(days=7)

        services = self.service_ids.filtered(
            lambda s: start_date <= s.service_date <= end_date
        )

        schedule = {}
        current_date = start_date
        while current_date <= end_date:
            day_services = services.filtered(lambda s: s.service_date == current_date)
            capacity_info = self.get_available_capacity(current_date)

            schedule[current_date.strftime("%Y-%m-%d")] = {
                "services": day_services.ids,
                "service_count": len(day_services),
                "capacity_info": capacity_info,
            }
            current_date += timedelta(days=1)

        return schedule

    def check_specialization_match(self, material_type):
        """Check if team can handle specific material type"""
        self.ensure_one()

        # Primary specialization match
        if self.specialization == material_type:
            return {"match": True, "level": "primary"}

        # Secondary specialization match
        if material_type in self.secondary_specializations.mapped("name"):
            return {"match": True, "level": "secondary"}

        # Mixed capability
        if self.specialization == "mixed":
            return {"match": True, "level": "mixed"}

        return {"match": False, "level": None}

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

    @api.constrains("travel_radius")
    def _check_travel_radius(self):
        """Validate travel radius"""
        for team in self:
            if team.travel_radius < 0:
                raise ValidationError(_("Travel radius cannot be negative"))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set up team properly"""
        teams = super().create(vals_list)
        for team in teams:
            # Add team leader to members if not already included
            if team.team_leader_id and team.team_leader_id not in team.member_ids:
                team.member_ids = [(4, team.team_leader_id.id)] + [
                    (4, m.id) for m in team.member_ids
                ]
        return teams

    def write(self, vals):
        """Override write to handle team composition changes"""
        if "team_leader_id" in vals and vals["team_leader_id"]:
            # Ensure new leader is in member list
            for team in self:
                leader_id = vals["team_leader_id"]
                # If member_ids is being updated, merge leader into it
                if "member_ids" in vals and vals["member_ids"]:
                    # Extract all ids from incoming member_ids commands
                    member_ids_cmds = vals["member_ids"]
                    # Only add leader if not already present in the update
                    ids_in_cmds = set()
                    for cmd in member_ids_cmds:
                        if cmd[0] == 4:
                            ids_in_cmds.add(cmd[1])
                        elif cmd[0] == 6 and isinstance(cmd[2], list):
                            ids_in_cmds.update(cmd[2])
                    if leader_id not in ids_in_cmds:
                        vals["member_ids"].append((4, leader_id))
                # If member_ids is not being updated, append leader to current members
                elif leader_id not in team.member_ids.ids:
                    vals["member_ids"] = [(4, leader_id)]

        return super().write(vals)

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_team_summary(self):
        """Get team summary for reporting"""
        self.ensure_one()
        return {
            "name": self.name,
            "state": self.state,
            "specialization": self.specialization,
            "member_count": self.member_count,
            "services_completed": self.total_services_completed,
            "weight_processed": self.total_weight_processed,
            "efficiency_rating": self.efficiency_rating,
            "customer_satisfaction": self.customer_satisfaction,
            "total_ratings": self.total_ratings_received,
            "satisfaction_percentage": self.satisfaction_percentage,
            "latest_feedback": self.latest_feedback_date,
            "team_leader": self.team_leader_id.name if self.team_leader_id else None,
            "daily_capacity": self.max_capacity_per_day,
        }

    def get_satisfaction_analysis(self):
        """
        Get detailed customer satisfaction analysis leveraging existing portal feedback

        Returns:
            dict: Comprehensive satisfaction metrics and recommendations
        """
        self.ensure_one()

        # Analyze feedback trends using existing portal feedback data
        feedback_data = self.feedback_ids | self.env["customer.feedback"].search(
            [("service_id", "in", self.service_ids.ids)]
        )

        # Sentiment analysis from existing AI system
        positive_feedback = feedback_data.filtered(
            lambda f: f.sentiment_category == "positive"
        )
        negative_feedback = feedback_data.filtered(
            lambda f: f.sentiment_category == "negative"
        )

        # Rating distribution
        rating_distribution = {}
        for rating in [1, 2, 3, 4, 5]:
            count = len(feedback_data.filtered(lambda f: f.rating == rating))
            rating_distribution[rating] = count

        return {
            "team_name": self.name,
            "overall_rating": self.customer_satisfaction,
            "total_feedback_count": len(feedback_data),
            "satisfaction_percentage": self.satisfaction_percentage,
            "rating_distribution": rating_distribution,
            "sentiment_breakdown": {
                "positive_count": len(positive_feedback),
                "negative_count": len(negative_feedback),
                "neutral_count": len(feedback_data)
                - len(positive_feedback)
                - len(negative_feedback),
            },
            "recent_feedback_trend": self._calculate_feedback_trend(feedback_data),
            "improvement_recommendations": self._generate_improvement_recommendations(
                feedback_data
            ),
            "latest_feedback_date": self.latest_feedback_date,
        }

    def _calculate_feedback_trend(self, feedback_data):
        """Calculate feedback trend over time using existing feedback data"""
        if not feedback_data:
            return {"trend": "no_data", "change": 0.0}

        # Get recent vs older feedback
        recent_cutoff = fields.Datetime.now() - timedelta(days=30)
        recent_feedback = feedback_data.filtered(
            lambda f: f.create_date >= recent_cutoff
        )
        older_feedback = feedback_data.filtered(lambda f: f.create_date < recent_cutoff)

        if not recent_feedback or not older_feedback:
            return {"trend": "insufficient_data", "change": 0.0}

        recent_avg = sum(recent_feedback.mapped("rating")) / len(recent_feedback)
        older_avg = sum(older_feedback.mapped("rating")) / len(older_feedback)

        change = recent_avg - older_avg

        if change > 0.2:
            trend = "improving"
        elif change < -0.2:
            trend = "declining"
        else:
            trend = "stable"

        return {"trend": trend, "change": change}

    def _generate_improvement_recommendations(self, feedback_data):
        """Generate recommendations based on existing feedback analysis"""
        recommendations = []

        negative_feedback = feedback_data.filtered(
            lambda f: f.sentiment_category == "negative"
        )

        if len(negative_feedback) > len(feedback_data) * 0.3:  # More than 30% negative
            recommendations.append(
                "Address recurring customer concerns identified in negative feedback"
            )

        if self.customer_satisfaction < 3.5:
            recommendations.append(
                "Focus on service quality improvement and customer communication"
            )

        if self.total_ratings_received < 5:
            recommendations.append(
                "Encourage more customer feedback through portal engagement"
            )

        return recommendations

    # ...existing code...


class ShreddingSpecialization(models.Model):
    """Shredding Team Specializations"""

    _name = "shredding.specialization"
    _description = "Shredding Specialization"
    _order = "name"

    name = fields.Char(
        string="Specialization Name",
        required=True,
        help="Name of the specialization",
    )
    description = fields.Text(
        string="Description",
        help="Detailed description of the specialization",
    )
    certification_required = fields.Boolean(
        string="Certification Required",
        default=False,
        help="Specialization requires specific certification",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether this specialization is active",
    )
