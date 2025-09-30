from odoo import models, fields


class NaidCustodyRecent(models.Model):
    _inherit = ['naid.custody', 'rm.recent.window.mixin']
    _name = 'naid.custody'

    # Pseudo boolean fields for event recency filters
    is_recent_7d_event = fields.Boolean(
        string='Events Last 7 Days',
        search='_search_is_recent_7d_event',
        help='True when event_date is within the last 7 days.'
    )
    is_recent_30d_event = fields.Boolean(
        string='Events Last 30 Days',
        search='_search_is_recent_30d_event',
        help='True when event_date is within the last 30 days.'
    )

    def _rm_recent_reference_field_map(self):
        return {
            'event': 'event_date',
            'create': 'create_date',
        }
