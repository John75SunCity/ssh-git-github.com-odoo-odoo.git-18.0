# Test file to validate records.location model using Odoo extensions
# Copy-paste the current model here and let extensions suggest fixes

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsLocationTest(models.Model):
    _name = "records.location.test"
    _description = "Test Records Location"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")

    # Location Type - from the error in model_records.xml
    location_type = fields.Selection(
        [
            ("warehouse", "Warehouse"),
            ("office", "Office"),
            ("vault", "Vault"),
            ("archive", "Archive"),
            ("temporary", "Temporary"),
        ],
        string="Location Type",
        required=True,
        tracking=True,
    )

    # Fields referenced in model_records.xml data file
    building = fields.Char(string="Building", tracking=True)
    zone = fields.Char(string="Zone", tracking=True)
    active = fields.Boolean(string="Active", default=True)
    climate_controlled = fields.Boolean(
        string="Climate Controlled", default=False, tracking=True
    )
    access_level = fields.Selection(
        [
            ("public", "Public"),
            ("restricted", "Restricted"),
            ("secure", "Secure"),
            ("confidential", "Confidential"),
        ],
        string="Access Level",
        default="public",
        tracking=True,
    )
    max_capacity = fields.Integer(string="Maximum Capacity", tracking=True)

    # Standard fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )

    # Let Odoo extensions suggest what other fields should be here...
    # Are we missing any critical fields for a location model?
