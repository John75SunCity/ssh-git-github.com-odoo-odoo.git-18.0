# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import hashlib
from pulp import LpMinimize, LpProblem, LpVariable, lpSum, value  # For optimization

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
    monthly_cost = fields.Float(compute='_compute_monthly_cost', store=True, help='Optimized with PuLP.')

    # Links
    box_ids = fields.One2many('records.box', 'department_id', string='Boxes')
    document_ids = fields.One2many('records.document', 'department_id', string='Documents')
    shredding_ids = fields.One2many('shredding.service', 'department_id', string='Shredding Services')
    invoice_ids = fields.One2many('account.move', 'department_id', string='Invoices')
    portal_request_ids = fields.One2many('portal.request', 'department_id', string='Portal Requests')

    @api.depends('code')
    def _compute_hashed_code(self):
        for rec in self:
            rec.hashed_code = hashlib.sha256(rec.code.encode()).hexdigest() if rec.code else False

    @api.depends('box_ids')
    def _compute_monthly_cost(self):
        for rec in self:
            rec.monthly_cost = sum(rec.box_ids.mapped('storage_fee'))  # Base; optimize below

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
        """Innovative: Use PuLP to minimize costs across depts (e.g., allocate min fees)."""
        prob = LpProblem("Fee_Optimization", LpMinimize)
        fees = LpVariable.dicts("Fee", self.ids, lowBound=0)
        prob += lpSum([fees[d.id] for d in self]), "Total_Fees"
        for d in self:
            prob += fees[d.id] >= d.partner_id.minimum_fee_per_department or 0, f"Min_Fee_{d.id}"
        prob.solve()
        for d in self:
            d.monthly_cost = value(fees[d.id])  # Update; in practice, write to field