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
        string="Customer Satisfaction",
        compute="_compute_customer_satisfaction",
        store=True,
        help="Average customer satisfaction rating",
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
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
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
        """Compute customer satisfaction based on completed services"""
        for team in self:
            completed_with_rating = team.service_ids.filtered(
                lambda s: s.state == "completed" and s.customer_signature
            )
            if completed_with_rating:
                # Placeholder: In reality, you'd have a rating field
                team.customer_satisfaction = 4.5  # Default good rating
            else:
                team.customer_satisfaction = 0.0

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
    # CONSTRAINT METHODS
    # ============================================================================
    @api.constrains("working_hours_start", "working_hours_end")
    def _check_working_hours(self):
        """Validate working hours"""
        for team in self:
            if team.working_hours_start >= team.working_hours_end:
                raise ValidationError(_("End time must be after start time"))
            if not (0 <= team.working_hours_start <= 24):
                raise ValidationError(_("Start time must be between 0 and 24"))
            if not (0 <= team.working_hours_end <= 24):
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
                team.member_ids = [(4, team.team_leader_id.id)]
        return teams

    def write(self, vals):
        """Override write to handle team composition changes"""
        if "team_leader_id" in vals and vals["team_leader_id"]:
            # Ensure new leader is in member list
            for team in self:
                if vals["team_leader_id"] not in team.member_ids.ids:
                    if "member_ids" not in vals:
                        vals["member_ids"] = [(4, vals["team_leader_id"])]

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
            "team_leader": self.team_leader_id.name if self.team_leader_id else None,
            "daily_capacity": self.max_capacity_per_day,
        }

    @api.model
    def get_available_teams(self, material_type=None, service_date=None):
        """Get teams available for service assignment"""
        domain = [("state", "=", "active")]

        teams = self.search(domain)

        if material_type:
            # Filter by specialization capability
            suitable_teams = teams.filtered(
                lambda t: t.check_specialization_match(material_type)["match"]
            )
        else:
            suitable_teams = teams

        if service_date:
            # Check capacity availability
            available_teams = []
            for team in suitable_teams:
                capacity_info = team.get_available_capacity(service_date)
                if capacity_info["available_capacity"] > 0:
                    available_teams.append(team)
            return self.browse([t.id for t in available_teams])

        return suitable_teams
