from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class RecordsBillingConfigAudit(models.Model):
    _name = 'records.billing.config.audit'
    _description = 'Records Billing Config Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'audit_date desc, id desc'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    code = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean()
    config_id = fields.Many2one()
    user_id = fields.Many2one()
    model_id = fields.Many2one()
    binding_model_id = fields.Many2one()
    groups_id = fields.Many2many()
    audit_date = fields.Datetime()
    action_type = fields.Selection()
    field_name = fields.Char()
    field_changed = fields.Char()
    old_value = fields.Text()
    new_value = fields.Text()
    change_reason = fields.Text()
    binding_view_types = fields.Char()
    ip_address = fields.Char()
    user_agent = fields.Text()
    session_id = fields.Char()
    requires_approval = fields.Boolean()
    approval_required = fields.Boolean()
    approved = fields.Boolean()
    approved_by_id = fields.Many2one()
    approved_by = fields.Many2one()
    approval_date = fields.Datetime()
    approval_status = fields.Selection()
    impact_level = fields.Selection()
    impact_assessment = fields.Text()
    affected_customers = fields.Integer()
    financial_impact = fields.Monetary()
    currency_id = fields.Many2one()
    compliance_checked = fields.Boolean()
    compliance_notes = fields.Text()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_name(self):
            """Compute audit entry name"""
            for record in self:
                parts = []
                if record.action_type:
                    action_dict = dict(record._fields['action_type'].selection)
                    parts.append(action_dict.get(record.action_type, record.action_type))

                if record.field_name:
                    parts.append("(%s)" % record.field_name)

                if record.audit_date:
                    parts.append(record.audit_date.strftime('%Y-%m-%d %H:%M'))

                record.name = " ".join(parts) if parts else "New Audit Entry":

    def _compute_display_name(self):
            """Compute display name"""
            for record in self:
                if record.user_id:
                    record.display_name = _("%(name)s by %(user)s", name=record.name, user=record.user_id.name)
                else:
                    record.display_name = record.name or "New Audit Entry"

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_approve_change(self):
            """Approve the audit entry"""
            self.ensure_one()
            if not self.requires_approval:
                raise UserError(_('This change does not require approval'))

            if self.approved:
                raise UserError(_('This change has already been approved'))

            self.write({)}
                'approved': True,
                'approved_by_id': self.env.user.id,
                'approval_date': fields.Datetime.now(),
                'approval_status': 'approved'

            self.message_post(body=_('Change approved'))


    def action_flag_for_review(self):
            """Flag entry for management review""":
            self.ensure_one()
            self.write({)}
                'requires_approval': True,
                'approval_status': 'pending'


            # Create activity for manager:
            self.activity_schedule()
                'mail.mail_activity_data_todo',
                summary=_('Review billing configuration change'),
                note=_('Please review this billing configuration change: %s', self.name),
                user_id=self.config_id.create_uid.id


            self.message_post(body=_('Entry flagged for management review')):
        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def log_change(self, config_id, action_type, field_name=None, old_value=None, new_value=None, reason=None):
            """Utility method to create audit log entries"""
            audit_vals = {}
                'config_id': config_id,
                'action_type': action_type,
                'field_name': field_name,
                'old_value': str(old_value) if old_value is not None else None,:
                'new_value': str(new_value) if new_value is not None else None,:
                'change_reason': reason,
                'user_id': self.env.user.id,


            # Determine impact level based on field changed
            if field_name in ['base_rate', 'storage_rate', 'retrieval_rate']:
                audit_vals.update({)}
                    'impact_level': 'high',
                    'requires_approval': True,
                    'approval_status': 'pending'

            elif field_name in ['active', 'customer_ids']:
                audit_vals.update({)}
                    'impact_level': 'medium',
                    'approval_status': 'pending'

            else:
                audit_vals.update({)}
                    'impact_level': 'low',
                    'approval_status': 'approved'


            return self.create(audit_vals)

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_values_different(self):
            """Ensure old and new values are actually different"""
            for record in self:
                if record.action_type == 'update' and record.old_value == record.new_value:
                    raise ValidationError(_('Old and new values must be different for update actions')):

    def _check_approval_consistency(self):
            """Validate approval fields consistency"""
            for record in self:
                if record.approved and not record.approved_by_id:
                    raise ValidationError(_('Approved entries must have an approver'))

                if not record.requires_approval and record.approved:
                    raise ValidationError(_('Cannot approve changes that do not require approval'))


    def _check_affected_customers(self):
            """Validate affected customers count"""
            for record in self:
                if record.affected_customers < 0:
                    raise ValidationError(_('Affected customers count cannot be negative'))
