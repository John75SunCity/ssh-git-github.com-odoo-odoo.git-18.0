"""
maintenance_request.py

Extension of the standard Odoo maintenance.request model to add cost tracking.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MaintenanceRequest(models.Model):
    """
    Extension of Maintenance Request to add cost tracking for service items.
    """
    _inherit = 'maintenance.request'

    # === COST TRACKING ===
    cost = fields.Monetary(
        string="Maintenance Cost",
        help="Cost of this maintenance request",
        currency_field='currency_id',
        compute='_compute_total_cost',
        store=True
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # === ADDITIONAL TRACKING ===
    labor_cost = fields.Monetary(
        string="Labor Cost",
        help="Cost of labor for this maintenance",
        currency_field='currency_id'
    )
    parts_cost = fields.Monetary(
        string="Parts Cost",
        help="Cost of parts used in maintenance",
        currency_field='currency_id'
    )
    external_cost = fields.Monetary(
        string="External Service Cost",
        help="Cost of external services",
        currency_field='currency_id'
    )

    # === RECORDS MANAGEMENT INTEGRATION ===
    equipment_id = fields.Many2one(
        comodel_name='maintenance.equipment',
        string='Equipment',
        help="Equipment requiring maintenance"
    )
    maintenance_team_id = fields.Many2one(
        comodel_name='maintenance.team',
        string='Maintenance Team',
        help="Team responsible for this maintenance request"
    )
    records_container_id = fields.Many2one(
        comodel_name='records.container',
        string='Related Container',
        help="Records container associated with this maintenance"
    )
    priority = fields.Selection([
        ('0', 'Very Low'),
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High')
    ], string='Priority', default='1')

    @api.depends('labor_cost', 'parts_cost', 'external_cost')
    def _compute_total_cost(self):
        """Compute total cost from components."""
        for request in self:
            request.cost = request.labor_cost + request.parts_cost + request.external_cost

    def action_create_invoice(self):
        """Create invoice for maintenance costs."""
        self.ensure_one()
        if not self.cost:
            raise UserError(_("Cannot create invoice with zero cost."))

        invoice_vals = {
            'move_type': 'in_invoice',
            'partner_id': self.user_id.partner_id.id if self.user_id else self.env.company.partner_id.id,
            'invoice_date': fields.Date.context_today(self),
            'ref': _("Maintenance: %s") % self.name,
            'invoice_line_ids': [(0, 0, {
                'name': _("Maintenance Service - %s") % (self.equipment_id.name or self.name),
                'quantity': 1,
                'price_unit': self.cost,
            })]
        }

        invoice = self.env['account.move'].create(invoice_vals)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Maintenance Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def get_maintenance_costs_report(self, date_from=None, date_to=None):
        """Generate maintenance costs report."""
        domain = []
        if date_from:
            domain.append(('request_date', '>=', date_from))
        if date_to:
            domain.append(('request_date', '<=', date_to))

        requests = self.search(domain)
        total_cost = sum(requests.mapped('cost'))

        return {
            'total_requests': len(requests),
            'total_cost': total_cost,
            'average_cost': total_cost / len(requests) if requests else 0,
            'requests_data': requests.read(['name', 'cost', 'request_date', 'equipment_id'])
        }
