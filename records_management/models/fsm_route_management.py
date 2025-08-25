from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FsmRouteManagement(models.Model):
    _name = 'fsm.route.management'
    _description = 'FSM Route Management - Central Hub'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, priority desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Route Name", required=True, index=True, copy=False, default=lambda self: _('New'))
    sequence = fields.Integer(string="Sequence", default=10)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    scheduled_date = fields.Date(string="Scheduled Date", required=True, index=True)
    start_time = fields.Float(string="Scheduled Start Time")
    end_time = fields.Float(string="Scheduled End Time")
    estimated_duration = fields.Float(string="Estimated Duration (Hours)", compute='_compute_estimated_duration', store=True)

    actual_start_time = fields.Datetime(string="Actual Start Time", readonly=True)
    actual_end_time = fields.Datetime(string="Actual End Time", readonly=True)

    driver_id = fields.Many2one('res.users', string="Driver", domain="[('share', '=', False)]")
    vehicle_id = fields.Many2one('maintenance.equipment', string="Vehicle", domain="[('category_id.name', '=', 'Vehicles')]")
    backup_driver_id = fields.Many2one('res.users', string="Backup Driver")

    route_type = fields.Selection([
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
        ('mixed', 'Mixed')
    ], string="Route Type", default='pickup')

    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')], string='Priority', default='1')

    total_stops = fields.Integer(string="Total Stops", compute='_compute_route_stats', store=True)
    total_distance = fields.Float(string="Total Distance (km/mi)")
    total_containers = fields.Integer(string="Total Containers", compute='_compute_route_stats', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('optimized', 'Optimized'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft', tracking=True)

    pickup_request_ids = fields.One2many('pickup.request', 'route_id', string="Pickup Requests")

    # Configuration
    max_stops_per_route = fields.Integer(string="Max Stops", default=50)
    max_driving_hours = fields.Float(string="Max Driving Hours", default=8.0)
    # Use existing geographic areas model; no custom fsm.service.area model exists
    service_area_ids = fields.Many2many('res.country.state', string="Service Areas")

    route_notes = fields.Text(string="Internal Notes")
    customer_instructions = fields.Text(string="Instructions for Customers")

    # Analytics
    completion_rate = fields.Float(string="Completion Rate (%)", compute='_compute_performance_metrics', store=True)
    on_time_rate = fields.Float(string="On-Time Rate (%)", compute='_compute_performance_metrics', store=True)
    fuel_cost = fields.Monetary(string="Fuel Cost")
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('start_time', 'end_time')
    def _compute_estimated_duration(self):
        for record in self:
            if record.start_time and record.end_time and record.end_time > record.start_time:
                record.estimated_duration = record.end_time - record.start_time
            else:
                record.estimated_duration = 0.0

    @api.depends('pickup_request_ids', 'pickup_request_ids.state', 'pickup_request_ids.container_count')
    def _compute_route_stats(self):
        for record in self:
            requests = record.pickup_request_ids
            record.total_stops = len(requests)
            record.total_containers = sum(req.container_count for req in requests)
            # Distance calculation would integrate with a mapping service

    @api.depends('pickup_request_ids', 'pickup_request_ids.state')
    def _compute_performance_metrics(self):
        for record in self:
            requests = record.pickup_request_ids
            if not requests:
                record.completion_rate = 0.0
                record.on_time_rate = 0.0
                continue

            completed = requests.filtered(lambda r: r.state == "completed")
            record.completion_rate = (len(completed) / len(requests)) * 100 if requests else 0.0
            # On-time calculation would need time tracking on pickup requests
            record.on_time_rate = 100.0  # Placeholder

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("fsm.route.management") or _("New Route")
        return super().create(vals_list)

    def write(self, vals):
        if "state" in vals:
            for record in self:
                if vals["state"] != record.state:
                    old_state = dict(record._fields["state"].selection).get(record.state, record.state)
                    new_state = dict(record._fields["state"].selection).get(vals["state"], vals["state"])
                    record.message_post(body=_("Route status changed from %s to %s", old_state, new_state))
        return super().write(vals)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_route(self):
        self.ensure_one()
        if not self.driver_id:
            raise UserError(_("Cannot start route without an assigned driver."))
        if not self.vehicle_id:
            raise UserError(_("Cannot start route without an assigned vehicle."))
        self.write({
            "state": "in_progress",
            "actual_start_time": fields.Datetime.now()
        })
        self.pickup_request_ids.write({"state": "in_progress"})
        self.message_post(body=_("Route started by %s at %s", self.driver_id.name, fields.Datetime.now()))

    def action_complete_route(self):
        self.ensure_one()
        self.write({
            "state": "completed",
            "actual_end_time": fields.Datetime.now()
        })
        completed_pickups = self.pickup_request_ids.filtered(lambda r: r.state == "completed")
        self.message_post(body=_("%s out of %s pickups successful", len(completed_pickups), len(self.pickup_request_ids)))

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _get_next_business_day(self, current_date):
        """Get next business day (Monday-Friday)"""
        next_date = current_date + timedelta(days=1)
        while next_date.weekday() > 4:  # Saturday=5, Sunday=6
            next_date += timedelta(days=1)
        return next_date

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('start_time', 'end_time')
    def _check_time_logic(self):
        for record in self:
            if record.start_time and record.end_time and record.start_time >= record.end_time:
                raise ValidationError(_("Start time must be before end time."))

    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        for record in self:
            if record.scheduled_date and record.scheduled_date < fields.Date.today():
                raise ValidationError(_("Cannot schedule routes in the past."))

    @api.constrains('pickup_request_ids')
    def _check_max_stops(self):
        for record in self:
            if len(record.pickup_request_ids) > record.max_stops_per_route:
                raise ValidationError(
                    _("Route exceeds maximum stops limit (%s/%s)",
                    len(record.pickup_request_ids), record.max_stops_per_route)
                )

