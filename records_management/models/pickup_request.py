# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
from odoo import models, fields, api


class PickupRequest(models.Model):
    """Model for pickup requests with workflow enhancements."""
    _name = 'pickup.request'
    _description = 'Pickup Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Name',
        required=True,
        default='New',
        tracking=True
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True
    )
    request_date = fields.Date(
        string='Request Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    request_item_ids = fields.One2many(
        'pickup.request.item',
        'pickup_id',
        string='Request Items'
    )
    notes = fields.Text(string='Notes')
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        tracking=True
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        tracking=True,
        digits=(16, 2)
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot',
        domain="[('product_id', '=', product_id)]"
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='draft', string='Status', tracking=True)
    scheduled_date = fields.Date(string='Scheduled Date', tracking=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        tracking=True
    )
    driver_id = fields.Many2one(
        'res.partner',
        string='Driver',
        domain="[('is_company', '=', False)]",
        tracking=True
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehicle',
        tracking=True
    )
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High')
    ], default='0', string='Priority', tracking=True)
    signature = fields.Binary(string='Signature')
    signed_by = fields.Many2one('res.users', string='Signed By')
    signature_date = fields.Datetime(string='Signature Date')
    completion_date = fields.Date(string='Completion Date', tracking=True)

    @api.model_create_multi
    def create(self, vals_list: List[dict]) -> 'PickupRequest':
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                sequence = self.env['ir.sequence'].next_by_code(
                    'pickup.request'
                )
                vals['name'] = sequence or 'New'
        return super().create(vals_list)

    def action_confirm(self) -> bool:
        return self.write({'state': 'confirmed'})

    def action_schedule(self) -> bool:
        if not self.scheduled_date:
            self.scheduled_date = fields.Date.context_today(self)
        return self.write({'state': 'scheduled'})

    def action_complete(self) -> bool:
        self.completion_date = fields.Date.context_today(self)
        return self.write({'state': 'completed'})

    def action_cancel(self) -> bool:
        return self.write({'state': 'cancelled'})

    @api.onchange('customer_id')
    def _onchange_customer_id(self) -> None:
        """
        Update domain for driver and vehicle based on customer
        for better UI.
        """
        return {
            'domain': {
                'driver_id': [('parent_id', '=', self.customer_id.id)]
            }
        }
