# Custom Box Volume Calculator Design
# Using Odoo Extensions for Validation

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class CustomBoxVolumeCalculator(models.TransientModel):
    """
    Wizard for calculating standard box equivalents for custom-sized boxes
    Used by technicians during shredding service to ensure fair pricing
    """

    _name = "custom.box.volume.calculator"
    _description = "Custom Box Volume Calculator"

    # Input fields for custom box dimensions
    custom_length = fields.Float(
        string="Custom Length (inches)",
        required=True,
        help="Length of the custom box in inches",
    )
    custom_width = fields.Float(
        string="Custom Width (inches)",
        required=True,
        help="Width of the custom box in inches",
    )
    custom_height = fields.Float(
        string="Custom Height (inches)",
        required=True,
        help="Height of the custom box in inches",
    )

    # Standard box reference (15" x 12" x 10")
    standard_length = fields.Float(
        string="Standard Length (inches)", default=15.0, readonly=True
    )
    standard_width = fields.Float(
        string="Standard Width (inches)", default=12.0, readonly=True
    )
    standard_height = fields.Float(
        string="Standard Height (inches)", default=10.0, readonly=True
    )

    # Calculated fields
    custom_volume = fields.Float(
        string="Custom Box Volume (cubic inches)",
        compute="_compute_volumes",
        help="Volume of the custom box",
    )
    standard_volume = fields.Float(
        string="Standard Box Volume (cubic inches)",
        compute="_compute_volumes",
        help='Volume of standard box (15" x 12" x 10")',
    )
    volume_ratio = fields.Float(
        string="Volume Ratio",
        compute="_compute_volume_ratio",
        help="How many standard boxes this custom box equals",
    )
    equivalent_boxes = fields.Float(
        string="Equivalent Standard Boxes",
        compute="_compute_volume_ratio",
        help="Custom box volume expressed as standard box quantity",
    )

    # Pricing calculation
    standard_box_rate = fields.Float(
        string="Standard Box Rate ($)",
        default=6.00,
        help="Price charged for one standard size box",
    )
    calculated_price = fields.Float(
        string="Calculated Price ($)",
        compute="_compute_pricing",
        help="Fair price for the custom box based on volume",
    )

    @api.depends("custom_length", "custom_width", "custom_height")
    def _compute_volumes(self):
        """Calculate volumes for both custom and standard boxes"""
        for record in self:
            # Custom box volume
            if record.custom_length and record.custom_width and record.custom_height:
                record.custom_volume = (
                    record.custom_length * record.custom_width * record.custom_height
                )
            else:
                record.custom_volume = 0

            # Standard box volume (15" x 12" x 10" = 1,800 cubic inches)
            record.standard_volume = (
                record.standard_length * record.standard_width * record.standard_height
            )

    @api.depends("custom_volume", "standard_volume")
    def _compute_volume_ratio(self):
        """Calculate how many standard boxes the custom box equals"""
        for record in self:
            if record.standard_volume > 0:
                record.volume_ratio = record.custom_volume / record.standard_volume
                record.equivalent_boxes = round(record.volume_ratio, 2)
            else:
                record.volume_ratio = 0
                record.equivalent_boxes = 0

    @api.depends("equivalent_boxes", "standard_box_rate")
    def _compute_pricing(self):
        """Calculate fair price based on volume equivalency"""
        for record in self:
            record.calculated_price = round(
                record.equivalent_boxes * record.standard_box_rate, 2
            )

    def action_apply_to_service(self):
        """Apply calculated pricing to shredding service"""
        self.ensure_one()

        if not self.custom_length or not self.custom_width or not self.custom_height:
            raise UserError("Please enter all box dimensions before applying.")

        # Return action to apply to parent shredding service
        return {
            "type": "ir.actions.act_window_close",
            "infos": {
                "equivalent_boxes": self.equivalent_boxes,
                "calculated_price": self.calculated_price,
                "custom_dimensions": f'{self.custom_length}" x {self.custom_width}" x {self.custom_height}"',
                "volume_ratio": self.volume_ratio,
            },
        }
