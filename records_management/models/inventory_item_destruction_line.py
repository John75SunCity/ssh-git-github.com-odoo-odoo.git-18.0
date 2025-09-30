from odoo import models, fields

class InventoryItemDestructionLine(models.Model):
    _name = 'inventory.item.destruction.line'
    _description = 'Inventory Item Destruction Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    destruction_id = fields.Many2one(comodel_name='inventory.item.destruction', string='Destruction', required=True, ondelete='cascade')
    item_id = fields.Many2one(comodel_name='inventory.item', string='Inventory Item', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    location_id = fields.Many2one(comodel_name='records.location', string='Location')
    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('incineration', 'Incineration'),
        ('physical', 'Physical Destruction'),
        ('other', 'Other')
    ], string='Destruction Method', default='shredding')
    certificate_number = fields.Char(string='Certificate Number')
    notes = fields.Text(string='Notes')
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('destroyed', 'Destroyed'),
        ('certified', 'Certified')
    ], string='Status', default='pending')
    destruction_date = fields.Datetime(string='Destruction Date')
    responsible_id = fields.Many2one(comodel_name='res.users', string='Destroyed By')
