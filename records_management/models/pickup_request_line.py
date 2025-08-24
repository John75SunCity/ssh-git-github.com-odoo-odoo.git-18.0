from odoo import models, fields, api, _

class PickupRequestLine(models.Model):
    """
    Represents a single line item within a Pickup Request in the Records Management system.

    Each PickupRequestLine links a specific container (records.container) to a pickup request,
    capturing details such as item description, quantity, sequence, and notes. This model is
    used to track the individual containers or items to be picked up as part of a larger
    pickup operation, supporting audit trails, compliance, and operational workflows.

    Fields:
        request_id (Many2one): Reference to the parent Pickup Request.
        container_id (Many2one): The container being picked up.
        item_description (Char): Description of the item or contents.
        quantity (Integer): Number of items/containers for this line.
        sequence (Integer): Ordering of the line within the request.
        notes (Text): Additional notes or instructions.
        company_id (Many2one): Company context for multi-company support.
        active (Boolean): Active flag for archiving/deactivation.
    """

    _name = 'pickup.request.line'
    _description = 'Pickup Request Line'
    _order = 'sequence, id'

    request_id = fields.Many2one('pickup.request', string='Pickup Request', required=True)
    container_id = fields.Many2one('records.container', string='Container', required=True)
    item_description = fields.Char(string='Item Description')
    quantity = fields.Integer(string='Quantity', default=1)
    # The 'sequence' field determines the order of line items within a pickup request.
    # Adjust this value to customize the display or processing order of lines.
    sequence = fields.Integer(string='Sequence', default=10)
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, required=True)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        (
            'quantity_non_negative',
            'CHECK(quantity >= 0)',
            'Quantity must be zero or positive.'
        ),
    ]
