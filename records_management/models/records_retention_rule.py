
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
    name = fields.Char(string="Rule Name", required=True, tracking=True, index=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    sequence = fields.Integer(string="Sequence", default=10, help="Determines the order of execution for rules within a policy.")
    active = fields.Boolean(string='Active', default=True)
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
    partner_id = fields.Many2one('res.partner', string='Customer')
    department_id = fields.Many2one('hr.department', string='Department')
    category_id = fields.Many2one('records.category', string='Category')
    tag_ids = fields.Many2many('records.tag', string='Tags')
    country_ids = fields.Many2many('res.country', string='Applicable Countries')
    state_ids = fields.Many2many('res.country.state', string='Applicable States')
    branch_company_id = fields.Many2one(
        'res.company',
        string='Branch (Subsidiary/Location)',
        help="Specifies the branch or subsidiary company, distinct from the main company_id."
    )

    # Hierarchy
    is_template = fields.Boolean(string='Is Template')
    template_id = fields.Many2one('records.retention.rule', string='Template')
    parent_rule_id = fields.Many2one('records.retention.rule', string='Parent Rule', check_company=True)
    child_rule_ids = fields.One2many('records.retention.rule', 'parent_rule_id', string='Child Rules')
    rule_level = fields.Integer(string='Rule Level', compute='_compute_rule_level', store=True)

    # ============================================================================
    # RETENTION PERIOD
    # ============================================================================
    retention_type = fields.Selection([('permanent', 'Permanent'), ('temporary', 'Temporary')], string='Retention Type', default='temporary')
    retention_period = fields.Integer(string="Retention Period", tracking=True)
    retention_unit = fields.Selection([
        ('days', 'Days'),
        ('months', 'Months'),
        ('years', 'Years'),
        ('indefinite', 'Indefinite'),
    ], string="Retention Unit", default='years', required=True, tracking=True)
    retention_event = fields.Selection([('creation', 'Creation Date'), ('end_of_year', 'End of Fiscal Year'), ('last_activity', 'Last Activity Date')], string='Retention Event')

    # ============================================================================
    # ACTION, STATE & STATUS
    # ============================================================================
    action_on_expiry = fields.Selection([
        ('destroy', 'Schedule for Destruction'),
        ('archive', 'Archive'),
        ('review', 'Flag for Review'),
    ], string="Action on Expiry", default='destroy', required=True, tracking=True)
    state = fields.Selection(related='policy_id.state', readonly=True, store=True)
    next_action_date = fields.Date(string='Next Action Date')
    next_action = fields.Selection([('review', 'Review'), ('destroy', 'Destroy')], string='Next Action')
    expiration_date = fields.Date(string='Expiration Date', compute='_compute_expiration_details', store=True, compute_sudo=True)
    is_expired = fields.Boolean(string='Is Expired', compute='_compute_expiration_details', store=True, compute_sudo=True)
    overdue_days = fields.Integer(string='Overdue Days', compute='_compute_expiration_details', store=True, compute_sudo=True)

    # Consolidated Status Fields
    approval_status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Approval Status', default='draft', tracking=True)
    approved_by_id = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Date(string='Approval Date')
    rejection_reason = fields.Text(string='Rejection Reason')

    version_status = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('superseded', 'Superseded'),
        ('expired', 'Expired'),
    ], string='Version Status', default='draft', tracking=True)
    version = fields.Integer(string='Version', default=1)
    rule_code = fields.Char(string='Rule Code', help="Unique code to identify rule versions")
    is_latest_version = fields.Boolean(string='Is Latest Version', compute='_compute_version_details')

    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('unknown', 'Unknown')
    ], string='Compliance Status', default='unknown')
    compliance_notes = fields.Text(string='Compliance Notes')
    compliance_check_date = fields.Date(string='Compliance Check Date')
    compliance_checker_id = fields.Many2one('res.users', string='Compliance Checker')

    # Legal Hold
    is_legal_hold = fields.Boolean(string='Legal Hold')
    legal_hold_reason = fields.Text(string='Legal Hold Reason')

    # Documents and Audit
    document_ids = fields.One2many('records.document', 'retention_rule_id', string='Documents')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count')
    audit_log_ids = fields.One2many('records.audit.log', 'rule_id', string='Audit Logs')
    related_regulation = fields.Char(string='Related Regulation')
    storage_location_id = fields.Many2one('stock.location', string='Storage Location')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('document_ids')
    def _compute_document_count(self):
        """Efficiently compute the number of documents for each rule."""
        counts = self.env['records.document'].read_group(
            [('retention_rule_id', 'in', self.ids)],
            ['retention_rule_id'],
            ['retention_rule_id']
        )
        count_map = {
            group['retention_rule_id'][0]: group['retention_rule_id_count']
            for group in counts if group['retention_rule_id']
        }
        for rule in self:
            rule.document_count = count_map.get(rule.id, 0)

    @api.depends('policy_id.name', 'name')
    def _compute_display_name(self):
        """Generate display name for the rule."""
        for rule in self:
            if rule.policy_id and rule.name:
                rule.display_name = f"{rule.policy_id.name} - {rule.name}"
            else:
                rule.display_name = rule.name or _("New Rule")

    @api.depends('parent_rule_id.rule_level')
    def _compute_rule_level(self):
        """Compute hierarchy level (depth from root)."""
        for rule in self:
            level = 0
            current = rule
            while current.parent_rule_id:
                level += 1
                current = current.parent_rule_id
            rule.rule_level = level

    @api.depends('expiration_date')
    def _compute_expiration_details(self):
        today = fields.Date.today()
        for rule in self:
            if rule.expiration_date:
                rule.is_expired = rule.expiration_date < today
                rule.overdue_days = (today - rule.expiration_date).days if rule.is_expired else 0
            else:
                rule.is_expired = False
                rule.overdue_days = 0

    @api.depends('version', 'rule_code')
    def _compute_version_details(self):
        """Determine if this is the latest version of the rule."""
        for rule in self:
            # Find the highest version for this rule_code
            latest_version = self.search([
                ('rule_code', '=', rule.rule_code)
            ], order='version desc', limit=1)
            rule.is_latest_version = (rule.id == latest_version.id) if latest_version else True

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('retention_period', 'retention_unit')
    def _check_retention_period(self):
        """Validate retention period is positive and required if not indefinite."""
        for rule in self:
            if rule.retention_unit != 'indefinite':
                if rule.retention_period is None or rule.retention_period <= 0:
                    raise ValidationError(_("Retention period must be a positive number for rule '%s'.") % (rule.display_name or rule.name))
            else:
                if rule.retention_period != 0:
                    raise ValidationError(_("Retention period should be 0 for indefinite retention in rule '%s'.") % (rule.display_name or rule.name))

    @api.constrains('parent_rule_id')
    def _check_hierarchy_cycle(self):
        """Prevent cycles in rule hierarchy."""
        for rule in self:
            rule._check_recursion()

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('retention_unit')
    def _onchange_retention_unit(self):
        """Reset retention period to 0 when unit is set to indefinite."""
        if self.retention_unit == 'indefinite':
            self.retention_period = 0
        elif self.retention_unit in ['days', 'months', 'years']:
            # Placeholder for future logic for other units
            pass
