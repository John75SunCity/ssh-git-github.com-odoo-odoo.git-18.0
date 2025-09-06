from odoo import models, fields, api, _


class DocumentRetrievalTeam(models.Model):
    # Removed dedicated _name; we only extend maintenance.team directly.
    _inherit = 'maintenance.team'
    _description = 'Document Retrieval Team'

    # ============================================================================
    # ADD ONLY THE FIELDS THAT ARE NOT ALREADY IN maintenance.team
    # ============================================================================

    # Example of adding a specialization field
    retrieval_specialization = fields.Selection([
        ('standard', 'Standard'),
        ('secure', 'Secure/Confidential'),
        ('bulk', 'Bulk Retrieval'),
        ('scan_on_demand', 'Scan-on-Demand')
    ], string='Retrieval Specialization', default='standard')

    # Example of adding a link to retrieval work orders
    retrieval_work_order_ids = fields.One2many(
        'records.retrieval.work.order',
        'retrieval_team_id',
        string='Retrieval Work Orders'
    )

    # Computed fields for team-specific metrics
    active_retrievals_count = fields.Integer(
        string="Active Retrievals",
        compute='_compute_retrieval_metrics'
    )
    average_retrieval_time = fields.Float(
        string="Avg. Retrieval Time (Hours)",
        compute='_compute_retrieval_metrics',
        help="Average time from creation to completion for retrieval work orders."
    )

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================

    @api.depends('retrieval_work_order_ids.state', 'retrieval_work_order_ids.completion_date', 'retrieval_work_order_ids.create_date')
    def _compute_retrieval_metrics(self):
        for team in self:
            active_orders = team.retrieval_work_order_ids.filtered(
                lambda wo: wo.state in ['pending', 'in_progress']
            )
            team.active_retrievals_count = len(active_orders)

            completed_orders = team.retrieval_work_order_ids.filtered(
                lambda wo: wo.state == 'completed' and wo.completion_date and wo.create_date
            )

            if completed_orders:
                total_duration_hours = 0
                for order in completed_orders:
                    duration = order.completion_date - order.create_date
                    total_duration_hours += duration.total_seconds() / 3600
                team.average_retrieval_time = total_duration_hours / len(completed_orders)
            else:
                team.average_retrieval_time = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_view_retrieval_work_orders(self):
        """Action to open the work orders assigned to this team."""
        self.ensure_one()
        return {
            'name': _('Retrieval Work Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.retrieval.work.order',
            'view_mode': 'tree,form,kanban',
            'domain': [('id', 'in', self.retrieval_work_order_ids.ids)],
        }

    # Additional placeholders migrated from aggregate placeholder file
    def action_view_team_members(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Team Members'),
            'res_model': 'hr.employee',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.member_ids.ids)] if hasattr(self, 'member_ids') else [('id', '=', 0)],
        }

    def action_view_performance_metrics(self):
        self.ensure_one()
        return False  # Placeholder for future dashboard

    def action_view_work_orders(self):
        self.ensure_one()
        return self.action_view_retrieval_work_orders()
