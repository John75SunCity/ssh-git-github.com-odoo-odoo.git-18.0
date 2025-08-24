# -*- coding: utf-8 -*-
"""
Customer Inventory Report Module

This model is used to generate, configure, and store customer inventory reports.
It defines the parameters for the report and tracks its generation status.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CustomerInventoryReport(models.AbstractModel):
    _name = 'report.records_management.report_customer_inventory'
    _description = 'Customer Inventory Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        This method is called by the Odoo reporting engine to gather the data
        for the PDF report.
        """
        docs = self.env['customer.inventory'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'customer.inventory',
            'docs': docs,
            'data': data,
        }

class CustomerInventoryReportWizard(models.TransientModel):
    _name = 'customer.inventory.report.wizard'
    _description = 'Customer Inventory Report Wizard'

    # ============================================================================
    # WIZARD FIELDS
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    department_id = fields.Many2one('records.department', string='Department', domain="[('partner_id', '=', partner_id)]")
    inventory_date_from = fields.Date(string='From Date')
    inventory_date_to = fields.Date(string='To Date', default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_print_report(self):
        """
        Generates and returns the PDF report based on the wizard's criteria.
        """
        self.ensure_one()

        domain = [('partner_id', '=', self.partner_id.id)]
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        if self.inventory_date_from:
            domain.append(('inventory_date', '>=', self.inventory_date_from))
        if self.inventory_date_to:
            domain.append(('inventory_date', '<=', self.inventory_date_to))

        inventories = self.env['customer.inventory'].search(domain)

        if not inventories:
            raise UserError(_("No inventory records found for the selected criteria."))

        return self.env.ref('records_management.action_report_customer_inventory').report_action(inventories)
