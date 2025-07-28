# -*- coding: utf-8 -*-
"""
Records Box Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class RecordsBox(models.Model):
    """
    Records Box Management
    Core model for tracking physical records storage boxes
    """
    
    _name = 'records.box'
    _description = 'Records Box'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = "name"
    
    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Box Number', required=True, tracking=True)
    description = fields.Text(string='Box Description', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Box Manager', 
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
    location_id = fields.Many2one('records.location', string='Storage Location', tracking=True)
    container_id = fields.Many2one('records.container', string='Container', tracking=True)
    
    # ==========================================
    # BOX SPECIFICATIONS
    # ==========================================
    box_type = fields.Selection([
        ('standard', 'Standard Box'),
        ('legal', 'Legal Size Box'),
        ('oversized', 'Oversized Box'),
        ('hanging', 'Hanging File Box'),
        ('archive', 'Archive Box')
    ], string='Box Type', default='standard', required=True, tracking=True)
    
    # Computed display fields for box type
    box_type_code = fields.Char(string='Box Type Code', compute='_compute_box_type_display', store=True)
    box_type_display = fields.Char(string='Box Type Display', compute='_compute_box_type_display', store=True)
    
    # Barcode for box identification
    barcode = fields.Char(string='Barcode', tracking=True, copy=False)
    
    # Monthly storage rate
    monthly_rate = fields.Float(string='Monthly Storage Rate', digits=(10, 2), tracking=True, 
                               help='Monthly storage rate for this box')
    
    # Measurements
    estimated_weight = fields.Float(string='Estimated Weight (lbs)', tracking=True)
    actual_weight = fields.Float(string='Actual Weight (lbs)', tracking=True)
    weight = fields.Float(string='Weight (lbs)', compute='_compute_weight', store=True,
                         help='Current weight: actual weight if available, otherwise estimated weight')
    
    # ==========================================
    # CONTENT TRACKING
    # ==========================================
    document_ids = fields.One2many('records.document', 'box_id', string='Documents')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count', store=True)
    confidential_documents = fields.Boolean(string='Contains Confidential Documents', 
                                           compute='_compute_confidential_status', store=True)
    
    # Content estimates
    estimated_pages = fields.Integer(string='Estimated Pages', tracking=True)
    content_summary = fields.Text(string='Content Summary', tracking=True)
    
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
    # BALE ASSIGNMENT (for destroyed boxes)
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
        """Count documents in box"""
        for record in self:
            record.document_count = len(record.document_ids)
    
    @api.depends('document_ids', 'document_ids.confidential')
    def _compute_confidential_status(self):
        """Check if box contains confidential documents"""
        for record in self:
            record.confidential_documents = any(record.document_ids.mapped('confidential'))
    
    @api.depends('actual_weight', 'estimated_weight')
    def _compute_weight(self):
        """Compute weight: actual weight if available, otherwise estimated weight"""
        for record in self:
            record.weight = record.actual_weight or record.estimated_weight or 0.0
    
    @api.depends('box_type')
    def _compute_box_type_display(self):
        """Compute box type display fields"""
        for record in self:
            if record.box_type:
                # Create display name from selection
                display = dict(record._fields['box_type'].selection).get(record.box_type, record.box_type)
                record.box_type_display = display
                # Create code from box type
                code_map = {
                    'standard': 'STD',
                    'legal': 'LGL',
                    'oversized': 'LRG',
                    'hanging': 'HNG',
                    'archive': 'ARC'
                }
                record.box_type_code = code_map.get(record.box_type, 'STD')
            else:
                record.box_type_display = ''
                record.box_type_code = ''
    
    # ==========================================
    # WORKFLOW METHODS
    # ==========================================
    def action_index_box(self):
        """Mark box as indexed"""
        self.ensure_one()
        if self.state != 'received':
            raise ValidationError(_('Only received boxes can be indexed'))
        
        self.write({
            'state': 'indexed',
            'indexed_date': fields.Date.today()
        })
        self.message_post(body=_('Box indexed'))
    
    def action_store_box(self):
        """Mark box as stored"""
        self.ensure_one()
        if self.state != 'indexed':
            raise ValidationError(_('Only indexed boxes can be stored'))
        
        if not self.location_id:
            raise ValidationError(_('Storage location must be specified'))
        
        self.write({
            'state': 'stored',
            'stored_date': fields.Date.today()
        })
        self.message_post(body=_('Box stored at %s') % self.location_id.name)
    
    def action_retrieve_box(self):
        """Mark box as retrieved"""
        self.ensure_one()
        if self.state != 'stored':
            raise ValidationError(_('Only stored boxes can be retrieved'))
        
        self.write({
            'state': 'retrieved',
            'retrieval_date': fields.Date.today()
        })
        self.message_post(body=_('Box retrieved from storage'))
    
    def action_destroy_box(self):
        """Mark box as destroyed"""
        self.ensure_one()
        if self.state not in ['stored', 'retrieved']:
            raise ValidationError(_('Only stored or retrieved boxes can be destroyed'))
        
        self.write({
            'state': 'destroyed',
            'destruction_date': fields.Date.today()
        })
        self.message_post(body=_('Box marked for destruction'))
    
    def action_generate_barcode(self):
        """Generate barcode for the box"""
        self.ensure_one()
        if not self.barcode:
            # Generate a simple barcode based on box name and id
            barcode = f"BOX-{self.name}-{self.id}"
            self.write({'barcode': barcode})
            self.message_post(body=_('Barcode generated: %s') % barcode)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Print Barcode',
            'res_model': 'records.box',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_documents(self):
        """View documents in this box"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents in Box %s' % self.name,
            'res_model': 'records.document',
            'domain': [('box_id', '=', self.id)],
            'view_mode': 'tree,form',
            'context': {'default_box_id': self.id},
            'target': 'current',
        }
    
    def action_bulk_convert_box_type(self):
        """Bulk convert box types - wizard for changing multiple box types"""
        if len(self) == 1:
            # Single record action
            return {
                'type': 'ir.actions.act_window',
                'name': 'Convert Box Type',
                'res_model': 'records.box',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_box_type': self.box_type}
            }
        else:
            # Multiple records - could open wizard in future
            # For now, just open form view to edit selected records
            return {
                'type': 'ir.actions.act_window',
                'name': 'Bulk Convert Box Types',
                'res_model': 'records.box',
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
