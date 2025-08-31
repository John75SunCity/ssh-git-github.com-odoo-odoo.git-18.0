from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ShredModelBin(models.Model):
    """Shredding Bin Model for Records Management"""

    _name = "shred.model_bin"
    _description = "Shredding Bin Model"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True, tracking=True)
    barcode = fields.Char(
        string="Barcode",
        required=True,
        index=True,
        tracking=True,
        help="Unique 10-digit barcode for bin identification",
    )
    barcode_inventory_id = fields.Many2one(
        comodel_name="bin.barcode.inventory",
        string="Barcode Inventory",
        tracking=True,
        help="Link to barcode inventory record for additional bin details",
    )
    capacity = fields.Float(string="Capacity (lbs)", tracking=True)
    current_weight = fields.Float(string="Current Weight (lbs)", tracking=True)
    material_type = fields.Selection(
        [("wht", "WHT"), ("mix", "MIX"), ("occ", "OCC (Cardboard)"), ("trash", "TRASH")],
        string="Material Type",
        default="wht",
        tracking=True,
        help="Paper grade classification for recycling",
    )
    status = fields.Selection(
        [("empty", "Empty"), ("partial", "Partial"), ("full", "Full"), ("processing", "Processing")],
        string="Status",
        default="empty",
        tracking=True,
    )
    location_id = fields.Many2one("records.location", string="Location", tracking=True)
    last_emptied = fields.Date(string="Last Emptied", tracking=True)
    notes = fields.Text(string="Notes")

    # ============================================================================
    # CONSTRAINTS & VALIDATION
    # ============================================================================
    _sql_constraints = [
        ("barcode_unique", "unique(barcode)", "Barcode must be unique across all bins"),
        ("barcode_length", "length(barcode) >= 10", "Barcode must be at least 10 digits"),
    ]

    @api.constrains("barcode")
    def _check_barcode_format(self):
        """Validate barcode format and uniqueness"""
        for record in self:
            if record.barcode:
                # Check if barcode contains only digits
                if not record.barcode.isdigit():
                    raise ValidationError(_("Barcode must contain only digits"))

                # Check length using Odoo style
                if record.barcode and len(record.barcode) < 10:
                    raise ValidationError(_("Barcode must be at least 10 digits long"))

    @api.onchange("barcode")
    def _onchange_barcode(self):
        """Auto-populate fields when barcode is entered"""
        if self.barcode and self.barcode_inventory_id:
            # If barcode matches inventory record, update related fields
            if self.barcode_inventory_id.barcode == self.barcode:
                # Could auto-populate capacity, material_type, etc. from inventory
                pass

    @api.onchange("barcode_inventory_id")
    def _onchange_barcode_inventory(self):
        """Update barcode when inventory record is selected"""
        if self.barcode_inventory_id and not self.barcode:
            self.barcode = self.barcode_inventory_id.barcode
            # Could also populate capacity, material_type from inventory record

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") and vals.get("barcode"):
                vals["name"] = f"BIN-{vals['barcode']}"
        return super().create(vals_list)
