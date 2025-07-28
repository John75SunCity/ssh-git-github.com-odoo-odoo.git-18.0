# -*- coding: utf-8 -*-
"""
Document Retrieval Work Order
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class DocumentRetrievalWorkOrder(models.Model):
    """
    Document Retrieval Work Order - Manages document retrieval requests and workflow
    """
    
    _name = 'document.retrieval.work.order'
    _description = 'Document Retrieval Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, request_date desc, name'
    _rec_name = 'name'
    
    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Work Order Number', required=True, copy=False, 
                       default=lambda self: _('New'), tracking=True)
    description = fields.Text(string='Description', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Assigned To', 
                             default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    
    # ==========================================
    # CUSTOMER INFORMATION
    # ==========================================
    customer_id = fields.Many2one('res.partner', string='Customer', 
                                 required=True, tracking=True,
                                 domain=[('is_company', '=', True)])
    department_id = fields.Many2one('records.department', string='Department', tracking=True)
    contact_person = fields.Many2one('res.partner', string='Contact Person', tracking=True)
    
    # ==========================================
    # REQUEST DETAILS
    # ==========================================
    request_date = fields.Datetime(string='Request Date', default=fields.Datetime.now, 
                                   required=True, tracking=True)
    needed_by_date = fields.Datetime(string='Needed By', tracking=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High'),
        ('4', 'Urgent')
    ], string='Priority', default='1', required=True, tracking=True)
    
    urgency_level = fields.Selection([
        ('standard', 'Standard'),
        ('expedited', 'Expedited'),
        ('emergency', 'Emergency'),
        ('rush', 'Rush')
    ], string='Urgency Level', default='standard', tracking=True)
    
    # ==========================================
    # RETRIEVAL SPECIFICATIONS
    # ==========================================
    retrieval_type = fields.Selection([
        ('document', 'Document Retrieval'),
        ('file', 'File Retrieval'),
        ('box', 'Box Retrieval'),
        ('scan', 'Scan on Demand'),
        ('copy', 'Copy Services')
    ], string='Retrieval Type', default='document', required=True, tracking=True)
    
    item_count = fields.Integer(string='Number of Items', default=1, tracking=True)
    estimated_pages = fields.Integer(string='Estimated Pages', tracking=True)
    box_count = fields.Integer(string='Number of Boxes', default=1, tracking=True)
    
    # ==========================================
    # DELIVERY INFORMATION
    # ==========================================
    delivery_method = fields.Selection([
        ('pickup', 'Customer Pickup'),
        ('courier', 'Courier Delivery'),
        ('mail', 'Mail Delivery'),
        ('digital', 'Digital Delivery'),
        ('secure_transport', 'Secure Transport')
    ], string='Delivery Method', tracking=True)
    
    delivery_address = fields.Text(string='Delivery Address')
    delivery_instructions = fields.Text(string='Delivery Instructions')
    
    # ==========================================
    # WORKFLOW MANAGEMENT
    # ==========================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('retrieved', 'Retrieved'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)
    
    # ==========================================
    # TIMING FIELDS
    # ==========================================
    start_date = fields.Datetime(string='Start Date', tracking=True)
    completion_date = fields.Datetime(string='Completion Date', tracking=True)
    actual_delivery_date = fields.Datetime(string='Actual Delivery Date', tracking=True)
    
    # ==========================================
    # PRICING INFORMATION
    # ==========================================
    estimated_cost = fields.Float(string='Estimated Cost', tracking=True)
    actual_cost = fields.Float(string='Actual Cost', tracking=True)
    
    # ==========================================
    # NOTES AND COMMUNICATION
    # ==========================================
    internal_notes = fields.Text(string='Internal Notes')
    customer_notes = fields.Text(string='Customer Notes')
    
    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends('item_count', 'estimated_pages', 'box_count')
    def _compute_total_items(self):
        """Compute total items for retrieval"""
        for record in self:
            record.total_items = record.item_count + record.box_count
    
    total_items = fields.Integer(string='Total Items', compute='_compute_total_items', store=True)
    
    # ==========================================
    # ONCHANGE METHODS
    # ==========================================
    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        """Update domain for contact person when customer changes"""
        if self.customer_id:
            return {
                'domain': {
                    'contact_person': [('parent_id', '=', self.customer_id.id)]
                }
            }
        else:
            return {
                'domain': {
                    'contact_person': []
                }
            }
    
    # ==========================================
    # WORKFLOW ACTIONS
    # ==========================================
    def action_confirm(self):
        """Confirm the work order"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft work orders can be confirmed'))
            record.write({'state': 'confirmed'})
            record.message_post(body=_('Work order confirmed'))
    
    def action_start(self):
        """Start the work order"""
        for record in self:
            if record.state != 'confirmed':
                raise UserError(_('Only confirmed work orders can be started'))
            record.write({
                'state': 'in_progress',
                'start_date': fields.Datetime.now()
            })
            record.message_post(body=_('Work order started'))
    
    def action_complete_retrieval(self):
        """Mark retrieval as completed"""
        for record in self:
            if record.state != 'in_progress':
                raise UserError(_('Only in-progress work orders can be completed'))
            record.write({'state': 'retrieved'})
            record.message_post(body=_('Retrieval completed'))
    
    def action_deliver(self):
        """Mark as delivered"""
        for record in self:
            if record.state != 'retrieved':
                raise UserError(_('Only retrieved work orders can be delivered'))
            record.write({
                'state': 'delivered',
                'actual_delivery_date': fields.Datetime.now()
            })
            record.message_post(body=_('Work order delivered'))
    
    def action_complete(self):
        """Mark work order as completed"""
        for record in self:
            if record.state != 'delivered':
                raise UserError(_('Only delivered work orders can be completed'))
            record.write({
                'state': 'completed',
                'completion_date': fields.Datetime.now()
            })
            record.message_post(body=_('Work order completed'))
    
    def action_cancel(self):
        """Cancel the work order"""
        for record in self:
            if record.state in ['completed']:
                raise UserError(_('Cannot cancel completed work orders'))
            record.write({'state': 'cancelled'})
            record.message_post(body=_('Work order cancelled'))
    
    # ==========================================
    # CREATE/WRITE METHODS
    # ==========================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence number - batch compatible"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('document.retrieval.work.order') or _('New')
        return super().create(vals_list)
    
    # ==========================================
    # VALIDATION
    # ==========================================
    @api.constrains('item_count', 'box_count')
    def _check_counts(self):
        """Validate counts"""
        for record in self:
            if record.item_count < 0:
                raise ValidationError(_('Item count cannot be negative'))
            if record.box_count < 0:
                raise ValidationError(_('Box count cannot be negative'))
    
    @api.constrains('request_date', 'needed_by_date')
    def _check_dates(self):
        """Validate dates"""
        for record in self:
            if record.needed_by_date and record.needed_by_date < record.request_date:
                raise ValidationError(_('Needed by date cannot be before request date'))
