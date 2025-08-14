# -*- coding: utf-8 -*-
"""
Base Rate Configuration Module

Central management of standard rates that serve as the foundation for customer pricing.
Supports container-type specific rates, service rates, and company-specific configurations.
Used as fallback rates when customer-specific rates are not defined.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BaseRate(models.Model):
    """Base Rate Configuration

    Central management of standard rates that serve as the foundation for customer pricing.
    Supports container-type specific rates, service rates, and company-specific configurations.
    Used as fallback rates when customer-specific rates are not defined.
    """
    _name = 'base.rate'
    _description = 'Base Rate Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'company_id, effective_date desc'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string='Rate Configuration Name',
        required=True,
        tracking=True,
        help='Name for this base rate configuration'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Rate Manager',
        default=lambda self: self.env.user,
        tracking=True,
        help='User responsible for managing these rates'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Whether this rate configuration is active'
    )

    # ============================================================================
    # RATE VALIDITY FIELDS
    # ============================================================================
    effective_date = fields.Date(
        string='Effective Date',
        default=fields.Date.today,
        required=True,
        tracking=True,
        help='Date these rates become effective'
    )
    
    expiration_date = fields.Date(
        string='Expiration Date',
        tracking=True,
        help='Date these rates expire (leave blank for no expiration)'
    )
    
    version = fields.Char(
        string='Version',
        default='1.0',
        help='Version identifier for rate changes'
    )
    
    description = fields.Text(
        string='Description',
        help='Description of this rate configuration'
    )

    # ============================================================================
    # CURRENCY CONFIGURATION
    # ============================================================================
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # ============================================================================
    # CONTAINER STORAGE RATES (Monthly)
    # ============================================================================
    standard_box_rate = fields.Monetary(
        string='TYPE 01 - Standard Box Rate',
        currency_field='currency_id',
        required=True,
        help='Monthly rate for TYPE 01 standard boxes (1.2 CF, 35 lbs avg)'
    )
    
    legal_box_rate = fields.Monetary(
        string='TYPE 02 - Legal/Banker Box Rate',
        currency_field='currency_id',
        required=True,
        help='Monthly rate for TYPE 02 legal boxes (2.4 CF, 65 lbs avg)'
    )
    
    map_box_rate = fields.Monetary(
        string='TYPE 03 - Map Box Rate',
        currency_field='currency_id',
        required=True,
        help='Monthly rate for TYPE 03 map boxes (0.875 CF, 35 lbs avg)'
    )
    
    odd_size_rate = fields.Monetary(
        string='TYPE 04 - Odd Size/Temp Box Rate',
        currency_field='currency_id',
        required=True,
        help='Monthly rate for TYPE 04 odd size boxes (5.0 CF, 75 lbs avg)'
    )
    
    pathology_rate = fields.Monetary(
        string='TYPE 06 - Pathology Box Rate',
        currency_field='currency_id',
        required=True,
        help='Monthly rate for TYPE 06 pathology boxes (0.042 CF, 40 lbs avg)'
    )

    # ============================================================================
    # SERVICE RATES
    # ============================================================================
    pickup_rate = fields.Monetary(
        string='Pickup Service Rate',
        currency_field='currency_id',
        required=True,
        help='Base rate per pickup service request'
    )
    
    delivery_rate = fields.Monetary(
        string='Delivery Service Rate',
        currency_field='currency_id',
        required=True,
        help='Base rate per delivery service request'
    )
    
    destruction_rate = fields.Monetary(
        string='Destruction Service Rate',
        currency_field='currency_id',
        required=True,
        help='Base rate per destruction service'
    )
    
    # Additional service rates
    document_retrieval_rate = fields.Monetary(
        string='Document Retrieval Rate',
        currency_field='currency_id',
        help='Rate per document retrieval request'
    )
    
    scanning_rate = fields.Monetary(
        string='Document Scanning Rate',
        currency_field='currency_id',
        help='Rate per document scanned'
    )
    
    indexing_rate = fields.Monetary(
        string='Document Indexing Rate',
        currency_field='currency_id',
        help='Rate per document indexed'
    )
    
    # Time-based rates
    technician_hourly_rate = fields.Monetary(
        string='Technician Hourly Rate',
        currency_field='currency_id',
        help='Hourly rate for field technician services'
    )
    
    supervisor_hourly_rate = fields.Monetary(
        string='Supervisor Hourly Rate',
        currency_field='currency_id',
        help='Hourly rate for supervisor oversight'
    )

    # ============================================================================
    # SETUP AND ONE-TIME FEES
    # ============================================================================
    new_customer_setup_fee = fields.Monetary(
        string='New Customer Setup Fee',
        currency_field='currency_id',
        help='One-time fee for new customer onboarding'
    )
    
    container_setup_fee = fields.Monetary(
        string='Container Setup Fee',
        currency_field='currency_id',
        help='One-time fee per new container setup'
    )
    
    barcode_generation_fee = fields.Monetary(
        string='Barcode Generation Fee',
        currency_field='currency_id',
        help='Fee for generating new container barcodes'
    )

    # ============================================================================
    # VOLUME-BASED RATE MODIFIERS
    # ============================================================================
    enable_volume_tiers = fields.Boolean(
        string='Enable Volume-Based Pricing',
        default=False,
        help='Enable volume-based rate modifications'
    )
    
    small_volume_threshold = fields.Integer(
        string='Small Volume Threshold',
        default=25,
        help='Container count for small volume (higher rate)'
    )
    
    small_volume_multiplier = fields.Float(
        string='Small Volume Multiplier',
        default=1.1,
        help='Rate multiplier for small volume customers'
    )
    
    large_volume_threshold = fields.Integer(
        string='Large Volume Threshold',
        default=100,
        help='Container count for large volume (discounted rate)'
    )
    
    large_volume_multiplier = fields.Float(
        string='Large Volume Multiplier',
        default=0.9,
        help='Rate multiplier for large volume customers'
    )
    
    enterprise_volume_threshold = fields.Integer(
        string='Enterprise Volume Threshold',
        default=500,
        help='Container count for enterprise volume (maximum discount)'
    )
    
    enterprise_volume_multiplier = fields.Float(
        string='Enterprise Volume Multiplier',
        default=0.75,
        help='Rate multiplier for enterprise volume customers'
    )

    # ============================================================================
    # LOCATION-BASED RATE MODIFIERS
    # ============================================================================
    enable_location_modifiers = fields.Boolean(
        string='Enable Location-Based Rates',
        default=False,
        help='Enable location-specific rate modifications'
    )
    
    premium_location_multiplier = fields.Float(
        string='Premium Location Multiplier',
        default=1.2,
        help='Rate multiplier for premium storage locations'
    )
    
    standard_location_multiplier = fields.Float(
        string='Standard Location Multiplier',
        default=1.0,
        help='Rate multiplier for standard storage locations'
    )
    
    economy_location_multiplier = fields.Float(
        string='Economy Location Multiplier',
        default=0.85,
        help='Rate multiplier for economy storage locations'
    )

    # ============================================================================
    # BILLING CONFIGURATION
    # ============================================================================
    billing_frequency_default = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    ], string='Default Billing Frequency', default='monthly')
    
    proration_method = fields.Selection([
        ('daily', 'Daily Proration'),
        ('monthly', 'Full Month'),
        ('none', 'No Proration')
    ], string='Proration Method', default='daily')
    
    minimum_monthly_charge = fields.Monetary(
        string='Minimum Monthly Charge',
        currency_field='currency_id',
        help='Minimum monthly charge regardless of container count'
    )

    # ============================================================================
    # COMPUTED RATE ANALYSIS FIELDS
    # ============================================================================
    average_container_rate = fields.Monetary(
        string='Average Container Rate',
        compute='_compute_rate_analysis',
        currency_field='currency_id',
        help='Average rate across all container types'
    )
    
    rate_per_cubic_foot = fields.Monetary(
        string='Average Rate per Cubic Foot',
        compute='_compute_rate_analysis',
        currency_field='currency_id',
        help='Average rate per cubic foot of storage'
    )
    
    total_service_rate = fields.Monetary(
        string='Total Service Rate',
        compute='_compute_rate_analysis',
        currency_field='currency_id',
        help='Combined rate for all services'
    )

    # Usage statistics
    customers_using_rates = fields.Integer(
        string='Customers Using These Rates',
        compute='_compute_usage_stats',
        help='Number of customers using these base rates'
    )
    
    containers_at_base_rates = fields.Integer(
        string='Containers at Base Rates',
        compute='_compute_usage_stats',
        help='Number of containers billed at these base rates'
    )

    # ============================================================================
    # WORKFLOW STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('standard_box_rate', 'legal_box_rate', 'map_box_rate', 'odd_size_rate', 'pathology_rate')
    def _compute_rate_analysis(self):
        """Compute rate analysis metrics"""
        for rate in self:
            # Calculate average container rate (weighted by typical usage)
            # TYPE 01 is most common (60%), TYPE 02 (25%), others (15%)
            total_rate = (
                rate.standard_box_rate * 0.60 +
                rate.legal_box_rate * 0.25 +
                rate.map_box_rate * 0.05 +
                rate.odd_size_rate * 0.05 +
                rate.pathology_rate * 0.05
            )
            rate.average_container_rate = total_rate
            
            # Calculate rate per cubic foot (weighted average)
            total_volume = (1.2 * 0.60) + (2.4 * 0.25) + (0.875 * 0.05) + (5.0 * 0.05) + (0.042 * 0.05)
            if total_volume > 0:
                rate.rate_per_cubic_foot = total_rate / total_volume
            else:
                rate.rate_per_cubic_foot = 0.0
            
            # Sum all service rates
            rate.total_service_rate = (
                rate.pickup_rate + rate.delivery_rate + rate.destruction_rate +
                (rate.document_retrieval_rate or 0.0) + (rate.scanning_rate or 0.0) +
                (rate.indexing_rate or 0.0)
            )

    def _compute_usage_stats(self):
        """Compute statistics on rate usage"""
        for rate in self:
            if not rate.active:
                rate.customers_using_rates = 0
                rate.containers_at_base_rates = 0
                continue
            
            # Count customers without negotiated rates
            all_customers = self.env['res.partner'].search([
                ('is_company', '=', True),
                ('company_id', '=', rate.company_id.id)
            ])
            
            customers_with_negotiated = self.env['customer.negotiated.rate'].search([
                ('state', '=', 'active'),
                ('company_id', '=', rate.company_id.id)
            ]).mapped('partner_id')
            
            customers_using_base = all_customers - customers_with_negotiated
            rate.customers_using_rates = len(customers_using_base)
            
            # Count containers for customers using base rates
            containers = self.env['records.container'].search([
                ('partner_id', 'in', customers_using_base.ids),
                ('active', '=', True)
            ])
            rate.containers_at_base_rates = len(containers)

    # ============================================================================
    # CONSTRAINT VALIDATIONS
    # ============================================================================
    @api.constrains('effective_date', 'expiration_date')
    def _check_date_validity(self):
        """Validate date range"""
        for rate in self:
            if rate.expiration_date and rate.effective_date > rate.expiration_date:
                raise ValidationError(_('Effective date cannot be after expiration date'))

    @api.constrains('small_volume_threshold', 'large_volume_threshold', 'enterprise_volume_threshold')
    def _check_volume_thresholds(self):
        """Validate volume thresholds are in ascending order"""
        for rate in self:
            if rate.enable_volume_tiers:
                if rate.small_volume_threshold >= rate.large_volume_threshold:
                    raise ValidationError(_('Large volume threshold must be greater than small volume threshold'))
                if rate.large_volume_threshold >= rate.enterprise_volume_threshold:
                    raise ValidationError(_('Enterprise volume threshold must be greater than large volume threshold'))

    @api.constrains('small_volume_multiplier', 'large_volume_multiplier', 'enterprise_volume_multiplier')
    def _check_multipliers(self):
        """Validate rate multipliers are reasonable"""
        for rate in self:
            multipliers = [rate.small_volume_multiplier, rate.large_volume_multiplier, rate.enterprise_volume_multiplier]
            for multiplier in multipliers:
                if multiplier <= 0 or multiplier > 10:
                    raise ValidationError(_('Rate multipliers must be between 0.01 and 10.00'))

    @api.constrains('company_id')
    def _check_unique_active_rate(self):
        """Ensure only one active base rate per company"""
        for rate in self:
            if rate.active:
                other_active = self.search([
                    ('company_id', '=', rate.company_id.id),
                    ('active', '=', True),
                    ('id', '!=', rate.id)
                ])
                if other_active:
                    raise ValidationError(_('Only one active base rate configuration is allowed per company'))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_container_rate(self, container_type, volume=None):
        """Get the rate for a specific container type"""
        self.ensure_one()
        
        base_rates = {
            'type_01': self.standard_box_rate,
            'type_02': self.legal_box_rate,
            'type_03': self.map_box_rate,
            'type_04': self.odd_size_rate,
            'type_06': self.pathology_rate,
        }
        
        return base_rates.get(container_type, self.standard_box_rate)

    def get_volume_multiplier(self, container_count):
        """Get volume-based rate multiplier"""
        self.ensure_one()
        
        if not self.enable_volume_tiers:
            return 1.0
        
        if container_count >= self.enterprise_volume_threshold:
            return self.enterprise_volume_multiplier
        elif container_count >= self.large_volume_threshold:
            return self.large_volume_multiplier
        elif container_count <= self.small_volume_threshold:
            return self.small_volume_multiplier
        else:
            return 1.0

    def get_location_multiplier(self, location_type):
        """Get location-based rate multiplier"""
        self.ensure_one()
        
        if not self.enable_location_modifiers:
            return 1.0
        
        multipliers = {
            'premium': self.premium_location_multiplier,
            'standard': self.standard_location_multiplier,
            'economy': self.economy_location_multiplier,
        }
        
        return multipliers.get(location_type, self.standard_location_multiplier)

    def calculate_customer_rate(self, partner_id, container_type, location_type='standard'):
        """Calculate final rate for a customer considering all modifiers"""
        self.ensure_one()
        
        # Get base container rate
        base_rate = self.get_container_rate(container_type)
        
        # Get customer's container count for volume multiplier
        container_count = self.env['records.container'].search_count([
            ('partner_id', '=', partner_id),
            ('active', '=', True)
        ])
        
        volume_multiplier = self.get_volume_multiplier(container_count)
        location_multiplier = self.get_location_multiplier(location_type)
        
        final_rate = base_rate * volume_multiplier * location_multiplier
        
        return {
            'base_rate': base_rate,
            'volume_multiplier': volume_multiplier,
            'location_multiplier': location_multiplier,
            'final_rate': final_rate,
            'container_count': container_count
        }

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_duplicate_rates(self):
        """Create a new version of these rates"""
        self.ensure_one()
        
        new_rate = self.copy({
            'name': _('%s (v%s)', self.name, fields.Datetime.now().strftime('%Y%m%d')),
            'effective_date': fields.Date.today(),
            'active': False,  # New rates start inactive
            'version': str(float(self.version or '1.0') + 0.1)
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Base Rate Configuration'),
            'res_model': 'base.rate',
            'res_id': new_rate.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def action_apply_increase(self):
        """Open wizard to apply percentage increase to all rates"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Apply Rate Increase'),
            'res_model': 'base.rate.increase.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_base_rate_id': self.id}
        }

    def action_view_customers_using_rates(self):
        """View customers using these base rates"""
        self.ensure_one()
        
        # Get customers without negotiated rates
        customers_with_negotiated = self.env['customer.negotiated.rate'].search([
            ('state', '=', 'active'),
            ('company_id', '=', self.company_id.id)
        ]).mapped('partner_id')
        
        all_customers = self.env['res.partner'].search([
            ('is_company', '=', True),
            ('company_id', '=', self.company_id.id)
        ])
        
        customers_using_base = all_customers - customers_with_negotiated
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customers Using Base Rates'),
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', customers_using_base.ids)],
            'context': {'default_company_id': self.company_id.id}
        }

    def action_activate_rates(self):
        """Activate these rates and deactivate others"""
        self.ensure_one()
        
        # Deactivate other active rates for this company
        other_rates = self.search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True),
            ('id', '!=', self.id)
        ])
        other_rates.write({'active': False})
        
        # Activate this rate
        self.write({'active': True, 'state': 'active'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Base rates activated successfully'),
                'type': 'success'
            }
        }

    def action_deactivate_rates(self):
        """Deactivate these rates"""
        self.ensure_one()
        
        self.write({'active': False, 'state': 'inactive'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Base rates deactivated successfully'),
                'type': 'success'
            }
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model
    def get_active_rate_for_company(self, company_id=None):
        """Get the active base rate for a company"""
        if not company_id:
            company_id = self.env.company.id
        
        return self.search([
            ('company_id', '=', company_id),
            ('active', '=', True)
        ], limit=1)

    @api.model
    def create_default_rates(self, company_id):
        """Create default base rates for a new company"""
        return self.create({
            'name': _('Default Base Rates'),
            'company_id': company_id,
            'standard_box_rate': 4.50,
            'legal_box_rate': 6.75,
            'map_box_rate': 3.95,
            'odd_size_rate': 22.50,
            'pathology_rate': 0.19,
            'pickup_rate': 50.00,
            'delivery_rate': 50.00,
            'destruction_rate': 75.00,
            'document_retrieval_rate': 15.00,
            'scanning_rate': 0.25,
            'indexing_rate': 0.15,
            'technician_hourly_rate': 45.00,
            'supervisor_hourly_rate': 65.00,
            'new_customer_setup_fee': 100.00,
            'container_setup_fee': 2.50,
            'barcode_generation_fee': 1.00,
            'minimum_monthly_charge': 25.00,
            'active': True,
            'state': 'active'
        })

    def get_service_rate(self, service_type):
        """Get rate for a specific service type"""
        self.ensure_one()
        
        service_rates = {
            'pickup': self.pickup_rate,
            'delivery': self.delivery_rate,
            'destruction': self.destruction_rate,
            'document_retrieval': self.document_retrieval_rate,
            'scanning': self.scanning_rate,
            'indexing': self.indexing_rate,
        }
        
        return service_rates.get(service_type, 0.0)

    def get_hourly_rate(self, role_type):
        """Get hourly rate for a specific role"""
        self.ensure_one()
        
        hourly_rates = {
            'technician': self.technician_hourly_rate,
            'supervisor': self.supervisor_hourly_rate,
        }
        
        return hourly_rates.get(role_type, self.technician_hourly_rate)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('standard_box_rate', 'legal_box_rate', 'map_box_rate', 'odd_size_rate', 'pathology_rate')
    def _check_container_rates(self):
        """Validate container rates are positive"""
        for record in self:
            container_rates = [
                record.standard_box_rate, record.legal_box_rate, record.map_box_rate,
                record.odd_size_rate, record.pathology_rate
            ]
            for rate in container_rates:
                if rate < 0:
                    raise ValidationError(_('Container rates cannot be negative'))

    @api.constrains('pickup_rate', 'delivery_rate', 'destruction_rate')
    def _check_service_rates(self):
        """Validate service rates are positive"""
        for record in self:
            service_rates = [record.pickup_rate, record.delivery_rate, record.destruction_rate]
            for rate in service_rates:
                if rate < 0:
                    raise ValidationError(_('Service rates cannot be negative'))

