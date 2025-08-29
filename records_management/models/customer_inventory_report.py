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

    @api.model
    def generate_monthly_reports(self):
        """
        Generate monthly inventory reports for all customers.
        This method is called by the scheduled action.
        """
        try:
            self._generate_inventory_reports()
        except Exception as e:
            self.env['ir.logging'].create({
                'name': 'Monthly Report Generation Error',
                'type': 'server',
                'level': 'ERROR',
                'message': _('Error generating monthly inventory reports: %s') % str(e),
                'path': 'customer.inventory.report.wizard',
                'func': 'generate_monthly_reports',
            })
            raise

    def _generate_inventory_reports(self):
        """Internal method to generate inventory reports"""
        customers = self.env['res.partner'].search([('customer_rank', '>', 0)])

        generated_reports = 0
        for customer in customers:
            try:
                self._generate_customer_report(customer)
                generated_reports += 1
            except Exception as e:
                self.env['ir.logging'].create({
                    'name': 'Customer Report Error',
                    'type': 'server',
                    'level': 'ERROR',
                    'message': _('Error generating report for customer %s: %s') % (customer.name, str(e)),
                    'path': 'customer.inventory.report.wizard',
                    'func': '_generate_inventory_reports',
                })

        # Log success
        self.env['ir.logging'].create({
            'name': 'Monthly Report Generation',
            'type': 'server',
            'level': 'INFO',
            'message': _('Monthly inventory reports generated for %s customers') % generated_reports,
            'path': 'customer.inventory.report.wizard',
            'func': '_generate_inventory_reports',
        })

    def _generate_customer_report(self, customer):
        """Generate inventory report for a specific customer"""
        # Get customer's inventory items
        inventories = self.env['customer.inventory'].search([
            ('partner_id', '=', customer.id),
        ])

        if not inventories:
            return  # No items to report

        # Create wizard instance for report generation
        wizard = self.create({
            'partner_id': customer.id,
            'inventory_date_to': fields.Date.today(),
        })

        # Generate the report
        try:
            report_action = wizard.action_print_report()
            # Log individual report generation
            self.env['ir.logging'].create({
                'name': 'Customer Report Generated',
                'type': 'server',
                'level': 'INFO',
                'message': _('Inventory report generated for customer %s with %s inventory records') % (
                    customer.name, len(inventories)),
                'path': 'customer.inventory.report.wizard',
                'func': '_generate_customer_report',
            })
        except Exception as e:
            self.env['ir.logging'].create({
                'name': 'Customer Report Generation Failed',
                'type': 'server',
                'level': 'ERROR',
                'message': _('Failed to generate report for customer %s: %s') % (customer.name, str(e)),
                'path': 'customer.inventory.report.wizard',
                'func': '_generate_customer_report',
            })

    @api.model
    def run_monthly_inventory_report_automation(self):
        """
        Run the monthly inventory report automation workflow.
        This method is called by the scheduled action.
        """
        try:
            self._run_inventory_report_workflow()
        except Exception as e:
            self.env['ir.logging'].create({
                'name': 'Inventory Report Workflow Error',
                'type': 'server',
                'level': 'ERROR',
                'message': _('Error in inventory report automation workflow: %s') % str(e),
                'path': 'customer.inventory.report.wizard',
                'func': 'run_monthly_inventory_report_automation',
            })
            raise

    def _run_inventory_report_workflow(self):
        """Internal method to run inventory report workflow"""
        # Log workflow start
        self.env['ir.logging'].create({
            'name': 'Inventory Report Workflow',
            'type': 'server',
            'level': 'INFO',
            'message': _('Monthly inventory report automation workflow started'),
            'path': 'customer.inventory.report.wizard',
            'func': '_run_inventory_report_workflow',
        })

        # Generate reports for all customers
        self.generate_monthly_reports()

        # TODO: Implement additional workflow logic here
        # This could include:
        # - Sending report emails to customers
        # - Archiving old reports
        # - Generating summary reports

        # Log workflow completion
        self.env['ir.logging'].create({
            'name': 'Inventory Report Workflow',
            'type': 'server',
            'level': 'INFO',
            'message': _('Monthly inventory report automation workflow completed successfully'),
            'path': 'customer.inventory.report.wizard',
            'func': '_run_inventory_report_workflow',
        })
