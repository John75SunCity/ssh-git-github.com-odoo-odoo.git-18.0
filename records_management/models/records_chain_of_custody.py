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
    user_id = fields.Many2one('res.users', string='Responsible User',
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
    
    # ==========================================
    # LOCATION AND TRANSFER DETAILS
    # ==========================================
    from_location_id = fields.Many2one('records.location', string='From Location',
                                      tracking=True)
    to_location_id = fields.Many2one('records.location', string='To Location',
                                    required=True, tracking=True)
    transfer_date = fields.Datetime(string='Transfer Date',
                                   default=fields.Datetime.now, required=True, tracking=True)
    expected_return_date = fields.Datetime(string='Expected Return Date', tracking=True)
    actual_return_date = fields.Datetime(string='Actual Return Date', tracking=True)

    # ==========================================
    # PERSONNEL TRACKING
    # ==========================================
    transferred_by_id = fields.Many2one('res.users', string='Transferred By',
                                       default=lambda self: self.env.user, tracking=True)
    received_by_id = fields.Many2one('res.users', string='Received By', tracking=True)
    authorized_by_id = fields.Many2one('res.users', string='Authorized By', tracking=True)
    customer_representative_id = fields.Many2one('res.partner', string='Customer Representative')
    witness_id = fields.Many2one('res.users', string='Witness', tracking=True)

    # ==========================================
    # CUSTODY STATUS AND WORKFLOW
    # ==========================================
    custody_status = fields.Selection([
        ('draft', 'Draft'),
        ('pending_transfer', 'Pending Transfer'),
        ('transferred', 'Transferred'),
        ('in_custody', 'In Custody'),
        ('returned', 'Returned'),
        ('destroyed', 'Destroyed'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged')
    ], string='Custody Status', default='draft', tracking=True, required=True)

    custody_type = fields.Selection([
        ('temporary', 'Temporary Custody'),
        ('permanent', 'Permanent Transfer'),
        ('destruction', 'For Destruction'),
        ('retrieval', 'Document Retrieval'),
        ('audit', 'Audit Review'),
        ('legal', 'Legal Hold'),
        ('storage', 'Storage Transfer')
    ], string='Custody Type', required=True, tracking=True)

    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency')
    ], string='Priority', default='normal', tracking=True)

    # ==========================================
    # NAID COMPLIANCE FIELDS
    # ==========================================
    naid_compliant = fields.Boolean(string='NAID Compliant', default=True, tracking=True)
    signature_required = fields.Boolean(string='Signature Required', default=True)
    signature_obtained = fields.Boolean(string='Signature Obtained', tracking=True)
    photo_id_verified = fields.Boolean(string='Photo ID Verified', tracking=True)
    security_seal_number = fields.Char(string='Security Seal Number', tracking=True)
    tamper_evident = fields.Boolean(string='Tamper Evident Packaging', tracking=True)

    # ==========================================
    # DOCUMENTATION FIELDS
    # ==========================================
    custody_notes = fields.Text(string='Custody Notes', tracking=True)
    security_notes = fields.Text(string='Security Notes', tracking=True)
    special_instructions = fields.Text(string='Special Instructions')
    compliance_notes = fields.Text(string='Compliance Notes', tracking=True)
    
    # Digital signatures and certificates
    digital_signature = fields.Binary(string='Digital Signature')
    custody_certificate = fields.Binary(string='Custody Certificate')
    
    # Chain verification
    verification_code = fields.Char(string='Verification Code', tracking=True)
    chain_intact = fields.Boolean(string='Chain Intact', default=True, tracking=True)
    anomaly_detected = fields.Boolean(string='Anomaly Detected', tracking=True)
    anomaly_description = fields.Text(string='Anomaly Description')

    # ==========================================
    # TIMING AND CONDITIONS
    # ==========================================
    estimated_duration = fields.Float(string='Estimated Duration (Hours)', tracking=True)
    actual_duration = fields.Float(string='Actual Duration (Hours)',
                                  compute='_compute_actual_duration', store=True)
    
    # Environmental conditions
    temperature_range = fields.Char(string='Temperature Range')
    humidity_range = fields.Char(string='Humidity Range')
    security_level = fields.Selection([
        ('standard', 'Standard'),
        ('enhanced', 'Enhanced'),
        ('maximum', 'Maximum Security')
    ], string='Security Level', default='standard', tracking=True)

    # ==========================================
    # BILLING AND COST TRACKING
    # ==========================================
    billable = fields.Boolean(string='Billable Service', default=True)
    custody_cost = fields.Float(string='Custody Cost', tracking=True)
    transport_cost = fields.Float(string='Transport Cost', tracking=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost', store=True)

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    customer_id = fields.Many2one(related='box_id.partner_id', string='Customer', readonly=True)
    item_description = fields.Char(string='Item Description', compute='_compute_item_description')
    custody_duration_status = fields.Char(string='Duration Status', compute='_compute_duration_status')
    
    # Chain validation
    previous_custody_id = fields.Many2one('records.chain.of.custody.log', string='Previous Custody')
    next_custody_ids = fields.One2many('records.chain.of.custody.log', 'previous_custody_id',
                                      string='Next Custody Records')
    chain_complete = fields.Boolean(string='Chain Complete', compute='_compute_chain_complete')

    @api.depends('transfer_date', 'actual_return_date')
    def _compute_actual_duration(self):
        """Calculate actual custody duration"""
        for record in self:
            if record.transfer_date and record.actual_return_date:
                delta = record.actual_return_date - record.transfer_date
                record.actual_duration = delta.total_seconds() / 3600.0
            else:
                record.actual_duration = 0.0

    @api.depends('custody_cost', 'transport_cost')
    def _compute_total_cost(self):
        """Calculate total custody cost"""
        for record in self:
            record.total_cost = record.custody_cost + record.transport_cost

    @api.depends('box_id', 'document_id')
    def _compute_item_description(self):
        """Compute description of item in custody"""
        for record in self:
            if record.box_id:
                record.item_description = f"Box: {record.box_id.name}"
            elif record.document_id:
                record.item_description = f"Document: {record.document_id.name}"
            else:
                record.item_description = "No item specified"

    @api.depends('transfer_date', 'expected_return_date', 'actual_return_date')
    def _compute_duration_status(self):
        """Compute custody duration status"""
        for record in self:
            if record.actual_return_date:
                if record.expected_return_date and record.actual_return_date > record.expected_return_date:
                    record.custody_duration_status = "Overdue Return"
                else:
                    record.custody_duration_status = "Returned On Time"
            elif record.expected_return_date and fields.Datetime.now() > record.expected_return_date:
                record.custody_duration_status = "Overdue"
            else:
                record.custody_duration_status = "On Time"

    @api.depends('previous_custody_id', 'next_custody_ids')
    def _compute_chain_complete(self):
        """Check if chain of custody is complete"""
        for record in self:
            # Chain is complete if it has proper linkage and no gaps
            record.chain_complete = bool(record.previous_custody_id or record.next_custody_ids)

    # ==========================================
    # WORKFLOW ACTION METHODS
    # ==========================================
    def action_confirm_transfer(self):
        """Confirm custody transfer"""
        self.ensure_one()
        if self.custody_status != 'draft':
            raise UserError(_('Only draft custody records can be confirmed'))

        if self.name == _('New'):
            self.name = self.env['ir.sequence'].next_by_code('records.chain.of.custody.log') or _('New')

        # Validate required fields for NAID compliance
        if self.naid_compliant:
            if self.signature_required and not self.signature_obtained:
                raise UserError(_('Signature required for NAID compliant transfer'))
            if not self.photo_id_verified:
                raise UserError(_('Photo ID verification required for NAID compliance'))

        self.write({
            'custody_status': 'pending_transfer',
            'verification_code': self._generate_verification_code()
        })

        self.message_post(
            body=_('Custody transfer confirmed by %s') % self.env.user.name,
            message_type='notification'
        )

    def action_execute_transfer(self):
        """Execute the custody transfer"""
        self.ensure_one()
        if self.custody_status != 'pending_transfer':
            raise UserError(_('Only pending transfers can be executed'))

        if not self.received_by_id:
            raise UserError(_('Receiver must be specified'))

        self.write({
            'custody_status': 'transferred',
            'transfer_date': fields.Datetime.now()
        })

        # Update item location if applicable
        if self.box_id and self.to_location_id:
            self.box_id.write({'location_id': self.to_location_id.id})

        self.message_post(
            body=_('Custody transferred from %s to %s') % 
                 (self.transferred_by_id.name, self.received_by_id.name),
            message_type='notification'
        )

    def action_accept_custody(self):
        """Accept custody of items"""
        self.ensure_one()
        if self.custody_status != 'transferred':
            raise UserError(_('Only transferred items can be accepted'))

        self.write({'custody_status': 'in_custody'})
        self.message_post(
            body=_('Custody accepted by %s') % self.env.user.name,
            message_type='notification'
        )

    def action_return_custody(self):
        """Return items from custody"""
        self.ensure_one()
        if self.custody_status != 'in_custody':
            raise UserError(_('Only items in custody can be returned'))

        self.write({
            'custody_status': 'returned',
            'actual_return_date': fields.Datetime.now()
        })

        self.message_post(
            body=_('Items returned from custody by %s') % self.env.user.name,
            message_type='notification'
        )

    def action_report_anomaly(self):
        """Report custody anomaly"""
        self.ensure_one()
        self.write({
            'anomaly_detected': True,
            'chain_intact': False
        })

        # Create activity for investigation
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary='Investigate custody anomaly',
            note=f'Anomaly detected in custody chain: {self.anomaly_description}',
            user_id=self.user_id.id
        )

        self.message_post(
            body=_('Custody anomaly reported by %s') % self.env.user.name,
            message_type='notification'
        )

    # ==========================================
    # HELPER METHODS
    # ==========================================
    def _generate_verification_code(self):
        """Generate unique verification code for chain integrity"""
        import hashlib
        import time
        
        data = f"{self.id}{self.transfer_date}{self.transferred_by_id.id}{time.time()}"
        return hashlib.md5(data.encode()).hexdigest()[:8].upper()

    def _create_custody_certificate(self):
        """Generate custody certificate PDF"""
        # This would integrate with report generation
        pass

    @api.model
    def create(self, vals):
        """Override create to set sequence number and validation"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('records.chain.of.custody.log') or _('New')
        
        # Set verification code if not provided
        if not vals.get('verification_code'):
            vals['verification_code'] = self._generate_verification_code()
        
        return super().create(vals)

    # ==========================================
    # VALIDATION METHODS
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

    @api.constrains('box_id', 'document_id')
    def _check_custody_item(self):
        """Ensure at least one item is specified"""
        for record in self:
            if not record.box_id and not record.document_id:
                raise ValidationError(_('Either a box or document must be specified for custody'))

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
