from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsPromotionalDiscount(models.Model):
    _name = 'records.promotional.discount'
    _description = 'Records Promotional Discount'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Promotion Name', required=True, tracking=True)
    promotion_code = fields.Char(string='Promotion Code', copy=False, help="Unique code customers can use to apply the discount.")
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)

    # ============================================================================
    # DISCOUNT CONFIGURATION
    # ============================================================================
    discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_amount', 'Fixed Amount'),
    ], string="Discount Type", default='percentage', required=True, tracking=True)
    discount_value = fields.Float(string="Discount Value", required=True, tracking=True, help="The percentage or fixed amount of the discount.")

    # ============================================================================
    # APPLICABILITY & CONDITIONS
    # ============================================================================
    product_ids = fields.Many2many('product.product', string="Applicable Products/Services", help="Leave empty to apply to all eligible services.")
    partner_ids = fields.Many2many('res.partner', string="Applicable Customers", help="Leave empty to apply to all customers.")
    minimum_order_amount = fields.Monetary(string="Minimum Order Amount", currency_field='currency_id', tracking=True, help="The minimum amount required to be eligible for the discount.")
    maximum_discount_amount = fields.Monetary(string="Maximum Discount", currency_field='currency_id', tracking=True, help="The maximum discount amount that can be applied. 0 for no limit.")

    # ============================================================================
    # LIFECYCLE & USAGE
    # ============================================================================
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today, required=True, tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)
    usage_limit = fields.Integer(string='Total Usage Limit', default=0, tracking=True, help="Total number of times this discount can be used across all customers. 0 for unlimited.")
    usage_limit_per_customer = fields.Integer(string='Usage Limit Per Customer', default=1, tracking=True, help="How many times a single customer can use this discount. 0 for unlimited.")
    times_used = fields.Integer(string='Times Used', compute='_compute_times_used', store=True, help="How many times this discount has been used in total.")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True, compute='_compute_state', store=True)

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('start_date', 'end_date', 'active')
    def _compute_state(self):
        today = fields.Date.context_today(self)
        for record in self:
            if not record.active:
                record.state = 'cancelled'
            elif record.end_date and record.end_date < today:
                record.state = 'expired'
            elif record.start_date and record.start_date > today:
                record.state = 'draft'
            else:
                record.state = 'active'

    def _compute_times_used(self):
        # This would typically be computed based on related sale order lines
        # For now, we'll leave it as a placeholder.
        for record in self:
            record.times_used = 0

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("The start date cannot be after the end date."))

    @api.constrains('discount_value')
    def _check_discount_value(self):
        for record in self:
            if record.discount_value <= 0:
                raise ValidationError(_("Discount value must be positive."))
            if record.discount_type == 'percentage' and record.discount_value > 100:
                raise ValidationError(_("Percentage discount cannot exceed 100%."))

    @api.constrains('promotion_code')
    def _check_unique_promotion_code(self):
        for record in self:
            if record.promotion_code:
                domain = [('promotion_code', '=', record.promotion_code), ('id', '!=', record.id)]
                if self.search_count(domain) > 0:
                    raise ValidationError(_("This promotion code is already in use."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        self.write({'active': True})

    def action_cancel(self):
        self.write({'active': False})
