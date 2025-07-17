# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import hashlib

class RecordsDepartment(models.Model):
    """Customer Department for records management, billing, and access control."""
    _name = 'records.department'
    _description = 'Records Department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Department Name', required=True, tracking=True)
    code = fields.Char(string='Code', tracking=True, help='For quick reference and billing.')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True, index=True)
    parent_id = fields.Many2one('records.department', string='Parent Department', index=True, tracking=True)
    child_ids = fields.One2many('records.department', 'parent_id', string='Sub-Departments')
    retention_policy_id = fields.Many2one('records.retention.policy', string='Retention Policy', tracking=True)
    notes = fields.Text(string='Notes', tracking=True, help='Sensitive notes; consider encryption for ISO compliance.')
    hashed_code = fields.Char(compute='_compute_hashed_code', store=True, help='Hashed for data integrity (ISO 27001).')
    active = fields.Boolean(default=True, tracking=True)

    # Links to records management
    box_ids = fields.One2many('records.box', 'department_id', string='Boxes')
    document_ids = fields.One2many('records.document', 'department_id', string='Documents')
    shredding_ids = fields.One2many('shredding.service', 'department_id', string='Shredding Services')  # Assume add department_id to shredding.service
    invoice_ids = fields.One2many('account.move', 'department_id', string='Invoices')  # For departmental billing; assume extension

    @api.depends('code')
    def _compute_hashed_code(self):
        """Compute hash for integrity checks (NAID/ISO)."""
        for rec in self:
            if rec.code:
                rec.hashed_code = hashlib.sha256(rec.code.encode()).hexdigest()
            else:
                rec.hashed_code = False

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        """Prevent hierarchy loops (data integrity)."""
        for rec in self:
            if rec._has_cycle(rec.parent_id):
                raise ValidationError(_("Cannot create recursive department hierarchy."))

    def _has_cycle(self, parent):
        if not parent:
            return False
        if parent == self:
            return True
        return self._has_cycle(parent.parent_id)

    def action_view_boxes(self):
        """Modern UI: Action to view related boxes."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Boxes'),
            'view_mode': 'kanban,tree,form',
            'res_model': 'records.box',
            'domain': [('department_id', 'in', self.ids)],
            'context': {'default_department_id': self.id},
        }

    # TODO: Add computed field for estimated fees using simple formula or integrate PuLP for optimization