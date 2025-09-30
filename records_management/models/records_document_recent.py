from odoo import models, fields


class RecordsDocumentRecent(models.Model):
    _inherit = ['records.document', 'rm.recent.window.mixin']
    _name = 'records.document'  # reaffirm model name for multiple inheritance

    # Pseudo boolean recency & expiry search fields
    is_recent_30d_last_access = fields.Boolean(
        string='Accessed Last 30 Days',
        search='_search_is_recent_30d_last_access',
        help='True when last_access_date within last 30 days.'
    )
    expiring_30d_destruction = fields.Boolean(
        string='Destruction Next 30 Days',
        search='_search_expiring_30d_destruction',
        help='True when destruction eligible date is within next 30 days.'
    )

    def _rm_recent_reference_field_map(self):
        # Self-documenting keys used in dynamic search fields
        return {
            'create': 'create_date',
            'destruction': 'destruction_eligible_date',
            'last_access': 'last_access_date',
        }
