# -*- coding: utf-8 -*-
"""
FSM Route Management - Central Hub for Field Service Operations

This module serves as the central orchestrator for all Field Service Management
operations in the Records Management system. It integrates with existing FSM tools:
- fsm_reschedule_wizard: Handles route rescheduling
- fsm_notification: Manages driver and customer notifications  
- route optimizer: Optimizes pickup and delivery routes
- pickup_request: Customer pickup requests
- records_vehicle: Vehicle and driver management

Designed for intuitive user experience with unified interface while keeping
existing specialized models for flexibility and maintainability.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
import logging
import json

_logger = logging.getLogger(__name__)


class FsmRouteManagement(models.Model):
    _name = "fsm.route.management"
    _description = "FSM Route Management - Central Hub"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "scheduled_date desc, priority desc, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Route Name",
        required=True,
        tracking=True,
        index=True,
        help="Name or identifier for this route"
    )
    sequence = fields.Integer(string="Sequence", default=10)
    company_id = fields.Many2one(
        "res.company",
        string="Company", 
        default=lambda self: self.env.company,
        required=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="Route Manager",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for managing this route"
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # ROUTE SCHEDULING & TIMING
    # ============================================================================
    scheduled_date = fields.Date(
        string="Scheduled Date",
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Date when route is scheduled to run"
    )
    start_time = fields.Float(
        string="Start Time",
        default=8.0,
        help="Route start time (24-hour format)"
    )
    end_time = fields.Float(
        string="End Time", 
        default=17.0,
        help="Expected route completion time"
    )
    estimated_duration = fields.Float(
        string="Estimated Duration (hours)",
        compute="_compute_estimated_duration",
        store=True,
        help="Total estimated duration for route completion"
    )
    actual_start_time = fields.Datetime(
        string="Actual Start",
        tracking=True,
        help="When the route actually started"
    )
    actual_end_time = fields.Datetime(
        string="Actual End",
        tracking=True,
        help="When the route was completed"
    )

    # ============================================================================
    # DRIVER & VEHICLE ASSIGNMENT  
    # ============================================================================
    driver_id = fields.Many2one(
        "res.users",
        string="Assigned Driver",
        domain=[("groups_id", "in", [])],  # Will be configured for drivers group
        tracking=True,
        help="Driver assigned to this route"
    )
    vehicle_id = fields.Many2one(
        "records.vehicle", 
        string="Vehicle",
        tracking=True,
        help="Vehicle assigned to this route"
    )
    backup_driver_id = fields.Many2one(
        "res.users",
        string="Backup Driver",
        help="Backup driver in case primary driver unavailable"
    )

    # ============================================================================
    # ROUTE DETAILS & OPTIMIZATION
    # ============================================================================
    route_type = fields.Selection([
        ("pickup", "Pickup Route"),
        ("delivery", "Delivery Route"), 
        ("mixed", "Mixed Route"),
        ("emergency", "Emergency Route"),
        ("maintenance", "Maintenance Route")
    ], string="Route Type", default="pickup", required=True, tracking=True)

    priority = fields.Selection([
        ("0", "Very Low"),
        ("1", "Low"),
        ("2", "Normal"), 
        ("3", "High"),
        ("4", "Very High"),
        ("5", "Critical")
    ], string="Priority", default="2", tracking=True)

    total_stops = fields.Integer(
        string="Total Stops",
        compute="_compute_route_stats",
        store=True,
        help="Total number of stops on this route"
    )
    total_distance = fields.Float(
        string="Total Distance (miles)",
        compute="_compute_route_stats", 
        store=True,
        help="Total route distance in miles"
    )
    total_containers = fields.Integer(
        string="Total Containers",
        compute="_compute_route_stats",
        store=True,
        help="Total containers to pickup/deliver"
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("optimized", "Optimized"),
        ("assigned", "Driver Assigned"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("rescheduled", "Rescheduled")
    ], string="Status", default="draft", tracking=True, required=True)

    # ============================================================================
    # RELATIONSHIP FIELDS - Integration with existing FSM models
    # ============================================================================
    pickup_request_ids = fields.One2many(
        "pickup.request",
        "route_id", 
        string="Pickup Requests",
        help="Customer pickup requests assigned to this route"
    )
    
    # Integration with existing FSM tools
    optimization_result_ids = fields.One2many(
        "route.optimizer",
        "route_management_id",
        string="Route Optimizations",
        help="Route optimization results"
    )
    
    reschedule_history_ids = fields.One2many(
        "fsm.reschedule.wizard",
        "route_management_id", 
        string="Reschedule History",
        help="History of route reschedules"
    )
    
    notification_ids = fields.One2many(
        "fsm.notification",
        "route_management_id",
        string="Notifications", 
        help="Notifications sent for this route"
    )

    # ============================================================================
    # ROUTE CONFIGURATION & CONSTRAINTS
    # ============================================================================
    max_stops_per_route = fields.Integer(
        string="Max Stops",
        default=25,
        help="Maximum stops allowed per route"
    )
    max_driving_hours = fields.Float(
        string="Max Driving Hours", 
        default=8.0,
        help="Maximum driving hours per route"
    )
    service_area_ids = fields.Many2many(
        "records.location",
        string="Service Areas",
        help="Geographic areas covered by this route"
    )
    
    # Route notes and special instructions
    route_notes = fields.Text(
        string="Route Notes",
        help="Special instructions or notes for the driver"
    )
    customer_instructions = fields.Text(
        string="Customer Instructions",
        help="Special customer instructions for stops"
    )

    # ============================================================================
    # PERFORMANCE TRACKING
    # ============================================================================
    completion_rate = fields.Float(
        string="Completion Rate %",
        compute="_compute_performance_metrics",
        store=True,
        help="Percentage of stops completed successfully"
    )
    on_time_rate = fields.Float(
        string="On-Time Rate %", 
        compute="_compute_performance_metrics",
        store=True,
        help="Percentage of stops completed on time"
    )
    fuel_cost = fields.Monetary(
        string="Estimated Fuel Cost",
        currency_field="currency_id",
        help="Estimated fuel cost for this route"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )

    # ============================================================================
    # MAIL FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("start_time", "end_time")
    def _compute_estimated_duration(self):
        for record in self:
            if record.start_time and record.end_time:
                record.estimated_duration = record.end_time - record.start_time
            else:
                record.estimated_duration = 0.0

    @api.depends("pickup_request_ids")
    def _compute_route_stats(self):
        for record in self:
            requests = record.pickup_request_ids
            record.total_stops = len(requests)
            record.total_containers = sum(req.container_count or 0 for req in requests)
            # Distance calculation would integrate with mapping service
            record.total_distance = 0.0  # Placeholder for mapping integration

    @api.depends("pickup_request_ids", "pickup_request_ids.state")
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
            record.on_time_rate = 85.0  # Placeholder

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi  
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("fsm.route.management") or "New Route"
        return super().create(vals_list)

    def write(self, vals):
        # Track state changes
        if "state" in vals:
            for record in self:
                if vals["state"] != record.state:
                    old_state = dict(record._fields["state"].selection)[record.state] 
                    new_state = dict(record._fields["state"].selection)[vals["state"]]
                    record.message_post(
                        body=_("Route status changed from %s to %s", old_state, new_state)
                    )
        return super().write(vals)

    # ============================================================================
    # UNIFIED FSM ORCHESTRATION METHODS
    # ============================================================================
    def action_optimize_route(self):
        """Launch route optimizer - integrates with existing route.optimizer model"""
        self.ensure_one()
        
        # Check if route optimizer model exists and call it
        if "route.optimizer" in self.env:
            optimizer = self.env["route.optimizer"].create({
                "route_management_id": self.id,
                "optimization_date": fields.Datetime.now(),
                "pickup_request_ids": [(6, 0, self.pickup_request_ids.ids)]
            })
            return optimizer.action_optimize()
        else:
            # Fallback optimization logic
            return self._basic_route_optimization()

    def action_reschedule_route(self):
        """Launch reschedule wizard - integrates with existing fsm.reschedule.wizard"""
        self.ensure_one()
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Reschedule Route"),
            "res_model": "fsm.reschedule.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_route_management_id": self.id,
                "default_current_date": self.scheduled_date,
                "default_pickup_request_ids": [(6, 0, self.pickup_request_ids.ids)]
            }
        }

    def action_send_notifications(self):
        """Send route notifications - integrates with existing fsm.notification model"""
        self.ensure_one()
        
        # Create notifications for driver and customers
        notification_vals = []
        
        # Driver notification
        if self.driver_id:
            notification_vals.append({
                "route_management_id": self.id,
                "recipient_id": self.driver_id.partner_id.id,
                "notification_type": "driver_assignment", 
                "subject": _("Route Assignment: %s", self.name),
                "message": _("You have been assigned to route %s scheduled for %s", 
                           self.name, self.scheduled_date),
                "send_sms": True,
                "send_email": True
            })
        
        # Customer notifications for each pickup
        for pickup in self.pickup_request_ids:
            if pickup.partner_id:
                notification_vals.append({
                    "route_management_id": self.id,
                    "recipient_id": pickup.partner_id.id,
                    "notification_type": "pickup_scheduled",
                    "subject": _("Pickup Scheduled: %s", pickup.name),
                    "message": _("Your pickup has been scheduled for %s", self.scheduled_date),
                    "send_email": True
                })
        
        # Create notifications using existing model
        if notification_vals and "fsm.notification" in self.env:
            notifications = self.env["fsm.notification"].create(notification_vals)
            notifications.action_send_all()
        
        self.message_post(
            body=_("Route notifications sent to driver and customers (%d notifications)", 
                 len(notification_vals))
        )

    def action_assign_driver(self):
        """Smart driver assignment based on availability and location"""
        self.ensure_one()
        
        # This would integrate with driver scheduling system
        available_drivers = self.env["res.users"].search([
            ("groups_id", "in", []),  # Driver group - to be configured
            # Add availability constraints
        ])
        
        if available_drivers:
            # Simple assignment - can be enhanced with AI/ML
            self.driver_id = available_drivers[0]
            self.state = "assigned"
            self.message_post(
                body=_("Driver %s automatically assigned to route", self.driver_id.name)
            )
        else:
            raise UserError(_("No available drivers found for route assignment"))

    def action_start_route(self):
        """Start the route - updates state and tracking"""
        self.ensure_one()
        
        if not self.driver_id:
            raise UserError(_("Cannot start route without assigned driver"))
            
        if not self.vehicle_id:
            raise UserError(_("Cannot start route without assigned vehicle"))
        
        self.write({
            "state": "in_progress",
            "actual_start_time": fields.Datetime.now()
        })
        
        # Update pickup requests to in_progress
        self.pickup_request_ids.write({"state": "in_progress"})
        
        self.message_post(
            body=_("Route started by driver %s at %s", 
                 self.driver_id.name, fields.Datetime.now())
        )

    def action_complete_route(self):
        """Complete the route and update all related records"""
        self.ensure_one()
        
        self.write({
            "state": "completed", 
            "actual_end_time": fields.Datetime.now()
        })
        
        # Update pickup requests based on completion
        completed_pickups = self.pickup_request_ids.filtered(lambda r: r.state == "completed")
        remaining_pickups = self.pickup_request_ids - completed_pickups
        
        if remaining_pickups:
            # Auto-reschedule incomplete pickups
            self._auto_reschedule_remaining(remaining_pickups)
        
        self.message_post(
            body=_("Route completed. %d/%d pickups successful", 
                 len(completed_pickups), len(self.pickup_request_ids))
        )

    def action_view_route_dashboard(self):
        """Open unified route dashboard view"""
        self.ensure_one()
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Route Dashboard: %s", self.name),
            "res_model": "fsm.route.management",
            "res_id": self.id,
            "view_mode": "form",
            "view_id": False,  # Will use the main form view with dashboard layout
            "target": "current",
            "context": {"dashboard_mode": True}
        }

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _basic_route_optimization(self):
        """Basic route optimization when optimizer model not available"""
        # Simple geographic sorting by customer location
        if self.pickup_request_ids:
            # This would integrate with mapping service for real optimization
            sorted_requests = self.pickup_request_ids.sorted(lambda r: r.partner_id.name)
            for i, request in enumerate(sorted_requests):
                request.sequence = i + 1
        
        self.state = "optimized"
        return True

    def _auto_reschedule_remaining(self, remaining_pickups):
        """Auto-reschedule incomplete pickups to next business day"""
        next_date = self._get_next_business_day(self.scheduled_date)
        
        # Create new route for remaining pickups  
        new_route = self.copy({
            "name": _("%s - Rescheduled", self.name),
            "scheduled_date": next_date,
            "state": "scheduled",
            "pickup_request_ids": [(6, 0, remaining_pickups.ids)]
        })
        
        # Clear pickup requests from current route
        remaining_pickups.write({"route_id": new_route.id})
        
        return new_route

    def _get_next_business_day(self, current_date):
        """Get next business day (Monday-Friday)"""
        next_date = current_date + timedelta(days=1)
        while next_date.weekday() > 4:  # Saturday=5, Sunday=6
            next_date += timedelta(days=1)
        return next_date

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("start_time", "end_time")
    def _check_time_logic(self):
        for record in self:
            if record.start_time >= record.end_time:
                raise ValidationError(_("Start time must be before end time"))

    @api.constrains("scheduled_date")
    def _check_scheduled_date(self):
        for record in self:
            if record.scheduled_date < fields.Date.today():
                raise ValidationError(_("Cannot schedule routes in the past"))

    @api.constrains("max_stops_per_route", "pickup_request_ids")
    def _check_max_stops(self):
        for record in self:
            if len(record.pickup_request_ids) > record.max_stops_per_route:
                raise ValidationError(
                    _("Route exceeds maximum stops limit (%d/%d)",
                    len(record.pickup_request_ids), record.max_stops_per_route)
                )

    # ============================================================================  
    # SEARCH METHODS
    # ============================================================================
    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Enhanced search by route name, driver, or date"""
        args = args or []
        domain = []
        
        if name:
            domain = [
                "|", "|", "|",
                ("name", operator, name),
                ("driver_id.name", operator, name), 
                ("route_type", operator, name),
                ("scheduled_date", operator, name)
            ]
            
        return self._search(domain + args, limit=limit)

    # ============================================================================
    # REPORTING METHODS  
    # ============================================================================
    @api.model
    def get_route_analytics(self, date_from=None, date_to=None):
        """Get route performance analytics"""
        domain = []
        if date_from:
            domain.append(("scheduled_date", ">=", date_from))
        if date_to:
            domain.append(("scheduled_date", "<=", date_to))
            
        routes = self.search(domain)
        
        return {
            "total_routes": len(routes),
            "completed_routes": len(routes.filtered(lambda r: r.state == "completed")),
            "average_completion_rate": sum(routes.mapped("completion_rate")) / len(routes) if routes else 0,
            "total_containers": sum(routes.mapped("total_containers")),
            "total_distance": sum(routes.mapped("total_distance")),
        }