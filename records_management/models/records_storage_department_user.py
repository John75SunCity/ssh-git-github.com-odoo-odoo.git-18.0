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
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one(related='department_id.company_id', store=True, readonly=True, comodel_name='res.company')

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    department_id = fields.Many2one('records.department', string="Department", required=True, ondelete='cascade', index=True, tracking=True)
    user_id = fields.Many2one('res.users', string="User", required=True, ondelete='cascade', index=True, tracking=True)

    # ============================================================================
    # PERMISSIONS & LIFECYCLE
    # ============================================================================
    role = fields.Selection([
        ('viewer', 'Viewer'),
        ('editor', 'Editor'),
        ('manager', 'Manager'),
    ], string="Role", default='viewer', required=True, tracking=True, help="Defines the user's level of access within this department.")

    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string="Status", default='active', required=True, tracking=True)

    start_date = fields.Date(string="Start Date", default=fields.Date.context_today, tracking=True)
    end_date = fields.Date(string="End Date", tracking=True)

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('unique_user_department', 'unique(user_id, department_id)', 'A user can only be assigned to a department once.')
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

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activates the user's assignment to the department."""
        self.write({'state': 'active', 'active': True})
        self.message_post(body=_("User assignment activated."))

    def action_deactivate(self):
        """Deactivates the user's assignment, effectively revoking access."""
        self.write({'state': 'inactive', 'active': False, 'end_date': fields.Date.context_today(self)})
        self.message_post(body=_("User assignment deactivated."))
