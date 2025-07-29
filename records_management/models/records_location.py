# -*- coding: utf-8 -*-
"""
Records Location Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class RecordsLocation(models.Model):
    """
    Records Location Management
    Physical storage locations for records boxes
    """

    _name = "records.location"
    _description = "Records Location"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string="Location Name", required=True, tracking=True)
    description = fields.Text(string="Description", tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Location Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ==========================================
    # LOCATION HIERARCHY
    # ==========================================
    parent_location_id = fields.Many2one(
        "records.location", string="Parent Location", tracking=True
    )
    child_location_ids = fields.One2many(
        "records.location", "parent_location_id", string="Child Locations"
    )

    location_type = fields.Selection(
        [
            ("warehouse", "Warehouse"),
            ("room", "Room"),
            ("aisle", "Aisle"),
            ("rack", "Rack"),
            ("shelf", "Shelf"),
            ("bin", "Bin"),
        ],
        string="Location Type",
        required=True,
        tracking=True,
    )

    # ==========================================
    # PHYSICAL SPECIFICATIONS
    # ==========================================
    max_capacity = fields.Integer(string="Maximum Capacity (boxes)", tracking=True)
    current_occupancy = fields.Integer(
        string="Current Occupancy", compute="_compute_current_occupancy", store=True
    )
    available_space = fields.Integer(
        string="Available Space", compute="_compute_available_space", store=True
    )

    # Dimensions
    length = fields.Float(string="Length (ft)", tracking=True)
    width = fields.Float(string="Width (ft)", tracking=True)
    height = fields.Float(string="Height (ft)", tracking=True)

    # ==========================================
    # ACCESS AND SECURITY
    # ==========================================
    access_level = fields.Selection(
        [
            ("public", "Public Access"),
            ("restricted", "Restricted Access"),
            ("secure", "Secure Access"),
            ("maximum", "Maximum Security"),
        ],
        string="Access Level",
        default="restricted",
        tracking=True,
    )

    requires_key = fields.Boolean(string="Requires Key Access", tracking=True)
    climate_controlled = fields.Boolean(string="Climate Controlled", tracking=True)
    fire_protected = fields.Boolean(string="Fire Protection", tracking=True)

    # ==========================================
    # LOCATION ADDRESS
    # ==========================================
    building = fields.Char(string="Building", tracking=True)
    floor = fields.Char(string="Floor", tracking=True)
    zone = fields.Char(string="Zone", tracking=True)
    aisle = fields.Char(string="Aisle", tracking=True)
    rack_number = fields.Char(string="Rack Number", tracking=True)
    shelf_number = fields.Char(string="Shelf Number", tracking=True)

    # ==========================================
    # RELATIONSHIPS
    # ==========================================
    container_ids = fields.One2many(
        "records.container", "location_id", string="Stored Containers"
    )

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    container_count = fields.Integer(
        string="Container Count", compute="_compute_container_count", store=True
    )
    capacity = fields.Integer(string="Capacity", related="max_capacity", store=True)
    current_utilization = fields.Float(
        string="Current Utilization (%)",
        compute="_compute_current_utilization",
        store=True,
    )
    available_utilization = fields.Float(
        string="Available Utilization (%)",
        compute="_compute_available_utilization",
        store=True,
    )
    available_spaces = fields.Integer(
        string="Available Spaces", compute="_compute_available_spaces", store=True
    )

    # ==========================================
    # STATUS
    # ==========================================
    status = fields.Selection(
        [
            ("available", "Available"),
            ("occupied", "Occupied"),
            ("full", "Full"),
            ("maintenance", "Under Maintenance"),
            ("inactive", "Inactive"),
        ],
        string="Status",
        default="available",
        tracking=True,
    )

    # ==========================================
    # NOTES
    # ==========================================
    notes = fields.Text(string="Notes", tracking=True)
    special_instructions = fields.Text(string="Special Instructions", tracking=True)
    access_instructions = fields.Text(
        string="Access Instructions",
        tracking=True,
        help="Specific instructions for accessing this location",
    )
    security_level = fields.Selection(
        [
            ("low", "Low Security"),
            ("medium", "Medium Security"),
            ("high", "High Security"),
            ("maximum", "Maximum Security"),
        ],
        string="Security Level",
        default="medium",
        tracking=True,
    )

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends("container_ids")
    def _compute_container_count(self):
        """Calculate total number of containers in this location"""
        for record in self:
            record.container_count = len(record.container_ids)

    @api.depends("container_count", "max_capacity")
    def _compute_current_utilization(self):
        """Calculate current utilization percentage"""
        for record in self:
            if record.max_capacity and record.max_capacity > 0:
                record.current_utilization = (
                    record.container_count / record.max_capacity
                ) * 100
            else:
                record.current_utilization = 0.0

    @api.depends("container_ids")
    def _compute_current_occupancy(self):
        """Calculate current occupancy"""
        for record in self:
            record.current_occupancy = len(
                record.container_ids.filtered(lambda c: c.state == "stored")
            )

    @api.depends("max_capacity", "current_occupancy")
    def _compute_available_space(self):
        """Calculate available space"""
        for record in self:
            if record.max_capacity:
                record.available_space = record.max_capacity - record.current_occupancy
            else:
                record.available_space = 0

    @api.depends("current_utilization")
    def _compute_available_utilization(self):
        """Calculate available utilization percentage"""
        for record in self:
            record.available_utilization = 100.0 - record.current_utilization

    @api.depends("available_space")
    def _compute_available_spaces(self):
        """Calculate available spaces (alias for available_space)"""
        for record in self:
            record.available_spaces = record.available_space

    # ==========================================
    # ACTION METHODS
    # ==========================================
    def action_set_maintenance(self):
        """Set location to maintenance mode"""
        self.ensure_one()
        self.write({"status": "maintenance"})
        self.message_post(body=_("Location set to maintenance mode"))

    def action_set_available(self):
        """Make location available"""
        self.ensure_one()
        self.write({"status": "available"})
        self.message_post(body=_("Location made available"))

    def action_view_containers(self):
        """View containers in this location"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Containers in {self.name}",
            "view_mode": "tree,form",
            "res_model": "records.container",
            "domain": [("location_id", "=", self.id)],
            "context": {"default_location_id": self.id},
        }

    def action_location_report(self):
        """Generate location utilization report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.location_utilization_report",
            "report_type": "qweb-pdf",
            "data": {
                "location_id": self.id,
                "location_name": self.name,
                "container_count": self.container_count,
                "max_capacity": self.max_capacity,
                "current_utilization": self.current_utilization,
                "available_spaces": self.available_spaces,
                "status": self.status,
                "access_level": self.access_level,
            },
            "context": self.env.context,
        }

    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    @api.constrains("max_capacity")
    def _check_max_capacity(self):
        """Validate maximum capacity"""
        for record in self:
            if record.max_capacity and record.max_capacity < 0:
                raise ValidationError(_("Maximum capacity cannot be negative"))

    @api.constrains("length", "width", "height")
    def _check_dimensions(self):
        """Validate dimensions"""
        for record in self:
            if any(
                [
                    record.length and record.length <= 0,
                    record.width and record.width <= 0,
                    record.height and record.height <= 0,
                ]
            ):
                raise ValidationError(_("Dimensions must be positive values"))

    @api.constrains("parent_location_id")
    def _check_parent_location(self):
        """Prevent circular references"""
        for record in self:
            if record.parent_location_id:
                current = record.parent_location_id
                while current:
                    if current == record:
                        raise ValidationError(
                            _("Cannot create circular location hierarchy")
                        )
                    current = current.parent_location_id

    @api.depends("container_count", "max_capacity")
    def _compute_utilization(self):
        """Calculate current utilization percentage"""
        for record in self:
            if record.max_capacity and record.max_capacity > 0:
                record.current_utilization = (
                    record.container_count / record.max_capacity
                ) * 100
            else:
                record.current_utilization = 0.0
