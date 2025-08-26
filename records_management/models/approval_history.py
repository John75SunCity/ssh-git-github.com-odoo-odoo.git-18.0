from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ApprovalHistory(models.Model):
    _name = 'approval.history'
    _description = 'Approval History'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'approval_date desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one("res.users", string="User", default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # APPROVAL SPECIFIC FIELDS
    # ============================================================================
    contact_id = fields.Many2one("res.partner", string="Contact", tracking=True)
    approval_date = fields.Datetime(string="Approval Date", tracking=True, index=True)
    approval_type = fields.Selection([
        ('document', 'Document Approval'),
        ('destruction', 'Destruction Approval'),
        ('access', 'Access Approval'),
        ('budget', 'Budget Approval'),
        ('policy', 'Policy Approval'),
    ], string="Approval Type", required=True, tracking=True)

    approval_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('escalated', 'Escalated'),
    ], string="Approval Status", default='pending', required=True, tracking=True)

    approved_by_id = fields.Many2one("res.users", string="Approved By", tracking=True)
    approval_amount = fields.Monetary(string="Approval Amount", currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)

    # ============================================================================
    # TIMING AND TRACKING FIELDS
    # ============================================================================
    response_time_hours = fields.Float(string="Response Time (Hours)", compute="_compute_response_time", store=True)
    request_date = fields.Datetime(string="Request Date", required=True, default=fields.Datetime.now, tracking=True)
    completed_date = fields.Datetime(string="Completed Date", tracking=True)

    # ============================================================================
    # DESCRIPTION AND REFERENCE FIELDS
    # ============================================================================
    description = fields.Text(string="Description")
    approval_notes = fields.Text(string="Approval Notes", tracking=True)
    reference_document = fields.Char(string="Reference Document", index=True)

    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string="Priority", default='normal', tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string="State", default='draft', tracking=True)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    context = fields.Char(string="Context")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('request_date', 'completed_date')
    def _compute_response_time(self):
        """Compute response time in hours"""
        for record in self:
            if record.request_date and record.completed_date:
                delta = record.completed_date - record.request_date
                record.response_time_hours = delta.total_seconds() / 3600.0
            else:
                record.response_time_hours = 0.0

    # ============================================================================
    # CRUD METHODS
    # ============================================================================
    def write(self, vals):
        """Override write to track important changes"""
        # Update completion date when status changes to completed states
        if 'approval_status' in vals and vals['approval_status'] in ['approved', 'rejected']:
            vals['completed_date'] = fields.Datetime.now()
            if vals['approval_status'] == 'approved':
                vals['approved_by_id'] = self.env.user.id
        return super().write(vals)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_approve(self):
        """Approve the request"""
        self.ensure_one()
        if self.approval_status != "pending":
            raise UserError(_("Only pending approvals can be approved"))

        self.write({
            'approval_status': 'approved',
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'completed_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Approval granted by %s") % self.env.user.name)

    def action_reject(self):
        """Reject the request"""
        self.ensure_one()
        if self.approval_status != "pending":
            raise UserError(_("Only pending approvals can be rejected"))

        self.write({
            'approval_status': 'rejected',
            'state': 'rejected',
            'completed_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Approval rejected by %s") % self.env.user.name)

    def action_cancel(self):
        """Cancel the request"""
        self.ensure_one()
        if self.approval_status in ["approved", "rejected"]:
            raise UserError(_("Cannot cancel completed approvals"))

        self.write({
            'approval_status': 'cancelled',
            'state': 'cancelled',
        })
        self.message_post(body=_("Approval cancelled by %s") % self.env.user.name)

    def action_reset_to_pending(self):
        """Reset approval to pending status"""
        self.ensure_one()
        if self.approval_status == "pending":
            raise UserError(_("Approval is already pending"))

        self.write({
            'approval_status': 'pending',
            'state': 'submitted',
            'approved_by_id': False,
            'completed_date': False,
        })
        self.message_post(body=_("Approval reset to pending by %s") % self.env.user.name)

    def action_escalate(self):
        """Escalate approval to higher authority"""
        self.ensure_one()
        self.write({
            'approval_status': 'escalated',
            'priority': 'urgent',
        })

        # Create activity for manager
        manager = self.env.user.employee_id.parent_id.user_id if self.env.user.employee_id.parent_id else False
        if manager:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=manager.id,
                summary=_("Escalated Approval Required"),
                note=_("This approval has been escalated and requires immediate attention.")
            )

        self.message_post(body=_("Approval escalated by %s") % self.env.user.name)

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_approval_summary(self):
        """Get approval summary for reporting"""
        self.ensure_one()
        return {
            'name': self.name,
            'type': self.approval_type,
            'status': self.approval_status,
            'amount': self.approval_amount,
            'currency': self.currency_id.name,
            'response_time': self.response_time_hours,
            'approved_by': self.approved_by_id.name if self.approved_by_id else False,
        }

    @api.model
    def get_performance_metrics(self, date_from=None, date_to=None):
        """Get performance metrics for specified period"""
        domain = []
        if date_from:
            domain.append(('request_date', '>=', date_from))
        if date_to:
            domain.append(('request_date', '<=', date_to))

        approvals = self.search(domain)

        return {
            'total_approvals': len(approvals),
            'approved_count': len(approvals.filtered(lambda r: r.approval_status == 'approved')),
            'rejected_count': len(approvals.filtered(lambda r: r.approval_status == 'rejected')),
            'pending_count': len(approvals.filtered(lambda r: r.approval_status == 'pending')),
            'average_response_time': sum(approvals.mapped('response_time_hours')) / len(approvals) if approvals else 0,
        }

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Enhanced search by name, type, or reference"""
        args = args or []
        domain = []

        if name:
            domain = [
                '|', '|', '|',
                ('name', operator, name),
                ('approval_type', operator, name),
                ('reference_document', operator, name),
                ('description', operator, name)
            ]

        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('request_date', 'completed_date')
    def _check_dates(self):
        """Validate date consistency"""
        for record in self:
            if record.request_date and record.completed_date:
                if record.completed_date < record.request_date:
                    raise ValidationError(_("Completed date cannot be before request date"))

    @api.constrains('approval_amount')
    def _check_approval_amount(self):
        """Validate approval amount"""
        for record in self:
            if record.approval_amount < 0:
                raise ValidationError(_("Approval amount cannot be negative"))
