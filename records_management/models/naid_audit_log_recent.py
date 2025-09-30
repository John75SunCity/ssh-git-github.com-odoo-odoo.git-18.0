from odoo import models, fields


class NaidAuditLogRecent(models.Model):
    _inherit = ['naid.audit.log', 'rm.recent.window.mixin']
    _name = 'naid.audit.log'

    # Pseudo boolean fields enabling search view filters
    is_recent_7d_create = fields.Boolean(
        string='Created Last 7 Days',
        search='_search_is_recent_7d_create',
        help='True when create_date is within the last 7 days.',
    )
    is_recent_30d_create = fields.Boolean(
        string='Created Last 30 Days',
        search='_search_is_recent_30d_create',
        help='True when create_date is within the last 30 days.',
    )

    def _rm_recent_reference_field_map(self):
        return {
            'create': 'create_date',
        }
