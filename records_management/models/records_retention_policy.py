"""
records_retention_policy.py

This module defines the RecordsRetentionPolicy model for the Odoo Records Management system.
It manages document retention policies, destruction methods, compliance tracking, versioning,
and lifecycle management for physical and electronic records. The model supports hierarchical
policy structures, audit trails, review cycles, and integration with related business objects
such as document types, departments, and compliance logs.

Key Features:
- Policy definition and unique code generation
- Retention period and destruction method management
- Versioning and status tracking
- Compliance review and audit logging
- Relationships to documents, rules, and organizational entities
- Action methods for workflow transitions and UI integration
"""

# Stdlib first
import calendar
from datetime import date
import logging
# Odoo core imports next
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class RecordsRetentionPolicy(models.Model):
    """
    Records Retention Policy
    Manages document retention, destruction, compliance, and lifecycle for records management.
    """
    _name = 'records.retention.policy'
    _description = 'Records Retention Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # === CORE IDENTIFICATION ===
    name = fields.Char(string="Policy Name", required=True, tracking=True)
    DEFAULT_CODE = 'New'
    code = fields.Char(
        string="Policy Code",
        required=True,
        copy=False,
        readonly=True,
        default=DEFAULT_CODE,
        tracking=True
    )
    default_code = fields.Char(
        string="Default Code",
        copy=False,
        help="Default identification code for the retention policy"
    )
    sequence = fields.Integer(string='Sequence', default=10)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    # Contextual label disambiguation (Batch 2)
    description = fields.Text(string="Policy Description")
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Policy Owner", default=lambda self: self.env.user, tracking=True)

    # === RETENTION & DESTRUCTION ===
    retention_unit = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years'),
        ('indefinite', 'Indefinite')
    ], string="Retention Unit", default='years', required=True, tracking=True)
    retention_period = fields.Integer(string="Retention Period", default=7, tracking=True)
    retention_years = fields.Integer(string='Retention Years', compute='_compute_retention_years', store=True, readonly=True)
    destruction_method = fields.Selection([
        ('shred', 'Shredding'),
        ('pulp', 'Pulping'),
        ('incinerate', 'Incineration'),
        ('disintegrate', 'Disintegration'),
    ], string="Destruction Method", default='shred', tracking=True)

    # === STATUS & VERSIONING (example of using Selection instead of many booleans) ===
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ], string="Status", default='draft', required=True, tracking=True)

    # === RELATIONSHIPS ===
    rule_ids = fields.One2many('records.retention.rule', 'policy_id', string="Retention Rules")
    document_type_id = fields.Many2one('records.document.type', string='Document Type')
    partner_id = fields.Many2one('res.partner', string='Customer')
    department_id = fields.Many2one('hr.department', string='Department')
    category_id = fields.Many2one('records.category', string='Category')
    branch_id = fields.Many2one('res.company', string='Operating Unit')
    document_ids = fields.One2many('records.document', 'retention_policy_id', string='Documents')
    audit_log_ids = fields.One2many('records.audit.log', 'policy_id', string='Audit Log')
    child_policy_ids = fields.One2many('records.retention.policy', 'parent_policy_id', string='Child Policies')
    parent_policy_id = fields.Many2one('records.retention.policy', string='Parent Policy')
    version_ids = fields.One2many('records.retention.policy.version', 'policy_id', string='Policy Versions')
    template_id = fields.Many2one('records.retention.policy', string='Template')
    destruction_approver_ids = fields.Many2many(
        'res.users',
        relation='records_retention_policy_destruction_approver_rel',
        column1='policy_id',
        column2='user_id',
        string='Destruction Approvers'
    )
    tag_ids = fields.Many2many(
        'records.tag',
        relation='records_retention_policy_tag_rel',
        column1='policy_id',
        column2='tag_id',
        string='Tags'
    )
    country_ids = fields.Many2many(
        'res.country',
        relation='records_retention_policy_country_rel',
        column1='policy_id',
        column2='country_id',
        string='Applicable Countries'
    )
    state_ids = fields.Many2many(
        'res.country.state',
        relation='records_retention_policy_state_rel',
        column1='policy_id',
        column2='state_id',
        string='Applicable States'
    )
    storage_location_id = fields.Many2one('records.location', string='Storage Location')

    # === COMPUTED COUNTS & STATS ===
    rule_count = fields.Integer(string="Rule Count", compute='_compute_counts')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count')
    version_count = fields.Integer(string="Version Count", compute='_compute_counts')
    policy_level = fields.Integer(string='Policy Level', compute='_compute_policy_level')

    # === REVIEW & COMPLIANCE ===
    review_frequency = fields.Selection([
        ('quarterly', 'Quarterly'),
        ('biannual', 'Biannual'),
        ('annual', 'Annual'),
        ('none', 'None'),
    ], string="Review Frequency", default='annual', tracking=True)
    last_review_date = fields.Date(string="Last Review Date", readonly=True)
    next_review_date = fields.Date(string="Next Review Date", compute='_compute_next_review_date', store=True)
    review_cycle = fields.Integer(string='Review Cycle (days)')
    last_review_by_id = fields.Many2one('res.users', string='Last Reviewed By')
    next_reviewer_id = fields.Many2one('res.users', string='Next Reviewer')
    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('unknown', 'Unknown')
    ], string='Compliance Status')
    compliance_notes = fields.Text(string='Compliance Notes')
    compliance_check_date = fields.Date(string='Compliance Check Date')
    compliance_checker_id = fields.Many2one('res.users', string='Compliance Checker')
    is_compliant = fields.Boolean(string='Is Compliant')

    # === POLICY FLAGS & STATUS TRACKING ===
    is_default = fields.Boolean(string='Is Default Policy')
    is_legal_hold = fields.Boolean(string='Legal Hold')
    legal_hold_reason = fields.Text(string='Legal Hold Reason')
    is_template = fields.Boolean(string='Is Template')
    is_global = fields.Boolean(string='Is Global')
    is_approved = fields.Boolean(string='Is Approved')
    is_rejected = fields.Boolean(string='Is Rejected')
    is_pending_approval = fields.Boolean(string='Pending Approval')
    is_pending_review = fields.Boolean(string='Pending Review')
    is_pending_destruction = fields.Boolean(string='Pending Destruction')
    is_under_legal_hold = fields.Boolean(string='Under Legal Hold')
    is_under_review = fields.Boolean(string='Under Review')
    is_under_destruction = fields.Boolean(string='Under Destruction')
    is_expired = fields.Boolean(string='Is Expired')
    is_overdue = fields.Boolean(string='Is Overdue')
    is_archived = fields.Boolean(string='Is Archived')
    is_restored = fields.Boolean(string='Is Restored')
    is_deleted = fields.Boolean(string='Is Deleted')
    is_purged = fields.Boolean(string='Is Purged')
    is_locked = fields.Boolean(string='Is Locked')
    is_unlocked = fields.Boolean(string='Is Unlocked')
    is_versioned = fields.Boolean(string='Is Versioned')
    is_latest_version = fields.Boolean(string='Is Latest Version')
    is_major_version = fields.Boolean(string='Is Major Version')
    is_minor_version = fields.Boolean(string='Is Minor Version')
    is_draft = fields.Boolean(string='Is Draft')
    is_published = fields.Boolean(string='Is Published')
    is_unpublished = fields.Boolean(string='Is Unpublished')
    is_superseded = fields.Boolean(string='Is Superseded')
    is_effective = fields.Boolean(string='Is Effective')
    is_ineffective = fields.Boolean(string='Is Ineffective')
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

    # === DATES & AUDIT TRAIL ===
    expiration_date = fields.Date(string='Expiration Date')
    overdue_days = fields.Integer(string='Overdue Days')
    next_action_date = fields.Date(string='Next Action Date')
    next_action = fields.Selection([('review', 'Review'), ('destroy', 'Destroy')], string='Next Action')
    related_regulation = fields.Char(string='Related Regulation')
    approved_by_id = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Date(string='Approval Date')
    rejection_reason = fields.Text(string='Rejection Reason')
    rejected_by_id = fields.Many2one('res.users', string='Rejected By')
    rejection_date = fields.Date(string='Rejection Date')
    archived_by_id = fields.Many2one('res.users', string='Archived By')
    archived_date = fields.Date(string='Archived Date')
    restored_by_id = fields.Many2one('res.users', string='Restored By')
    restored_date = fields.Date(string='Restored Date')
    deleted_by_id = fields.Many2one('res.users', string='Deleted By')
    deleted_date = fields.Date(string='Deleted Date')
    purged_by_id = fields.Many2one('res.users', string='Purged By')
    purged_date = fields.Date(string='Purged Date')
    locked_by_id = fields.Many2one('res.users', string='Locked By')
    locked_date = fields.Date(string='Locked Date')
    unlocked_by_id = fields.Many2one('res.users', string='Unlocked By')
    unlocked_date = fields.Date(string='Unlocked Date')
    published_by_id = fields.Many2one('res.users', string='Published By')
    published_date = fields.Date(string='Published Date')
    unpublished_by_id = fields.Many2one('res.users', string='Unpublished By')
    unpublished_date = fields.Date(string='Unpublished Date')
    superseded_by_id = fields.Many2one('records.retention.policy', string='Superseded By')
    supersedes_id = fields.Many2one('records.retention.policy', string='Supersedes')
    effective_date = fields.Date(string='Effective Date')
    ineffective_date = fields.Date(string='Ineffective Date')
    version = fields.Integer(
        string='Version',
        help='Indicates the version number of the policy for tracking changes and versioning history.'
    )

    # === SQL CONSTRAINTS ===
    _sql_constraints = [
        ('name_company_uniq', 'unique (name, company_id)', 'Policy Name must be unique per company!'),
        ('code_company_uniq', 'unique (code, company_id)', 'Policy Code must be unique per company!'),
    ]

    # === ORM OVERRIDES ===
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate code if not provided."""
        for vals in vals_list:
            if vals.get('code', self.DEFAULT_CODE) == self.DEFAULT_CODE:
                vals['code'] = self.env['ir.sequence'].next_by_code('records.retention.policy') or self.DEFAULT_CODE
        return super().create(vals_list)

    def copy(self, default=None):
        """Duplicate policy as draft, reset code and version history."""
        self.ensure_one()
        default = dict(default or {})
        default.update({
            # Adjusted to pass parameter inside _() per linter requirement
            'name': _("%s (Copy)", self.name),
            'code': self.DEFAULT_CODE,
            'state': 'draft',
            'version_ids': [],
            'last_review_date': False,
        })
        return super().copy(default)
    @api.depends('name', 'code', 'default_code')
    def _compute_display_name(self):
        """Display name as [CODE] Name if code is set."""
        for policy in self:
            policy.display_name = f"[{policy.code}] {policy.name}" if policy.code and policy.code != policy.DEFAULT_CODE else policy.name

    @api.depends('rule_ids', 'version_ids')
    def _compute_counts(self):
        """Compute rule and version counts."""
        for policy in self:
            policy.rule_count = len(policy.rule_ids)
            policy.version_count = len(policy.version_ids)

    current_version_id = fields.Many2one(
        'records.retention.policy.version',
        string='Current Version',
        compute='_compute_current_version',
        store=True,
        readonly=True
    )

    @api.depends('version_ids.state')
    def _compute_current_version(self):
        """Get current active version."""
        for policy in self:
            active_version = policy.version_ids.filtered(lambda v: v.state == 'active')
            policy.current_version_id = active_version[0] if active_version else False

    def _add_months(self, dt, months):
        """Safe month adder without external deps (replaces dateutil.relativedelta)."""
        if not dt or not months:
            return dt
        # Compute target year/month
        total = (dt.month - 1) + months
        year = dt.year + total // 12
        month = (total % 12) + 1
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, min(dt.day, last_day))

    @api.depends('last_review_date', 'review_frequency')
    def _compute_next_review_date(self):
        """Calculate next review date based on frequency (internal month math)."""
        months_map = {'quarterly': 3, 'biannual': 6, 'annual': 12}
        for policy in self:
            if policy.last_review_date and policy.review_frequency != 'none':
                months = months_map.get(policy.review_frequency)
                policy.next_review_date = self._add_months(policy.last_review_date, months) if months else False
            else:
                policy.next_review_date = False

    @api.depends('document_ids')
    def _compute_document_count(self):
        """Compute the number of documents linked to this policy."""
        for policy in self:
            policy.document_count = len(policy.document_ids)
    @api.depends('parent_policy_id')
    def _compute_policy_level(self):
        """Compute policy level (hierarchy depth) with circular reference safeguard and batch caching."""
        # Cache to avoid redundant traversals in batch
        cache = {}
        for policy in self:
            if policy.id in cache:
                policy.policy_level = cache[policy.id]
                continue
            visited = set()
            current = policy
            level = 1
            while current.parent_policy_id:
                parent_id = current.parent_policy_id.id
                if parent_id in visited:
                    # Circular reference detected, break to prevent infinite recursion
                    break
                visited.add(parent_id)
                if parent_id in cache:
                    level += cache[parent_id] - 1
                    break
                level += 1
                current = current.parent_policy_id
            policy.policy_level = level
            cache[policy.id] = level

    @api.depends('retention_period', 'retention_unit')
    def _compute_retention_years(self):
        """Compute retention period in years (as float for precision)."""
        for policy in self:
            if policy.retention_unit == 'years':
                policy.retention_years = policy.retention_period
            elif policy.retention_unit == 'months':
                policy.retention_years = policy.retention_period / 12
            elif policy.retention_unit == 'weeks':
                policy.retention_years = policy.retention_period / 52
            elif policy.retention_unit == 'days':
                policy.retention_years = policy.retention_period / 365
            elif policy.retention_unit == 'indefinite':
                policy.retention_years = 0
            else:
                _logger.warning(f"Unsupported retention unit '{policy.retention_unit}' for policy '{policy.name}'. Set retention_years to 0.")
                policy.retention_years = 0

    # Class-level constant for retention period defaults
    RETENTION_PERIOD_DEFAULTS = {
        'days': 30,
        'weeks': 4,
        'months': 12,
        'years': 7,
    }
    _retention_period_was_indefinite = fields.Boolean(string='Was Indefinite', default=False)

    @api.onchange('retention_unit')
    def _onchange_retention_unit(self):
        """Set retention period to 0 if indefinite, or restore default if changed back from indefinite, but do not override user input."""
        if self.retention_unit == 'indefinite':
            self.retention_period = 0
            self._retention_period_was_indefinite = True
    # Computed field for expiration status
    # is_expired field is already defined above, so this duplicate definition is removed.
            if not self.retention_period:
                self.retention_period = self.RETENTION_PERIOD_DEFAULTS.get(self.retention_unit, 1)

    # Computed field for expiration status
    is_expired = fields.Boolean(
        string='Is Expired',
        compute='_compute_is_expired',
        store=True,
        help='Indicates if the retention policy has expired'
    )

    @api.depends('expiration_date', 'state')
    def _compute_is_expired(self):
        """Compute if the retention policy is expired"""
        today = date.today()
        for record in self:
            if record.expiration_date and record.state in ['active', 'under_review']:
                record.is_expired = record.expiration_date < today
            else:
                record.is_expired = False

    # === ACTION METHODS ===
    def action_activate(self):
        """Activate policy if it has at least one rule."""
        self.ensure_one()
        if not self.rule_ids:
            raise UserError(_("You cannot activate a policy with no retention rules."))
        self.write({'state': 'active'})
        self.message_post(body=_("Policy activated."))

    def action_archive(self):
        """Archive the policy."""
        self.ensure_one()
        self.write({'active': False, 'state': 'archived'})
        self.message_post(body=_("Policy archived."))

    def action_set_to_draft(self):
        """Set policy state to draft."""
        self.ensure_one()
        self.write({'state': 'draft'})

    def action_create_new_version(self):
        """Open wizard to create a new version of this policy."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create New Version'),
            'res_model': 'records.policy.version.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_policy_id': self.id}
        }

    def action_view_rules(self):
        """Show all retention rules for this policy."""
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
        """Show all versions for this policy."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Policy Versions'),
            'res_model': 'records.policy.version',
            'view_mode': 'tree,form',
            'domain': [('policy_id', '=', self.id)],
            'context': {'default_policy_id': self.id}
        }
