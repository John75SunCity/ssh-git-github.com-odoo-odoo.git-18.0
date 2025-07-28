# -*- coding: utf-8 -*-
"""
Global Document Retrieval Rates Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class GlobalRetrievalRates(models.Model):
    """
    Global Document Retrieval Rates
    Base pricing model for document retrieval services
    """
    
    _name = 'global.rates'
    _description = 'Global Document Retrieval Rates'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'effective_date desc, name'
    _rec_name = 'name'
    
    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Rate Schedule Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Created By', 
                             default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    
    # ==========================================
    # RATE SCHEDULE DETAILS
    # ==========================================
    effective_date = fields.Date(string='Effective Date', required=True, 
                                 default=fields.Date.today, tracking=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    
    rate_type = fields.Selection([
        ('standard', 'Standard Rates'),
        ('premium', 'Premium Service'),
        ('economy', 'Economy Service'),
        ('government', 'Government Rates'),
        ('enterprise', 'Enterprise Rates')
    ], string='Rate Type', default='standard', required=True, tracking=True)
    
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                 default=lambda self: self.env.company.currency_id, required=True)
    
    # ==========================================
    # STATUS AND VERSION CONTROL
    # ==========================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('superseded', 'Superseded'),
        ('expired', 'Expired')
    ], string='Status', default='draft', tracking=True, required=True)
    
    version = fields.Char(string='Version', default='1.0', tracking=True)
    previous_version_id = fields.Many2one('global.rates', string='Previous Version')
    next_version_id = fields.Many2one('global.rates', string='Next Version')
    
    # ==========================================
    # BASE PRICING STRUCTURE
    # ==========================================
    
    # Document-based pricing
    base_document_rate = fields.Float(string='Base Rate per Document', 
                                     digits='Product Price', required=True,
                                     help='Base rate for retrieving a single document')
    
    # Page-based pricing
    page_rate = fields.Float(string='Rate per Page', digits='Product Price',
                            help='Additional rate per page for large documents')
    page_threshold = fields.Integer(string='Page Threshold', default=10,
                                   help='Documents with more pages incur page charges')
    
    # Box-based pricing
    box_handling_rate = fields.Float(string='Box Handling Rate', digits='Product Price',
                                    help='Rate for handling documents from boxes')
    
    # ==========================================
    # URGENCY MULTIPLIERS
    # ==========================================
    standard_multiplier = fields.Float(string='Standard Service Multiplier', default=1.0,
                                      help='Multiplier for standard service (usually 1.0)')
    
    expedited_multiplier = fields.Float(string='Expedited Service Multiplier', default=1.5,
                                       help='Multiplier for expedited service')
    
    rush_multiplier = fields.Float(string='Rush Service Multiplier', default=2.0,
                                  help='Multiplier for rush/emergency service')
    
    same_day_multiplier = fields.Float(string='Same Day Service Multiplier', default=3.0,
                                      help='Multiplier for same-day service')
    
    # ==========================================
    # VOLUME DISCOUNTS
    # ==========================================
    volume_discount_enabled = fields.Boolean(string='Enable Volume Discounts', default=True)
    
    # Volume thresholds and discounts
    volume_tier_1_threshold = fields.Integer(string='Tier 1 Threshold', default=50,
                                            help='Minimum documents for tier 1 discount')
    volume_tier_1_discount = fields.Float(string='Tier 1 Discount %', default=5.0,
                                         help='Discount percentage for tier 1')
    
    volume_tier_2_threshold = fields.Integer(string='Tier 2 Threshold', default=100,
                                            help='Minimum documents for tier 2 discount')
    volume_tier_2_discount = fields.Float(string='Tier 2 Discount %', default=10.0,
                                         help='Discount percentage for tier 2')
    
    volume_tier_3_threshold = fields.Integer(string='Tier 3 Threshold', default=500,
                                            help='Minimum documents for tier 3 discount')
    volume_tier_3_discount = fields.Float(string='Tier 3 Discount %', default=15.0,
                                         help='Discount percentage for tier 3')
    
    # ==========================================
    # SERVICE TYPE RATES
    # ==========================================
    
    # Digital delivery
    digital_delivery_rate = fields.Float(string='Digital Delivery Rate', digits='Product Price',
                                        help='Additional rate for digital/electronic delivery')
    
    # Secure delivery
    secure_delivery_rate = fields.Float(string='Secure Delivery Rate', digits='Product Price',
                                       help='Additional rate for secure/courier delivery')
    
    # Research services
    research_hourly_rate = fields.Float(string='Research Hourly Rate', digits='Product Price',
                                       help='Hourly rate for research services')
    
    # Certification services
    certification_rate = fields.Float(string='Certification Rate', digits='Product Price',
                                     help='Rate for document certification')
    
    # ==========================================
    # ADDITIONAL FEES
    # ==========================================
    
    # Setup and handling fees
    minimum_charge = fields.Float(string='Minimum Charge', digits='Product Price',
                                 help='Minimum charge per request')
    
    handling_fee = fields.Float(string='Handling Fee', digits='Product Price',
                               help='Base handling fee per request')
    
    # Travel and location fees
    on_site_service_rate = fields.Float(string='On-Site Service Rate', digits='Product Price',
                                       help='Additional rate for on-site services')
    
    travel_rate_per_mile = fields.Float(string='Travel Rate per Mile', digits='Product Price',
                                       help='Rate per mile for travel')
    
    # ==========================================
    # SERVICE LEVEL AGREEMENTS
    # ==========================================
    
    # Turnaround times (in hours)
    standard_turnaround = fields.Integer(string='Standard Turnaround (hours)', default=72)
    expedited_turnaround = fields.Integer(string='Expedited Turnaround (hours)', default=24)
    rush_turnaround = fields.Integer(string='Rush Turnaround (hours)', default=4)
    same_day_turnaround = fields.Integer(string='Same Day Turnaround (hours)', default=2)
    
    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    
    @api.depends('effective_date', 'expiry_date')
    def _compute_is_current(self):
        """Check if rate schedule is currently active"""
        today = fields.Date.today()
        for rate in self:
            is_current = (rate.effective_date <= today and 
                         (not rate.expiry_date or rate.expiry_date >= today) and
                         rate.state == 'active')
            rate.is_current = is_current
    
    is_current = fields.Boolean(string='Current Rate Schedule', 
                               compute='_compute_is_current', store=True)
    
    # ==========================================
    # CRUD METHODS
    # ==========================================
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle versioning"""
        records = super().create(vals_list)
        for record in records:
            if not record.version:
                record.version = '1.0'
        return records
    
    def copy(self, default=None):
        """Override copy to create new version"""
        default = dict(default or {})
        default.update({
            'name': _('%s (Copy)') % self.name,
            'state': 'draft',
            'effective_date': fields.Date.today(),
            'expiry_date': False,
            'previous_version_id': self.id,
        })
        
        # Auto-increment version
        if self.version:
            try:
                version_parts = self.version.split('.')
                major = int(version_parts[0])
                minor = int(version_parts[1]) if len(version_parts) > 1 else 0
                default['version'] = f"{major}.{minor + 1}"
            except:
                default['version'] = '1.0'
        
        new_record = super().copy(default)
        self.next_version_id = new_record.id
        return new_record
    
    # ==========================================
    # WORKFLOW ACTIONS
    # ==========================================
    
    def action_activate(self):
        """Activate rate schedule"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft rate schedules can be activated'))
        
        # Check for overlapping active schedules
        overlapping = self.search([
            ('id', '!=', self.id),
            ('rate_type', '=', self.rate_type),
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'active'),
            ('effective_date', '<=', self.expiry_date or fields.Date.max),
            '|', ('expiry_date', '=', False), ('expiry_date', '>=', self.effective_date)
        ])
        
        if overlapping:
            raise UserError(_('There are overlapping active rate schedules: %s') % 
                          ', '.join(overlapping.mapped('name')))
        
        self.write({'state': 'active'})
        self.message_post(body=_('Rate schedule activated'))
    
    def action_supersede(self):
        """Mark rate schedule as superseded"""
        self.ensure_one()
        if self.state != 'active':
            raise UserError(_('Only active rate schedules can be superseded'))
        
        self.write({
            'state': 'superseded',
            'expiry_date': fields.Date.today()
        })
        self.message_post(body=_('Rate schedule superseded'))
    
    def action_expire(self):
        """Mark rate schedule as expired"""
        self.ensure_one()
        if self.state not in ['active', 'superseded']:
            raise UserError(_('Only active or superseded rate schedules can be expired'))
        
        self.write({'state': 'expired'})
        self.message_post(body=_('Rate schedule expired'))
    
    def action_create_new_version(self):
        """Create a new version of this rate schedule"""
        self.ensure_one()
        new_version = self.copy()
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'global.rates',
            'res_id': new_version.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    # ==========================================
    # CALCULATION METHODS
    # ==========================================
    
    def calculate_base_cost(self, document_count=1, page_count=0, box_count=0):
        """Calculate base cost for retrieval"""
        self.ensure_one()
        
        # Base document cost
        base_cost = document_count * self.base_document_rate
        
        # Add page charges if applicable
        if page_count > (document_count * self.page_threshold):
            excess_pages = page_count - (document_count * self.page_threshold)
            base_cost += excess_pages * self.page_rate
        
        # Add box handling charges
        if box_count > 0:
            base_cost += box_count * self.box_handling_rate
        
        return base_cost
    
    def apply_urgency_multiplier(self, base_cost, urgency='standard'):
        """Apply urgency multiplier to base cost"""
        self.ensure_one()
        
        multipliers = {
            'standard': self.standard_multiplier,
            'expedited': self.expedited_multiplier,
            'rush': self.rush_multiplier,
            'same_day': self.same_day_multiplier,
        }
        
        multiplier = multipliers.get(urgency, self.standard_multiplier)
        return base_cost * multiplier
    
    def apply_volume_discount(self, base_cost, document_count):
        """Apply volume discount based on document count"""
        self.ensure_one()
        
        if not self.volume_discount_enabled:
            return base_cost
        
        discount_percent = 0.0
        
        if document_count >= self.volume_tier_3_threshold:
            discount_percent = self.volume_tier_3_discount
        elif document_count >= self.volume_tier_2_threshold:
            discount_percent = self.volume_tier_2_discount
        elif document_count >= self.volume_tier_1_threshold:
            discount_percent = self.volume_tier_1_discount
        
        discount_amount = base_cost * (discount_percent / 100.0)
        return base_cost - discount_amount
    
    def calculate_total_cost(self, document_count=1, page_count=0, box_count=0, 
                           urgency='standard', include_fees=True):
        """Calculate total cost including all factors"""
        self.ensure_one()
        
        # Calculate base cost
        base_cost = self.calculate_base_cost(document_count, page_count, box_count)
        
        # Apply urgency multiplier
        cost_with_urgency = self.apply_urgency_multiplier(base_cost, urgency)
        
        # Apply volume discount
        cost_with_discount = self.apply_volume_discount(cost_with_urgency, document_count)
        
        # Add fees if requested
        if include_fees:
            cost_with_discount += self.handling_fee
            
            # Apply minimum charge
            if cost_with_discount < self.minimum_charge:
                cost_with_discount = self.minimum_charge
        
        return cost_with_discount
    
    def get_turnaround_time(self, urgency='standard'):
        """Get turnaround time for urgency level"""
        self.ensure_one()
        
        turnaround_times = {
            'standard': self.standard_turnaround,
            'expedited': self.expedited_turnaround,
            'rush': self.rush_turnaround,
            'same_day': self.same_day_turnaround,
        }
        
        return turnaround_times.get(urgency, self.standard_turnaround)
    
    # ==========================================
    # VALIDATION
    # ==========================================
    
    @api.constrains('effective_date', 'expiry_date')
    def _check_dates(self):
        """Validate effective and expiry dates"""
        for rate in self:
            if rate.expiry_date and rate.effective_date > rate.expiry_date:
                raise ValidationError(_('Effective date cannot be after expiry date'))
    
    @api.constrains('base_document_rate')
    def _check_base_rate(self):
        """Validate base document rate"""
        for rate in self:
            if rate.base_document_rate <= 0:
                raise ValidationError(_('Base document rate must be positive'))
    
    @api.constrains('volume_tier_1_threshold', 'volume_tier_2_threshold', 'volume_tier_3_threshold')
    def _check_volume_thresholds(self):
        """Validate volume tier thresholds"""
        for rate in self:
            if (rate.volume_tier_1_threshold >= rate.volume_tier_2_threshold or
                rate.volume_tier_2_threshold >= rate.volume_tier_3_threshold):
                raise ValidationError(_('Volume tier thresholds must be in ascending order'))
    
    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    @api.model
    def get_current_rates(self, rate_type='standard', company_id=None):
        """Get current active rates for a type and company"""
        if not company_id:
            company_id = self.env.company.id
        
        current_rates = self.search([
            ('rate_type', '=', rate_type),
            ('company_id', '=', company_id),
            ('state', '=', 'active'),
            ('is_current', '=', True)
        ], limit=1)
        
        return current_rates
    
    def get_rate_summary(self):
        """Get formatted rate summary"""
        self.ensure_one()
        
        return {
            'name': self.name,
            'version': self.version,
            'effective_date': self.effective_date,
            'base_rate': self.base_document_rate,
            'currency': self.currency_id.name,
            'rate_type': dict(self._fields['rate_type'].selection)[self.rate_type],
            'status': dict(self._fields['state'].selection)[self.state],
        }
