# -*- coding: utf-8 -*-
"""
Barcode Pricing Tier Module

Manages tiered pricing structures for barcode products and services.
This model allows for creating different pricing levels based on volume,
customer type, and included features like NAID compliance and support.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class BarcodePricingTier(models.Model):
    """
    Barcode Pricing Tier

    Defines specific pricing tiers for barcode products, allowing for
    discounts, validity periods, and feature bundling.
    """
    _name = 'barcode.pricing.tier'
    _description = 'Barcode Pricing Tier'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'tier_level, name'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION & WORKFLOW
    # ============================================================================
    name = fields.Char(
        string='Tier Name',
        required=True,
        tracking=True,
        index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Pricing Manager',
        default=lambda self: self.env.user,
        tracking=True
    )
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired')
    ], string='Status', default='draft', required=True, tracking=True)

    # ============================================================================
    # PRICING & TIER CONFIGURATION
    # ============================================================================
    product_id = fields.Many2one(
        'product.product',
        string='Related Product',
        required=True,
        help="The product this pricing tier applies to."
    )
    tier_level = fields.Selection([
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('custom', 'Custom')
    ], string='Tier Level', default='bronze', required=True, tracking=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True
    )
    base_price = fields.Monetary(
        string='Base Price',
        required=True,
        tracking=True,
        help="The standard price before any discounts."
    )
    volume_discount = fields.Float(
        string='Volume Discount (%)',
        tracking=True,
        help="Discount percentage applied for volume purchases."
    )
    discounted_price = fields.Monetary(
        string='Discounted Price',
        compute='_compute_discounted_price',
        store=True,
        help="Price after applying the volume discount."
    )

    # ============================================================================
    # QUANTITY & VALIDITY
    # ============================================================================
    minimum_quantity = fields.Integer(string='Minimum Quantity', default=1)
    maximum_quantity = fields.Integer(string='Maximum Quantity', default=0, help="0 for no limit.")
    valid_from = fields.Date(string='Valid From', default=fields.Date.today)
    valid_to = fields.Date(string='Valid To')
    is_expired = fields.Boolean(
        string='Is Expired',
        compute='_compute_is_expired',
        store=True
    )
    days_until_expiry = fields.Integer(
        string='Days Until Expiry',
        compute='_compute_days_until_expiry'
    )

    # ============================================================================
    # FEATURE INCLUSIONS
    # ============================================================================
    includes_setup = fields.Boolean(string='Includes Setup Fee')
    includes_support = fields.Boolean(string='Includes Support')
    support_level = fields.Selection([
        ('none', 'None'),
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise')
    ], string='Support Level', default='none')
    includes_naid_compliance = fields.Boolean(string='Includes NAID Compliance')
    includes_portal_access = fields.Boolean(string='Includes Portal Access')
    max_monthly_requests = fields.Integer(string='Max Monthly Requests', help="0 for unlimited.")

    # ============================================================================
    # CUSTOMER ASSIGNMENT & DOCUMENTATION
    # ============================================================================
    customer_ids = fields.Many2many(
        'res.partner',
        'barcode_tier_partner_rel',
        'tier_id',
        'partner_id',
        string='Assigned Customers',
        help="Customers this tier applies to. Leave empty for all customers."
    )
    description = fields.Html(string='Public Description')
    terms_conditions = fields.Html(string='Terms & Conditions')
    internal_notes = fields.Text(string='Internal Notes')

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends('base_price', 'volume_discount')
    def _compute_discounted_price(self):
        """Calculate discounted price based on volume discount."""
        for record in self:
            discount = record.base_price * (record.volume_discount / 100)
            record.discounted_price = record.base_price - discount

    @api.depends('valid_to')
    def _compute_is_expired(self):
        """Check if pricing tier has expired."""
        for record in self:
            record.is_expired = record.valid_to and record.valid_to < fields.Date.today()

    @api.depends('valid_to')
    def _compute_days_until_expiry(self):
        """Calculate days until expiry."""
        for record in self:
            if record.valid_to and not record.is_expired:
                delta = record.valid_to - fields.Date.today()
                record.days_until_expiry = delta.days
            else:
                record.days_until_expiry = 0

    @api.onchange('includes_support')
    def _onchange_includes_support(self):
        """Update support level when support inclusion changes."""
        if not self.includes_support:
            self.support_level = 'none'
        elif self.support_level == 'none':
            self.support_level = 'basic'

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate pricing tier."""
        self.ensure_one()
        self._validate_pricing_configuration()
        self.write({'state': 'active'})
        self.message_post(body=_("Pricing tier activated."))

    def action_deactivate(self):
        """Deactivate pricing tier."""
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body=_("Pricing tier deactivated and set to draft."))

    def action_expire(self):
        """Manually mark pricing tier as expired."""
        self.ensure_one()
        self.write({'state': 'expired', 'valid_to': fields.Date.today() - timedelta(days=1)})
        self.message_post(body=_("Pricing tier manually expired."))

    # ============================================================================
    # BUSINESS LOGIC & VALIDATION
    # ============================================================================
    def _validate_pricing_configuration(self):
        """Validate pricing configuration before activation."""
        self.ensure_one()
        if self.base_price <= 0:
            raise ValidationError(_("Base price must be greater than zero."))
        if self.maximum_quantity != 0 and self.minimum_quantity > self.maximum_quantity:
            raise ValidationError(_("Minimum quantity cannot exceed maximum quantity."))
        if not (0 <= self.volume_discount <= 100):
            raise ValidationError(_("Volume discount must be between 0 and 100 percent."))
        if self.valid_to and self.valid_to < self.valid_from:
            raise ValidationError(_("Valid to date must be after valid from date."))

    @api.model
    def _check_expired_tiers(self):
        """Cron job to check and mark expired tiers."""
        expired_tiers = self.search([
            ('state', '=', 'active'),
            ('valid_to', '<', fields.Date.today())
        ])
        expired_tiers.write({'state': 'expired'})
        for tier in expired_tiers:
            tier.message_post(body=_("Pricing tier automatically expired."))

    @api.constrains('base_price')
    def _check_base_price(self):
        """Validate base price is positive."""
        for record in self:
            if record.base_price < 0:
                raise ValidationError(_("Base price cannot be negative."))

    @api.constrains('volume_discount')
    def _check_volume_discount(self):
        """Validate volume discount percentage."""
        for record in self:
            if not (0 <= record.volume_discount <= 100):
                raise ValidationError(_("Volume discount must be between 0 and 100."))

    @api.constrains('minimum_quantity', 'maximum_quantity')
    def _check_quantity_range(self):
        """Validate quantity range."""
        for record in self:
            if record.minimum_quantity < 0:
                raise ValidationError(_("Minimum quantity cannot be negative."))
            if record.maximum_quantity != 0 and record.minimum_quantity > record.maximum_quantity:
                raise ValidationError(_("Minimum quantity cannot be greater than maximum quantity."))

    @api.constrains('valid_from', 'valid_to')
    def _check_validity_dates(self):
        """Validate validity date range."""
        for record in self:
            if record.valid_to and record.valid_from and record.valid_to < record.valid_from:
                raise ValidationError(_("The 'Valid To' date cannot be before the 'Valid From' date."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default name if not provided."""
        for vals in vals_list:
            if not vals.get('name'):
                tier_level = vals.get('tier_level', 'custom')
                product_name = self.env['product.product'].browse(vals.get('product_id')).name if vals.get('product_id') else 'Product'
                level_name = dict(self._fields['tier_level'].selection).get(tier_level, 'Custom').capitalize()
                vals['name'] = _("%s - %s Tier") % (product_name, level_name)
        return super().create(vals_list)
