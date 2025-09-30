from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsDepartment(models.Model):
    _name = 'records.department'
    _description = 'Customer Department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'partner_id, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Department Name', required=True, tracking=True, index=True)
    code = fields.Char(string='Code', required=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one(comodel_name='res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)
    # Batch 3 label disambiguation
    description = fields.Text(string='Department Description')

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer", required=True, ondelete='cascade', tracking=True)
    billing_contact_ids = fields.One2many('records.department.billing.contact', 'department_id', string="Billing Contacts")
    container_ids = fields.One2many('records.container', 'department_id', string="Containers")
    document_ids = fields.One2many('records.document', 'department_id', string="Documents")
    user_ids = fields.Many2many(
        'res.users',
        relation='records_department_user_rel',
        column1='department_id',
        column2='user_id',
        string='Users'
    )
    # Hierarchy
    parent_department_id = fields.Many2one(
        comodel_name='records.department',
        string='Parent Department',
        index=True,
        help='Set a parent to build a hierarchical department structure for large customers.'
    )
    child_department_ids = fields.One2many(
        comodel_name='records.department',
        inverse_name='parent_department_id',
        string='Child Departments'
    )

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # ANALYTICS
    # ============================================================================
    container_count = fields.Integer(compute='_compute_counts', string="Container Count", store=True)
    document_count = fields.Integer(compute='_compute_counts', string="Document Count", store=True)
    child_count = fields.Integer(compute='_compute_child_count', string='Child Dept. Count', store=True)

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('name_partner_uniq', 'unique(name, partner_id, company_id)', 'The department name must be unique per customer.'),
    ]

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id.name')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id:
                record.display_name = f"{record.partner_id.name} - {record.name}"
            else:
                record.display_name = record.name

    @api.depends('container_ids', 'document_ids')
    def _compute_counts(self):
        for record in self:
            record.container_count = len(record.container_ids)
            record.document_count = len(record.document_ids)

    @api.depends('child_department_ids')
    def _compute_child_count(self):
        for record in self:
            record.child_count = len(record.child_department_ids)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        # DEPRECATED (Phase 1): Previously validated draft -> active and posted chatter.
        # Prefer direct state change via statusbar; retain minimal guard for safety.
        self.ensure_one()
        if self.state == 'draft':
            self.write({'state': 'active'})

    def action_archive(self):
        # DEPRECATED (Phase 1): Replace with direct write; maintain safety constraint.
        self.ensure_one()
        if self.container_count > 0 or self.document_count > 0:
            raise UserError(_("Cannot archive a department that still has active containers or documents."))
        self.write({'state': 'archived', 'active': False})

    def action_view_containers(self):
        self.ensure_one()
        return {
            'name': _('Containers'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.container',
            'view_mode': 'tree,form,kanban',
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id, 'default_partner_id': self.partner_id.id}
        }

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form,kanban',
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id, 'default_partner_id': self.partner_id.id}
        }

    def get_department_users(self):
        return self.user_ids.filtered(lambda u: u.active)

    def action_view_child_departments(self):
        self.ensure_one()
        return {
            'name': _('Child Departments'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.department',
            'view_mode': 'list,form,kanban',
            'domain': [('parent_department_id', '=', self.id)],
            'context': {'default_parent_department_id': self.id, 'search_default_parent_department_id': self.id},
        }

    # =========================================================================
    # CONSTRAINTS
    # =========================================================================
    @api.constrains('parent_department_id')
    def _check_parent_hierarchy(self):
        for record in self:
            if not record.parent_department_id:
                continue
            if record.parent_department_id == record:
                raise ValidationError(_("A department cannot be its own parent."))
            # Detect recursion / cycles
            ancestor = record.parent_department_id
            visited = set()
            while ancestor:
                if ancestor == record:
                    raise ValidationError(_("Recursive department hierarchy detected (cycle)."))
                if ancestor.id in visited:
                    # Safety break (should not normally happen)
                    break
                visited.add(ancestor.id)
                ancestor = ancestor.parent_department_id
