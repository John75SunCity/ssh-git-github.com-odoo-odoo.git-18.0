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
from dateutil.relativedelta import relativedelta

# Odoo core imports next
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# Note: Translation warnings during module loading are expected
# for constraint definitions - this is non-blocking behavior


_logger = logging.getLogger(__name__)


class RecordsRetentionPolicy(models.Model):
    """Records Retention Policy

    Modernized version:
    - Removes legacy boolean mirror fields (is_approved, is_rejected, etc.) in favor of primary selection axes.
    - Introduces computed `review_state` (derived from expiration / next review metrics) and auxiliary computed metrics.
    - Adds semantic helper fields: retention_display, is_latest_version, overdue_days.
    - Provides smart button actions for documents & child policies.
    NOTE: If external modules relied on removed booleans, they must now pivot to selection fields
    (approval_state, publication_state, lifecycle_state, review_state) or explicit dates.
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
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one(comodel_name='res.users', string="Policy Owner", default=lambda self: self.env.user, tracking=True)

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

    # === STATUS & VERSIONING ===
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ], string="Status", default='draft', required=True, tracking=True)

    # === RELATIONSHIPS ===
    rule_ids = fields.One2many('records.retention.rule', 'policy_id', string="Retention Rules")
    document_type_id = fields.Many2one(comodel_name='records.document.type', string='Document Type')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer')
    department_id = fields.Many2one(comodel_name='hr.department', string='Department')
    category_id = fields.Many2one(comodel_name='records.category', string='Category')
    branch_id = fields.Many2one(comodel_name='res.company', string='Operating Unit')
    document_ids = fields.One2many('records.document', 'retention_policy_id', string='Documents')
    audit_log_ids = fields.One2many('records.audit.log', 'policy_id', string='Audit Log')
    child_policy_ids = fields.One2many('records.retention.policy', 'parent_policy_id', string='Child Policies')
    parent_policy_id = fields.Many2one(comodel_name='records.retention.policy', string='Parent Policy')
    version_ids = fields.One2many('records.retention.policy.version', 'policy_id', string='Policy Versions')
    template_id = fields.Many2one(comodel_name='records.retention.policy', string='Template')
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
    storage_location_id = fields.Many2one(comodel_name='records.location', string='Storage Location')

    # === COMPUTED COUNTS & STATS ===
    rule_count = fields.Integer(string="Rule Count", compute='_compute_counts')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count')
    version_count = fields.Integer(string="Version Count", compute='_compute_counts')
    policy_level = fields.Integer(string='Policy Level', compute='_compute_policy_level')
    retention_display = fields.Char(string='Retention', compute='_compute_retention_display', store=False)
    overdue_days = fields.Integer(string='Overdue Days', compute='_compute_overdue_days', store=False,
                                  help="Days past expiration or next review date (whichever first applied)")

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
    last_review_by_id = fields.Many2one(comodel_name='res.users', string='Last Reviewed By')
    next_reviewer_id = fields.Many2one(comodel_name='res.users', string='Next Reviewer')
    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('unknown', 'Unknown')
    ], string='Compliance Status')
    compliance_notes = fields.Text(string='Compliance Notes')
    compliance_check_date = fields.Date(string='Compliance Check Date')
    compliance_checker_id = fields.Many2one(comodel_name='res.users', string='Compliance Checker')
    is_compliant = fields.Boolean(string='Is Compliant')

    # === STATE AXES (Primary Workflow Dimensions) ===
    # Approval workflow state
    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    ], string="Approval State", default='draft', tracking=True,
       help="Current approval status of the retention policy")

    # Version management
    version_type = fields.Selection([
        ('major', 'Major Version'),
        ('minor', 'Minor Version'),
        ('patch', 'Patch Version'),
    ], string="Version Type", default='major',
       help="Type of version change for this policy")

    # Lifecycle management
    lifecycle_state = fields.Selection([
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
        ('purged', 'Purged'),
        ('restored', 'Restored'),
        ('locked', 'Locked'),
        ('unlocked', 'Unlocked'),
    ], string="Lifecycle State", default='active', tracking=True,
       help="Current lifecycle status of the retention policy")

    # Review and compliance state: see computed definition below; removed duplicate non-computed field.

    # Publication status
    publication_state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('unpublished', 'Unpublished'),
        ('effective', 'Effective'),
        ('ineffective', 'Ineffective'),
        ('superseded', 'Superseded'),
    ], string="Publication State", default='draft', tracking=True,
       help="Current publication status of the retention policy")

    # Timeline status (Optional – retained for forward planning / analytics)
    timeline_status = fields.Selection([
        ('current', 'Current'),
        ('historical', 'Historical'),
        ('future', 'Future'),
    ], string="Timeline Status", default='current', help="Temporal relevance of the policy (planning tool)")

    # Core configuration flags
    is_default = fields.Boolean(string='Is Default Policy',
                               help="Indicates if this is the default policy for new documents")
    is_template = fields.Boolean(string='Is Template',
                                help="Indicates if this policy serves as a template for new policies")
    is_global = fields.Boolean(string='Is Global',
                              help="Indicates if this policy applies globally across all departments")
    is_legal_hold = fields.Boolean(string='Legal Hold',
                                  help="Indicates if documents under this policy are under legal hold")
    legal_hold_reason = fields.Text(string='Legal Hold Reason')
    is_versioned = fields.Boolean(string='Is Versioned', default=True,
                                 help="Indicates if this policy supports versioning")
    is_latest_version = fields.Boolean(string='Is Latest Version', compute='_compute_is_latest_version', store=True,
                                      help="Automatically indicates if this record is the latest version")
    is_pending_destruction = fields.Boolean(string='Pending Destruction',
                                           help="Indicates if documents are pending destruction under this policy")
    # Backward compatibility NOTE: Former boolean derivative flags removed in refactor.
    # Domains and UI should now rely on the core selection fields or computed review_state.

    # === COMPUTED REVIEW STATE (Replaces multiple scattered booleans) ===
    review_state = fields.Selection([
        ('current', 'Current'),
        ('pending_review', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('overdue', 'Overdue'),
        ('expired', 'Expired'),
    ], string="Review State", compute='_compute_review_state', store=True, tracking=True,
       help="Derived review lifecycle based on expiration & review scheduling.")

    # Removed legacy boolean mirror compute blocks.

    # === DATES & AUDIT TRAIL ===
    expiration_date = fields.Date(string='Expiration Date')
    next_action_date = fields.Date(string='Next Action Date')
    next_action = fields.Selection([('review', 'Review'), ('destroy', 'Destroy')], string='Next Action')
    related_regulation = fields.Char(string='Related Regulation')
    approved_by_id = fields.Many2one(comodel_name='res.users', string='Approved By')
    approval_date = fields.Date(string='Approval Date')
    rejection_reason = fields.Text(string='Rejection Reason')
    rejected_by_id = fields.Many2one(comodel_name='res.users', string='Rejected By')
    rejection_date = fields.Date(string='Rejection Date')
    archived_by_id = fields.Many2one(comodel_name='res.users', string='Archived By')
    archived_date = fields.Date(string='Archived Date')
    restored_by_id = fields.Many2one(comodel_name='res.users', string='Restored By')
    restored_date = fields.Date(string='Restored Date')
    deleted_by_id = fields.Many2one(comodel_name='res.users', string='Deleted By')
    deleted_date = fields.Date(string='Deleted Date')
    purged_by_id = fields.Many2one(comodel_name='res.users', string='Purged By')
    purged_date = fields.Date(string='Purged Date')
    locked_by_id = fields.Many2one(comodel_name='res.users', string='Locked By')
    locked_date = fields.Date(string='Locked Date')
    unlocked_by_id = fields.Many2one(comodel_name='res.users', string='Unlocked By')
    unlocked_date = fields.Date(string='Unlocked Date')
    published_by_id = fields.Many2one(comodel_name='res.users', string='Published By')
    published_date = fields.Date(string='Published Date')
    unpublished_by_id = fields.Many2one(comodel_name='res.users', string='Unpublished By')
    unpublished_date = fields.Date(string='Unpublished Date')
    superseded_by_id = fields.Many2one(comodel_name='records.retention.policy', string='Superseded By')
    supersedes_id = fields.Many2one(comodel_name='records.retention.policy', string='Supersedes')
    effective_date = fields.Date(string='Effective Date')
    ineffective_date = fields.Date(string='Ineffective Date')
    version = fields.Integer(
        string='Version',
        help='Indicates the version number of the policy for tracking changes and versioning history.'
    )

    # === SQL CONSTRAINTS ===
    _name_company_uniq = models.Constraint('unique (name, company_id)', _('Policy Name must be unique per company!'))
    _code_company_uniq = models.Constraint('unique (code, company_id)', _('Policy Code must be unique per company!'))

    # === SMART STATE MANAGEMENT ===
    # Automatic state transitions based on actions and dates

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate code and set initial states."""
        for vals in vals_list:
            if vals.get('code', self.DEFAULT_CODE) == self.DEFAULT_CODE:
                vals['code'] = self.env['ir.sequence'].next_by_code('records.retention.policy') or self.DEFAULT_CODE

            # Set default states if not provided
            if 'approval_state' not in vals:
                vals['approval_state'] = 'draft'
            if 'lifecycle_state' not in vals:
                vals['lifecycle_state'] = 'active'
            if 'publication_state' not in vals:
                vals['publication_state'] = 'draft'

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
            if policy.last_review_date and policy.review_frequency not in ('none', False):
                months = months_map.get(policy.review_frequency)
                policy.next_review_date = self._add_months(policy.last_review_date, months) if months else False
            else:
                policy.next_review_date = False

    @api.depends('document_ids')
    def _compute_document_count(self):
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
        for policy in self:
            unit = policy.retention_unit
            value = policy.retention_period or 0
            if unit == 'years':
                policy.retention_years = value
            elif unit == 'months':
                policy.retention_years = value / 12.0
            elif unit == 'weeks':
                policy.retention_years = value / 52.0
            elif unit == 'days':
                policy.retention_years = value / 365.0
            elif unit == 'indefinite':
                policy.retention_years = 0
            else:
                _logger.warning("Unsupported retention unit '%s' for policy '%s'. Setting retention_years=0", unit, policy.name)
                policy.retention_years = 0

    def _compute_retention_display(self):
        for policy in self:
            if policy.retention_unit == 'indefinite':
                policy.retention_display = _('Indefinite')
            else:
                policy.retention_display = _('%s %s') % (policy.retention_period, dict(self._fields['retention_unit'].selection).get(policy.retention_unit, ''))

    @api.depends('expiration_date', 'next_review_date')
    def _compute_overdue_days(self):
        today = date.today()
        for policy in self:
            days = 0
            if policy.expiration_date and policy.expiration_date < today:
                days = (today - policy.expiration_date).days
            elif policy.next_review_date and policy.next_review_date < today:
                days = (today - policy.next_review_date).days
            policy.overdue_days = days

    @api.depends('version_ids.version', 'version_ids.state')
    def _compute_is_latest_version(self):
        for policy in self:
            if not policy.version_ids:
                policy.is_latest_version = True
                continue
            # Latest = highest version number among active or all? Using max numeric from version field if integer.
            try:
                max_version = max(v.version for v in policy.version_ids if isinstance(v.version, int)) if any(isinstance(v.version, int) for v in policy.version_ids) else False
            except Exception:
                max_version = False
            if max_version and policy.version == max_version:
                policy.is_latest_version = True
            else:
                # Fallback: mark current_version_id equivalence
                policy.is_latest_version = (policy.current_version_id and policy.current_version_id.policy_id.id == policy.id)

    @api.depends('expiration_date', 'next_review_date', 'state', 'approval_state', 'publication_state')
    def _compute_review_state(self):
        """Derive review_state based on key temporal fields and approval/publication context."""
        today = date.today()
        for policy in self:
            # Expired if expiration date passed and policy was active/published
            if policy.expiration_date and policy.expiration_date < today:
                policy.review_state = 'expired'
            elif policy.next_review_date and policy.next_review_date < today:
                policy.review_state = 'overdue'
            elif policy.approval_state == 'under_review':
                policy.review_state = 'under_review'
            else:
                policy.review_state = 'current'

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

    # Removed obsolete _compute_review_state_auto (logic merged into _compute_review_state)

    # === OPTIMIZED ACTION METHODS ===
    def action_activate(self):
        """Activate policy if it has at least one rule."""
        self.ensure_one()
        if not self.rule_ids:
            raise UserError(_("You cannot activate a policy with no retention rules."))
        self.write({
            'state': 'active',
            'approval_state': 'approved',  # activation implies approval
            'lifecycle_state': 'active',
            'publication_state': 'published',
            'effective_date': self.effective_date or date.today(),
        })
        self.message_post(body=_("Policy activated."))

    def action_archive(self):
        """Archive the policy."""
        self.ensure_one()
        self.write({
            'active': False,
            'state': 'archived',
            'lifecycle_state': 'archived'
        })
        self.message_post(body=_("Policy archived."))

    def action_set_to_draft(self):
        """Set policy state to draft."""
        self.ensure_one()
        self.write({
            'state': 'draft',
            'approval_state': 'draft',
            'publication_state': 'draft'
        })

    def action_submit_for_approval(self):
        """Submit policy for approval."""
        self.ensure_one()
        self.write({'approval_state': 'pending'})
        self.message_post(body=_("Policy submitted for approval."))

    def action_approve(self):
        """Approve the policy."""
        self.ensure_one()
        self.write({
            'approval_state': 'approved',
            'approved_by_id': self.env.user.id,
            'approval_date': date.today()
        })
        self.message_post(body=_("Policy approved."))

    def action_reject(self):
        """Reject the policy."""
        self.ensure_one()
        self.write({
            'approval_state': 'rejected',
            'rejected_by_id': self.env.user.id,
            'rejection_date': date.today()
        })
        self.message_post(body=_("Policy rejected."))

    def action_publish(self):
        """Publish the policy."""
        self.ensure_one()
        if self.approval_state != 'approved':
            raise UserError(_("You can only publish approved policies."))
        self.write({
            'publication_state': 'published',
            'published_by_id': self.env.user.id,
            'published_date': date.today()
        })
        self.message_post(body=_("Policy published."))

    def action_lock(self):
        """Lock the policy for editing."""
        self.ensure_one()
        self.write({
            'lifecycle_state': 'locked',
            'locked_by_id': self.env.user.id,
            'locked_date': date.today()
        })
        self.message_post(body=_("Policy locked."))

    def action_unlock(self):
        """Unlock the policy for editing."""
        self.ensure_one()
        self.write({
            'lifecycle_state': 'unlocked',
            'unlocked_by_id': self.env.user.id,
            'unlocked_date': date.today()
        })
        self.message_post(body=_("Policy unlocked."))

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

    def action_view_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents'),
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('retention_policy_id', '=', self.id)],
            'context': {'default_retention_policy_id': self.id}
        }

    def action_view_child_policies(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Child Policies'),
            'res_model': 'records.retention.policy',
            'view_mode': 'tree,form',
            'domain': [('parent_policy_id', '=', self.id)],
            'context': {'default_parent_policy_id': self.id}
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
            'res_model': 'records.retention.policy.version',
            'view_mode': 'tree,form',
            'domain': [('policy_id', '=', self.id)],
            'context': {'default_policy_id': self.id}
        }

    @api.constrains('parent_policy_id')
    def _check_policy_hierarchy(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive retention policies.'))
        # Explicit self-parent guard (UI domain removed to avoid active_id access issue)
        for rec in self:
            if rec.parent_policy_id and rec.parent_policy_id.id == rec.id:
                raise ValidationError(_('A policy cannot be its own parent.'))

class RecordsRetentionPolicyVersion(models.Model):
    _name = 'records.retention.policy.version'
    _description = 'Records Retention Policy Version'
    _order = 'version desc'

    policy_id = fields.Many2one(comodel_name='records.retention.policy', string='Policy', required=True, ondelete='cascade')
    version = fields.Char(string='Version', required=True)
    state = fields.Selection(related='policy_id.state', store=True)
    create_date = fields.Datetime(string='Creation Date', readonly=True)
    create_uid = fields.Many2one(comodel_name='res.users', string='Created By', readonly=True)
