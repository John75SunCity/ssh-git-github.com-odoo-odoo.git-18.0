try:
    from odoo import fields, models, api
except ImportError:
    # Fallbacks for environments without Odoo
    class DummyField:
        def __init__(self, *args, **kwargs): pass
        @staticmethod
        def from_string(val): return val
        @staticmethod
        def today(): return '1970-01-01'
    class DummyMeta(type):
        def __getattr__(self, name):
            return DummyField
    class fields(metaclass=DummyMeta):
        Many2one = DummyField
        Date = DummyField
        Selection = DummyField
        Many2many = DummyField
    class models(metaclass=DummyMeta):
        class Model(metaclass=DummyMeta):
            pass
    class DummyApi:
        @staticmethod
        def constrains(*args, **kwargs):
            def decorator(func): return func
            return decorator
        @staticmethod
        def onchange(*args, **kwargs):
            def decorator(func): return func
            return decorator
    api = DummyApi()

try:
    from odoo.exceptions import ValidationError
except ImportError:
    ValidationError = Exception  # fallback for environments without odoo

class PickupRequest(models.Model):
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
        default=lambda self: fields.Date.today(),
        required=True,
        help="The date when the pickup is requested. Cannot be in the past."
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], default='draft', string='Status', help="Current status of the pickup request.")
    item_ids = fields.Many2many(
        'stock.production.lot',
        string='Items',
        help="Items to be picked up. Only items belonging to the selected customer are allowed."
    )

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

    def action_done(self):
        """
        Mark the pickup request as done, moving it to the 'done' state.
        """
        for rec in self:
            rec.state = 'done'

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
