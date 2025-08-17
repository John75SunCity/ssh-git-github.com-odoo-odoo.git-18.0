# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RecordsBulkUserImport(models.TransientModel):
    _name = 'records.bulk.user.import'
    _description = 'Records Bulk User Import'

    name = fields.Char(string='Name', default='Bulk User Import'),
    csv_file = fields.Binary(string='CSV File', required=True),
    filename = fields.Char(string='Filename')

    def action_import_users(self):
        # Placeholder for import logic:
            pass
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
