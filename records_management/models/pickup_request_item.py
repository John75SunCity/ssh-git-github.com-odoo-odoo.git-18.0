from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PickupRequestItem(models.Model):
    _name = 'pickup.request.item'
    _description = 'Pickup Request Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    request_id = fields.Many2one('pickup.request', string='Pickup Request', required=True, ondelete='cascade')

    item_type = fields.Selection([
        ('box', 'Document Box'),
        ('file', 'File Cabinet'),
        ('equipment', 'Equipment'),
        ('other', 'Other'),
    ], string='Item Type', required=True, default='box')

    quantity = fields.Integer(string='Quantity', default=1, required=True)
    estimated_weight = fields.Float(string='Estimated Weight (lbs)')
    weight = fields.Float(string='Actual Weight (lbs)', default=0.0)  # Added for constraints
    unit_cost = fields.Float(string='Unit Cost', default=0.0)  # Added for constraints
    notes = fields.Text(string='Notes')

    # For document boxes
    box_size = fields.Selection([
        ('letter', 'Letter Size'),
        ('legal', 'Legal Size'),
        ('banker', 'Banker Box'),
        ('custom', 'Custom Size'),
    ], string='Box Size')

    # Status tracking
    state = fields.Selection([  # Added for workflow management
        ('draft', 'Draft'),
        ('collected', 'Collected'),
        ('delivered', 'Delivered'),
        ('exception', 'Exception'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', readonly=True)
    collected = fields.Boolean(string='Collected', default=False)
    collected_date = fields.Datetime(string='Collection Date', readonly=True)

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('quantity')
    def _check_quantity(self):
        """Validate quantity is positive"""
        for item in self:
            if item.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero."))

    @api.constrains('estimated_weight')
    def _check_estimated_weight(self):
        """Validate estimated weight is positive"""
        for item in self:
            if item.estimated_weight and item.estimated_weight < 0:
                raise ValidationError(_("Estimated weight must be positive."))

    @api.constrains('weight')
    def _check_weights(self):
        """Validate weights are positive"""
        for item in self:
            if item.weight < 0:
                raise ValidationError(_("Weight cannot be negative."))

    @api.constrains('unit_cost')
    def _check_unit_cost(self):
        """Validate unit cost is not negative"""
        for item in self:
            if item.unit_cost < 0:
                raise ValidationError(_("Unit cost cannot be negative."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_collected(self):
        """Mark item as collected"""
        self.ensure_one()
        self.write({
            'collected': True,
            'collected_date': fields.Datetime.now(),
            'state': 'collected'  # Updated to use state field
        })
        self.request_id.message_post(body=_("Item '%s' marked as collected.", self.name))

    def action_unmark_collected(self):
        """Unmark item as collected"""
        self.ensure_one()
        self.write({
            'collected': False,
            'collected_date': False,
            'state': 'delivered'  # Updated to use state field
        })
        self.request_id.message_post(body=_("Item '%s' unmarked as collected.", self.name))
        self.create_naid_audit_log('delivery', f'Item {self.name} delivered')

    def action_mark_exception(self):
        """Mark item as having an exception"""
        self.ensure_one()
        self.write({'state': 'exception'})  # Now uses state field
        self.create_naid_audit_log('exception', f'Exception recorded for item {self.name}')

    def action_cancel(self):
        """Cancel the pickup item"""
        self.ensure_one()
        self.write({'state': 'cancelled'})  # Now uses state field
        self.create_naid_audit_log('cancellation', f'Item {self.name} cancelled')

    def action_reset_to_draft(self):
        """Reset item to draft state"""
        self.ensure_one()
        self.write({'state': 'draft'})  # Now uses state field
        self.create_naid_audit_log('reset', f'Item {self.name} reset to draft')

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def create_naid_audit_log(self, event_type, description):
        """Create NAID compliance audit log entry"""
        if self.env['ir.model'].search([('model', '=', 'naid.audit.log')]):
            self.env['naid.audit.log'].create({
                'event_type': event_type,
                'description': description,
                'related_model': self._name,
                'related_id': self.id,
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
            })

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_items_by_status(self, status_list=None):
        """Get items filtered by status"""
        domain = []
        if status_list:
            domain.append(('state', 'in', status_list))  # Updated to use state field
        return self.search(domain)
