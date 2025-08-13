# -*- coding: utf-8 -*-
"""
Pickup Route Stop Management Module

This module manages individual stops within pickup routes, providing detailed
tracking of each location visit including timing, status, and completion details.

Features:
- Individual stop management within routes
- GPS coordinate tracking
- Time tracking for each stop
- Integration with pickup requests
- Performance metrics per stop

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PickupRouteStop(models.Model):
    """
    Individual stops within pickup routes.

    This model represents each location that needs to be visited during a pickup route,
    providing detailed tracking of arrival times, completion status, and performance metrics.
    """

    _name = "pickup.route.stop"
    _description = "Pickup Route Stop"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "route_id, sequence, planned_arrival"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    display_name = fields.Char(
        string="Stop Name", compute="_compute_display_name", store=True
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    route_id = fields.Many2one(
        "pickup.route",
        string="Route",
        required=True,
        ondelete="cascade",
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        help="Customer location for this stop",
    )
    pickup_request_id = fields.Many2one(
        "pickup.request",
        string="Pickup Request",
        help="Associated pickup request for this stop",
    )

    # ============================================================================
    # SEQUENCE AND PLANNING
    # ============================================================================
    sequence = fields.Integer(
        string="Stop Sequence",
        default=10,
        help="Order of this stop in the route",
    )
    planned_arrival = fields.Datetime(
        string="Planned Arrival", help="When we plan to arrive at this stop"
    )
    planned_departure = fields.Datetime(
        string="Planned Departure", help="When we plan to leave this stop"
    )
    actual_arrival = fields.Datetime(string="Actual Arrival", tracking=True)
    actual_departure = fields.Datetime(
        string="Actual Departure", tracking=True
    )

    # ============================================================================
    # LOCATION AND ADDRESS
    # ============================================================================
    address = fields.Text(
        string="Stop Address", help="Full address for this stop"
    )
    gps_latitude = fields.Float(string="GPS Latitude", digits=(10, 7))
    gps_longitude = fields.Float(string="GPS Longitude", digits=(10, 7))
    distance = fields.Float(
        string="Distance to Stop (km)", help="Distance from previous stop"
    )

    # ============================================================================
    # STATUS AND COMPLETION
    # ============================================================================
    state = fields.Selection(
        [
            ("planned", "Planned"),
            ("in_transit", "In Transit"),
            ("arrived", "Arrived"),
            ("completed", "Completed"),
            ("skipped", "Skipped"),
        ],
        string="Status",
        default="planned",
        tracking=True,
    )

    completion_status = fields.Selection(
        [
            ("successful", "Successful"),
            ("partial", "Partial"),
            ("failed", "Failed"),
            ("rescheduled", "Rescheduled"),
        ],
        string="Completion Status",
    )

    # ============================================================================
    # PERFORMANCE METRICS
    # ============================================================================
    planned_duration = fields.Float(
        string="Planned Duration (minutes)",
        help="Expected time to spend at this stop",
    )
    actual_duration = fields.Float(
        string="Actual Duration (minutes)",
        compute="_compute_actual_duration",
        store=True,
        help="Actual time spent at this stop",
    )
    delay_minutes = fields.Float(
        string="Delay (minutes)",
        compute="_compute_delay",
        store=True,
        help="Minutes behind schedule",
    )

    # ============================================================================
    # NOTES AND DETAILS
    # ============================================================================
    notes = fields.Text(string="Stop Notes")
    completion_notes = fields.Text(
        string="Completion Notes",
        help="Notes about what was completed at this stop",
    )
    special_instructions = fields.Text(
        string="Special Instructions",
        help="Special handling instructions for this stop",
    )

    # Mail framework fields
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities"
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("partner_id.name", "sequence", "pickup_request_id.name")
    def _compute_display_name(self):
        for stop in self:
            if stop.pickup_request_id:
                stop.display_name = _(
                    "Stop %s: %s (%s)",
                    stop.sequence,
                    stop.partner_id.name,
                    stop.pickup_request_id.name,
                )
            else:
                stop.display_name = _(
                    "Stop %s: %s", stop.sequence, stop.partner_id.name
                )

    @api.depends("actual_arrival", "actual_departure")
    def _compute_actual_duration(self):
        for stop in self:
            if stop.actual_arrival and stop.actual_departure:
                delta = stop.actual_departure - stop.actual_arrival
                stop.actual_duration = (
                    delta.total_seconds() / 60.0
                )  # Convert to minutes
            else:
                stop.actual_duration = 0.0

    @api.depends("planned_arrival", "actual_arrival")
    def _compute_delay(self):
        for stop in self:
            if stop.planned_arrival and stop.actual_arrival:
                delta = stop.actual_arrival - stop.planned_arrival
                stop.delay_minutes = (
                    delta.total_seconds() / 60.0
                )  # Convert to minutes
            else:
                stop.delay_minutes = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_in_transit(self):
        """Mark stop as in transit"""
        self.ensure_one()
        if self.state != "planned":
            raise UserError(_("Can only mark planned stops as in transit"))

        self.write({"state": "in_transit"})
        self.message_post(body=_("Stop marked as in transit"))

    def action_mark_arrived(self):
        """Mark arrival at stop"""
        self.ensure_one()
        if self.state not in ["planned", "in_transit"]:
            raise UserError(_("Invalid state transition to arrived"))

        self.write(
            {"state": "arrived", "actual_arrival": fields.Datetime.now()}
        )
        self.message_post(body=_("Arrived at stop"))

    def action_complete_stop(self):
        """Complete the stop"""
        self.ensure_one()
        if self.state != "arrived":
            raise UserError(_("Must arrive at stop before completing"))

        self.write(
            {
                "state": "completed",
                "actual_departure": fields.Datetime.now(),
                "completion_status": "successful",
            }
        )

        # Update associated pickup request
        if self.pickup_request_id:
            self.pickup_request_id.action_mark_completed()

        self.message_post(body=_("Stop completed successfully"))

    def action_skip_stop(self):
        """Skip this stop"""
        self.ensure_one()
        if self.state in ["completed"]:
            raise UserError(_("Cannot skip completed stops"))

        self.write({"state": "skipped", "completion_status": "failed"})
        self.message_post(body=_("Stop skipped"))

    def action_reschedule_stop(self):
        """Reschedule this stop"""
        self.ensure_one()
        self.write({"state": "planned", "completion_status": "rescheduled"})
        self.message_post(body=_("Stop rescheduled"))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("planned_arrival", "planned_departure")
    def _check_planned_times(self):
        for stop in self:
            if stop.planned_arrival and stop.planned_departure:
                if stop.planned_arrival >= stop.planned_departure:
                    raise ValidationError(
                        _("Planned departure must be after arrival")
                    )

    @api.constrains("actual_arrival", "actual_departure")
    def _check_actual_times(self):
        for stop in self:
            if stop.actual_arrival and stop.actual_departure:
                if stop.actual_arrival >= stop.actual_departure:
                    raise ValidationError(
                        _("Actual departure must be after arrival")
                    )

    @api.constrains("gps_latitude")
    def _check_gps_latitude(self):
        for stop in self:
            if stop.gps_latitude and not (-90 <= stop.gps_latitude <= 90):
                raise ValidationError(
                    _("GPS latitude must be between -90 and 90 degrees")
                )

    @api.constrains("gps_longitude")
    def _check_gps_longitude(self):
        for stop in self:
            if stop.gps_longitude and not (-180 <= stop.gps_longitude <= 180):
                raise ValidationError(
                    _("GPS longitude must be between -180 and 180 degrees")
                )

    # ============================================================================
    # OVERRIDE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        stops = super().create(vals_list)

        # Auto-populate address from partner if not provided
        for stop in stops:
            if not stop.address and stop.partner_id:
                stop.address = stop.partner_id.contact_address

        return stops
