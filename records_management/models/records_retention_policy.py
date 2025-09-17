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

    # === OPTIMIZED STATUS TRACKING WITH SELECTION FIELDS ===

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

    # Review and compliance state
    review_state = fields.Selection([
        ('current', 'Current'),
        ('pending_review', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('overdue', 'Overdue'),
        ('expired', 'Expired'),
    ], string="Review State", default='current', tracking=True,
       help="Current review status of the retention policy")

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

    # Timeline status
    timeline_status = fields.Selection([
        ('current', 'Current'),
        ('historical', 'Historical'),
        ('future', 'Future'),
    ], string="Timeline Status", default='current',
       help="Indicates the temporal relevance of the policy")

    # Essential boolean flags (kept for critical functionality)
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
    is_latest_version = fields.Boolean(string='Is Latest Version', default=True,
                                      help="Indicates if this is the latest version of the policy")
    is_pending_destruction = fields.Boolean(string='Pending Destruction',
                                           help="Indicates if documents are pending destruction under this policy")

    # === BACKWARD COMPATIBILITY COMPUTED FIELDS ===
    # These computed fields maintain compatibility with existing views and logic
    # while using the new optimized selection fields internally

    is_approved = fields.Boolean(string='Is Approved', compute='_compute_approval_booleans', store=False)
    is_rejected = fields.Boolean(string='Is Rejected', compute='_compute_approval_booleans', store=False)
    is_pending_approval = fields.Boolean(string='Pending Approval', compute='_compute_approval_booleans', store=False)
    is_under_review = fields.Boolean(string='Under Review', compute='_compute_approval_booleans', store=False)

    is_archived = fields.Boolean(string='Is Archived', compute='_compute_lifecycle_booleans', store=False)
    is_deleted = fields.Boolean(string='Is Deleted', compute='_compute_lifecycle_booleans', store=False)
    is_locked = fields.Boolean(string='Is Locked', compute='_compute_lifecycle_booleans', store=False)

    is_pending_review = fields.Boolean(string='Pending Review', compute='_compute_review_booleans', store=False)
    is_overdue = fields.Boolean(string='Is Overdue', compute='_compute_review_booleans', store=False)
    is_expired = fields.Boolean(string='Is Expired', compute='_compute_review_booleans', store=False)

    is_published = fields.Boolean(string='Is Published', compute='_compute_publication_booleans', store=False)
    is_draft = fields.Boolean(string='Is Draft', compute='_compute_publication_booleans', store=False)
    is_effective = fields.Boolean(string='Is Effective', compute='_compute_publication_booleans', store=False)
    is_superseded = fields.Boolean(string='Is Superseded', compute='_compute_publication_booleans', store=False)

    is_current = fields.Boolean(string='Is Current', compute='_compute_timeline_booleans', store=False)
    is_historical = fields.Boolean(string='Is Historical', compute='_compute_timeline_booleans', store=False)
    is_future = fields.Boolean(string='Is Future', compute='_compute_timeline_booleans', store=False)

    # Legal hold compatibility - ensures full backward compatibility
    is_under_legal_hold = fields.Boolean(string='Under Legal Hold', compute='_compute_legal_hold_booleans', store=False)

    # Additional compatibility fields for lifecycle states
    is_restored = fields.Boolean(string='Is Restored', compute='_compute_lifecycle_extended_booleans', store=False)
    is_purged = fields.Boolean(string='Is Purged', compute='_compute_lifecycle_extended_booleans', store=False)
    is_unlocked = fields.Boolean(string='Is Unlocked', compute='_compute_lifecycle_extended_booleans', store=False)

    # Additional compatibility fields for publishing states
    is_unpublished = fields.Boolean(string='Is Unpublished', compute='_compute_publication_extended_booleans', store=False)
    is_ineffective = fields.Boolean(string='Is Ineffective', compute='_compute_publication_extended_booleans', store=False)

    @api.depends('approval_state')
    def _compute_approval_booleans(self):
        """Compute approval-related boolean flags based on approval_state."""
        for record in self:
            record.is_approved = record.approval_state == 'approved'
            record.is_rejected = record.approval_state == 'rejected'
            record.is_pending_approval = record.approval_state == 'pending'
            record.is_under_review = record.approval_state == 'under_review'

    @api.depends('lifecycle_state')
    def _compute_lifecycle_booleans(self):
        """Compute lifecycle-related boolean flags based on lifecycle_state."""
        for record in self:
            record.is_archived = record.lifecycle_state == 'archived'
            record.is_deleted = record.lifecycle_state == 'deleted'
            record.is_locked = record.lifecycle_state == 'locked'

    @api.depends('review_state')
    def _compute_review_booleans(self):
        """Compute review-related boolean flags based on review_state."""
        for record in self:
            record.is_pending_review = record.review_state == 'pending_review'
            record.is_overdue = record.review_state == 'overdue'
            record.is_expired = record.review_state == 'expired'

    @api.depends('publication_state')
    def _compute_publication_booleans(self):
        """Compute publication-related boolean flags based on publication_state."""
        for record in self:
            record.is_published = record.publication_state == 'published'
            record.is_draft = record.publication_state == 'draft'
            record.is_effective = record.publication_state == 'effective'
            record.is_superseded = record.publication_state == 'superseded'

    @api.depends('timeline_status')
    def _compute_timeline_booleans(self):
        """Compute timeline-related boolean flags based on timeline_status."""
        for record in self:
            record.is_current = record.timeline_status == 'current'
            record.is_historical = record.timeline_status == 'historical'
            record.is_future = record.timeline_status == 'future'

    @api.depends('is_legal_hold')
    def _compute_legal_hold_booleans(self):
        """Compute legal hold related boolean flags."""
        for record in self:
            # is_under_legal_hold is the same as is_legal_hold for backward compatibility
            record.is_under_legal_hold = record.is_legal_hold

    @api.depends('lifecycle_state')
    def _compute_lifecycle_extended_booleans(self):
        """Compute extended lifecycle-related boolean flags based on lifecycle_state."""
        for record in self:
            record.is_restored = record.lifecycle_state == 'restored'
            record.is_purged = record.lifecycle_state == 'purged'
            record.is_unlocked = record.lifecycle_state == 'unlocked'

    @api.depends('publication_state')
    def _compute_publication_extended_booleans(self):
        """Compute extended publication-related boolean flags based on publication_state."""
        for record in self:
            record.is_unpublished = record.publication_state == 'unpublished'
            record.is_ineffective = record.publication_state == 'ineffective'

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

    # Auto-update review_state based on expiration logic
    @api.depends('expiration_date', 'state', 'next_review_date')
    def _compute_review_state_auto(self):
        """Auto-compute review_state based on dates and current status."""
        today = date.today()
        for record in self:
            if record.expiration_date and record.state in ['active']:
                if record.expiration_date < today:
                    record.review_state = 'expired'
                elif record.next_review_date and record.next_review_date < today:
                    record.review_state = 'overdue'
                else:
                    record.review_state = 'current'
            else:
                record.review_state = 'current'

    # === OPTIMIZED ACTION METHODS ===
    def action_activate(self):
        """Activate policy if it has at least one rule."""
        self.ensure_one()
        if not self.rule_ids:
            raise UserError(_("You cannot activate a policy with no retention rules."))
        self.write({
            'state': 'active',
            'approval_state': 'approved',
            'lifecycle_state': 'active',
            'publication_state': 'published'
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

class RecordsRetentionPolicyVersion(models.Model):
    _name = 'records.retention.policy.version'
    _description = 'Records Retention Policy Version'
    _order = 'version desc'

    policy_id = fields.Many2one('records.retention.policy', string='Policy', required=True, ondelete='cascade')
    version = fields.Char(string='Version', required=True)
    state = fields.Selection(related='policy_id.state', store=True)
    create_date = fields.Datetime(string='Creation Date', readonly=True)
    create_uid = fields.Many2one('res.users', string='Created By', readonly=True)
