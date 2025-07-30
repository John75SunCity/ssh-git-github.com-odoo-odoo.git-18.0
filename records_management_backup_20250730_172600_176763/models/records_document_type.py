# -*- coding: utf-8 -*-
""",
Record Document Type
"""

from odoo import models, fields, api, _


class RecordsDocumentType(models.Model):
    """,
    Record Document Type
    """

    _name = "records.document.type",
    _description = "Record Document Type",
    _inherit = ['mail.thread', 'mail.activity.mixin'],
    _order = "name"

    # Core fields
    name = fields.
            'type': 'ir.actions.act_window',
            'name': f'Documents - {self.name(
            'type': 'ir.actions.act_window',
            'name': f'Documents - (self.name)',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('document_type_id', '=', self.id)],
            'context': ('default_document_type_id': self.id)
        )

    def action_confirm(self):
        pass
    """Confirm the record""",
        self.write(('state': 'confirmed'))

    def action_done(self):
        pass
    """Mark as done""",
        self.write(('state': 'done'))
