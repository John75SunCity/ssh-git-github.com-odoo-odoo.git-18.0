# -*- coding: utf-8 -*-
"""
Customer Key Restriction Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResPartnerKeyRestriction(models.Model):
    """
    Extend res.partner to add key restriction functionality
    """
    
    _inherit = 'res.partner'
    
    # ==========================================
    # KEY RESTRICTION FIELDS
    # ==========================================
    
    key_issuance_allowed = fields.Boolean(
        string='Key Issuance Allowed',
        default=True,
        tracking=True,
        help='Allow issuing bin keys to this customer. If disabled, bin unlock service must be used instead.'
    )
    
    key_restriction_reason = fields.Selection([
        ('policy', 'Company Policy'),
        ('security', 'Security Requirements'),
        ('compliance', 'Compliance Requirements'),
        ('contract', 'Contract Terms'),
        ('risk', 'Risk Assessment'),
        ('other', 'Other')
    ], string='Restriction Reason', tracking=True,
       help='Reason why key issuance is restricted for this customer')
    
    key_restriction_notes = fields.Text(
        string='Key Restriction Notes',
        tracking=True,
        help='Additional notes about key restrictions for this customer'
    )
    
    key_restriction_date = fields.Date(
        string='Restriction Effective Date',
        tracking=True,
        help='Date when key restriction became effective'
    )
    
    key_restriction_approved_by = fields.Many2one(
        'res.users',
        string='Restriction Approved By',
        tracking=True,
        help='User who approved the key restriction'
    )
    
    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    
    @api.depends('key_issuance_allowed')
    def _compute_key_restriction_status(self):
        """Compute readable restriction status"""
        for partner in self:
            if partner.key_issuance_allowed:
                partner.key_restriction_status = 'allowed'
            else:
                partner.key_restriction_status = 'restricted'
    
    key_restriction_status = fields.Selection([
        ('allowed', 'Key Issuance Allowed'),
        ('restricted', 'Key Issuance Restricted')
    ], string='Key Status', compute='_compute_key_restriction_status', store=True)
    
    # Count of bin unlock services needed due to restrictions
    restricted_unlock_count = fields.Integer(
        string='Restricted Unlock Services',
        compute='_compute_restricted_unlock_count',
        help='Number of bin unlock services due to key restrictions'
    )
    
    @api.depends('key_issuance_allowed')
    def _compute_restricted_unlock_count(self):
        """Count bin unlock services for restricted customers"""
        for partner in self:
            if not partner.key_issuance_allowed:
                unlock_services = self.env['bin.unlock.service'].search_count([
                    ('customer_id', '=', partner.id),
                    ('unlock_reason', '=', 'key_restriction')
                ])
                partner.restricted_unlock_count = unlock_services
            else:
                partner.restricted_unlock_count = 0
    
    # ==========================================
    # VALIDATION AND BUSINESS LOGIC
    # ==========================================
    
    @api.constrains('key_issuance_allowed', 'key_restriction_reason')
    def _check_key_restriction_reason(self):
        """Validate that restricted customers have a reason"""
        for partner in self:
            if not partner.key_issuance_allowed and not partner.key_restriction_reason:
                raise UserError(_('Key restriction reason is required when key issuance is not allowed'))
    
    def action_restrict_key_issuance(self):
        """Restrict key issuance for this customer"""
        self.ensure_one()
        if not self.key_issuance_allowed:
            raise UserError(_('Key issuance is already restricted for this customer'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Restrict Key Issuance'),
            'res_model': 'key.restriction.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_action': 'restrict'
            }
        }
    
    def action_allow_key_issuance(self):
        """Allow key issuance for this customer"""
        self.ensure_one()
        if self.key_issuance_allowed:
            raise UserError(_('Key issuance is already allowed for this customer'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Allow Key Issuance'),
            'res_model': 'key.restriction.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_action': 'allow'
            }
        }
    
    def action_view_unlock_services(self):
        """View bin unlock services for this customer"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bin Unlock Services'),
            'res_model': 'bin.unlock.service',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.id)],
            'context': {
                'default_customer_id': self.id,
                'search_default_key_restriction': 1 if not self.key_issuance_allowed else 0
            }
        }
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def check_key_issuance_allowed(self, raise_error=True):
        """Check if key issuance is allowed for this customer"""
        self.ensure_one()
        
        if not self.key_issuance_allowed:
            message = _('Key issuance is restricted for customer "%s". Reason: %s') % (
                self.name,
                dict(self._fields['key_restriction_reason'].selection).get(
                    self.key_restriction_reason, 'Not specified'
                )
            )
            
            if raise_error:
                raise UserError(message)
            else:
                return False, message
        
        return True, _('Key issuance is allowed')
    
    def get_key_restriction_summary(self):
        """Get summary of key restrictions"""
        self.ensure_one()
        
        if self.key_issuance_allowed:
            return {
                'status': 'allowed',
                'message': _('Key issuance is allowed for this customer'),
                'icon': 'fa-key text-success'
            }
        else:
            return {
                'status': 'restricted',
                'message': _('Key issuance is restricted. Use bin unlock service instead.'),
                'reason': dict(self._fields['key_restriction_reason'].selection).get(
                    self.key_restriction_reason, 'Not specified'
                ),
                'notes': self.key_restriction_notes,
                'effective_date': self.key_restriction_date,
                'icon': 'fa-ban text-danger'
            }


# ==========================================
# KEY RESTRICTION WIZARD
# ==========================================
class KeyRestrictionWizard(models.TransientModel):
    """
    Wizard for managing key issuance restrictions
    """
    
    _name = 'key.restriction.wizard'
    _description = 'Key Restriction Management Wizard'
    
    # ==========================================
    # CORE FIELDS
    # ==========================================
    
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True)
    action = fields.Selection([
        ('restrict', 'Restrict Key Issuance'),
        ('allow', 'Allow Key Issuance')
    ], string='Action', required=True, readonly=True)
    
    # For restriction
    restriction_reason = fields.Selection([
        ('policy', 'Company Policy'),
        ('security', 'Security Requirements'),
        ('compliance', 'Compliance Requirements'),
        ('contract', 'Contract Terms'),
        ('risk', 'Risk Assessment'),
        ('other', 'Other')
    ], string='Restriction Reason')
    
    restriction_notes = fields.Text(string='Notes')
    effective_date = fields.Date(string='Effective Date', default=fields.Date.today)
    
    # For allowing
    allow_reason = fields.Text(string='Reason for Allowing', help='Reason for removing key restriction')
    
    # ==========================================
    # ACTIONS
    # ==========================================
    
    def action_confirm(self):
        """Confirm the key restriction change"""
        self.ensure_one()
        
        if self.action == 'restrict':
            if not self.restriction_reason:
                raise UserError(_('Restriction reason is required'))
            
            self.partner_id.write({
                'key_issuance_allowed': False,
                'key_restriction_reason': self.restriction_reason,
                'key_restriction_notes': self.restriction_notes,
                'key_restriction_date': self.effective_date,
                'key_restriction_approved_by': self.env.user.id
            })
            
            # Log the restriction
            self.partner_id.message_post(
                body=_('Key issuance restricted. Reason: %s') % dict(
                    self._fields['restriction_reason'].selection
                )[self.restriction_reason],
                message_type='notification'
            )
            
        elif self.action == 'allow':
            old_reason = dict(self.partner_id._fields['key_restriction_reason'].selection).get(
                self.partner_id.key_restriction_reason, 'Not specified'
            )
            
            self.partner_id.write({
                'key_issuance_allowed': True,
                'key_restriction_reason': False,
                'key_restriction_notes': self.allow_reason,
                'key_restriction_date': False,
                'key_restriction_approved_by': self.env.user.id
            })
            
            # Log the change
            self.partner_id.message_post(
                body=_('Key issuance restriction removed. Previous reason: %s. New reason: %s') % (
                    old_reason, self.allow_reason or 'Not specified'
                ),
                message_type='notification'
            )
        
        return {'type': 'ir.actions.act_window_close'}
