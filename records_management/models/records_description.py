from odoo import models, fields


class Description(models.Model):
    """
    Represents a description entity in the Records Management system.

    This model provides a way to store and manage descriptive text
    that can be referenced by other models in the system for
    standardized descriptions, templates, or categorization.

    Fields:
        name (Char): Name/title of the description.
        description (Text): The actual descriptive text content.
        category (Selection): Category type of the description.
        active (Boolean): Active flag for archiving/deactivation.
        company_id (Many2one): Company context for multi-company support.
    """

    _name = "records.description"
    _description = "Description"
    _order = "name"

    name = fields.Char(string="Title", required=True)
    description_text = fields.Text(string="Description", required=True)
    category = fields.Selection(
        [
            ("general", "General"),
            ("template", "Template"),
            ("instruction", "Instruction"),
            ("policy", "Policy"),
            ("other", "Other"),
        ],
        string="Category",
        default="general",
        required=True,
    )
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company, required=True)
