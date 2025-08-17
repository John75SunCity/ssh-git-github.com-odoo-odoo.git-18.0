from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class ShreddingTeam(models.Model):
    _name = 'shredding.team'
    _description = 'Shredding Team Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    partner_id = fields.Many2one()
    active = fields.Boolean()
    sequence = fields.Integer()
    state = fields.Selection()
    description = fields.Text(string='Description')
    team_leader_id = fields.Many2one()
    supervisor_id = fields.Many2one()
    member_ids = fields.Many2many()
    employee_ids = fields.Many2many()
    member_count = fields.Integer()
    specialization = fields.Selection()
    certification_level = fields.Selection()
    security_clearance = fields.Boolean()
    max_capacity_per_day = fields.Float()
    max_volume_per_day = fields.Float()
    working_hours_start = fields.Float()
    working_hours_end = fields.Float()
    working_days = fields.Selection()
    overtime_available = fields.Boolean()
    vehicle_ids = fields.Many2many()
    equipment_ids = fields.Many2many()
    primary_equipment_id = fields.Many2one()
    mobile_unit = fields.Boolean()
    total_services_completed = fields.Integer()
    total_weight_processed = fields.Float()
    average_service_time = fields.Float()
    efficiency_rating = fields.Float()
    customer_satisfaction = fields.Float()
    total_ratings_received = fields.Integer()
    satisfaction_percentage = fields.Float()
    latest_feedback_date = fields.Datetime()
    service_ids = fields.One2many()
    service_count = fields.Integer()
    active_service_ids = fields.One2many()
    completed_service_ids = fields.One2many()
    feedback_ids = fields.One2many()
    base_location_id = fields.Many2one()
    service_area_ids = fields.Many2many()
    travel_radius = fields.Float()
    emergency_response = fields.Boolean()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')
    date = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_member_count(self):
            """Compute total number of team members"""
            for team in self:
                team.member_count = len(team.member_ids)


    def _compute_service_count(self):
            """Compute total number of assigned services"""
            for team in self:
                team.service_count = len(team.service_ids)


    def _compute_performance_metrics(self):
            """Compute team performance metrics"""
            for team in self:
                completed_services = team.service_ids.filtered()
                    lambda s: s.state == "completed"

                team.total_services_completed = len(completed_services)
                team.total_weight_processed = sum()
                    completed_services.mapped("actual_weight")

                if completed_services:
                    total_duration = sum()
                        s.duration_hours
                        for s in completed_services:
                        if s.duration_hours:

                    team.average_service_time = ()
                        (total_duration / len(completed_services))
                        if completed_services:
                        else 0.0

                else:
                    team.average_service_time = 0.0


    def _compute_efficiency_rating(self):
            """Compute team efficiency rating"""
            for team in self:
                if team.max_capacity_per_day > 0:
                    days_active = max(1, team.total_services_completed // 5)
                    theoretical_capacity = team.max_capacity_per_day * days_active
                    team.efficiency_rating = ()
                        ()
                            (team.total_weight_processed / theoretical_capacity)
                            * 100

                        if theoretical_capacity > 0:
                        else 0.0

                else:
                    team.efficiency_rating = 0.0


    def _compute_customer_satisfaction(self):
            """Compute customer satisfaction metrics using portal feedback."""
            for team in self:
                team_feedback = team.feedback_ids.filtered(lambda f: f.rating > 0)
                service_feedback = self.env["customer.feedback").search(]
                    []
                        ("service_id", "in", team.completed_service_ids.ids),
                        ("rating", ">", 0),


                all_feedback = team_feedback | service_feedback
                if all_feedback:
                    ratings = all_feedback.mapped("rating")
                    if ratings:
                        team.total_ratings_received = len(ratings)
                        team.customer_satisfaction = sum(ratings) / len(ratings)
                        satisfied_count = len([r for r in ratings if r >= 4.0]):
                        team.satisfaction_percentage = ()
                            satisfied_count / len(ratings)

                        team.latest_feedback_date = all_feedback.sorted()
                            "create_date", reverse=True

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
            """Activate the team for service assignment""":
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
                raise UserError()
                    _()
                        "Cannot deactivate team with active services. Complete or reassign services first."


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
            return {}
                "type": "ir.actions.act_window",
                "name": _("Team Services"),
                "res_model": "shredding.service",
                "view_mode": "tree,form",
                "domain": [("team_id", "=", self.id)],
                "context": {"default_team_id": self.id},


        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def get_available_capacity(self, date=None):
            """Calculate available capacity for a given date""":
            self.ensure_one()
            if not date:

    def _check_working_hours(self):
            """Validate working hours"""
            for team in self:
                if team.working_hours_start >= team.working_hours_end:
                    raise ValidationError(_("End time must be after start time"))
                if not 0 <= team.working_hours_start <= 24:
                    raise ValidationError(_("Start time must be between 0 and 24"))
                if not 0 <= team.working_hours_end <= 24:
                    raise ValidationError(_("End time must be between 0 and 24"))


    def _check_capacity(self):
            """Validate daily capacity"""
            for team in self:
                if team.max_capacity_per_day < 0:
                    raise ValidationError(_("Daily capacity cannot be negative"))


    def _check_team_composition(self):
            """Validate team composition"""
            for team in self:
                if team.team_leader_id and team.team_leader_id not in team.member_ids:
                    raise ValidationError(_("Team leader must be included in team members"))

        # ============================================================================
            # ORM OVERRIDES
        # ============================================================================

    def create(self, vals_list):
            """Override create to add team leader to members if not present.""":
            teams = super().create(vals_list)
            for team in teams.filtered(:)
                lambda t: t.team_leader_id and t.team_leader_id not in t.member_ids

                team.member_ids = [(4, team.team_leader_id.id)]
            return teams


    def write(self, vals):
            """Override write to ensure team leader is always a member."""
            res = super().write(vals)
            if "team_leader_id" in vals or "member_ids" in vals:
                for team in self.filtered(:)
                    lambda t: t.team_leader_id
                    and t.team_leader_id not in t.member_ids

                    team.write({"member_ids": [(4, team.team_leader_id.id)]})
            return res
            return res
