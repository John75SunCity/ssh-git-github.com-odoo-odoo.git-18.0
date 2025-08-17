from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError


class PickupRoute(models.Model):
    _name = 'pickup.route'
    _description = 'Pickup Route Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'route_date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    route_date = fields.Date()
    planned_start_time = fields.Datetime()
    planned_end_time = fields.Datetime()
    actual_start_time = fields.Datetime()
    actual_end_time = fields.Datetime()
    driver_id = fields.Many2one()
    vehicle_id = fields.Many2one()
    supervisor_id = fields.Many2one()
    state = fields.Selection()
    priority = fields.Selection()
    pickup_request_ids = fields.One2many()
    route_stop_ids = fields.One2many()
    total_distance = fields.Float()
    estimated_duration = fields.Float()
    actual_duration = fields.Float()
    fuel_cost = fields.Monetary()
    total_cost = fields.Monetary()
    currency_id = fields.Many2one()
    request_count = fields.Integer()
    completion_percentage = fields.Float()
    efficiency_score = fields.Float()
    notes = fields.Text(string='Route Notes')
    special_instructions = fields.Text()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    total_weight = fields.Float(string='Total Weight')
    actual_arrival_time = fields.Char(string='Actual Arrival Time')
    action_cancel_route = fields.Char(string='Action Cancel Route')
    action_complete_route = fields.Char(string='Action Complete Route')
    action_plan_route = fields.Char(string='Action Plan Route')
    action_start_route = fields.Char(string='Action Start Route')
    action_view_pickup_requests = fields.Char(string='Action View Pickup Requests')
    action_view_route_map = fields.Char(string='Action View Route Map')
    actual_pickup_time = fields.Float(string='Actual Pickup Time')
    audit_trail_complete = fields.Char(string='Audit Trail Complete')
    button_box = fields.Char(string='Button Box')
    certificates_generated = fields.Char(string='Certificates Generated')
    color = fields.Char(string='Color')
    company = fields.Char(string='Company')
    completed = fields.Boolean(string='Completed')
    container_count = fields.Integer(string='Container Count')
    context = fields.Char(string='Context')
    create_date = fields.Date(string='Create Date')
    current_load = fields.Char(string='Current Load')
    current_location = fields.Char(string='Current Location')
    domain = fields.Char(string='Domain')
    draft = fields.Char(string='Draft')
    driver = fields.Char(string='Driver')
    end_location_id = fields.Many2one('end.location')
    estimated_pickup_time = fields.Float(string='Estimated Pickup Time')
    eta_next_stop = fields.Char(string='Eta Next Stop')
    help = fields.Char(string='Help')
    high_priority = fields.Selection(string='High Priority')
    history = fields.Char(string='History')
    in_progress = fields.Char(string='In Progress')
    last_update_time = fields.Float(string='Last Update Time')
    max_capacity = fields.Char(string='Max Capacity')
    my_driving = fields.Char(string='My Driving')
    my_routes = fields.Char(string='My Routes')
    naid_compliance_required = fields.Boolean(string='Naid Compliance Required')
    naid_required = fields.Boolean(string='Naid Required')
    overdue = fields.Char(string='Overdue')
    partner_id = fields.Many2one('res.partner')
    pickup_address = fields.Char(string='Pickup Address')
    pickup_count = fields.Integer(string='Pickup Count')
    pickup_stops = fields.Char(string='Pickup Stops')
    planned = fields.Char(string='Planned')
    res_model = fields.Char(string='Res Model')
    route_details = fields.Char(string='Route Details')
    route_month = fields.Char(string='Route Month')
    route_type = fields.Selection(string='Route Type')
    route_week = fields.Char(string='Route Week')
    signatures_collected = fields.Char(string='Signatures Collected')
    start_location_id = fields.Many2one('start.location')
    this_week = fields.Char(string='This Week')
    today = fields.Char(string='Today')
    total_stops = fields.Char(string='Total Stops')
    tracking = fields.Char(string='Tracking')
    type = fields.Selection(string='Type')
    urgent_priority = fields.Selection(string='Urgent Priority')
    vehicle = fields.Char(string='Vehicle')
    view_mode = fields.Char(string='View Mode')
    web_ribbon = fields.Char(string='Web Ribbon')
    write_date = fields.Date(string='Write Date')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_container_count(self):
            for record in self:""
                record.container_count = len(record.container_ids)""

    def _compute_pickup_count(self):
            for record in self:""
                record.pickup_count = len(record.pickup_ids)""

    def _compute_total_stops(self):
            for record in self:""
                record.total_stops = sum(record.line_ids.mapped('amount'))""

    def _compute_request_count(self):
            for route in self:""
                route.request_count = len(route.pickup_request_ids)""

    def _compute_route_metrics(self):
            for route in self:""
                total_distance = sum(route.route_stop_ids.mapped("distance"))
                route.total_distance = total_distance""
                ""
                # Estimate duration based on distance and average speed""
                average_speed = 40  # km/hour""
                if total_distance > 0:""
                    route.estimated_duration = total_distance / average_speed""
                else:""
                    route.estimated_duration = 0.0""

    def _compute_actual_duration(self):
            for route in self:""
                if route.actual_start_time and route.actual_end_time:""
                    delta = route.actual_end_time - route.actual_start_time""
                    route.actual_duration = delta.total_seconds() / 3600.0  # Convert to hours""
                else:""
                    route.actual_duration = 0.0""

    def _compute_costs(self):
            for route in self:""
                fuel_cost = 0.0""
                if route.total_distance and route.vehicle_id:""
                    # Example calculation - adjust based on actual vehicle fuel efficiency""
                    fuel_per_km = 0.8  # 8 liters per 100km = 0.8 L/km""
                    fuel_price = 1.50   # Price per liter""
                    fuel_cost = route.total_distance * fuel_per_km * fuel_price""
                ""
                route.fuel_cost = fuel_cost""
                route.total_cost = fuel_cost  # Add other costs as needed""

    def _compute_completion_percentage(self):
            for route in self:""
                if not route.pickup_request_ids:""
                    route.completion_percentage = 0.0""
                    continue""
                ""
                completed_requests = route.pickup_request_ids.filtered()""
                    lambda r: r.state in ["completed", "delivered"]
                ""
                total_requests = len(route.pickup_request_ids)""
                route.completion_percentage = (len(completed_requests) / total_requests) * 100""

    def _compute_efficiency_score(self):
            for route in self:""
                score = 0.0""
                if route.estimated_duration > 0 and route.actual_duration > 0:""
                    # Time efficiency (50% weight)""
                    time_efficiency = min(route.estimated_duration / route.actual_duration, 1.0) * 50""
                    ""
                    # Completion efficiency (50% weight)  ""
                    completion_efficiency = route.completion_percentage * 0.5""
                    ""
                    score = time_efficiency + completion_efficiency""
                ""
                route.efficiency_score = min(score, 100.0)""

    def action_plan_route(self):
            """Plan the route and set to planned state"""
            if self.state != "draft":
                raise UserError(_("Can only plan draft routes"))
            ""
            if not self.pickup_request_ids:""
                raise UserError(_("Cannot plan route without pickup requests"))
            ""
            # Auto-generate route stops based on pickup requests""
            self._generate_route_stops()""
            ""
            self.write({"state": "planned"})
            self.message_post(body=_("Route planned with %d stops", len(self.route_stop_ids)))

    def action_start_route(self):
            """Start route execution"""
            if self.state != "planned":
                raise UserError(_("Can only start planned routes"))
            ""
            self.write({)}""
                "state": "in_progress",
                "actual_start_time": fields.Datetime.now()
            ""
            self.message_post(body=_("Route started by %s", self.env.user.name))

    def action_complete_route(self):
            """Complete the route"""
            if self.state != "in_progress":
                raise UserError(_("Can only complete routes in progress"))
            ""
            # Check if all requests are completed:""
            incomplete_requests = self.pickup_request_ids.filtered()""
                lambda r: r.state not in ["completed", "delivered", "cancelled"]
            ""
            if incomplete_requests:""
                raise UserError(_())""
                    "Cannot complete route with incomplete requests: %s",
                    ", ".join(incomplete_requests.mapped("name"))
                ""
            ""
            self.write({)}""
                "state": "completed",
                "actual_end_time": fields.Datetime.now()
            ""
            self.message_post(body=_("Route completed"))

    def action_cancel_route(self):
            """Cancel the route"""
            if self.state in ["completed"]:
                raise UserError(_("Cannot cancel completed routes"))
            ""
            self.write({"state": "cancelled"})
            self.message_post(body=_("Route cancelled"))

    def action_view_pickup_requests(self):
            """View pickup requests for this route""":

    def action_optimize_route(self):
            """Optimize route order for efficiency""":

    def _generate_route_stops(self):
            """Generate route stops based on pickup requests"""

    def _optimize_stop_order(self):
            """Optimize the order of route stops"""

    def _check_actual_times(self):
            for route in self:""
                if route.actual_start_time and route.actual_end_time:""
                    if route.actual_start_time >= route.actual_end_time:""
                        raise ValidationError(_("Actual end time must be after start time"))

    def _check_pickup_requests_same_date(self):
            for route in self:""
                if route.pickup_request_ids:""
                    request_dates = route.pickup_request_ids.mapped("pickup_date")
                    if len(set(request_dates)) > 1:""
                        raise ValidationError(_())""
                            "All pickup requests on a route must have the same pickup date"
                        ""

    def create(self, vals_list):
            for vals in vals_list:""
                if vals.get("name", "New") == "New":
                    vals["name"] = self.env["ir.sequence"].next_by_code("pickup.route") or "New"
            return super().create(vals_list)""
