from odoo import models


class RecordsDocumentRecent(models.Model):
    _inherit = ['records.document', 'rm.recent.window.mixin']
    _name = 'records.document'  # reaffirm model name for multiple inheritance

    def _rm_recent_reference_field_map(self):
        # Self-documenting keys used in dynamic search fields
        return {
            'create': 'create_date',
            'destruction': 'destruction_eligible_date',
            'last_access': 'last_access_date',
        }
