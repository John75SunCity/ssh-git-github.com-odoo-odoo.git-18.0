# -*- coding: utf-8 -*-
"""
Model for individual stops within a pickup route.
"""
from odoo import models, fields, api, _


class PickupRouteStop(models.Model):
    """Individual stops within a pickup route"""

    _name = "pickup.route.stop"
    _description = "Pickup Route Stop"
    _order = "route_id, sequence, id"

    route_id = fields.Many2one(
        "pickup.route", string="Route", required=True, ondelete="cascade"
    )
    pickup_request_id = fields.Many2one(
        "pickup.request",
        string="Pickup Request",
        help="Associated pickup request",
    )
    sequence = fields.Integer(string="Sequence", default=10)
    name = fields.Char(string="Stop Name", compute="_compute_name", store=True)
    location_id = fields.Many2one(
        "records.location", string="Location", required=True
    )
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

    @api.depends("pickup_request_id.name", "location_id.name")
    def _compute_name(self):
        """Compute stop name"""
        for record in self:
            if record.pickup_request_id:
                record.name = _("Stop: %s", record.pickup_request_id.name)
            elif record.location_id:
                record.name = _("Stop: %s", record.location_id.name)
            else:
                record.name = _("Stop %s", record.id)

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
