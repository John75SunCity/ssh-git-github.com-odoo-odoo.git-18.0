from odoo import models, fields, api, _

class RecordsContainerContentLine(models.Model):
    """
    Represents a line item within container content in the Records Management system.

    Each RecordsContainerContentLine provides detailed tracking for individual
    items or documents within a container's content, supporting granular
    inventory management, compliance tracking, and audit trails.

    Fields:
        content_id (Many2one): Reference to the parent container content.
        name (Char): Name/description of the content line item.
        document_type (Char): Type of document or item.
        quantity (Integer): Quantity of items in this line.
        sequence (Integer): Ordering of the line within the content.
        notes (Text): Additional notes or instructions.
        company_id (Many2one): Company context for multi-company support.
        active (Boolean): Active flag for archiving/deactivation.
    """

    _name = 'records.container.content.line'
    _description = 'Records Container Content Line'
    _order = 'sequence, id'

    content_id = fields.Many2one('container.content', string='Container Content', required=True)
    name = fields.Char(string='Item Name', required=True)
    document_type = fields.Char(string='Document Type')
    quantity = fields.Integer(string='Quantity', default=1)
    sequence = fields.Integer(string='Sequence', default=10)
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, required=True)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        (
            'quantity_positive',
            'CHECK(quantity > 0)',
            'Quantity must be positive.'
        ),
    ]
