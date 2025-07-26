# -*- coding: utf-8 -*-
"""
Document Retrieval Work Order Management with Priority Pricing System

This module handles document retrieval requests with customer-specific rates,
priority levels, and transparent pricing for both customers and technicians.

Pricing Structure:
- Base retrieval: $3.50 per box/file + $25.00 delivery
- Priority levels with additional fees per item and per work order
- Customer-specific rate overrides
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class DocumentRetrievalRates(models.Model):
    """Base rates for document retrieval services"""
    _name = 'document.retrieval.rates'
    _description = 'Document Retrieval Base Rates'
    _rec_name = 'name'

    name = fields.Char(string='Rate Name', required=True)
    
    # Base rates
    base_retrieval_rate = fields.Float(
        string='Base Retrieval Rate per Item',
        default=3.50,
        help='Standard cost per box/file retrieved'
    )
    
    base_delivery_rate = fields.Float(
        string='Base Delivery Rate per Order',
        default=25.00,
        help='Standard delivery fee per work order'
    )
    
    # Priority rates - per item
    rush_end_of_day_item = fields.Float(
        string='Rush (End of Day) - Per Item',
        default=1.50,
        help='Additional fee per item for end-of-day delivery'
    )
    
    rush_4_hours_item = fields.Float(
        string='Rush (4 Hours) - Per Item',
        default=3.00,
        help='Additional fee per item for 4-hour delivery'
    )
    
    emergency_1_hour_item = fields.Float(
        string='Emergency (1 Hour) - Per Item',
        default=7.50,
        help='Additional fee per item for 1-hour delivery'
    )
    
    weekend_item = fields.Float(
        string='Weekend Service - Per Item',
        default=5.00,
        help='Additional fee per item for weekend service'
    )
    
    holiday_item = fields.Float(
        string='Holiday Service - Per Item',
        default=10.00,
        help='Additional fee per item for holiday service'
    )
    
    # Priority rates - per work order
    rush_end_of_day_order = fields.Float(
        string='Rush (End of Day) - Per Order',
        default=15.00,
        help='Additional delivery fee for end-of-day orders'
    )
    
    rush_4_hours_order = fields.Float(
        string='Rush (4 Hours) - Per Order',
        default=35.00,
        help='Additional delivery fee for 4-hour orders'
    )
    
    emergency_1_hour_order = fields.Float(
        string='Emergency (1 Hour) - Per Order',
        default=75.00,
        help='Additional delivery fee for 1-hour orders'
    )
    
    weekend_order = fields.Float(
        string='Weekend Service - Per Order',
        default=50.00,
        help='Additional delivery fee for weekend orders'
    )
    
    holiday_order = fields.Float(
        string='Holiday Service - Per Order',
        default=100.00,
        help='Additional delivery fee for holiday orders'
    )
    
    # Working hours and days
    working_hours_start = fields.Float(
        string='Working Hours Start',
        default=8.0,
        help='Start of working hours (24-hour format)'
    )
    
    working_hours_end = fields.Float(
        string='Working Hours End',
        default=17.0,
        help='End of working hours (24-hour format)'
    )
    
    # Company and date tracking
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    
    active = fields.Boolean(default=True)
    effective_date = fields.Date(
        string='Effective Date',
        default=fields.Date.today,
        required=True
    )


class CustomerRetrievalRates(models.Model):
    """Customer-specific retrieval rate overrides"""
    _name = 'customer.retrieval.rates'
    _description = 'Customer-Specific Retrieval Rates'
    _rec_name = 'display_name'

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        domain=[('is_company', '=', True)]
    )
    
    # Override base rates (if 0.0, use base rates)
    custom_retrieval_rate = fields.Float(
        string='Custom Retrieval Rate per Item',
        default=0.0,
        help='Customer-specific rate per item (0 = use base rate)'
    )
    
    custom_delivery_rate = fields.Float(
        string='Custom Delivery Rate per Order',
        default=0.0,
        help='Customer-specific delivery rate (0 = use base rate)'
    )
    
    # Priority multipliers (1.0 = standard, 0.5 = 50% discount, 1.5 = 50% premium)
    rush_multiplier = fields.Float(
        string='Rush Service Multiplier',
        default=1.0,
        help='Multiplier for rush services (1.0 = standard rates)'
    )
    
    emergency_multiplier = fields.Float(
        string='Emergency Service Multiplier',
        default=1.0,
        help='Multiplier for emergency services (1.0 = standard rates)'
    )
    
    weekend_multiplier = fields.Float(
        string='Weekend Service Multiplier',
        default=1.0,
        help='Multiplier for weekend services (1.0 = standard rates)'
    )
    
    holiday_multiplier = fields.Float(
        string='Holiday Service Multiplier',
        default=1.0,
        help='Multiplier for holiday services (1.0 = standard rates)'
    )
    
    # Contract terms
    contract_notes = fields.Text(
        string='Contract Notes',
        help='Special terms and conditions for this customer'
    )
    
    
    expiry_date = fields.Date(
        string='Expiry Date',
        help='When these rates expire (empty = no expiry)'
    )
    
    

    @api.depends('customer_id', 'effective_date')
    def _compute_display_name(self):
        for record in self:
            if record.customer_id:
                record.display_name = f"{record.customer_id.name} - {record.effective_date}"
            else:
                record.display_name = f"New Customer Rate - {record.effective_date}"


class DocumentRetrievalWorkOrder(models.Model):
    """Document Retrieval Work Orders with Priority Pricing"""
    _name = 'document.retrieval.work.order'
    _description = 'Document Retrieval Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc, name'
    _rec_name = 'name'

    # Core identification
        tracking=True
    )
    
    # Customer information
    )
    
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        tracking=True,
        domain="[('partner_id', '=', customer_id)]"
    )
    
    # Request details
    request_date = fields.Datetime(
        string='Request Date',
        required=True,
        tracking=True
    )
    
    requested_by = fields.Many2one(
        'res.users',
        string='Requested By',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    # Priority and service level
    priority = fields.Selection([
        ('standard', 'Standard (48 Hours)'),
        ('rush_eod', 'Rush (End of Day)'),
        ('rush_4h', 'Rush (4 Hours)'),
        ('emergency_1h', 'Emergency (1 Hour)'),
        ('weekend', 'Weekend Service'),
        ('holiday', 'Holiday Service')
    ], string='Priority Level', default='standard', required=True, tracking=True)
    
    # Delivery scheduling
    delivery_date = fields.Date(
        string='Requested Delivery Date',
        tracking=True
    )
    
    delivery_time = fields.Datetime(
        string='Requested Delivery Time',
        tracking=True
    )
    
    actual_delivery_date = fields.Date(
        string='Actual Delivery Date',
        tracking=True
    )
    
    # Items to retrieve
    retrieval_item_ids = fields.One2many(
        'document.retrieval.item',
        'work_order_id',
        string='Items to Retrieve'
    )
    
    item_count = fields.Integer(
        string='Number of Items',
        compute='_compute_item_count',
        store=True
    )
    
    # Pricing calculation
    base_retrieval_cost = fields.Float(
        string='Base Retrieval Cost',
        compute='_compute_pricing',
        store=True,
        help='Base cost for retrieving items'
    )
    
    base_delivery_cost = fields.Float(
        string='Base Delivery Cost',
        compute='_compute_pricing',
        store=True,
        help='Base delivery fee'
    )
    
    priority_item_cost = fields.Float(
        string='Priority Fee (Items)',
        compute='_compute_pricing',
        store=True,
        help='Additional priority fees per item'
    )
    
    priority_order_cost = fields.Float(
        string='Priority Fee (Order)',
        compute='_compute_pricing',
        store=True,
        help='Additional priority fees per order'
    )
    
    total_cost = fields.Float(
        string='Total Cost',
        compute='_compute_pricing',
        store=True,
        tracking=True
    )
    
    # Customer rate information
    customer_rates_id = fields.Many2one(
        'customer.retrieval.rates',
        string='Customer Rates',
        compute='_compute_customer_rates',
        store=True,
        help='Active customer-specific rates'
    )
    
    has_custom_rates = fields.Boolean(
        string='Has Custom Rates',
        compute='_compute_customer_rates',
        store=True
    )
    
    # Status and workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('ready_delivery', 'Ready for Delivery'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Personnel assignment
    technician_id = fields.Many2one(
        'res.users',
        string='Assigned Technician',
        tracking=True,
        domain=[('groups_id', 'in', [
            'records_management.group_records_user'
        ])]
    )
    
    driver_id = fields.Many2one(
        'res.users',
        string='Delivery Driver',
        tracking=True
    )
    
    # Delivery details
    delivery_address = fields.Text(
        string='Delivery Address',
        help='Where to deliver the retrieved documents'
    )
    
    delivery_contact = fields.Char(
        string='Delivery Contact',
        help='Contact person for delivery'
    )
    
    delivery_phone = fields.Char(
        string='Delivery Phone',
        help='Phone number for delivery coordination'
    )
    
    # Notes and documentation
    retrieval_notes = fields.Text(
        string='Retrieval Notes',
        help='Special instructions for retrieval'
    )
    
    delivery_notes = fields.Text(
        string='Delivery Notes',
        help='Special instructions for delivery'
    )
    
    internal_notes = fields.Text(
        string='Internal Notes',
        help='Internal notes not visible to customer'
    )
    
    # Customer signature and confirmation
    customer_signature = fields.Binary(
        string='Customer Signature'
    )
    
    customer_signature_date = fields.Datetime(
        string='Signature Date'
    )
    
    delivered_by = fields.Many2one(
        'res.users',
        string='Delivered By'
    )
    
    # Company and audit

    @api.model
    def create(self, vals):
        """Generate sequence number on creation"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'document.retrieval.work.order'
            ) or _('New')
        return super().create(vals)

    @api.depends('retrieval_item_ids')
    def _compute_item_count(self):
        """Compute total number of items to retrieve"""
        for order in self:
            order.item_count = len(order.retrieval_item_ids)

    @api.depends('customer_id')
    def _compute_customer_rates(self):
        """Get active customer-specific rates"""
        for order in self:
            if order.customer_id:
                # Find active customer rates
                customer_rates = self.env['customer.retrieval.rates'].search([
                    ('customer_id', '=', order.customer_id.id),
                    ('active', '=', True),
                    ('effective_date', '<=', fields.Date.today()),
                    '|',
                    ('expiry_date', '=', False),
                    ('expiry_date', '>=', fields.Date.today())
                ], limit=1, order='effective_date desc')
                
                if customer_rates:
                    order.customer_rates_id = customer_rates.id
                    order.has_custom_rates = True
                else:
                    order.customer_rates_id = False
                    order.has_custom_rates = False
            else:
                order.customer_rates_id = False
                order.has_custom_rates = False

    @api.depends('item_count', 'priority', 'customer_rates_id')
    def _compute_pricing(self):
        """Compute pricing based on priority, customer rates, and items"""
        for order in self:
            if not order.item_count:
                order.base_retrieval_cost = 0.0
                order.base_delivery_cost = 0.0
                order.priority_item_cost = 0.0
                order.priority_order_cost = 0.0
                order.total_cost = 0.0
                continue
            
            # Get base rates
            base_rates = self.env['document.retrieval.rates'].search([
                ('company_id', '=', order.company_id.id),
                ('active', '=', True)
            ], limit=1, order='effective_date desc')
            
            if not base_rates:
                # Create default rates if none exist
                base_rates = self.env['document.retrieval.rates'].create({
                    'name': 'Default Rates',
                    'company_id': order.company_id.id
                })
            
            # Apply customer-specific rates or use base rates
            if order.customer_rates_id and order.customer_rates_id.custom_retrieval_rate > 0:
                retrieval_rate = order.customer_rates_id.custom_retrieval_rate
            else:
                retrieval_rate = base_rates.base_retrieval_rate
            
            if order.customer_rates_id and order.customer_rates_id.custom_delivery_rate > 0:
                delivery_rate = order.customer_rates_id.custom_delivery_rate
            else:
                delivery_rate = base_rates.base_delivery_rate
            
            # Calculate base costs
            order.base_retrieval_cost = retrieval_rate * order.item_count
            order.base_delivery_cost = delivery_rate
            
            # Calculate priority fees
            priority_item_fee = 0.0
            priority_order_fee = 0.0
            
            if order.priority == 'rush_eod':
                priority_item_fee = base_rates.rush_end_of_day_item
                priority_order_fee = base_rates.rush_end_of_day_order
            elif order.priority == 'rush_4h':
                priority_item_fee = base_rates.rush_4_hours_item
                priority_order_fee = base_rates.rush_4_hours_order
            elif order.priority == 'emergency_1h':
                priority_item_fee = base_rates.emergency_1_hour_item
                priority_order_fee = base_rates.emergency_1_hour_order
            elif order.priority == 'weekend':
                priority_item_fee = base_rates.weekend_item
                priority_order_fee = base_rates.weekend_order
            elif order.priority == 'holiday':
                priority_item_fee = base_rates.holiday_item
                priority_order_fee = base_rates.holiday_order
            
            # Apply customer multipliers if available
            if order.customer_rates_id:
                if order.priority in ['rush_eod', 'rush_4h']:
                    multiplier = order.customer_rates_id.rush_multiplier
                elif order.priority == 'emergency_1h':
                    multiplier = order.customer_rates_id.emergency_multiplier
                elif order.priority == 'weekend':
                    multiplier = order.customer_rates_id.weekend_multiplier
                elif order.priority == 'holiday':
                    multiplier = order.customer_rates_id.holiday_multiplier
                else:
                    multiplier = 1.0
                
                priority_item_fee *= multiplier
                priority_order_fee *= multiplier
            
            order.priority_item_cost = priority_item_fee * order.item_count
            order.priority_order_cost = priority_order_fee
            
            # Calculate total cost
            order.total_cost = (
                order.base_retrieval_cost +
                order.base_delivery_cost +
                order.priority_item_cost +
                order.priority_order_cost
            )

    def action_confirm(self):
        """Confirm the work order"""
        self.ensure_one()
        if not self.retrieval_item_ids:
            raise UserError(_('Cannot confirm work order without items to retrieve.'))
        
        self.write({'state': 'confirmed'})
        
        # Send notification to customer
        self.message_post(
            body=_('Work order confirmed. Estimated cost: $%.2f') % self.total_cost
        )
        return True

    def action_assign_technician(self):
        """Assign technician to work order"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_('Can only assign technicians to confirmed work orders.'))
        
        self.write({'state': 'assigned'})
        return True

    def action_start_retrieval(self):
        """Start retrieval process"""
        self.ensure_one()
        if self.state != 'assigned':
            raise UserError(_('Work order must be assigned before starting retrieval.'))
        
        self.write({'state': 'in_progress'})
        return True

    def action_ready_for_delivery(self):
        """Mark items as ready for delivery"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_('Can only mark in-progress orders as ready for delivery.'))
        
        self.write({'state': 'ready_delivery'})
        return True

    def action_deliver(self):
        """Mark as delivered"""
        self.ensure_one()
        if self.state != 'ready_delivery':
            raise UserError(_('Order must be ready for delivery first.'))
        
        self.write({
            'state': 'delivered',
            'actual_delivery_date': fields.Date.today(),
            'delivered_by': self.env.user.id
        })
        return True

    def action_complete(self):
        """Complete the work order"""
        self.ensure_one()
        if self.state != 'delivered':
            raise UserError(_('Order must be delivered before completion.'))
        
        self.write({'state': 'completed'})
        return True

    def action_view_pricing_breakdown(self):
        """Show detailed pricing breakdown"""
        self.ensure_one()
        return {
            'name': _('Pricing Breakdown - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'document.retrieval.pricing.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_work_order_id': self.id},
        }

    def action_add_items(self):
        """Add items to retrieve"""
        self.ensure_one()
        return {
            'name': _('Add Items to Retrieve'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.retrieval.item',
            'view_mode': 'tree,form',
            'domain': [('work_order_id', '=', self.id)],
            'context': {'default_work_order_id': self.id},
        }


class DocumentRetrievalItem(models.Model):
    """Items to be retrieved in a work order"""
    _name = 'document.retrieval.item'
    _description = 'Document Retrieval Item'
    _rec_name = 'display_name'

    
    work_order_id = fields.Many2one(
        'document.retrieval.work.order',
        string='Work Order',
        required=True,
        ondelete='cascade'
    )
    
    # Item identification
    item_type = fields.Selection([
        ('box', 'Box'),
        ('file', 'File'),
        ('document', 'Document')
    ], string='Item Type', required=True, default='box')
    
    box_id = fields.Many2one(
        'records.box',
        string='Box',
        domain="[('customer_id', '=', customer_id)]"
    )
    
    document_id = fields.Many2one(
        'records.document',
        string='Document',
        domain="[('customer_id', '=', customer_id)]"
    )
    
    barcode = fields.Char(
        string='Barcode',
        help='Barcode of the item to retrieve'
    )
    
    description = fields.Char(
        string='Description',
        required=True,
        help='Description of the item to retrieve'
    )
    
    # Location and status
    current_location = fields.Char(
        string='Current Location',
        help='Where the item is currently stored'
    )
    
    status = fields.Selection([
        ('requested', 'Requested'),
        ('located', 'Located'),
        ('retrieved', 'Retrieved'),
        ('delivered', 'Delivered')
    ], string='Status', default='requested')
    
    # Customer from work order
    
    # Notes

    @api.depends('item_type', 'box_id', 'document_id', 'description')
    def _compute_display_name(self):
        for item in self:
            if item.item_type == 'box' and item.box_id:
                item.display_name = f"Box: {item.box_id.name}"
            elif item.item_type == 'document' and item.document_id:
                item.display_name = f"Document: {item.document_id.name}"
            elif item.description:
                item.display_name = f"{item.item_type.title()}: {item.description}"
            else:
                item.display_name = f"New {item.item_type.title()}"


class DocumentRetrievalPricingWizard(models.TransientModel):
    """Wizard to show detailed pricing breakdown"""
    _name = 'document.retrieval.pricing.wizard'
    _description = 'Document Retrieval Pricing Breakdown'

    
    # Pricing details (computed from work order)
    customer_name = fields.Char(
        related='work_order_id.customer_id.name',
        string='Customer'
    )
    
    
    
    
    
    
    )
    
    )
    
