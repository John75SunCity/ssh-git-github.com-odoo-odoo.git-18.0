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
    name = fields.Char(string="Name", required=True, tracking=True, index=True),
    description = fields.Text(string="Description"),
    sequence = fields.Integer(string="Sequence", default=10)

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ]),
        string="Vehicle State",  # Changed to avoid conflict with status field
        default="draft",
        tracking=True,
    )

    # Company and User
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    ),
    user_id = fields.Many2one(
        "res.users", string="Vehicle Manager", default=lambda self: self.env.user
    )

    # Timestamps
    )
    date_created = fields.Datetime(
        string="Vehicle Created Date", default=fields.Datetime.now
    ),
    date_modified = fields.Datetime(string="Modified Date")

    # Control Fields
    active = fields.Boolean(string="Active", default=True),
    notes = fields.Text(string="Internal Notes")

    # Vehicle Details
    vin = fields.Char(
        string="VIN", tracking=True, help="Vehicle Identification Number."
    )
    )
    license_plate = fields.Char(string="License Plate", required=True, tracking=True),
    driver_id = fields.Many2one(
        "hr.employee",
        string="Driver",
        tracking=True,
        help="Assigned driver for the vehicle.",
    )
    driver_contact = fields.Char(
        related="driver_id.mobile_phone", string="Driver Contact", readonly=True)
    vehicle_type = fields.Selection(
        [("truck", "Truck"), ("van", "Van"), ("car", "Car")],
        string="Vehicle Type",
        default="truck",
        tracking=True,
    )

    # Capacity
    )
    total_capacity = fields.Float(string="Total Capacity (cubic meters)", tracking=True)
    max_boxes = fields.Integer(
        string="Max Boxes",
        tracking=True,
        help="Maximum number of standard boxes the vehicle can hold.",
    )

    # Maintenance
    )
    last_service_date = fields.Date(string="Last Service Date", tracking=True),
    next_service_date = fields.Date(string="Next Service Date", tracking=True)
    service_notes = fields.Text(string="Service Notes")

    # Status and Route
    status = fields.Selection(
        [
            ("available", "Available"),
            ("in_service", "In Service"),
            ("maintenance", "Under Maintenance"),
        ]),
        string="Service Status",  # Changed to avoid conflict with state field
        default="available",
        tracking=True,
    )
    pickup_route_ids = fields.One2many(
        "pickup.route", "vehicle_id", string="Pickup Routes"
    )

    # Route and Schedule Information (Missing fields from view analysis)
    route_date = fields.Date(string="Route Date", tracking=True),
    start_time = fields.Datetime(string="Start Time", tracking=True)
    vehicle_capacity_volume = fields.Float(
        string="Vehicle Capacity Volume (cubic meters)", tracking=True
    )
    vehicle_capacity_weight = fields.Float(
        string="Vehicle Capacity Weight (kg)", tracking=True
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

    def action_set_available(self):
        """Set vehicle status to available."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot set archived vehicle as available.")
        # Update status and notes
        self.write(
            {
                "status": "available",
                "state": "active",
                "notes": (self.notes or "")
                + _("\nSet to available on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create availability activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Vehicle available: %s") % self.name,
            note=_(
                "Vehicle has been set to available status and is ready for service."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Vehicle set to available status: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Vehicle Available"),
                "message": _("Vehicle %s is now available for service.") % self.name,
                "type": "success",
                "sticky": False,
            },
        }
)
    def action_set_in_use(self):
        """Set vehicle status to in use."""
        self.ensure_one()
        if self.status == "maintenance":
            raise UserError(_("Cannot use vehicle that is under maintenance.")
        # Update status and notes
        self.write(
            {
                "status": "in_service",
                "state": "active",
                "notes": (self.notes or "")
                + _("\nSet to in service on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create in-service activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Vehicle in service: %s") % self.name,
            note=_("Vehicle is currently in service and unavailable for other routes."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Vehicle set to in service: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Vehicle Routes"),
            "res_model": "pickup.route",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("vehicle_id", "=", self.id)],
            "context": {
                "default_vehicle_id": self.id,
                "search_default_vehicle_id": self.id,
            },
        }

    def action_set_maintenance(self):
        """Set vehicle status to maintenance."""
        self.ensure_one()

        # Update status and notes
        self.write(
            {
                "status": "maintenance",
                "state": "inactive",
                "notes": (self.notes or "")
                + _("\nSent for maintenance on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create maintenance activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Vehicle maintenance required: %s") % self.name,
            note=_("Vehicle requires maintenance and is temporarily out of service."),
            user_id=self.user_id.id,
            )
            date_deadline=fields.Date.today() + fields.timedelta(days=3),
        )

        self.message_post(
            body=_("Vehicle sent for maintenance: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Vehicle Maintenance"),
            "res_model": "records.vehicle",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
            "context": {
                "form_view_initial_mode": "edit",
            },
        }

    # === BUSINESS CRITICAL FIELDS ===        "mail.followers", "res_id", string="Followers"
    )
    capacity = fields.Float(string="Capacity", digits=(10, 2)
    fuel_type = fields.Selection(
        [("gas", "Gasoline"), ("diesel", "Diesel"), ("electric", "Electric")],
        string="Fuel Type",
    )
    maintenance_date = fields.Date(string="Last Maintenance"),
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")

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
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = _("New Vehicle")
        return super().create(vals_list)