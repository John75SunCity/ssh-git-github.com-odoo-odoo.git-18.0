from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PickupRequest(models.Model):
    _name = 'pickup.request'
    _description = 'Pickup Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, default='New', tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.context_today, required=True, tracking=True)
    request_item_ids = fields.One2many('pickup.request.item', 'pickup_id', string='Request Items')  # canonical one2many
    notes = fields.Text(string='Notes')
    
    # New fields
    product_id = fields.Many2one('product.product', string='Product', required=True, tracking=True)
    quantity = fields.Float(string='Quantity', required=True, tracking=True)
    lot_id = fields.Many2one('stock.lot', string='Lot', domain="[('product_id', '=', product_id)]")
    
    # Status tracking
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='draft', string='Status', tracking=True)
    
    # Additional fields for the view
    scheduled_date = fields.Date(string='Scheduled Date', tracking=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', tracking=True)
    driver_id = fields.Many2one('res.partner', string='Driver', domain="[('is_company', '=', False)]", tracking=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', tracking=True)
    priority = fields.Selection([('0', 'Normal'), ('1', 'High')], default='0', string='Priority', tracking=True)
    signature = fields.Binary(string='Signature')
    signed_by = fields.Many2one('res.users', string='Signed By')
    signature_date = fields.Datetime(string='Signature Date')
    completion_date = fields.Date(string='Completion Date', tracking=True)
    
    @api.multi
    def action_confirm(self):
        for record in self:
            record.state = 'confirmed'
        return True
    
    @api.multi
    def action_schedule(self):
        for record in self:
            if not record.scheduled_date:
                record.scheduled_date = fields.Date.context_today(self)
            record.state = 'scheduled'
        return True
    
    @api.multi
    def action_complete(self):
        for record in self:
            record.completion_date = fields.Date.context_today(self)
            record.state = 'completed'
        return True
    
    @api.multi
    def action_cancel(self):
        for record in self:
            record.state = 'cancelled'
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('pickup.request') or 'New'
        return super().create(vals_list)