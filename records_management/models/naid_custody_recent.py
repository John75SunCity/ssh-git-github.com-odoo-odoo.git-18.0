from odoo import models


class NaidCustodyRecent(models.Model):
    _inherit = ['naid.custody', 'rm.recent.window.mixin']
    _name = 'naid.custody'

    def _rm_recent_reference_field_map(self):
        return {
            'event': 'event_date',
            'create': 'create_date',
        }
