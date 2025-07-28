# -*- coding: utf-8 -*-
"""
Records Container Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class RecordsContainer(models.Model):
    """
    Records Container Management
    Core model for tracking physical records storage containers
    """
    
    _name = 'records.container'
    _description = 'Records Container'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = "name"
    
    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Container Number', required=True, tracking=True)
    description = fields.Text(string='Container Description', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Container Manager', 
                             default=lambda self: self.env.user, tracking=True)
    
    # Source tracking for converted transitory items
    source_transitory_id = fields.Many2one('transitory.items', string='Source Transitory Item',
                                          readonly=True, tracking=True,
                                          help="Link to original customer-declared item")
    
    # ==========================================
    # CUSTOMER AND LOCATION
    # ==========================================
    customer_id = fields.Many2one('res.partner', string='Customer', 
                                 required=True, tracking=True,
                                 domain=[('is_company', '=', True)])
    department_id = fields.Many2one('hr.department', string='Department', 
                                   tracking=True, help='Department responsible for this container')
    location_id = fields.Many2one('records.location', string='Storage Location', tracking=True)
    parent_container_id = fields.Many2one('records.container', string='Parent Container', tracking=True)
    
    # ==========================================
    # CONTAINER SPECIFICATIONS
    # ==========================================
    container_type = fields.Selection([
        ('01', 'Type 01 - Standard Container'),
        ('03', 'Type 03 - Map Container'),
        ('04', 'Type 04 - Pallet/Wide Container'),
        ('05', 'Type 05 - Pathology Container'),
        ('06', 'Type 06 - Specialty Container')
    ], string='Container Type', default='01', required=True, tracking=True)
    
    # Computed display fields for container type
    container_type_code = fields.Char(string='Container Type Code', compute='_compute_container_type_display', store=True)
    container_type_display = fields.Char(string='Container Type Display', compute='_compute_container_type_display', store=True)
    
    # Barcode for container identification
    barcode = fields.Char(string='Barcode', tracking=True, copy=False)
    
    # Monthly storage rate
    monthly_rate = fields.Float(string='Monthly Storage Rate', digits=(10, 2), tracking=True, 
                               help='Monthly storage rate for this container')
    
    # Measurements
    estimated_weight = fields.Float(string='Estimated Weight (lbs)', tracking=True)
    actual_weight = fields.Float(string='Actual Weight (lbs)', tracking=True)
    weight = fields.Float(string='Weight (lbs)', compute='_compute_weight', store=True,
                         help='Current weight: actual weight if available, otherwise estimated weight')
    
    # ==========================================
    # CONTENT TRACKING
    # ==========================================
    document_ids = fields.One2many('records.document', 'container_id', string='Documents')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count', store=True)
    confidential_documents = fields.Boolean(string='Contains Confidential Documents', 
                                           compute='_compute_confidential_status', store=True)
    
    # Additional relationships
    movement_ids = fields.One2many('records.container.movement', 'container_id', string='Movement History')
    service_request_ids = fields.One2many('portal.request', 'container_id', string='Service Requests')
    
    # Content estimates
    estimated_pages = fields.Integer(string='Estimated Pages', tracking=True)
    content_summary = fields.Text(string='Content Summary', tracking=True)
    
    # Additional container specifications
    retention_policy_id = fields.Many2one('records.retention.policy', string='Retention Policy', tracking=True)
    size_category = fields.Selection([
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('extra_large', 'Extra Large')
    ], string='Size Category', default='medium', tracking=True)
    
    # ==========================================
    # WORKFLOW STATUS
    # ==========================================
    state = fields.Selection([
        ('received', 'Received'),
        ('indexed', 'Indexed'),
        ('stored', 'Stored'),
        ('retrieved', 'Retrieved'),
        ('destroyed', 'Destroyed')
    ], string='Status', default='received', tracking=True, required=True)
    
    # ==========================================
    # DATE TRACKING
    # ==========================================
    received_date = fields.Date(string='Received Date', 
                               default=fields.Date.today, required=True, tracking=True)
    indexed_date = fields.Date(string='Indexed Date', tracking=True)
    stored_date = fields.Date(string='Stored Date', tracking=True)
    retrieval_date = fields.Date(string='Retrieval Date', tracking=True)
    destruction_date = fields.Date(string='Destruction Date', tracking=True)
    
    # ==========================================
    # BALE ASSIGNMENT (for destroyed containers)
    # ==========================================
    bale_id = fields.Many2one('paper.bale', string='Assigned Bale', tracking=True)
    
    # ==========================================
    # NOTES
    # ==========================================
    notes = fields.Text(string='Notes', tracking=True)
    special_instructions = fields.Text(string='Special Instructions', tracking=True)
    
    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends('document_ids')
    def _compute_document_count(self):
        """Count documents in container"""
        for record in self:
            record.document_count = len(record.document_ids)
    
    @api.depends('document_ids', 'document_ids.confidential')
    def _compute_confidential_status(self):
        """Check if container contains confidential documents"""
        for record in self:
            record.confidential_documents = any(record.document_ids.mapped('confidential'))
    
    @api.depends('actual_weight', 'estimated_weight')
    def _compute_weight(self):
        """Compute weight: actual weight if available, otherwise estimated weight"""
        for record in self:
            record.weight = record.actual_weight or record.estimated_weight or 0.0
    
    @api.depends('container_type')
    def _compute_container_type_display(self):
        """Compute container type display fields"""
        for record in self:
            if record.container_type:
                # Create display name from selection
                display = dict(record._fields['container_type'].selection).get(record.container_type, record.container_type)
                record.container_type_display = display
                # Create code from container type - using the actual type codes
                record.container_type_code = record.container_type or '01'
            else:
                record.container_type_display = ''
                record.container_type_code = '01'
    
    # ==========================================
    # WORKFLOW METHODS
    # ==========================================
    def action_index_container(self):
        """Mark container as indexed"""
        self.ensure_one()
        if self.state != 'received':
            raise ValidationError(_('Only received containers can be indexed'))
        
        self.write({
            'state': 'indexed',
            'indexed_date': fields.Date.today()
        })
        self.message_post(body=_('Container indexed'))
    
    def action_store_container(self):
        """Mark container as stored"""
        self.ensure_one()
        if self.state != 'indexed':
            raise ValidationError(_('Only indexed containers can be stored'))
        
        if not self.location_id:
            raise ValidationError(_('Storage location must be specified'))
        
        self.write({
            'state': 'stored',
            'stored_date': fields.Date.today()
        })
        self.message_post(body=_('Container stored at %s') % self.location_id.name)
    
    def action_retrieve_container(self):
        """Mark container as retrieved"""
        self.ensure_one()
        if self.state != 'stored':
            raise ValidationError(_('Only stored containers can be retrieved'))
        
        self.write({
            'state': 'retrieved',
            'retrieval_date': fields.Date.today()
        })
        self.message_post(body=_('Container retrieved from storage'))
    
    def action_destroy_container(self):
        """Mark container as destroyed"""
        self.ensure_one()
        if self.state not in ['stored', 'retrieved']:
            raise ValidationError(_('Only stored or retrieved containers can be destroyed'))
        
        self.write({
            'state': 'destroyed',
            'destruction_date': fields.Date.today()
        })
        self.message_post(body=_('Container marked for destruction'))
    
    def action_generate_barcode(self):
        """Generate barcode for the container"""
        self.ensure_one()
        if not self.barcode:
            # Generate a simple barcode based on container name and id
            barcode = f"CONT-{self.name}-{self.id}"
            self.write({'barcode': barcode})
            self.message_post(body=_('Barcode generated: %s') % barcode)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Print Barcode',
            'res_model': 'records.container',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_documents(self):
        """View documents in this container"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents in Container %s' % self.name,
            'res_model': 'records.document',
            'domain': [('container_id', '=', self.id)],
            'view_mode': 'tree,form',
            'context': {'default_container_id': self.id},
            'target': 'current',
        }
    
    def action_bulk_convert_container_type(self):
        """Bulk convert container types - wizard for changing multiple container types"""
        if len(self) == 1:
            # Single record action
            return {
                'type': 'ir.actions.act_window',
                'name': 'Convert Container Type',
                'res_model': 'records.container',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_container_type': self.container_type}
            }
        else:
            # Multiple records - could open wizard in future
            # For now, just open form view to edit selected records
            return {
                'type': 'ir.actions.act_window',
                'name': 'Bulk Convert Container Types',
                'res_model': 'records.container',
                'domain': [('id', 'in', self.ids)],
                'view_mode': 'tree',
                'target': 'current',
                'context': {'active_ids': self.ids}
            }
    
    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    @api.constrains('estimated_weight', 'actual_weight')
    def _check_weights(self):
        """Validate weight values"""
        for record in self:
            if record.estimated_weight and record.estimated_weight < 0:
                raise ValidationError(_('Estimated weight cannot be negative'))
            if record.actual_weight and record.actual_weight < 0:
                raise ValidationError(_('Actual weight cannot be negative'))
    
    @api.constrains('estimated_pages')
    def _check_pages(self):
        """Validate page count"""
        for record in self:
            if record.estimated_pages and record.estimated_pages < 0:
                raise ValidationError(_('Estimated pages cannot be negative'))
