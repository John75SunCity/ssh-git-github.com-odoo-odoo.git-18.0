# -*- coding: utf-8 -*-
from odoo import models, fields


class HardDriveScanWizard(models.TransientModel):
    _name = 'hard.drive.scan.wizard'
    _description = 'Hard Drive Scan Wizard'

    # Wizard Fields
    name = fields.Char(string='Name', required=True)

    # Selection Options
    action_type = fields.Selection([
        ('execute', 'Execute'),
        ('cancel', 'Cancel')
    ], string='Action', default='execute')

    # Text Fields
    notes = fields.Text(string='Notes')

    def action_execute(self):
        """Execute the wizard action."""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        """Cancel the wizard."""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
    def action_cancel(self):
        """Cancel the wizard."""

        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
