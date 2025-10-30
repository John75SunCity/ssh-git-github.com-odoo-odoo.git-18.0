# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from datetime import datetime, timedelta


class TsheetsSyncWizard(models.TransientModel):
    _name = "qb.tsheets.sync.wizard"
    _description = "Quick TSheets Sync Wizard"

    config_id = fields.Many2one(
        comodel_name="qb.tsheets.sync.config",
        string="Configuration",
        required=True,
        default=lambda self: self.env["qb.tsheets.sync.config"].search([], limit=1),
    )
    date_from = fields.Date(
        string="Sync From Date",
        required=True,
        default=lambda self: fields.Date.today() - timedelta(days=7),
        help="Start date for fetching timesheets from TSheets"
    )
    date_to = fields.Date(
        string="Sync To Date",
        required=True,
        default=fields.Date.today,
        help="End date for fetching timesheets from TSheets"
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
        
        # Call the sync service with date range
        service = self.env["qb.tsheets.sync.service"]
        result = service.manual_sync(self.config_id, date_from=self.date_from, date_to=self.date_to)
        
        # Return notification or action result
        return result or {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sync Complete'),
                'message': _('TSheets synchronization completed successfully. Check Sync Logs for details.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_skip_sync(self):
        """Skip sync and close the wizard"""
        return {'type': 'ir.actions.act_window_close'}
