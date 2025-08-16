# -*- coding: utf-8 -*-
"""
Barcode Pricing Tier Module

This module provides comprehensive pricing tier management for barcode products
in the Records Management System. It handles multi-tier pricing structures,
volume discounts, and customer-specific pricing configurations with full
audit trail capabilities.

Key Features:
- Multi-level pricing tiers (Basic, Standard, Premium, Enterprise)
- Volume-based discount calculations
- Time-based pricing validity periods
- Support level integration with pricing
- Complete audit trails for pricing changes

Business Processes:
1. Tier Configuration: Set up pricing tiers with base prices and discounts
2. Volume Management: Configure minimum/maximum quantities for tier eligibility
3. Validity Management: Time-bound pricing with automatic expiration
4. Support Integration: Link support levels to pricing tiers
5. Customer Assignment: Associate customers with specific pricing tiers

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _

from odoo.exceptions import ValidationError, UserError




class BarcodePricingTier(models.Model):
    _name = "barcode.pricing.tier"
    _description = "Barcode Pricing Tier"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "tier_level, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Tier Name", 
        required=True, 
        tracking=True, 
        index=True,
        help="Name of the pricing tier"
    )
    company_id = fields.Many2one(
        "res.company", 
        string="Company",
        default=lambda self: self.env.company, 
        required=True
    )
    user_id = fields.Many2one(
        "res.users", 
        string="Responsible User",
        default=lambda self: self.env.user, 
        tracking=True
    )
    active = fields.Boolean(
        string="Active", 
        default=True,
        tracking=True
    )
    
    # Partner Relationship
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        tracking=True,
        help="Associated partner for this pricing tier"
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("expired", "Expired")
        ],
        string="Status",
        default="draft",
        tracking=True,
        required=True,
        help="Current status of the pricing tier"
    )

    # ============================================================================
    # PRICING CONFIGURATION
    # ============================================================================
    product_id = fields.Many2one(
        "barcode.product", 
        string="Barcode Product", 
        required=True,
        tracking=True,
        help="Associated barcode product for pricing"
    )
    
    tier_level = fields.Selection(
        [
            ("basic", "Basic Tier"),
            ("standard", "Standard Tier"),
            ("premium", "Premium Tier"),
            ("enterprise", "Enterprise Tier"),
        ],
        string="Tier Level",
        default="standard",
        required=True,
        tracking=True,
        help="Pricing tier level classification"
    )

    # ============================================================================
    # PRICING DETAILS
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    
    base_price = fields.Monetary(
        string="Base Price", 
        currency_field="currency_id",
        default=0.0,
        tracking=True,
        help="Base price before discounts"
    )
    
    volume_discount = fields.Float(
        string="Volume Discount (%)", 
        digits=(5, 2),
        default=0.0,
        tracking=True,
        help="Percentage discount for volume purchases"
    )
    
    minimum_quantity = fields.Integer(
        string="Minimum Quantity", 
        default=1,
        help="Minimum quantity required for this tier"
    )
    
    maximum_quantity = fields.Integer(
        string="Maximum Quantity", 
        default=9999,
        help="Maximum quantity allowed for this tier"
    )

    # ============================================================================
    # VALIDITY PERIOD
    # ============================================================================
    valid_from = fields.Date(
        string="Valid From", 
        default=fields.Date.today,
        required=True,
        tracking=True,
        help="Date when pricing tier becomes effective"
    )
    
    valid_to = fields.Date(
        string="Valid To",
        tracking=True,
        help="Date when pricing tier expires (leave empty for indefinite)"
    )

    # ============================================================================
    # TIER FEATURES & SERVICES
    # ============================================================================
    includes_setup = fields.Boolean(
        string="Includes Setup", 
        default=False,
        help="Whether setup services are included in this tier"
    )
    
    includes_support = fields.Boolean(
        string="Includes Support", 
        default=False,
        help="Whether support services are included in this tier"
    )
    
    support_level = fields.Selection(
        [
            ("none", "No Support"),
            ("basic", "Basic Support (Email only)"),
            ("standard", "Standard Support (Email + Phone)"),
            ("premium", "Premium Support (24/7 Email + Phone)"),
            ("enterprise", "Enterprise Support (Dedicated account manager)"),
        ],
        string="Support Level",
        default="none",
        help="Level of support included in this tier"
    )

    # Records Management specific features
    includes_naid_compliance = fields.Boolean(
        string="NAID Compliance Included",
        default=False,
        help="Whether NAID compliance features are included"
    )
    
    includes_portal_access = fields.Boolean(
        string="Portal Access Included",
        default=True,
        help="Whether customer portal access is included"
    )
    
    max_monthly_requests = fields.Integer(
        string="Max Monthly Service Requests",
        default=10,
        help="Maximum number of monthly service requests included"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    discounted_price = fields.Monetary(
        string="Discounted Price",
        compute="_compute_discounted_price",
        currency_field="currency_id",
        store=True,
        help="Final price after applying volume discount"
    )
    
    is_expired = fields.Boolean(
        string="Is Expired",
        compute="_compute_is_expired",
        store=True,
        help="Whether the pricing tier has expired"
    )
    
    days_until_expiry = fields.Integer(
        string="Days Until Expiry",
        compute="_compute_days_until_expiry",
        help="Number of days until expiry (negative if expired)"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    customer_ids = fields.Many2many(
        "res.partner",
        "barcode_pricing_tier_customer_rel",
        "tier_id",
        "partner_id",
        string="Assigned Customers",
        help="Customers assigned to this pricing tier"
    )

    # ============================================================================
    # DOCUMENTATION FIELDS
    # ============================================================================
    description = fields.Html(
        string="Description",
        help="Detailed description of the pricing tier"
    )
    
    terms_conditions = fields.Html(
        string="Terms & Conditions",
        help="Terms and conditions for this pricing tier"
    )
    
    internal_notes = fields.Text(
        string="Internal Notes",
        help="Internal notes for staff reference"
    )

    # ============================================================================
    # MAIL FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities"
    )
    message_ids = fields.One2many(
        "mail.message", "res_id", string="Messages"
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("base_price", "volume_discount")
    def _compute_discounted_price(self):
        """Calculate discounted price based on volume discount"""
        for tier in self:
            if tier.volume_discount > 0:
                discount_amount = tier.base_price * (tier.volume_discount / 100)
                tier.discounted_price = tier.base_price - discount_amount
            else:
                tier.discounted_price = tier.base_price

    @api.depends("valid_to")
    def _compute_is_expired(self):
        """Check if pricing tier has expired"""
        today = fields.Date.today()
        for tier in self:
            tier.is_expired = tier.valid_to and tier.valid_to < today

    @api.depends("valid_to")
    def _compute_days_until_expiry(self):
        """Calculate days until expiry"""
        today = fields.Date.today()
        for tier in self:
            if tier.valid_to:
                delta = tier.valid_to - today
                tier.days_until_expiry = delta.days
            else:
                tier.days_until_expiry = 0

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange("tier_level")
    def _onchange_tier_level(self):
        """Set default values based on tier level"""
        if self.tier_level:
            defaults = self._default_tier_level_config()
            tier_config = defaults.get(self.tier_level, {})

            for field, value in tier_config.items():
                setattr(self, field, value)

    @api.onchange("includes_support")
    def _onchange_includes_support(self):
        """Update support level when support inclusion changes"""
        if not self.includes_support:
            self.support_level = "none"
        elif self.support_level == "none":
            self.support_level = "basic"

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate pricing tier"""

        self.ensure_one()
        
        if self.state != "draft":
            raise UserError(_("Only draft pricing tiers can be activated"))
        
        self._validate_pricing_configuration()
        self.write({"state": "active"})
        self.message_post(body=_("Pricing tier activated"))

    def action_deactivate(self):
        """Deactivate pricing tier"""

        self.ensure_one()
        
        if self.state != "active":
            raise UserError(_("Only active pricing tiers can be deactivated"))
        
        self.write({"state": "inactive"})
        self.message_post(body=_("Pricing tier deactivated"))

    def action_expire(self):
        """Mark pricing tier as expired"""

        self.ensure_one()
        
        self.write({
            "state": "expired",
            "active": False
        })
        self.message_post(body=_("Pricing tier marked as expired"))

    def action_extend_validity(self):
        """Open wizard to extend validity period"""

        self.ensure_one()
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Extend Validity Period"),
            "res_model": "barcode.pricing.tier.extend.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_tier_id": self.id,
                "default_current_valid_to": self.valid_to,
            }
        }

    def action_duplicate_tier(self):
        """Create a copy of this pricing tier"""

        self.ensure_one()

        copy_vals = {
            "name": _("%s (Copy)", self.name),
            "state": "draft",
            "valid_from": fields.Date.today(),
            "valid_to": False,
        }

        new_tier = self.copy(copy_vals)

        return {
            "type": "ir.actions.act_window",
            "name": _("Pricing Tier Copy"),
            "res_model": self._name,
            "res_id": new_tier.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_assign_customers(self):
        """Open wizard to assign customers to this tier"""

        self.ensure_one()
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Assign Customers to Tier"),
            "res_model": "barcode.pricing.tier.customer.wizard",
            "view_mode": "form", 
            "target": "new",
            "context": {"default_tier_id": self.id}
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_price_for_quantity(self, quantity):
        """Calculate price for a given quantity"""
        self.ensure_one()
        
        if quantity < self.minimum_quantity:
            raise UserError(_(
                "Quantity %s is below minimum quantity %s for tier %s",
                quantity, self.minimum_quantity, self.name
            ))

        if quantity > self.maximum_quantity:
            raise UserError(_(
                "Quantity %s exceeds maximum quantity %s for tier %s",
                quantity, self.maximum_quantity, self.name
            ))

        return self.discounted_price * quantity

    def is_valid_for_date(self, date):
        """Check if tier is valid for a specific date"""
        self.ensure_one()
        
        if date < self.valid_from:
            return False
        
        if self.valid_to and date > self.valid_to:
            return False

        return True

    def _default_tier_level_config(self):
        """Get default configuration for each tier level"""
        return {
            "basic": {
                "support_level": "basic",
                "includes_support": True,
                "includes_setup": False,
                "includes_naid_compliance": False,
                "max_monthly_requests": 5,
            },
            "standard": {
                "support_level": "standard", 
                "includes_support": True,
                "includes_setup": True,
                "includes_naid_compliance": False,
                "max_monthly_requests": 15,
            },
            "premium": {
                "support_level": "premium",
                "includes_support": True,
                "includes_setup": True,
                "includes_naid_compliance": True,
                "max_monthly_requests": 50,
            },
            "enterprise": {
                "support_level": "enterprise",
                "includes_support": True, 
                "includes_setup": True,
                "includes_naid_compliance": True,
                "max_monthly_requests": 999,
            }
        }

    def _validate_pricing_configuration(self):
        """Validate pricing configuration before activation"""
        if self.base_price <= 0:
            raise ValidationError(_("Base price must be greater than zero"))
        
        if self.minimum_quantity > self.maximum_quantity:
            raise ValidationError(_("Minimum quantity cannot exceed maximum quantity"))
        
        if self.volume_discount < 0 or self.volume_discount > 100:
            raise ValidationError(_("Volume discount must be between 0 and 100 percent"))
        
        if self.valid_to and self.valid_to <= self.valid_from:
            raise ValidationError(_("Valid to date must be after valid from date"))

    @api.model
    def _check_expired_tiers(self):
        """Cron job to check and mark expired tiers"""
        today = fields.Date.today()
        expired_tiers = self.search([
            ("state", "=", "active"),
            ("valid_to", "<", today)
        ])
        
        for tier in expired_tiers:
            tier.action_expire()

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("base_price")
    def _check_base_price(self):
        """Validate base price is positive"""
        for tier in self:
            if tier.base_price < 0:
                raise ValidationError(_("Base price cannot be negative"))

    @api.constrains("volume_discount")
    def _check_volume_discount(self):
        """Validate volume discount percentage"""
        for tier in self:
            if tier.volume_discount < 0 or tier.volume_discount > 100:
                raise ValidationError(_("Volume discount must be between 0 and 100 percent"))

    @api.constrains("minimum_quantity", "maximum_quantity")
    def _check_quantity_range(self):
        """Validate quantity range"""
        for tier in self:
            if tier.minimum_quantity < 1:
                raise ValidationError(_("Minimum quantity must be at least 1"))
            
            if tier.maximum_quantity < tier.minimum_quantity:
                raise ValidationError(_("Maximum quantity must be greater than minimum quantity"))

    @api.constrains("valid_from", "valid_to")
    def _check_validity_dates(self):
        """Validate validity date range"""
        for tier in self:
            if tier.valid_to and tier.valid_to <= tier.valid_from:
                raise ValidationError(_("Valid to date must be after valid from date"))

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display with tier level and price"""
        result = []
        for tier in self:
            name = tier.name
            if tier.tier_level:
                level_name = dict(tier._fields["tier_level"].selection).get(tier.tier_level)
                name = _("%s (%s)", name, level_name)
            if tier.discounted_price:
                name = _("%s - %s", name,
                        tier.currency_id.format(tier.discounted_price))
            result.append((tier.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default name if not provided"""
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                tier_level = vals.get("tier_level", "standard")
                level_name = dict(self._fields["tier_level"].selection).get(tier_level, "Standard")
                vals["name"] = _("%s Pricing Tier", level_name)

        return super().create(vals_list)
