# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    department_id = fields.Many2one('records.department', string='Department', index=True, check_company=True)  # Added for inverse; ISO company integrity)

    @api.depends('amount_total', 'department_id')
    def _compute_shredding_cost(self):
        """Innovative: Placeholder for PuLP-optimized cost (extend for real destruction links)."""
        for rec in self:
            rec.shredding_cost = rec.amount_total * 0.1  # Simple; use PuLP for dept allocation

    shredding_cost = fields.Float(compute='_compute_shredding_cost', store=True)

    def action_view_department_invoices(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Department Invoices'),
            'view_mode': 'kanban,tree,form',
            'res_model': 'account.move',
            'domain': [('department_id', '=', self.department_id.id)],
            'context': {'default_department_id': self.department_id.id},
        }

    def write(self, vals):
        res = super().write(vals)
        if 'department_id' in vals:
    pass
            self.message_post(body=_('Department updated to %s for NAID audit.' % self.department_id.name))
        return res