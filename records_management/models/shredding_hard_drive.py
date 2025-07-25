# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ShreddingHardDrive(models.Model):
    """Model for hard drive and electronic media destruction tracking."""
    _name = 'shredding.hard_drive'
    _description = 'Hard Drive Destruction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_id, destruction_date desc'

    # Core fields
    name = fields.Char('Drive Reference', required=True, default='/')
    description = fields.Text('Description')
    
    # Service relationship
    service_id = fields.Many2one('shredding.service', string='Shredding Service', 
                                 required=True, ondelete='cascade')
    
    # Device identification
    device_type = fields.Selection([
        ('hdd', 'Hard Disk Drive (HDD)'),
        ('ssd', 'Solid State Drive (SSD)'),
        ('usb', 'USB Drive'),
        ('cd_dvd', 'CD/DVD'),
        ('tape', 'Magnetic Tape'),
        ('floppy', 'Floppy Disk'),
        ('mobile', 'Mobile Device'),
        ('tablet', 'Tablet'),
        ('laptop', 'Laptop Hard Drive'),
        ('server', 'Server Drive'),
        ('other', 'Other Electronic Media')
    ], string='Device Type', required=True, tracking=True)
    
    # Physical characteristics
    manufacturer = fields.Char('Manufacturer')
    model_number = fields.Char('Model Number')
    serial_number = fields.Char('Serial Number', tracking=True)
    capacity_gb = fields.Float('Capacity (GB)', digits=(10, 2))
    physical_size = fields.Selection([
        ('2.5', '2.5 inch'),
        ('3.5', '3.5 inch'),
        ('m.2', 'M.2'),
        ('usb', 'USB Form Factor'),
        ('custom', 'Custom Size'),
        ('other', 'Other')
    ], string='Physical Size')
    
    # Security and data classification
    security_level = fields.Selection([
        ('standard', 'Standard'),
        ('confidential', 'Confidential'),
        ('secret', 'Secret'),
        ('top_secret', 'Top Secret'),
        ('custom', 'Custom Classification')
    ], string='Security Level', default='standard', required=True)
    
    data_classification = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal Use'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
        ('pii', 'Personally Identifiable Information'),
        ('phi', 'Protected Health Information'),
        ('financial', 'Financial Data'),
        ('government', 'Government Classified')
    ], string='Data Classification', required=True)
    
    # Destruction details
    destruction_method = fields.Selection([
        ('physical_shred', 'Physical Shredding'),
        ('disintegration', 'Disintegration'),
        ('degaussing', 'Degaussing'),
        ('crushing', 'Physical Crushing'),
        ('incineration', 'Incineration'),
        ('acid_bath', 'Chemical Destruction'),
        ('combined', 'Combined Methods')
    ], string='Destruction Method', required=True, tracking=True)
    
    destruction_date = fields.Datetime('Destruction Date', tracking=True)
    destruction_technician = fields.Many2one('res.users', string='Destruction Technician')
    witness_present = fields.Boolean('Witness Present', default=False)
    witness_name = fields.Char('Witness Name')
    
    # Chain of custody
    received_from = fields.Char('Received From')
    received_date = fields.Datetime('Received Date', default=fields.Datetime.now)
    custody_verified = fields.Boolean('Custody Verified', default=False)
    
    # Pre-destruction verification
    data_wiped = fields.Boolean('Data Previously Wiped', default=False)
    encryption_status = fields.Selection([
        ('none', 'No Encryption'),
        ('basic', 'Basic Encryption'),
        ('advanced', 'Advanced Encryption'),
        ('military', 'Military Grade'),
        ('unknown', 'Unknown')
    ], string='Encryption Status', default='unknown')
    
    functionality_test = fields.Selection([
        ('functional', 'Functional'),
        ('partial', 'Partially Functional'),
        ('non_functional', 'Non-Functional'),
        ('damaged', 'Physically Damaged')
    ], string='Pre-Destruction Functionality')
    
    # Destruction verification
    destruction_verified = fields.Boolean('Destruction Verified', default=False)
    particle_size_mm = fields.Float('Particle Size (mm)', digits=(5, 2),
                                   help='Maximum particle size after destruction')
    destruction_photographed = fields.Boolean('Destruction Photographed', default=False)
    video_recorded = fields.Boolean('Video Recorded', default=False)
    
    # Compliance and standards
    nist_compliant = fields.Boolean('NIST 800-88 Compliant', default=False)
    dod_compliant = fields.Boolean('DoD 5220.22-M Compliant', default=False)
    hipaa_compliant = fields.Boolean('HIPAA Compliant', default=False)
    custom_standard = fields.Char('Custom Standard')
    
    # Certificate and documentation
    certificate_generated = fields.Boolean('Certificate Generated', default=False)
    certificate_number = fields.Char('Certificate Number')
    chain_of_custody_complete = fields.Boolean('Chain of Custody Complete', default=False)
    
    # Status
    state = fields.Selection([
        ('received', 'Received'),
        ('verified', 'Verified'),
        ('ready', 'Ready for Destruction'),
        ('in_progress', 'Destruction in Progress'),
        ('destroyed', 'Destroyed'),
        ('certified', 'Certified Complete')
    ], string='Status', default='received', tracking=True)
    
    # Weight and measurements
    weight_kg = fields.Float('Weight (kg)', digits=(8, 3))
    dimensions = fields.Char('Dimensions (L x W x H)')
    
    # Environmental considerations
    hazardous_materials = fields.Boolean('Contains Hazardous Materials', default=False)
    special_handling = fields.Text('Special Handling Requirements')
    
    # Company and customer
    customer_id = fields.Many2one('res.partner', string='Customer')
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
    active = fields.Boolean('Active', default=True)
    
    # Computed fields
    days_in_custody = fields.Integer('Days in Custody', compute='_compute_custody_days')
    service_name = fields.Char('Service Name', related='service_id.name', readonly=True)
    compliance_score = fields.Float('Compliance Score', compute='_compute_compliance_score')
    destruction_complete = fields.Boolean('Destruction Complete', compute='_compute_destruction_status')
    
    @api.depends('received_date')
    def _compute_custody_days(self):
        """Compute days the device has been in custody"""
        for record in self:
            if record.received_date:
                end_date = record.destruction_date or fields.Datetime.now()
                delta = end_date - record.received_date
                record.days_in_custody = delta.days
            else:
                record.days_in_custody = 0
    
    @api.depends('nist_compliant', 'dod_compliant', 'hipaa_compliant', 'destruction_verified', 'certificate_generated')
    def _compute_compliance_score(self):
        """Compute compliance score based on standards met"""
        for record in self:
            score = 0
            total_checks = 5
            
            if record.nist_compliant:
                score += 1
            if record.dod_compliant:
                score += 1
            if record.hipaa_compliant:
                score += 1
            if record.destruction_verified:
                score += 1
            if record.certificate_generated:
                score += 1
                
            record.compliance_score = (score / total_checks) * 100
    
    @api.depends('state', 'destruction_verified', 'certificate_generated')
    def _compute_destruction_status(self):
        """Determine if destruction process is complete"""
        for record in self:
            record.destruction_complete = (
                record.state in ('destroyed', 'certified') and
                record.destruction_verified and
                record.certificate_generated
            )
    
    @api.model
    def create(self, vals):
        """Generate sequence for drive reference"""
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('shredding.hard.drive') or '/'
        return super().create(vals)
    
    @api.constrains('particle_size_mm')
    def _check_particle_size(self):
        """Validate particle size requirements"""
        for record in self:
            if record.particle_size_mm and record.particle_size_mm > 2.0:
                if record.security_level in ('secret', 'top_secret'):
                    raise ValidationError(_('Particle size must be ≤ 2mm for high security items'))
    
    def action_verify_device(self):
        """Verify device details and custody"""
        self.ensure_one()
        self.write({
            'state': 'verified',
            'custody_verified': True
        })
    
    def action_start_destruction(self):
        """Start the destruction process"""
        self.ensure_one()
        if not self.destruction_technician:
            raise ValidationError(_('Destruction technician must be assigned'))
        self.write({'state': 'in_progress'})
    
    def action_complete_destruction(self):
        """Complete the destruction process"""
        self.ensure_one()
        self.write({
            'state': 'destroyed',
            'destruction_date': fields.Datetime.now(),
            'destruction_verified': True
        })
    
    def action_generate_certificate(self):
        """Generate destruction certificate"""
        self.ensure_one()
        if not self.destruction_verified:
            raise ValidationError(_('Destruction must be verified before generating certificate'))
        
        certificate_num = self.env['ir.sequence'].next_by_code('destruction.certificate') or '/'
        self.write({
            'state': 'certified',
            'certificate_generated': True,
            'certificate_number': certificate_num,
            'chain_of_custody_complete': True
        })
