from odoo import models, fields, _

class PortalRequestLine(models.Model):
    """
    Represents a line item within a portal request in the Records Management system.

    Each PortalRequestLine captures details about individual items requested
    through the customer portal, supporting detailed request tracking,
    fulfillment workflows, and audit trails.

    Fields:
        request_id (Many2one): Reference to the parent portal request.
        item_type (Selection): Type of item being requested.
        description (Char): Description of the requested item.
        quantity (Integer): Quantity requested.
        status (Selection): Status of this line item.
        sequence (Integer): Ordering of the line within the request.
        notes (Text): Additional notes or instructions.
        company_id (Many2one): Company context for multi-company support.
        active (Boolean): Active flag for archiving/deactivation.
    """
    _name = 'portal.request.line'
    _description = 'Portal Request Line'
    _inherit = ['portal.mixin']
    _order = 'sequence, id'

    request_id = fields.Many2one(comodel_name='portal.request', string='Portal Request', required=True)
    item_type = fields.Selection([
        ('document', 'Document'),
        ('container', 'Container'),
        ('report', 'Report'),
        ('service', 'Service'),
        ('other', 'Other')
    ], string='Item Type', default='document', required=True)
    # Batch 3 label disambiguation
    description = fields.Char(string='Line Details', required=True)
    quantity = fields.Integer(string='Quantity', default=1)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company.id, required=True)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('quantity_positive', 'CHECK(quantity > 0)', 'Quantity must be positive.'),
    ]
