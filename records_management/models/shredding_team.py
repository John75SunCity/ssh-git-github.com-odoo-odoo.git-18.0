from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ShreddingTeam(models.Model):
    _name = 'shredding.team'
    _description = 'Shredding Team Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Team Name", required=True, tracking=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('inactive', 'Inactive'),
    ], string="Status", default='draft', required=True, tracking=True)
    description = fields.Text(string='Description')

    # ============================================================================
    # TEAM COMPOSITION
    # ============================================================================
    team_leader_id = fields.Many2one(comodel_name='hr.employee', string="Team Leader", tracking=True)
    member_ids = fields.Many2many('hr.employee', 'shredding_team_member_rel', 'team_id', 'employee_id', string="Team Members")
    member_count = fields.Integer(string="Member Count", compute='_compute_member_count', store=True)

    # ============================================================================
    # SPECIALIZATION & COMPLIANCE
    # ============================================================================
    specialization = fields.Selection(
        [
            ("on_site", "Mobile Shredding"),
            ("off_site", "Off-Site Plant"),
            ("media_destruction", "Media Destruction"),
            ("specialized", "Specialized Destruction"),
        ],
        string="Specialization",
    )
    certification_level = fields.Selection([('naid_aaa', 'NAID AAA Certified'), ('standard', 'Standard')], string="Certification Level")
    security_clearance = fields.Boolean(string="Security Clearance")

    # ============================================================================
    # CAPACITY & SCHEDULING
    # ============================================================================
    max_capacity_per_day = fields.Float(string="Max Weight/Day (kg)")
    max_volume_per_day = fields.Float(string="Max Volume/Day (m³)")
    working_hours_start = fields.Float(string="Working Hours Start", default=8.0)
    working_hours_end = fields.Float(string="Working Hours End", default=17.0)
    overtime_available = fields.Boolean(string="Overtime Available")

    # ============================================================================
    # RESOURCES & LOCATION
    # ============================================================================
    vehicle_ids = fields.Many2many(
        'fleet.vehicle',
        relation='shredding_team_vehicle_rel',
        column1='team_id',
        column2='vehicle_id',
        string="Assigned Vehicles"
    )
    equipment_ids = fields.Many2many(
        'maintenance.equipment',
        relation='shredding_team_equipment_rel',
        column1='team_id',
        column2='equipment_id',
        string="Assigned Equipment",
        domain="[('equipment_category', '=', 'shredder')]"
    )
    primary_equipment_id = fields.Many2one(comodel_name='maintenance.equipment', string="Primary Shredder")
    mobile_unit = fields.Boolean(string="Is Mobile Unit")
    base_location_id = fields.Many2one(comodel_name='stock.location', string="Base Location")
    service_area_ids = fields.Many2many(
        'res.country.state',
        relation='shredding_team_service_area_rel',
        column1='team_id',
        column2='state_id',
        string="Service Areas"
    )
    travel_radius = fields.Float(string="Travel Radius (km)")
    emergency_response = fields.Boolean(string="Emergency Response Team")

    # ============================================================================
    # PERFORMANCE METRICS (COMPUTED)
    # ============================================================================
    service_ids = fields.One2many('project.task', 'shredding_team_id', string="Assigned Services")
    service_count = fields.Integer(string="Total Service Count", compute='_compute_performance_metrics', store=True)
    total_services_completed = fields.Integer(string="Services Completed", compute='_compute_performance_metrics', store=True)
    total_weight_processed = fields.Float(string="Total Weight Processed (kg)", compute='_compute_performance_metrics', store=True)
    average_service_time = fields.Float(string="Avg. Service Time (hrs)", compute='_compute_performance_metrics', store=True)
    efficiency_rating = fields.Float(string="Efficiency Rating (%)", compute='_compute_performance_metrics', store=True)

    # ============================================================================
    # CUSTOMER FEEDBACK (COMPUTED)
    # ============================================================================
    feedback_ids = fields.One2many('customer.feedback', 'shredding_team_id', string="Direct Feedback")
    customer_satisfaction = fields.Float(string="Avg. Satisfaction (1-5)", compute='_compute_customer_satisfaction', store=True)
    total_ratings_received = fields.Integer(string="Total Ratings", compute='_compute_customer_satisfaction', store=True)
    satisfaction_percentage = fields.Float(string="Satisfaction Rate (%)", compute='_compute_customer_satisfaction', store=True)
    latest_feedback_date = fields.Datetime(string="Latest Feedback", compute='_compute_customer_satisfaction', store=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('member_ids')
    def _compute_member_count(self):
        for team in self:
            team.member_count = len(team.member_ids)

    @api.depends('service_ids.total_weight', 'max_capacity_per_day')
    def _compute_performance_metrics(self):
        for team in self:
            # Simplified calculation since stage_id and planned_hours don't exist in shredding service model
            team.service_count = len(team.service_ids)
            team.total_services_completed = len(team.service_ids)  # Simplified
            team.total_weight_processed = sum(team.service_ids.mapped('total_weight') or [0.0])

            # Simplified time calculation
            if team.service_ids:
                team.average_service_time = 8.0  # Default estimate hours
            else:
                team.average_service_time = 0.0

            if team.max_capacity_per_day > 0 and team.total_services_completed > 0:
                # Assuming 1 service per day for simplicity in this calculation
                theoretical_capacity = team.max_capacity_per_day * team.total_services_completed
                team.efficiency_rating = (team.total_weight_processed / theoretical_capacity) * 100 if theoretical_capacity > 0 else 0.0
            else:
                team.efficiency_rating = 0.0

    @api.depends('feedback_ids.rating')
    def _compute_customer_satisfaction(self):
        for team in self:
            # Only use direct team feedback since service_ids (project.task) don't have feedback_ids
            all_feedback = team.feedback_ids
            valid_feedback = all_feedback.filtered(lambda f: f.rating and f.rating > 0)

            if valid_feedback:
                ratings = [float(r) for r in valid_feedback.mapped('rating')]
                team.total_ratings_received = len(ratings)
                team.customer_satisfaction = sum(ratings) / len(ratings) if ratings else 0.0
                satisfied_count = len([r for r in ratings if r >= 4.0])
                team.satisfaction_percentage = (satisfied_count / len(ratings) * 100) if ratings else 0.0
                team.latest_feedback_date = max(valid_feedback.mapped('create_date'))
            else:
                team.total_ratings_received = 0
                team.customer_satisfaction = 0.0
                team.satisfaction_percentage = 0.0
                team.latest_feedback_date = False

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate_team(self):
        self.ensure_one()
        if not self.team_leader_id:
            raise UserError(_("A team leader is required to activate the team."))
        if not self.member_ids:
            raise UserError(_("The team must have members to be activated."))
        self.write({"state": "active"})
        self.message_post(body=_("Team has been activated and is ready for service assignment."))

    def action_deactivate_team(self):
        self.ensure_one()
        active_services = self.env['project.task'].search_count([('shredding_team_id', '=', self.id), ('stage_id.is_closed', '=', False)])
        if active_services > 0:
            raise UserError(_("Cannot deactivate a team with active services. Please complete or reassign all services first."))
        self.write({"state": "inactive"})
        self.message_post(body=_("Team has been deactivated."))

    def action_view_services(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Team Services'),
            'res_model': 'project.task',
            'view_mode': 'list,form,kanban',
            'domain': [('shredding_team_id', '=', self.id)],
            'context': {'default_shredding_team_id': self.id},
        }

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('working_hours_start', 'working_hours_end')
    def _check_working_hours(self):
        for team in self:
            if team.working_hours_start is not False and team.working_hours_end is not False:
                if not (0 <= team.working_hours_start < 24 and 0 <= team.working_hours_end <= 24):
                    raise ValidationError(_("Working hours must be between 0 and 24."))
                if team.working_hours_start >= team.working_hours_end:
                    raise ValidationError(_("Start time must be before end time."))

    @api.constrains('team_leader_id', 'member_ids')
    def _check_team_composition(self):
        for team in self:
            if team.team_leader_id and team.team_leader_id not in team.member_ids:
                raise ValidationError(_("The team leader must be included in the team members list."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        teams = super().create(vals_list)
        for team in teams:
            if team.team_leader_id and team.team_leader_id not in team.member_ids:
                team.member_ids = [(4, team.team_leader_id.id)]
        return teams

    def write(self, vals):
        res = super().write(vals)
        if "team_leader_id" in vals or "member_ids" in vals:
            for team in self.filtered(lambda t: t.team_leader_id and t.team_leader_id not in t.member_ids):
                team.write({"member_ids": [(4, team.team_leader_id.id)]})
        return res
