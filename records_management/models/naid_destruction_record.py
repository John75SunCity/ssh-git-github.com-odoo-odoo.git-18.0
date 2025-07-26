# -*- coding: utf-8 -*-
"""
NAID Destruction Record Management
Tracks destruction records and certificates
"""

from odoo import models, fields, api

class NAIDDestructionRecord(models.Model):
    _name = 'naid.destruction.record'
    _description = 'NAID Destruction Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'destruction_date desc, name'
    _rec_name = 'name'

    # Core identification
    name = fields.Char('Record Name', required=True, tracking=True)
    destruction_number = fields.Char('Destruction Number', required=True, tracking=True)
    destruction_type = fields.Selection([
        ('shredding', 'Shredding'),
        ('pulping', 'Pulping'),
        ('disintegration', 'Disintegration'),
        ('incineration', 'Incineration'),
        ('chemical', 'Chemical Destruction'),
        ('degaussing', 'Degaussing'),
        ('overwriting', 'Data Overwriting')
    
    # NAID compliance relationship
    compliance_id = fields.Many2one('naid.compliance', string='NAID Compliance Record', tracking=True)
    
    # Destruction details
    destruction_date = fields.Datetime('Destruction Date', required=True, tracking=True)
    completion_date = fields.Datetime('Completion Date', tracking=True)
    certificate_date = fields.Date('Certificate Date', tracking=True)
    
    # Material details
    material_type = fields.Selection([
        ('paper', 'Paper Documents'),
        ('hard_drive', 'Hard Drives'),
        ('optical_media', 'Optical Media'),
        ('magnetic_tape', 'Magnetic Tape'),
        ('electronic', 'Electronic Devices'),
        ('mixed', 'Mixed Materials')
    
    total_weight = fields.Float('Total Weight', tracking=True)
    item_count = fields.Integer('Item Count', tracking=True)
    
    # Customer and location
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    destruction_location = fields.Many2one('records.location', string='Destruction Location', tracking=True)
    
    # Personnel and witnesses
    destruction_supervisor = fields.Many2one('res.users', string='Destruction Supervisor', tracking=True)
    customer_witness = fields.Many2one('res.partner', string='Customer Witness', tracking=True)
    naid_witness = fields.Many2one('res.users', string='NAID Witness', tracking=True)
    
    # Status and verification
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('certified', 'Certified'),
        ('cancelled', 'Cancelled')
    
    witnessed = fields.Boolean('Witnessed Destruction', tracking=True)
    photographed = fields.Boolean('Photographed', tracking=True)
    video_recorded = fields.Boolean('Video Recorded', tracking=True)
    
    # Certificate details
    certificate_number = fields.Char('Certificate Number', tracking=True)
    certificate_generated = fields.Boolean('Certificate Generated', tracking=True)
    
    # Company and user context
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible User', default=lambda self: self.env.user)
    active = fields.Boolean('Active', default=True)
    
    # Additional details
    description = fields.Text('Description')
    destruction_notes = fields.Text('Destruction Notes')
    special_instructions = fields.Text('Special Instructions')
    
    def action_start_destruction(self):
        """Start the destruction process"""
        self.ensure_one()
        self.write({
            'status': 'in_progress',
            'destruction_date': fields.Datetime.now()
        })
        
    def action_complete_destruction(self):
        """Complete the destruction process"""
        self.ensure_one()
        self.write({
            'status': 'completed',
            'completion_date': fields.Datetime.now()
        })
        
    def action_generate_certificate(self):
        """Generate destruction certificate"""
        self.ensure_one()
        # Generate certificate logic here
        certificate_number = f"CERT-{self.destruction_number}-{fields.Date.today().strftime('%Y%m%d')}"
        self.write({
            'status': 'certified',
            'certificate_generated': True,
            'certificate_number': certificate_number,
            'certificate_date': fields.Date.today()
        })
