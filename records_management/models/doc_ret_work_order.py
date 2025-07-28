# -*- coding: utf-8 -*-
"""
Document Retrieval Work Order Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class DocumentRetrievalWorkOrder(models.Model):
    """
    Document Retrieval Work Order
    Manages work orders for document retrieval requests
    """
    
    _name = 'doc.ret.wo'
    _description = 'Document Retrieval Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_date, create_date desc'
    _rec_name = 'name'
    
    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Work Order Reference', required=True, tracking=True,
                      default=lambda self: _('New'), copy=False)
    description = fields.Text(string='Work Order Description', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Work Order Manager', 
                             default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    
    # ==========================================
    # CUSTOMER INFORMATION
    # ==========================================
    customer_id = fields.Many2one('res.partner', string='Customer', 
                                 required=True, tracking=True,
                                 domain=[('is_company', '=', True)])
    customer_contact_id = fields.Many2one('res.partner', string='Customer Contact', tracking=True)
    department_id = fields.Many2one('records.department', string='Department', tracking=True)
    
    # ==========================================
    # WORK ORDER DETAILS
    # ==========================================
    work_order_type = fields.Selection([
        ('standard', 'Standard Retrieval'),
        ('expedited', 'Expedited Retrieval'),
        ('emergency', 'Emergency Retrieval'),
        ('bulk', 'Bulk Retrieval'),
        ('research', 'Research Request')
    ], string='Work Order Type', default='standard', required=True, tracking=True)
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', tracking=True)
    
    # ==========================================
    # SCHEDULING
    # ==========================================
    request_date = fields.Datetime(string='Request Date', 
                                   default=fields.Datetime.now, required=True, tracking=True)
    scheduled_date = fields.Datetime(string='Scheduled Date', tracking=True)
    due_date = fields.Datetime(string='Due Date', tracking=True)
    
    estimated_start_time = fields.Datetime(string='Estimated Start Time')
    estimated_completion_time = fields.Datetime(string='Estimated Completion Time')
    actual_start_time = fields.Datetime(string='Actual Start Time')
    actual_completion_time = fields.Datetime(string='Actual Completion Time')
    
    # ==========================================
    # PERSONNEL ASSIGNMENT
    # ==========================================
    assigned_team_id = fields.Many2one('hr.team', string='Assigned Team', tracking=True)
    primary_technician_id = fields.Many2one('res.users', string='Primary Technician', tracking=True)
    secondary_technician_id = fields.Many2one('res.users', string='Secondary Technician', tracking=True)
    supervisor_id = fields.Many2one('res.users', string='Supervisor', tracking=True)
    
    # ==========================================
    # WORK ORDER STATUS
    # ==========================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)
    
    # ==========================================
    # RETRIEVAL SPECIFICATIONS
    # ==========================================
    retrieval_item_ids = fields.One2many('document.retrieval.item', 'work_order_id',
                                         string='Retrieval Items')
    total_documents = fields.Integer(string='Total Documents', compute='_compute_totals', store=True)
    total_pages = fields.Integer(string='Total Pages', compute='_compute_totals', store=True)
    total_boxes = fields.Integer(string='Total Boxes', compute='_compute_totals', store=True)
    
    delivery_method = fields.Selection([
        ('pickup', 'Customer Pickup'),
        ('courier', 'Courier Delivery'),
        ('mail', 'Mail Delivery'),
        ('digital', 'Digital Delivery'),
        ('secure_transport', 'Secure Transport')
    ], string='Delivery Method', required=True, tracking=True)
    
    delivery_address = fields.Text(string='Delivery Address')
    delivery_instructions = fields.Text(string='Delivery Instructions')
    
    # ==========================================
    # PRICING AND BILLING
    # ==========================================
    rate_id = fields.Many2one('customer.retrieval.rates', string='Applied Rate', tracking=True)
    estimated_cost = fields.Float(string='Estimated Cost', compute='_compute_costs', store=True)
    actual_cost = fields.Float(string='Actual Cost', tracking=True)
    
    billable = fields.Boolean(string='Billable', default=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    invoiced = fields.Boolean(string='Invoiced', compute='_compute_invoiced', store=True)
    
    # ==========================================
    # QUALITY AND COMPLIANCE
    # ==========================================
    quality_check_required = fields.Boolean(string='Quality Check Required', default=True)
    quality_check_completed = fields.Boolean(string='Quality Check Completed')
    quality_notes = fields.Text(string='Quality Notes')
    
    chain_of_custody_required = fields.Boolean(string='Chain of Custody Required', default=True)
    custody_log_ids = fields.One2many('records.chain.of.custody.log', 'work_order_id',
                                     string='Chain of Custody Records')
    
    # ==========================================
    # DOCUMENTATION
    # ==========================================
    completion_notes = fields.Text(string='Completion Notes')
    customer_signature = fields.Binary(string='Customer Signature')
    technician_signature = fields.Binary(string='Technician Signature')
    delivery_receipt = fields.Binary(string='Delivery Receipt')
    
    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends('retrieval_item_ids', 'retrieval_item_ids.document_count', 
                 'retrieval_item_ids.page_count', 'retrieval_item_ids.box_count')
    def _compute_totals(self):
        """Compute total documents, pages, and boxes"""
        for order in self:
            order.total_documents = sum(order.retrieval_item_ids.mapped('document_count'))
            order.total_pages = sum(order.retrieval_item_ids.mapped('page_count'))
            order.total_boxes = sum(order.retrieval_item_ids.mapped('box_count'))
    
    @api.depends('rate_id', 'total_documents', 'total_pages', 'total_boxes', 'work_order_type')
    def _compute_costs(self):
        """Compute estimated cost based on rate and quantities"""
        for order in self:
            if order.rate_id and order.total_documents:
                urgency = 'standard'
                if order.work_order_type == 'expedited':
                    urgency = 'expedited'
                elif order.work_order_type == 'emergency':
                    urgency = 'emergency'
                
                order.estimated_cost = order.rate_id.calculate_retrieval_cost(
                    document_count=order.total_documents,
                    page_count=order.total_pages,
                    box_count=order.total_boxes,
                    urgency=urgency
                )
            else:
                order.estimated_cost = 0.0
    
    @api.depends('invoice_id')
    def _compute_invoiced(self):
        """Check if work order is invoiced"""
        for order in self:
            order.invoiced = bool(order.invoice_id)
    
    # ==========================================
    # CRUD METHODS
    # ==========================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence number"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('doc.ret.wo') or _('New')
        return super().create(vals_list)
    
    # ==========================================
    # WORKFLOW ACTIONS
    # ==========================================
    def action_confirm(self):
        """Confirm work order"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft work orders can be confirmed'))
        
        if not self.retrieval_item_ids:
            raise UserError(_('Please add at least one retrieval item'))
        
        self.write({'state': 'confirmed'})
        self.message_post(body=_('Work order confirmed'))
    
    def action_assign(self):
        """Assign work order to technician"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_('Only confirmed work orders can be assigned'))
        
        if not self.primary_technician_id:
            raise UserError(_('Please assign a primary technician'))
        
        self.write({'state': 'assigned'})
        self.message_post(body=_('Work order assigned to %s') % self.primary_technician_id.name)
    
    def action_start(self):
        """Start work order execution"""
        self.ensure_one()
        if self.state != 'assigned':
            raise UserError(_('Only assigned work orders can be started'))
        
        self.write({
            'state': 'in_progress',
            'actual_start_time': fields.Datetime.now()
        })
        self.message_post(body=_('Work order started'))
    
    def action_complete(self):
        """Complete work order"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_('Only work orders in progress can be completed'))
        
        if self.quality_check_required and not self.quality_check_completed:
            raise UserError(_('Quality check must be completed before finishing'))
        
        self.write({
            'state': 'completed',
            'actual_completion_time': fields.Datetime.now()
        })
        self.message_post(body=_('Work order completed'))
    
    def action_deliver(self):
        """Mark as delivered"""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_('Only completed work orders can be delivered'))
        
        self.write({'state': 'delivered'})
        self.message_post(body=_('Work order delivered'))
    
    def action_create_invoice(self):
        """Create invoice for work order"""
        self.ensure_one()
        if self.state not in ['completed', 'delivered']:
            raise UserError(_('Only completed or delivered work orders can be invoiced'))
        
        if not self.billable:
            raise UserError(_('This work order is not billable'))
        
        if self.invoiced:
            raise UserError(_('Work order already invoiced'))
        
        # Create invoice
        invoice_vals = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': f'Document Retrieval - {self.name}',
                'quantity': 1,
                'price_unit': self.actual_cost or self.estimated_cost,
                'account_id': self.env['account.account'].search([
                    ('account_type', '=', 'income')
                ], limit=1).id,
            })]
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        self.write({
            'state': 'invoiced',
            'invoice_id': invoice.id
        })
        
        self.message_post(body=_('Invoice created: %s') % invoice.name)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_cancel(self):
        """Cancel work order"""
        self.ensure_one()
        if self.state in ['completed', 'delivered', 'invoiced']:
            raise UserError(_('Cannot cancel completed, delivered, or invoiced work orders'))
        
        self.write({'state': 'cancelled'})
        self.message_post(body=_('Work order cancelled'))
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    def get_estimated_turnaround(self):
        """Get estimated turnaround time"""
        self.ensure_one()
        if self.rate_id:
            urgency = 'standard'
            if self.work_order_type == 'expedited':
                urgency = 'expedited'
            elif self.work_order_type == 'emergency':
                urgency = 'emergency'
            return self.rate_id.get_turnaround_time(urgency)
        return 24  # Default 24 hours
    
    # ==========================================
    # VALIDATION
    # ==========================================
    @api.constrains('scheduled_date', 'due_date')
    def _check_dates(self):
        """Validate dates"""
        for order in self:
            if order.scheduled_date and order.due_date:
                if order.scheduled_date > order.due_date:
                    raise ValidationError(_('Scheduled date cannot be after due date'))
    
    @api.constrains('actual_start_time', 'actual_completion_time')
    def _check_actual_times(self):
        """Validate actual times"""
        for order in self:
            if order.actual_start_time and order.actual_completion_time:
                if order.actual_completion_time <= order.actual_start_time:
                    raise ValidationError(_('Completion time must be after start time'))


# ==========================================
# DOCUMENT RETRIEVAL ITEM MODEL
# ==========================================
class DocumentRetrievalItem(models.Model):
    """
    Individual items in a document retrieval work order
    """
    
    _name = 'document.retrieval.item'
    _description = 'Document Retrieval Item'
    _order = 'sequence, id'
    
    # ==========================================
    # CORE FIELDS
    # ==========================================
    sequence = fields.Integer(string='Sequence', default=10)
    work_order_id = fields.Many2one('doc.ret.wo', string='Work Order', 
                                   required=True, ondelete='cascade')
    name = fields.Char(string='Item Description', required=True)
    
    # ==========================================
    # ITEM SPECIFICATIONS
    # ==========================================
    item_type = fields.Selection([
        ('document', 'Single Document'),
        ('folder', 'Document Folder'),
        ('box', 'Records Box'),
        ('file', 'File Cabinet'),
        ('custom', 'Custom Item')
    ], string='Item Type', required=True, default='document')
    
    box_id = fields.Many2one('records.box', string='Records Box')
    folder_name = fields.Char(string='Folder Name')
    document_reference = fields.Char(string='Document Reference')
    
    # ==========================================
    # QUANTITIES
    # ==========================================
    document_count = fields.Integer(string='Document Count', default=1)
    page_count = fields.Integer(string='Page Count', default=1)
    box_count = fields.Integer(string='Box Count', default=0)
    
    # ==========================================
    # LOCATION INFORMATION
    # ==========================================
    storage_location = fields.Char(string='Storage Location')
    shelf_number = fields.Char(string='Shelf Number')
    section = fields.Char(string='Section')
    notes = fields.Text(string='Retrieval Notes')
    
    # ==========================================
    # STATUS
    # ==========================================
    status = fields.Selection([
        ('pending', 'Pending'),
        ('located', 'Located'),
        ('retrieved', 'Retrieved'),
        ('not_found', 'Not Found'),
        ('damaged', 'Damaged')
    ], string='Status', default='pending')
    
    retrieved_by = fields.Many2one('res.users', string='Retrieved By')
    retrieved_date = fields.Datetime(string='Retrieved Date')
    
    # ==========================================
    # ACTIONS
    # ==========================================
    def action_mark_located(self):
        """Mark item as located"""
        self.write({'status': 'located'})
    
    def action_mark_retrieved(self):
        """Mark item as retrieved"""
        self.write({
            'status': 'retrieved',
            'retrieved_by': self.env.user.id,
            'retrieved_date': fields.Datetime.now()
        })
    
    def action_mark_not_found(self):
        """Mark item as not found"""
        self.write({'status': 'not_found'})
