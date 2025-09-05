from odoo import models, fields

class InventoryItemProfile(models.Model):
    """
    Represents an inventory item profile in the Records Management system.

    Each InventoryItemProfile defines templates or categories for inventory
    items, providing standardized configurations for different types of
    items managed within the records system.

    Fields:
        name (Char): Name of the inventory item profile.
        description (Text): Description of the profile.
        item_type (Selection): Type of inventory item.
        default_location_id (Many2one): Default storage location.
        retention_period (Integer): Default retention period in days.
        active (Boolean): Active flag for archiving/deactivation.
        company_id (Many2one): Company context for multi-company support.
    """

    _name = 'inventory.item.profile'
    _description = 'Inventory Item Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Profile Name', required=True)
    description = fields.Text(string='Description')
    item_type = fields.Selection([
        ('document', 'Document'),
        ('container', 'Container'),
        ('media', 'Media'),
        ('equipment', 'Equipment'),
        ('other', 'Other')
    ], string='Item Type', default='document', required=True)
    default_location_id = fields.Many2one('records.location', string='Default Location')
    retention_period = fields.Integer(string='Retention Period (Days)', default=365)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, required=True)

    _sql_constraints = [
        (
            'retention_period_positive',
            'CHECK(retention_period > 0)',
            'Retention period must be positive.'
        ),
    ]
