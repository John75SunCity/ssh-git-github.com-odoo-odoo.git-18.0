from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsBillingConfigAudit(models.Model):
    _name = 'records.billing.config.audit'
    _description = 'Records Billing Config Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'audit_date desc, id desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Audit Entry", compute='_compute_name', store=True)
    config_id = fields.Many2one('records.billing.config', string="Billing Configuration", required=True, ondelete='cascade', readonly=True)
    user_id = fields.Many2one('res.users', string="Changed By", required=True, readonly=True, default=lambda self: self.env.user)
    audit_date = fields.Datetime(string="Change Date", required=True, readonly=True, default=fields.Datetime.now)
    company_id = fields.Many2one(related='config_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)

    # ============================================================================
    # CHANGE DETAILS
    # ============================================================================
    action_type = fields.Selection([
        ('create', 'Create'),
        ('write', 'Update'),
        ('archive', 'Archive'),
    ], string="Action", required=True, readonly=True)

    field_changed = fields.Char(string="Field Changed", readonly=True)
    old_value = fields.Text(string="Old Value", readonly=True)
    new_value = fields.Text(string="New Value", readonly=True)
    change_reason = fields.Text(string="Reason for Change")

    # ============================================================================
    # APPROVAL & IMPACT
    # ============================================================================
    requires_approval = fields.Boolean(string="Requires Approval", readonly=True)
    approval_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Approval Status", default='pending', tracking=True)

    approved_by_id = fields.Many2one('res.users', string="Approved By", readonly=True)
    approval_date = fields.Datetime(string="Approval Date", readonly=True)

    impact_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string="Impact Level", readonly=True)

    # ============================================================================
    # TECHNICAL DETAILS
    # ============================================================================
    ip_address = fields.Char(string="IP Address", readonly=True)
    user_agent = fields.Text(string="User Agent", readonly=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('action_type', 'field_changed', 'audit_date')
    def _compute_name(self):
        for record in self:
            parts = []
            if record.action_type:
                action_dict = dict(record._fields['action_type'].selection)
                parts.append(action_dict.get(record.action_type, record.action_type))
            if record.field_changed:
                parts.append(f"({record.field_changed})")
            if record.audit_date:
                parts.append(f"on {record.audit_date.strftime('%Y-%m-%d')}")
            record.name = " ".join(parts) if parts else _("New Audit Entry")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_approve_change(self):
        self.ensure_one()
        if not self.requires_approval:
            raise UserError(_('This change does not require approval.'))
        if self.approval_status == 'approved':
            raise UserError(_('This change has already been approved.'))

        self.write({
            'approval_status': 'approved',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        self.message_post(body=_('Change approved by %s.', self.env.user.name))

    def action_reject_change(self):
        self.ensure_one()
        if not self.requires_approval:
            raise UserError(_('This change does not require approval.'))

        self.write({
            'approval_status': 'rejected',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        self.message_post(body=_('Change rejected by %s.', self.env.user.name))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    @api.model
    def log_change(self, config, action_type, changes):
        """
        Utility method to create audit log entries for one or more field changes.
        :param config: The records.billing.config recordset.
        :param action_type: The type of action ('write', 'create', etc.).
        :param changes: A dictionary of changes, e.g., {'field_name': {'old': old_val, 'new': new_val}}.
        """
        request = self.env.context.get('request')
        ip = request.httprequest.remote_addr if request else ''
        ua = request.httprequest.user_agent.string if request else ''

        for field, values in changes.items():
            audit_vals = {
                'config_id': config.id,
                'action_type': action_type,
                'field_changed': field,
                'old_value': str(values.get('old')),
                'new_value': str(values.get('new')),
                'user_id': self.env.user.id,
                'ip_address': ip,
                'user_agent': ua,
            }

            # Determine impact and approval requirements
            if field in ['unit_price', 'recurring_interval']:
                audit_vals.update({
                    'impact_level': 'high',
                    'requires_approval': True,
                    'approval_status': 'pending',
                })
            elif field in ['active', 'billing_type']:
                audit_vals.update({'impact_level': 'medium'})
            else:
                audit_vals.update({'impact_level': 'low'})

            audit_entry = self.create(audit_vals)
            if audit_vals.get('requires_approval'):
                # Create activity for manager if one is configured
                manager_group = self.env.ref('records_management.group_records_manager', raise_if_not_found=False)
                if manager_group:
                    audit_entry.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary=_('Review High-Impact Billing Change'),
                        note=_('Please review and approve the change to "%s" on billing config "%s".', field, config.name),
                        user_id=manager_group.users[0].id if manager_group.users else self.env.user.company_id.partner_id.user_ids[0].id if self.env.user.company_id.partner_id.user_ids else None
                    )
        return True

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('old_value', 'new_value', 'action_type')
    def _check_values_different(self):
        for record in self:
            if record.action_type == 'write' and record.old_value == record.new_value:
                raise ValidationError(_('Old and new values must be different for an update action.'))

    @api.constrains('approval_status', 'approved_by_id')
    def _check_approval_consistency(self):
        for record in self:
            if record.approval_status in ['approved', 'rejected'] and not record.approved_by_id:
                raise ValidationError(_('Approved or rejected entries must have a processing user.'))
