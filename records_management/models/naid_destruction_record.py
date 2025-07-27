# -*- coding: utf-8 -*-
"""
NAID Destruction Record Management
"""

from odoo import models, fields, api, _
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class NAIDDestructionRecord(models.Model):
    """
    NAID Destruction Record Management
    Manages comprehensive destruction records for NAID compliance
    """
    
    _name = 'naid.destruction.record'
    _description = 'NAID Destruction Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'destruction_date desc, name'
    _rec_name = "name"
    
    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Record Number', required=True, tracking=True, 
                       default=lambda self: _('New'))
    description = fields.Text(string='Description', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Responsible User', 
                             default=lambda self: self.env.user, tracking=True)
    
    # ==========================================
    # DESTRUCTION DETAILS
    # ==========================================
    destruction_date = fields.Datetime(string='Destruction Date', 
                                       default=fields.Datetime.now, tracking=True)
    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('pulping', 'Pulping'),
        ('incineration', 'Incineration'),
        ('disintegration', 'Disintegration'),
        ('chemical', 'Chemical Destruction')
    ], string='Destruction Method', required=True, tracking=True)
    
    destruction_location = fields.Char(string='Destruction Location', tracking=True)
    equipment_used = fields.Char(string='Equipment Used', tracking=True)
    
    # ==========================================
    # NAID COMPLIANCE
    # ==========================================
    naid_certificate_id = fields.Many2one('naid.certificate', string='NAID Certificate', tracking=True)
    destruction_level = fields.Selection([
        ('dod_3_pass', 'DoD 3-Pass'),
        ('dod_7_pass', 'DoD 7-Pass'),
        ('nist_purge', 'NIST Purge'),
        ('physical_destruction', 'Physical Destruction')
    ], string='Destruction Level', tracking=True)
    
    # ==========================================
    # CHAIN OF CUSTODY
    # ==========================================
    custody_received_from = fields.Many2one('res.partner', string='Received From', tracking=True)
    custody_received_date = fields.Datetime(string='Received Date', tracking=True)
    custody_delivered_by = fields.Many2one('res.users', string='Delivered By', tracking=True)
    
    # ==========================================
    # WITNESSES
    # ==========================================
    witness_ids = fields.One2many('destruction.witness', 'destruction_record_id', 
                                  string='Witnesses')
    witness_count = fields.Integer(string='Witness Count', 
                                  compute='_compute_witness_count', store=True)
    
    # ==========================================
    # DOCUMENTATION
    # ==========================================
    destruction_photographed = fields.Boolean(string='Destruction Photographed', tracking=True)
    video_recorded = fields.Boolean(string='Video Recorded', tracking=True)
    
    destruction_report = fields.Html(string='Destruction Report', tracking=True)
    destruction_notes = fields.Text(string='Destruction Notes', tracking=True)
    
    # ==========================================
    # VERIFICATION
    # ==========================================
    verified = fields.Boolean(string='Verified', tracking=True)
    verified_by = fields.Many2one('res.users', string='Verified By', tracking=True)
    verification_date = fields.Datetime(string='Verification Date', tracking=True)
    
    # ==========================================
    # STATUS
    # ==========================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('certified', 'Certified')
    ], string='Status', default='draft', tracking=True, required=True)
    
    # ==========================================
    # ITEMS DESTROYED
    # ==========================================
    destruction_item_ids = fields.One2many('destruction.item', 'destruction_record_id', 
                                           string='Items Destroyed')
    
    total_weight = fields.Float(string='Total Weight (lbs)', 
                               compute='_compute_total_weight', store=True)
    total_boxes = fields.Integer(string='Total Boxes', 
                                compute='_compute_totals', store=True)
    
    # ==========================================
    # CERTIFICATE GENERATION
    # ==========================================
    certificate_generated = fields.Boolean(string='Certificate Generated', tracking=True)
    certificate_date = fields.Datetime(string='Certificate Date', tracking=True)
    certificate_number = fields.Char(string='Certificate Number', tracking=True)
    
    # ==========================================
    # COMPUTE METHODS
    # ==========================================
    @api.depends('witness_ids')
    def _compute_witness_count(self):
        for record in self:
            record.witness_count = len(record.witness_ids)
    
    @api.depends('destruction_item_ids', 'destruction_item_ids.weight')
    def _compute_total_weight(self):
        for record in self:
            record.total_weight = sum(record.destruction_item_ids.mapped('weight'))
    
    @api.depends('destruction_item_ids')
    def _compute_totals(self):
        for record in self:
            record.total_boxes = len(record.destruction_item_ids)
    
    # ==========================================
    # WORKFLOW METHODS
    # ==========================================
    def action_start_destruction(self):
        """Start destruction process"""
        self.ensure_one()
        if self.state != 'draft':
            return
        
        self.write({
            'state': 'in_progress',
            'destruction_date': fields.Datetime.now()
        })
        self.message_post(body=_('Destruction process started'))
    
    def action_complete_destruction(self):
        """Complete destruction process"""
        self.ensure_one()
        if self.state != 'in_progress':
            return
        
        self.write({'state': 'completed'})
        self.message_post(body=_('Destruction process completed'))
    
    def action_verify(self):
        """Verify destruction"""
        self.ensure_one()
        if self.state != 'completed':
            return
        
        self.write({
            'state': 'verified',
            'verified': True,
            'verified_by': self.env.user.id,
            'verification_date': fields.Datetime.now()
        })
        self.message_post(body=_('Destruction verified'))
    
    def action_generate_certificate(self):
        """Generate destruction certificate"""
        self.ensure_one()
        if self.state != 'verified':
            return
        
        # Generate certificate number
        sequence = self.env['ir.sequence'].next_by_code('naid.destruction.certificate')
        
        self.write({
            'state': 'certified',
            'certificate_generated': True,
            'certificate_date': fields.Datetime.now(),
            'certificate_number': sequence
        })
        self.message_post(body=_('Destruction certificate generated: %s') % sequence)
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('naid.destruction.record') or _('New')
        return super().create(vals_list)


class DestructionWitness(models.Model):
    """Witness for destruction process"""
    
    _name = 'destruction.witness'
    _description = 'Destruction Witness'
    _inherit = ['mail.thread']
    
    destruction_record_id = fields.Many2one('naid.destruction.record', 
                                           string='Destruction Record', required=True)
    partner_id = fields.Many2one('res.partner', string='Witness', required=True, tracking=True)
    witness_type = fields.Selection([
        ('customer', 'Customer Representative'),
        ('naid', 'NAID Representative'),
        ('internal', 'Internal Witness'),
        ('third_party', 'Third Party Auditor')
    ], string='Witness Type', required=True, tracking=True)
    
    signature_required = fields.Boolean(string='Signature Required', default=True)
    signature_obtained = fields.Boolean(string='Signature Obtained', tracking=True)
    signature_date = fields.Datetime(string='Signature Date', tracking=True)
    
    notes = fields.Text(string='Notes', tracking=True)
