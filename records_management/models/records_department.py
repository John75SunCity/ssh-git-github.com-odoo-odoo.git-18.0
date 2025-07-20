# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import hashlib

# Temporarily disable PuLP import for development (fixes 'pulp not installed' error during module install on Odoo.sh).
# PuLP is an optional external dependency for advanced fee optimization—commented out to allow loading without it.
# To enable in production: List 'pulp' in __manifest__.py external_dependencies {'python': ['pulp']}, install via pip in shell (odoo-cloc: apt update && apt install python3-pulp), uncomment import/check.
# This accomplishes fallback to base_cost computation (simple/safe), keeps code clean (no crashes), user-friendly (no UI changes). Innovative: For standards like NAID AAA/ISO 15489, add cron to recompute fees periodically; future: Integrate AI (torch) for predictive costing if PuLP unavailable.

# try:
#     from pulp import LpMinimize, LpProblem, LpVariable, lpSum, value
#     PULP_AVAILABLE = True
# except ImportError:
PULP_AVAILABLE = False  # Fallback if not installed

class RecordsDepartment(models.Model):
    _name = 'records.department'
    _description = 'Records Department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Department Name', required=True, tracking=True)
    code = fields.Char(string='Code', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True, index=True)
    parent_id = fields.Many2one('records.department', string='Parent Department', index=True, tracking=True)
    child_ids = fields.One2many('records.department', 'parent_id', string='Sub-Departments')
    
    # Contact Information
    manager_id = fields.Many2one('res.partner', string='Manager', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    
    # Additional Information
    description = fields.Text(string='Description', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, tracking=True)
    
    retention_policy_id = fields.Many2one('records.retention.policy', string='Retention Policy', tracking=True)
    notes = fields.Text(string='Notes', tracking=True)
    hashed_code = fields.Char(compute='_compute_hashed_code', store=True)
    active = fields.Boolean(default=True, tracking=True)
    monthly_cost = fields.Float(compute='_compute_monthly_cost', store=True, help='Optimized with PuLP if available.')
    
    # Computed fields for billing views
    total_boxes = fields.Integer(compute='_compute_box_stats', string='Total Boxes', store=True)
    
    # Hierarchy fields
    level = fields.Integer(compute='_compute_hierarchy_level', string='Level', store=True, help='Hierarchy level (0=root, 1=department, 2=sub-department, etc.)')
    complete_name = fields.Char(compute='_compute_complete_name', string='Complete Name', store=True, recursive=True, help='Full hierarchical name')
    all_child_ids = fields.Many2many('records.department', compute='_compute_all_children', string='All Child Departments')
    
    # User management
    user_ids = fields.One2many('records.storage.department.user', 'department_id', string='Department Users')
    user_count = fields.Integer(compute='_compute_user_count', string='User Count', store=True)

    # Links
    box_ids = fields.One2many('records.box', 'department_id', string='Boxes')
    document_ids = fields.One2many('records.document', 'department_id', string='Documents')  # Now valid with inverse
    shredding_ids = fields.One2many('shredding.service', 'department_id', string='Shredding Services')
    invoice_ids = fields.One2many('account.move', 'department_id', string='Invoices')
    portal_request_ids = fields.One2many('portal.request', 'department_id', string='Portal Requests')

    @api.depends('code')
    def _compute_hashed_code(self):
        for rec in self:
            rec.hashed_code = hashlib.sha256(rec.code.encode()).hexdigest() if rec.code else False

    @api.depends('box_ids', 'box_ids.state')
    def _compute_box_stats(self):
        """Compute statistics about boxes for this department"""
        for rec in self:
            rec.total_boxes = len(rec.box_ids.filtered(lambda b: b.state == 'active'))

    @api.depends('parent_id')
    def _compute_hierarchy_level(self):
        """Compute the hierarchy level of each department"""
        for rec in self:
            level = 0
            parent = rec.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            rec.level = level

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        """Compute the complete hierarchical name"""
        for rec in self:
            if rec.parent_id:
                rec.complete_name = f"{rec.parent_id.complete_name} / {rec.name}"
            else:
                rec.complete_name = rec.name

    @api.depends('child_ids', 'child_ids.child_ids')
    def _compute_all_children(self):
        """Compute all child departments recursively"""
        for rec in self:
            all_children = rec.child_ids
            for child in rec.child_ids:
                all_children |= child.all_child_ids
            rec.all_child_ids = all_children

    @api.depends('user_ids')
    def _compute_user_count(self):
        """Compute the number of users in this department"""
        for rec in self:
            rec.user_count = len(rec.user_ids)

    @api.depends('box_ids', 'document_ids')
    def _compute_monthly_cost(self):
        for rec in self:
            base_cost = sum(rec.box_ids.mapped('storage_fee')) + sum(rec.document_ids.mapped('storage_fee') or [0])  # Include docs if fee added
            if PULP_AVAILABLE:
                prob = LpProblem("Fee_Optim", LpMinimize)
                fee = LpVariable("Fee", lowBound=0)
                prob += fee, "Total"
                prob += fee >= rec.partner_id.minimum_fee_per_department or 0, "Min_Fee"
                prob.solve()
                rec.monthly_cost = value(fee) + base_cost
            else:
                rec.monthly_cost = base_cost  # Fallback

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        for rec in self:
            if rec._has_cycle(rec.parent_id):
                raise ValidationError(_("No recursive hierarchies (data integrity)."))
            # Ensure department and parent belong to same customer
            if rec.parent_id and rec.parent_id.partner_id != rec.partner_id:
                raise ValidationError(_("Department and parent department must belong to the same customer."))

    @api.constrains('parent_id', 'partner_id')
    def _check_customer_consistency(self):
        """Ensure all departments in hierarchy belong to same customer"""
        for rec in self:
            if rec.parent_id and rec.parent_id.partner_id != rec.partner_id:
                raise ValidationError(_("All departments in hierarchy must belong to the same customer: %s") % rec.partner_id.name)

    def _has_cycle(self, parent):
        if not parent:
            return False
        if parent == self:
            return True
        return self._has_cycle(parent.parent_id)

    def action_view_boxes(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Boxes'),
            'view_mode': 'kanban,tree,form',
            'res_model': 'records.box',
            'domain': [('department_id', 'in', self.ids)],
            'context': {'default_department_id': self.id},
        }

    def action_setup_billing_contact(self):
        """Action to setup billing contact for this department"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Setup Billing Contact'),
            'view_mode': 'form',
            'res_model': 'records.department.billing.contact',
            'context': {
                'default_customer_id': self.partner_id.id,
                'default_department_id': self.id,
            },
            'target': 'new',
        }

    def action_view_users(self):
        """Action to view department users"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Department Users'),
            'view_mode': 'tree,form',
            'res_model': 'records.storage.department.user',
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id},
        }

    def action_add_user(self):
        """Action to add user to department"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add User to Department'),
            'view_mode': 'form',
            'res_model': 'records.storage.department.user',
            'context': {
                'default_department_id': self.id,
                'default_access_level': 'viewer',
            },
            'target': 'new',
        }

    def action_view_hierarchy(self):
        """Action to view department hierarchy"""
        # Find root department
        root = self
        while root.parent_id:
            root = root.parent_id
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Department Hierarchy'),
            'view_mode': 'tree',
            'res_model': 'records.department',
            'domain': [('id', 'child_of', root.id)],
            'context': {'expand_all': True},
        }

    def get_all_parent_departments(self):
        """Get all parent departments up to root"""
        parents = self.browse()
        current = self.parent_id
        while current:
            parents |= current
            current = current.parent_id
        return parents

    def get_all_child_departments(self):
        """Get all child departments recursively"""
        return self.all_child_ids

    def is_child_of(self, department):
        """Check if this department is a child of given department"""
        return department in self.get_all_parent_departments()

    def is_parent_of(self, department):
        """Check if this department is a parent of given department"""
        return self in department.get_all_parent_departments()

    # Customer Portal Methods
    def get_portal_accessible_records(self, user):
        """Get records accessible to a portal user based on their department access"""
        department_user = self.env['records.storage.department.user'].search([
            ('user_id', '=', user.partner_id.id),
            ('department_id', '=', self.id),
            ('active', '=', True)
        ], limit=1)
        
        if not department_user:
            return self.env['records.box'].browse()
        
        accessible_departments = department_user.get_accessible_departments()
        return self.env['records.box'].search([
            ('department_id', 'in', accessible_departments.ids)
        ])

    def can_user_access_department(self, user):
        """Check if a portal user can access this department"""
        department_user = self.env['records.storage.department.user'].search([
            ('user_id', '=', user.partner_id.id),
            ('active', '=', True)
        ])
        
        for du in department_user:
            accessible_depts = du.get_accessible_departments()
            if self in accessible_depts:
                return True
        return False

    def get_user_permissions(self, user):
        """Get user permissions for this department"""
        department_user = self.env['records.storage.department.user'].search([
            ('user_id', '=', user.partner_id.id),
            ('department_id', '=', self.id),
            ('active', '=', True)
        ], limit=1)
        
        if not department_user:
            return {}
        
        return {
            'can_view_inventory': department_user.can_view_inventory,
            'can_view_subdepartments': department_user.can_view_subdepartments,
            'can_add_boxes': department_user.can_add_boxes,
            'can_request_services': department_user.can_request_services,
            'can_request_deletion': department_user.can_request_deletion,
            'can_approve_deletion': department_user.can_approve_deletion,
            'can_view_billing': department_user.can_view_billing,
            'can_manage_users': department_user.can_manage_users,
            'access_level': department_user.access_level,
        }

    def action_optimize_fees(self):
        if not PuLP_AVAILABLE:
            raise ValidationError(_("PuLP not installed; add to requirements.txt for advanced optimization."))
        self._compute_monthly_cost()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('Optimized'), 'message': _('Fees updated with PuLP.'), 'sticky': False},
        }