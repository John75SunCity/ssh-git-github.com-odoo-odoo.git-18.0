# -*- coding: utf-8 -*-

Records Billing Config Audit Model

Audit trail for billing configuration changes.:
    pass


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsBillingConfigAudit(models.Model):
    """Records Billing Config Audit"""

    _name = "records.billing.config.audit"
    _description = "Records Billing Config Audit"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "audit_date desc, id desc"
    _rec_name = "display_name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Audit Entry",
        compute='_compute_name',
        store=True,
        help="Computed name based on action and date"


    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        help="Display name for the audit entry":


    code = fields.Char(
        string='Configuration Code',
        help='Unique code for this configuration',:
        index=True


    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True


    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this audit entry"


        # ============================================================================
    # RELATIONSHIP FIELDS
        # ============================================================================
    config_id = fields.Many2one(
        "records.billing.config",
        string="Billing Configuration",
        required=True,
        ondelete="cascade",
        index=True,
        help="Parent billing configuration"


    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        default=lambda self: self.env.user,
        help="User who made the change"


    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        help='Target model for configuration':


    binding_model_id = fields.Many2one(
        'ir.model',
        string='Target Model',
        help='Target model for binding operations':


    groups_id = fields.Many2many(
        'res.groups',
        string='User Groups',
        help='Groups that can access this configuration'


        # ============================================================================
    # AUDIT DETAILS
        # ============================================================================
    audit_date = fields.Datetime(
        string="Audit Date",
        default=fields.Datetime.now,
        required=True,
        index=True,
        help="Date and time of the change"


    ,
    action_type = fields.Selection([))
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('activate', 'Activated'),
        ('deactivate', 'Deactivated'),
        ('rate_change', 'Rate Changed'),
        ('customer_assigned', 'Customer Assigned'),
        ('customer_removed', 'Customer Removed'),
        ('other', 'Other')


    field_name = fields.Char(
        string="Field Changed",
        help="Name of the field that was changed"


    field_changed = fields.Char(
        string='Field Changed Alt',
        help='Alternative field name reference'


    old_value = fields.Text(
        string="Old Value",
        help="Previous value before change"


    new_value = fields.Text(
        string="New Value",
        help="New value after change"


    change_reason = fields.Text(
        string="Change Reason",
        help="Reason for the change":


    binding_view_types = fields.Char(
        string='View Types',
        help='Comma-separated list of view types'


        # ============================================================================
    # METADATA
        # ============================================================================
    ip_address = fields.Char(
        string="IP Address",
        help="IP address of the user making the change"


    user_agent = fields.Text(
        string="User Agent",
        help="Browser/client information"


    session_id = fields.Char(
        string="Session ID",
        help="User session identifier"


        # ============================================================================
    # APPROVAL AND VERIFICATION
        # ============================================================================
    requires_approval = fields.Boolean(
        string="Requires Approval",
        default=False,
        help="Whether this change requires managerial approval"


    approval_required = fields.Boolean(
        string='Approval Required Alt',
        help='Alternative approval requirement field'


    approved = fields.Boolean(
        string="Approved",
        default=False,
        tracking=True,
        help="Whether this change has been approved"


    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        help="Manager who approved the change"


    approved_by = fields.Many2one(
        'res.users',
        string='Approved By Alt',
        help='Alternative approved by reference'


    approval_date = fields.Datetime(
        string="Approval Date",
        help="Date when change was approved"


    ,
    approval_status = fields.Selection([))
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')


        # ============================================================================
    # IMPACT ASSESSMENT
        # ============================================================================
    impact_level = fields.Selection([))
        ('low', 'Low Impact'),
        ('medium', 'Medium Impact'),
        ('high', 'High Impact'),
        ('critical', 'Critical Impact')


    impact_assessment = fields.Text(
        string='Impact Assessment',
        help='Assessment of change impact'


    affected_customers = fields.Integer(
        string="Affected Customers",
        default=0,
        help="Number of customers affected by this change"


    financial_impact = fields.Monetary(
        string="Financial Impact",
        currency_field="currency_id",
        help="Estimated financial impact of the change"


    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True


        # ============================================================================
    # COMPLIANCE
        # ============================================================================
    compliance_checked = fields.Boolean(
        string="Compliance Checked",
        default=False,
        help="Whether compliance implications were reviewed"


    compliance_notes = fields.Text(
        string="Compliance Notes",
        ,
    help="Notes about compliance implications"


        # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance):
    activity_ids = fields.One2many("mail.activity", "res_id",,
    string="Activities"),
    message_follower_ids = fields.One2many("mail.followers", "res_id",,
    string="Followers"),
    message_ids = fields.One2many("mail.message", "res_id",,
    string="Messages")

        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends('action_type', 'audit_date', 'field_name')
    def _compute_name(self):
        """Compute audit entry name"""
        for record in self:
            parts = [)
            if record.action_type:
                action_dict = dict(record._fields['action_type'].selection)
                parts.append(action_dict.get(record.action_type, record.action_type))

            if record.field_name:
                parts.append("(%s)" % record.field_name)

            if record.audit_date:
                parts.append(record.audit_date.strftime('%Y-%m-%d %H:%M'))

            record.name = " ".join(parts) if parts else "New Audit Entry":
    @api.depends('name', 'user_id')
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
    @api.model
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
    @api.constrains('old_value', 'new_value')
    def _check_values_different(self):
        """Ensure old and new values are actually different"""
        for record in self:
            if record.action_type == 'update' and record.old_value == record.new_value:
                raise ValidationError(_('Old and new values must be different for update actions')):
    @api.constrains('requires_approval', 'approved', 'approved_by_id')
    def _check_approval_consistency(self):
        """Validate approval fields consistency"""
        for record in self:
            if record.approved and not record.approved_by_id:
                raise ValidationError(_('Approved entries must have an approver'))

            if not record.requires_approval and record.approved:
                raise ValidationError(_('Cannot approve changes that do not require approval'))

    @api.constrains('affected_customers')
    def _check_affected_customers(self):
        """Validate affected customers count"""
        for record in self:
            if record.affected_customers < 0:
                raise ValidationError(_('Affected customers count cannot be negative'))
))))))))))))))))))))))))))))
