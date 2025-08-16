# -*- coding: utf-8 -*-
"""
Records Vehicle Management Module

This module provides comprehensive vehicle management functionality for the Records Management
System. It handles vehicle lifecycle, route assignments, maintenance tracking, and dr    pickup_route_ids = fields.One2many(
        "fsm.route",
        "vehicle_id",
        string="Pickup Routes",
        help="Routes assigned to this vehicle",
    )anagement with full integration to the pickup and delivery workflow system.

Key Features:
- Complete vehicle lifecycle management from registration to retirement
- Driver assignment and contact management with HR employee integration
- Capacity planning with volume and weight constraints
- Maintenance scheduling with service date tracking and alerts
- Route assignment integration with pickup.route model
- Real-time status tracking (available, in service, maintenance)
- Activity-based workflow management with stakeholder notifications

Business Processes:
1. Vehicle Registration: Register vehicles with specifications and capacity details
2. Driver Assignment: Assign HR employees as drivers with contact integration
3. Route Planning: Assign vehicles to pickup routes based on capacity and availability
4. Status Management: Track real-time vehicle status and availability
5. Maintenance scheduling: Schedule and track vehicle maintenance activities
6. Performance Monitoring: Monitor vehicle utilization and service metrics

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""
# Python stdlib imports
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsVehicle(models.Model):
    _name = "records.vehicle"
    _description = "Records Vehicle Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Vehicle Name",
        required=True,
        tracking=True,
        index=True,
        help="Name or identifier for this vehicle",
    )
    description = fields.Text(
        string="Description", help="Detailed description of the vehicle"
    )
    sequence = fields.Integer(
        string="Sequence", default=10, help="Display order for vehicles"
    )

    # ============================================================================
    # FRAMEWORK FIELDS
    # ============================================================================
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
        help="User responsible for this vehicle",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record",
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Vehicle State",
        default="draft",
        tracking=True,
        help="Current lifecycle state of the vehicle",
    )
    status = fields.Selection(
        [
            ("available", "Available"),
            ("in_service", "In Service"),
            ("maintenance", "Under Maintenance"),
        ],
        string="Service Status",
        default="available",
        tracking=True,
        help="Current operational status of the vehicle",
    )

    # ============================================================================
    # VEHICLE IDENTIFICATION
    # ============================================================================
    vin = fields.Char(
        string="VIN", tracking=True, help="Vehicle Identification Number"
    )
    license_plate = fields.Char(
        string="License Plate",
        required=True,
        tracking=True,
        index=True,
        help="Vehicle license plate number",
    )

    # ============================================================================
    # VEHICLE SPECIFICATIONS
    # ============================================================================
    vehicle_type = fields.Selection(
        [
            ("truck", "Truck"),
            ("van", "Van"),
            ("car", "Car"),
            ("trailer", "Trailer"),
        ],
        string="Vehicle Type",
        default="truck",
        tracking=True,
        help="Type of vehicle for capacity planning",
    )
    fuel_type = fields.Selection(
        [
            ("gas", "Gasoline"),
            ("diesel", "Diesel"),
            ("electric", "Electric"),
            ("hybrid", "Hybrid"),
        ],
        string="Fuel Type",
        default="diesel",
        tracking=True,
        help="Fuel type for cost tracking",
    )

    # ============================================================================
    # CAPACITY SPECIFICATIONS
    # ============================================================================
    total_capacity = fields.Float(
        string="Total Capacity (cubic meters)",
        tracking=True,
        digits=(10, 2),
        help="Total cargo volume capacity",
    )
    vehicle_capacity_volume = fields.Float(
        string="Volume Capacity (m³)",
        tracking=True,
        digits=(10, 2),
        help="Maximum volume capacity in cubic meters",
    )
    vehicle_capacity_weight = fields.Float(
        string="Weight Capacity (kg)",
        tracking=True,
        digits=(10, 2),
        help="Maximum weight capacity in kilograms",
    )
    max_boxes = fields.Integer(
        string="Max Boxes", tracking=True, help="Maximum number of standard boxes"
    )

    # ============================================================================
    # PHYSICAL DIMENSIONS
    # ============================================================================
    length = fields.Float(
        string="Length (m)", digits=(10, 2), help="Vehicle length in meters"
    )
    width = fields.Float(
        string="Width (m)", digits=(10, 2), help="Vehicle width in meters"
    )
    height = fields.Float(
        string="Height (m)", digits=(10, 2), help="Vehicle height in meters"
    )

    # ============================================================================
    # DRIVER MANAGEMENT
    # ============================================================================
    driver_id = fields.Many2one(
        "hr.employee",
        string="Assigned Driver",
        tracking=True,
        help="Primary driver assigned to this vehicle",
    )
    driver_contact = fields.Char(
        related="driver_id.mobile_phone",
        string="Driver Contact",
        readonly=True,
        help="Driver's mobile phone number",
    )

    # ============================================================================
    # MAINTENANCE TRACKING
    # ============================================================================
    last_service_date = fields.Date(
        string="Last Service Date",
        tracking=True,
        help="Date of last maintenance service",
    )
    next_service_date = fields.Date(
        string="Next Service Date",
        tracking=True,
        help="Scheduled next maintenance date",
    )
    maintenance_date = fields.Date(
        string="Last Maintenance",
        tracking=True,
        help="Date of most recent maintenance",
    )
    service_notes = fields.Text(
        string="Service Notes", help="Notes about maintenance and service history"
    )

    # ============================================================================
    # ROUTE AND SCHEDULING
    # ============================================================================
    route_date = fields.Date(
        string="Route Date",
        tracking=True,
        help="Date for current or next route assignment",
    )
    start_time = fields.Datetime(
        string="Start Time", tracking=True, help="Start time for current route"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    pickup_route_ids = fields.One2many(
        "pickup.route",
        "vehicle_id",
        string="Pickup Routes",
        help="Routes assigned to this vehicle",
    )

    # ============================================================================
    # AUDIT AND TRACKING
    # ============================================================================
    created_date = fields.Datetime(
        string="Created Date",
        default=fields.Datetime.now,
        readonly=True,
        help="Record creation timestamp",
    )
    updated_date = fields.Datetime(
        string="Updated Date", readonly=True, help="Last update timestamp"
    )

    # ============================================================================
    # DOCUMENTATION
    # ============================================================================
    notes = fields.Text(
        string="Internal Notes", help="Internal notes and comments about the vehicle"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Formatted display name with license plate",
    )
    capacity = fields.Float(
        string="Capacity",
        compute="_compute_capacity",
        store=True,
        digits=(10, 2),
        help="Primary capacity measure",
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities"
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    fuel_capacity = fields.Float(string="Fuel Capacity", default=0.0, help="Fuel tank capacity")
    maintenance_due_date = fields.Char(string="Maintenance Due Date", help="Next maintenance due date")
    insurance_expiry = fields.Char(string="Insurance Expiry", help="Insurance expiry date")
    registration_number = fields.Char(string="Registration Number", help="Vehicle registration number")
    Vehicles = fields.Char(string='Vehicles')
    action_set_available = fields.Char(string='Action Set Available')
    action_set_in_use = fields.Char(string='Action Set In Use')
    action_set_maintenance = fields.Char(string='Action Set Maintenance')
    available = fields.Char(string='Available')
    group_driver = fields.Char(string='Group Driver')
    group_status = fields.Selection([], string='Group Status')  # TODO: Define selection options
    group_type = fields.Selection([], string='Group Type')  # TODO: Define selection options
    help = fields.Char(string='Help')
    in_use = fields.Char(string='In Use')
    maintenance = fields.Char(string='Maintenance')
    res_model = fields.Char(string='Res Model')
    routes = fields.Char(string='Routes')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("name", "license_plate")
    def _compute_display_name(self):
        """Compute formatted display name with license plate"""
        for record in self:
            if record.license_plate:
                record.display_name = _(
                    "%s [%s]", record.name or "Unknown", record.license_plate
                )
            else:
                record.display_name = record.name or "New Vehicle"

    @api.depends("total_capacity", "vehicle_capacity_volume")
    def _compute_capacity(self):
        """Compute primary capacity measure"""
        for record in self:
            record.capacity = (
                record.total_capacity or record.vehicle_capacity_volume or 0.0
            )

    # ============================================================================
    # ODOO FRAMEWORK METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values and generate sequence"""
        for vals in vals_list:
            if not vals.get("name"):
                sequence = self.env["ir.sequence"].next_by_code("records.vehicle")
                vals["name"] = sequence or _(
                    "Vehicle-%s", fields.Date.today().strftime("%Y%m%d")
                )
            vals["created_date"] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        """Override write to update modification timestamps"""
        vals["updated_date"] = fields.Datetime.now()
        return super().write(vals)

    def name_get(self):
        """Custom name display with license plate"""
        result = []
        for record in self:
            name = record.name
            if record.license_plate:
                name = _("%s [%s]", name, record.license_plate)
            if record.vehicle_type:
                name = _("%s (%s)", name, record.vehicle_type)
            result.append((record.id, name))
        return result

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate the vehicle"""
        self.ensure_one()
        self.write({"state": "active", "status": "available"})
        self.message_post(body=_("Vehicle activated and set to available"))

    def action_deactivate(self):
        """Deactivate the vehicle"""
        self.ensure_one()
        self.write({"state": "inactive", "status": "maintenance"})
        self.message_post(body=_("Vehicle deactivated"))

    def action_archive(self):
        """Archive the vehicle"""
        self.ensure_one()
        self.write({"state": "archived", "active": False})
        self.message_post(body=_("Vehicle archived"))

    def action_set_available(self):
        """Set vehicle status to available"""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot set archived vehicle as available"))
        timestamp = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.write(
            {
                "status": "available",
                "state": "active",
                "notes": (self.notes or "")
                + _("\nSet to available on %s", timestamp),
            }
        )
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Vehicle Available: %s", self.name),
            note=_(
                "Vehicle has been set to available status and is ready for service."
            ),
            user_id=self.user_id.id,
        )
        self.message_post(
            body=_("Vehicle set to available status: %s", self.name),
            message_type="notification",
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Vehicle Available"),
                "message": _("Vehicle %s is now available for service.", self.name),
                "type": "success",
                "sticky": False,
            },
        }

    def action_set_in_service(self):
        """Set vehicle status to in service"""
        self.ensure_one()
        if self.status == "maintenance":
            raise UserError(_("Cannot use vehicle that is under maintenance"))
        timestamp = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.write(
            {
                "status": "in_service",
                "state": "active",
                "notes": (self.notes or "")
                + _("\nSet to in service on %s", timestamp),
            }
        )
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Vehicle In Service: %s", self.name),
            note=_(
                "Vehicle is currently in service and unavailable for other routes."
            ),
            user_id=self.user_id.id,
        )
        self.message_post(
            body=_("Vehicle set to in service: %s", self.name),
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
        """Set vehicle status to maintenance"""
        self.ensure_one()
        timestamp = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.write(
            {
                "status": "maintenance",
                "state": "inactive",
                "notes": (self.notes or "")
                + _("\nSent for maintenance on %s", timestamp),
            }
        )
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Vehicle Maintenance Required: %s", self.name),
            note=_(
                "Vehicle requires maintenance and is temporarily out of service."
            ),
            user_id=self.user_id.id,
            date_deadline=fields.Date.today() + timedelta(days=3),
        )
        self.message_post(
            body=_("Vehicle sent for maintenance: %s", self.name),
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

    def action_view_routes(self):
        """View routes assigned to this vehicle"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Vehicle Routes"),
            "res_model": "fsm.route",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("vehicle_id", "=", self.id)],
            "context": {
                "default_vehicle_id": self.id,
                "search_default_vehicle_id": self.id,
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("license_plate")
    def _check_license_plate_unique(self):
        """Ensure license plates are unique per company"""
        for record in self:
            if record.license_plate:
                existing = self.search(
                    [
                        ("license_plate", "=", record.license_plate),
                        ("company_id", "=", record.company_id.id),
                        ("id", "!=", record.id),
                    ]
                )
                if existing:
                    raise ValidationError(
                        _("License plate must be unique within the company")
                    )

    @api.constrains(
        "total_capacity",
        "vehicle_capacity_volume",
        "vehicle_capacity_weight",
        "max_boxes",
    )
    def _check_capacity_values(self):
        """Validate capacity values are positive"""
        for record in self:
            if any(
                val < 0
                for val in [
                    record.total_capacity or 0,
                    record.vehicle_capacity_volume or 0,
                    record.vehicle_capacity_weight or 0,
                    record.max_boxes or 0,
                ]
            ):
                raise ValidationError(_("Capacity values must be positive"))

    @api.constrains("length", "width", "height")
    def _check_dimensions(self):
        """Validate vehicle dimensions are positive"""
        for record in self:
            if any(
                val < 0
                for val in [record.length or 0, record.width or 0, record.height or 0]
            ):
                raise ValidationError(_("Vehicle dimensions must be positive"))

    @api.constrains("next_service_date", "last_service_date")
    def _check_service_dates(self):
        """Validate service date logic"""
        for record in self:
            if (
                record.next_service_date
                and record.last_service_date
                and record.next_service_date <= record.last_service_date
            ):
                raise ValidationError(
                    _("Next service date must be after last service date")
                )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_available_capacity(self):
        """Get available capacity information"""
        self.ensure_one()
        return {
            "volume": self.vehicle_capacity_volume or self.total_capacity or 0,
            "weight": self.vehicle_capacity_weight or 0,
            "boxes": self.max_boxes or 0,
            "is_available": self.status == "available" and self.state == "active",
        }

    def is_maintenance_due(self):
        """Check if vehicle is due for maintenance"""
        self.ensure_one()
        if not self.next_service_date:
            return False
        return fields.Date.today() >= self.next_service_date

    @api.model
    def cron_check_maintenance_due(self):
        """Cron job to check maintenance schedules and create activities for due vehicles"""
        due_vehicles = self.search(
            [
                ("next_service_date", "<=", fields.Date.today()),
                ("status", "!=", "maintenance"),
                ("state", "=", "active"),
            ]
        )
        for vehicle in due_vehicles:
            vehicle.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Maintenance Due: %s", vehicle.name),
                note=_(
                    "Vehicle maintenance is due based on the scheduled service date."
                ),
                user_id=vehicle.user_id.id,
                date_deadline=fields.Date.today(),
            )

    @api.depends('vehicle_capacity_weight')
    def _compute_capacity_status(self):
        """Compute vehicle capacity status"""
        for record in self:
            if record.vehicle_capacity_weight:
                if record.vehicle_capacity_weight >= 10000:
                    record.capacity_status = 'heavy_duty'
                elif record.vehicle_capacity_weight >= 5000:
                    record.capacity_status = 'medium_duty'
                else:
                    record.capacity_status = 'light_duty'
            else:
                record.capacity_status = 'unknown'
