# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
import hashlib
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ShreddingService(models.Model):
    """Document Shredding Service with enhanced workflow, NAID/ISO compliance, including hard drives and uniforms."""
    _name = 'shredding.service'
    _description = 'Document Shredding Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_date desc, name'

    name = fields.Char(string='Service Reference', required=True, default='New')
    status = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('in_progress', 'In Progress'),
        ('completed', 'Completed'), ('invoiced', 'Invoiced'), ('cancelled', 'Cancelled')
    ], default='draft', string='Status')
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    department_id = fields.Many2one('records.department', string='Department', domain="[('partner_id', '=', customer_id)]")  # Added for granular
    service_date = fields.Date(string='Service Date', default=fields.Date.context_today, required=True)
    scheduled_date = fields.Date(string='Scheduled Date')
    service_type = fields.Selection([
        ('bin', 'Bin Shredding'), ('box', 'Box Shredding'),
        ('hard_drive', 'Hard Drive Destruction'), ('uniform', 'Uniform Shredding')
    bin_ids = fields.Many2many(
        'stock.lot',
        relation='shredding_service_bin_rel',  # Custom relation to avoid conflict with shredded_box_ids
        column1='service_id',
        column2='lot_id',
        string='Serviced Bins',
        domain="[('product_id.name', '=', 'Shredding Bin')]"
    box_quantity = fields.Integer(string='Number of Boxes')
    shredded_box_ids = fields.Many2many('stock.lot', 
                                        relation='shredding_service_shredded_box_rel',
                                        column1='service_id',
                                        column2='lot_id',
                                        string='Shredded Boxes', 
                                        domain="[('customer_id', '!=', False)]")
    hard_drive_quantity = fields.Integer(string='Number of Hard Drives')  # New
    hard_drive_ids = fields.One2many('shredding.hard_drive', 'service_id', string='Hard Drive Details')
    hard_drive_scanned_count = fields.Integer(compute='_compute_hard_drive_counts', store=True, string='Scanned Count', compute_sudo=False)
    hard_drive_verified_count = fields.Integer(compute='_compute_hard_drive_counts', store=True, string='Verified Count', compute_sudo=False)
    item_count = fields.Integer(compute='_compute_item_count', store=True, string='Items to Destroy Count', compute_sudo=False)
    uniform_quantity = fields.Integer(string='Number of Uniforms')  # New
    total_boxes = fields.Integer(compute='_compute_total_boxes', store=True)
    unit_cost = fields.Float(string='Unit Cost', default=5.0)
    total_cost = fields.Float(compute='_compute_total_cost', store=True)
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    audit_barcodes = fields.Text(string='Audit Barcodes', help='Barcodes for NAID audit trails')
    total_charge = fields.Float(compute='_compute_total_charge', store=True)
    latitude = fields.Float(string='Latitude (for mobile verification)', digits=(16, 8))
    longitude = fields.Float('Longitude', digits=(16, 8))
    attachment_ids = fields.Many2many('ir.attachment', 
                                     relation='shredding_service_attachment_rel',
                                     column1='service_id',
                                     column2='attachment_id',
                                     string='Attachments (e.g., photos, CCTV clips)')
    map_display = fields.Char(compute='_compute_map_display', store=True)
    certificate_id = fields.Many2one('ir.attachment', string='Destruction Certificate', readonly=True)  # New for auto-certificate
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)  # New for auto-invoicing
    bale_ids = fields.One2many('paper.bale', 'shredding_id', string='Generated Bales')  # Link to bales
    pos_session_id = fields.Many2one('pos.session', string='POS Session (Walk-in)')  # New for walk-in
    estimated_bale_weight = fields.Float(compute='_compute_estimated_bale_weight', store=True, help='Predictive weight for recycling efficiency')

    # Phase 2 Audit & Compliance Fields - Added by automated script
    naid_certificate_id = fields.Many2one('naid.certificate', string='NAID Certificate')
    naid_compliance_level = fields.Selection([('aaa', 'NAID AAA'), ('aa', 'NAID AA'), ('a', 'NAID A')], string='NAID Compliance Level')
    naid_compliance_verified = fields.Boolean('NAID Compliance Verified', default=False)
    destruction_standard = fields.Selection([('dod_5220', 'DoD 5220.22-M'), ('nist_800_88', 'NIST 800-88'), ('iso_27040', 'ISO/IEC 27040'), ('custom', 'Custom Standard')], string='Destruction Standard')
    witness_verification_required = fields.Boolean('Witness Verification Required', default=True)
    witness_required = fields.Boolean('Witness Required', default=True, help='Shorthand for witness verification requirement')
    photo_documentation_required = fields.Boolean('Photo Documentation Required', default=True)
    video_documentation_required = fields.Boolean('Video Documentation Required', default=False)
    certificate_of_destruction = fields.Text('Certificate of Destruction Notes')
    audit_trail_ids = fields.One2many('records.audit.log', 'shredding_service_id', string='Audit Trail')
    compliance_documentation_ids = fields.Many2many('ir.attachment', relation='compliance_documentation_ids_rel', string='Compliance Documentation', 
                                                   domain="[('res_model', '=', 'shredding.service')  # Fixed: was One2many with missing inverse field]", 
                                                   compute='_compute_compliance_docs')
    destruction_method_verified = fields.Boolean('Destruction Method Verified', default=False)
    destruction_method = fields.Selection([
        ('shred', 'Physical Shredding'),
        ('crush', 'Crushing'),
        ('degauss', 'Degaussing'),
        ('wipe', 'Data Wiping'),
        ('incineration', 'Incineration'),
        ('pulverization', 'Pulverization')
    certificate_required = fields.Boolean('Certificate Required', default=True)
    chain_of_custody_maintained = fields.Boolean('Chain of Custody Maintained', default=False)
    environmental_compliance = fields.Boolean('Environmental Compliance Verified', default=False)
    quality_control_performed = fields.Boolean('Quality Control Performed', default=False)
    quality_control_date = fields.Datetime('Quality Control Date')
    quality_control_officer_id = fields.Many2one('res.users', string='Quality Control Officer')
    particle_size_verified = fields.Boolean('Particle Size Verified', default=False)
    contamination_check = fields.Boolean('Contamination Check Performed', default=False)
    equipment_calibration_verified = fields.Boolean('Equipment Calibration Verified', default=False)

    # Phase 2 Audit & Compliance Fields - Added by automated script
    audit_required = fields.Boolean('Audit Required', default=True)
    audit_completed = fields.Boolean('Audit Completed', default=False)
    audit_date = fields.Date('Audit Date')
    auditor_id = fields.Many2one('res.users', string='Auditor')
    compliance_status = fields.Selection([('pending', 'Pending'), ('compliant', 'Compliant'), ('non_compliant', 'Non-Compliant')], string='Compliance Status', default='pending')
    regulatory_approval = fields.Boolean('Regulatory Approval', default=False)
    
    # PHASE 3: Missing Critical Business Fields (55 fields) - NAID Compliance Enhanced
    
    # Timing and scheduling fields
    actual_completion_time = fields.Datetime('Actual Completion Time', tracking=True)
    actual_start_time = fields.Datetime('Actual Start Time', tracking=True)
    estimated_duration = fields.Float('Estimated Duration (hours)', default=2.0)
    equipment_calibration_date = fields.Date('Equipment Calibration Date', tracking=True)
    
    # Personnel assignments
    assigned_technician = fields.Many2one('res.users', string='Assigned Technician', tracking=True)
    security_officer = fields.Many2one('res.users', string='Security Officer', tracking=True)
    supervising_manager = fields.Many2one('res.users', string='Supervising Manager', tracking=True)
    customer_representative = fields.Many2one('res.partner', string='Customer Representative', tracking=True)
    
    # Location and transfer tracking
    location = fields.Many2one('records.location', string='Service Location', tracking=True)
    service_location = fields.Char('Service Location Description')
    transfer_date = fields.Date('Transfer Date', tracking=True)
    transfer_location = fields.Char('Transfer Location')
    
    # Personnel details for witnesses
    from_person = fields.Char('From Person')
    to_person = fields.Char('To Person')
    witness_count = fields.Integer('Number of Witnesses', default=0)
    witness_name = fields.Char('Witness Name')
    witness_title = fields.Char('Witness Title/Position')
    
    # Certificate and documentation
    certificate_count = fields.Integer('Certificate Count', compute='_compute_certificate_metrics', store=True)
    certificate_date = fields.Date('Certificate Date', tracking=True)
    certificate_notes = fields.Text('Certificate Notes')
    certificate_number = fields.Char('Certificate Number', tracking=True)
    certificate_type = fields.Selection([
        ('standard', 'Standard Certificate'),
        ('naid_aaa', 'NAID AAA Certificate'),
        ('iso', 'ISO Compliance Certificate'),
        ('custom', 'Custom Certificate')
    included_in_certificate = fields.Boolean('Included in Certificate', default=True)
    
    # Chain of custody and tracking
    chain_of_custody_ids = fields.Many2many('records.chain.custody', relation='chain_of_custody_ids_rel', string='Chain of Custody Records')  # Fixed: was One2many with missing inverse field
    chain_of_custody_number = fields.Char('Chain of Custody Number', tracking=True)
    seal_number = fields.Char('Seal Number', tracking=True)
    serial_number = fields.Char('Serial Number', tracking=True)
    
    # Weight and measurements
    pre_destruction_weight = fields.Float('Pre-Destruction Weight (lbs)', tracking=True)
    post_destruction_weight = fields.Float('Post-Destruction Weight (lbs)', tracking=True)
    particle_size = fields.Float('Particle Size (mm)', help='Size of shredded particles for compliance')
    unit_of_measure = fields.Selection([
        ('lbs', 'Pounds'),
        ('kg', 'Kilograms'),
        ('boxes', 'Boxes'),
        ('items', 'Items')
    
    # Verification and quality control
    destruction_efficiency = fields.Float('Destruction Efficiency (%)', compute='_compute_destruction_metrics', store=True)
    photo_id_verified = fields.Boolean('Photo ID Verified', default=False, tracking=True)
    quality_control_passed = fields.Boolean('Quality Control Passed', default=False, tracking=True)
    signature_required = fields.Boolean('Signature Required', default=True)
    signature_verified = fields.Boolean('Signature Verified', default=False, tracking=True)
    third_party_verified = fields.Boolean('Third Party Verified', default=False, tracking=True)
    verification_date = fields.Date('Verification Date', tracking=True)
    verified = fields.Boolean('Verified', default=False, tracking=True)
    verified_at_facility_date = fields.Date('Verified at Facility Date')
    verified_before_destruction = fields.Boolean('Verified Before Destruction', default=False, tracking=True)
    verified_by_customer = fields.Boolean('Verified by Customer', default=False, tracking=True)
    
    # Documentation and media
    destruction_photographed = fields.Boolean('Destruction Photographed', default=False, tracking=True)
    destruction_notes = fields.Text('Destruction Notes')
    video_recorded = fields.Boolean('Video Recorded', default=False, tracking=True)
    
    # Scanning and tracking
    scanned_at_customer = fields.Boolean('Scanned at Customer Site', default=False, tracking=True)
    scanned_at_customer_date = fields.Date('Scanned at Customer Date')
    
    # Business and NAID compliance
    company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
        ('top_secret', 'Top Secret')
    destroyed = fields.Boolean('Destroyed', default=False, tracking=True)
    item_type = fields.Selection([
        ('documents', 'Documents'),
        ('hard_drives', 'Hard Drives'),
        ('optical_media', 'Optical Media'),
        ('uniforms', 'Uniforms'),
        ('mixed', 'Mixed Materials')
    naid_member_id = fields.Many2one('res.partner', string='NAID Member Company')
    shredding_equipment = fields.Char('Shredding Equipment Used')
    
    # One2many relationships
    destruction_item_ids = fields.Many2many('destruction.item', relation='destruction_item_ids_rel', string='Destruction Items')  # Fixed: was One2many with missing inverse field
    witness_verification_ids = fields.Many2many('witness.verification', relation='witness_verification_ids_rel', string='Witness Verifications')  # Fixed: was One2many with missing inverse field
    
    # Compute methods for new fields
    @api.depends('destruction_item_ids')
    def _compute_certificate_metrics(self):
        """Compute certificate-related metrics"""
        for record in self:
            # Count certificates generated for this service
            record.certificate_count = len(record.destruction_item_ids.filtered('certificate_generated'))
    
    @api.depends('pre_destruction_weight', 'post_destruction_weight')
    def _compute_destruction_metrics(self):
        """Compute destruction efficiency and metrics"""
        for record in self:
            if record.pre_destruction_weight > 0:
                weight_reduction = record.pre_destruction_weight - record.post_destruction_weight
                record.destruction_efficiency = (weight_reduction / record.pre_destruction_weight) * 100
            else:
                record.destruction_efficiency = 0.0