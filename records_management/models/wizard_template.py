# -*- coding: utf-8 -*-
"""
Wizard Template Module

This module provides a comprehensive template for creating transient wizards within
the Records Management System. It includes all standard fields, methods, and patterns
used throughout the system for consistency and maintainability.

Key Features:
- Complete enterprise field template
- Mail thread framework integration
- Standard action methods with audit trails
- Company and user context management
- Comprehensive validation and error handling
- NAID compliance ready structure

Business Process:
1. Wizard Initialization: Set up context and default values
2. User Input: Collect required information with validation
3. Processing: Execute business logic with error handling
4. Audit Trail: Create audit logs and notifications
5. Result: Return appropriate actions or close wizard

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class WizardTemplate(models.TransientModel):
    _name = 'wizard.template'
    _description = 'Wizard Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc, create_date desc'  # Explicitly specify sort direction for clarity
    _rec_name = 'name'

    # Magic values for auto-generated names
    NAME_NEW = 'New'
    NAME_SLASH = '/'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        index=True,
        help="Name or title of this wizard operation"
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Set to false to hide this wizard without deleting it"
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    # ============================================================================
    # CONTEXT AND COMPANY FIELDS
    # ============================================================================
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        help="Company this wizard operation belongs to"
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        help="User executing this wizard"
    )
    
    # ============================================================================
    # BUSINESS SPECIFIC FIELDS
    # ============================================================================
    
    description = fields.Text(
        string='Description',
        help="Detailed description of the wizard operation"
    )
    
    notes = fields.Html(
        string='Internal Notes',
        help="Internal notes for reference and documentation"
    )
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Priority', default='normal', tracking=True)

    # ============================================================================
    # TIMING AND SCHEDULING FIELDS
    # ============================================================================
    
    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        help="When this wizard operation is scheduled to run"
    )
    
    completed_date = fields.Datetime(
        string='Completed Date',
        readonly=True,
        help="When this wizard operation was completed"
    )
    
    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Related Partner',
        help="Partner associated with this wizard operation"
    )
    
    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS (REQUIRED for mail.thread inheritance)
    # ============================================================================
    
    activity_ids = fields.One2many(
        'mail.activity',
        'res_id',
        string='Activities',
        domain=[('res_model', '=', 'wizard.template')]
    )
    
    message_follower_ids = fields.One2many(
        'mail.followers',
        'res_id',
        string='Followers',
        domain=[('res_model', '=', 'wizard.template')]
    )
    
    message_ids = fields.One2many(
        'mail.message',
        'res_id',
        string='Messages',
        domain=[('res_model', '=', 'wizard.template')]
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    
    @api.depends('state', 'scheduled_date')
    def _compute_can_execute(self):
        """Determine if wizard can be executed"""
        for record in self:
            record.can_execute = (
                record.state == 'draft' and 
                (not record.scheduled_date or record.scheduled_date <= fields.Datetime.now())
            )
    
    can_execute = fields.Boolean(
        string='Can Execute',
        compute='_compute_can_execute',
        help="Whether this wizard can be executed now"
    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    
    def action_execute(self):
        """Execute the wizard action with comprehensive processing"""
        self.ensure_one()
        
        # Validation
        self._validate_execution()
        
        try:
            # Update state
            self.write({
                'state': 'processing',
                'completed_date': fields.Datetime.now()
            })
            
            # Execute business logic
            result = self._execute_business_logic()
            
            # Mark as completed
            self.write({'state': 'completed'})
            
            # Create audit trail
            self._create_audit_log('wizard_executed')
            
            # Send notifications
            self._send_completion_notification()
            
            return result or {'type': 'ir.actions.act_window_close'}
            
        except Exception as e:
            # Handle errors gracefully
            self.write({'state': 'cancelled'})
            self._create_audit_log('wizard_failed', error=str(e))
            raise UserError(_(f'Wizard execution failed: {str(e)}')) from e
    
    def action_cancel(self):
        """Cancel the wizard operation"""
        self.ensure_one()
        
        if self.state == 'completed':
            raise UserError(_('Cannot cancel completed wizard operations'))
        
        self.write({
            'state': 'cancelled',
            'completed_date': fields.Datetime.now()
        })
        
        self._create_audit_log('wizard_cancelled')
        
        return {'type': 'ir.actions.act_window_close'}
    
    def action_reset_to_draft(self):
        """Reset wizard to draft state"""
        self.ensure_one()
        
        if self.state == 'processing':
            raise UserError(_('Cannot reset wizard that is currently processing'))
        
        self.write({
            'state': 'draft',
            'completed_date': False
        })
        
        self._create_audit_log('wizard_reset')

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    
    def _execute_business_logic(self):
        """Override this method in specific wizard implementations"""
        # Default implementation - override in specific wizards
        return True
    
    def _validate_execution(self):
        """Validate that wizard can be executed"""
        if self.state != 'draft':
            raise ValidationError(_('Wizard must be in draft state to execute'))
        
        if self.scheduled_date and self.scheduled_date > fields.Datetime.now():
            raise ValidationError(_('Cannot execute wizard before scheduled date'))
    
    def _create_audit_log(self, action, **kwargs):
        """Create audit log entry for NAID compliance"""
        try:
            audit_vals = {
                'name': _(f'Wizard Template: {action}'),
                'model_name': self._name,
                'record_id': self.id,
                'action': action,
                'user_id': self.env.user.id,
                'company_id': self.company_id.id,
                'details': kwargs.get('error', _(f'Wizard {action} executed successfully')),
            }
            
            # Try to create audit log if model exists
            if 'naid.audit.log' in self.env:
                self.env['naid.audit.log'].create(audit_vals)
                
        except Exception:
            # Don't fail wizard if audit logging fails
            pass
    
    def _send_completion_notification(self):
        """Send notification when wizard completes"""
        if self.user_id:
            self.message_post(
                body=_(f'Wizard Template "{self.name}" completed successfully'),
                message_type='notification',
                partner_ids=[self.user_id.partner_id.id]
            )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    
    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        """Validate scheduled date is not in the past for new records"""
        for record in self:
            if (record.scheduled_date and 
                record.scheduled_date < fields.Datetime.now() and 
                record.state == 'draft' and 
                not record._origin.id):  # Only for new records
                raise ValidationError(_(
                    'Scheduled date cannot be in the past for new wizard operations'
                ))
    
    @api.constrains('name')
    def _check_name_length(self):
        """Ensure name is not too short"""
        for record in self:
            if len(record.name.strip()) < 3:
                raise ValidationError(_(
                    'Wizard name must be at least 3 characters long'
                ))

    # ============================================================================
    # ORM OVERRIDE METHODS
    # ============================================================================
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add auto-numbering and validation"""
        for vals in vals_list:
            # Auto-generate name if not provided
            if not vals.get('name') or vals['name'] in [self.NAME_NEW, self.NAME_SLASH]:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'wizard.template'
                ) or _('New Wizard')
        
        records = super().create(vals_list)
        
        # Create initial audit log
        for record in records:
            record._create_audit_log('wizard_created')
        
        return records
    
    def write(self, vals):
        """Override write to track important changes"""
        # Track state changes
        if 'state' in vals:
            for record in self:
                if record.state != vals['state']:
                    record._create_audit_log('state_changed', 
                                           old_state=record.state, 
                                           new_state=vals['state'])
        
        return super().write(vals)
    
    def unlink(self):
        """Override unlink to prevent deletion of completed wizards"""
        for record in self:
            if record.state == 'completed':
                raise UserError(_('Cannot delete completed wizard operations'))
        
        return super().unlink()
