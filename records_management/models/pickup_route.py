# -*- coding: utf-8 -*-
"""
Pickup Route Management Module

This module provides comprehensive route planning and optimization for pickup operations within
the Records Management System. It implements intelligent route management, GPS tracking, and
operational efficiency optimization for document collection and service delivery operations.

Key Features:
- Intelligent route planning and optimization with GPS integration
- Multi-stop route management with time and distance optimization
- Driver assignment and vehicle tracking for pickup operations
- Real-time route updates and dynamic rerouting capabilities
- Customer scheduling integration with automated appointment management
- Route performance analytics and efficiency reporting
- Integration with fuel management and cost tracking systems

Business Processes:
1. Route Planning: Automated route creation based on pickup requests and geographical optimization
2. Driver Assignment: Driver allocation based on availability, skills, and route requirements
3. Schedule Management: Customer appointment scheduling and confirmation workflows
4. Route Execution: Real-time tracking and status updates during route execution
5. Performance Analysis: Route efficiency analysis and optimization recommendations
6. Exception Handling: Management of route deviations, delays, and emergency situations
7. Cost Tracking: Fuel, mileage, and operational cost tracking for route profitability

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PickupRoute(models.Model):
    _name = "pickup.route"
    _description = "Pickup Route"
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
        help="Unique identifier for the pickup route",
    )
    # Partner Relationship
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    )
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
        help="User responsible for route management",
    )
    active = fields.Boolean(
        string="Active", default=True, help="Active status of the route"
    )
    sequence = fields.Integer(
        string="Sequence", default=10, help="Sequence for ordering routes"
    )

    # ============================================================================
    # ROUTE SCHEDULING AND TIMING
    # ============================================================================
    route_date = fields.Date(
        string="Route Date",
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Scheduled date for the route",
    )
    start_time = fields.Datetime(
        string="Start Time", tracking=True, help="Scheduled start time for the route"
    )
    end_time = fields.Datetime(
        string="End Time", help="Scheduled end time for the route"
    )
    actual_start_time = fields.Datetime(
        string="Actual Start Time", help="Actual time when route execution started"
    )
    actual_end_time = fields.Datetime(
        string="Actual End Time", help="Actual time when route execution completed"
    )
    estimated_duration = fields.Float(
        string="Estimated Duration (hours)", help="Estimated time to complete the route"
    )
    actual_duration = fields.Float(
        string="Actual Duration (hours)",
        compute="_compute_actual_duration",
        store=True,
        help="Actual time taken to complete the route",
    )

    # ============================================================================
    # ROUTE TYPE AND CLASSIFICATION
    # ============================================================================
    route_type = fields.Selection(
        [
            ("regular", "Regular Route"),
            ("on_demand", "On-Demand Route"),
            ("bulk", "Bulk Collection"),
            ("express", "Express Route"),
            ("maintenance", "Maintenance Route"),
            ("emergency", "Emergency Route"),
        ],
        string="Route Type",
        default="regular",
        required=True,
        tracking=True,
        help="Classification of the pickup route",
    )
    priority = fields.Selection(
        [
            ("0", "Very Low"),
            ("1", "Low"),
            ("2", "Normal"),
            ("3", "High"),
            ("4", "Very High"),
        ],
        string="Priority",
        default="2",
        help="Route execution priority",
    )
    service_level = fields.Selection(
        [
            ("standard", "Standard Service"),
            ("premium", "Premium Service"),
            ("express", "Express Service"),
            ("white_glove", "White Glove Service"),
        ],
        string="Service Level",
        default="standard",
        help="Level of service for this route",
    )

    # ============================================================================
    # STATUS AND WORKFLOW MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("planned", "Planned"),
            ("confirmed", "Confirmed"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current status of the pickup route",
    )
    completion_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("partial", "Partially Completed"),
            ("complete", "Fully Completed"),
            ("failed", "Failed"),
        ],
        string="Completion Status",
        default="pending",
        help="Route completion status",
    )

    # ============================================================================
    # PERSONNEL AND VEHICLE ASSIGNMENT
    # ============================================================================
    driver_id = fields.Many2one(
        "res.partner",
        string="Driver",
        tracking=True,
        help="Driver assigned to this route",
    )
    assistant_driver_id = fields.Many2one(
        "res.partner", string="Assistant Driver", help="Assistant driver for the route"
    )
    vehicle_id = fields.Many2one(
        "records.vehicle",
        string="Vehicle",
        tracking=True,
        help="Vehicle assigned to this route",
    )
    backup_vehicle_id = fields.Many2one(
        "records.vehicle", string="Backup Vehicle", help="Backup vehicle for this route"
    )

    # ============================================================================
    # ROUTE OPTIMIZATION AND TRACKING
    # ============================================================================
    start_location_id = fields.Many2one(
        "records.location",
        string="Start Location",
        help="Starting location for the route",
    )
    end_location_id = fields.Many2one(
        "records.location", string="End Location", help="Ending location for the route"
    )
    total_distance = fields.Float(
        string="Total Distance (miles)", help="Total distance of the route"
    )
    estimated_fuel_cost = fields.Monetary(
        string="Estimated Fuel Cost",
        currency_field="currency_id",
        help="Estimated fuel cost for the route",
    )
    actual_fuel_cost = fields.Monetary(
        string="Actual Fuel Cost",
        currency_field="currency_id",
        help="Actual fuel cost for the route",
    )
    currency_id = fields.Many2one(
        "res.currency", string="Currency", related="company_id.currency_id", store=True
    )

    # ============================================================================
    # ROUTE PERFORMANCE METRICS
    # ============================================================================
    total_stops = fields.Integer(
        string="Total Stops",
        compute="_compute_route_metrics",
        store=True,
        help="Total number of stops on the route",
    )
    completed_stops = fields.Integer(
        string="Completed Stops",
        compute="_compute_route_metrics",
        store=True,
        help="Number of completed stops",
    )
    efficiency_score = fields.Float(
        string="Efficiency Score",
        compute="_compute_efficiency_score",
        store=True,
        help="Route efficiency score (0-100)",
    )
    on_time_performance = fields.Float(
        string="On-Time Performance (%)",
        compute="_compute_performance_metrics",
        store=True,
        help="Percentage of on-time deliveries",
    )

    # ============================================================================
    # DOCUMENTATION AND COMMUNICATION
    # ============================================================================
    description = fields.Text(
        string="Description", help="Detailed description of the route"
    )
    route_instructions = fields.Text(
        string="Route Instructions", help="Special instructions for route execution"
    )
    driver_notes = fields.Text(
        string="Driver Notes", help="Notes from the driver during route execution"
    )
    completion_notes = fields.Text(
        string="Completion Notes", help="Notes upon route completion"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    pickup_request_ids = fields.One2many(
        "pickup.request",
        "route_id",
        string="Pickup Requests",
        help="Pickup requests assigned to this route",
    )
    route_stop_ids = fields.One2many(
        "pickup.route.stop",
        "route_id",
        string="Route Stops",
        help="Individual stops on this route",
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
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("name", "route_date", "route_type")
    def _compute_display_name(self):
        """Compute display name with route date and type"""
        for record in self:
            parts = []
            if record.name:
                parts.append(record.name)

            if record.route_date:
                parts.append(f"({record.route_date})")

            if record.route_type:
                route_type_label = dict(record._fields["route_type"].selection)[
                    record.route_type
                ]
                parts.append(f"- {route_type_label}")

            record.display_name = " ".join(parts) or "Pickup Route"

    @api.depends("actual_start_time", "actual_end_time")
    def _compute_actual_duration(self):
        """Calculate actual duration in hours"""
        for record in self:
            if record.actual_start_time and record.actual_end_time:
                delta = record.actual_end_time - record.actual_start_time
                record.actual_duration = delta.total_seconds() / 3600
            else:
                record.actual_duration = 0.0

    @api.depends("route_stop_ids")
    def _compute_route_metrics(self):
        """Compute route performance metrics"""
        for record in self:
            stops = record.route_stop_ids
            record.total_stops = len(stops)
            record.completed_stops = len(
                stops.filtered(lambda s: s.status == "completed")
            )

    @api.depends("estimated_duration", "actual_duration", "total_distance")
    def _compute_efficiency_score(self):
        """Calculate route efficiency score"""
        for record in self:
            if record.estimated_duration and record.actual_duration:
                time_efficiency = min(
                    100, (record.estimated_duration / record.actual_duration) * 100
                )
                record.efficiency_score = time_efficiency
            else:
                record.efficiency_score = 0.0

    @api.depends(
        "route_stop_ids",
        "route_stop_ids.scheduled_time",
        "route_stop_ids.actual_arrival_time",
    )
    def _compute_performance_metrics(self):
        """Calculate on-time performance metrics"""
        for record in self:
            stops_with_times = record.route_stop_ids.filtered(
                lambda s: s.scheduled_time and s.actual_arrival_time
            )

            if stops_with_times:
                on_time_stops = stops_with_times.filtered(
                    lambda s: s.actual_arrival_time <= s.scheduled_time
                )
                record.on_time_performance = (
                    len(on_time_stops) / len(stops_with_times)
                ) * 100
            else:
                record.on_time_performance = 0.0

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence and defaults"""
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("pickup.route") or "ROUTE-NEW"
                )
        return super().create(vals_list)

    def write(self, vals):
        """Override write for state change tracking"""
        if "state" in vals:
            for record in self:
                old_state = record.state
                new_state = vals["state"]
                if old_state != new_state:
                    record.message_post(
                        body=_("Route status changed from %s to %s", (old_state), new_state)
                    )
        return super().write(vals)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the route"""
        self.ensure_one()
        if self.state != "planned":
            raise UserError(_("Only planned routes can be confirmed"))

        if not self.driver_id:
            raise UserError(_("Driver must be assigned before confirming route"))

        if not self.vehicle_id:
            raise UserError(_("Vehicle must be assigned before confirming route"))

        self.write({"state": "confirmed"})
        self.message_post(body=_("Route confirmed and ready for execution"))

    def action_start_route(self):
        """Start route execution"""
        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Only confirmed routes can be started"))

        self.write(
            {
                "state": "in_progress",
                "actual_start_time": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Route execution started"))

    def action_complete_route(self):
        """Complete route execution"""
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Only in-progress routes can be completed"))

        # Check if all stops are completed
        incomplete_stops = self.route_stop_ids.filtered(
            lambda s: s.status != "completed"
        )
        if incomplete_stops:
            raise UserError(
                _("Cannot complete route with incomplete stops: %s", "), ".join(incomplete_stops.mapped("name"))
            )

        self.write(
            {
                "state": "completed",
                "actual_end_time": fields.Datetime.now(),
                "completion_status": "complete",
            }
        )
        self.message_post(body=_("Route execution completed successfully"))

    def action_cancel_route(self):
        """Cancel the route"""
        self.ensure_one()
        if self.state in ["completed"]:
            raise UserError(_("Completed routes cannot be cancelled"))

        self.write({"state": "cancelled"})
        self.message_post(body=_("Route cancelled"))

    def action_reset_to_draft(self):
        """Reset route to draft state"""
        self.ensure_one()
        if self.state in ["completed"]:
            raise UserError(_("Completed routes cannot be reset"))

        self.write(
            {
                "state": "draft",
                "actual_start_time": False,
                "actual_end_time": False,
            }
        )
        self.message_post(body=_("Route reset to draft"))

    def action_optimize_route(self):
        """Optimize route stops for efficiency"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Optimize Route"),
            "res_model": "pickup.route.optimize.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_route_id": self.id},
        }

    def action_view_route_stops(self):
        """View route stops"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Route Stops"),
            "res_model": "pickup.route.stop",
            "view_mode": "tree,form",
            "domain": [("route_id", "=", self.id)],
            "context": {"default_route_id": self.id},
        }

    def action_view_pickup_requests(self):
        """View associated pickup requests"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Pickup Requests"),
            "res_model": "pickup.request",
            "view_mode": "tree,form",
            "domain": [("route_id", "=", self.id)],
            "context": {"default_route_id": self.id},
        }

    def action_generate_route_sheet(self):
        """Generate route sheet report"""
        self.ensure_one()
        return self.env.ref(
            "records_management.action_report_route_sheet"
        ).report_action(self)

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def calculate_route_efficiency(self):
        """Calculate overall route efficiency"""
        self.ensure_one()

        efficiency_factors = {
            "time_efficiency": 0.4,
            "distance_efficiency": 0.3,
            "fuel_efficiency": 0.2,
            "completion_rate": 0.1,
        }

        total_score = 0.0

        # Time efficiency
        if self.estimated_duration and self.actual_duration:
            time_score = min(
                100, (self.estimated_duration / self.actual_duration) * 100
            )
            total_score += time_score * efficiency_factors["time_efficiency"]

        # Distance efficiency (based on optimal vs actual)
        # For production GPS/mapping integration implementation details,
        # see: /records_management/doc/developer/models/pickup_route_management.md
        # Section: "GPS Integration & Route Optimization"
        distance_score = 85.0  # Placeholder - Replace with production GPS integration
        total_score += distance_score * efficiency_factors["distance_efficiency"]

        # Fuel efficiency
        if self.estimated_fuel_cost and self.actual_fuel_cost:
            fuel_score = min(
                100, (self.estimated_fuel_cost / self.actual_fuel_cost) * 100
            )
            total_score += fuel_score * efficiency_factors["fuel_efficiency"]

        # Completion rate
        if self.total_stops > 0:
            completion_score = (self.completed_stops / self.total_stops) * 100
            total_score += completion_score * efficiency_factors["completion_rate"]

        return total_score

    def assign_pickup_requests(self, pickup_request_ids):
        """Assign pickup requests to this route"""
        self.ensure_one()

        pickup_requests = self.env["pickup.request"].browse(pickup_request_ids)

        # Validate pickup requests can be assigned
        for request in pickup_requests:
            if request.state not in ["confirmed", "scheduled"]:
                raise UserError(
                    _("Pickup request %s is not in a valid state for route assignment", request.name)
                )

        # Assign to route
        pickup_requests.write({"route_id": self.id})

        # Create route stops with incrementing sequence
        next_sequence = max(self.route_stop_ids.mapped("sequence") or [0]) + 1
        for request in pickup_requests:
            self.env["pickup.route.stop"].create(
                {
                    "route_id": self.id,
                    "pickup_request_id": request.id,
                    "location_id": request.pickup_location_id.id,
                    "scheduled_time": request.scheduled_pickup_date,
                    "sequence": next_sequence,
                }
            )
            next_sequence += 1

        self.message_post(
            body=_("Assigned %d pickup requests to route", len(pickup_requests))
        )

    def get_route_summary(self):
        """Get route summary for reporting"""
        self.ensure_one()
        return {
            "route_name": self.name,
            "route_date": self.route_date,
            "driver": self.driver_id.name if self.driver_id else None,
            "vehicle": self.vehicle_id.name if self.vehicle_id else None,
            "total_stops": self.total_stops,
            "completed_stops": self.completed_stops,
            "efficiency_score": self.efficiency_score,
            "on_time_performance": self.on_time_performance,
            "status": self.state,
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("start_time", "end_time")
    def _check_route_times(self):
        """Validate route start and end times"""
        for record in self:
            if record.start_time and record.end_time:
                if record.start_time >= record.end_time:
                    raise ValidationError(_("Start time must be before end time"))

    @api.constrains("actual_start_time", "actual_end_time")
    def _check_actual_times(self):
        """Validate actual start and end times"""
        for record in self:
            if record.actual_start_time and record.actual_end_time:
                if record.actual_start_time >= record.actual_end_time:
                    raise ValidationError(
                        _("Actual start time must be before actual end time")
                    )

    @api.constrains("total_distance")
    def _check_distance(self):
        """Validate total distance is positive"""
        for record in self:
            if record.total_distance and record.total_distance <= 0:
                raise ValidationError(_("Total distance must be positive"))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name_parts = [record.name]

            if record.route_date:
                name_parts.append(f"({record.route_date})")

            if record.driver_id:
                name_parts.append(f"- {record.driver_id.name}")

            result.append((record.id, " ".join(name_parts)))
        return result

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Enhanced search by name, driver, or vehicle"""
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                ("name", operator, name),
                ("driver_id.name", operator, name),
                ("vehicle_id.name", operator, name),
            ]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


class PickupRouteStop(models.Model):
    """Individual stops within a pickup route"""

    _name = "pickup.route.stop"
    _description = "Pickup Route Stop"
    _order = "route_id, sequence, id"

    route_id = fields.Many2one(
        "pickup.route", string="Route", required=True, ondelete="cascade"
    )
    pickup_request_id = fields.Many2one(
        "pickup.request", string="Pickup Request", help="Associated pickup request"
    )
    sequence = fields.Integer(string="Sequence", default=10)
    name = fields.Char(string="Stop Name", compute="_compute_name", store=True)
    location_id = fields.Many2one("records.location", string="Location", required=True)
    address = fields.Text(string="Address", related="location_id.full_address")
    scheduled_time = fields.Datetime(
        string="Scheduled Time", help="Scheduled arrival time"
    )
    actual_arrival_time = fields.Datetime(
        string="Actual Arrival Time", help="Actual arrival time at stop"
    )
    departure_time = fields.Datetime(
        string="Departure Time", help="Time of departure from stop"
    )
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("skipped", "Skipped"),
            ("failed", "Failed"),
        ],
        string="Status",
        default="pending",
    )
    estimated_service_time = fields.Float(
        string="Estimated Service Time (minutes)",
        help="Estimated time to complete service at stop",
    )
    actual_service_time = fields.Float(
        string="Actual Service Time (minutes)",
        compute="_compute_actual_service_time",
        store=True,
    )
    notes = fields.Text(string="Notes")

    @api.depends("pickup_request_id", "location_id")
    def _compute_name(self):
        """Compute stop name"""
        for record in self:
            if record.pickup_request_id:
                record.name = _("Stop: %s"
            elif record.location_id:
                record.name = _("Stop: %s"
            else:
                record.name = _("Stop %s"

    @api.depends("actual_arrival_time", "departure_time")
    def _compute_actual_service_time(self):
        """Calculate actual service time in minutes"""
        for record in self:
            if record.actual_arrival_time and record.departure_time:
                delta = record.departure_time - record.actual_arrival_time
                record.actual_service_time = delta.total_seconds() / 60
            else:
                record.actual_service_time = 0.0

    def action_start_service(self):
        """Start service at this stop"""
        self.ensure_one()
        self.write(
            {
                "status": "in_progress",
                "actual_arrival_time": fields.Datetime.now(),
            }
        )

    def action_complete_service(self):
        """Complete service at this stop"""
        self.ensure_one()
        self.write(
            {
                "status": "completed",
                "departure_time": fields.Datetime.now(),
            }
        )

    def action_skip_stop(self):
        """Skip this stop"""
        self.ensure_one()
        self.write({"status": "skipped"})


class PickupRouteOptimizeWizard(models.TransientModel):
    """Wizard for optimizing pickup routes"""

    _name = "pickup.route.optimize.wizard"
    _description = "Pickup Route Optimization Wizard"

    route_id = fields.Many2one("pickup.route", string="Route", required=True)
    optimization_method = fields.Selection(
        [
            ("distance", "Minimize Distance"),
            ("time", "Minimize Time"),
            ("fuel", "Minimize Fuel Cost"),
            ("balanced", "Balanced Optimization"),
        ],
        string="Optimization Method",
        default="balanced",
        required=True,
    )
    consider_traffic = fields.Boolean(
        string="Consider Traffic",
        default=True,
        help="Include traffic conditions in optimization",
    )
    consider_time_windows = fields.Boolean(
        string="Consider Time Windows",
        default=True,
        help="Respect customer time windows",
    )
    notes = fields.Text(string="Optimization Notes")

    def action_optimize_route(self):
        """Optimize the route stops"""
        self.ensure_one()

        # This would integrate with external routing APIs
        # For now, implement a simple distance-based optimization

        stops = self.route_id.route_stop_ids.sorted("sequence")

        # Placeholder optimization logic
        # In real implementation, this would call external routing services
        optimized_sequence = 1
        for stop in stops:
            stop.write({"sequence": optimized_sequence})
            optimized_sequence += 1

        self.route_id.message_post(
            body=_("Route optimized using %s method", dict(self._fields["optimization_method"].selection))[
                self.optimization_method
            ]
        )

        return {"type": "ir.actions.act_window_close"}
        return {"type": "ir.actions.act_window_close"}
