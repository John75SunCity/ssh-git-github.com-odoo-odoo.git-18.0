from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ============================================================================
    # RECORDS MANAGEMENT FIELDS
    # ============================================================================
    is_records_customer = fields.Boolean(
        string="Is a Records Management Customer",
        default=False,
        tracking=True,
        help="Check this box if this partner is a customer of the records management services."
    )

    department_ids = fields.One2many(
        'records.department',
        'partner_id',
        string="Departments"
    )

    department_count = fields.Integer(
        string="Department Count",
        compute='_compute_department_count',
        store=True
    )

    container_count = fields.Integer(
        string="Container Count",
        compute='_compute_records_stats',
    )

    document_count = fields.Integer(
        string="Document Count",
        compute='_compute_records_stats',
    )

    destruction_address_id = fields.Many2one('res.partner', string='Destruction Address')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('department_ids')
    def _compute_department_count(self):
        """Computes the number of departments associated with this partner."""
        for partner in self:
            partner.department_count = len(partner.department_ids)

    def _compute_records_stats(self):
        """Computes the count of containers and documents for the partner."""
        # This approach is more efficient than looping and searching for each partner.
        container_data = self.env['records.container']._read_group(
            [('partner_id', 'in', self.ids)],
            ['partner_id'],
            ['__count']
        )
        document_data = self.env['records.document']._read_group(
            [('partner_id', 'in', self.ids)],
            ['partner_id'],
            ['__count']
        )

        container_map = {item['partner_id'][0]: item['__count'] for item in container_data}
        document_map = {item['partner_id'][0]: item['__count'] for item in document_data}

        for partner in self:
            partner.container_count = container_map.get(partner.id, 0)
            partner.document_count = document_map.get(partner.id, 0)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_departments(self):
        """Opens the tree view of departments related to this partner."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Departments'),
            'res_model': 'records.department',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
                'default_company_id': self.company_id.id or self.env.company.id,
            }
        }

    def action_view_containers(self):
        """Opens the tree view of containers related to this partner."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Containers'),
            'res_model': 'records.container',
            'view_mode': 'tree,form,kanban',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

    def action_view_documents(self):
        """Opens the tree view of documents related to this partner."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents'),
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }
