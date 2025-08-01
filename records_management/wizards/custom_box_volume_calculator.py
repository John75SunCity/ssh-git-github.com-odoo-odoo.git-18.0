# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CustomBoxVolumeCalculator(models.TransientModel):
    """
    Wizard for calculating standard box equivalents for custom-sized boxes.
    Used by technicians during shredding service to ensure fair pricing based on volume.

    Business Logic:
    - Standard box: 15" x 12" x 10" = 1,800 cubic inches = $6.00 base rate
    - Custom box: Any dimensions converted to equivalent standard boxes
    - Fair pricing: Volume ratio determines multiplier for standard rate
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

    # Standard box reference dimensions (15" x 12" x 10")
    standard_length = fields.Float(
        string="Standard Length (inches)",
        default=15.0,
        readonly=True,
        help="Standard box length: 15 inches",
    )
    standard_width = fields.Float(
        string="Standard Width (inches)",
        default=12.0,
        readonly=True,
        help="Standard box width: 12 inches",
    )
    standard_height = fields.Float(
        string="Standard Height (inches)",
        default=10.0,
        readonly=True,
        help="Standard box height: 10 inches",
    )

    # Volume calculations
    custom_volume = fields.Float(
        string="Custom Box Volume (cubic inches)",
        compute="_compute_volumes",
        store=False,
        help="Volume of the custom box (L×W×H)",
    )
    standard_volume = fields.Float(
        string="Standard Box Volume (cubic inches)",
        compute="_compute_volumes",
        store=False,
        help="Volume of standard box: 1,800 cubic inches",
    )

    # Equivalency calculations
    volume_ratio = fields.Float(
        string="Volume Ratio",
        compute="_compute_equivalency",
        store=False,
        help="How many standard boxes this custom box equals",
    )
    equivalent_boxes = fields.Float(
        string="Equivalent Standard Boxes",
        compute="_compute_equivalency",
        store=False,
        help="Custom box volume expressed as standard box quantity",
    )

    # Pricing fields
    standard_box_rate = fields.Float(
        string="Standard Box Rate ($)",
        default=6.00,
        help='Price charged for one standard size box (15"×12"×10")',
    )
    calculated_price = fields.Float(
        string="Calculated Price ($)",
        compute="_compute_pricing",
        store=False,
        help="Fair price for the custom box based on volume equivalency",
    )

    # Display fields
    custom_dimensions_display = fields.Char(
        string="Custom Dimensions",
        compute="_compute_display_fields",
        help="Formatted display of custom box dimensions",
    )
    standard_dimensions_display = fields.Char(
        string="Standard Dimensions",
        default='15" × 12" × 10"',
        readonly=True,
        help="Standard box dimensions for reference",
    )
    pricing_explanation = fields.Text(
        string="Pricing Explanation",
        compute="_compute_pricing_explanation",
        help="Detailed explanation of how the price was calculated",
    )

    @api.depends(
        "custom_length",
        "custom_width",
        "custom_height",
        "standard_length",
        "standard_width",
        "standard_height",
    )
    def _compute_volumes(self):
        """Calculate volumes for both custom and standard boxes"""
        for record in self:
            # Custom box volume calculation
            if record.custom_length and record.custom_width and record.custom_height:
                record.custom_volume = (
                    record.custom_length * record.custom_width * record.custom_height
                )
            else:
                record.custom_volume = 0

            # Standard box volume calculation (should always be 1,800 cubic inches)
            record.standard_volume = (
                record.standard_length * record.standard_width * record.standard_height
            )

    @api.depends("custom_volume", "standard_volume")
    def _compute_equivalency(self):
        """Calculate how many standard boxes the custom box equals"""
        for record in self:
            if record.standard_volume > 0 and record.custom_volume > 0:
                record.volume_ratio = record.custom_volume / record.standard_volume
                record.equivalent_boxes = round(record.volume_ratio, 2)
            else:
                record.volume_ratio = 0
                record.equivalent_boxes = 0

    @api.depends("equivalent_boxes", "standard_box_rate")
    def _compute_pricing(self):
        """Calculate fair price based on volume equivalency"""
        for record in self:
            if record.equivalent_boxes > 0:
                record.calculated_price = round(
                    record.equivalent_boxes * record.standard_box_rate, 2
                )
            else:
                record.calculated_price = 0.00

    @api.depends("custom_length", "custom_width", "custom_height")
    def _compute_display_fields(self):
        """Create formatted dimension display strings"""
        for record in self:
            if record.custom_length and record.custom_width and record.custom_height:
                record.custom_dimensions_display = f'{record.custom_length}" × {record.custom_width}" × {record.custom_height}"'
            else:
                record.custom_dimensions_display = "Not Set"

    @api.depends(
        "custom_volume",
        "standard_volume",
        "equivalent_boxes",
        "calculated_price",
        "standard_box_rate",
    )
    def _compute_pricing_explanation(self):
        """Generate detailed pricing explanation for technician"""
        for record in self:
            if record.custom_volume > 0 and record.standard_volume > 0:
                explanation = f"""VOLUME-BASED PRICING CALCULATION:

Custom Box: {record.custom_dimensions_display}
Custom Volume: {record.custom_volume:,.0f} cubic inches

Standard Box: {record.standard_dimensions_display}  
Standard Volume: {record.standard_volume:,.0f} cubic inches

Volume Ratio: {record.custom_volume:,.0f} ÷ {record.standard_volume:,.0f} = {record.volume_ratio:.3f}
Equivalent Boxes: {record.equivalent_boxes} standard boxes

Price Calculation:
{record.equivalent_boxes} boxes × ${record.standard_box_rate:.2f} = ${record.calculated_price:.2f}

This ensures fair pricing based on actual volume of material to be shredded."""
                record.pricing_explanation = explanation
            else:
                record.pricing_explanation = (
                    "Enter custom box dimensions to see pricing calculation."
                )

    @api.constrains("custom_length", "custom_width", "custom_height")
    def _check_dimensions(self):
        """Validate that dimensions are reasonable"""
        for record in self:
            if record.custom_length and (
                record.custom_length <= 0 or record.custom_length > 100
            ):
                raise ValidationError(
                    _("Custom length must be between 0 and 100 inches.")
                )
            if record.custom_width and (
                record.custom_width <= 0 or record.custom_width > 100
            ):
                raise ValidationError(
                    _("Custom width must be between 0 and 100 inches.")
                )
            if record.custom_height and (
                record.custom_height <= 0 or record.custom_height > 100
            ):
                raise ValidationError(
                    _("Custom height must be between 0 and 100 inches.")
                )

    def action_apply_to_service(self):
        """Apply calculated pricing to parent shredding service"""
        self.ensure_one()

        if not all([self.custom_length, self.custom_width, self.custom_height]):
            raise UserError(_("Please enter all box dimensions before applying."))

        if self.equivalent_boxes <= 0:
            raise UserError(
                _("Invalid box dimensions. Please check your measurements.")
            )

        # Return calculated values to be used by calling wizard/form
        return {
            "type": "ir.actions.act_window_close",
            "infos": {
                "equivalent_boxes": self.equivalent_boxes,
                "calculated_price": self.calculated_price,
                "custom_dimensions": self.custom_dimensions_display,
                "volume_ratio": self.volume_ratio,
                "pricing_explanation": self.pricing_explanation,
            },
        }

    def action_recalculate(self):
        """Force recalculation of all computed fields"""
        self.ensure_one()
        # Trigger recomputation by invalidating cache
        self.invalidate_cache()
        return {"type": "ir.actions.do_nothing"}

    def action_reset(self):
        """Reset all input fields to start over"""
        self.ensure_one()
        self.write(
            {
                "custom_length": 0,
                "custom_width": 0,
                "custom_height": 0,
                "standard_box_rate": 6.00,
            }
        )
        return {"type": "ir.actions.do_nothing"}
