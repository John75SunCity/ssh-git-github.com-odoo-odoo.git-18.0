from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class UnlockServicePart(models.Model):
    _name = 'unlock.service.part'
    _description = 'Unlock Service Part Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    sequence = fields.Integer(string="Sequence", default=10)
    name = fields.Char(string="Description", related='product_id.name')

    service_history_id = fields.Many2one('unlock.service.history', string="Service History", required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Customer", related='service_history_id.partner_id', store=True)
    technician_id = fields.Many2one('res.users', string="Technician", related='service_history_id.technician_id', store=True)

    product_id = fields.Many2one('product.product', string="Product", required=True, domain="[('type', '=', 'product')]")
    product_category_id = fields.Many2one('product.category', string="Product Category", related='product_id.categ_id', store=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", related='product_id.uom_id')

    quantity_planned = fields.Float(string="Planned Quantity", default=1.0)
    quantity_used = fields.Float(string="Used Quantity")
    quantity = fields.Float(string="Final Quantity", compute='_compute_quantity', store=True)

    unit_cost = fields.Float(string="Unit Cost", related='product_id.standard_price')
    unit_price = fields.Float(string="Unit Price", related='product_id.lst_price')
    markup_percentage = fields.Float(string="Markup (%)", default=20.0)

    currency_id = fields.Many2one('res.currency', string="Currency", related='company_id.currency_id')
    service_price = fields.Monetary(string="Service Price", compute='_compute_service_price', store=True)
    total_cost = fields.Monetary(string="Total Cost", compute='_compute_total_amounts', store=True)
    total_price = fields.Monetary(string="Total Price", compute='_compute_total_amounts', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('reserved', 'Reserved'),
        ('used', 'Used'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)

    is_critical = fields.Boolean(string="Critical Part")
    is_warranty_covered = fields.Boolean(string="Warranty Covered")
    warranty_date = fields.Date(string="Warranty End Date")

    vendor_id = fields.Many2one('res.partner', string="Vendor")
    procurement_date = fields.Date(string="Procurement Date")
    batch_number = fields.Char(string="Batch/Serial Number")
    expiry_date = fields.Date(string="Expiry Date")

    usage_notes = fields.Text(string="Usage Notes")
    replacement_reason = fields.Text(string="Reason for Replacement")

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('product_id', 'service_history_id.name', 'quantity')
    def _compute_display_name(self):
        for record in self:
            if record.product_id and record.service_history_id:
                record.display_name = _("%s - %s (Qty: %s)", record.service_history_id.name, record.product_id.name, record.quantity)
            elif record.product_id:
                record.display_name = record.product_id.name
            else:
                record.display_name = _("New Service Part")

    @api.depends('quantity_used', 'quantity_planned')
    def _compute_quantity(self):
        for record in self:
            record.quantity = record.quantity_used or record.quantity_planned

    @api.depends('unit_price', 'markup_percentage')
    def _compute_service_price(self):
        for record in self:
            if record.unit_price and record.markup_percentage:
                record.service_price = record.unit_price * (1 + record.markup_percentage / 100)
            else:
                record.service_price = record.unit_price

    @api.depends('quantity', 'unit_cost', 'service_price')
    def _compute_total_amounts(self):
        for record in self:
            record.total_cost = record.quantity * record.unit_cost
            record.total_price = record.quantity * record.service_price

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id and self.product_id.qty_available <= 0:
            return {
                'warning': {
                    'title': _('Stock Warning'),
                    'message': _('Product %s is out of stock. Available: %s', self.product_id.name, self.product_id.qty_available)
                }
            }

    # ============================================================================
    # CONSTRAINT METHODS
    # ============================================================================
    @api.constrains('quantity_planned', 'quantity_used')
    def _check_quantities(self):
        for record in self:
            if record.quantity_planned < 0:
                raise ValidationError(_("Planned quantity cannot be negative."))
            if record.quantity_used < 0:
                raise ValidationError(_("Used quantity cannot be negative."))
            if record.quantity_used and record.quantity_used > record.quantity_planned:
                raise ValidationError(_("Used quantity (%s) cannot exceed planned quantity (%s) for %s.", record.quantity_used, record.quantity_planned, record.product_id.name))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_plan(self):
        self.ensure_one()
        self.write({'state': 'planned'})

    def action_reserve_stock(self):
        self.ensure_one()
        if self.state != 'planned':
            raise UserError(_("Can only reserve stock for planned parts."))
        if self.quantity_planned > self.product_id.qty_available:
            raise UserError(_("Cannot reserve %s units of %s. Only %s available.", self.quantity_planned, self.product_id.name, self.product_id.qty_available))
        self.write({'state': 'reserved'})

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancelled'})
