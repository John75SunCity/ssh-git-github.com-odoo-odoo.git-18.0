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
    user_id = fields.Many2one('res.users', string='Responsible User', 
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
    
    confidential = fields.Boolean(string='Confidential', tracking=True)
    classification_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string='Classification', default='internal', tracking=True)
    
    # ==========================================
    # PHYSICAL PROPERTIES
    # ==========================================
    page_count = fields.Integer(string='Number of Pages', tracking=True)
    document_format = fields.Selection([
        ('paper', 'Paper'),
        ('digital', 'Digital Copy'),
        ('microfilm', 'Microfilm'),
        ('cd_dvd', 'CD/DVD'),
        ('usb', 'USB Drive')
    ], string='Format', default='paper', tracking=True)
    
    # ==========================================
    # RELATIONSHIPS
    # ==========================================
    box_id = fields.Many2one('records.box', string='Records Box', tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer',
                                 domain=[('is_company', '=', True)], tracking=True)
    
    # ==========================================
    # DATE TRACKING
    # ==========================================
    creation_date = fields.Date(string='Document Date', tracking=True)
    received_date = fields.Date(string='Received Date', 
                               default=fields.Date.today, tracking=True)
    
    # ==========================================
    # RETENTION AND DISPOSAL
    # ==========================================
    retention_period_years = fields.Integer(string='Retention Period (Years)', 
                                           default=7, tracking=True)
    destruction_date = fields.Date(string='Scheduled Destruction Date', 
                                  compute='_compute_destruction_date', store=True)
    destroyed = fields.Boolean(string='Destroyed', tracking=True)
    destruction_certificate_id = fields.Many2one('destruction.certificate', 
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
            else:
                record.destruction_date = False
    
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
        certificate = self.env['destruction.certificate'].create(cert_vals)
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
