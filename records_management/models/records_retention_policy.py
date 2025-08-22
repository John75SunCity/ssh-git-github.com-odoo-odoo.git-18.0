from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta


class RecordsRetentionPolicy(models.Model):
    _name = 'records.retention.policy'
    _description = 'Records Retention Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)

    retention_unit = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years'),
        ('indefinite', 'Indefinite')
    ], string="Retention Unit", default='years', required=True, tracking=True)
    retention_period = fields.Integer(string="Retention Period", default=7, tracking=True)
    destruction_method = fields.Selection([
        ('shred', 'Shredding'),
        ('pulp', 'Pulping'),
        ('incinerate', 'Incineration'),
        ('disintegrate', 'Disintegration'),
    ], string="Destruction Method", default='shred', tracking=True)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Policy Name", required=True, tracking=True)
    code = fields.Char(string="Policy Code", required=True, copy=False, readonly=True, default=lambda self: _('New'), tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
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

    # New Fields from analysis
    document_type_id = fields.Many2one('records.document.type', string='Document Type')
    partner_id = fields.Many2one('res.partner', string='Customer')
    department_id = fields.Many2one('hr.department', string='Department')
    category_id = fields.Many2one('records.category', string='Category')
    retention_type = fields.Selection([('permanent', 'Permanent'), ('temporary', 'Temporary')], string='Retention Type')
    retention_event = fields.Selection([('creation', 'Creation Date'), ('end_of_year', 'End of Fiscal Year'), ('last_activity', 'Last Activity Date')], string='Retention Event')
    is_legal_hold = fields.Boolean(string='Legal Hold')
    legal_hold_reason = fields.Text(string='Legal Hold Reason')
    is_active = fields.Boolean(string='Is Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    branch_id = fields.Many2one('operating.unit', string='Operating Unit')
    document_ids = fields.One2many('records.document', 'retention_policy_id', string='Documents')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count')
    next_action_date = fields.Date(string='Next Action Date')
    next_action = fields.Selection([('review', 'Review'), ('destroy', 'Destroy')], string='Next Action')
    destruction_approver_ids = fields.Many2many('res.users', string='Destruction Approvers')
    is_default = fields.Boolean(string='Is Default Policy')
    audit_log_ids = fields.One2many('records.audit.log', 'policy_id', string='Audit Log')
    related_regulation = fields.Char(string='Related Regulation')
    storage_location_id = fields.Many2one('stock.location', string='Storage Location')
    is_template = fields.Boolean(string='Is Template')
    template_id = fields.Many2one('records.retention.policy', string='Template')
    child_policy_ids = fields.One2many('records.retention.policy', 'parent_policy_id', string='Child Policies')
    parent_policy_id = fields.Many2one('records.retention.policy', string='Parent Policy')
    policy_level = fields.Integer(string='Policy Level', compute='_compute_policy_level')
    is_global = fields.Boolean(string='Is Global')
    country_ids = fields.Many2many('res.country', string='Applicable Countries')
    state_ids = fields.Many2many('res.country.state', string='Applicable States')
    tag_ids = fields.Many2many('records.tag', string='Tags')
    priority = fields.Selection([('0', 'Low'), ('1', 'Medium'), ('2', 'High')], string='Priority')
    review_cycle = fields.Integer(string='Review Cycle (days)')
    last_review_by_id = fields.Many2one('res.users', string='Last Reviewed By')
    next_reviewer_id = fields.Many2one('res.users', string='Next Reviewer')
    is_approved = fields.Boolean(string='Is Approved')
    approved_by_id = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Date(string='Approval Date')
    rejection_reason = fields.Text(string='Rejection Reason')
    is_rejected = fields.Boolean(string='Is Rejected')
    rejected_by_id = fields.Many2one('res.users', string='Rejected By')
    rejection_date = fields.Date(string='Rejection Date')
    is_pending_approval = fields.Boolean(string='Pending Approval')
    is_pending_review = fields.Boolean(string='Pending Review')
    is_pending_destruction = fields.Boolean(string='Pending Destruction')
    is_under_legal_hold = fields.Boolean(string='Under Legal Hold')
    is_under_review = fields.Boolean(string='Under Review')
    is_under_destruction = fields.Boolean(string='Under Destruction')
    is_expired = fields.Boolean(string='Is Expired')
    expiration_date = fields.Date(string='Expiration Date')
    is_overdue = fields.Boolean(string='Is Overdue')
    overdue_days = fields.Integer(string='Overdue Days')
    is_compliant = fields.Boolean(string='Is Compliant')
    compliance_status = fields.Selection([('compliant', 'Compliant'), ('non_compliant', 'Non-Compliant'), ('unknown', 'Unknown')], string='Compliance Status')
    compliance_notes = fields.Text(string='Compliance Notes')
    compliance_check_date = fields.Date(string='Compliance Check Date')
    compliance_checker_id = fields.Many2one('res.users', string='Compliance Checker')
    is_archived = fields.Boolean(string='Is Archived')
    archived_by_id = fields.Many2one('res.users', string='Archived By')
    archived_date = fields.Date(string='Archived Date')
    is_restored = fields.Boolean(string='Is Restored')
    restored_by_id = fields.Many2one('res.users', string='Restored By')
    restored_date = fields.Date(string='Restored Date')
    is_deleted = fields.Boolean(string='Is Deleted')
    deleted_by_id = fields.Many2one('res.users', string='Deleted By')
    deleted_date = fields.Date(string='Deleted Date')
    is_purged = fields.Boolean(string='Is Purged')
    purged_by_id = fields.Many2one('res.users', string='Purged By')
    purged_date = fields.Date(string='Purged Date')
    is_locked = fields.Boolean(string='Is Locked')
    locked_by_id = fields.Many2one('res.users', string='Locked By')
    locked_date = fields.Date(string='Locked Date')
    is_unlocked = fields.Boolean(string='Is Unlocked')
    unlocked_by_id = fields.Many2one('res.users', string='Unlocked By')
    unlocked_date = fields.Date(string='Unlocked Date')
    is_versioned = fields.Boolean(string='Is Versioned')
    version = fields.Integer(string='Version')
    is_latest_version = fields.Boolean(string='Is Latest Version')
    is_major_version = fields.Boolean(string='Is Major Version')
    is_minor_version = fields.Boolean(string='Is Minor Version')
    is_draft = fields.Boolean(string='Is Draft')
    is_published = fields.Boolean(string='Is Published')
    published_by_id = fields.Many2one('res.users', string='Published By')
    published_date = fields.Date(string='Published Date')
    is_unpublished = fields.Boolean(string='Is Unpublished')
    unpublished_by_id = fields.Many2one('res.users', string='Unpublished By')
    unpublished_date = fields.Date(string='Unpublished Date')
    is_superseded = fields.Boolean(string='Is Superseded')
    superseded_by_id = fields.Many2one('records.retention.policy', string='Superseded By')
    supersedes_id = fields.Many2one('records.retention.policy', string='Supersedes')
    is_effective = fields.Boolean(string='Is Effective')
    effective_date = fields.Date(string='Effective Date')
    is_ineffective = fields.Boolean(string='Is Ineffective')
    ineffective_date = fields.Date(string='Ineffective Date')
    is_current = fields.Boolean(string='Is Current')
    is_historical = fields.Boolean(string='Is Historical')
    is_future = fields.Boolean(string='Is Future')
    is_active_version = fields.Boolean(string='Is Active Version')
    is_inactive_version = fields.Boolean(string='Is Inactive Version')
    is_draft_version = fields.Boolean(string='Is Draft Version')
    is_approved_version = fields.Boolean(string='Is Approved Version')
    is_rejected_version = fields.Boolean(string='Is Rejected Version')
    is_pending_approval_version = fields.Boolean(string='Is Pending Approval Version')
    is_pending_review_version = fields.Boolean(string='Is Pending Review Version')
    is_under_review_version = fields.Boolean(string='Is Under Review Version')
    is_expired_version = fields.Boolean(string='Is Expired Version')
    is_overdue_version = fields.Boolean(string='Is Overdue Version')
    is_compliant_version = fields.Boolean(string='Is Compliant Version')
    is_non_compliant_version = fields.Boolean(string='Is Non-Compliant Version')
    is_unknown_compliance_version = fields.Boolean(string='Is Unknown Compliance Version')
    is_locked_version = fields.Boolean(string='Is Locked Version')
    is_unlocked_version = fields.Boolean(string='Is Unlocked Version')
    is_versioned_version = fields.Boolean(string='Is Versioned Version')
    is_latest_version_version = fields.Boolean(string='Is Latest Version Version')
    is_major_version_version = fields.Boolean(string='Is Major Version Version')
    is_minor_version_version = fields.Boolean(string='Is Minor Version Version')
    is_draft_version_version = fields.Boolean(string='Is Draft Version Version')
    is_published_version_version = fields.Boolean(string='Is Published Version Version')
    is_unpublished_version_version = fields.Boolean(string='Is Unpublished Version Version')
    is_superseded_version = fields.Boolean(string='Is Superseded Version')
    is_effective_version = fields.Boolean(string='Is Effective Version')
    is_ineffective_version = fields.Boolean(string='Is Ineffective Version')
    is_current_version = fields.Boolean(string='Is Current Version')
    is_historical_version = fields.Boolean(string='Is Historical Version')
    is_future_version = fields.Boolean(string='Is Future Version')

    _sql_constraints = [
        ('name_company_uniq', 'unique (name, company_id)', 'Policy Name must be unique per company!'),
        ('code_company_uniq', 'unique (code, company_id)', 'Policy Code must be unique per company!'),
    ]

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('records.retention.policy') or _('New')
        return super().create(vals_list)

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.update({
            'name': _('%s (Copy)', self.name),
            'code': _('New'),
            'state': 'draft',
            'version_ids': [],
            'last_review_date': False,
        })
        return super().copy(default)

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends('name', 'code')
    def _compute_display_name(self):
        for policy in self:
            policy.display_name = f"[{policy.code}] {policy.name}" if policy.code and policy.code != _('New') else policy.name

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

    @api.onchange('retention_unit')
    def _onchange_retention_unit(self):
        if self.retention_unit == 'indefinite':
            self.retention_period = 0

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
        self.ensure_one()
        return super().action_archive()

    def action_set_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})

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
