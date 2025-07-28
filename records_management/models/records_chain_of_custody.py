# -*- coding: utf-8 -*-
"""
Records Chain of Custody Management - Enterprise Grade NAID AAA Compliant
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class RecordsChainOfCustody(models.Model):
    """
    Comprehensive Chain of Custody Management with NAID AAA Compliance
    Tracks complete custody history for documents, boxes, and destruction processes
    """

    _name = "records.chain.of.custody.log"
    _description = "Records Chain of Custody Management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "transfer_date desc, name"
    _rec_name = "name"

    # ==========================================
    # CORE IDENTIFICATION FIELDS
    # ==========================================
    name = fields.Char(string="Custody Reference", required=True, tracking=True,
                      default=lambda self: _('New'), copy=False)
    description = fields.Text(string="Custody Description", tracking=True)
    company_id = fields.Many2one('res.company', string='Company',
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Custody Manager',
                             default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True, tracking=True)

    # ==========================================
    # CUSTODY RELATIONSHIPS
    # ==========================================
    movement_id = fields.Many2one('records.box.movement', string='Related Movement',
                                 tracking=True, ondelete='cascade')
    box_id = fields.Many2one('records.box', string='Records Box',
                            tracking=True, ondelete='cascade')
    document_id = fields.Many2one('records.document', string='Document',
                                 tracking=True, ondelete='cascade')
    shredding_service_id = fields.Many2one('shred.svc', string='Shredding Service',
                                          tracking=True, ondelete='cascade')
    work_order_id = fields.Many2one('doc.ret.wo', string='Document Retrieval Work Order',
                                   tracking=True, ondelete='cascade',
                                   help='Related document retrieval work order')

    # ==========================================
    # CUSTODY PARTIES
    # ==========================================
    from_party_id = fields.Many2one('res.partner', string='From Party',
                                   tracking=True, help='Party transferring custody')
    to_party_id = fields.Many2one('res.partner', string='To Party',
                                 tracking=True, help='Party receiving custody')
    custodian_id = fields.Many2one('res.users', string='Current Custodian',
                                  tracking=True, help='Current responsible party')

    # ==========================================
    # TRANSFER DETAILS
    # ==========================================
    transfer_date = fields.Datetime(string='Transfer Date', required=True,
                                   default=fields.Datetime.now, tracking=True)
    expected_return_date = fields.Datetime(string='Expected Return Date', tracking=True)
    actual_return_date = fields.Datetime(string='Actual Return Date', tracking=True)

    custody_event = fields.Selection([
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
        ('transfer', 'Transfer'),
        ('return', 'Return'),
        ('destruction', 'Destruction'),
        ('retrieval_start', 'Retrieval Started'),
        ('retrieval_complete', 'Retrieval Complete'),
        ('storage', 'Storage'),
        ('inspection', 'Inspection')
    ], string='Custody Event', required=True, tracking=True)

    # ==========================================
    # LOCATION INFORMATION
    # ==========================================
    location_from = fields.Char(string='From Location', tracking=True)
    location_to = fields.Char(string='To Location', tracking=True)
    from_location_id = fields.Many2one('records.location', string='From Records Location')
    to_location_id = fields.Many2one('records.location', string='To Records Location')

    # ==========================================
    # VERIFICATION AND SECURITY
    # ==========================================
    verified = fields.Boolean(string='Verified', default=False, tracking=True)
    verification_date = fields.Datetime(string='Verification Date', tracking=True)
    verification_code = fields.Char(string='Verification Code', tracking=True)
    verified_by_customer = fields.Boolean(string='Verified by Customer', tracking=True)

    signature_required = fields.Boolean(string='Signature Required', default=True)
    signature_obtained = fields.Boolean(string='Signature Obtained', tracking=True)
    photo_id_verified = fields.Boolean(string='Photo ID Verified', tracking=True)

    # ==========================================
    # NAID AAA COMPLIANCE
    # ==========================================
    naid_compliant = fields.Boolean(string='NAID AAA Compliant', default=True, tracking=True)
    chain_intact = fields.Boolean(string='Chain of Custody Intact', default=True, tracking=True)
    
    witness_name = fields.Char(string='Witness Name')
    witness_title = fields.Char(string='Witness Title')
    witness_signature = fields.Binary(string='Witness Signature')

    # ==========================================
    # DOCUMENTATION
    # ==========================================
    notes = fields.Text(string='Transfer Notes', tracking=True)
    special_instructions = fields.Text(string='Special Instructions')
    
    photo_before = fields.Binary(string='Photo Before Transfer')
    photo_after = fields.Binary(string='Photo After Transfer')
    transfer_receipt = fields.Binary(string='Transfer Receipt')

    # ==========================================
    # ADDITIONAL TRACKING FIELDS
    # ==========================================
    customer_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    key = fields.Char(string='Key', tracking=True)
    priority = fields.Char(string='Priority', tracking=True)
    request_type = fields.Char(string='Request Type', tracking=True)
    state = fields.Char(string='State', tracking=True)
    value = fields.Char(string='Value', tracking=True)

    # ==========================================
    # AUDIT TRAIL
    # ==========================================
    sequence_number = fields.Integer(string='Sequence Number', readonly=True)
    audit_hash = fields.Char(string='Audit Hash', readonly=True)
    previous_log_id = fields.Many2one('records.chain.of.custody.log', 
                                     string='Previous Log Entry')

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    
    @api.depends('transfer_date', 'actual_return_date')
    def _compute_custody_duration(self):
        """Calculate custody duration"""
        for record in self:
            if record.transfer_date and record.actual_return_date:
                delta = record.actual_return_date - record.transfer_date
                record.custody_duration = delta.total_seconds() / 3600.0  # hours
            else:
                record.custody_duration = 0.0

    custody_duration = fields.Float(string='Custody Duration (Hours)', 
                                   compute='_compute_custody_duration', store=True)

    @api.depends('verified', 'signature_obtained', 'naid_compliant')
    def _compute_compliance_status(self):
        """Compute overall compliance status"""
        for record in self:
            if record.naid_compliant and record.verified:
                if record.signature_required:
                    record.compliance_status = 'compliant' if record.signature_obtained else 'non_compliant'
                else:
                    record.compliance_status = 'compliant'
            else:
                record.compliance_status = 'non_compliant'

    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('pending', 'Pending Verification')
    ], string='Compliance Status', compute='_compute_compliance_status', store=True)

    # ==========================================
    # CRUD METHODS
    # ==========================================
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence and audit trail"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('chain.of.custody') or _('New')
            
            # Set sequence number
            last_log = self.search([], order='sequence_number desc', limit=1)
            vals['sequence_number'] = (last_log.sequence_number or 0) + 1
            
        records = super().create(vals_list)
        
        # Generate audit hash
        for record in records:
            record._generate_audit_hash()
            
        return records

    def _generate_audit_hash(self):
        """Generate audit hash for chain integrity"""
        import hashlib
        hash_string = f"{self.id}-{self.transfer_date}-{self.custody_event}-{self.sequence_number}"
        self.audit_hash = hashlib.md5(hash_string.encode()).hexdigest()

    # ==========================================
    # WORKFLOW ACTIONS
    # ==========================================
    
    def action_verify_custody(self):
        """Verify custody transfer"""
        self.ensure_one()
        
        if self.verified:
            raise UserError(_('Custody transfer already verified'))
        
        self.write({
            'verified': True,
            'verification_date': fields.Datetime.now(),
            'verification_code': self._generate_verification_code()
        })
        
        self.message_post(body=_('Custody transfer verified'))

    def _generate_verification_code(self):
        """Generate unique verification code"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def action_complete_transfer(self):
        """Complete the custody transfer"""
        self.ensure_one()
        
        if not self.verified:
            raise UserError(_('Transfer must be verified first'))
        
        if self.custody_event in ['pickup', 'transfer']:
            # Update custodian
            if self.to_party_id:
                # Find user associated with partner
                user = self.env['res.users'].search([('partner_id', '=', self.to_party_id.id)], limit=1)
                if user:
                    self.custodian_id = user.id

        self.message_post(body=_('Custody transfer completed'))

    # ==========================================
    # WORK ORDER INTEGRATION METHODS
    # ==========================================
    
    @api.model
    def create_work_order_custody_log(self, work_order_id, custody_event, from_party=None, to_party=None, notes=None):
        """Create custody log entry for document retrieval work order"""
        work_order = self.env['doc.ret.wo'].browse(work_order_id)
        
        vals = {
            'work_order_id': work_order_id,
            'custody_event': custody_event,
            'from_party_id': from_party.id if from_party else False,
            'to_party_id': to_party.id if to_party else False,
            'transfer_date': fields.Datetime.now(),
            'location_from': work_order.customer_id.name if custody_event == 'pickup' else 'Records Center',
            'location_to': 'Records Center' if custody_event == 'pickup' else work_order.delivery_address,
            'custodian_id': self.env.user.id,
            'notes': notes or f'Custody event for work order {work_order.name}',
            'verified': True,
            'verification_date': fields.Datetime.now(),
            'naid_compliant': True,
        }
        
        return self.create(vals)
    
    def action_verify_work_order_custody(self):
        """Verify custody for work order related transfers"""
        self.ensure_one()
        if not self.work_order_id:
            raise UserError(_('This custody log is not related to a work order'))
        
        self.write({
            'verified': True,
            'verification_date': fields.Datetime.now(),
            'verified_by_customer': True,
        })
        
        # Update work order status if needed
        if self.custody_event == 'delivery':
            self.work_order_id.action_deliver()
        
        self.message_post(body=_('Work order custody verified'))
        
        return True

    # ==========================================
    # REPORTING METHODS
    # ==========================================
    
    def get_custody_timeline(self):
        """Get custody timeline for related items"""
        self.ensure_one()
        
        domain = []
        if self.box_id:
            domain = [('box_id', '=', self.box_id.id)]
        elif self.document_id:
            domain = [('document_id', '=', self.document_id.id)]
        elif self.work_order_id:
            domain = [('work_order_id', '=', self.work_order_id.id)]
        
        timeline = self.search(domain, order='transfer_date asc')
        
        return [{
            'date': log.transfer_date,
            'event': log.custody_event,
            'from_party': log.from_party_id.name if log.from_party_id else 'N/A',
            'to_party': log.to_party_id.name if log.to_party_id else 'N/A',
            'location': f"{log.location_from} → {log.location_to}",
            'verified': log.verified,
            'notes': log.notes or ''
        } for log in timeline]

    # ==========================================
    # VALIDATION
    # ==========================================
    
    @api.constrains('transfer_date', 'expected_return_date', 'actual_return_date')
    def _check_custody_dates(self):
        """Validate custody dates"""
        for record in self:
            if record.expected_return_date and record.transfer_date:
                if record.expected_return_date <= record.transfer_date:
                    raise ValidationError(_('Expected return date must be after transfer date'))
            
            if record.actual_return_date and record.transfer_date:
                if record.actual_return_date < record.transfer_date:
                    raise ValidationError(_('Return date cannot be before transfer date'))

    @api.constrains('box_id', 'document_id', 'work_order_id')
    def _check_custody_item(self):
        """Ensure at least one item is specified"""
        for record in self:
            if not any([record.box_id, record.document_id, record.work_order_id]):
                raise ValidationError(_('At least one item (box, document, or work order) must be specified for custody'))

    @api.constrains('from_location_id', 'to_location_id')
    def _check_locations(self):
        """Validate location transfer"""
        for record in self:
            if record.from_location_id and record.to_location_id:
                if record.from_location_id == record.to_location_id:
                    raise ValidationError(_('From and To locations must be different'))

    # ==========================================
    # NAID COMPLIANCE METHODS
    # ==========================================
    
    def validate_naid_compliance(self):
        """Validate NAID AAA compliance requirements"""
        self.ensure_one()
        if not self.naid_compliant:
            return True

        compliance_issues = []
        
        if self.signature_required and not self.signature_obtained:
            compliance_issues.append('Missing required signature')
        
        if not self.photo_id_verified:
            compliance_issues.append('Photo ID not verified')
        
        if not self.verification_code:
            compliance_issues.append('Missing verification code')
        
        if not self.chain_intact:
            compliance_issues.append('Chain of custody integrity compromised')

        if compliance_issues:
            raise ValidationError(_('NAID compliance issues: %s') % ', '.join(compliance_issues))
        
        return True
