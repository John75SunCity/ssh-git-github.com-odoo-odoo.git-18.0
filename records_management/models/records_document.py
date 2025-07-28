# -*- coding: utf-8 -*-
"""
Records Document Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class RecordsDocument(models.Model):
    """
    Records Document Management
    Individual document tracking within records boxes
    """
    
    _name = 'records.document'
    _description = 'Records Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = "name"
    
    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Document Title', required=True, tracking=True)
    description = fields.Text(string='Description', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Document Manager', 
                             default=lambda self: self.env.user, tracking=True)
    
    # ==========================================
    # DOCUMENT CLASSIFICATION
    # ==========================================
    document_type = fields.Selection([
        ('financial', 'Financial Records'),
        ('legal', 'Legal Documents'),
        ('personnel', 'Personnel Files'),
        ('medical', 'Medical Records'),
        ('insurance', 'Insurance Documents'),
        ('tax', 'Tax Records'),
        ('contracts', 'Contracts'),
        ('correspondence', 'Correspondence'),
        ('other', 'Other')
    ], string='Document Type', required=True, tracking=True)
    
    document_type_id = fields.Many2one('records.document.type', string='Document Type', tracking=True)
    document_category = fields.Char(string='Document Category', tracking=True)
    
    confidential = fields.Boolean(string='Confidential', tracking=True)
    classification_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string='Classification', default='internal', tracking=True)
    
    # State management
    state = fields.Selection([
        ('active', 'Active'),
        ('pending_destruction', 'Pending Destruction'),
        ('destroyed', 'Destroyed')
    ], string='State', default='active', tracking=True)
    
    # Permanent flag for records that should never be destroyed
    permanent_flag = fields.Boolean(string='Permanent Record', tracking=True)
    permanent_flag_set_by = fields.Many2one('res.users', string='Permanent Flag Set By', tracking=True)
    permanent_flag_set_date = fields.Date(string='Permanent Flag Set Date', tracking=True)
    
    # ==========================================
    # PHYSICAL PROPERTIES
    # ==========================================
    page_count = fields.Integer(string='Number of Pages', tracking=True)
    document_format = fields.Selection([
        ('paper', 'Paper'),
        ('digital', 'Digital Scan'),
        ('microfilm', 'Microfilm'),
        ('cd_dvd', 'CD/DVD'),
        ('usb', 'USB Drive')
    ], string='Format', default='paper', tracking=True)
    
    # Additional classification fields
    media_type = fields.Selection([
        ('paper', 'Paper'),
        ('digital', 'Digital'),
        ('microfilm', 'Microfilm'),
        ('other', 'Other')
    ], string='Media Type', default='paper', tracking=True)
    
    original_format = fields.Char(string='Original Format', tracking=True)
    digitized = fields.Boolean(string='Digitized', tracking=True)
    
    # ==========================================
    # RELATIONSHIPS
    # ==========================================
    box_id = fields.Many2one('records.box', string='Records Box', tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer',
                                 domain=[('is_company', '=', True)], tracking=True)
    department_id = fields.Many2one('records.department', string='Department', tracking=True)
    retention_policy_id = fields.Many2one('records.retention.policy', string='Retention Policy', tracking=True)
    
    # One2many relationships
    digital_scan_ids = fields.One2many('records.digital.scan', 'document_id', string='Digital Scans')
    
    # ==========================================
    # DATE TRACKING
    # ==========================================
    creation_date = fields.Date(string='Document Date', tracking=True)
    created_date = fields.Date(string='Created Date', tracking=True)
    received_date = fields.Date(string='Received Date', 
                               default=fields.Date.today, tracking=True)
    storage_date = fields.Date(string='Storage Date', tracking=True)
    last_access_date = fields.Date(string='Last Access Date', tracking=True)
    
    # ==========================================
    # RETENTION AND DISPOSAL
    # ==========================================
    retention_period_years = fields.Integer(string='Retention Period (Years)', 
                                           default=7, tracking=True)
    destruction_date = fields.Date(string='Scheduled Destruction Date', 
                                  compute='_compute_destruction_date', store=True)
    destruction_eligible_date = fields.Date(string='Destruction Eligible Date',
                                           compute='_compute_destruction_date', store=True)
    days_until_destruction = fields.Integer(string='Days Until Destruction',
                                           compute='_compute_days_until_destruction')
    destroyed = fields.Boolean(string='Destroyed', tracking=True)
    destruction_certificate_id = fields.Many2one('naid.certificate', 
                                                string='Destruction Certificate')
    
    # ==========================================
    # NOTES
    # ==========================================
    notes = fields.Text(string='Notes', tracking=True)
    special_instructions = fields.Text(string='Special Instructions', tracking=True)
    
    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends('received_date', 'retention_period_years')
    def _compute_destruction_date(self):
        """Calculate destruction date based on retention period"""
        for record in self:
            if record.received_date and record.retention_period_years:
                from dateutil.relativedelta import relativedelta
                record.destruction_date = record.received_date + relativedelta(years=record.retention_period_years)
                record.destruction_eligible_date = record.destruction_date
            else:
                record.destruction_date = False
                record.destruction_eligible_date = False
    
    @api.depends('destruction_eligible_date')
    def _compute_days_until_destruction(self):
        """Calculate days until destruction"""
        today = fields.Date.today()
        for record in self:
            if record.destruction_eligible_date:
                delta = record.destruction_eligible_date - today
                record.days_until_destruction = delta.days
            else:
                record.days_until_destruction = 0
    
    # ==========================================
    # ACTION METHODS
    # ==========================================
    def action_mark_destroyed(self):
        """Mark document as destroyed"""
        self.ensure_one()
        self.write({'destroyed': True})
        self.message_post(body=_('Document marked as destroyed'))
    
    def action_create_destruction_certificate(self):
        """Create destruction certificate"""
        self.ensure_one()
        if not self.destroyed:
            self.write({'destroyed': True})
        
        cert_vals = {
            'name': f'Destruction Certificate - {self.name}',
            'document_id': self.id,
            'customer_id': self.customer_id.id if self.customer_id else False,
            'destruction_date': fields.Date.today(),
            'destruction_method': 'shredding',
        }
        certificate = self.env['naid.certificate'].create(cert_vals)
        self.write({'destruction_certificate_id': certificate.id})
        
        self.message_post(body=_('Destruction certificate created'))
    
    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    @api.constrains('retention_period_years')
    def _check_retention_period(self):
        """Validate retention period"""
        for record in self:
            if record.retention_period_years and record.retention_period_years < 0:
                raise ValidationError(_('Retention period cannot be negative'))
    
    @api.constrains('page_count')
    def _check_page_count(self):
        """Validate page count"""
        for record in self:
            if record.page_count and record.page_count < 0:
                raise ValidationError(_('Page count cannot be negative'))
