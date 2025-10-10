from odoo import models, fields, api, _


class RecordsStorageDepartmentUser(models.Model):
    _name = 'records.storage.department.user'
    _description = 'Storage Department User Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'department_id, user_id'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(related='department_id.company_id', store=True, readonly=True, comodel_name='res.company')

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    department_id = fields.Many2one(comodel_name='records.department', string="Department", required=True, ondelete='cascade', index=True, tracking=True)
    user_id = fields.Many2one(comodel_name='res.users', string="User", required=True, ondelete='cascade', index=True, tracking=True)

    # ============================================================================
    # PERMISSIONS & LIFECYCLE
    # ============================================================================
    # Contextual label disambiguation (Batch 2)
    role = fields.Selection([
        ('viewer', 'Viewer'),
        ('editor', 'Editor'),
        ('manager', 'Manager'),
    ], string="Department Role", default='viewer', required=True, tracking=True, help="Defines the user's level of access within this department.")

    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string="Status", default='active', required=True, tracking=True)

    start_date = fields.Date(string="Start Date", default=fields.Date.context_today, tracking=True)
    end_date = fields.Date(string="End Date", tracking=True)

    # ============================================================================
    # BUSINESS FIELDS (Previously missing from model)
    # ============================================================================
    assignment_count = fields.Integer(string="Assignment Count", compute='_compute_assignment_count', store=True,
                                     help="Number of active assignments for this user across all departments")
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string="Assignment Priority", default='normal', tracking=True,
       help="Priority level of this department assignment (primary vs secondary department)")

    access_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
        ('classified', 'Classified')
    ], string="Security Access Level", default='internal', tracking=True,
       help="Security clearance level for accessing department records")

    description = fields.Char(string="Assignment Description", tracking=True,
                             help="Brief description of the user's role and responsibilities in this department")
    notes = fields.Text(string="Internal Notes", tracking=True,
                       help="Internal notes about this assignment, visible only to managers")

    # ==========================================================================
    # VIRTUAL / SEARCH OPTIMIZATION FIELDS (Dynamic date domains refactor)
    # ==========================================================================
    start_date_this_month = fields.Boolean(
        string="Started This Month",
        compute="_compute_start_date_period_flags",
        search="_search_start_date_this_month",
        help="Indicates assignments whose start date falls within the current calendar month."
    )

    # ============================================================================
    # GRANULAR PERMISSIONS
    # ============================================================================
    can_view_records = fields.Boolean(string="Can View Records", default=True, tracking=True)
    can_edit_records = fields.Boolean(string="Can Edit Records", default=False, tracking=True)
    can_delete_records = fields.Boolean(string="Can Delete Records", default=False, tracking=True)
    can_export_records = fields.Boolean(string="Can Export Records", default=False, tracking=True)
    can_manage_users = fields.Boolean(string="Can Manage Department Users", default=False, tracking=True)
    can_approve_requests = fields.Boolean(string="Can Approve Requests", default=False, tracking=True)

    # ============================================================================
    # AUDIT TRAIL & HISTORY
    # ============================================================================
    history_ids = fields.One2many('records.storage.department.user.history', 'assignment_id',
                                 string="Assignment History", readonly=True,
                                 help="Historical changes to this department assignment")

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    # SQL constraints
    _sql_constraints = [
        ('unique_user_department', 'unique(user_id, department_id)', 'A user can only be assigned to a department once.'),
    ]

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('user_id.name', 'department_id.name')
    def _compute_display_name(self):
        for record in self:
            if record.user_id and record.department_id:
                record.display_name = f"{record.user_id.name} - {record.department_id.name}"
            else:
                record.display_name = _("New Department Assignment")

    @api.depends('user_id')
    def _compute_assignment_count(self):
        """Compute the total number of active assignments for this user across all departments."""
        for record in self:
            if record.user_id:
                record.assignment_count = self.search_count([
                    ('user_id', '=', record.user_id.id),
                    ('state', '=', 'active'),
                    ('active', '=', True)
                ])
            else:
                record.assignment_count = 0

    # --------------------------------------------------------------------------
    # COMPUTE: PERIOD FLAGS
    # --------------------------------------------------------------------------
    @api.depends('start_date')
    def _compute_start_date_period_flags(self):
        """Compute boolean period flags for optimized search filters.

        Replaces UI domains that previously embedded Python date arithmetic
        (relativedelta/day manipulations) with a simple boolean field that can
        be safely referenced in search views.
        """
        today = fields.Date.context_today(self)
        # First day of current month
        month_start = today.replace(day=1)
        # First day of next month (safe month increment)
        if month_start.month == 12:
            next_month_start = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month_start = month_start.replace(month=month_start.month + 1)

        for rec in self:
            sd = rec.start_date
            rec.start_date_this_month = bool(sd and month_start <= sd < next_month_start)

    # --------------------------------------------------------------------------
    # SEARCH HELPERS
    # --------------------------------------------------------------------------
    def _search_start_date_this_month(self, operator, value):
        """Search helper for start_date_this_month virtual flag.

        Accepts truthy comparisons only; falsy searches fall back to a domain
        excluding the month range to preserve logical semantics.
        """
        # Normalize expected truthy values
        truthy = {'1', 1, True, 'true', 'True'}
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        if month_start.month == 12:
            next_month_start = month_start.replace(year=month_start.year + 1, month=1)
        else:
            next_month_start = month_start.replace(month=month_start.month + 1)

        if operator in ('=', '==') and value in truthy:
            return [('start_date', '>=', month_start), ('start_date', '<', next_month_start)]
        if operator in ('!=', '<>') and value in truthy:
            return ['|', ('start_date', '=', False), ('start_date', '<', month_start), ('start_date', '>=', next_month_start)]
        # For any other pattern (including searching for False) return a domain that negates the range
        if operator in ('=', '==') and value not in truthy:
            return ['|', ('start_date', '=', False), ('start_date', '<', month_start), ('start_date', '>=', next_month_start)]
        # Default safe fallback
        return [('id', '!=', 0)]

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activates the user's assignment to the department."""
        self.ensure_one()
        self.write({'state': 'active', 'active': True})
        self.message_post(body=_("User assignment activated."))

    def action_deactivate(self):
        """Deactivates the user's assignment, effectively revoking access."""
        self.ensure_one()
        self.write({'state': 'inactive', 'active': False, 'end_date': fields.Date.context_today(self)})
        self.message_post(body=_("User assignment deactivated."))

    def action_view_assignments(self):
        """Placeholder navigation action (was in placeholder file)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Department Assignments'),
            'res_model': 'records.storage.department.user',
            'view_mode': 'tree,form',
            'domain': [('department_id', '=', self.department_id.id)],
            'context': {'default_department_id': self.department_id.id},
            'target': 'current',
        }


class RecordsStorageDepartmentUserHistory(models.Model):
    """Model to track historical changes to department user assignments."""
    _name = 'records.storage.department.user.history'
    _description = 'Department User Assignment History'
    _order = 'change_date desc'
    _rec_name = 'change_summary'

    assignment_id = fields.Many2one(comodel_name='records.storage.department.user', string="Assignment",
                                   required=True, ondelete='cascade', index=True)
    change_date = fields.Datetime(string="Change Date", default=fields.Datetime.now, required=True)
    changed_by_id = fields.Many2one(comodel_name='res.users', string="Changed By", default=lambda self: self.env.user, required=True)
    change_type = fields.Selection([
        ('created', 'Assignment Created'),
        ('activated', 'Assignment Activated'),
        ('deactivated', 'Assignment Deactivated'),
        ('role_changed', 'Role Changed'),
        ('permissions_changed', 'Permissions Changed'),
        ('access_level_changed', 'Access Level Changed'),
        ('other', 'Other Change')
    ], string="Change Type", required=True)
    change_summary = fields.Char(string="Change Summary", required=True)
    old_values = fields.Text(string="Previous Values")
    new_values = fields.Text(string="New Values")
    notes = fields.Text(string="Change Notes")
