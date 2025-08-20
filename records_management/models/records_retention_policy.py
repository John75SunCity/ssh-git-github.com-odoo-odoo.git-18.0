from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta


class RecordsRetentionPolicy(models.Model):
    _name = 'records.retention.policy'
    _description = 'Records Retention Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Policy Name", required=True, tracking=True)
    code = fields.Char(string="Policy Code", required=True, copy=False, readonly=True, default=lambda self: _('New'), tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    user_id = fields.Many2one('res.users', string="Policy Owner", default=lambda self: self.env.user, tracking=True)
    description = fields.Text(string="Description")

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    rule_ids = fields.One2many('records.retention.rule', 'policy_id', string="Retention Rules")
    version_ids = fields.One2many('records.policy.version', 'policy_id', string="Version History")

    # ============================================================================
    # COMPUTED COUNTS & STATS
    # ============================================================================
    rule_count = fields.Integer(string="Rule Count", compute='_compute_counts')
    version_count = fields.Integer(string="Version Count", compute='_compute_counts')
    current_version_id = fields.Many2one('records.policy.version', string="Current Active Version", compute='_compute_current_version', store=True)

    # ============================================================================
    # REVIEW & COMPLIANCE
    # ============================================================================
    review_frequency = fields.Selection([
        ('quarterly', 'Quarterly'),
        ('biannual', 'Biannual'),
        ('annual', 'Annual'),
        ('none', 'None'),
    ], string="Review Frequency", default='annual', tracking=True)
    last_review_date = fields.Date(string="Last Review Date", readonly=True)
    next_review_date = fields.Date(string="Next Review Date", compute='_compute_next_review_date', store=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('records.retention.policy') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends('rule_ids', 'version_ids')
    def _compute_counts(self):
        for policy in self:
            policy.rule_count = len(policy.rule_ids)
            policy.version_count = len(policy.version_ids)

    @api.depends('version_ids.state')
    def _compute_current_version(self):
        for policy in self:
            active_version = policy.version_ids.filtered(lambda v: v.state == 'active')
            policy.current_version_id = active_version[0] if active_version else False

    @api.depends('last_review_date', 'review_frequency')
    def _compute_next_review_date(self):
        for policy in self:
            if policy.last_review_date and policy.review_frequency != 'none':
                months_map = {'quarterly': 3, 'biannual': 6, 'annual': 12}
                policy.next_review_date = policy.last_review_date + relativedelta(months=months_map[policy.review_frequency])
            else:
                policy.next_review_date = False

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        self.ensure_one()
        if not self.rule_ids:
            raise UserError(_("You cannot activate a policy with no retention rules."))
        self.write({'state': 'active'})
        self.message_post(body=_("Policy activated."))

    def action_archive(self):
        self.write({'state': 'archived', 'active': False})
        self.message_post(body=_("Policy archived."))

    def action_set_to_draft(self):
        self.write({'state': 'draft', 'active': True})
        self.message_post(body=_("Policy set to draft."))

    def action_create_new_version(self):
        """Opens a wizard to create a new version of this policy."""
        self.ensure_one()
        # This would typically open a wizard. For now, it's a placeholder.
        # You would pass context to the wizard with the policy_id.
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create New Version'),
            'res_model': 'records.policy.version.wizard', # Assumes a wizard exists
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_policy_id': self.id}
        }

    def action_view_rules(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Retention Rules'),
            'res_model': 'records.retention.rule',
            'view_mode': 'tree,form',
            'domain': [('policy_id', '=', self.id)],
            'context': {'default_policy_id': self.id}
        }

    def action_view_versions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Policy Versions'),
            'res_model': 'records.policy.version',
            'view_mode': 'tree,form',
            'domain': [('policy_id', '=', self.id)],
            'context': {'default_policy_id': self.id}
        }
