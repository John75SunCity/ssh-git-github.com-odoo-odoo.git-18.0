# -*- coding: utf-8 -*-
"""
Legacy Customer Retrieval Rates - MIGRATED TO NEW RATE SYSTEM
This file maintains compatibility while redirecting to the new unified rate system
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class CustomerRetrievalRates(models.Model):
    """
    LEGACY MODEL - Redirects to customer.rate.profile system
    Use customer.rate.profile with service categories instead
    """
    
    _name = 'customer.retrieval.rates'
    _description = 'Customer Retrieval Rates (Legacy - Use customer.rate.profile)'
    _inherit = 'customer.rate.profile'
    
    def create(self, vals):
        """Override to set service category to retrieval"""
        # Map legacy fields to new system
        if 'customer_id' in vals:
            vals['partner_id'] = vals.pop('customer_id')
        
        # Set default service settings for retrieval
        vals.update({
            'profile_type': 'service_specific',
            'service_category': 'pickup'
        })
        
        return super().create(vals)
    
    # Legacy field mappings for backward compatibility
    customer_id = fields.Many2one('res.partner', related='partner_id', readonly=False)
    rate_type = fields.Selection([
        ('standard', 'Standard Rate'),
        ('expedited', 'Expedited Rate'),
        ('emergency', 'Emergency Rate'),
        ('bulk', 'Bulk Rate'),
        ('contract', 'Contract Rate')
    ], string='Rate Type', default='standard')
    
    base_rate = fields.Float(string='Base Rate per Document', 
                            help='Base price for retrieving one document')
    per_file_rate = fields.Float(string='Per File Rate',
                                help='Additional charge per individual file')
    per_page_rate = fields.Float(string='Per Page Rate',
                                help='Additional charge per page')
    per_box_rate = fields.Float(string='Per Box Rate',
                               help='Charge for accessing a box')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    
    @api.depends('partner_id', 'rate_type', 'profile_type')
    def _compute_name(self):
        """Compute display name - Legacy compatibility"""
        for record in self:
            if record.partner_id:
                name_parts = [record.partner_id.name]
                if record.rate_type:
                    name_parts.append(record.rate_type.title())
                record.name = ' - '.join(name_parts)
            else:
                record.name = 'New Rate'
    
    def calculate_retrieval_cost(self, document_count=1, file_count=0, page_count=0, 
                                box_count=1, urgency='standard', delivery_date=None):
        """
        Legacy method - redirects to new rate calculation system
        """
        # Use the new rate calculation system
        return self.calculate_rate(
            quantity=document_count,
            service_type='retrieval',
            urgency_level=urgency
        )
    
    @api.model
    def migrate_to_new_system(self):
        """
        Migrate all existing customer retrieval rates to new customer.rate.profile system
        This should be run once during upgrade
        """
        _logger.info("Migrating customer retrieval rates to new customer.rate.profile system...")
        
        # Find all existing customer rates that haven't been migrated
        legacy_rates = self.search([('profile_type', '=', False)])
        
        for rate in legacy_rates:
            # Update to use new system structure
            rate.write({
                'profile_type': 'service_specific',
                'service_category': 'pickup',
                'adjustment_type': 'percentage_discount' if rate.discount_rate else 'override',
                'adjustment_value': rate.discount_rate or 0.0,
                'state': 'active' if rate.state == 'active' else 'draft'
            })
            
            # Create rate adjustments for the specific rates
            if rate.base_rate:
                self.env['rate.adjustment'].create({
                    'profile_id': rate.id,
                    'service_type': 'retrieval',
                    'adjustment_type': 'override',
                    'adjustment_value': rate.base_rate,
                    'description': f'Base retrieval rate: ${rate.base_rate}',
                    'state': 'active'
                })
                
        _logger.info("Customer retrieval rates migration completed")
        return True
