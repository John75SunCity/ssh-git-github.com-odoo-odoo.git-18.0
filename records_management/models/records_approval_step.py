# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsApprovalStep(models.Model):
    """Model for approval workflow steps."""
    _name = 'records.approval.step'
    _description = 'Records Approval Step'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'workflow_id, sequence, id'

    # Core fields
    name = fields.Char('Step Name', required=True, tracking=True)
    description = fields.Text('Description')
    sequence = fields.Integer('Sequence', default=10, help='Order of step in workflow')
    
    # Workflow relationship
    workflow_id = fields.Many2one('records.approval.workflow', string='Approval Workflow', 
                                  required=True, ondelete='cascade'
    
    # Approval details
    approver_user_id = fields.Many2one('res.users', string='Approver')
    approver_group_id = fields.Many2one('res.groups', string='Approver Group')
    approval_type = fields.Selection([
        ('user', 'Specific User'),
        ('group', 'Group Member'),
        ('manager', 'Department Manager'),
        ('any', 'Any User'),
    ), string='Approval Type', default='user', tracking=True)
    # Status and timing
    state = fields.Selection([
        ('pending', 'Pending',
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('skipped', 'Skipped'),
    ), string='State', default='pending', tracking=True)
    
    approved_date = fields.Datetime('Approved Date', readonly=True)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True)
    rejection_reason = fields.Text('Rejection Reason')
    
    # Conditions
    required = fields.Boolean('Required', default=True, 
                             help='If unchecked, this step can be skipped',
    auto_approve = fields.Boolean('Auto Approve', default=False,
                                 help='Automatically approve this step under certain conditions')
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company
    active = fields.Boolean('Active', default=True)
    
    @api.constrains('approver_user_id', 'approver_group_id', 'approval_type')
    def _check_approver_settings(self):
        """Validate approver configuration"""
        for record in self:
            if record.approval_type == 'user' and not record.approver_user_id:
    pass
                raise ValidationError(_('Specific user must be selected for user approval type'))
            if record.approval_type == 'group' and not record.approver_group_id:
    pass
                raise ValidationError(_('Group must be selected for group approval type'))
    
    def action_approve(self):
        """Approve this step"""
        self.ensure_one()
        self.write({
            'state': 'approved',
            'approved_date': fields.Datetime.now(),
            'approved_by': self.env.user.id
        })
    
    def action_reject(self, reason=None):
        """Reject this step"""
        self.ensure_one()
        vals = {'state': 'rejected'}
        if reason:
    pass
            vals['rejection_reason'] = reason
        self.write(vals)
