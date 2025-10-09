from odoo import models, fields, _

class InventoryItemType(models.Model):
    """
    Represents an inventory item type in the Records Management system.

    This model defines different categories or types of inventory items
    that can be managed within the records system, providing classification
    and standardization for inventory management processes.

    Fields:
        name (Char): Name of the inventory item type.
        description (Text): Description of the item type.
        code (Char): Unique code for the item type.
        category (Selection): Category classification.
        active (Boolean): Active flag for archiving/deactivation.
        company_id (Many2one): Company context for multi-company support.
    """

    _name = 'inventory.item.type'
    _description = 'Inventory Item Type'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(string='Type Name', required=True)
    description = fields.Text(string='Description')
    code = fields.Char(string='Type Code', required=True)
    category = fields.Selection([
        ('physical', 'Physical Items'),
        ('digital', 'Digital Assets'),
        ('consumable', 'Consumable Items'),
        ('equipment', 'Equipment'),
        ('document', 'Documents'),
        ('other', 'Other')
    ], string='Category', default='physical', required=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company.id, required=True)

    _code_unique = models.Constraint('unique(code, company_id)', _('Type code must be unique per company.'))
