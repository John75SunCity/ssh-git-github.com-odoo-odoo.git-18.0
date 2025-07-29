# -*- coding: utf-8 -*-
"""
Pickup Route Management System
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
from datetime import datetime, timedelta
import json

_logger = logging.getLogger(__name__)


class PickupRoute(models.Model):
    """
    Pickup Route Management
    Manages pickup routes for document collection and delivery services
    """

    _name = "pickup.route"
    _description = "Pickup Route"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "route_date desc, sequence, name"
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(
        string="Route Name",
        required=True,
        tracking=True,
        default=lambda self: _("New"),
        copy=False,
    )
    description = fields.Text(string="Route Description", tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Route Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)

    # ==========================================
    # ROUTE SCHEDULING
    # ==========================================
    route_date = fields.Date(
        string="Route Date", required=True, default=fields.Date.today, tracking=True
    )
    start_time = fields.Datetime(string="Planned Start Time", tracking=True)
    end_time = fields.Datetime(string="Planned End Time", tracking=True)
    actual_start_time = fields.Datetime(string="Actual Start Time")
    actual_end_time = fields.Datetime(string="Actual End Time")

    sequence = fields.Integer(
        string="Route Sequence", default=10, help="Order of routes for the same date"
    )

    # ==========================================
    # ROUTE TYPE AND PRIORITY
    # ==========================================
    route_type = fields.Selection(
        [
            ("pickup", "Document Pickup"),
            ("delivery", "Document Delivery"),
            ("mixed", "Pickup & Delivery"),
            ("emergency", "Emergency Service"),
            ("maintenance", "Equipment Maintenance"),
        ],
        string="Route Type",
        default="pickup",
        required=True,
        tracking=True,
    )

    priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Urgent")],
        string="Priority",
        default="1",
        tracking=True,
    )

    # ==========================================
    # VEHICLE AND DRIVER ASSIGNMENT
    # ==========================================
    vehicle_id = fields.Many2one(
        "records.vehicle", string="Assigned Vehicle", tracking=True
    )
    driver_id = fields.Many2one("res.users", string="Primary Driver", tracking=True)
    co_driver_id = fields.Many2one("res.users", string="Co-Driver", tracking=True)

    # Vehicle capacity tracking
    vehicle_capacity_weight = fields.Float(
        string="Vehicle Weight Capacity (lbs)",
        related="vehicle_id.vehicle_capacity_weight",
        readonly=True,
    )
    vehicle_capacity_volume = fields.Float(
        string="Vehicle Volume Capacity (ft³)",
        related="vehicle_id.vehicle_capacity_volume",
        readonly=True,
    )

    # ==========================================
    # ROUTE STATUS
    # ==========================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("planned", "Planned"),
            ("assigned", "Assigned"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        required=True,
    )

    # ==========================================
    # ROUTE STOPS
    # ==========================================
    route_stop_ids = fields.One2many(
        "pickup.route.stop", "route_id", string="Route Stops"
    )
    stop_count = fields.Integer(
        string="Number of Stops", compute="_compute_route_metrics", store=True
    )

    # ==========================================
    # ROUTE METRICS
    # ==========================================
    total_distance = fields.Float(
        string="Total Distance (miles)", compute="_compute_route_metrics", store=True
    )
    estimated_duration = fields.Float(
        string="Estimated Duration (hours)",
        compute="_compute_route_metrics",
        store=True,
    )
    actual_duration = fields.Float(
        string="Actual Duration (hours)", compute="_compute_actual_duration", store=True
    )

    # Load tracking
    total_containers = fields.Integer(
        string="Total Containers", compute="_compute_load_metrics", store=True
    )
    total_weight = fields.Float(
        string="Total Weight (lbs)", compute="_compute_load_metrics", store=True
    )
    total_volume = fields.Float(
        string="Total Volume (ft³)", compute="_compute_load_metrics", store=True
    )

    # Utilization percentages
    weight_utilization = fields.Float(
        string="Weight Utilization %", compute="_compute_utilization", store=True
    )
    volume_utilization = fields.Float(
        string="Volume Utilization %", compute="_compute_utilization", store=True
    )

    # ==========================================
    # ROUTE OPTIMIZATION
    # ==========================================
    optimization_enabled = fields.Boolean(
        string="Route Optimization Enabled", default=True
    )
    optimized = fields.Boolean(string="Route Optimized", default=False)
    optimization_notes = fields.Text(string="Optimization Notes")

    # GPS tracking
    gps_tracking_enabled = fields.Boolean(string="GPS Tracking Enabled", default=True)
    current_location = fields.Char(string="Current Location")
    gps_coordinates = fields.Char(string="GPS Coordinates")

    # ==========================================
    # DOCUMENTATION AND COMPLIANCE
    # ==========================================
    driver_signature = fields.Binary(string="Driver Signature")
    supervisor_signature = fields.Binary(string="Supervisor Signature")
    route_notes = fields.Text(string="Route Notes")

    # Fuel and expenses
    fuel_cost = fields.Float(string="Fuel Cost", digits="Product Price")
    other_expenses = fields.Float(string="Other Expenses", digits="Product Price")
    total_expenses = fields.Float(
        string="Total Expenses", compute="_compute_total_expenses", store=True
    )

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================

    @api.depends("route_stop_ids", "route_stop_ids.distance_to_next")
    def _compute_route_metrics(self):
        """Compute route distance, duration and stop count"""
        for route in self:
            route.stop_count = len(route.route_stop_ids)
            route.total_distance = sum(route.route_stop_ids.mapped("distance_to_next"))
            # Estimate 45 minutes per stop + driving time at 30 mph average
            route.estimated_duration = (route.stop_count * 0.75) + (
                route.total_distance / 30.0
            )

    @api.depends("actual_start_time", "actual_end_time")
    def _compute_actual_duration(self):
        """Compute actual route duration"""
        for route in self:
            if route.actual_start_time and route.actual_end_time:
                delta = route.actual_end_time - route.actual_start_time
                route.actual_duration = (
                    delta.total_seconds() / 3600.0
                )  # Convert to hours
            else:
                route.actual_duration = 0.0

    @api.depends(
        "route_stop_ids",
        "route_stop_ids.container_count",
        "route_stop_ids.estimated_weight",
        "route_stop_ids.estimated_volume",
    )
    def _compute_load_metrics(self):
        """Compute total load metrics"""
        for route in self:
            route.total_containers = sum(route.route_stop_ids.mapped("container_count"))
            route.total_weight = sum(route.route_stop_ids.mapped("estimated_weight"))
            route.total_volume = sum(route.route_stop_ids.mapped("estimated_volume"))

    @api.depends(
        "total_weight",
        "total_volume",
        "vehicle_capacity_weight",
        "vehicle_capacity_volume",
    )
    def _compute_utilization(self):
        """Compute vehicle utilization percentages"""
        for route in self:
            if route.vehicle_capacity_weight > 0:
                route.weight_utilization = (
                    route.total_weight / route.vehicle_capacity_weight
                ) * 100
            else:
                route.weight_utilization = 0.0

            if route.vehicle_capacity_volume > 0:
                route.volume_utilization = (
                    route.total_volume / route.vehicle_capacity_volume
                ) * 100
            else:
                route.volume_utilization = 0.0

    @api.depends("fuel_cost", "other_expenses")
    def _compute_total_expenses(self):
        """Compute total route expenses"""
        for route in self:
            route.total_expenses = route.fuel_cost + route.other_expenses

    # ==========================================
    # CRUD METHODS
    # ==========================================

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence number"""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                sequence = self.env["ir.sequence"].next_by_code("pickup.route")
                vals["name"] = sequence or _("New")
        return super().create(vals_list)

    # ==========================================
    # WORKFLOW ACTIONS
    # ==========================================

    def action_plan_route(self):
        """Plan the route"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft routes can be planned"))

        if not self.route_stop_ids:
            raise UserError(_("Please add at least one stop to the route"))

        self.write({"state": "planned"})
        self.message_post(body=_("Route planned"))

    def action_assign_vehicle(self):
        """Assign vehicle and driver to route"""
        self.ensure_one()
        if self.state != "planned":
            raise UserError(_("Only planned routes can be assigned"))

        if not self.vehicle_id:
            raise UserError(_("Please assign a vehicle"))

        if not self.driver_id:
            raise UserError(_("Please assign a driver"))

        # Check vehicle capacity
        if self.weight_utilization > 100:
            raise UserError(_("Route exceeds vehicle weight capacity"))

        if self.volume_utilization > 100:
            raise UserError(_("Route exceeds vehicle volume capacity"))

        self.write({"state": "assigned"})
        self.message_post(
            body=_("Route assigned to vehicle %s and driver %s")
            % (self.vehicle_id.name, self.driver_id.name)
        )

    def action_start_route(self):
        """Start route execution"""
        self.ensure_one()
        if self.state != "assigned":
            raise UserError(_("Only assigned routes can be started"))

        self.write({"state": "in_progress", "actual_start_time": fields.Datetime.now()})
        self.message_post(body=_("Route started"))

    def action_complete_route(self):
        """Complete route execution"""
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Only routes in progress can be completed"))

        # Check if all stops are completed
        incomplete_stops = self.route_stop_ids.filtered(
            lambda s: s.status != "completed"
        )
        if incomplete_stops:
            raise UserError(_("All stops must be completed before finishing route"))

        self.write({"state": "completed", "actual_end_time": fields.Datetime.now()})
        self.message_post(body=_("Route completed"))

    def action_optimize_route(self):
        """Optimize route stop order"""
        self.ensure_one()
        if self.state not in ["draft", "planned"]:
            raise UserError(_("Only draft or planned routes can be optimized"))

        if not self.optimization_enabled:
            raise UserError(_("Route optimization is disabled"))

        # Simple optimization: sort by priority, then by distance from depot
        # In a real implementation, this would use a sophisticated routing algorithm
        stops = self.route_stop_ids.sorted(key=lambda s: (s.priority, s.sequence))

        for i, stop in enumerate(stops):
            stop.sequence = (i + 1) * 10

        self.write(
            {
                "optimized": True,
                "optimization_notes": f"Route optimized on {fields.Datetime.now()}",
            }
        )
        self.message_post(body=_("Route optimized"))

    def action_cancel(self):
        """Cancel route"""
        self.ensure_one()
        if self.state in ["completed"]:
            raise UserError(_("Cannot cancel completed routes"))

        self.write({"state": "cancelled"})
        self.message_post(body=_("Route cancelled"))

    # ==========================================
    # UTILITY METHODS
    # ==========================================

    def get_route_summary(self):
        """Get route summary for reporting"""
        self.ensure_one()

        return {
            "name": self.name,
            "date": self.route_date,
            "type": dict(self._fields["route_type"].selection)[self.route_type],
            "driver": self.driver_id.name if self.driver_id else "Unassigned",
            "vehicle": self.vehicle_id.name if self.vehicle_id else "Unassigned",
            "stops": self.stop_count,
            "distance": self.total_distance,
            "duration": self.estimated_duration,
            "status": dict(self._fields["state"].selection)[self.state],
        }

    def get_efficiency_metrics(self):
        """Get route efficiency metrics"""
        self.ensure_one()

        metrics = {
            "weight_utilization": self.weight_utilization,
            "volume_utilization": self.volume_utilization,
            "stops_per_hour": (
                self.stop_count / self.estimated_duration
                if self.estimated_duration > 0
                else 0
            ),
            "miles_per_stop": (
                self.total_distance / self.stop_count if self.stop_count > 0 else 0
            ),
        }

        if self.actual_duration > 0:
            metrics.update(
                {
                    "actual_stops_per_hour": self.stop_count / self.actual_duration,
                    "schedule_variance": (
                        (self.actual_duration - self.estimated_duration)
                        / self.estimated_duration
                    )
                    * 100,
                }
            )

        return metrics

    # ==========================================
    # VALIDATION
    # ==========================================

    @api.constrains("start_time", "end_time")
    def _check_times(self):
        """Validate start and end times"""
        for route in self:
            if route.start_time and route.end_time:
                if route.end_time <= route.start_time:
                    raise ValidationError(_("End time must be after start time"))

    @api.constrains("route_stop_ids")
    def _check_stops(self):
        """Validate route stops"""
        for route in self:
            if route.route_stop_ids:
                sequences = route.route_stop_ids.mapped("sequence")
                if len(sequences) != len(set(sequences)):
                    raise ValidationError(
                        _("Stop sequences must be unique within a route")
                    )


# ==========================================
# ROUTE STOP MODEL
# ==========================================
class PickupRouteStop(models.Model):
    """
    Individual stops in a pickup route
    """

    _name = "pickup.route.stop"
    _description = "Pickup Route Stop"
    _order = "route_id, sequence, id"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    route_id = fields.Many2one(
        "pickup.route", string="Route", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(string="Stop Sequence", default=10)
    name = fields.Char(string="Stop Name", required=True)

    # ==========================================
    # LOCATION INFORMATION
    # ==========================================
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)
    contact_id = fields.Many2one("res.partner", string="Contact Person")

    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    city = fields.Char(string="City")
    state_id = fields.Many2one("res.country.state", string="State")
    zip = fields.Char(string="ZIP Code")
    country_id = fields.Many2one("res.country", string="Country")

    # Coordinates for optimization
    latitude = fields.Float(string="Latitude", digits=(10, 7))
    longitude = fields.Float(string="Longitude", digits=(10, 7))

    # ==========================================
    # STOP DETAILS
    # ==========================================
    stop_type = fields.Selection(
        [
            ("pickup", "Pickup"),
            ("delivery", "Delivery"),
            ("service", "Service Call"),
            ("inspection", "Inspection"),
        ],
        string="Stop Type",
        required=True,
        default="pickup",
    )

    priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Urgent")],
        string="Priority",
        default="1",
    )

    # ==========================================
    # SCHEDULING
    # ==========================================
    planned_arrival_time = fields.Datetime(string="Planned Arrival")
    planned_departure_time = fields.Datetime(string="Planned Departure")
    actual_arrival_time = fields.Datetime(string="Actual Arrival")
    actual_departure_time = fields.Datetime(string="Actual Departure")

    estimated_duration = fields.Float(string="Estimated Duration (minutes)", default=30)
    actual_duration = fields.Float(
        string="Actual Duration (minutes)",
        compute="_compute_actual_duration",
        store=True,
    )

    # ==========================================
    # LOAD INFORMATION
    # ==========================================
    container_count = fields.Integer(string="Container Count", default=0)
    estimated_weight = fields.Float(string="Estimated Weight (lbs)", default=0.0)
    estimated_volume = fields.Float(string="Estimated Volume (ft³)", default=0.0)

    # ==========================================
    # DISTANCE AND ROUTING
    # ==========================================
    distance_from_previous = fields.Float(string="Distance from Previous Stop (miles)")
    distance_to_next = fields.Float(string="Distance to Next Stop (miles)")
    driving_time_to_next = fields.Float(string="Driving Time to Next Stop (minutes)")

    # ==========================================
    # STATUS AND COMPLETION
    # ==========================================
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("en_route", "En Route"),
            ("arrived", "Arrived"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("skipped", "Skipped"),
        ],
        string="Status",
        default="pending",
    )

    completion_notes = fields.Text(string="Completion Notes")
    customer_signature = fields.Binary(string="Customer Signature")
    driver_signature = fields.Binary(string="Driver Signature")

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================

    @api.depends("actual_arrival_time", "actual_departure_time")
    def _compute_actual_duration(self):
        """Compute actual duration at stop"""
        for stop in self:
            if stop.actual_arrival_time and stop.actual_departure_time:
                delta = stop.actual_departure_time - stop.actual_arrival_time
                stop.actual_duration = (
                    delta.total_seconds() / 60.0
                )  # Convert to minutes
            else:
                stop.actual_duration = 0.0

    # ==========================================
    # ACTIONS
    # ==========================================

    def action_mark_arrived(self):
        """Mark stop as arrived"""
        self.write({"status": "arrived", "actual_arrival_time": fields.Datetime.now()})

    def action_start_service(self):
        """Start service at stop"""
        self.write({"status": "in_progress"})

    def action_complete_stop(self):
        """Complete stop"""
        self.write(
            {"status": "completed", "actual_departure_time": fields.Datetime.now()}
        )

    def action_skip_stop(self):
        """Skip stop (with reason in notes)"""
        self.write({"status": "skipped"})

    def action_mark_failed(self):
        """Mark stop as failed"""
        self.write({"status": "failed"})

    # ==========================================
    # UTILITY METHODS
    # ==========================================

    def get_full_address(self):
        """Get formatted full address"""
        self.ensure_one()
        address_parts = [
            self.street,
            self.street2,
            self.city,
            self.state_id.name if self.state_id else None,
            self.zip,
            self.country_id.name if self.country_id else None,
        ]
        return ", ".join(filter(None, address_parts))

    # ==========================================
    # VALIDATION
    # ==========================================

    @api.constrains("planned_arrival_time", "planned_departure_time")
    def _check_planned_times(self):
        """Validate planned times"""
        for stop in self:
            if stop.planned_arrival_time and stop.planned_departure_time:
                if stop.planned_departure_time <= stop.planned_arrival_time:
                    raise ValidationError(
                        _("Planned departure must be after planned arrival")
                    )
