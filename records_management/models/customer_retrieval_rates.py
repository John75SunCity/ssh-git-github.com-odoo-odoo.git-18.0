# -*- coding: utf-8 -*-
"""
Customer Retrieval Rates Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class CustomerRetrievalRates(models.Model):
    """
    Customer-Specific Document Retrieval Rates
    Manages custom pricing for document retrieval services per customer
    """
    
    _name = 'customer.retrieval.rates'
    _description = 'Customer Retrieval Rates'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'customer_id, priority desc'
    _rec_name = 'name'
    
    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Rate Name', compute='_compute_name', store=True)
    description = fields.Text(string='Rate Description', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Rate Manager', 
                             default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    
    # ==========================================
    # CUSTOMER INFORMATION
    # ==========================================
    customer_id = fields.Many2one('res.partner', string='Customer', 
                                 required=True, tracking=True,
                                 domain=[('is_company', '=', True)])
    department_id = fields.Many2one('records.department', string='Department', tracking=True)
    
    # ==========================================
    # RATE CONFIGURATION
    # ==========================================
    rate_type = fields.Selection([
        ('standard', 'Standard Rate'),
        ('expedited', 'Expedited Rate'),
        ('emergency', 'Emergency Rate'),
        ('bulk', 'Bulk Rate'),
        ('contract', 'Contract Rate')
    ], string='Rate Type', default='standard', required=True, tracking=True)
    
    priority = fields.Selection([
        ('1', 'Low Priority'),
        ('2', 'Normal Priority'),
        ('3', 'High Priority'),
        ('4', 'Urgent Priority')
    ], string='Priority', default='2', tracking=True)
    
    # ==========================================
    # PRICING STRUCTURE
    # ==========================================
    base_rate = fields.Float(string='Base Rate per Document', required=True, tracking=True,
                            help='Base price for retrieving one document')
    per_page_rate = fields.Float(string='Per Page Rate', tracking=True,
                                help='Additional charge per page')
    per_box_rate = fields.Float(string='Per Box Rate', tracking=True,
                               help='Charge for accessing a box')
    
    # Volume discounts
    min_quantity = fields.Integer(string='Minimum Quantity', default=1, tracking=True)
    max_quantity = fields.Integer(string='Maximum Quantity', tracking=True)
    discount_rate = fields.Float(string='Volume Discount %', tracking=True,
                                help='Discount percentage for volume orders')
    
    # Time-based pricing
    rush_multiplier = fields.Float(string='Rush Multiplier', default=1.0, tracking=True,
                                  help='Multiplier for rush orders')
    same_day_multiplier = fields.Float(string='Same Day Multiplier', default=1.5, tracking=True)
    next_day_multiplier = fields.Float(string='Next Day Multiplier', default=1.2, tracking=True)
    
    # ==========================================
    # SERVICE SPECIFICATIONS
    # ==========================================
    service_level = fields.Selection([
        ('basic', 'Basic Retrieval'),
        ('standard', 'Standard Service'),
        ('premium', 'Premium Service'),
        ('white_glove', 'White Glove Service')
    ], string='Service Level', default='standard', tracking=True)
    
    delivery_method = fields.Selection([
        ('pickup', 'Customer Pickup'),
        ('courier', 'Courier Delivery'),
        ('mail', 'Mail Delivery'),
        ('digital', 'Digital Delivery'),
        ('secure_transport', 'Secure Transport')
    ], string='Delivery Method', tracking=True)
    
    # ==========================================
    # TIME SPECIFICATIONS
    # ==========================================
    standard_turnaround = fields.Integer(string='Standard Turnaround (Hours)', 
                                        default=24, tracking=True)
    expedited_turnaround = fields.Integer(string='Expedited Turnaround (Hours)', 
                                         default=4, tracking=True)
    emergency_turnaround = fields.Integer(string='Emergency Turnaround (Hours)', 
                                         default=1, tracking=True)
    
    # ==========================================
    # VALIDITY AND CONDITIONS
    # ==========================================
    valid_from = fields.Date(string='Valid From', default=fields.Date.today, required=True)
    valid_to = fields.Date(string='Valid To', tracking=True)
    
    contract_reference = fields.Char(string='Contract Reference', tracking=True)
    terms_and_conditions = fields.Text(string='Terms and Conditions')
    
    # ==========================================
    # APPROVAL WORKFLOW
    # ==========================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)
    
    approved_by_id = fields.Many2one('res.users', string='Approved By', tracking=True)
    approval_date = fields.Datetime(string='Approval Date', tracking=True)
    
    # ==========================================
    # USAGE STATISTICS
    # ==========================================
    usage_count = fields.Integer(string='Times Used', readonly=True)
    total_revenue = fields.Float(string='Total Revenue', readonly=True)
    last_used_date = fields.Datetime(string='Last Used', readonly=True)
    
    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends('customer_id', 'rate_type', 'service_level')
    def _compute_name(self):
        """Compute display name"""
        for record in self:
            if record.customer_id:
                name_parts = [record.customer_id.name]
                if record.rate_type:
                    name_parts.append(record.rate_type.title())
                if record.service_level:
                    name_parts.append(record.service_level.title())
                record.name = ' - '.join(name_parts)
            else:
                record.name = 'New Rate'
    
    # ==========================================
    # WORKFLOW ACTIONS
    # ==========================================
    def action_submit(self):
        """Submit rate for approval"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft rates can be submitted'))
        
        self.write({'state': 'submitted'})
        self.message_post(body=_('Rate submitted for approval'))
    
    def action_approve(self):
        """Approve rate"""
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_('Only submitted rates can be approved'))
        
        self.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now()
        })
        self.message_post(body=_('Rate approved by %s') % self.env.user.name)
    
    def action_activate(self):
        """Activate rate"""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Only approved rates can be activated'))
        
        # Check validity dates
        today = fields.Date.today()
        if self.valid_from > today:
            raise UserError(_('Rate is not yet valid'))
        if self.valid_to and self.valid_to < today:
            raise UserError(_('Rate has expired'))
        
        self.write({'state': 'active'})
        self.message_post(body=_('Rate activated'))
    
    def action_cancel(self):
        """Cancel rate"""
        self.ensure_one()
        if self.state in ['expired']:
            raise UserError(_('Cannot cancel expired rates'))
        
        self.write({'state': 'cancelled'})
        self.message_post(body=_('Rate cancelled'))
    
    # ==========================================
    # PRICING CALCULATION METHODS
    # ==========================================
    def calculate_retrieval_cost(self, document_count=1, page_count=0, box_count=1, 
                                urgency='standard', delivery_date=None):
        """Calculate total cost for retrieval based on parameters"""
        self.ensure_one()
        
        if self.state != 'active':
            raise UserError(_('Cannot use inactive rate'))
        
        # Base calculation
        total_cost = 0.0
        
        # Document base cost
        total_cost += self.base_rate * document_count
        
        # Per page cost
        if page_count and self.per_page_rate:
            total_cost += self.per_page_rate * page_count
        
        # Per box cost
        if box_count and self.per_box_rate:
            total_cost += self.per_box_rate * box_count
        
        # Volume discount
        if (self.min_quantity <= document_count and 
            (not self.max_quantity or document_count <= self.max_quantity) and 
            self.discount_rate):
            discount = total_cost * (self.discount_rate / 100)
            total_cost -= discount
        
        # Urgency multiplier
        if urgency == 'rush' and self.rush_multiplier:
            total_cost *= self.rush_multiplier
        elif urgency == 'same_day' and self.same_day_multiplier:
            total_cost *= self.same_day_multiplier
        elif urgency == 'next_day' and self.next_day_multiplier:
            total_cost *= self.next_day_multiplier
        
        return total_cost
    
    def get_turnaround_time(self, urgency='standard'):
        """Get turnaround time for urgency level"""
        self.ensure_one()
        
        if urgency == 'expedited':
            return self.expedited_turnaround
        elif urgency == 'emergency':
            return self.emergency_turnaround
        else:
            return self.standard_turnaround
    
    # ==========================================
    # CRON METHODS
    # ==========================================
    @api.model
    def _cron_expire_rates(self):
        """Cron job to expire rates past their validity date"""
        today = fields.Date.today()
        expired_rates = self.search([
            ('state', '=', 'active'),
            ('valid_to', '<', today)
        ])
        
        for rate in expired_rates:
            rate.write({'state': 'expired'})
            rate.message_post(body=_('Rate automatically expired'))
        
        _logger.info(f'Expired {len(expired_rates)} customer retrieval rates')
    
    # ==========================================
    # VALIDATION
    # ==========================================
    @api.constrains('base_rate', 'per_page_rate', 'per_box_rate')
    def _check_rates(self):
        """Validate rate values"""
        for record in self:
            if record.base_rate < 0:
                raise ValidationError(_('Base rate cannot be negative'))
            if record.per_page_rate < 0:
                raise ValidationError(_('Per page rate cannot be negative'))
            if record.per_box_rate < 0:
                raise ValidationError(_('Per box rate cannot be negative'))
    
    @api.constrains('min_quantity', 'max_quantity')
    def _check_quantities(self):
        """Validate quantity ranges"""
        for record in self:
            if record.min_quantity < 1:
                raise ValidationError(_('Minimum quantity must be at least 1'))
            if record.max_quantity and record.max_quantity < record.min_quantity:
                raise ValidationError(_('Maximum quantity cannot be less than minimum'))
    
    @api.constrains('valid_from', 'valid_to')
    def _check_validity_dates(self):
        """Validate validity dates"""
        for record in self:
            if record.valid_to and record.valid_to < record.valid_from:
                raise ValidationError(_('Valid to date cannot be before valid from date'))
    
    # ==========================================
    # USAGE TRACKING
    # ==========================================
    def record_usage(self, revenue=0.0):
        """Record usage of this rate"""
        self.ensure_one()
        self.write({
            'usage_count': self.usage_count + 1,
            'total_revenue': self.total_revenue + revenue,
            'last_used_date': fields.Datetime.now()
        })
