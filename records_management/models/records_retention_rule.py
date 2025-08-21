from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsRetentionRule(models.Model):
    _name = 'records.retention.rule'
    _description = 'Records Retention Rule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'policy_id, sequence, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Rule Name", required=True, tracking=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    sequence = fields.Integer(string="Sequence", default=10, help="Determines the order of execution for rules within a policy.")
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one(
        'res.company',
        related='policy_id.company_id',
        store=True,
        readonly=True
    )

    # ============================================================================
    # RELATIONSHIPS & APPLICABILITY
    # ============================================================================
    policy_id = fields.Many2one('records.retention.policy', string="Policy", required=True, ondelete='cascade', index=True, tracking=True)
    document_type_id = fields.Many2one('records.document.type', string="Document Type", help="Apply this rule only to this type of document. Leave empty to apply to all.")

    # ============================================================================
    # RETENTION PERIOD
    # ============================================================================
    retention_period = fields.Integer(string="Retention Period", tracking=True)
    retention_unit = fields.Selection([
        ('days', 'Days'),
        ('months', 'Months'),
        ('years', 'Years'),
        ('indefinite', 'Indefinite'),
    ], string="Retention Unit", default='years', required=True, tracking=True)

    # ============================================================================
    # ACTION & STATE
    # ============================================================================
    action_on_expiry = fields.Selection([
        ('destroy', 'Schedule for Destruction'),
        ('archive', 'Archive'),
        ('review', 'Flag for Review'),
    ], string="Action on Expiry", default='destroy', required=True, tracking=True)

    state = fields.Selection(related='policy_id.state', readonly=True, store=True)

    # New Fields from analysis
    partner_id = fields.Many2one('res.partner', string='Customer')
    department_id = fields.Many2one('hr.department', string='Department')
    category_id = fields.Many2one('records.category', string='Category')
    retention_type = fields.Selection([('permanent', 'Permanent'), ('temporary', 'Temporary')], string='Retention Type')
    retention_event = fields.Selection([('creation', 'Creation Date'), ('end_of_year', 'End of Fiscal Year'), ('last_activity', 'Last Activity Date')], string='Retention Event')
    is_legal_hold = fields.Boolean(string='Legal Hold')
    legal_hold_reason = fields.Text(string='Legal Hold Reason')
    is_active = fields.Boolean(string='Is Active', default=True)
    branch_id = fields.Many2one('res.branch', string='Branch')
    document_ids = fields.One2many('records.document', 'retention_rule_id', string='Documents')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count')
    next_action_date = fields.Date(string='Next Action Date')
    next_action = fields.Selection([('review', 'Review'), ('destroy', 'Destroy')], string='Next Action')
    destruction_approver_ids = fields.Many2many('res.users', string='Destruction Approvers')
    is_default = fields.Boolean(string='Is Default Rule')
    audit_log_ids = fields.One2many('records.audit.log', 'rule_id', string='Audit Log')
    related_regulation = fields.Char(string='Related Regulation')
    storage_location_id = fields.Many2one('stock.location', string='Storage Location')
    is_template = fields.Boolean(string='Is Template')
    template_id = fields.Many2one('records.retention.rule', string='Template')
    child_rule_ids = fields.One2many('records.retention.rule', 'parent_rule_id', string='Child Rules')
    parent_rule_id = fields.Many2one('records.retention.rule', string='Parent Rule')
    rule_level = fields.Integer(string='Rule Level', compute='_compute_rule_level')
    is_global = fields.Boolean(string='Is Global')
    country_ids = fields.Many2many('res.country', string='Applicable Countries')
    state_ids = fields.Many2many('res.country.state', string='Applicable States')
    tag_ids = fields.Many2many('records.tag', string='Tags')
    priority = fields.Selection([('0', 'Low'), ('1', 'Medium'), ('2', 'High')], string='Priority')
    review_cycle = fields.Integer(string='Review Cycle (days)')
    last_review_date = fields.Date(string='Last Review Date')
    last_review_by_id = fields.Many2one('res.users', string='Last Reviewed By')
    next_review_date = fields.Date(string='Next Review Date')
    next_reviewer_id = fields.Many2one('res.users', string='Next Reviewer')
    is_approved = fields.Boolean(string='Is Approved')
    approved_by_id = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Date(string='Approval Date')
    rejection_reason = fields.Text(string='Rejection Reason')
    is_rejected = fields.Boolean(string='Is Rejected')
    rejected_by_id = fields.Many2one('res.users', string='Rejected By')
    rejection_date = fields.Date(string='Rejection Date')
    is_pending_approval = fields.Boolean(string='Is Pending Approval')
    is_pending_review = fields.Boolean(string='Is Pending Review')
    is_pending_destruction = fields.Boolean(string='Is Pending Destruction')
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
    superseded_by_id = fields.Many2one('records.retention.rule', string='Superseded By')
    supersedes_id = fields.Many2one('records.retention.rule', string='Supersedes')
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

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('policy_id.name', 'name')
    def _compute_display_name(self):
        """Generate display name for the rule."""
        for rule in self:
            if rule.policy_id and rule.name:
                rule.display_name = f"{rule.policy_id.name} - {rule.name}"
            else:
                rule.display_name = rule.name or _("New Rule")

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('retention_period', 'retention_unit')
    def _check_retention_period(self):
        """Validate retention period is not negative and is set if not indefinite."""
        for rule in self:
            if rule.retention_unit != 'indefinite':
                if rule.retention_period <= 0:
                    raise ValidationError(_("The retention period must be a positive number."))
            else:
                # For indefinite, we can standardize the period to 0 for consistency
                if rule.retention_period != 0:
                    rule.retention_period = 0

