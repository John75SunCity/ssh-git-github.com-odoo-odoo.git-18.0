from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import hashlib


class PermanentFlagWizard(models.TransientModel):
    _name = 'records.permanent.flag.wizard'
    _description = 'Permanent Flag Security Wizard'

    document_ids = fields.Many2many(
        'records.document', 
        string='Documents',
        required=True
    )
    action_type = fields.Selection([
        ('mark', 'Mark as Permanent'),
        ('unmark', 'Remove Permanent Flag')
    ], string='Action', required=True)
    
    user_password = fields.Char(
        'Your Password', 
        required=True,
        help="Enter your user password to confirm this security-sensitive action"
    )
    
    document_count = fields.Integer(
        'Number of Documents',
        compute='_compute_document_count'
    )
    
    # Additional fields for enhanced functionality
    box_id = fields.Many2one('records.box', string='Box')
    customer_id = fields.Many2one('res.partner', string='Customer')
    permanent_flag = fields.Boolean(string='Permanent Flag', default=True)
    permanent_flag_set_by = fields.Many2one('res.users', string='Set By', default=lambda self: self.env.user)
    permanent_flag_set_date = fields.Datetime(string='Set Date', default=fields.Datetime.now)
    
    # Technical fields for view compatibility
    arch = fields.Text(string='View Architecture')
    model = fields.Char(string='Model Name', default='records.permanent.flag.wizard')
    name = fields.Char(string='Wizard Name', compute='_compute_name')
    
    @api.depends('action_type', 'document_count')
    def _compute_name(self):
        for record in self:
            if record.action_type == 'mark':
                record.name = f"Mark {record.document_count} documents as permanent"
            elif record.action_type == 'unmark':
                record.name = f"Remove permanent flag from {record.document_count} documents"
            else:
                record.name = "Permanent Flag Wizard"
    
    @api.depends('document_ids')
    def _compute_document_count(self):
        for wizard in self:
            wizard.document_count = len(wizard.document_ids)
    
    def action_confirm(self):
        """Confirm the permanent flag action after password verification."""
        self.ensure_one()
        
        # Verify password
        if not self._verify_password():
            raise ValidationError(_('Invalid password. Please try again.'))
        
        if self.action_type == 'mark':
            self._mark_documents_permanent()
        elif self.action_type == 'unmark':
            self._unmark_documents_permanent()
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _verify_password(self):
        """Verify the user's password."""
        if not self.user_password:
            return False
            
        # Get the current user's password hash from database
        user = self.env.user
        if not user.password:
            return False
            
        # Odoo stores passwords as crypt-style hashes
        # We need to use the same verification method
        from passlib.context import CryptContext
        crypt_context = CryptContext(schemes=['pbkdf2_sha512', 'plaintext'], deprecated=['plaintext'])
        
        try:
            return crypt_context.verify(self.user_password, user.password)
        except Exception:
            return False
    
    def _mark_documents_permanent(self):
        """Mark documents as permanent."""
        # Filter out already permanent documents
        documents_to_mark = self.document_ids.filtered(lambda d: not d.permanent_flag)
        
        if not documents_to_mark:
            raise ValidationError(_('All selected documents are already marked as permanent.'))
        
        # Mark as permanent
        documents_to_mark._set_permanent_flag(permanent=True)
        
        # Show success message
        message = _('%d document(s) have been marked as PERMANENT by %s.') % (
            len(documents_to_mark), self.env.user.name
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Documents Marked as Permanent'),
                'message': message,
                'type': 'success',
                'sticky': True
            }
        }
    
    def _unmark_documents_permanent(self):
        """Remove permanent flag - admin only."""
        # Double-check admin permissions
        if not self.env.user.has_group('base.group_system'):
            raise ValidationError(_(
                'Only administrators can remove the permanent flag from documents.'
            ))
        
        # Filter documents that are actually permanent
        documents_to_unmark = self.document_ids.filtered(lambda d: d.permanent_flag)
        
        if not documents_to_unmark:
            raise ValidationError(_('None of the selected documents have the permanent flag set.'))
        
        # Remove permanent flag
        documents_to_unmark._set_permanent_flag(permanent=False)
        
        # Show success message
        message = _('%d document(s) have had their PERMANENT flag removed by administrator %s.') % (
            len(documents_to_unmark), self.env.user.name
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Permanent Flags Removed'),
                'message': message,
                'type': 'warning',
                'sticky': True
            }
        }
