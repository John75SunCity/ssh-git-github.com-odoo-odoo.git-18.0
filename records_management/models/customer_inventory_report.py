# -*- coding: utf-8 -*-
"""
Customer Inventory Report Module

This model is used to generate, configure, and store customer inventory reports.
It defines the parameters for the report and tracks its generation status.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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
    department_id = fields.Many2one(
        "records.department", string="Department", domain="[('partner_id', '=', partner_id)]"
    )
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

        # ============================================================================
        # ADVANCED WORKFLOW LOGIC - Implemented with Odoo 18.0 patterns
        # ============================================================================

        # 1. Email reports to customers automatically
        self._send_reports_to_customers()

        # 2. Archive old reports (older than retention period)
        self._archive_old_reports()

        # 3. Generate executive summary reports
        self._generate_summary_reports()

        # 4. Create follow-up activities for incomplete reports
        self._create_followup_activities()

        # Log workflow completion
        self.env['ir.logging'].create({
            'name': 'Inventory Report Workflow',
            'type': 'server',
            'level': 'INFO',
            'message': _('Monthly inventory report automation workflow completed successfully'),
            'path': 'customer.inventory.report.wizard',
            'func': '_run_inventory_report_workflow',
        })

    # ============================================================================
    # WORKFLOW IMPLEMENTATION METHODS - Odoo 18.0 Best Practices
    # ============================================================================

    def _send_reports_to_customers(self):
        """Send generated reports to customers via email using Odoo 18.0 mail system"""
        month_start = fields.Datetime.to_string(fields.Date.today().replace(day=1))
        recent_reports = self.env["customer.inventory.report"].search(
            [("create_date", ">=", month_start), ("state", "=", "completed")]
        )

        for report in recent_reports:
            if report.partner_id.email:
                # Use Odoo 18.0 mail template system
                template = self.env.ref("records_management.email_template_inventory_report", raise_if_not_found=False)
                if template:
                    template.send_mail(report.id, force_send=True)
                    report.message_post(body=_("Inventory report sent to customer via email"))

    def _archive_old_reports(self):
        """Archive reports older than retention period (e.g., 2 years)"""
        retention_date = fields.Datetime.subtract(fields.Datetime.now(), days=730)  # 2 years
        retention_date = fields.Datetime.now() - timedelta(days=730)  # 2 years
        old_reports = self.env["customer.inventory.report"].search(
            [("create_date", "<", retention_date), ("active", "=", True)]
        )

        if old_reports:
            old_reports.write({"active": False})
            _logger.info("Archived %s old inventory reports" % len(old_reports))

    def _generate_summary_reports(self):
        """Generate executive summary reports for management"""
        # Use Odoo's date utilities to get the first day of the current month as a string
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        month_start_str = fields.Datetime.to_string(fields.Datetime.from_string(str(month_start)))
        summary_data = self.env["customer.inventory.report"].read_group(
            [("create_date", ">=", month_start_str)],
            ["partner_id", "total_containers", "total_documents"],
            ["partner_id"],
        )

        # Create summary in system parameter or log for now
        summary_text = "Executive Summary Data: %s reports processed" % len(summary_data)
        self.env["ir.logging"].create(
            {
                "name": "Executive Summary",
                "type": "server",
                "level": "INFO",
                "message": summary_text,
                "path": "customer.inventory.report.wizard",
            }
        )

    def _create_followup_activities(self):
        """Create follow-up activities for incomplete or problematic reports"""

        month_start = fields.Datetime.to_string(fields.Date.today().replace(day=1))
        incomplete_reports = self.env["customer.inventory.report"].search(
            [("create_date", ">=", month_start), ("state", "in", ["draft", "error"])]
        )

        activity_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
        if not activity_type:
            return

        for report in incomplete_reports:
            # Check if activity already exists
            existing_activity = self.env["mail.activity"].search(
                [
                    ("res_model", "=", "customer.inventory.report"),
                    ("res_id", "=", report.id),
                    ("activity_type_id", "=", activity_type.id),
                    ("user_id", "=", self.env.user.id),
                ],
                limit=1,
            )

            if not existing_activity:
                self.env["mail.activity"].create(
                    {
                        "res_model": "customer.inventory.report",
                        "res_id": report.id,
                        "user_id": self.env.user.id,
                        "date_deadline": (fields.Date.to_date(fields.Date.today()) + timedelta(days=3)),
                    }
                )

    @api.model
    def cron_generate_monthly_reports(self):
        """Cron job to automatically generate monthly inventory reports"""
        try:
            wizard = self.create({})
            wizard.run_monthly_inventory_report_automation()
            return True
        except Exception as e:
            _logger.error("Error in monthly inventory report cron: %s" % e)
            return False
        except Exception as e:
            _logger.error("Error in monthly inventory report cron: %s" % e)
            return False
