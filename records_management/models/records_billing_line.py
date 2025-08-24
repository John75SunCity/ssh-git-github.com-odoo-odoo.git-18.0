from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsBillingLine(models.Model):
    _name = 'records.billing.line'
    _description = 'Records Billing Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'billing_id, date desc, id desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Line Description", required=True, readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', related='billing_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='billing_id.currency_id', store=True, readonly=True)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    billing_id = fields.Many2one('records.billing', string="Billing Document", required=True, ondelete='cascade', index=True)
    config_id = fields.Many2one('records.billing.config', string="Billing Config", help="The configuration that generated this line.")
    partner_id = fields.Many2one(related='billing_id.partner_id', string="Customer", store=True, readonly=True)
    department_id = fields.Many2one(related='billing_id.department_id', string="Department", store=True, readonly=True)

    # ============================================================================
    # BILLING DETAILS
    # ============================================================================
    date = fields.Date(string="Billing Date", required=True, default=fields.Date.context_today, readonly=True, states={'draft': [('readonly', False)]})
    service_type = fields.Selection([
        ('storage', 'Storage'),
        ('shredding', 'Shredding'),
        ('retrieval', 'Retrieval'),
        ('delivery', 'Delivery'),
        ('other', 'Other'),
    ], string="Service Type", required=True, default='storage', readonly=True, states={'draft': [('readonly', False)]})

    quantity = fields.Float(string="Quantity", default=1.0, required=True, readonly=True, states={'draft': [('readonly', False)]})
    unit_price = fields.Monetary(string="Unit Price", required=True, readonly=True, states={'draft': [('readonly', False)]})
    discount_percentage = fields.Float(string="Discount (%)", readonly=True, states={'draft': [('readonly', False)]})

    # ============================================================================
    # COMPUTED AMOUNTS
    # ============================================================================
    subtotal = fields.Monetary(string="Subtotal", compute='_compute_amounts', store=True)
    discount_amount = fields.Monetary(string="Discount Amount", compute='_compute_amounts', store=True)
    amount = fields.Monetary(string="Total", compute='_compute_amounts', store=True)

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)

    billable = fields.Boolean(string="Billable", default=True)
    invoiced = fields.Boolean(string="Invoiced", default=False, readonly=True, copy=False)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('quantity', 'unit_price', 'discount_percentage')
    def _compute_amounts(self):
        """Compute subtotal, discount amount, and total amount."""
        for line in self:
            subtotal = line.quantity * line.unit_price
            discount = subtotal * (line.discount_percentage / 100)
            line.subtotal = subtotal
            line.discount_amount = discount
            line.amount = subtotal - discount

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Billing line confirmed."))

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Billing line cancelled."))

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
        self.message_post(body=_("Billing line reset to draft."))

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('quantity')
    def _check_quantity(self):
        """Validate quantity is positive."""
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be a positive number."))

    @api.constrains('unit_price')
    def _check_unit_price(self):
        """Validate unit price is not negative."""
        for record in self:
            if record.unit_price < 0:
                raise ValidationError(_("Unit price cannot be negative."))

    @api.constrains('discount_percentage')
    def _check_discount_percentage(self):
        """Validate discount percentage is within a valid range."""
        for record in self:
            if not (0 <= record.discount_percentage <= 100):
                raise ValidationError(_("Discount percentage must be between 0 and 100."))



