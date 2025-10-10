from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# Note: Translation warnings during module loading are expected
# for constraint definitions - this is non-blocking behavior



class StockLotAttribute(models.Model):
    _name = 'stock.lot.attribute'
    _description = 'Stock Lot Attribute'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Attribute Name", required=True, tracking=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    attribute_type = fields.Selection([
        ('char', 'Text (Single Line)'),
        ('text', 'Text (Multi-Line)'),
        ('integer', 'Number (Integer)'),
        ('float', 'Number (Decimal)'),
        ('boolean', 'Yes/No'),
        ('date', 'Date'),
        ('datetime', 'Date & Time'),
        ('selection', 'Selection')
    ], string="Type", required=True, default='char', tracking=True)
    description = fields.Text(string="Description")
    required = fields.Boolean(string="Required for Lot")

    selection_option_ids = fields.One2many('stock.lot.attribute.option', 'attribute_id', string="Selection Options")
    option_count = fields.Integer(compute='_compute_option_count', string="Option Count")

    # SQL constraints
    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 'Attribute names must be unique per company.'),
        ('technical_name_company_uniq', 'unique(technical_name, company_id)', 'Technical names must be unique per company.'),
    ]

    # ============================================================================
    # METHODS
    # ============================================================================
    @api.depends('selection_option_ids')
    def _compute_option_count(self):
        for attribute in self:
            attribute.option_count = len(attribute.selection_option_ids)

    @api.constrains('attribute_type', 'selection_option_ids')
    def _check_attribute_type_consistency(self):
        for record in self:
            if record.attribute_type == 'selection' and not record.selection_option_ids:
                raise ValidationError(_("Selection type attributes must have at least one option defined."))
            if record.attribute_type != 'selection' and record.selection_option_ids:
                raise ValidationError(_("Only 'Selection' type attributes can have options."))

    def copy(self, default=None):
        default = dict(default or {})
        if 'name' not in default:
            default['name'] = _("%s (Copy)", self.name)
        return super().copy(default)
