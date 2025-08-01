# -*- coding: utf-8 -*-
from odoo import models, fields, api


class RecordsContainer(models.Model):
    _name = "records.container"
    _description = "Records Container"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Container Number", required=True)
    container_type = fields.Selection(
        [("box", "Box"), ("file", "File"), ("binder", "Binder")],
        string="Container Type",
        required=True,
    )
    location_id = fields.Many2one("records.location", string="Location")
    customer_id = fields.Many2one("res.partner", string="Customer")
    customer_inventory_id = fields.Many2one(
        "customer.inventory", string="Customer Inventory"
    )
    capacity = fields.Float(string="Capacity")
    current_usage = fields.Float(string="Current Usage")
    creation_date = fields.Date(string="Creation Date", default=fields.Date.today)
    destruction_date = fields.Date(string="Destruction Date")
    state = fields.Selection(
        [("active", "Active"), ("stored", "Stored"), ("destroyed", "Destroyed")],
        default="active",
    )

    # Container Specifications
    max_boxes = fields.Integer(
        string="Maximum Boxes",
        default=50,
        help="Maximum number of boxes this container can hold",
    )
    length = fields.Float(string="Length (cm)", help="Container length in centimeters")
    width = fields.Float(string="Width (cm)", help="Container width in centimeters")
    height = fields.Float(string="Height (cm)", help="Container height in centimeters")
    active = fields.Boolean(
        string="Active", default=True, help="Set to false to hide this container"
    )

    # Computed fields for inch display
    length_inches = fields.Float(
        string="Length (in)",
        compute="_compute_dimensions_inches",
        help="Container length in inches",
    )
    width_inches = fields.Float(
        string="Width (in)",
        compute="_compute_dimensions_inches",
        help="Container width in inches",
    )
    height_inches = fields.Float(
        string="Height (in)",
        compute="_compute_dimensions_inches",
        help="Container height in inches",
    )
    dimensions_display = fields.Char(
        string="Dimensions",
        compute="_compute_dimensions_display",
        help="Formatted dimension display (L×W×H in inches)",
    )
    container_size_type = fields.Selection(
        [
            ("standard", 'Standard (15"×12"×10")'),
            ("legal", 'Legal/Double-size (15"×24"×10")'),
            ("custom", "Custom Size"),
        ],
        string="Container Size Type",
        compute="_compute_container_size_type",
    )

    @api.depends("length", "width", "height")
    def _compute_dimensions_inches(self):
        """Convert centimeter dimensions to inches (1 inch = 2.54 cm)"""
        for record in self:
            cm_to_inch = 1 / 2.54
            record.length_inches = (
                round(record.length * cm_to_inch, 1) if record.length else 0
            )
            record.width_inches = (
                round(record.width * cm_to_inch, 1) if record.width else 0
            )
            record.height_inches = (
                round(record.height * cm_to_inch, 1) if record.height else 0
            )

    @api.depends("length_inches", "width_inches", "height_inches")
    def _compute_dimensions_display(self):
        """Create formatted dimension display string"""
        for record in self:
            if record.length_inches and record.width_inches and record.height_inches:
                record.dimensions_display = f'{record.length_inches}"×{record.width_inches}"×{record.height_inches}"'
            else:
                record.dimensions_display = "Not Set"

    @api.depends("length_inches", "width_inches", "height_inches")
    def _compute_container_size_type(self):
        """Determine if container matches standard sizes"""
        for record in self:
            # Check for standard size: 15"×12"×10"
            if (
                abs(record.length_inches - 15) < 0.5
                and abs(record.width_inches - 12) < 0.5
                and abs(record.height_inches - 10) < 0.5
            ):
                record.container_size_type = "standard"
            # Check for legal/double-size: 15"×24"×10"
            elif (
                abs(record.length_inches - 15) < 0.5
                and abs(record.width_inches - 24) < 0.5
                and abs(record.height_inches - 10) < 0.5
            ):
                record.container_size_type = "legal"
            else:
                record.container_size_type = "custom"

    def action_set_standard_size(self):
        """Set container to standard size: 15"×12"×10" (38.1×30.5×25.4 cm)"""
        self.ensure_one()
        self.write(
            {
                "length": 38.1,  # 15 inches
                "width": 30.5,  # 12 inches
                "height": 25.4,  # 10 inches
            }
        )
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_set_legal_size(self):
        """Set container to legal/double size: 15"×24"×10" (38.1×61×25.4 cm)"""
        self.ensure_one()
        self.write(
            {
                "length": 38.1,  # 15 inches
                "width": 61.0,  # 24 inches
                "height": 25.4,  # 10 inches
            }
        )
        return {"type": "ir.actions.client", "tag": "reload"}
