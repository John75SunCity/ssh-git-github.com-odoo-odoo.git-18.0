from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PickupRequest(models.Model):
    _name = 'pickup.request'
    _description = 'Pickup Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # fields and methods here

    # If you need to access another model, use:
    # self.env['other.model'].search([...])
    """
    PickupRequest Model

    This model represents a request for picking up items by a customer.
    It manages the customer, requested items, request date, and the workflow state.
    Includes validation to ensure data integrity and business logic for state transitions.
    """
    _name = 'pickup.request'
    _description = 'Pickup Request'

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        help="The customer requesting the pickup."
    )
    request_date = fields.Date(
        string='Request Date',
        default=fields.Date.today,
        required=True,
        help="The date when the pickup is requested. Cannot be in the past."
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='draft', string='Status', help="Current status of the pickup request.")
    item_ids = fields.Many2many(
        'stock.lot',
        string='Items',
        domain="[('customer_id', '=', customer_id)]",
        help="Items to be picked up. Only items belonging to the selected customer are allowed."
    )
    
    # One2many relationship with the pickup.request.item model
    request_item_ids = fields.One2many(
        'pickup.request.item',
        'pickup_id',
        string='Request Items'
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        compute='_compute_warehouse',
        store=True
    )
    signature = fields.Binary(string='Signature')
    
    # Additional fields referenced in the view
    scheduled_date = fields.Date(
        string='Scheduled Date',
        help="The date when the pickup is scheduled to occur."
    )
    completion_date = fields.Date(
        string='Completion Date',
        help="The date when the pickup was completed."
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehicle',
        help="The vehicle used for this pickup."
    )
    driver_id = fields.Many2one(
        'res.partner',
        string='Driver',
        domain="[('is_company', '=', False)]",
        help="The driver assigned to this pickup."
    )
    name = fields.Char(
        string='Reference',
        readonly=True,
        default='New',
        copy=False
    )
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High')
    ], default='0', string='Priority')
    notes = fields.Text(string='Notes')
    signed_by = fields.Many2one('res.users', string='Signed By')
    signature_date = fields.Datetime(string='Signature Date')

    @api.depends('item_ids')
    def _compute_warehouse(self):
        """
        Compute the warehouse based on the selected items.
        Sets the warehouse_id field to the warehouse containing all selected items,
        if they are all located in the same warehouse.
        """
        for record in self:
            quants = self.env['stock.quant'].search([
                ('lot_id', 'in', record.item_ids.ids),
                ('location_id.usage', '=', 'internal')
            ])
            warehouses = quants.mapped('location_id.warehouse_id')
            if len(warehouses) == 1:
                record.warehouse_id = warehouses[0]
            else:
                record.warehouse_id = False

    @api.constrains('request_date')
    def _check_request_date(self):
        """
        Ensure the request date is not in the past.
        """
        for rec in self:
            if rec.request_date and rec.request_date < fields.Date.to_date(fields.Date.today()):
                raise ValidationError("The request date cannot be in the past.")

    @api.constrains('item_ids', 'customer_id')
    def _check_item_customer(self):
        """
        Constraint: Ensure all selected items belong to the selected customer.
        """
        for rec in self:
            if rec.customer_id and rec.item_ids:
                invalid_items = rec.item_ids.filtered(lambda l: l.customer_id != rec.customer_id)
                if invalid_items:
                    raise ValidationError("All items must belong to the selected customer.")

    def action_confirm(self):
        """
        Confirm the pickup request, moving it to the 'confirmed' state.
        """
        for rec in self:
            rec.state = 'confirmed'

    def action_schedule(self):
        """
        Schedule the pickup request, moving it to the 'scheduled' state.
        """
        for rec in self:
            if not rec.scheduled_date:
                rec.scheduled_date = fields.Date.today()
            rec.state = 'scheduled'

    def action_complete(self):
        """
        Complete the pickup request, moving it to the 'completed' state.
        """
        for rec in self:
            rec.completion_date = fields.Date.today()
            rec.state = 'completed'

    def action_cancel(self):
        """
        Cancel the pickup request, moving it to the 'cancelled' state.
        """
        for rec in self:
            rec.state = 'cancelled'

    def action_done(self):
        """
        Legacy method for backward compatibility.
        Mark the pickup request as completed.
        """
        return self.action_complete()

    @api.model
    def create_pickup_request(self, partner, item_ids):
        """
        Create a pickup request for the given partner and item_ids.

        Args:
            partner (res.partner): The customer.
            item_ids (list): List of stock.lot ids.

        Returns:
            pickup.request record or None
        Raises:
            ValidationError: If no items are provided.
        """
        if not item_ids:
            raise ValidationError(_("No items selected for pickup."))
        items = self.env['stock.lot'].search([
            ('id', 'in', item_ids),
            ('customer_id', '=', partner.id)
        ])
        if not items:
            raise ValidationError(_("Selected items are invalid or do not belong to you."))
        return self.create({
            'customer_id': partner.id,
            'item_ids': [(6, 0, items.ids)],
        })

    # Security rules should be defined in the appropriate XML security files.
    # See your module's security configuration for access rights setup.

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        """
        Dynamically filter items based on the selected customer.
        Also clears item_ids if no customer is selected.
        """
        if self.customer_id:
            return {
                'domain': {
                    'item_ids': [('customer_id', '=', self.customer_id.id)]
                }
            }
        else:
            self.item_ids = [(5, 0, 0)]  # Clear all selected items
            return {
                'domain': {
                    'item_ids': []
                }
            }

    @api.model
    def create(self, vals):
        """
        Override create method to assign a sequence number.
        """
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('pickup.request') or 'New'
        return super(PickupRequest, self).create(vals)
