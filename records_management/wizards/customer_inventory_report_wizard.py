# -*- coding: utf-8 -*-
"""
Customer Inventory Report Wizard

This wizard is used to generate customer inventory reports based on user-selected criteria.

Author: Records Management System
Version: 18.0.0.2.29
License: LGPL-3
"""

from odoo import models, fields, _
from odoo.exceptions import UserError

class CustomerInventoryReportWizard(models.TransientModel):
    _name = 'customer.inventory.report.wizard'
    _description = 'Customer Inventory Report Wizard'

    # ============================================================================
    # WIZARD FIELDS
    # ============================================================================
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True)
    department_id = fields.Many2one(comodel_name='records.department', string='Department', domain="[('partner_id', '=', partner_id)]")
    inventory_date_from = fields.Date(string='From Date')
    inventory_date_to = fields.Date(string='To Date', default=fields.Date.context_today)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, default=lambda self: self.env.company)

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
