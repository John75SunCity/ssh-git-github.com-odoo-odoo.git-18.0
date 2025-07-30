# -*- coding: utf-8 -*-
"""
Records Location Report Wizard
"""

from odoo import models, fields, api, _


class RecordsLocationReportWizard(models.TransientModel):
    """
    Records Location Report Wizard
    """

    _name = "records.location.report.wizard"
    _description = "Records Location Report Wizard"

    # Core fields
    name = fields.Char(string="Report Name", default="Location Report")
    location_ids = fields.Many2many('records.location', string='Locations')
    date_from = fields.Date(string='Date From', default=fields.Date.today)
    date_to = fields.Date(string='Date To', default=fields.Date.today)
    report_type = fields.Selection([
        ('summary', 'Summary'),
        ('detailed', 'Detailed')
    ], string='Report Type', default='summary')

    def action_generate_report(self):
        """Generate the location report"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Location Report',
            'res_model': 'records.location',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.location_ids.ids)] if self.location_ids else [],
        }
