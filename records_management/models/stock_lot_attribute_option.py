from odoo import models, fields, _

class StockLotAttributeOption(models.Model):
    _name = 'stock.lot.attribute.option'
    _description = 'Stock Lot Attribute Option'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Option Name", required=True, translate=True)
    sequence = fields.Integer(default=10)
    attribute_id = fields.Many2one(
        'stock.lot.attribute',
        string="Attribute",
        required=True,
        ondelete='cascade'
    )

    # SQL constraints
    _sql_constraints = [
        ('name_attribute_uniq', 'unique(name, attribute_id)', 'Option names must be unique per attribute.'),
        ('value_attribute_uniq', 'unique(value, attribute_id)', 'Option values must be unique per attribute.'),
    ]
    _name_attribute_uniq = models.Constraint(
        'UNIQUE(name, attribute_id)',
        "Options must be unique per attribute!",
    )
