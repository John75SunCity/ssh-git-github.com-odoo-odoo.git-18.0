# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class VisitorPosWizard(models.TransientModel):
    """Wizard to Link POS Transaction to Visitor"""
    _name = 'visitor.pos.wizard'
    _description = 'Wizard to Link POS Transaction to Visitor'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    visitor_id = fields.Many2one('records.visitor', string='Visitor', required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    pos_order_id = fields.Many2one('pos.order', string='POS Transaction', domain="[('partner_id', '=', partner_id)]")
    
    service_type = fields.Selection([
        ('document_shred', 'Document Shredding'),
        ('hard_drive', 'Hard Drive Destruction'),
        ('uniform_shred', 'Uniform Shredding'),
    ], string='Service Type', required=True)
    
    notes = fields.Text(string='Additional Notes')

    # Customer Information
    name = fields.Char(string='Service Name', required=True, default='Walk-in Service')
    visitor_name = fields.Char(string='Visitor Name', related='visitor_id.name', readonly=True)
    visitor_email = fields.Char(string='Visitor Email', related='visitor_id.email', readonly=True)
    visitor_phone = fields.Char(string='Visitor Phone', related='visitor_id.phone', readonly=True)
    
    create_new_customer = fields.Boolean(string='Create New Customer', default=False)
    existing_customer_id = fields.Many2one('res.partner', string='Existing Customer')
    customer_record_created = fields.Boolean(string='Customer Record Created', readonly=True)
    customer_record_id = fields.Many2one('res.partner', string='Created Customer Record', readonly=True)
    
    customer_category = fields.Selection([
        ('new', 'New Customer'),
        ('existing', 'Existing Customer'),
        ('corporate', 'Corporate'),
        ('individual', 'Individual'),
    ], string='Customer Category', default='new')

    # Financial Configuration
    customer_credit_limit = fields.Float(string='Customer Credit Limit', default=0.0)
    customer_payment_terms = fields.Many2one('account.payment.term', string='Customer Payment Terms')
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method')
    payment_reference = fields.Char(string='Payment Reference')
    
    # Service Processing
    customer_processing_time = fields.Float(string='Customer Processing Time (minutes)')
    estimated_service_time = fields.Float(string='Estimated Service Time (minutes)')
    total_processing_time = fields.Float(string='Total Processing Time (minutes)', compute='_compute_total_processing_time')
    estimated_volume = fields.Float(string='Estimated Volume (cubic ft)')
    
    processing_priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Processing Priority', default='normal')

    # Service Location and Setup
    service_location = fields.Many2one('stock.location', string='Service Location')
    express_service = fields.Boolean(string='Express Service', default=False)
    pickup_required = fields.Boolean(string='Pickup Required', default=False)
    scanning_required = fields.Boolean(string='Scanning Required', default=False)
    special_requirements = fields.Text(string='Special Requirements')
    
    # Document Configuration
    document_type = fields.Selection([
        ('confidential', 'Confidential'),
        ('public', 'Public'),
        ('medical', 'Medical'),
        ('financial', 'Financial'),
        ('legal', 'Legal'),
    ], string='Document Type', default='confidential')
    
    document_count = fields.Integer(string='Document Count', default=1)
    required_document_ids = fields.Many2many('ir.attachment', string='Required Documents')
    
    # Digital Services
    digitization_format = fields.Selection([
        ('pdf', 'PDF'),
        ('tiff', 'TIFF'),
        ('jpeg', 'JPEG'),
        ('png', 'PNG'),
    ], string='Digitization Format', default='pdf')
    
    # Destruction and Security
    destruction_method = fields.Selection([
        ('shred', 'Shredding'),
        ('incineration', 'Incineration'),
        ('pulping', 'Pulping'),
        ('disintegration', 'Disintegration'),
    ], string='Destruction Method', default='shred')
    
    shredding_type = fields.Selection([
        ('strip_cut', 'Strip Cut'),
        ('cross_cut', 'Cross Cut'),
        ('micro_cut', 'Micro Cut'),
    ], string='Shredding Type', default='cross_cut')
    
    witness_required = fields.Boolean(string='Witness Required', default=False)
    witness_verification = fields.Boolean(string='Witness Verification', readonly=True)
    
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('top_secret', 'Top Secret'),
    ], string='Confidentiality Level', default='confidential')

    # Chain of Custody and Compliance
    chain_of_custody = fields.Boolean(string='Chain of Custody Required', default=True)
    chain_of_custody_id = fields.Many2one('records.chain.of.custody', string='Chain of Custody Record')
    certificate_required = fields.Boolean(string='Certificate Required', default=True)
    compliance_documentation = fields.Text(string='Compliance Documentation')
    
    # NAID Compliance
    naid_compliance = fields.Boolean(string='NAID Compliance Required', default=False)
    naid_certificate_level = fields.Selection([
        ('aaa', 'AAA Certification'),
        ('aa', 'AA Certification'),
        ('a', 'A Certification'),
    ], string='NAID Certificate Level')
    
    # Quality Control and Audit
    audit_required = fields.Boolean(string='Audit Required', default=False)
    audit_level = fields.Selection([
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('comprehensive', 'Comprehensive'),
    ], string='Audit Level', default='standard')
    
    audit_notes = fields.Text(string='Audit Notes')
    quality_check_by = fields.Many2one('res.users', string='Quality Check By')
    final_verification_by = fields.Many2one('res.users', string='Final Verification By')

    # Status fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')

    @api.depends('customer_processing_time', 'estimated_service_time')
    def _compute_total_processing_time(self):
        """Compute total processing time"""
        for record in self:
            record.total_processing_time = record.customer_processing_time + record.estimated_service_time

    def action_link_pos_transaction(self):
        """Link the POS transaction to the visitor"""
        self.ensure_one()
        
        if not self.pos_order_id:
    pass
            raise UserError(_('Please select a POS transaction.'))
        
        # Update visitor with POS information
        self.visitor_id.write({
            'pos_order_id': self.pos_order_id.id,
            'service_type': self.service_type,
            'notes': self.notes,
        })
        
        # Create message on visitor
        self.visitor_id.message_post(
            body=_('POS transaction %s linked to visitor.') % self.pos_order_id.name
        )
        
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        """Cancel the wizard"""
        return {'type': 'ir.actions.act_window_close'}
