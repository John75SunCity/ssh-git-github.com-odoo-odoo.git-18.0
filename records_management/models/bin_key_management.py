# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class BinKeyManagement(models.Model):
    """Track bin key issuance and management for secure shredding bins"""
    _name = 'bin.key.management'
    _description = 'Bin Key Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc, id desc'
    _rec_name = 'key_number'

    # Core identification
    key_number = fields.Char(
        string='Key Number/ID',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('bin.key.management') or 'KEY-NEW',
        tracking=True,
        help="Unique identifier for the key (all keys are generic but tracked individually)"
    )
    
    # Key holder information
    partner_id = fields.Many2one(
        'res.partner',
        string='Key Holder',
        required=True,
        tracking=True,
        help="Contact who has been issued this key"
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Customer Company',
        related='partner_id.parent_id',
        store=True,
        help="The company this contact belongs to"
    )
    
    # Key status and tracking
    status = fields.Selection([
        ('issued', 'Issued'),
        ('returned', 'Returned'),
        ('lost', 'Lost/Missing'),
        ('replaced', 'Replaced'),
        ('deactivated', 'Deactivated'),
    ], string='Key Status', default='issued', required=True, tracking=True)
    
    # Issue information
    issue_date = fields.Date(
        string='Issue Date',
        default=fields.Date.today,
        required=True,
        tracking=True
    )
    
    issued_by_user_id = fields.Many2one(
        'res.users',
        string='Issued By',
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )
    
    issue_location = fields.Char(
        string='Issue Location',
        help="Where the key was issued (e.g., customer site, office)"
    )
    
    # Return information
    return_date = fields.Date(
        string='Return Date',
        tracking=True
    )
    
    returned_by_user_id = fields.Many2one(
        'res.users',
        string='Returned To',
        tracking=True
    )
    
    return_reason = fields.Text(
        string='Return Reason',
        help="Why the key was returned"
    )
    
    # Replacement tracking
    replaced_by_key_id = fields.Many2one(
        'bin.key.management',
        string='Replaced By Key',
        tracking=True,
        help="If this key was replaced, reference to the new key"
    )
    
    replaces_key_id = fields.Many2one(
        'bin.key.management',
        string='Replaces Key',
        tracking=True,
        help="If this key replaces another, reference to the old key"
    )
    
    # Service information
    bin_locations = fields.Text(
        string='Bin Locations',
        help="List of bin locations this key provides access to"
    )
    
    emergency_contact = fields.Boolean(
        string='Emergency Contact',
        default=False,
        help="This contact can be reached for emergency bin access"
    )
    
    # Unlock service tracking
    unlock_service_ids = fields.One2many(
        'bin.unlock.service',
        'key_holder_id',
        string='Unlock Services',
        help="Track when we've unlocked bins for this key holder"
    )
    
    unlock_service_count = fields.Integer(
        string='Unlock Services Count',
        compute='_compute_unlock_service_count',
        help="Number of times we've unlocked bins for this contact"
    )
    
    # Notes and documentation
    notes = fields.Text(
        string='Notes',
        help="Additional notes about this key assignment"
    )
    
    # Audit fields
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    create_uid = fields.Many2one(
        'res.users',
        string='Created by',
        readonly=True
    )
    
    @api.depends('unlock_service_ids')
    def _compute_unlock_service_count(self):
        """Compute the number of unlock services for this key holder"""
        for record in self:
            record.unlock_service_count = len(record.unlock_service_ids)
    
    def action_return_key(self):
        """Mark key as returned"""
        self.ensure_one()
        if self.status != 'issued':
    pass
            raise UserError(_('Can only return keys that are currently issued.'))
        
        self.write({
            'status': 'returned',
            'return_date': fields.Date.today(),
            'returned_by_user_id': self.env.user.id
        })
        
        # Update partner key status
        self.partner_id._compute_has_bin_key()
        
        self.message_post(
            body=_('Key %s returned by %s') % (self.key_number, self.env.user.name)
        )
        
        return True
    
    def action_mark_lost(self):
        """Mark key as lost/missing"""
        self.ensure_one()
        if self.status not in ['issued']:
    pass
            raise UserError(_('Can only mark issued keys as lost.'))
        
        self.write({
            'status': 'lost',
            'return_date': fields.Date.today(),
            'returned_by_user_id': self.env.user.id
        })
        
        self.message_post(
            body=_('Key %s marked as lost/missing by %s') % (self.key_number, self.env.user.name)
        )
        
        return True
    
    def action_replace_key(self):
        """Create a replacement key"""
        self.ensure_one()
        if self.status not in ['lost', 'issued']:
    pass
            raise UserError(_('Can only replace lost or issued keys.'))
        
        # Create new key
        new_key = self.create({
            'partner_id': self.partner_id.id,
            'issue_location': self.issue_location,
            'bin_locations': self.bin_locations,
            'emergency_contact': self.emergency_contact,
            'replaces_key_id': self.id,
            'notes': _('Replacement for key %s') % self.key_number
        })
        
        # Mark current key as replaced
        self.write({
            'status': 'replaced',
            'replaced_by_key_id': new_key.id,
            'return_date': fields.Date.today()
        })
        
        self.message_post(
            body=_('Key %s replaced by new key %s') % (self.key_number, new_key.key_number)
        )
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bin.key.management',
            'res_id': new_key.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_unlock_services(self):
        """View unlock services for this key holder"""
        self.ensure_one()
        return {
            'name': _('Unlock Services - %s') % self.partner_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'bin.unlock.service',
            'view_mode': 'tree,form',
            'domain': [('key_holder_id', '=', self.id)],
            'context': {
                'default_key_holder_id': self.id,
                'default_partner_id': self.partner_id.id,
            }
        }


class BinUnlockService(models.Model):
    """Track bin unlock services provided to customers"""
    _name = 'bin.unlock.service'
    _description = 'Bin Unlock Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_date desc, id desc'
    _rec_name = 'service_number'

    # Core identification
    service_number = fields.Char(
        string='Service Number',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('bin.unlock.service') or 'UNLOCK-NEW',
        tracking=True
    )
    
    # Customer and key information
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer Contact',
        required=True,
        tracking=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Customer Company',
        related='partner_id.parent_id',
        store=True
    )
    
    key_holder_id = fields.Many2one(
        'bin.key.management',
        string='Key Holder Record',
        help="Reference to the key management record if customer has a key"
    )
    
    # Service details
    service_date = fields.Datetime(
        string='Service Date',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )
    
    technician_id = fields.Many2one(
        'res.users',
        string='Technician',
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        domain=[('groups_id', 'in', ['records_management.group_shredding_technician', 'records_management.group_records_manager'])]
    )
    
    bin_location = fields.Char(
        string='Bin Location',
        required=True,
        help="Specific location of the bin that was unlocked"
    )
    
    # Reason and resolution
    unlock_reason = fields.Selection([
        ('wrong_item', 'Wrong Item Deposited'),
        ('retrieve_item', 'Need to Retrieve Item'),
        ('maintenance', 'Bin Maintenance'),
        ('emergency', 'Emergency Access'),
        ('other', 'Other'),
    ], string='Unlock Reason', required=True)
    
    reason_description = fields.Text(
        string='Reason Description',
        required=True,
        help="Detailed description of why unlock was needed"
    )
    
    items_retrieved = fields.Text(
        string='Items Retrieved',
        help="Description of items retrieved from the bin"
    )
    
    # Billing information
    charge_amount = fields.Float(
        string='Charge Amount',
        default=25.00,
        help="Amount charged for the unlock service"
    )
    
    billable = fields.Boolean(
        string='Billable',
        default=True,
        help="Whether this service should be billed to the customer"
    )
    
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        readonly=True,
        help="Invoice generated for this service"
    )
    
    # Status tracking
    status = fields.Selection([
        ('completed', 'Completed'),
        ('pending_billing', 'Pending Billing'),
        ('billed', 'Billed'),
        ('no_charge', 'No Charge'),
    ], string='Status', default='completed', tracking=True)
    
    # Resolution and follow-up
    follow_up_required = fields.Boolean(
        string='Follow-up Required',
        help="Check if additional follow-up is needed"
    )
    
    follow_up_notes = fields.Text(
        string='Follow-up Notes'
    )
    
    # Photos and documentation
    photo_ids = fields.Many2many(
        'ir.attachment',
        string='Photos',
        help="Photos taken during the service"
    )
    
    notes = fields.Text(
        string='Service Notes'
    )
    
    def action_create_invoice(self):
    pass
        """Create invoice for the unlock service"""
        self.ensure_one()
        
        if not self.billable:
    pass
            raise UserError(_('This service is marked as non-billable.'))
        
        if self.invoice_id:
    pass
            raise UserError(_('Invoice already exists for this service.'))
        
        # Create invoice
        invoice_vals = {
            'partner_id': self.company_id.id or self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'ref': self.service_number,
            'invoice_line_ids': [(0, 0, {
                'name': _('Bin Unlock Service - %s') % self.bin_location,
                'quantity': 1,
                'price_unit': self.charge_amount,
                'account_id': self.env['account.account'].search([
                    ('user_type_id.name', '=', 'Income')])
                ], limit=1).id
            })]
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        self.write({
            'invoice_id': invoice.id,
            'status': 'billed'
        })
        
        self.message_post(
            body=_('Invoice %s created for unlock service') % invoice.name
        )
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_mark_no_charge(self):
        """Mark service as no charge"""
        self.ensure_one()
        self.write({
            'billable': False,
            'status': 'no_charge'
        })
        
        self.message_post(
            body=_('Service marked as no charge by %s') % self.env.user.name
        )
        
        return True
