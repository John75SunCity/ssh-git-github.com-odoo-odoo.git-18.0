# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class CustomerInventoryReport(models.Model):
    """Model for customer inventory reports."""
    _name = 'customer.inventory.report'
    _description = 'Customer Inventory Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'report_date desc, customer_id'

    # Phase 1: Core Customer Inventory Report Fields (13 fields)
    
    # Report identification and basic info
    name = fields.Char('Report Name', required=True, tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    report_date = fields.Date('Report Date', required=True, default=fields.Date.today, tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('sent', 'Sent'),
        ('reviewed', 'Reviewed'),
        ('archived', 'Archived')
    
    # Inventory details and relationships
    location_id = fields.Many2one('records.location', string='Primary Location', tracking=True)
    active_locations = fields.Integer('Active Locations', compute='_compute_inventory_totals', store=True)
    storage_date = fields.Date('Storage Date', tracking=True)
    
    # Document and box tracking
    box_ids = fields.One2many('records.box', 'customer_id', string='Boxes')
    document_ids = fields.One2many('records.document', 'customer_id', string='Documents')
    document_type_id = fields.Many2one('records.document.type', string='Document Type Filter')
    
    # Computed totals
    total_boxes = fields.Integer('Total Boxes', compute='_compute_inventory_totals', store=True)
    total_documents = fields.Integer('Total Documents', compute='_compute_inventory_totals', store=True)
    volume_category = fields.Selection([
        ('small', 'Small (< 100 boxes)'),
        ('medium', 'Medium (100-500 boxes)'),
        ('large', 'Large (500-1000 boxes)'),
        ('enterprise', 'Enterprise (> 1000 boxes)')
    
    # Additional contextual fields
    notes = fields.Text('Notes')
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Review')
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible User', default=lambda self: self.env.user)
    active = fields.Boolean('Active', default=True)
    
    @api.depends('box_ids', 'document_ids')
    def _compute_inventory_totals(self):
        """Compute inventory totals and active locations"""
        for record in self:
            record.total_boxes = len(record.box_ids)
            record.total_documents = len(record.document_ids)
            
            # Count unique locations
            locations = record.box_ids.mapped('location_id')
            record.active_locations = len(locations.filtered('active'))
    
    @api.depends('total_boxes')
    def _compute_volume_category(self):
        """Compute volume category based on total boxes"""
        for record in self:
            if record.total_boxes < 100:
                record.volume_category = 'small'
            elif record.total_boxes < 500:
                record.volume_category = 'medium'
            elif record.total_boxes < 1000:
                record.volume_category = 'large'
            else:
                record.volume_category = 'enterprise'