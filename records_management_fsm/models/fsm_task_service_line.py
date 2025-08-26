from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class FsmTaskServiceLine(models.Model):
    _name = 'fsm.task.service.line'
    _description = 'FSM Task Service Line Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'task_id, sequence'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Service", compute='_compute_name', store=True)
    sequence = fields.Integer(string="Sequence", default=10)

    task_id = fields.Many2one('fsm.task', string='FSM Task', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Customer', related='task_id.partner_id', store=True)
    company_id = fields.Many2one('res.company', string='Company', related='task_id.company_id', store=True)

    service_name = fields.Char(string='Service Name', required=True)
    description = fields.Text(string='Service Description')

    service_type = fields.Selection([
        ('repair', 'Repair'),
        ('maintenance', 'Maintenance'),
        ('installation', 'Installation'),
        ('other', 'Other')
    ], string='Service Type', default='maintenance')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    # On-site addition tracking
    added_on_site = fields.Boolean(string='Added On-Site', default=False)
    added_by_id = fields.Many2one('res.users', string='Added By', readonly=True)
    added_date = fields.Datetime(string='Added Date', readonly=True)

    # Approval fields
    customer_approved = fields.Boolean(string='Customer Approved', default=False)
    approval_method = fields.Selection([
        ('signature', 'Signature'),
        ('email', 'Email'),
        ('verbal', 'Verbal')
    ], string='Approval Method')

    # Pricing fields
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    unit_price = fields.Monetary(string='Unit Price')
    quantity = fields.Float(string='Quantity', default=1.0)
    total_price = fields.Monetary(string='Total Price', compute='_compute_total_price', store=True)

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('service_name', 'task_id.name')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.task_id.name or ''} - {record.service_name or ''}"

    @api.depends('unit_price', 'quantity')
    def _compute_total_price(self):
        for line in self:
            line.total_price = line.unit_price * line.quantity

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_request_approval(self):
        self.ensure_one()
        if self.customer_approved:
            raise UserError(_("This service has already been approved."))
        self.write({'state': 'pending_approval'})
    self.task_id.message_post(body=_("Approval requested for additional service: %s") % self.service_name)
        # Add logic here to send an email or notification for approval
        return True

    def action_approve_service(self):
        self.ensure_one()
        self.write({'state': 'approved', 'customer_approved': True})
    self.task_id.message_post(body=_("Additional service approved: %s") % self.service_name)
        return True

    def action_reject_service(self):
        self.ensure_one()
        self.write({'state': 'rejected'})
    self.task_id.message_post(body=_("Additional service rejected: %s") % self.service_name)
        return True

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('added_on_site'):
                vals['added_by_id'] = self.env.user.id
                vals['added_date'] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        if 'state' in vals:
            for record in self:
                old_state_label = dict(record._fields['state'].selection).get(record.state)
                new_state_label = dict(record._fields['state'].selection).get(vals['state'])
                if old_state_label != new_state_label:
                    record.message_post(body=_("Service '%s' status changed from %s to %s") % (record.service_name, old_state_label, new_state_label))
        return super().write(vals)



