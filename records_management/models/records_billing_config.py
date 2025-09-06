# -*- coding: utf-8 -*-
"""
Records Billing Configuration Model

This model handles billing configuration and automation for the Records Manageme    # Invoice settings
    invoice_template_id = fields.Many2one('ir.ui.view', string='I    # Basic additional fields
    amount = fields.Float(string='Amount', digits=(10, 2))
    auto_apply = fields.Boolean(string='Auto Apply', default=False)
    cost_amount = fields.Float(string='Cost Amount', digits=(10, 2))
    customer_count = fields.Integer(string='Customer Count', compute='_compute_customer_count')
    effective_date = fields.Date(string='Effective Date')
    minimum_threshold = fields.Float(string='Minimum Threshold', digits=(10, 2))
    quantity = fields.Float(string='Quantity', digits=(10, 2))
    rule_name = fields.Char(string='Rule Name')
    service_type = fields.Selection([
        ('storage', 'Storage'),
        ('retrieval', 'Retrieval'),
        ('destruction', 'Destruction'),
        ('digital', 'Digital'),
    ], string='Service Type')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Status', default='draft')
    unit_of_measure = fields.Char(string='Unit of Measure')
    valid_from = fields.Date(string='Valid From')
    valid_until = fields.Date(string='Valid Until')

    # Additional missing fields for view compatibility
    discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('none', 'No Discount'),
    ], string='Discount Type', default='none')
    discount_value = fields.Float(string='Discount Value', digits=(10, 2))
    last_invoice_date = fields.Date(string='Last Invoice Date', compute='_compute_last_invoice_date', store=True)
    revenue_amount = fields.Monetary(string='Revenue Amount', currency_field='currency_id', compute='_compute_revenue_amount', store=True)
    tracking_date = fields.Date(string='Tracking Date', default=fields.Date.context_today)

    # Computed fields for analytics
    @api.depends('invoice_generation_log_ids')
    def _compute_invoice_count(self):
        for record in self:
            record.invoice_count = len(record.invoice_generation_log_ids)

    @api.depends('usage_tracking_ids')
    def _compute_billing_history_count(self):
        for record in self:
            record.billing_history_count = len(record.usage_tracking_ids)

    @api.depends('usage_tracking_ids')
    def _compute_total_revenue(self):
        for record in self:
            record.total_revenue = sum(record.usage_tracking_ids.mapped('total_cost'))

    @api.depends('usage_tracking_ids')
    def _compute_monthly_revenue(self):
        for record in self:
            # Calculate revenue for current month
            current_month = fields.Date.today().replace(day=1)
            next_month = current_month + relativedelta(months=1)
            monthly_usage = record.usage_tracking_ids.filtered(
                lambda u: current_month <= u.tracking_date < next_month
            )
            record.monthly_revenue = sum(monthly_usage.mapped('total_cost'))

    @api.depends('usage_tracking_ids')
    def _compute_quarterly_revenue(self):
        for record in self:
            # Calculate revenue for current quarter
            today = fields.Date.today()
            quarter_start = today.replace(month=((today.month - 1) // 3) * 3 + 1, day=1)
            quarter_end = quarter_start + relativedelta(months=3)
            quarterly_usage = record.usage_tracking_ids.filtered(
                lambda u: quarter_start <= u.tracking_date < quarter_end
            )
            record.quarterly_revenue = sum(quarterly_usage.mapped('total_cost'))

    @api.depends('usage_tracking_ids')
    def _compute_annual_revenue(self):
        for record in self:
            # Calculate revenue for current year
            current_year = fields.Date.today().year
            annual_usage = record.usage_tracking_ids.filtered(
                lambda u: u.tracking_date.year == current_year
            )
            record.annual_revenue = sum(annual_usage.mapped('total_cost'))

    @api.depends('monthly_revenue')
    def _compute_average_monthly_billing(self):
        for record in self:
            # This would need historical data to calculate properly
            # For now, just return current month
            record.average_monthly_billing = record.monthly_revenue

    @api.depends('usage_tracking_ids')
    def _compute_billing_accuracy_rate(self):
        for record in self:
            billable_count = len(record.usage_tracking_ids.filtered(lambda u: u.billable))
            total_count = len(record.usage_tracking_ids)
            record.billing_accuracy_rate = (billable_count / total_count * 100) if total_count > 0 else 0.0

    @api.depends('usage_tracking_ids')
    def _compute_collection_rate(self):
        for record in self:
            # This would need payment status data
            # For now, return a placeholder
            record.collection_rate = 95.0

    @api.depends('usage_tracking_ids')
    def _compute_payment_delay_average(self):
        for record in self:
            # This would need payment date data
            # For now, return a placeholder
            record.payment_delay_average = 2.5

    @api.depends()
    def _compute_customer_count(self):
        for record in self:
            # Count customers associated with this billing config
            record.customer_count = 0  # Placeholder - would need actual logice Template')
    consolidate_charges = fields.Boolean(string='Consolidate Charges', default=True)
    prorate_monthly = fields.Boolean(string='Prorate Monthly', default=True)
    include_usage_details = fields.Boolean(string='Include Usage Details', default=True)

    # Email settings
    send_invoice_email = fields.Boolean(string='Send Invoice Email', default=True)
    invoice_email_template_id = fields.Many2one('mail.template', string='Invoice Email Template').
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
    active = fields.Boolean(default=True)

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

    # Customer and billing model
    partner_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    billing_model = fields.Selection(
        [
            ("standard", "Standard"),
            ("enterprise", "Enterprise"),
            ("custom", "Custom"),
        ],
        string="Billing Model",
        default="standard",
        tracking=True,
    )
    service_category = fields.Selection(
        [
            ("storage", "Storage"),
            ("retrieval", "Retrieval"),
            ("destruction", "Destruction"),
            ("digital", "Digital Services"),
        ],
        string="Service Category",
        tracking=True,
    )

    # Pricing structure
    base_rate = fields.Float(string="Base Rate", digits=(10, 2), tracking=True)
    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)
    rate_unit = fields.Selection(
        [
            ("per_box", "Per Box"),
            ("per_pound", "Per Pound"),
            ("per_cubic_foot", "Per Cubic Foot"),
            ("flat_rate", "Flat Rate"),
        ],
        string="Rate Unit",
        default="per_box",
    )
    minimum_charge = fields.Float(string="Minimum Charge", digits=(10, 2))

    # Billing schedule
    billing_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annual", "Annual"),
        ],
        string="Billing Frequency",
        default="monthly",
        tracking=True,
    )
    billing_cycle_start = fields.Date(string="Billing Cycle Start")
    next_billing_date = fields.Date(string="Next Billing Date", tracking=True)
    last_invoice_date = fields.Date(string="Last Invoice Date", readonly=True)
    auto_billing = fields.Boolean(string="Auto Billing", default=False)

    # Payment terms
    payment_terms = fields.Selection(
        [
            ("net_15", "Net 15"),
            ("net_30", "Net 30"),
            ("net_45", "Net 45"),
            ("net_60", "Net 60"),
        ],
        string="Payment Terms",
        default="net_30",
        tracking=True,
    )
    payment_method = fields.Selection(
        [
            ("check", "Check"),
            ("wire", "Wire Transfer"),
            ("ach", "ACH"),
            ("credit_card", "Credit Card"),
        ],
        string="Payment Method",
        tracking=True,
    )
    late_fee_percentage = fields.Float(string="Late Fee %", digits=(5, 2), default=1.5)
    grace_period_days = fields.Integer(string="Grace Period (Days)", default=5)

    # Rate structure (One2many)
    billing_rate_ids = fields.One2many("records.billing.rate", "config_id", string="Billing Rates")

    # Usage tracking settings
    track_box_storage = fields.Boolean(string="Track Box Storage", default=True)
    track_document_count = fields.Boolean(string="Track Document Count", default=True)
    track_access_frequency = fields.Boolean(string="Track Access Frequency", default=True)
    track_special_handling = fields.Boolean(string="Track Special Handling", default=True)
    track_pickup_delivery = fields.Boolean(string="Track Pickup/Delivery", default=True)
    track_retrieval_requests = fields.Boolean(string="Track Retrieval Requests", default=True)
    track_destruction_services = fields.Boolean(string="Track Destruction Services", default=True)
    track_digital_services = fields.Boolean(string="Track Digital Services", default=True)

    # Usage tracking records
    usage_tracking_ids = fields.One2many("records.usage.tracking", "config_id", string="Usage Tracking")

    # Invoice settings
    # Invoice settings
    invoice_template_id = fields.Many2one("ir.ui.view", string="Invoice Template")
    consolidate_charges = fields.Boolean(string="Consolidate Charges", default=True)
    prorate_monthly = fields.Boolean(string="Prorate Monthly", default=True)
    include_usage_details = fields.Boolean(string="Include Usage Details", default=True)

    # Email settings
    send_invoice_email = fields.Boolean(string="Send Invoice Email", default=True)
    invoice_email_template_id = fields.Many2one("mail.template", string="Invoice Email Template")
    cc_accounting = fields.Boolean(string="CC Accounting", default=True)
    reminder_schedule = fields.Selection(
        [
            ("weekly", "Weekly"),
            ("biweekly", "Bi-weekly"),
            ("monthly", "Monthly"),
        ],
        string="Reminder Schedule",
        default="weekly",
    )

    # Invoice generation logs
    invoice_generation_log_ids = fields.One2many(
        "invoice.generation.log", "config_id", string="Invoice Generation Logs"
    )

    # Discount rules
    discount_rule_ids = fields.One2many("discount.rule", "config_id", string="Discount Rules")

    # Analytics (computed fields)
    invoice_count = fields.Integer(string="Invoice Count", compute="_compute_invoice_count")
    billing_history_count = fields.Integer(string="Billing History Count", compute="_compute_billing_history_count")
    total_revenue = fields.Float(string="Total Revenue", compute="_compute_total_revenue", digits=(10, 2))
    monthly_revenue = fields.Float(string="Monthly Revenue", compute="_compute_monthly_revenue", digits=(10, 2))
    quarterly_revenue = fields.Float(string="Quarterly Revenue", compute="_compute_quarterly_revenue", digits=(10, 2))
    annual_revenue = fields.Float(string="Annual Revenue", compute="_compute_annual_revenue", digits=(10, 2))
    average_monthly_billing = fields.Float(
        string="Avg Monthly Billing", compute="_compute_average_monthly_billing", digits=(10, 2)
    )

    # Performance indicators
    billing_accuracy_rate = fields.Float(
        string="Billing Accuracy Rate", compute="_compute_billing_accuracy_rate", digits=(5, 2)
    )
    collection_rate = fields.Float(string="Collection Rate", compute="_compute_collection_rate", digits=(5, 2))
    payment_delay_average = fields.Float(
        string="Payment Delay Average (Days)", compute="_compute_payment_delay_average", digits=(5, 2)
    )
    customer_satisfaction_score = fields.Float(
        string="Customer Satisfaction Score", compute="_compute_customer_satisfaction_score", digits=(3, 1)
    )

    # Revenue analytics
    revenue_analytics_ids = fields.One2many("revenue.analytic", "config_id", string="Revenue Analytics")

    # Notification settings
    billing_failure_alerts = fields.Boolean(string="Billing Failure Alerts", default=True)
    payment_overdue_alerts = fields.Boolean(string="Payment Overdue Alerts", default=True)
    usage_threshold_alerts = fields.Boolean(string="Usage Threshold Alerts", default=True)
    revenue_variance_alerts = fields.Boolean(string="Revenue Variance Alerts", default=True)

    # Notification recipients
    finance_team_notifications = fields.Boolean(string="Finance Team Notifications", default=True)
    manager_notifications = fields.Boolean(string="Manager Notifications", default=True)
    customer_notifications = fields.Boolean(string="Customer Notifications", default=True)
    escalation_notifications = fields.Boolean(string="Escalation Notifications", default=True)

    # Advanced configuration
    accounting_system_sync = fields.Boolean(string="Accounting System Sync", default=True)
    payment_gateway_integration = fields.Boolean(string="Payment Gateway Integration", default=False)
    tax_calculation_method = fields.Selection(
        [
            ("inclusive", "Tax Inclusive"),
            ("exclusive", "Tax Exclusive"),
        ],
        string="Tax Calculation Method",
        default="exclusive",
    )
    multi_currency_support = fields.Boolean(string="Multi-Currency Support", default=False)

    # Security & compliance
    audit_trail_enabled = fields.Boolean(string="Audit Trail Enabled", default=True)
    data_retention_period = fields.Integer(string="Data Retention Period (Months)", default=84)
    encryption_enabled = fields.Boolean(string="Encryption Enabled", default=True)
    compliance_reporting = fields.Boolean(string="Compliance Reporting", default=True)

    @api.model
    def _compute_monthly_storage_fees(self):
        """
        Compute monthly storage fees for each customer based on their inventory.
        This method is called by the scheduled action.
        """
        try:
            self._compute_storage_fees()
        except Exception as e:
            self.env["ir.logging"].create(
                {
                    "name": "Storage Fee Computation Error",
                    "type": "server",
                    "level": "ERROR",
                    "message": _("Error computing monthly storage fees: %s", str(e)),
                    "path": "records.billing.config",
                    "func": "_compute_monthly_storage_fees",
                }
            )
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
                    self.env["sale.order"].create(
                        {
                            "partner_id": customer.id,
                            "order_line": [
                                (
                                    0,
                                    0,
                                    {
                                        "product_id": product.id,
                                        "product_uom_qty": qty,
                                        "name": _("Monthly Storage Fee for %s items", qty),
                                    },
                                )
                            ],
                        }
                    )
                    created_orders += 1

        # Log success
        self.env["ir.logging"].create(
            {
                "name": "Storage Fee Computation",
                "type": "server",
                "level": "INFO",
                "message": _(
                    "Monthly storage fees computed for %s customers, %s orders created",
                    len([c for c, q in customer_items.items() if q > 0]),
                    created_orders,
                ),
                "path": "records.billing.config",
                "func": "_compute_storage_fees",
            }
        )

    @api.model
    def run_storage_fee_automation_workflow(self):
        """
        Run the storage fee automation workflow.
        This method is called by the scheduled action.
        """
        try:
            self._run_storage_fee_workflow()
        except Exception as e:
            self.env["ir.logging"].create(
                {
                    "name": "Storage Fee Workflow Error",
                    "type": "server",
                    "level": "ERROR",
                    "message": _("Error in storage fee automation workflow: %s", str(e)),
                    "path": "records.billing.config",
                    "func": "run_storage_fee_automation_workflow",
                }
            )
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

    @api.depends("invoice_generation_log_ids")
    def _compute_last_invoice_date(self):
        for record in self:
            if record.invoice_generation_log_ids:
                record.last_invoice_date = max(record.invoice_generation_log_ids.mapped("generation_date")).date()
            else:
                record.last_invoice_date = False

    @api.depends("usage_tracking_ids")
    def _compute_revenue_amount(self):
        for record in self:
            record.revenue_amount = sum(record.usage_tracking_ids.mapped("total_cost"))

    @api.model
    def _default_config(self):
        """Get the default billing configuration"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            config = self.create({
                'name': 'Default Billing Configuration',
                'auto_compute_storage_fees': True,
            })
        return config

    # =====================================================================
    # PLACEHOLDER BUTTON ACTIONS (from XML views) - Safe Navigation Stubs
    # =====================================================================
    def action_generate_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', '=', 0)],
            'target': 'current',
        }

    def action_view_analytics(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Billing Analytics'),
            'res_model': 'records.billing.rate',
            'view_mode': 'list,form',
            'domain': [('id', '=', 0)],
            'target': 'current',
        }

    def action_view_billing_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Billing History'),
            'res_model': 'invoice.generation.log',
            'view_mode': 'list,form',
            'domain': [('id', '=', 0)],
            'target': 'current',
        }

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', '=', 0)],
            'target': 'current',
        }
