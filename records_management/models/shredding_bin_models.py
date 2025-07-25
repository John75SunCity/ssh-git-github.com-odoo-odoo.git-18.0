# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ShreddingBin(models.Model):
    """Shredding bins for both standard and mobile services"""
    _name = 'shredding.bin'
    _description = 'Shredding Bin'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'barcode'

    # Basic Information
    name = fields.Char(string='Bin Reference', required=True, tracking=True)
    barcode = fields.Char(string='Barcode', required=True, size=10, index=True, tracking=True)
    
    # Bin Specifications
    bin_size = fields.Selection([
        ('23_gallon', '23 Gallon'),
        ('32_gallon', '32 Gallon'),
        ('console', 'Console'),
        ('64_gallon', '64 Gallon'),
        ('96_gallon', '96 Gallon')
    ], string='Bin Size', required=True, tracking=True)
    
    capacity_gallons = fields.Float(string='Capacity (Gallons)', compute='_compute_capacity', store=True)
    
    # Service Information
    current_service_type = fields.Selection([
        ('standard', 'Standard (Off-site)'),
        ('mobile', 'Mobile (On-site)')
    ], string='Current Service Type', default='standard', tracking=True)
    
    # Assignment and tracking
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        domain=[('is_company', '=', True)]
    )
    
    work_order_id = fields.Many2one(
        'work.order.shredding',
        string='Work Order',
        tracking=True
    )
    
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        tracking=True,
        domain="[('partner_id', '=', customer_id)]"
    )
    location_description = fields.Char(string='Location at Customer Site', tracking=True)
    
    # Status Tracking
    status = fields.Selection([
        ('available', 'Available'),
        ('deployed', 'Deployed at Customer'),
        ('full', 'Full - Ready for Service'),
        ('in_transit', 'In Transit'),
        ('being_serviced', 'Being Serviced'),
        ('maintenance', 'Maintenance Required')
    ], string='Status', default='available', tracking=True)
    
    last_service_date = fields.Date(string='Last Service Date', tracking=True)
    next_service_date = fields.Date(string='Next Scheduled Service', tracking=True)
    
    # Work Order Integration
    current_work_order_id = fields.Many2one('shredding.service', string='Current Work Order')
    service_history_ids = fields.One2many('shredding.service', 'bin_id', string='Service History')
    
    # Computed Fields
    current_rate = fields.Monetary(string='Current Rate', compute='_compute_current_rate', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    @api.depends('bin_size')
    def _compute_capacity(self):
        capacity_map = {
            '23_gallon': 23.0,
            '32_gallon': 32.0,
            'console': 32.0,  # Assuming console is similar to 32 gallon
            '64_gallon': 64.0,
            '96_gallon': 96.0
        }
        for bin_record in self:
            bin_record.capacity_gallons = capacity_map.get(bin_record.bin_size, 0.0)
    
    @api.depends('customer_id', 'bin_size', 'current_service_type')
    def _compute_current_rate(self):
        """Compute current rate based on customer-specific or base rates"""
        for bin_record in self:
            if bin_record.customer_id and bin_record.bin_size and bin_record.current_service_type:
                # Look for customer-specific rate first
                customer_rate = self.env['shredding.customer.rate'].search([
                    ('customer_id', '=', bin_record.customer_id.id),
                    ('bin_size', '=', bin_record.bin_size),
                    ('service_type', '=', bin_record.current_service_type),
                    ('active', '=', True)
                ], limit=1)
                
                if customer_rate:
                    bin_record.current_rate = customer_rate.rate
                else:
                    # Fall back to base rate
                    base_rate = self.env['shredding.base.rate'].search([
                        ('bin_size', '=', bin_record.bin_size),
                        ('service_type', '=', bin_record.current_service_type),
                        ('active', '=', True)
                    ], limit=1)
                    bin_record.current_rate = base_rate.rate if base_rate else 0.0
            else:
                bin_record.current_rate = 0.0
    
    def action_create_service_order(self):
        """Create a service order for this bin"""
        self.ensure_one()
        return {
            'name': _('Create Service Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'shredding.service',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bin_id': self.id,
                'default_customer_id': self.customer_id.id,
                'default_department_id': self.department_id.id,
                'default_service_type': self.current_service_type,
                'default_estimated_rate': self.current_rate
            }
        }


class ShreddingBaseRate(models.Model):
    """Base rates for shredding services by bin size and service type"""
    _name = 'shredding.base.rate'
    _description = 'Shredding Base Rate'
    _rec_name = 'display_name'

    display_name = fields.Char(string='Rate Name', compute='_compute_display_name', store=True)
    
    bin_size = fields.Selection([
        ('23_gallon', '23 Gallon'),
        ('32_gallon', '32 Gallon'),
        ('console', 'Console'),
        ('64_gallon', '64 Gallon'),
        ('96_gallon', '96 Gallon')
    ], string='Bin Size', required=True)
    
    service_type = fields.Selection([
        ('standard', 'Standard (Off-site)'),
        ('mobile', 'Mobile (On-site)')
    ], string='Service Type', required=True)
    
    rate = fields.Monetary(string='Base Rate', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    active = fields.Boolean(string='Active', default=True)
    effective_date = fields.Date(string='Effective Date', default=fields.Date.today)
    
    @api.depends('bin_size', 'service_type', 'rate')
    def _compute_display_name(self):
        bin_labels = dict(self._fields['bin_size'].selection)
        service_labels = dict(self._fields['service_type'].selection)
        
        for rate in self:
            bin_label = bin_labels.get(rate.bin_size, rate.bin_size)
            service_label = service_labels.get(rate.service_type, rate.service_type)
            rate.display_name = f"{bin_label} - {service_label}: ${rate.rate}"


class ShreddingCustomerRate(models.Model):
    """Customer-specific rates that override base rates"""
    _name = 'shredding.customer.rate'
    _description = 'Customer Shredding Rate'
    _rec_name = 'display_name'

    display_name = fields.Char(string='Rate Name', compute='_compute_display_name', store=True)
    
    customer_id = fields.Many2one('res.partner', string='Customer', required=True,
                                 domain="[('is_company', '=', True)]")
    
    bin_size = fields.Selection([
        ('23_gallon', '23 Gallon'),
        ('32_gallon', '32 Gallon'),
        ('console', 'Console'),
        ('64_gallon', '64 Gallon'),
        ('96_gallon', '96 Gallon')
    ], string='Bin Size', required=True)
    
    service_type = fields.Selection([
        ('standard', 'Standard (Off-site)'),
        ('mobile', 'Mobile (On-site)')
    ], string='Service Type', required=True)
    
    rate = fields.Monetary(string='Customer Rate', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    # Contract Information
    contract_reference = fields.Char(string='Contract Reference')
    effective_date = fields.Date(string='Effective Date', default=fields.Date.today, required=True)
    expiration_date = fields.Date(string='Expiration Date')
    
    active = fields.Boolean(string='Active', default=True)
    notes = fields.Text(string='Notes')
    
    @api.depends('customer_id', 'bin_size', 'service_type', 'rate')
    def _compute_display_name(self):
        bin_labels = dict(self._fields['bin_size'].selection)
        service_labels = dict(self._fields['service_type'].selection)
        
        for rate in self:
            customer_name = rate.customer_id.name if rate.customer_id else 'Unknown'
            bin_label = bin_labels.get(rate.bin_size, rate.bin_size)
            service_label = service_labels.get(rate.service_type, rate.service_type)
            rate.display_name = f"{customer_name} - {bin_label} - {service_label}: ${rate.rate}"
