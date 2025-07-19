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
    retention_policy_id = fields.Many2one('records.retention.policy', string='Retention Policy', tracking=True)
    notes = fields.Text(string='Notes', tracking=True)
    hashed_code = fields.Char(compute='_compute_hashed_code', store=True)
    active = fields.Boolean(default=True, tracking=True)
    monthly_cost = fields.Float(compute='_compute_monthly_cost', store=True, help='Optimized with PuLP if available.')

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

    def action_optimize_fees(self):
        if not PuLP_AVAILABLE:
            raise ValidationError(_("PuLP not installed; add to requirements.txt for advanced optimization."))
        self._compute_monthly_cost()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('Optimized'), 'message': _('Fees updated with PuLP.'), 'sticky': False},
        }