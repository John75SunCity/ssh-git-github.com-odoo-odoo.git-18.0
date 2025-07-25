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
    ], string='Service Type', required=True)  # Expanded for new services
    bin_ids = fields.Many2many(
        'stock.lot',
        relation='shredding_service_bin_rel',  # Custom relation to avoid conflict with shredded_box_ids
        column1='service_id',
        column2='lot_id',
        string='Serviced Bins',
        domain="[('product_id.name', '=', 'Shredding Bin')]"
    )
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
    timestamp = fields.Datetime(default=fields.Datetime.now, readonly=True)
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
    compliance_documentation_ids = fields.One2many('ir.attachment', 'res_id', string='Compliance Documentation', 
                                                   domain="[('res_model', '=', 'shredding.service')]", 
                                                   compute='_compute_compliance_docs')
    destruction_method_verified = fields.Boolean('Destruction Method Verified', default=False)
    destruction_method = fields.Selection([
        ('shred', 'Physical Shredding'),
        ('crush', 'Crushing'),
        ('degauss', 'Degaussing'),
        ('wipe', 'Data Wiping'),
        ('incineration', 'Incineration'),
        ('pulverization', 'Pulverization')
    ], string='Destruction Method')
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
    
    # Missing technical view fields