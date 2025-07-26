# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ShreddingBaseRates(models.Model):
    """Base rates for shredding services"""
    _name = 'shredding.base.rates'
    _description = 'Shredding Base Rates'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'effective_date desc'
    _rec_name = 'display_name'

    # Core fields
    name = fields.Char(string='Rate Name', required=True, tracking=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)
    effective_date = fields.Date(string='Effective Date', required=True, default=fields.Date.today, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    
    # Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired')
    ], default='draft', tracking=True)
    
    # External Shredding Rates (per bin/box)
    external_per_bin_rate = fields.Float(string='External Per Bin Rate', digits=(16, 2), tracking=True)
    external_service_call_rate = fields.Float(string='External Service Call Rate', digits=(16, 2), tracking=True)
    
    # Managed Inventory Rates
    managed_retrieval_rate = fields.Float(string='Managed Retrieval Rate', digits=(16, 2), tracking=True,
                                         help="Rate for retrieving items from warehouse for destruction")
    managed_permanent_removal_rate = fields.Float(string='Managed Permanent Removal Rate', digits=(16, 2), tracking=True,
                                                  help="Rate for permanent removal from inventory")
    managed_shredding_rate = fields.Float(string='Managed Shredding Rate', digits=(16, 2), tracking=True,
                                         help="Rate for actual shredding/destruction service")
    managed_service_call_rate = fields.Float(string='Managed Service Call Rate', digits=(16, 2), tracking=True,
                                            help="Base service call rate for managed inventory")
    
    # Company
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    @api.depends('name', 'effective_date')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} ({record.effective_date})"
    
    def action_activate(self):
        """Activate these rates"""
        self.ensure_one()
        # Deactivate other active rates for the same company
        self.search([
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'active'),
            ('id', '!=', self.id)
        ]).write({'state': 'expired'})
        
        self.write({'state': 'active'})
        return True
    
    @api.model
    def get_current_rates(self, company_id=None):
        """Get current active rates"""
        if not company_id:
            company_id = self.env.company.id
        
        return self.search([
            ('company_id', '=', company_id),
            ('state', '=', 'active'),
            ('effective_date', '<=', fields.Date.today())
        ], limit=1)

class ShreddingCustomerRates(models.Model):
    """Customer-specific shredding rates"""
    _name = 'shredding.customer.rates'
    _description = 'Customer Shredding Rates'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'partner_id, effective_date desc'
    _rec_name = 'display_name'

    # Core fields
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    
    # Workflow
        ('active', 'Active'),
        ('expired', 'Expired')
    ], default='draft', tracking=True)
    
    # External Shredding Rates (overrides for base rates)
    use_custom_external_rates = fields.Boolean(string='Use Custom External Rates', tracking=True)
    
    # Managed Inventory Rates (overrides for base rates)
    use_custom_managed_rates = fields.Boolean(string='Use Custom Managed Rates', tracking=True)
    
    # Discount/Markup
    discount_percentage = fields.Float(string='Discount Percentage', digits=(5, 2), tracking=True,
                                      help="Percentage discount from base rates")
    
    # Company
    
    @api.depends('name', 'partner_id.name', 'effective_date')
    def _compute_display_name(self):
        for record in self:
            partner_name = record.partner_id.name if record.partner_id else 'No Customer'
            record.display_name = f"{record.name} - {partner_name} ({record.effective_date})"
    
    @api.constrains('effective_date', 'expiry_date')
    def _check_date_range(self):
        for record in self:
            if record.expiry_date and record.effective_date > record.expiry_date:
                raise ValidationError(_('Effective date cannot be after expiry date.'))
    
    def action_activate(self):
        """Activate these rates"""
        self.ensure_one()
        # Deactivate other active rates for the same customer
        self.search([
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'active'),
            ('id', '!=', self.id)
        ]).write({'state': 'expired'})
        
        self.write({'state': 'active'})
        return True
    
    @api.model
    def get_customer_rates(self, partner_id, company_id=None):
        """Get current customer rates"""
        if not company_id:
            company_id = self.env.company.id
        
        domain = [
            ('partner_id', '=', partner_id),
            ('company_id', '=', company_id),
            ('state', '=', 'active'),
            ('effective_date', '<=', fields.Date.today())
        
        # Check expiry date
        today = fields.Date.today()
        domain.append('|')
        domain.append(('expiry_date', '=', False))
        domain.append(('expiry_date', '>=', today))
        
        return self.search(domain, limit=1)
    
    def get_effective_rate(self, rate_type, base_rates=None):
        """Get effective rate considering custom rates and discounts"""
        self.ensure_one()
        
        # Map rate types to field names
        rate_fields = {
            'external_per_bin': 'external_per_bin_rate',
            'external_service_call': 'external_service_call_rate',
            'managed_retrieval': 'managed_retrieval_rate',
            'managed_permanent_removal': 'managed_permanent_removal_rate',
            'managed_shredding': 'managed_shredding_rate',
            'managed_service_call': 'managed_service_call_rate',
        }
        
        if rate_type not in rate_fields:
            raise UserError(_('Invalid rate type: %s') % rate_type)
        
        field_name = rate_fields[rate_type]
        
        # Check if custom rate is defined
        is_external = rate_type.startswith('external_')
        is_managed = rate_type.startswith('managed_')
        
        custom_rate = None
        if is_external and self.use_custom_external_rates:
            custom_rate = getattr(self, field_name, 0.0)
        elif is_managed and self.use_custom_managed_rates:
            custom_rate = getattr(self, field_name, 0.0)
        
        if custom_rate:
            return custom_rate
        
        # Use base rate with discount
        if not base_rates:
            base_rates = self.env['shredding.base.rates'].get_current_rates(self.company_id.id)
        
        if not base_rates:
            return 0.0
        
        base_rate = getattr(base_rates, field_name, 0.0)
        
        # Apply discount if configured
        if self.discount_percentage:
            discount_multiplier = (100 - self.discount_percentage) / 100
            return base_rate * discount_multiplier
        
        return base_rate
