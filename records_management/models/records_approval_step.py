from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RecordsApprovalStep(models.Model):
    _name = 'records.approval.step'
    _description = 'Records Approval Step Instance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Step Name", required=True, readonly=True)
    sequence = fields.Integer(string='Sequence', default=10, readonly=True)
    company_id = fields.Many2one(related='request_id.company_id', store=True)
    
    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    request_id = fields.Many2one('records.approval.request', string="Approval Request", required=True, ondelete='cascade', readonly=True)
    workflow_line_id = fields.Many2one('records.approval.workflow.line', string="Workflow Step", readonly=True, help="The workflow template line this step is based on.")
    
    # ============================================================================
    # APPROVAL STATE & DETAILS
    # ============================================================================
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('skipped', 'Skipped'),
    ], string="Status", default='pending', required=True, tracking=True, readonly=True)
    
    approver_id = fields.Many2one('res.users', string="Assigned Approver", readonly=True, help="The user responsible for this approval step.")
    approver_group_id = fields.Many2one('res.groups', string="Assigned Group", readonly=True, help="The group responsible for this approval step.")
    
    approved_by_id = fields.Many2one('res.users', string="Processed By", readonly=True)
    approval_date = fields.Datetime(string="Processed Date", readonly=True)
    comments = fields.Text(string="Approver Comments")
    
    can_approve = fields.Boolean(string="Can Current User Approve?", compute='_compute_can_approve', help="Technical field to control UI visibility of approval buttons.")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('approver_id', 'approver_group_id')
    def _compute_can_approve(self):
        """Check if the current user is allowed to approve this step."""
        for step in self:
            can_approve = False
            if step.state == 'pending':
                if step.approver_id and step.approver_id == self.env.user:
                    can_approve = True
                elif step.approver_group_id and self.env.user.has_group(step.approver_group_id.xml_id):
                    can_approve = True
            step.can_approve = can_approve

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_approve(self):
        self.ensure_one()
        if not self.can_approve:
            raise UserError(_("You are not authorized to approve this step."))
        
        self.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        self.request_id._process_next_step()
        self.message_post(body=_("Step approved by %s.", self.env.user.name))

    def action_reject(self):
        self.ensure_one()
        if not self.can_approve:
            raise UserError(_("You are not authorized to reject this step."))
            
        self.write({
            'state': 'rejected',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        self.request_id.write({'state': 'rejected'})
        self.message_post(body=_("Step rejected by %s. Reason: %s", self.env.user.name, self.comments or _("No reason provided.")))

    def action_skip(self):
        """Allows a manager to skip an optional step."""
        self.ensure_one()
        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_("Only a Records Manager can skip an approval step."))
        
        self.write({
            'state': 'skipped',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        self.request_id._process_next_step()
        self.message_post(body=_("Step skipped by %s.", self.env.user.name))
