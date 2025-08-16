# -*- coding: utf-8 -*-
"""
Pickup Route Management Module

This module provides comprehensive route planning and optimization for pickup operations within
the Records Management System. It implements intelligent route management, GPS tracking, and
operational efficiency optimization for document collection and service delivery operations.

Features:
- Route optimization with GPS tracking
- Driver assignment and vehicle management
- Integration with FSM for field service operations
- Real-time route status tracking
- Cost and time estimation
- Performance analytics and reporting

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PickupRoute(models.Model):
    """
    Pickup Route Management for optimizing pickup schedules and operations.
    
    This model handles the complete lifecycle of pickup routes including planning,
    execution, tracking, and performance analysis. It integrates with FSM for
    field service operations and provides real-time visibility into route status.
    """
    
    _name = "pickup.route"
    _description = "Pickup Route Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "route_date desc, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Route Name", 
        required=True, 
        tracking=True,
        index=True,
        help="Unique route identifier"
    )
    company_id = fields.Many2one(
        "res.company", 
        default=lambda self: self.env.company, 
        required=True
    )
    user_id = fields.Many2one(
        "res.users", 
        default=lambda self: self.env.user, 
        tracking=True,
        string="Created By"
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # ROUTE PLANNING FIELDS
    # ============================================================================
    route_date = fields.Date(
        string="Route Date", 
        required=True, 
        default=fields.Date.today,
        tracking=True,
        index=True
    )
    planned_start_time = fields.Datetime(
        string="Planned Start Time",
        help="When the route is scheduled to begin"
    )
    planned_end_time = fields.Datetime(
        string="Planned End Time", 
        help="When the route is scheduled to complete"
    )
    actual_start_time = fields.Datetime(
        string="Actual Start Time",
        tracking=True
    )
    actual_end_time = fields.Datetime(
        string="Actual End Time",
        tracking=True
    )

    # ============================================================================
    # PERSONNEL AND VEHICLE ASSIGNMENT
    # ============================================================================
    driver_id = fields.Many2one(
        "res.users", 
        string="Driver", 
        required=True,
        tracking=True,
        domain="[('groups_id', 'in', [ref('records_management.group_driver')])]"
    )
    vehicle_id = fields.Many2one(
        "records.vehicle", 
        string="Vehicle", 
        required=True,
        tracking=True
    )
    supervisor_id = fields.Many2one(
        "res.users",
        string="Route Supervisor",
        domain="[('groups_id', 'in', [ref('records_management.group_records_manager')])]",
        help="Supervisor responsible for route oversight"
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ("draft", "Draft"),
        ("planned", "Planned"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ], string="State", default="draft", required=True, tracking=True)

    priority = fields.Selection([
        ("0", "Low"),
        ("1", "Normal"), 
        ("2", "High"),
        ("3", "Critical"),
    ], string="Priority", default="1", tracking=True)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    pickup_request_ids = fields.One2many(
        "pickup.request", 
        "route_id", 
        string="Pickup Requests",
        help="Pickup requests assigned to this route"
    )
    route_stop_ids = fields.One2many(
        "pickup.route.stop",
        "route_id",
        string="Route Stops",
        help="Ordered stops along this route"
    )

    # ============================================================================
    # PERFORMANCE AND METRICS
    # ============================================================================
    total_distance = fields.Float(
        string="Total Distance (km)",
        compute="_compute_route_metrics",
        store=True,
        help="Total planned distance for the route"
    )
    estimated_duration = fields.Float(
        string="Estimated Duration (hours)",
        compute="_compute_route_metrics", 
        store=True
    )
    actual_duration = fields.Float(
        string="Actual Duration (hours)",
        compute="_compute_actual_duration",
        store=True
    )
    fuel_cost = fields.Monetary(
        string="Estimated Fuel Cost",
        currency_field="currency_id",
        compute="_compute_costs",
        store=True
    )
    total_cost = fields.Monetary(
        string="Total Route Cost",
        currency_field="currency_id",
        compute="_compute_costs",
        store=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    request_count = fields.Integer(
        string="Request Count",
        compute="_compute_request_count",
        help="Number of pickup requests on this route"
    )
    completion_percentage = fields.Float(
        string="Completion %",
        compute="_compute_completion_percentage",
        help="Percentage of route completed"
    )
    efficiency_score = fields.Float(
        string="Efficiency Score",
        compute="_compute_efficiency_score", 
        help="Route efficiency rating (0-100)"
    )

    # ============================================================================
    # NOTES AND COMMUNICATION
    # ============================================================================
    notes = fields.Text(string="Route Notes")
    special_instructions = fields.Text(
        string="Special Instructions",
        help="Special handling or route instructions"
    )

    # Mail framework fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    total_weight = fields.Float(string="Total Weight", default=0.0, help="Total weight")
    actual_arrival_time = fields.Char(string="Actual Arrival Time", help="Actual arrival time")
    action_cancel_route = fields.Char(string='Action Cancel Route')
    action_complete_route = fields.Char(string='Action Complete Route')
    action_plan_route = fields.Char(string='Action Plan Route')
    action_start_route = fields.Char(string='Action Start Route')
    action_view_pickup_requests = fields.Char(string='Action View Pickup Requests')
    action_view_route_map = fields.Char(string='Action View Route Map')
    actual_pickup_time = fields.Float(string='Actual Pickup Time', digits=(12, 2))
    audit_trail_complete = fields.Char(string='Audit Trail Complete')
    button_box = fields.Char(string='Button Box')
    certificates_generated = fields.Char(string='Certificates Generated')
    color = fields.Char(string='Color')
    company = fields.Char(string='Company')
    completed = fields.Boolean(string='Completed', default=False)
    container_count = fields.Integer(string='Container Count', compute='_compute_container_count', store=True)
    context = fields.Char(string='Context')
    create_date = fields.Date(string='Create Date')
    current_load = fields.Char(string='Current Load')
    current_location = fields.Char(string='Current Location')
    domain = fields.Char(string='Domain')
    draft = fields.Char(string='Draft')
    driver = fields.Char(string='Driver')
    end_location_id = fields.Many2one('end.location', string='End Location Id')
    estimated_pickup_time = fields.Float(string='Estimated Pickup Time', digits=(12, 2))
    eta_next_stop = fields.Char(string='Eta Next Stop')
    help = fields.Char(string='Help')
    high_priority = fields.Selection([], string='High Priority')  # TODO: Define selection options
    history = fields.Char(string='History')
    in_progress = fields.Char(string='In Progress')
    last_update_time = fields.Float(string='Last Update Time', digits=(12, 2))
    max_capacity = fields.Char(string='Max Capacity')
    my_driving = fields.Char(string='My Driving')
    my_routes = fields.Char(string='My Routes')
    naid_compliance_required = fields.Boolean(string='Naid Compliance Required', default=False)
    naid_required = fields.Boolean(string='Naid Required', default=False)
    overdue = fields.Char(string='Overdue')
    partner_id = fields.Many2one('res.partner', string='Partner Id')
    pickup_address = fields.Char(string='Pickup Address')
    pickup_count = fields.Integer(string='Pickup Count', compute='_compute_pickup_count', store=True)
    pickup_stops = fields.Char(string='Pickup Stops')
    planned = fields.Char(string='Planned')
    res_model = fields.Char(string='Res Model')
    route_details = fields.Char(string='Route Details')
    route_month = fields.Char(string='Route Month')
    route_type = fields.Selection([], string='Route Type')  # TODO: Define selection options
    route_week = fields.Char(string='Route Week')
    signatures_collected = fields.Char(string='Signatures Collected')
    start_location_id = fields.Many2one('start.location', string='Start Location Id')
    this_week = fields.Char(string='This Week')
    today = fields.Char(string='Today')
    total_stops = fields.Char(string='Total Stops')
    tracking = fields.Char(string='Tracking')
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    urgent_priority = fields.Selection([], string='Urgent Priority')  # TODO: Define selection options
    vehicle = fields.Char(string='Vehicle')
    view_mode = fields.Char(string='View Mode')
    web_ribbon = fields.Char(string='Web Ribbon')
    write_date = fields.Date(string='Write Date')

    @api.depends('container_ids')
    def _compute_container_count(self):
        for record in self:
            record.container_count = len(record.container_ids)

    @api.depends('pickup_ids')
    def _compute_pickup_count(self):
        for record in self:
            record.pickup_count = len(record.pickup_ids)

    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies
    def _compute_total_stops(self):
        for record in self:
            record.total_stops = sum(record.line_ids.mapped('amount'))

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("pickup_request_ids")
    def _compute_request_count(self):
        for route in self:
            route.request_count = len(route.pickup_request_ids)

    @api.depends("route_stop_ids", "route_stop_ids.distance")
    def _compute_route_metrics(self):
        for route in self:
            total_distance = sum(route.route_stop_ids.mapped("distance"))
            route.total_distance = total_distance
            
            # Estimate duration based on distance and average speed
            average_speed = 40  # km/hour
            if total_distance > 0:
                route.estimated_duration = total_distance / average_speed
            else:
                route.estimated_duration = 0.0

    @api.depends("actual_start_time", "actual_end_time")
    def _compute_actual_duration(self):
        for route in self:
            if route.actual_start_time and route.actual_end_time:
                delta = route.actual_end_time - route.actual_start_time
                route.actual_duration = delta.total_seconds() / 3600.0  # Convert to hours
            else:
                route.actual_duration = 0.0

    @api.depends("total_distance", "vehicle_id")
    def _compute_costs(self):
        for route in self:
            fuel_cost = 0.0
            if route.total_distance and route.vehicle_id:
                # Example calculation - adjust based on actual vehicle fuel efficiency
                fuel_per_km = 0.08  # 8 liters per 100km = 0.08 L/km
                fuel_price = 1.50   # Price per liter
                fuel_cost = route.total_distance * fuel_per_km * fuel_price
            
            route.fuel_cost = fuel_cost
            route.total_cost = fuel_cost  # Add other costs as needed

    @api.depends("pickup_request_ids", "pickup_request_ids.state")
    def _compute_completion_percentage(self):
        for route in self:
            if not route.pickup_request_ids:
                route.completion_percentage = 0.0
                continue
            
            completed_requests = route.pickup_request_ids.filtered(
                lambda r: r.state in ["completed", "delivered"]
            )
            total_requests = len(route.pickup_request_ids)
            route.completion_percentage = (len(completed_requests) / total_requests) * 100

    @api.depends("actual_duration", "estimated_duration", "completion_percentage")
    def _compute_efficiency_score(self):
        for route in self:
            score = 0.0
            if route.estimated_duration > 0 and route.actual_duration > 0:
                # Time efficiency (50% weight)
                time_efficiency = min(route.estimated_duration / route.actual_duration, 1.0) * 50
                
                # Completion efficiency (50% weight)  
                completion_efficiency = route.completion_percentage * 0.5
                
                score = time_efficiency + completion_efficiency
            
            route.efficiency_score = min(score, 100.0)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_plan_route(self):
        """Plan the route and set to planned state"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Can only plan draft routes"))
        
        if not self.pickup_request_ids:
            raise UserError(_("Cannot plan route without pickup requests"))
        
        # Auto-generate route stops based on pickup requests
        self._generate_route_stops()
        
        self.write({"state": "planned"})
        self.message_post(body=_("Route planned with %d stops", len(self.route_stop_ids)))

    def action_start_route(self):
        """Start route execution"""
        self.ensure_one()
        if self.state != "planned":
            raise UserError(_("Can only start planned routes"))
        
        self.write({
            "state": "in_progress",
            "actual_start_time": fields.Datetime.now()
        })
        self.message_post(body=_("Route started by %s", self.env.user.name))

    def action_complete_route(self):
        """Complete the route"""
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Can only complete routes in progress"))
        
        # Check if all requests are completed
        incomplete_requests = self.pickup_request_ids.filtered(
            lambda r: r.state not in ["completed", "delivered", "cancelled"]
        )
        if incomplete_requests:
            raise UserError(_(
                "Cannot complete route with incomplete requests: %s",
                ", ".join(incomplete_requests.mapped("name"))
            ))
        
        self.write({
            "state": "completed",
            "actual_end_time": fields.Datetime.now()
        })
        self.message_post(body=_("Route completed"))

    def action_cancel_route(self):
        """Cancel the route"""
        self.ensure_one()
        if self.state in ["completed"]:
            raise UserError(_("Cannot cancel completed routes"))
        
        self.write({"state": "cancelled"})
        self.message_post(body=_("Route cancelled"))

    def action_view_pickup_requests(self):
        """View pickup requests for this route"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Pickup Requests - Route %s", self.name),
            "res_model": "pickup.request",
            "view_mode": "tree,form",
            "domain": [("route_id", "=", self.id)],
            "context": {"default_route_id": self.id}
        }

    def action_optimize_route(self):
        """Optimize route order for efficiency"""
        self.ensure_one()
        if not self.route_stop_ids:
            raise UserError(_("No route stops to optimize"))
        
        # Simple optimization - order by geographic proximity
        # In a real implementation, you might use a more sophisticated algorithm
        self._optimize_stop_order()
        self.message_post(body=_("Route optimized"))

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def _generate_route_stops(self):
        """Generate route stops based on pickup requests"""
        self.ensure_one()
        
        # Clear existing stops
        self.route_stop_ids.unlink()
        
        stop_vals = []
        sequence = 10
        for request in self.pickup_request_ids:
            stop_vals.append({
                "route_id": self.id,
                "sequence": sequence,
                "partner_id": request.partner_id.id,
                "pickup_request_id": request.id,
                "planned_arrival": request.pickup_date,
                "address": request.pickup_address or request.partner_id.contact_address,
                "notes": request.notes
            })
            sequence += 10
        
        if stop_vals:
            self.env["pickup.route.stop"].create(stop_vals)

    def _optimize_stop_order(self):
        """Optimize the order of route stops"""
        self.ensure_one()
        # This is a simplified optimization
        # In practice, you might use geographic coordinates and routing algorithms
        
        stops = self.route_stop_ids.sorted(lambda s: s.partner_id.name)
        sequence = 10
        for stop in stops:
            stop.sequence = sequence
            sequence += 10

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("planned_start_time", "planned_end_time")
    def _check_planned_times(self):
        for route in self:
            if route.planned_start_time and route.planned_end_time:
                if route.planned_start_time >= route.planned_end_time:
                    raise ValidationError(_("Planned end time must be after start time"))

    @api.constrains("actual_start_time", "actual_end_time")
    def _check_actual_times(self):
        for route in self:
            if route.actual_start_time and route.actual_end_time:
                if route.actual_start_time >= route.actual_end_time:
                    raise ValidationError(_("Actual end time must be after start time"))

    @api.constrains("pickup_request_ids")
    def _check_pickup_requests_same_date(self):
        for route in self:
            if route.pickup_request_ids:
                request_dates = route.pickup_request_ids.mapped("pickup_date")
                if len(set(request_dates)) > 1:
                    raise ValidationError(_(
                        "All pickup requests on a route must have the same pickup date"
                    ))

    # ============================================================================
    # OVERRIDE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("pickup.route") or "New"
        return super().create(vals_list)
