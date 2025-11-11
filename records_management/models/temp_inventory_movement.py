from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class TempInventoryMovement(models.Model):
    _name = 'temp.inventory.movement'
    _description = 'Temporary Inventory Movement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Reference", required=True, copy=False, readonly=True, default=lambda self: "New")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    product_id = fields.Many2one(
        'product.product',
        string="Product",
        required=True,
        domain="[('type', '=', 'product')]",
        help="The product being moved (e.g., a records container)."
    )
    container_id = fields.Many2one(
        'records.container',
        string="Container",
        help="The specific records container involved in the movement."
    )
    quantity = fields.Float(string="Quantity", required=True, default=1.0)

    location_src_id = fields.Many2one(comodel_name='stock.location', string="Source Location", required=True)
    location_dest_id = fields.Many2one(comodel_name='stock.location', string="Destination Location", required=True)

    user_id = fields.Many2one(
        'res.users',
        string="Movement User",
        default=lambda self: self.env.user,
        required=True
    )
    notes = fields.Text(string='Notes')

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        readonly=True
    )

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('temp.inventory.movement') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm_movement(self):
        """Confirm the movement and create the corresponding stock.move record."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft movements can be confirmed."))

        self._create_stock_move()
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Movement confirmed and stock move created."))

    def action_cancel(self):
        """Cancel the temporary movement."""
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Movement cancelled."))

    def action_reset_to_draft(self):
        """Reset the movement back to draft state."""
        self.write({'state': 'draft'})

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _create_stock_move(self):
        """Creates a stock.move record from the temporary movement data."""
        self.ensure_one()
        move_vals = {
            'name': self.product_id.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.product_id.uom_id.id,
            'location_id': self.location_src_id.id,
            'location_dest_id': self.location_dest_id.id,
            'origin': self.name,
            'company_id': self.company_id.id,
        }
        stock_move = self.env['stock.move'].create(move_vals)
        stock_move._action_confirm()
        stock_move._action_assign()
        return stock_move

    @api.constrains('quantity')
    def _check_quantity(self):
        """Validate that the quantity is positive."""
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("The quantity must be a positive number."))
