# -*- coding: utf-8 -*-
"""
Bin Unlock Service Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class BinUnlockService(models.Model):
    """
    Bin Unlock Service Request
    Service for unlocking customer bins with approval workflow
    """
    
    _name = 'bin.unlock.service'
    _description = 'Bin Unlock Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'
    
    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Service Reference', required=True, tracking=True,
                      default=lambda self: _('New'), copy=False)
    description = fields.Text(string='Service Description', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Service Manager', 
                             default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    
    # ==========================================
    # CUSTOMER AND BILLING
    # ==========================================
    customer_id = fields.Many2one('res.partner', string='Customer', 
                                 required=True, tracking=True,
                                 domain=[('is_company', '=', True)])
    department_id = fields.Many2one('records.department', string='Department', tracking=True)
    billing_contact_id = fields.Many2one('res.partner', string='Billing Contact', tracking=True)
    
    # ==========================================
    # BIN INFORMATION
    # ==========================================
    bin_identifier = fields.Char(string='Bin Identifier', required=True, tracking=True,
                                 help='Bin number or identifier to unlock')
    bin_location = fields.Char(string='Bin Location', tracking=True)
    lock_type = fields.Selection([
        ('physical', 'Physical Lock'),
        ('electronic', 'Electronic Lock'),
        ('security_tape', 'Security Tape'),
        ('combination', 'Combination Lock'),
        ('key_lock', 'Key Lock')
    ], string='Lock Type', default='physical', tracking=True)
    
    # ==========================================
    # SERVICE DETAILS
    # ==========================================
    service_date = fields.Datetime(string='Requested Service Date', 
                                   default=fields.Datetime.now, required=True, tracking=True)
    scheduled_date = fields.Datetime(string='Scheduled Date', tracking=True)
    completed_date = fields.Datetime(string='Completed Date', tracking=True)
    
    urgency = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('emergency', 'Emergency')
    ], string='Urgency', default='normal', tracking=True)
    
    reason = fields.Text(string='Unlock Reason', required=True, tracking=True)
    
    # Key restriction fields
    unlock_reason_code = fields.Selection([
        ('lost_key', 'Lost Key'),
        ('broken_key', 'Broken Key'),
        ('emergency', 'Emergency Access'),
        ('maintenance', 'Maintenance Required'),
        ('inspection', 'Inspection Required'),
        ('key_restriction', 'Customer Key Restriction'),
        ('other', 'Other')
    ], string='Unlock Reason Code', required=True, tracking=True, default='other')
    
    customer_key_restricted = fields.Boolean(
        string='Customer Key Restricted', 
        related='customer_id.key_issuance_allowed',
        readonly=True,
        help='Indicates if this customer is restricted from receiving keys'
    )
    
    key_restriction_reason = fields.Selection(
        related='customer_id.key_restriction_reason',
        readonly=True,
        string='Key Restriction Reason'
    )
    
    special_instructions = fields.Text(string='Special Instructions')
    
    # ==========================================
    # APPROVAL WORKFLOW
    # ==========================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('invoiced', 'Invoiced'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)
    
    approval_required = fields.Boolean(string='Approval Required', default=True)
    approved_by_id = fields.Many2one('res.users', string='Approved By', tracking=True)
    approval_date = fields.Datetime(string='Approval Date', tracking=True)
    approval_notes = fields.Text(string='Approval Notes')
    
    rejected_by_id = fields.Many2one('res.users', string='Rejected By', tracking=True)
    rejection_date = fields.Datetime(string='Rejection Date', tracking=True)
    rejection_reason = fields.Text(string='Rejection Reason')
    
    # ==========================================
    # SERVICE EXECUTION
    # ==========================================
    technician_id = fields.Many2one('res.users', string='Assigned Technician', tracking=True)
    service_start_time = fields.Datetime(string='Service Start Time')
    service_end_time = fields.Datetime(string='Service End Time')
    service_duration = fields.Float(string='Service Duration (Hours)', compute='_compute_service_duration')
    
    tools_required = fields.Text(string='Tools Required')
    safety_notes = fields.Text(string='Safety Notes')
    completion_notes = fields.Text(string='Completion Notes')
    
    # ==========================================
    # BILLING INFORMATION
    # ==========================================
    billable = fields.Boolean(string='Billable Service', default=True)
    service_rate = fields.Float(string='Service Rate', default=25.00, tracking=True)
    quantity = fields.Float(string='Quantity', default=1.0, tracking=True)
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    invoice_line_id = fields.Many2one('account.move.line', string='Invoice Line', readonly=True)
    invoiced = fields.Boolean(string='Invoiced', compute='_compute_invoiced', store=True)
    
    # ==========================================
    # DOCUMENTATION
    # ==========================================
    photo_before = fields.Binary(string='Photo Before Service')
    photo_after = fields.Binary(string='Photo After Service')
    signature_customer = fields.Binary(string='Customer Signature')
    signature_technician = fields.Binary(string='Technician Signature')
    
    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends('service_start_time', 'service_end_time')
    def _compute_service_duration(self):
        """Calculate service duration"""
        for record in self:
            if record.service_start_time and record.service_end_time:
                delta = record.service_end_time - record.service_start_time
                record.service_duration = delta.total_seconds() / 3600.0
            else:
                record.service_duration = 0.0
    
    @api.depends('service_rate', 'quantity')
    def _compute_total_amount(self):
        """Calculate total amount"""
        for record in self:
            record.total_amount = record.service_rate * record.quantity
    
    @api.depends('invoice_id', 'invoice_line_id')
    def _compute_invoiced(self):
        """Check if service is invoiced"""
        for record in self:
            record.invoiced = bool(record.invoice_id and record.invoice_line_id)
    
    # ==========================================
    # CRUD METHODS
    # ==========================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence number"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('bin.unlock.service') or _('New')
        return super().create(vals_list)
    
    # ==========================================
    # WORKFLOW ACTIONS
    # ==========================================
    def action_submit(self):
        """Submit service request for approval"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft requests can be submitted'))
        
        self.write({'state': 'submitted'})
        self.message_post(body=_('Service request submitted for approval'))
    
    def action_approve(self):
        """Approve service request"""
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_('Only submitted requests can be approved'))
        
        self.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now()
        })
        self.message_post(body=_('Service request approved by %s') % self.env.user.name)
    
    def action_reject(self):
        """Reject service request"""
        self.ensure_one()
        if self.state not in ['submitted', 'approved']:
            raise UserError(_('Only submitted or approved requests can be rejected'))
        
        self.write({
            'state': 'rejected',
            'rejected_by_id': self.env.user.id,
            'rejection_date': fields.Datetime.now()
        })
        self.message_post(body=_('Service request rejected by %s') % self.env.user.name)
    
    def action_schedule(self):
        """Schedule service"""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Only approved requests can be scheduled'))
        
        self.write({'state': 'scheduled'})
        self.message_post(body=_('Service scheduled for %s') % self.scheduled_date)
    
    def action_start_service(self):
        """Start service execution"""
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_('Only scheduled services can be started'))
        
        self.write({
            'state': 'in_progress',
            'service_start_time': fields.Datetime.now()
        })
        self.message_post(body=_('Service started by %s') % self.env.user.name)
    
    def action_complete_service(self):
        """Complete service"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_('Only services in progress can be completed'))
        
        self.write({
            'state': 'completed',
            'service_end_time': fields.Datetime.now(),
            'completed_date': fields.Datetime.now()
        })
        self.message_post(body=_('Service completed'))
    
    def action_create_invoice(self):
        """Create invoice for the service"""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_('Only completed services can be invoiced'))
        
        if not self.billable:
            raise UserError(_('This service is not billable'))
        
        if self.invoiced:
            raise UserError(_('Service already invoiced'))
        
        # Create invoice
        invoice_vals = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': f'Bin Unlock Service - {self.bin_identifier}',
                'quantity': self.quantity,
                'price_unit': self.service_rate,
                'account_id': self.env['account.account'].search([
                    ('account_type', '=', 'income')
                ], limit=1).id,
            })]
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        self.write({
            'state': 'invoiced',
            'invoice_id': invoice.id,
            'invoice_line_id': invoice.invoice_line_ids[0].id
        })
        
        self.message_post(body=_('Invoice created: %s') % invoice.name)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_cancel(self):
        """Cancel service request"""
        self.ensure_one()
        if self.state in ['completed', 'invoiced']:
            raise UserError(_('Cannot cancel completed or invoiced services'))
        
        self.write({'state': 'cancelled'})
        self.message_post(body=_('Service cancelled'))
    
    # ==========================================
    # KEY RESTRICTION LOGIC
    # ==========================================
    
    @api.onchange('customer_id')
    def _onchange_customer_key_restriction(self):
        """Auto-set unlock reason when customer is key restricted"""
        if self.customer_id and not self.customer_id.key_issuance_allowed:
            self.unlock_reason_code = 'key_restriction'
            self.reason = _('Customer is restricted from receiving keys. Service required for bin access.')
    
    @api.constrains('customer_id', 'unlock_reason_code')
    def _check_key_restriction_consistency(self):
        """Ensure unlock reason is consistent with customer key restrictions"""
        for record in self:
            if record.customer_id and not record.customer_id.key_issuance_allowed:
                if record.unlock_reason_code != 'key_restriction':
                    # Auto-correct the reason
                    record.unlock_reason_code = 'key_restriction'
                    if not record.reason or 'key' not in record.reason.lower():
                        record.reason = _('Customer is restricted from receiving keys. Service required for bin access.')
    
    def get_key_restriction_info(self):
        """Get key restriction information for this service"""
        self.ensure_one()
        
        if not self.customer_id:
            return {'restricted': False}
        
        restriction_info = self.customer_id.get_key_restriction_summary()
        restriction_info['service_required'] = not self.customer_id.key_issuance_allowed
        
        return restriction_info
    
    @api.model
    def create_for_key_restricted_customer(self, customer_id, bin_identifier, reason=None):
        """Helper method to create unlock service for key-restricted customers"""
        customer = self.env['res.partner'].browse(customer_id)
        
        if customer.key_issuance_allowed:
            raise UserError(_('Customer "%s" is not restricted from receiving keys') % customer.name)
        
        vals = {
            'customer_id': customer_id,
            'bin_identifier': bin_identifier,
            'unlock_reason_code': 'key_restriction',
            'reason': reason or _('Customer is restricted from receiving keys. Service required for bin access.'),
            'urgency': 'normal',
            'approval_required': True,
        }
        
        return self.create(vals)
    
    # ==========================================
    # VALIDATION
    # ==========================================
    @api.constrains('service_rate', 'quantity')
    def _check_billing_amounts(self):
        """Validate billing amounts"""
        for record in self:
            if record.billable:
                if record.service_rate < 0:
                    raise ValidationError(_('Service rate cannot be negative'))
                if record.quantity <= 0:
                    raise ValidationError(_('Quantity must be positive'))
    
    @api.constrains('service_start_time', 'service_end_time')
    def _check_service_times(self):
        """Validate service times"""
        for record in self:
            if record.service_start_time and record.service_end_time:
                if record.service_end_time <= record.service_start_time:
                    raise ValidationError(_('Service end time must be after start time'))

    @api.depends('service_rate', 'service_duration')
    def _compute_total_cost(self):
        """Calculate total service cost"""
        for record in self:
            record.total_cost = (record.service_rate or 0.0) * (record.service_duration or 0.0)
