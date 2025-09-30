from odoo import models


class NaidAuditLogRecent(models.Model):
    _inherit = ['naid.audit.log', 'rm.recent.window.mixin']
    _name = 'naid.audit.log'

    def _rm_recent_reference_field_map(self):
        return {
            'create': 'create_date',
        }
