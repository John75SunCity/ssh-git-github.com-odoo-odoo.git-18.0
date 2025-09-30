from odoo import models, fields

class InventoryItemRetrievalLine(models.Model):
    _name = 'inventory.item.retrieval.line'
    _description = 'Inventory Item Retrieval Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    retrieval_id = fields.Many2one(comodel_name='inventory.item.retrieval', string='Retrieval', required=True, ondelete='cascade')
    item_id = fields.Many2one(comodel_name='inventory.item', string='Inventory Item', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    location_id = fields.Many2one(comodel_name='records.location', string='Location')
    notes = fields.Text(string='Notes')
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('retrieved', 'Retrieved'),
        ('not_found', 'Not Found')
    ], string='Status', default='pending')
    retrieval_date = fields.Datetime(string='Retrieval Date')
    responsible_id = fields.Many2one(comodel_name='res.users', string='Retrieved By')
