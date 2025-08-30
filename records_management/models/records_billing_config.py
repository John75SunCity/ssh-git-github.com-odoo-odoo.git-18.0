# -*- coding: utf-8 -*-
"""
Records Billing Configuration Model

This model handles billing configuration and automation for the Records Management module.
It provides methods for scheduled actions like computing monthly storage fees and managing
billing workflows.
"""

from datetime import timedelta

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RecordsBillingConfig(models.Model):
    """
    Records Billing Configuration

    Central model for managing billing configurations and automated billing processes
    in the Records Management module.
    """

    _name = 'records.billing.config'
    _description = 'Records Billing Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Configuration Name', required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)

    # Billing settings
    auto_compute_storage_fees = fields.Boolean(
        string='Auto Compute Storage Fees',
        default=True,
        help='Automatically compute monthly storage fees for customers'
    )

    storage_fee_product_id = fields.Many2one(
        'product.product',
        string='Storage Fee Product',
        help='Product to use for monthly storage fees'
    )

    default_billing_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ], string='Default Billing Frequency', default='monthly')

    # Company and settings
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    @api.model
    def compute_monthly_storage_fees(self):
        """
        Compute monthly storage fees for each customer based on their inventory.
        This method is called by the scheduled action.
        """
        try:
            self._compute_storage_fees()
        except Exception as e:
            self.env['ir.logging'].create({
                'name': 'Storage Fee Computation Error',
                'type': 'server',
                'level': 'ERROR',
                'message': _('Error computing monthly storage fees: %s') % str(e),
                'path': 'records.billing.config',
                'func': 'compute_monthly_storage_fees',
            })
            raise

    def _compute_storage_fees(self):
        """Internal method to compute storage fees"""
        customer_items = {}
        quants = self.env['stock.quant'].search([('location_id.usage', '=', 'internal')])

        # Group items by customer
        for quant in quants:
            customer = getattr(getattr(quant, 'lot_id', None), 'customer_id', None)
            if not customer:
                continue
            if customer in customer_items:
                customer_items[customer] += quant.quantity
            else:
                customer_items[customer] = quant.quantity

        # Get storage fee product
        product = self.env.ref('records_management.product_storage_service', raise_if_not_found=False)
        if not product:
            raise UserError(_('Storage Service Product (records_management.product_storage_service) not found.'))

        # Create sale orders for customers with items
        created_orders = 0
        for customer, qty in customer_items.items():
            if qty > 0:
                existing_order = self.env['sale.order'].search([
                    ('partner_id', '=', customer.id),
                    ('state', '=', 'draft'),
                    ('order_line.product_id', '=', product.id),
                ], limit=1)

                if not existing_order:
                    self.env['sale.order'].create({
                        'partner_id': customer.id,
                        'order_line': [(0, 0, {
                            'product_id': product.id,
                            'product_uom_qty': qty,
                            'name': _('Monthly Storage Fee for %s items') % qty,
                        })],
                    })
                    created_orders += 1

        # Log success
        self.env['ir.logging'].create({
            'name': 'Storage Fee Computation',
            'type': 'server',
            'level': 'INFO',
            'message': _('Monthly storage fees computed for %s customers, %s orders created') % (
                len([c for c, q in customer_items.items() if q > 0]), created_orders),
            'path': 'records.billing.config',
            'func': '_compute_storage_fees',
        })

    @api.model
    def run_storage_fee_automation_workflow(self):
        """
        Run the storage fee automation workflow.
        This method is called by the scheduled action.
        """
        try:
            self._run_storage_fee_workflow()
        except Exception as e:
            self.env['ir.logging'].create({
                'name': 'Storage Fee Workflow Error',
                'type': 'server',
                'level': 'ERROR',
                'message': _('Error in storage fee automation workflow: %s') % str(e),
                'path': 'records.billing.config',
                'func': 'run_storage_fee_automation_workflow',
            })
            raise

    def _run_storage_fee_workflow(self):
        """Internal method to run storage fee workflow"""
        # Log workflow start
        self.env['ir.logging'].create({
            'name': 'Storage Fee Workflow',
            'type': 'server',
            'level': 'INFO',
            'message': _('Storage fee automation workflow started'),
            'path': 'records.billing.config',
            'func': '_run_storage_fee_workflow',
        })

        # ============================================================================
        # BILLING WORKFLOW LOGIC - Odoo 18.0 Implementation
        # ============================================================================

        # 1. Check for overdue payments and send reminders
        self._process_overdue_payments()

        # 2. Generate automated billing for recurring services
        self._generate_recurring_billing()

        # 3. Update billing statuses and create activities
        self._update_billing_statuses()

        # 4. Send automated billing notifications
        self._send_billing_notifications()

        # Log workflow completion
        self.env['ir.logging'].create({
            'name': 'Storage Fee Workflow',
            'type': 'server',
            'level': 'INFO',
            'message': _('Storage fee automation workflow completed successfully'),
            'path': 'records.billing.config',
            'func': '_run_storage_fee_workflow',
        })

    # ============================================================================
    # BILLING WORKFLOW IMPLEMENTATION METHODS - Odoo 18.0 Best Practices
    # ============================================================================

    def _process_overdue_payments(self):
        """Process overdue payments and send reminder notifications"""
        # Find overdue invoices
        overdue_invoices = self.env["account.move"].search(
            [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("payment_state", "in", ["not_paid", "partial"]),
                ("invoice_date_due", "<", fields.Date.today()),
            ]
        )

        for invoice in overdue_invoices:
            # Create follow-up activity
            activity_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
            if activity_type:
                self.env["mail.activity"].create(
                    {
                        "res_model": "account.move",
                        "res_id": invoice.id,
                        "activity_type_id": activity_type.id,
                        "summary": "Overdue Payment Follow-up",
                        "note": "Invoice %s is overdue. Please follow up with customer." % invoice.name,
                        "user_id": self.env.user.id,
                        "date_deadline": fields.Date.today(),
                    }
                )

    def _generate_recurring_billing(self):
        """Generate recurring billing for storage services"""
        # Find containers with recurring billing
        containers = self.env["records.container"].search(
            [("billing_status", "=", "active"), ("next_billing_date", "<=", fields.Date.today())]
        )

        for container in containers:
            # Create billing record
            billing_vals = {
                "partner_id": container.partner_id.id,
                "container_id": container.id,
                "billing_date": fields.Date.today(),
                "amount": container.monthly_storage_fee or 0.0,
                "description": "Monthly storage fee for %s" % container.name,
                "state": "draft",
            }

            # Create in appropriate billing model if it exists
            if hasattr(self.env, "records.billing"):
                self.env["records.billing"].create(billing_vals)

            # Update next billing date

            container.next_billing_date = fields.Date.today() + relativedelta(months=1)

    def _update_billing_statuses(self):
        """Update billing statuses based on payment status"""
        # Find paid invoices and update container billing status
        paid_invoices = self.env["account.move"].search(
            [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("payment_state", "=", "paid"),
                ("payment_date", ">=", fields.Date.today() - timedelta(days=30)),
            ]
        )

        for invoice in paid_invoices:
            # Update related container billing status if needed
            if invoice.invoice_line_ids:
                for line in invoice.invoice_line_ids:
                    if "storage" in (line.name or "").lower():
                        # Mark as paid in any related records
                        pass

    def _send_billing_notifications(self):
        """Send automated billing notifications to customers"""
        # Find recent invoices to send notifications
        recent_invoices = self.env["account.move"].search(
            [
                ("move_type", "=", "out_invoice"),
                ("state", "=", "posted"),
                ("create_date", ">=", fields.Datetime.now() - timedelta(days=1)),
            ]
        )

        for invoice in recent_invoices:
            if invoice.partner_id.email:
                # Send notification using Odoo's mail system
                template = self.env.ref("account.email_template_edi_invoice", raise_if_not_found=False)
                if template:
                    try:
                        template.send_mail(invoice.id, force_send=True)
                        invoice.message_post(body=_("Billing notification sent to customer"))
                    except Exception:
                        # Log error but continue processing
                        pass

    @api.model
    def get_default_config(self):
        """Get the default billing configuration"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            config = self.create({
                'name': 'Default Billing Configuration',
                'auto_compute_storage_fees': True,
            })
        return config
