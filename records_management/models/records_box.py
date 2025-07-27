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
    user_id = fields.Many2one('res.users', string='Responsible User', 
                             default=lambda self: self.env.user, tracking=True)
    
    # ==========================================
    # CUSTOMER AND LOCATION
    # ==========================================
    customer_id = fields.Many2one('res.partner', string='Customer', 
                                 required=True, tracking=True,
                                 domain=[('is_company', '=', True)])
    location_id = fields.Many2one('records.location', string='Storage Location', tracking=True)
    container_id = fields.Many2one('container', string='Container', tracking=True)
    
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
    
    # Measurements
    estimated_weight = fields.Float(string='Estimated Weight (lbs)', tracking=True)
    actual_weight = fields.Float(string='Actual Weight (lbs)', tracking=True)
    
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
    bale_id = fields.Many2one('records.management.bale', string='Assigned Bale', tracking=True)
    
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
