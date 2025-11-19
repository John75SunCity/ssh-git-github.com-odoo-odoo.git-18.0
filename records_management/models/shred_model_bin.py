from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# Note: Translation warnings during module loading are expected
# for constraint definitions - this is non-blocking behavior



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
        help="Unique barcode for bin identification (replacing old 10-digit system)",
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
    location_id = fields.Many2one("stock.location", string="Location", tracking=True)
    last_emptied = fields.Date(string="Last Emptied", tracking=True)
    notes = fields.Text(string="Notes")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        readonly=True,
    )

    # ============================================================================
    # CONSTRAINTS & VALIDATION
    # ============================================================================
    # SQL constraints
    _sql_constraints = [
        ('barcode_unique', 'unique(barcode)', 'Barcode must be unique across all bins'),
    ]

    @api.constrains("barcode")
    def _check_barcode_format(self):
        """Validate barcode format and uniqueness"""
        for record in self:
            if record.barcode:
                # Check if barcode contains only valid characters (flexible for new system)
                if not record.barcode.replace("-", "").replace("_", "").isalnum():
                    raise ValidationError(_("Barcode can only contain letters, numbers, hyphens, and underscores"))

                if len(record.barcode) < 3:
                    raise ValidationError(_("Barcode must be at least 3 characters long"))

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
