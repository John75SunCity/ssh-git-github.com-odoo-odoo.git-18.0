from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsApprovalWorkflow(models.Model):
    _name = 'records.approval.workflow'
    _description = 'Records Approval Workflow'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Workflow Name', required=True, tracking=True, help="A descriptive name for the approval workflow, e.g., 'High-Value Destruction Approval'.")
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)

    # ============================================================================
    # CONFIGURATION
    # ============================================================================
    res_model_id = fields.Many2one('ir.model', string="Applies To", required=True, tracking=True, ondelete='cascade',
        help="The model this approval workflow applies to (e.g., Destruction Request, Service Request).")
    description = fields.Text(string="Description", help="A detailed explanation of when and how this workflow should be used.")

    # ============================================================================
    # WORKFLOW LINES & STATE
    # ============================================================================
    approval_line_ids = fields.One2many('records.approval.workflow.line', 'workflow_id', string="Approval Steps", copy=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        self.ensure_one()
        if not self.approval_line_ids:
            raise ValidationError(_("Cannot activate a workflow with no approval steps defined."))
        self.write({'state': 'active'})
        self.message_post(body=_("Workflow activated by %s.", self.env.user.name))

    def action_archive(self):
        self.write({'state': 'archived', 'active': False})
        self.message_post(body=_("Workflow archived by %s.", self.env.user.name))

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body=_("Workflow reset to draft by %s.", self.env.user.name))

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
