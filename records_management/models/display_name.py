from odoo import models, fields, _

class DisplayName(models.Model):
    """
    Represents a display name configuration in the Records Management system.

    This model provides configurable display name templates and formats
    for various entities in the system, allowing standardization and
    customization of how names are displayed across the application.

    Fields:
        name (Char): Template name/identifier.
        pattern (Char): Display name pattern/template.
        model_name (Char): Target model for this display pattern.
        description (Text): Description of the display name template.
        active (Boolean): Active flag for archiving/deactivation.
        company_id (Many2one): Company context for multi-company support.
    """

    _name = 'display_name'
    _description = 'Display Name Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    pattern = fields.Char(string='Display Pattern', required=True,
                         help='Use {field_name} placeholders for dynamic fields')
    model_name = fields.Char(string='Target Model', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company.id, required=True)

    _name_model_unique = models.Constraint('unique(name, model_name, company_id)',
         "Template name must be unique per model and company.")
