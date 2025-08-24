from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsApprovalWorkflowLine(models.Model):
    _name = 'records.approval.workflow.line'
    _description = 'Records Approval Workflow Line'
    _order = 'sequence, id'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    workflow_id = fields.Many2one('records.approval.workflow', string="Workflow", required=True, ondelete='cascade')
    name = fields.Char(string="Step Name", required=True, help="e.g., 'Manager Approval', 'Compliance Review'")
    sequence = fields.Integer(string='Sequence', default=10, help="Defines the order of the approval steps.")

    # ============================================================================
    # APPROVER CONFIGURATION
    # ============================================================================
    approval_type = fields.Selection([
        ('user', 'Specific User'),
        ('group', 'Security Group'),
    ], string="Approval Type", required=True, default='group')

    user_id = fields.Many2one('res.users', string="Approver (User)", help="The specific user required to approve this step.")
    group_id = fields.Many2one('res.groups', string="Approver (Group)", help="Any user from this security group can approve this step.")

    # ============================================================================
    # RULES & BEHAVIOR
    # ============================================================================
    required = fields.Boolean(string="Required", default=True, help="If checked, this approval step is mandatory.")
    notifications_enabled = fields.Boolean(string="Send Notifications", default=True, help="If checked, a notification will be sent to the approver(s).")

    @api.constrains('approval_type', 'user_id', 'group_id')
    def _check_approver(self):
        for line in self:
            if line.approval_type == 'user' and not line.user_id:
                raise ValidationError(_("For the 'Specific User' approval type, you must select an approver."))
            if line.approval_type == 'group' and not line.group_id:
                raise ValidationError(_("For the 'Security Group' approval type, you must select a group."))
