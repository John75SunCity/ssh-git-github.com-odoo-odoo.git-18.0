from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# Note: Translation warnings during module loading are expected
# for constraint definitions - this is non-blocking behavior



class PaperModelBale(models.Model):
    """Paper Bale Model for Records Management"""

    _name = "paper.model_bale"
    _description = "Paper Bale Model"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True, tracking=True)
    bale_number = fields.Char(
        string="Bale Number", required=True, index=True, tracking=True, help="Sequential bale number for identification"
    )
    weight = fields.Float(string="Weight (lbs)", tracking=True)
    volume = fields.Float(string="Volume (cu ft)", tracking=True)
    material_type = fields.Selection(
        [("white", "WHITE"), ("mixed", "MIXED"), ("cardboard", "CARDBOARD"), ("trash", "TRASH")],
        string="Material Type",
        default="mixed",
        tracking=True,
        help="Paper grade classification for recycling",
    )
    date_created = fields.Date(string="Date Created", default=fields.Date.today, tracking=True)
    location_id = fields.Many2one("records.location", string="Location", tracking=True)
    notes = fields.Text(string="Notes")

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    # Migrated from _sql_constraints (Odoo 18) to models.Constraint (Odoo 19)
    _bale_number_unique = models.Constraint(
        'UNIQUE(bale_number)',
        "Bale number must be unique across all bales.",
    )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("bale_number")
    def _check_bale_number_format(self):
        """Validate bale number format."""
        for record in self:
            if record.bale_number and not record.bale_number.strip():
                raise ValidationError("Bale number cannot be empty")

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    # (Removed barcode-related onchange methods as we're using sequential numbering)

    # ============================================================================
    # CONFIGURATOR INTEGRATION
    # ============================================================================
    @api.model
    def _is_feature_enabled(self, feature_key):
        """Check if a feature is enabled in RM Module Configurator."""
        return self.env["rm.module.configurator"].is_feature_enabled(feature_key)

    @api.model
    def is_paper_bale_enabled(self):
        """Check if paper bale functionality is enabled."""
        return self._is_feature_enabled("paper_model_bale_enabled")

    @api.model
    def is_weight_tracking_enabled(self):
        """Check if weight tracking is enabled."""
        return self._is_feature_enabled("paper_bale_weight_tracking_enabled")

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("paper.model_bale") or "BALE/%s" % vals.get(
                    "bale_number", "NEW"
                )
        return super().create(vals_list)
