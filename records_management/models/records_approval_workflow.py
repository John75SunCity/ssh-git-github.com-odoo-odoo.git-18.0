from odoo import models, fields, api
from datetime import datetime, timedelta

class RecordsApprovalWorkflow(models.Model):
    _name = 'records.approval.workflow'
    _description = 'Records Approval Workflow'
    _order = 'name'

    name = fields.Char('Workflow Name', required=True)
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)
    
    # Workflow configuration
    workflow_type = fields.Selection([
        ('policy', 'Policy Approval'),
        ('document', 'Document Approval'),
        ('destruction', 'Destruction Approval'),
        ('access', 'Access Request Approval'),
        ('general', 'General Approval')
    ], string='Workflow Type', required=True, default='general')
    
    auto_approve_threshold = fields.Float('Auto-Approve Threshold', default=0.0,
                                        help='Automatically approve requests below this threshold')
    
    require_manager_approval = fields.Boolean('Require Manager Approval', default=True)
    require_compliance_review = fields.Boolean('Require Compliance Review', default=False)
    require_legal_review = fields.Boolean('Require Legal Review', default=False)
    
    # Approval steps
    step_ids = fields.One2many('records.approval.step', 'workflow_id', string='Approval Steps')
    
    # Statistics
    total_requests = fields.Integer('Total Requests', compute='_compute_statistics', compute_sudo=False)
    approved_requests = fields.Integer('Approved Requests', compute='_compute_statistics', compute_sudo=False)
    rejected_requests = fields.Integer('Rejected Requests', compute='_compute_statistics', compute_sudo=False)
    pending_requests = fields.Integer('Pending Requests', compute='_compute_statistics', compute_sudo=False)
    
    approval_rate = fields.Float('Approval Rate %', compute='_compute_statistics', compute_sudo=False)
    avg_approval_time = fields.Float('Avg Approval Time (hours)', compute='_compute_statistics', compute_sudo=False)
    
    @api.depends('step_ids')
    def _compute_statistics(self):
        """Compute workflow statistics"""
        for workflow in self:
            # For now, set default values as we don't have approval request model yet
            workflow.total_requests = 0
            workflow.approved_requests = 0
            workflow.rejected_requests = 0
            workflow.pending_requests = 0
            workflow.approval_rate = 0.0
            workflow.avg_approval_time = 0.0
    
    def action_duplicate(self):
        """Duplicate this workflow"""
        copy_values = {
            'name': f"{self.name} (Copy)",
            'active': False
        }
        return self.copy(copy_values)

class RecordsApprovalStep(models.Model):
    _name = 'records.approval.step'
    _description = 'Approval Workflow Step'
    _order = 'sequence, id'

    workflow_id = fields.Many2one('records.approval.workflow', string='Workflow', required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
    
    # Step configuration
    step_type = fields.Selection([
        ('user', 'Specific User'),
        ('group', 'User Group'),
        ('manager', 'Manager'),
        ('department', 'Department Head'),
        ('compliance', 'Compliance Officer'),
        ('legal', 'Legal Review'),
        ('automatic', 'Automatic')
    ], string='Step Type', required=True, default='user')
    
    approver_user_id = fields.Many2one('res.users', string='Approver User')
    approver_group_id = fields.Many2one('res.groups', string='Approver Group')
    
    is_required = fields.Boolean('Required Step', default=True)
    can_delegate = fields.Boolean('Can Delegate', default=False)
    timeout_hours = fields.Integer('Timeout (Hours)', default=48,
                                 help='Hours before this step times out')
    
    # Conditions
    condition_field = fields.Char('Condition Field', help='Field to check for conditions')
    condition_operator = fields.Selection([
        ('=', 'Equal'),
        ('!=', 'Not Equal'),
        ('>', 'Greater Than'),
        ('<', 'Less Than'),
        ('>=', 'Greater or Equal'),
        ('<=', 'Less or Equal'),
        ('in', 'In'),
        ('not in', 'Not In')
    ], string='Condition Operator')
    condition_value = fields.Char('Condition Value')
    
    @api.onchange('step_type')
    def _onchange_step_type(self):
        """Clear inappropriate fields when step type changes"""
        if self.step_type != 'user':
            self.approver_user_id = False
        if self.step_type != 'group':
            self.approver_group_id = False
