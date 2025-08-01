# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsVehicle(models.Model):
    _name = "records.vehicle"
    _description = "Records Vehicle"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Company and User
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Assigned User", default=lambda self: self.env.user
    )

    # Timestamps
    date_created = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    date_modified = fields.Datetime(string="Modified Date")

    # Control Fields
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Internal Notes")

    # Vehicle Details
    vin = fields.Char(
        string="VIN", tracking=True, help="Vehicle Identification Number."
    )
    license_plate = fields.Char(string="License Plate", required=True, tracking=True)
    driver_id = fields.Many2one(
        "hr.employee",
        string="Driver",
        tracking=True,
        help="Assigned driver for the vehicle.",
    )
    driver_contact = fields.Char(
        related="driver_id.mobile_phone", string="Driver Contact", readonly=True
    )
    vehicle_type = fields.Selection(
        [("truck", "Truck"), ("van", "Van"), ("car", "Car")],
        string="Vehicle Type",
        default="truck",
        tracking=True,
    )

    # Capacity
    total_capacity = fields.Float(string="Total Capacity (cubic meters)", tracking=True)
    max_boxes = fields.Integer(
        string="Max Boxes",
        tracking=True,
        help="Maximum number of standard boxes the vehicle can hold.",
    )

    # Maintenance
    last_service_date = fields.Date(string="Last Service Date", tracking=True)
    next_service_date = fields.Date(string="Next Service Date", tracking=True)
    service_notes = fields.Text(string="Service Notes")

    # Status and Route
    status = fields.Selection(
        [
            ("available", "Available"),
            ("in_service", "In Service"),
            ("maintenance", "Under Maintenance"),
        ],
        string="Operational Status",
        default="available",
        tracking=True,
    )
    pickup_route_ids = fields.One2many(
        "pickup.route", "vehicle_id", string="Pickup Routes"
    )

    # Dimensions
    length = fields.Float("Length (m)")
    width = fields.Float("Width (m)")
    height = fields.Float("Height (m)")

    # Computed Fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )

    @api.depends("name", "license_plate")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = (
                f"{record.name} [{record.license_plate or 'No Plate'}]"
            )

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()
        return super().write(vals)

    def action_activate(self):
        """Activate the record."""
        self.write({"state": "active", "status": "available"})

    def action_deactivate(self):
        """Deactivate the record."""
        self.write({"state": "inactive", "status": "maintenance"})

    def action_archive(self):
        """Archive the record."""
        self.write({"state": "archived", "active": False})

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values."""
        # Handle both single dict and list of dicts
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = _("New Vehicle")

        return super().create(vals_list)
