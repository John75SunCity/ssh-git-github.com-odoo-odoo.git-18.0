# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Partner(models.Model):
    """Extend partner model with bin key management functionality"""
    _inherit = 'res.partner'

    # Key management fields
    has_bin_key = fields.Boolean(
        string='Has Bin Key',
        compute='_compute_has_bin_key',
        store=True,
        help="Whether this contact currently has a bin key issued to them"
    )
    
    bin_key_ids = fields.One2many(
        'bin.key.management',
        'partner_id',
        string='Bin Keys',
        help="All keys that have been issued to this contact"
    )
    
    active_bin_key_id = fields.Many2one(
        'bin.key.management',
        string='Active Bin Key',
        compute='_compute_has_bin_key',
        store=True,
        help="The currently active key for this contact"
    )
    
    key_issue_date = fields.Date(
        string='Key Issue Date',
        related='active_bin_key_id.issue_date',
        readonly=True,
        help="When the current key was issued"
    )
    
    key_issued_by = fields.Many2one(
        'res.users',
        string='Key Issued By',
        related='active_bin_key_id.issued_by_user_id',
        readonly=True,
        help="Who issued the current key"
    )
    
    is_emergency_key_contact = fields.Boolean(
        string='Emergency Key Contact',
        related='active_bin_key_id.emergency_contact',
        readonly=True,
        help="This contact can be reached for emergency bin access"
    )
    
    # Key unlock service tracking
    unlock_service_ids = fields.One2many(
        'bin.unlock.service',
        'partner_id',
        string='Unlock Services',
        help="Bin unlock services provided to this contact"
    )
    
    unlock_service_count = fields.Integer(
        string='Unlock Services',
        compute='_compute_unlock_service_count',
        help="Number of unlock services provided"
    )
    
    total_unlock_charges = fields.Float(
        string='Total Unlock Charges',
        compute='_compute_unlock_service_stats',
        help="Total amount charged for unlock services"
    )
    
    # Key holder visibility for company contacts
    company_key_holders = fields.One2many(
        'res.partner',
        compute='_compute_company_key_holders',
        string='Key Holders in Company',
        help="Other contacts in this company who have bin keys"
    )
    
    company_key_holder_count = fields.Integer(
        string='Company Key Holders',
        compute='_compute_company_key_holders',
        help="Number of key holders in this company"
    )

    @api.depends('bin_key_ids', 'bin_key_ids.status')
    def _compute_has_bin_key(self):
        """Compute if contact currently has an active bin key"""
        for partner in self:
    pass
            active_key = partner.bin_key_ids.filtered(lambda k: k.status == 'issued')
            partner.has_bin_key = bool(active_key)
            partner.active_bin_key_id = active_key[0].id if active_key else False
    
    @api.depends('unlock_service_ids')
    def _compute_unlock_service_count(self):
    pass
        """Compute unlock service count"""
        for partner in self:
            partner.unlock_service_count = len(partner.unlock_service_ids)
    
    @api.depends('unlock_service_ids', 'unlock_service_ids.charge_amount', 'unlock_service_ids.billable')
    def _compute_unlock_service_stats(self):
        """Compute unlock service statistics"""
        for partner in self:
            billable_services = partner.unlock_service_ids.filtered('billable')
            partner.total_unlock_charges = sum(billable_services.mapped('charge_amount'))
    
    @api.depends('parent_id', 'parent_id.child_ids')
    def _compute_company_key_holders(self):
        """Compute other key holders in the same company"""
        for partner in self:
            if partner.parent_id:
    pass
                # Find other contacts in the same company who have keys
                company_contacts = partner.parent_id.child_ids.filtered(
                    lambda p: p.id != partner.id and p.has_bin_key
                )
                partner.company_key_holders = company_contacts
                partner.company_key_holder_count = len(company_contacts)
            else:
                partner.company_key_holders = False
                partner.company_key_holder_count = 0
    
    def action_issue_bin_key(self):
        """Issue a new bin key to this contact"""
        self.ensure_one()
        
        if self.has_bin_key:
    pass
            raise UserError(_('This contact already has an active bin key.'))
        
        return {
            'name': _('Issue Bin Key'),
            'type': 'ir.actions.act_window',
            'res_model': 'bin.key.management',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_issue_location': 'Customer Site',
                'default_emergency_contact': False,
            }
        }
    
    def action_view_bin_keys(self):
        """View all bin keys for this contact"""
        self.ensure_one()
        return {
            'name': _('Bin Keys - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'bin.key.management',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
            }
        }
    
    def action_return_bin_key(self):
        """Return the active bin key"""
        self.ensure_one()
        
        if not self.has_bin_key:
    pass
            raise UserError(_('This contact does not have an active bin key.'))
        
        return self.active_bin_key_id.action_return_key()
    
    def action_report_key_lost(self):
        """Report the bin key as lost"""
        self.ensure_one()
        
        if not self.has_bin_key:
    pass
            raise UserError(_('This contact does not have an active bin key.'))
        
        return self.active_bin_key_id.action_mark_lost()
    
    def action_replace_bin_key(self):
        """Replace the current bin key"""
        self.ensure_one()
        
        if not self.has_bin_key:
    pass
            raise UserError(_('This contact does not have an active bin key.'))
        
        return self.active_bin_key_id.action_replace_key()
    
    def action_create_unlock_service(self):
        """Create a new unlock service for this contact"""
        self.ensure_one()
        
        return {
            'name': _('Create Unlock Service'),
            'type': 'ir.actions.act_window',
            'res_model': 'bin.unlock.service',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_key_holder_id': self.active_bin_key_id.id if self.has_bin_key else False,
                'default_charge_amount': 25.00,
            }
        }
    
    def action_view_unlock_services(self):
        """View unlock services for this contact"""
        self.ensure_one()
        return {
            'name': _('Unlock Services - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'bin.unlock.service',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
                'default_key_holder_id': self.active_bin_key_id.id if self.has_bin_key else False,
            }
        }
    
    def action_view_company_key_holders(self):
    pass
        """View other key holders in the same company"""
        self.ensure_one()
        
        if not self.parent_id:
    pass
            raise UserError(_('This contact is not associated with a company.'))
        
        return {
            'name': _('Key Holders - %s') % self.parent_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [
                ('parent_id', '=', self.parent_id.id),
                ('has_bin_key', '=', True)
            ],
            'context': {
                'search_default_has_bin_key': 1,
            }
        }


class PartnerBinKeyWizard(models.TransientModel):
    """Wizard for quickly issuing bin keys from contact form"""
    _name = 'partner.bin.key.wizard'
    _description = 'Partner Bin Key Issue Wizard'
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        required=True,
        readonly=True
    )
    
    issue_location = fields.Char(
        string='Issue Location',
        default='Customer Site',
        required=True,
        help="Where the key is being issued"
    )
    
    bin_locations = fields.Text(
        string='Bin Locations',
        help="List of bin locations this key provides access to"
    )
    
    emergency_contact = fields.Boolean(
        string='Emergency Contact',
        default=False,
        help="This contact can be reached for emergency bin access"
    )
    
    notes = fields.Text(
        string='Notes',
        help="Additional notes about this key assignment"
    )
    
    def action_issue_key(self):
        """Issue the bin key"""
        self.ensure_one()
        
        # Create key management record
        key_record = self.env['bin.key.management'].create({
            'partner_id': self.partner_id.id,
            'issue_location': self.issue_location,
            'bin_locations': self.bin_locations,
            'emergency_contact': self.emergency_contact,
            'notes': self.notes,
        })
        
        # Show success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Key Issued'),
                'message': _('Bin key %s issued to %s successfully.') % (key_record.key_number, self.partner_id.name),
                'type': 'success',
            }
        }
