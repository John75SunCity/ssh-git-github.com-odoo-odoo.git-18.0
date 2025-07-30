# -*- coding: utf-8 -*-
"""
Records Management Vehicle Model
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsVehicle(models.Model):
    """
    Vehicle Management for Records Management Pickup Routes
    Simple vehicle model focused on capacity tracking for document pickup
    """

    _name = "records.vehicle"
    _description = "Records Management Vehicle"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(
        string="Vehicle Name",
        required=True,
        tracking=True,
        help="Vehicle identifier or name",
    )
    license_plate = fields.Char(string="License Plate", tracking=True)
    vin = fields.Char(string="VIN Number", help="Vehicle Identification Number")

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Vehicle Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)

    # ==========================================
    # VEHICLE SPECIFICATIONS
    # ==========================================
    vehicle_type = fields.Selection(
        [
            ("truck", "Truck"),
            ("van", "Van"),
            ("trailer", "Trailer"),
            ("car", "Car"),
            ("other", "Other"),
        ],
        string="Vehicle Type",
        default="truck",
        required=True,
        tracking=True,
    )

    # ==========================================
    # CAPACITY FIELDS (These are what pickup_route needs)
    # ==========================================
    vehicle_capacity_weight = fields.Float(
        string="Weight Capacity (lbs)",
        help="Maximum weight capacity in pounds",
        tracking=True,
    )
    vehicle_capacity_volume = fields.Float(
        string="Volume Capacity (cubic ft)",
        help="Maximum volume capacity in cubic feet",
        tracking=True,
    )

    # Additional capacity fields
    max_containers = fields.Integer(
        string="Max Containers", help="Maximum number of containers"
    )

    # ==========================================
    # PHYSICAL SPECIFICATIONS
    # ==========================================
    length = fields.Float(string="Length (ft)", help="Vehicle length in feet")
    width = fields.Float(string="Width (ft)", help="Vehicle width in feet")
    height = fields.Float(string="Height (ft)", help="Vehicle height in feet")

    # ==========================================
    # OPERATIONAL FIELDS
    # ==========================================
    driver_id = fields.Many2one("res.users", string="Primary Driver", tracking=True)
    driver_contact = fields.Char(
        string="Driver Contact", help="Driver phone or contact info"
    )

    # Operational status
    status = fields.Selection(
        [
            ("available", "Available"),
            ("in_use", "In Use"),
            ("maintenance", "Under Maintenance"),
            ("out_of_service", "Out of Service"),
        ],
        string="Status",
        default="available",
        tracking=True,
    )

    # ==========================================
    # MAINTENANCE TRACKING
    # ==========================================
    last_service_date = fields.Date(string="Last Service Date")
    next_service_date = fields.Date(string="Next Service Date")
    service_notes = fields.Text(string="Service Notes")

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    total_capacity = fields.Float(
        string="Total Capacity Score",
        compute="_compute_total_capacity",
        store=True,
        help="Combined capacity score for optimization",
    )

    # ==========================================
    # RELATIONSHIPS
    # ==========================================
    pickup_route_ids = fields.One2many(
        "pickup.route", "vehicle_id", string="Pickup Routes"
    )
    fuel_capacity = fields.Float(
        string="Fuel Capacity", default=0.0, help="Fuel tank capacity"
    )
    maintenance_due_date = fields.Char(
        string="Maintenance Due Date", help="Next maintenance due date"
    )
    insurance_expiry = fields.Char(
        string="Insurance Expiry", help="Insurance expiry date"
    )
    registration_number = fields.Char(
        string="Registration Number", help="Vehicle registration number"
    )
    Vehicles = fields.Char(string='Vehicles')
    action_set_available = fields.Char(string='Action Set Available')
    action_set_in_use = fields.Char(string='Action Set In Use')
    action_set_maintenance = fields.Char(string='Action Set Maintenance')
activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    available = fields.Char(string='Available')
    capacity = fields.Char(string='Capacity')
    group_driver = fields.Char(string='Group Driver')
    group_status = fields.Selection([], string='Group Status')  # TODO: Define selection options
    group_type = fields.Selection([], string='Group Type')  # TODO: Define selection options
    help = fields.Char(string='Help')
    in_use = fields.Char(string='In Use')
    maintenance = fields.Char(string='Maintenance')
    max_boxes = fields.Char(string='Max Boxes')
message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    res_model = fields.Char(string='Res Model')
    route_date = fields.Date(string='Route Date')
    routes = fields.Char(string='Routes')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    start_time = fields.Float(string='Start Time', digits=(12, 2))
    view_mode = fields.Char(string='View Mode')

    # ==========================================
    # COMPUTE METHODS
    # ==========================================
    @api.depends("vehicle_capacity_weight", "vehicle_capacity_volume")
    def _compute_total_capacity(self):
        """Compute total capacity score for optimization"""
        for vehicle in self:
            # Simple scoring: weight capacity + volume capacity normalized
            weight_score = vehicle.vehicle_capacity_weight or 0
            volume_score = (
                vehicle.vehicle_capacity_volume or 0
            ) * 50  # Weight volume more
            vehicle.total_capacity = weight_score + volume_score

    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    @api.constrains("vehicle_capacity_weight", "vehicle_capacity_volume")
    def _check_capacity_positive(self):
        """Ensure capacity values are positive"""
        for vehicle in self:
            if vehicle.vehicle_capacity_weight and vehicle.vehicle_capacity_weight < 0:
                raise ValidationError(_("Weight capacity must be positive"))
            if vehicle.vehicle_capacity_volume and vehicle.vehicle_capacity_volume < 0:
                raise ValidationError(_("Volume capacity must be positive"))

    @api.constrains("length", "width", "height")
    def _check_dimensions_positive(self):
        """Ensure dimension values are positive"""
        for vehicle in self:
            if vehicle.length and vehicle.length <= 0:
                raise ValidationError(_("Length must be positive"))
            if vehicle.width and vehicle.width <= 0:
                raise ValidationError(_("Width must be positive"))
            if vehicle.height and vehicle.height <= 0:
                raise ValidationError(_("Height must be positive"))

    # ==========================================
    # ACTION METHODS
    # ==========================================
    @api.depends("vehicle_capacity_weight")
    def _compute_capacity_status(self):
        """Compute vehicle capacity status"""
        for record in self:
            if record.vehicle_capacity_weight:
                if record.vehicle_capacity_weight >= 10000:
                    record.capacity_status = "heavy_duty"
                elif record.vehicle_capacity_weight >= 5000:
                    record.capacity_status = "medium_duty"
                else:
                    record.capacity_status = "light_duty"
            else:
                record.capacity_status = "unknown"

    def action_set_available(self):
        """Mark vehicle as available"""
        self.write({"status": "available"})

    def action_set_in_use(self):
        """Mark vehicle as in use"""
        self.write({"status": "in_use"})

    def action_set_maintenance(self):
        """Mark vehicle for maintenance"""
        self.write({"status": "maintenance"})

    def action_view_pickup_routes(self):
        """View pickup routes for this vehicle"""
        action = self.env.ref("records_management.action_pickup_request").read()[0]
        action["domain"] = [("vehicle_id", "=", self.id)]
        action["context"] = {"default_vehicle_id": self.id}
        return action
