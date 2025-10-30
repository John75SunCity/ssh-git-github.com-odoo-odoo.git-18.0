# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class TsheetsSyncWizard(models.TransientModel):
    _name = "qb.tsheets.sync.wizard"
    _description = "Quick TSheets Sync Wizard"

    config_id = fields.Many2one(
        comodel_name="qb.tsheets.sync.config",
        string="Configuration",
        required=True,
        default=lambda self: self.env["qb.tsheets.sync.config"].search([], limit=1),
    )
    message = fields.Html(string="Status", readonly=True)

    def action_sync_now(self):
        """Execute the sync and return the result"""
        self.ensure_one()
        if not self.config_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Configuration Required'),
                    'message': _('Please configure TSheets API settings first.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # Call the sync service
        service = self.env["qb.tsheets.sync.service"]
        result = service.manual_sync(self.config_id)
        
        # Return notification or action result
        return result or {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sync Complete'),
                'message': _('TSheets synchronization completed successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }
