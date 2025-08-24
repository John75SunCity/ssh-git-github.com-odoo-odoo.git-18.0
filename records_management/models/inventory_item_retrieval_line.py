from odoo import models, fields, api

class InventoryItemRetrievalLine(models.Model):
    _name = 'inventory.item.retrieval.line'
    _description = 'Inventory Item Retrieval Line'

    retrieval_id = fields.Many2one('inventory.item.retrieval', string='Retrieval', required=True, ondelete='cascade')
    item_id = fields.Many2one('inventory.item', string='Inventory Item', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    location_id = fields.Many2one('records.location', string='Location')
    notes = fields.Text(string='Notes')
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('retrieved', 'Retrieved'),
        ('not_found', 'Not Found')
    ], string='Status', default='pending')
    retrieval_date = fields.Datetime(string='Retrieval Date')
    responsible_id = fields.Many2one('res.users', string='Retrieved By')
