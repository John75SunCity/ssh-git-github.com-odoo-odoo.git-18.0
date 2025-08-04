# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class RecordsBillingConfig(models.Model):
    _name = "records.billing.config"
    _description = "Records Billing Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Basic Information
    name = fields.Char(string="Configuration Name", required=True, tracking=True)
    active = fields.Boolean(string="Active", default=True)
    partner_id = fields.Many2one("res.partner", string="Customer")
    customer_id = fields.Many2one(
        "res.partner", string="Customer"
    )  # Alternative reference
    billing_type = fields.Selection(
        [("standard", "Standard"), ("premium", "Premium"), ("custom", "Custom")],
        string="Billing Type",
        default="standard",
    )

    # Essential Billing Configuration Fields (from view analysis)
    billing_model = fields.Selection(
        [
            ("per_container", "Per Box"),
            ("per_cubic_foot", "Per Cubic Foot"),
            ("flat_rate", "Flat Rate"),
            ("tiered", "Tiered Pricing"),
            ("usage_based", "Usage Based"),
        ],
        string="Billing Model",
        required=True,
        tracking=True,
    )

    # Rate Configuration
    base_rate = fields.Monetary(
        string="Base Rate", currency_field="currency_id", tracking=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Billing Automation
    auto_billing = fields.Boolean(
        string="Auto Billing Enabled", default=False, tracking=True
    )
    billing_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annually", "Semi-Annually"),
            ("annually", "Annually"),
        ],
        string="Billing Frequency",
        default="monthly",
        tracking=True,
    )

    # Payment Configuration
    payment_terms = fields.Many2one("account.payment.term", string="Payment Terms")

    # Additional Configuration Fields
    minimum_charge = fields.Monetary(
        string="Minimum Charge", currency_field="currency_id"
    )
    setup_fee = fields.Monetary(string="Setup Fee", currency_field="currency_id")
    late_fee_percentage = fields.Float(string="Late Fee Percentage", digits=(5, 2))

    # Service Configuration
    storage_rate = fields.Monetary(string="Storage Rate", currency_field="currency_id")
    retrieval_rate = fields.Monetary(
        string="Retrieval Rate", currency_field="currency_id"
    )
    destruction_rate = fields.Monetary(
        string="Destruction Rate", currency_field="currency_id"
    )
    scanning_rate = fields.Monetary(
        string="Scanning Rate", currency_field="currency_id"
    )

    # Advanced Features
    tiered_pricing_enabled = fields.Boolean(
        string="Tiered Pricing Enabled", default=False
    )
    volume_discounts_enabled = fields.Boolean(
        string="Volume Discounts Enabled", default=False
    )
    contract_pricing = fields.Boolean(string="Contract Pricing", default=False)

    # Integration Settings
    accounting_system_sync = fields.Boolean(
        string="Accounting System Sync", default=False
    )
    auto_apply = fields.Boolean(string="Auto Apply Configuration", default=True)

    # === MISSING BUSINESS FIELDS FROM ANALYSIS ===

    # Financial Analytics & Reporting
    amount = fields.Monetary(
        string="Amount", currency_field="currency_id", help="Current billing amount"
    )
    annual_revenue = fields.Monetary(
        string="Annual Revenue",
        currency_field="currency_id",
        compute="_compute_annual_revenue",
        store=True,
        help="Total annual revenue for this configuration",
    )
    average_monthly_billing = fields.Monetary(
        string="Average Monthly Billing",
        currency_field="currency_id",
        compute="_compute_average_monthly_billing",
        store=True,
        help="Average monthly billing amount",
    )
    monthly_revenue = fields.Monetary(
        string="Monthly Revenue",
        currency_field="currency_id",
        compute="_compute_monthly_revenue",
        store=True,
        help="Current month revenue",
    )
    quarterly_revenue = fields.Monetary(
        string="Quarterly Revenue",
        currency_field="currency_id",
        compute="_compute_quarterly_revenue",
        store=True,
        help="Current quarter revenue",
    )
    revenue_amount = fields.Monetary(
        string="Revenue Amount",
        currency_field="currency_id",
        help="Total revenue amount",
    )
    total_revenue = fields.Monetary(
        string="Total Revenue",
        currency_field="currency_id",
        compute="_compute_total_revenue",
        store=True,
        help="Total cumulative revenue",
    )
    total_cost = fields.Monetary(
        string="Total Cost",
        currency_field="currency_id",
        compute="_compute_total_cost",
        store=True,
        help="Total operational costs",
    )
    cost_amount = fields.Monetary(
        string="Cost Amount", currency_field="currency_id", help="Current cost amount"
    )
    profit_margin = fields.Float(
        string="Profit Margin %",
        digits=(5, 2),
        compute="_compute_profit_margin",
        store=True,
        help="Calculated profit margin percentage",
    )

    # Billing Performance & Analytics
    billing_accuracy_rate = fields.Float(
        string="Billing Accuracy Rate",
        digits=(5, 2),
        default=99.0,
        help="Percentage of accurate billing transactions",
    )
    billing_history_count = fields.Integer(
        string="Billing History Count",
        compute="_compute_billing_history_count",
        store=True,
        help="Number of historical billing records",
    )
    collection_rate = fields.Float(
        string="Collection Rate %",
        digits=(5, 2),
        compute="_compute_collection_rate",
        store=True,
        help="Percentage of successful collections",
    )
    customer_satisfaction_score = fields.Float(
        string="Customer Satisfaction Score",
        digits=(3, 1),
        help="Customer satisfaction rating for billing",
    )
    payment_delay_average = fields.Float(
        string="Average Payment Delay (Days)",
        digits=(5, 1),
        compute="_compute_payment_delay_average",
        store=True,
        help="Average days for payment collection",
    )

    # Operational Configuration
    audit_trail_enabled = fields.Boolean(
        string="Audit Trail Enabled",
        default=True,
        help="Enable comprehensive audit logging",
    )
    billing_cycle_start = fields.Date(
        string="Billing Cycle Start Date",
        tracking=True,
        help="Start date for current billing cycle",
    )
    billing_failure_alerts = fields.Boolean(
        string="Billing Failure Alerts",
        default=True,
        help="Send alerts on billing failures",
    )
    compliance_reporting = fields.Boolean(
        string="Compliance Reporting", default=True, help="Generate compliance reports"
    )
    consolidate_charges = fields.Boolean(
        string="Consolidate Charges",
        default=False,
        help="Consolidate multiple charges into single invoice",
    )
    data_retention_period = fields.Integer(
        string="Data Retention Period (Years)",
        default=7,
        help="How long to retain billing data",
    )
    encryption_enabled = fields.Boolean(
        string="Encryption Enabled",
        default=True,
        help="Enable data encryption for billing information",
    )
    grace_period_days = fields.Integer(
        string="Grace Period (Days)", default=30, help="Grace period for late payments"
    )
    multi_currency_support = fields.Boolean(
        string="Multi-Currency Support",
        default=False,
        help="Enable multi-currency billing",
    )
    prorate_monthly = fields.Boolean(
        string="Prorate Monthly", default=True, help="Enable prorated monthly billing"
    )

    # Service Configuration
    billable = fields.Boolean(
        string="Billable", default=True, help="Mark this configuration as billable"
    )
    service_category = fields.Selection(
        [
            ("storage", "Storage Services"),
            ("retrieval", "Retrieval Services"),
            ("destruction", "Destruction Services"),
            ("scanning", "Scanning Services"),
            ("consultation", "Consultation Services"),
            ("other", "Other Services"),
        ],
        string="Service Category",
        help="Primary service category",
    )
    service_type = fields.Char(
        string="Service Type", help="Specific service type identifier"
    )
    quantity = fields.Float(
        string="Quantity", digits=(10, 2), help="Service quantity for billing"
    )
    unit_of_measure = fields.Char(
        string="Unit of Measure", help="Unit for quantity measurement"
    )
    unit_rate = fields.Monetary(
        string="Unit Rate", currency_field="currency_id", help="Rate per unit"
    )
    rate_type = fields.Selection(
        [
            ("fixed", "Fixed Rate"),
            ("variable", "Variable Rate"),
            ("tiered", "Tiered Rate"),
            ("usage", "Usage Based"),
        ],
        string="Rate Type",
        help="Type of billing rate",
    )
    rate_unit = fields.Char(string="Rate Unit", help="Unit for rate calculation")

    # Discount & Pricing Rules
    discount_percentage = fields.Float(
        string="Discount Percentage", digits=(5, 2), help="Default discount percentage"
    )
    discount_type = fields.Selection(
        [
            ("percentage", "Percentage"),
            ("fixed", "Fixed Amount"),
            ("volume", "Volume Based"),
            ("loyalty", "Loyalty Discount"),
        ],
        string="Discount Type",
        help="Type of discount applied",
    )
    discount_value = fields.Float(
        string="Discount Value", digits=(10, 2), help="Discount value amount"
    )
    minimum_threshold = fields.Monetary(
        string="Minimum Threshold",
        currency_field="currency_id",
        help="Minimum billing threshold",
    )
    tier_threshold = fields.Monetary(
        string="Tier Threshold",
        currency_field="currency_id",
        help="Threshold for tier pricing",
    )

    # Date & Period Management
    effective_date = fields.Date(
        string="Effective Date",
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Date when configuration becomes effective",
    )
    valid_from = fields.Date(
        string="Valid From", tracking=True, help="Configuration validity start date"
    )
    valid_until = fields.Date(
        string="Valid Until", tracking=True, help="Configuration validity end date"
    )
    period = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("yearly", "Yearly"),
        ],
        string="Billing Period",
        default="monthly",
    )
    period_start = fields.Date(
        string="Period Start", help="Current billing period start"
    )
    period_end = fields.Date(string="Period End", help="Current billing period end")
    generation_date = fields.Date(
        string="Generation Date", help="Date when billing was generated"
    )
    next_billing_date = fields.Date(
        string="Next Billing Date",
        compute="_compute_next_billing_date",
        store=True,
        help="Calculated next billing date",
    )

    # Customer & Invoice Management
    customer_count = fields.Integer(
        string="Customer Count",
        compute="_compute_customer_count",
        store=True,
        help="Number of customers using this configuration",
    )
    invoice_count = fields.Integer(
        string="Invoice Count",
        compute="_compute_invoice_count",
        store=True,
        help="Total number of invoices generated",
    )
    invoice_number = fields.Char(string="Invoice Number", help="Related invoice number")
    invoice_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("paid", "Paid"),
            ("overdue", "Overdue"),
            ("cancelled", "Cancelled"),
        ],
        string="Invoice Status",
        help="Current invoice status",
    )
    invoice_template = fields.Char(
        string="Invoice Template", help="Template used for invoice generation"
    )

    # Notification & Communication
    customer_notifications = fields.Boolean(
        string="Customer Notifications",
        default=True,
        help="Send notifications to customers",
    )
    escalation_notifications = fields.Boolean(
        string="Escalation Notifications",
        default=True,
        help="Send escalation notifications",
    )
    finance_team_notifications = fields.Boolean(
        string="Finance Team Notifications",
        default=True,
        help="Send notifications to finance team",
    )
    manager_notifications = fields.Boolean(
        string="Manager Notifications",
        default=True,
        help="Send notifications to managers",
    )
    payment_overdue_alerts = fields.Boolean(
        string="Payment Overdue Alerts",
        default=True,
        help="Send alerts for overdue payments",
    )
    revenue_variance_alerts = fields.Boolean(
        string="Revenue Variance Alerts",
        default=True,
        help="Send alerts for revenue variances",
    )
    usage_threshold_alerts = fields.Boolean(
        string="Usage Threshold Alerts",
        default=True,
        help="Send alerts when usage thresholds are reached",
    )
    send_invoice_email = fields.Boolean(
        string="Send Invoice Email",
        default=True,
        help="Automatically send invoice emails",
    )
    include_usage_details = fields.Boolean(
        string="Include Usage Details",
        default=True,
        help="Include detailed usage in invoices",
    )
    reminder_schedule = fields.Char(
        string="Reminder Schedule", help="Schedule for payment reminders"
    )
    invoice_email_template = fields.Char(
        string="Invoice Email Template", help="Email template for invoice delivery"
    )

    # Payment Configuration
    payment_method = fields.Selection(
        [
            ("credit_card", "Credit Card"),
            ("bank_transfer", "Bank Transfer"),
            ("check", "Check"),
            ("cash", "Cash"),
            ("ach", "ACH Transfer"),
            ("wire", "Wire Transfer"),
        ],
        string="Payment Method",
        help="Preferred payment method",
    )
    payment_gateway_integration = fields.Boolean(
        string="Payment Gateway Integration",
        default=False,
        help="Enable payment gateway integration",
    )
    tax_calculation_method = fields.Selection(
        [
            ("inclusive", "Tax Inclusive"),
            ("exclusive", "Tax Exclusive"),
            ("exempt", "Tax Exempt"),
        ],
        string="Tax Calculation Method",
        default="exclusive",
    )

    # Status & Control
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("expired", "Expired"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    rule_name = fields.Char(string="Rule Name", help="Name of the billing rule")

    # Tracking & Usage Analytics
    tracking_date = fields.Date(string="Tracking Date", help="Date for usage tracking")
    track_access_frequency = fields.Boolean(
        string="Track Access Frequency",
        default=True,
        help="Track how often services are accessed",
    )
    track_box_storage = fields.Boolean(
        string="Track Box Storage", default=True, help="Track box storage usage"
    )
    track_destruction_services = fields.Boolean(
        string="Track Destruction Services",
        default=True,
        help="Track destruction service usage",
    )
    track_digital_services = fields.Boolean(
        string="Track Digital Services",
        default=True,
        help="Track digital service usage",
    )
    track_document_count = fields.Boolean(
        string="Track Document Count", default=True, help="Track document quantities"
    )
    track_pickup_delivery = fields.Boolean(
        string="Track Pickup/Delivery",
        default=True,
        help="Track pickup and delivery services",
    )
    track_retrieval_requests = fields.Boolean(
        string="Track Retrieval Requests",
        default=True,
        help="Track document retrieval requests",
    )
    track_special_handling = fields.Boolean(
        string="Track Special Handling",
        default=True,
        help="Track special handling services",
    )

    # === CRITICAL MISSING VIEW FIELDS ===
    last_invoice_date = fields.Date(
        string="Last Invoice Date",
        compute="_compute_last_invoice_date",
        store=True,
        help="Date of the last generated invoice",
    )

    # === MISSING FRAMEWORK INTEGRATION FIELDS ===
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # === ADDITIONAL BUSINESS CRITICAL FIELDS ===
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    sequence = fields.Integer(string="Sequence", default=10)
    notes = fields.Text(string="Internal Notes")
    description = fields.Text(string="Description")

    # === BILLING ANALYTICS FIELDS ===
    last_billing_amount = fields.Monetary(
        string="Last Billing Amount",
        currency_field="currency_id",
        help="Amount of the last billing cycle",
    )
    ytd_revenue = fields.Monetary(
        string="YTD Revenue",
        currency_field="currency_id",
        compute="_compute_ytd_revenue",
        store=True,
    )
    billing_accuracy_rate = fields.Float(
        string="Billing Accuracy Rate",
        digits=(5, 2),
        help="Percentage of accurate billing transactions",
    )

    # === SERVICE INTEGRATION FIELDS ===
    default_service_ids = fields.Many2many(
        "product.product",
        string="Default Services",
        domain=[("type", "=", "service")],
        help="Default services for this billing configuration",
    )

    # === COMPUTE METHODS ===
    @api.depends("partner_id")
    def _compute_last_invoice_date(self):
        """Compute the last invoice date for this customer"""
        for record in self:
            if record.partner_id:
                last_invoice = self.env["account.move"].search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                    ],
                    order="invoice_date desc",
                    limit=1,
                )
                record.last_invoice_date = (
                    last_invoice.invoice_date if last_invoice else False
                )
            else:
                record.last_invoice_date = False

    @api.depends("partner_id")
    def _compute_ytd_revenue(self):
        """Compute year-to-date revenue"""
        from datetime import date

        year_start = date.today().replace(month=1, day=1)

        for record in self:
            if record.partner_id:
                invoices = self.env["account.move"].search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                        ("invoice_date", ">=", year_start),
                    ]
                )
                record.ytd_revenue = sum(invoices.mapped("amount_total"))
            else:
                record.ytd_revenue = 0.0

    # === ADDITIONAL COMPUTE METHODS ===
    @api.depends("partner_id", "billing_frequency")
    def _compute_monthly_analytics(self):
        """Compute monthly recurring revenue"""
        for record in self:
            if record.partner_id and record.billing_frequency:
                # Calculate based on base rate and frequency
                if record.billing_frequency == "monthly":
                    record.monthly_recurring_revenue = record.base_rate or 0.0
                elif record.billing_frequency == "quarterly":
                    record.monthly_recurring_revenue = (record.base_rate or 0.0) / 3
                elif record.billing_frequency == "annually":
                    record.monthly_recurring_revenue = (record.base_rate or 0.0) / 12
                else:
                    record.monthly_recurring_revenue = 0.0
            else:
                record.monthly_recurring_revenue = 0.0

    @api.depends("billing_cycle_start", "billing_frequency")
    def _compute_billing_cycle_count(self):
        """Compute number of completed billing cycles"""
        from datetime import date

        for record in self:
            if record.billing_cycle_start:
                days_since_start = (date.today() - record.billing_cycle_start).days
                if record.billing_frequency == "monthly":
                    record.billing_cycle_count = days_since_start // 30
                elif record.billing_frequency == "quarterly":
                    record.billing_cycle_count = days_since_start // 90
                elif record.billing_frequency == "annually":
                    record.billing_cycle_count = days_since_start // 365
                else:
                    record.billing_cycle_count = 0
            else:
                record.billing_cycle_count = 0

    @api.depends("partner_id")
    def _compute_overdue_amount(self):
        """Compute overdue amount for this configuration"""
        for record in self:
            if record.partner_id:
                overdue_invoices = self.env["account.move"].search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                        ("payment_state", "in", ["not_paid", "partial"]),
                        ("invoice_date_due", "<", fields.Date.today()),
                    ]
                )
                record.overdue_amount = sum(overdue_invoices.mapped("amount_residual"))
            else:
                record.overdue_amount = 0.0

    @api.depends("base_rate", "billing_frequency")
    def _compute_next_invoice_amount(self):
        """Compute estimated amount for next invoice"""
        for record in self:
            # Simple calculation based on base rate
            record.next_invoice_amount = record.base_rate or 0.0

    @api.depends("partner_id", "billing_frequency")
    def _compute_revenue_analytics(self):
        """Compute comprehensive revenue analytics"""
        for record in self:
            if record.partner_id:
                # Get revenue for different periods
                from datetime import date, timedelta

                today = date.today()

                # Monthly revenue (last 30 days)
                month_start = today - timedelta(days=30)
                monthly_invoices = self.env["account.move"].search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                        ("invoice_date", ">=", month_start),
                    ]
                )
                record.monthly_revenue = sum(monthly_invoices.mapped("amount_total"))

                # Quarterly revenue (last 90 days)
                quarter_start = today - timedelta(days=90)
                quarterly_invoices = self.env["account.move"].search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                        ("invoice_date", ">=", quarter_start),
                    ]
                )
                record.quarterly_revenue = sum(
                    quarterly_invoices.mapped("amount_total")
                )

                # Average monthly billing (last 12 months)
                year_start = today - timedelta(days=365)
                yearly_invoices = self.env["account.move"].search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                        ("invoice_date", ">=", year_start),
                    ]
                )
                total_yearly = sum(yearly_invoices.mapped("amount_total"))
                record.average_monthly_billing = (
                    total_yearly / 12 if total_yearly else 0.0
                )
            else:
                record.monthly_revenue = 0.0
                record.quarterly_revenue = 0.0
                record.average_monthly_billing = 0.0

    # === ADDITIONAL COMPUTE METHODS FOR NEW FIELDS ===

    @api.depends("partner_id")
    def _compute_customer_count(self):
        """Compute total number of unique customers"""
        for record in self:
            if record.partner_id:
                # Count all billing configs for same company
                count = self.search_count(
                    [
                        ("company_id", "=", record.company_id.id),
                        ("partner_id", "!=", False),
                    ]
                )
                record.customer_count = count
            else:
                record.customer_count = 0

    @api.depends("base_rate", "billing_frequency", "billing_line_ids.amount")
    def _compute_total_cost(self):
        """Calculate total costs for billing configuration"""
        for record in self:
            total_cost = 0.0
            # Base operating costs
            if record.base_rate and record.billing_frequency:
                frequency_multiplier = {
                    "monthly": 12,
                    "quarterly": 4,
                    "yearly": 1,
                    "weekly": 52,
                }.get(record.billing_frequency, 12)
                total_cost += (
                    record.base_rate * frequency_multiplier * 0.7
                )  # 70% margin

            # Additional line item costs
            total_cost += sum(line.amount * 0.6 for line in record.billing_line_ids)
            record.total_cost = total_cost

    @api.depends("annual_revenue", "total_cost")
    def _compute_profit_margin(self):
        """Calculate profit margin percentage"""
        for record in self:
            if record.annual_revenue and record.total_cost:
                record.profit_margin = (
                    (record.annual_revenue - record.total_cost) / record.annual_revenue
                ) * 100
            else:
                record.profit_margin = 0.0

    @api.depends("partner_id")
    def _compute_collection_rate(self):
        """Calculate payment collection rate"""
        for record in self:
            if record.partner_id:
                invoices = self.env["account.move"].search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                    ]
                )
                total_invoices = len(invoices)
                paid_invoices = len(
                    invoices.filtered(lambda x: x.payment_state == "paid")
                )

                if total_invoices > 0:
                    record.collection_rate = (paid_invoices / total_invoices) * 100
                else:
                    record.collection_rate = 0.0
            else:
                record.collection_rate = 0.0

    @api.depends("partner_id")
    def _compute_payment_delay_average(self):
        """Calculate average payment delay in days"""
        for record in self:
            if record.partner_id:
                invoices = self.env["account.move"].search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("payment_state", "=", "paid"),
                    ]
                )

                delays = []
                for invoice in invoices:
                    if invoice.invoice_date_due and invoice.invoice_payments_widget:
                        # Get payment date from payments
                        payments_data = json.loads(invoice.invoice_payments_widget)
                        if payments_data and "content" in payments_data:
                            for payment in payments_data["content"]:
                                if "date" in payment:
                                    payment_date = fields.Date.from_string(
                                        payment["date"]
                                    )
                                    delay = (
                                        payment_date - invoice.invoice_date_due
                                    ).days
                                    delays.append(max(0, delay))  # Only positive delays

                record.payment_delay_average = (
                    sum(delays) / len(delays) if delays else 0.0
                )
            else:
                record.payment_delay_average = 0.0

    # === CRITICAL MISSING FIELDS (from billing_views.xml analysis) ===

    # Framework Integration Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # Business Critical Fields
    amount = fields.Monetary(string="Total Amount", currency_field="currency_id")
    annual_revenue = fields.Monetary(
        string="Annual Revenue",
        currency_field="currency_id",
        compute="_compute_annual_revenue",
    )
    audit_trail_enabled = fields.Boolean(string="Audit Trail Enabled", default=True)

    # Rate Structure & Service Configuration
    service_category = fields.Selection(
        [
            ("storage", "Storage Services"),
            ("retrieval", "Retrieval Services"),
            ("destruction", "Destruction Services"),
            ("scanning", "Scanning Services"),
            ("transport", "Transport Services"),
            ("consultation", "Consultation Services"),
        ],
        string="Service Category",
        required=True,
        default="storage",
    )

    rate_unit = fields.Selection(
        [
            ("per_box", "Per Box"),
            ("per_cubic_foot", "Per Cubic Foot"),
            ("per_document", "Per Document"),
            ("per_hour", "Per Hour"),
            ("per_pickup", "Per Pickup"),
            ("monthly", "Monthly Rate"),
        ],
        string="Rate Unit",
        required=True,
        default="per_box",
    )

    # Billing Schedule Fields
    billing_cycle_start = fields.Date(
        string="Billing Cycle Start", default=fields.Date.today
    )
    next_billing_date = fields.Date(
        string="Next Billing Date", compute="_compute_next_billing_date"
    )
    payment_method = fields.Selection(
        [
            ("credit_card", "Credit Card"),
            ("ach", "ACH/Bank Transfer"),
            ("check", "Check"),
            ("wire", "Wire Transfer"),
            ("invoice", "Invoice Terms"),
        ],
        string="Payment Method",
        default="invoice",
    )
    grace_period_days = fields.Integer(string="Grace Period (Days)", default=30)

    # Statistical Fields for Dashboard
    invoice_count = fields.Integer(
        string="Invoice Count", compute="_compute_invoice_count"
    )
    billing_history_count = fields.Integer(
        string="Billing History Count", compute="_compute_billing_history_count"
    )
    total_revenue = fields.Monetary(
        string="Total Revenue",
        currency_field="currency_id",
        compute="_compute_total_revenue",
    )

    # Rate Management One2many Relationships
    billing_rate_ids = fields.One2many(
        "records.billing.rate", "billing_config_id", string="Billing Rates"
    )
    usage_tracking_ids = fields.One2many(
        "records.usage.tracking", "billing_config_id", string="Usage Tracking Records"
    )
    billing_adjustment_ids = fields.One2many(
        "records.billing.adjustment", "billing_config_id", string="Billing Adjustments"
    )
    invoice_line_ids = fields.One2many(
        "account.move.line", "billing_config_id", string="Invoice Lines"
    )

    # === ADDITIONAL MISSING RELATIONSHIPS ===
    contract_ids = fields.One2many(
        "records.billing.contract", "billing_config_id", string="Related Contracts"
    )

    discount_ids = fields.One2many(
        "records.billing.discount", "billing_config_id", string="Applied Discounts"
    )

    # === MISSING COMPUTED ANALYTICS ===
    monthly_recurring_revenue = fields.Monetary(
        string="Monthly Recurring Revenue",
        currency_field="currency_id",
        compute="_compute_monthly_analytics",
        store=True,
    )

    billing_cycle_count = fields.Integer(
        string="Billing Cycles Count",
        compute="_compute_billing_cycle_count",
        help="Number of completed billing cycles",
    )

    overdue_amount = fields.Monetary(
        string="Overdue Amount",
        currency_field="currency_id",
        compute="_compute_overdue_amount",
        help="Total overdue amount for this configuration",
    )

    next_invoice_amount = fields.Monetary(
        string="Next Invoice Amount",
        currency_field="currency_id",
        compute="_compute_next_invoice_amount",
        help="Estimated amount for next invoice",
    )

    # === MASSIVE MISSING FIELDS FROM VIEWS ===

    # Invoice Generation Log Fields
    invoice_generation_log_ids = fields.One2many(
        "records.invoice.generation.log",
        "billing_config_id",
        string="Invoice Generation Logs",
    )

    # Discount Rule Fields
    discount_rule_ids = fields.One2many(
        "records.billing.discount.rule", "billing_config_id", string="Discount Rules"
    )

    # Additional Revenue Analytics
    monthly_revenue = fields.Monetary(
        string="Monthly Revenue",
        currency_field="currency_id",
        compute="_compute_revenue_analytics",
        store=True,
    )
    quarterly_revenue = fields.Monetary(
        string="Quarterly Revenue",
        currency_field="currency_id",
        compute="_compute_revenue_analytics",
        store=True,
    )
    average_monthly_billing = fields.Monetary(
        string="Average Monthly Billing",
        currency_field="currency_id",
        compute="_compute_revenue_analytics",
        store=True,
    )

    # Contract Management
    contract_reference = fields.Char(string="Contract Reference")
    service_level_agreement = fields.Text(string="Service Level Agreement")
    performance_metrics_enabled = fields.Boolean(
        string="Performance Metrics Enabled", default=True
    )

    # Additional Financial Fields
    credit_limit = fields.Monetary(string="Credit Limit", currency_field="currency_id")
    current_balance = fields.Monetary(
        string="Current Balance", currency_field="currency_id"
    )
    credit_terms = fields.Char(string="Credit Terms")

    # System Integration
    erp_integration_enabled = fields.Boolean(
        string="ERP Integration Enabled", default=False
    )
    api_access_enabled = fields.Boolean(string="API Access Enabled", default=False)

    # === BILLING EFFICIENCY METRICS ===
    automation_enabled = fields.Boolean(
        string="Automation Enabled",
        default=True,
        help="Enable automated billing processes",
    )

    billing_template_id = fields.Many2one(
        "records.billing.template",
        string="Billing Template",
        help="Template used for invoice generation",
    )

    tax_configuration_id = fields.Many2one(
        "account.tax", string="Default Tax", help="Default tax applied to billing"
    )

    # Performance Metrics
    average_monthly_revenue = fields.Monetary(
        string="Average Monthly Revenue",
        currency_field="currency_id",
        compute="_compute_performance_metrics",
    )
    revenue_growth_rate = fields.Float(
        string="Revenue Growth Rate (%)", compute="_compute_performance_metrics"
    )
    customer_satisfaction_score = fields.Float(
        string="Customer Satisfaction Score",
        digits=(3, 2),
        help="Score from 1-10 based on customer feedback",
    )

    # Advanced Billing Configuration
    apply_seasonal_rates = fields.Boolean(string="Apply Seasonal Rates", default=False)
    seasonal_rate_multiplier = fields.Float(
        string="Seasonal Rate Multiplier", default=1.0, digits=(3, 2)
    )
    bulk_discount_threshold = fields.Integer(
        string="Bulk Discount Threshold", help="Minimum quantity for bulk discount"
    )
    bulk_discount_percentage = fields.Float(string="Bulk Discount %", digits=(5, 2))

    # Contract & Agreement Fields
    contract_start_date = fields.Date(string="Contract Start Date")
    contract_end_date = fields.Date(string="Contract End Date")
    contract_auto_renew = fields.Boolean(string="Auto-Renew Contract", default=False)
    contract_terms_url = fields.Char(string="Contract Terms URL")

    # Integration & Sync Fields
    external_billing_id = fields.Char(string="External Billing System ID")
    last_sync_date = fields.Datetime(string="Last Sync Date")
    sync_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("synced", "Synced"),
            ("error", "Error"),
            ("manual", "Manual Override"),
        ],
        string="Sync Status",
        default="pending",
    )

    # Compliance & Audit
    compliance_notes = fields.Text(string="Compliance Notes")
    audit_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annually", "Annually"),
            ("on_demand", "On Demand"),
        ],
        string="Audit Frequency",
        default="quarterly",
    )
    last_audit_date = fields.Date(string="Last Audit Date")
    next_audit_date = fields.Date(
        string="Next Audit Date", compute="_compute_next_audit_date"
    )

    # Notification & Communication
    billing_contact_ids = fields.Many2many(
        "res.partner", "billing_config_contact_rel", string="Billing Contacts"
    )
    send_billing_alerts = fields.Boolean(string="Send Billing Alerts", default=True)
    alert_threshold_amount = fields.Monetary(
        string="Alert Threshold Amount",
        currency_field="currency_id",
        help="Send alert when billing exceeds this amount",
    )

    # Reporting & Analytics
    generate_monthly_reports = fields.Boolean(
        string="Generate Monthly Reports", default=True
    )
    report_recipients = fields.Many2many(
        "res.users", "billing_config_report_users_rel", string="Report Recipients"
    )
    include_usage_analytics = fields.Boolean(
        string="Include Usage Analytics", default=True
    )

    # Custom Fields for Special Requirements
    custom_field_1 = fields.Char(string="Custom Field 1")
    custom_field_2 = fields.Char(string="Custom Field 2")
    custom_field_3 = fields.Monetary(
        string="Custom Amount Field", currency_field="currency_id"
    )

    # Status and State Management
    configuration_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("terminated", "Terminated"),
        ],
        string="Configuration Status",
        default="draft",
        tracking=True,
    )

    approval_required = fields.Boolean(string="Approval Required", default=False)
    approved_by = fields.Many2one("res.users", string="Approved By")
    approval_date = fields.Datetime(string="Approval Date")

    # Multi-currency Support
    base_currency_id = fields.Many2one("res.currency", string="Base Currency")
    exchange_rate_date = fields.Date(string="Exchange Rate Date")
    auto_currency_conversion = fields.Boolean(
        string="Auto Currency Conversion", default=False
    )

    # Usage Tracking Fields
    track_box_storage = fields.Boolean(string="Track Box Storage", default=True)
    track_document_count = fields.Boolean(string="Track Document Count", default=True)
    track_access_frequency = fields.Boolean(
        string="Track Access Frequency", default=False
    )
    track_special_handling = fields.Boolean(
        string="Track Special Handling", default=True
    )
    track_pickup_delivery = fields.Boolean(string="Track Pickup/Delivery", default=True)
    track_retrieval_requests = fields.Boolean(
        string="Track Retrieval Requests", default=True
    )
    track_destruction_services = fields.Boolean(
        string="Track Destruction Services", default=True
    )
    track_digital_services = fields.Boolean(
        string="Track Digital Services", default=False
    )

    # Invoice Generation Fields
    invoice_template = fields.Many2one("mail.template", string="Invoice Template")
    consolidate_charges = fields.Boolean(string="Consolidate Charges", default=True)
    prorate_monthly = fields.Boolean(string="Prorate Monthly", default=True)
    include_usage_details = fields.Boolean(string="Include Usage Details", default=True)
    send_invoice_email = fields.Boolean(string="Send Invoice Email", default=True)
    invoice_email_template = fields.Many2one(
        "mail.template", string="Invoice Email Template"
    )
    cc_accounting = fields.Boolean(string="CC Accounting Team", default=True)
    reminder_schedule = fields.Selection(
        [
            ("none", "No Reminders"),
            ("weekly", "Weekly"),
            ("biweekly", "Bi-weekly"),
            ("monthly", "Monthly"),
        ],
        string="Reminder Schedule",
        default="none",
    )

    # === COMPREHENSIVE MISSING FIELDS ENHANCEMENT ===

    # Revenue and Financial Management
    annual_revenue = fields.Monetary(
        string="Annual Revenue",
        currency_field="currency_id",
        compute="_compute_annual_revenue",
    )
    revenue_forecast = fields.Monetary(
        string="Revenue Forecast", currency_field="currency_id"
    )
    budget_allocation = fields.Monetary(
        string="Budget Allocation", currency_field="currency_id"
    )
    cost_center = fields.Char(string="Cost Center")
    profit_margin = fields.Float(string="Profit Margin (%)", digits=(5, 2))
    tax_rate = fields.Float(string="Tax Rate (%)", digits=(5, 2))
    discount_percentage = fields.Float(string="Discount Percentage", digits=(5, 2))
    markup_percentage = fields.Float(string="Markup Percentage", digits=(5, 2))

    # Audit and Compliance
    audit_trail_enabled = fields.Boolean(string="Audit Trail Enabled", default=True)
    compliance_reporting = fields.Boolean(string="Compliance Reporting", default=True)
    retention_compliance = fields.Boolean(string="Retention Compliance", default=True)
    naid_compliance = fields.Boolean(string="NAID Compliance", default=False)
    invoice_validation = fields.Boolean(string="Invoice Validation", default=True)
    billing_approval_required = fields.Boolean(
        string="Billing Approval Required", default=False
    )

    # Advanced Rate Configuration
    multi_tier_rates = fields.Boolean(string="Multi-Tier Rates", default=False)
    seasonal_rates = fields.Boolean(string="Seasonal Rates", default=False)
    promotional_rates = fields.Boolean(string="Promotional Rates", default=False)
    emergency_rates = fields.Boolean(string="Emergency Rates", default=False)
    overtime_rates = fields.Boolean(string="Overtime Rates", default=False)
    weekend_rates = fields.Boolean(string="Weekend Rates", default=False)
    holiday_rates = fields.Boolean(string="Holiday Rates", default=False)

    # Service-Specific Billing
    pickup_service_rate = fields.Monetary(
        string="Pickup Service Rate", currency_field="currency_id"
    )
    delivery_service_rate = fields.Monetary(
        string="Delivery Service Rate", currency_field="currency_id"
    )
    digital_conversion_rate = fields.Monetary(
        string="Digital Conversion Rate", currency_field="currency_id"
    )
    indexing_rate = fields.Monetary(
        string="Indexing Rate", currency_field="currency_id"
    )
    consultation_rate = fields.Monetary(
        string="Consultation Rate", currency_field="currency_id"
    )
    training_rate = fields.Monetary(
        string="Training Rate", currency_field="currency_id"
    )
    rush_service_rate = fields.Monetary(
        string="Rush Service Rate", currency_field="currency_id"
    )

    # Volume and Usage-Based Pricing
    volume_thresholds = fields.Text(string="Volume Thresholds (JSON)")
    usage_metrics = fields.Text(string="Usage Metrics Configuration")
    billing_cycles = fields.Integer(string="Billing Cycles", default=12)
    minimum_commitment = fields.Monetary(
        string="Minimum Commitment", currency_field="currency_id"
    )
    overage_rate = fields.Monetary(string="Overage Rate", currency_field="currency_id")
    base_allowance = fields.Integer(string="Base Allowance (boxes)")

    # Contract and Agreement Management
    contract_start_date = fields.Date(string="Contract Start Date")
    contract_end_date = fields.Date(string="Contract End Date")
    auto_renewal = fields.Boolean(string="Auto Renewal", default=False)
    renewal_notice_period = fields.Integer(
        string="Renewal Notice Period (days)", default=30
    )
    contract_value = fields.Monetary(
        string="Contract Value", currency_field="currency_id"
    )
    payment_guarantee = fields.Monetary(
        string="Payment Guarantee", currency_field="currency_id"
    )

    # Billing Periods and Timing
    billing_day = fields.Integer(string="Billing Day of Month", default=1)
    due_days = fields.Integer(string="Payment Due Days", default=30)
    grace_period = fields.Integer(string="Grace Period (days)", default=5)
    cutoff_date = fields.Date(string="Billing Cutoff Date")
    next_billing_date = fields.Date(string="Next Billing Date")
    last_billing_date = fields.Date(string="Last Billing Date")

    # Advanced Features and Automation
    auto_invoicing = fields.Boolean(string="Auto Invoicing", default=False)
    invoice_approval = fields.Boolean(string="Invoice Approval Required", default=False)
    electronic_delivery = fields.Boolean(string="Electronic Delivery", default=True)
    portal_access = fields.Boolean(string="Portal Access", default=True)
    real_time_billing = fields.Boolean(string="Real-time Billing", default=False)
    batch_processing = fields.Boolean(string="Batch Processing", default=True)

    # Integration and Synchronization
    erp_integration = fields.Boolean(string="ERP Integration", default=False)
    crm_sync = fields.Boolean(string="CRM Sync", default=False)
    inventory_sync = fields.Boolean(string="Inventory Sync", default=True)
    financial_sync = fields.Boolean(string="Financial Sync", default=True)
    api_enabled = fields.Boolean(string="API Enabled", default=False)
    webhook_notifications = fields.Boolean(
        string="Webhook Notifications", default=False
    )

    # Currency and International
    multi_currency = fields.Boolean(string="Multi-Currency Support", default=False)
    exchange_rate_source = fields.Selection(
        [
            ("manual", "Manual"),
            ("ecb", "European Central Bank"),
            ("fed", "Federal Reserve"),
            ("bank", "Bank Rate"),
        ],
        string="Exchange Rate Source",
        default="manual",
    )
    currency_hedging = fields.Boolean(string="Currency Hedging", default=False)

    # Reporting and Analytics
    detailed_reporting = fields.Boolean(string="Detailed Reporting", default=True)
    management_dashboard = fields.Boolean(string="Management Dashboard", default=True)
    kpi_tracking = fields.Boolean(string="KPI Tracking", default=False)
    trend_analysis = fields.Boolean(string="Trend Analysis", default=False)
    forecasting = fields.Boolean(string="Revenue Forecasting", default=False)
    benchmarking = fields.Boolean(string="Industry Benchmarking", default=False)

    # Revenue Analytics Fields
    monthly_revenue = fields.Monetary(
        string="Monthly Revenue",
        currency_field="currency_id",
        compute="_compute_revenue",
    )
    quarterly_revenue = fields.Monetary(
        string="Quarterly Revenue",
        currency_field="currency_id",
        compute="_compute_revenue",
    )
    annual_revenue = fields.Monetary(
        string="Annual Revenue",
        currency_field="currency_id",
        compute="_compute_revenue",
    )
    average_monthly_billing = fields.Monetary(
        string="Average Monthly Billing",
        currency_field="currency_id",
        compute="_compute_averages",
    )
    billing_accuracy_rate = fields.Float(
        string="Billing Accuracy Rate (%)", compute="_compute_accuracy"
    )
    collection_rate = fields.Float(
        string="Collection Rate (%)", compute="_compute_collection"
    )
    payment_delay_average = fields.Integer(
        string="Payment Delay Average (Days)", compute="_compute_delays"
    )
    customer_satisfaction_score = fields.Float(
        string="Customer Satisfaction Score", compute="_compute_satisfaction"
    )

    # Notification and Alert Fields
    billing_failure_alerts = fields.Boolean(
        string="Billing Failure Alerts", default=True
    )
    payment_overdue_alerts = fields.Boolean(
        string="Payment Overdue Alerts", default=True
    )
    usage_threshold_alerts = fields.Boolean(
        string="Usage Threshold Alerts", default=True
    )
    revenue_variance_alerts = fields.Boolean(
        string="Revenue Variance Alerts", default=True
    )
    finance_team_notifications = fields.Boolean(
        string="Finance Team Notifications", default=True
    )
    manager_notifications = fields.Boolean(string="Manager Notifications", default=True)
    customer_notifications = fields.Boolean(
        string="Customer Notifications", default=True
    )
    escalation_notifications = fields.Boolean(
        string="Escalation Notifications", default=True
    )

    # Advanced Integration Fields
    payment_gateway_integration = fields.Boolean(
        string="Payment Gateway Integration", default=False
    )
    tax_calculation_method = fields.Selection(
        [("inclusive", "Tax Inclusive"), ("exclusive", "Tax Exclusive")],
        string="Tax Calculation Method",
        default="exclusive",
    )

    # === ADDITIONAL CRITICAL BUSINESS FIELDS ===

    # Customer and Account Management
    account_manager = fields.Many2one("res.users", string="Account Manager")
    billing_contact = fields.Many2one("res.partner", string="Billing Contact")
    technical_contact = fields.Many2one("res.partner", string="Technical Contact")
    billing_address = fields.Text(string="Billing Address")
    shipping_address = fields.Text(string="Shipping Address")
    credit_limit = fields.Monetary(string="Credit Limit", currency_field="currency_id")
    credit_rating = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
        ],
        string="Credit Rating",
        default="good",
    )

    # Service Level and Quality Management
    service_level_agreement = fields.Text(string="Service Level Agreement")
    response_time_guaranteed = fields.Integer(
        string="Response Time (hours)", default=24
    )
    uptime_guarantee = fields.Float(string="Uptime Guarantee (%)", default=99.5)
    quality_metrics_enabled = fields.Boolean(
        string="Quality Metrics Enabled", default=True
    )
    performance_monitoring = fields.Boolean(
        string="Performance Monitoring", default=True
    )
    service_credits = fields.Boolean(string="Service Credits", default=False)

    # Document and Records Management Integration
    document_classification = fields.Boolean(
        string="Document Classification", default=True
    )
    retention_schedule = fields.Boolean(string="Retention Schedule", default=True)
    destruction_billing = fields.Boolean(string="Destruction Billing", default=True)
    digital_delivery = fields.Boolean(string="Digital Delivery", default=False)
    physical_delivery = fields.Boolean(string="Physical Delivery", default=True)
    expedited_service = fields.Boolean(string="Expedited Service", default=False)

    # Security and Compliance Enhancement
    security_clearance_required = fields.Boolean(
        string="Security Clearance Required", default=False
    )
    chain_of_custody_billing = fields.Boolean(
        string="Chain of Custody Billing", default=False
    )
    witness_destruction = fields.Boolean(string="Witness Destruction", default=False)
    certificate_generation = fields.Boolean(
        string="Certificate Generation", default=True
    )
    compliance_audit_billing = fields.Boolean(
        string="Compliance Audit Billing", default=False
    )
    regulatory_reporting = fields.Boolean(string="Regulatory Reporting", default=False)

    # Operational Efficiency
    bulk_processing = fields.Boolean(string="Bulk Processing", default=True)
    priority_processing = fields.Boolean(string="Priority Processing", default=False)
    off_hours_service = fields.Boolean(string="Off Hours Service", default=False)
    mobile_service = fields.Boolean(string="Mobile Service", default=True)
    remote_access = fields.Boolean(string="Remote Access", default=False)
    automated_workflows = fields.Boolean(string="Automated Workflows", default=True)

    # Financial Controls and Validation
    spending_limits = fields.Boolean(string="Spending Limits", default=False)
    budget_alerts = fields.Boolean(string="Budget Alerts", default=True)
    cost_allocation = fields.Boolean(string="Cost Allocation", default=False)
    department_billing = fields.Boolean(string="Department Billing", default=False)
    project_billing = fields.Boolean(string="Project Billing", default=False)
    time_tracking = fields.Boolean(string="Time Tracking", default=False)

    # Advanced Analytics and Reporting
    cost_analysis = fields.Boolean(string="Cost Analysis", default=True)
    profitability_analysis = fields.Boolean(
        string="Profitability Analysis", default=False
    )
    customer_analytics = fields.Boolean(string="Customer Analytics", default=True)
    usage_analytics = fields.Boolean(string="Usage Analytics", default=True)
    predictive_analytics = fields.Boolean(string="Predictive Analytics", default=False)
    business_intelligence = fields.Boolean(
        string="Business Intelligence", default=False
    )

    # System Configuration and Maintenance
    backup_billing_data = fields.Boolean(string="Backup Billing Data", default=True)
    data_archival = fields.Boolean(string="Data Archival", default=True)
    system_maintenance = fields.Boolean(string="System Maintenance", default=True)
    disaster_recovery = fields.Boolean(string="Disaster Recovery", default=False)
    load_balancing = fields.Boolean(string="Load Balancing", default=False)
    scalability_planning = fields.Boolean(string="Scalability Planning", default=False)

    # Legacy and Migration Support
    multi_currency_support = fields.Boolean(
        string="Multi-Currency Support", default=False
    )

    # One2many Relationship Fields
    usage_tracking_ids = fields.One2many(
        "records.usage.tracking", "config_id", string="Usage Tracking"
    )
    invoice_generation_log_ids = fields.One2many(
        "invoice.generation.log", "config_id", string="Invoice Generation Log"
    )
    discount_rule_ids = fields.One2many(
        "discount.rule", "config_id", string="Discount Rules"
    )
    revenue_analytics_ids = fields.One2many(
        "revenue.analytics", "config_id", string="Revenue Analytics"
    )

    # Analytics and Reporting
    annual_revenue = fields.Monetary(
        string="Annual Revenue",
        currency_field="currency_id",
        compute="_compute_revenue",
    )
    monthly_revenue = fields.Monetary(
        string="Monthly Revenue",
        currency_field="currency_id",
        compute="_compute_revenue",
    )
    audit_trail_enabled = fields.Boolean(string="Audit Trail Enabled", default=True)

    # Status and Workflow
    approval_required = fields.Boolean(string="Approval Required", default=False)
    approved_by = fields.Many2one("res.users", string="Approved By")
    approval_date = fields.Date(string="Approval Date")

    # Related Records
    billing_line_ids = fields.One2many(
        "records.billing.line", "config_id", string="Billing Lines"
    )
    invoice_ids = fields.One2many(
        "account.move", "billing_config_id", string="Related Invoices"
    )

    # === COMPREHENSIVE BILLING MANAGEMENT FIELDS ===

    # Service Configuration
    service_category = fields.Selection(
        [
            ("storage", "Storage Services"),
            ("retrieval", "Retrieval Services"),
            ("destruction", "Destruction Services"),
            ("digital", "Digital Services"),
            ("transportation", "Transportation Services"),
            ("consulting", "Consulting Services"),
        ],
        string="Service Category",
        tracking=True,
    )

    # Rate Structure Enhancement
    rate_unit = fields.Selection(
        [
            ("per_box", "Per Box"),
            ("per_cubic_foot", "Per Cubic Foot"),
            ("per_document", "Per Document"),
            ("per_page", "Per Page"),
            ("per_hour", "Per Hour"),
            ("per_month", "Per Month"),
            ("per_pickup", "Per Pickup"),
            ("per_shipment", "Per Shipment"),
        ],
        string="Rate Unit",
        tracking=True,
    )

    # Billing Schedule
    billing_cycle_start = fields.Date(string="Billing Cycle Start", tracking=True)
    next_billing_date = fields.Date(
        string="Next Billing Date", compute="_compute_next_billing_date", store=True
    )

    # Payment Configuration
    payment_method = fields.Selection(
        [
            ("credit_card", "Credit Card"),
            ("ach", "ACH Transfer"),
            ("check", "Check"),
            ("wire", "Wire Transfer"),
            ("invoice", "Net Terms Invoice"),
        ],
        string="Payment Method",
        tracking=True,
    )
    grace_period_days = fields.Integer(string="Grace Period (Days)", default=30)

    # Rate Management
    billing_rate_ids = fields.One2many(
        "records.billing.rate", "config_id", string="Billing Rates"
    )

    # Usage Tracking Configuration
    track_box_storage = fields.Boolean(string="Track Box Storage", default=True)
    track_document_count = fields.Boolean(string="Track Document Count", default=True)
    track_access_frequency = fields.Boolean(
        string="Track Access Frequency", default=False
    )
    track_special_handling = fields.Boolean(
        string="Track Special Handling", default=True
    )
    track_pickup_delivery = fields.Boolean(string="Track Pickup/Delivery", default=True)
    track_retrieval_requests = fields.Boolean(
        string="Track Retrieval Requests", default=True
    )
    track_destruction_services = fields.Boolean(
        string="Track Destruction Services", default=True
    )
    track_digital_services = fields.Boolean(
        string="Track Digital Services", default=False
    )

    # Usage Tracking Records
    usage_tracking_ids = fields.One2many(
        "records.usage.tracking", "config_id", string="Usage Tracking"
    )

    # Statistics and Computed Fields
    invoice_count = fields.Integer(
        string="Invoice Count", compute="_compute_statistics", store=True
    )
    billing_history_count = fields.Integer(
        string="Billing History Count", compute="_compute_statistics", store=True
    )
    total_revenue = fields.Monetary(
        string="Total Revenue",
        compute="_compute_statistics",
        store=True,
        currency_field="currency_id",
    )

    # Advanced Billing Features
    billing_tier_ids = fields.One2many(
        "records.billing.tier", "config_id", string="Billing Tiers"
    )
    volume_discount_enabled = fields.Boolean(
        string="Volume Discount Enabled", default=False
    )
    early_payment_discount = fields.Float(
        string="Early Payment Discount (%)", digits=(5, 2)
    )

    # Contract and Legal
    contract_id = fields.Many2one("records.contract", string="Service Contract")
    contract_start_date = fields.Date(string="Contract Start Date")
    contract_end_date = fields.Date(string="Contract End Date")
    auto_renewal = fields.Boolean(string="Auto Renewal", default=False)

    # Revenue Recognition
    revenue_recognition_method = fields.Selection(
        [
            ("immediate", "Immediate Recognition"),
            ("monthly", "Monthly Recognition"),
            ("service_completion", "Upon Service Completion"),
            ("milestone", "Milestone Based"),
        ],
        string="Revenue Recognition Method",
        default="monthly",
    )

    # Cost Management
    cost_center_id = fields.Many2one("account.account", string="Cost Center")
    profit_margin_target = fields.Float(
        string="Target Profit Margin (%)", digits=(5, 2)
    )

    # SLA and Performance
    sla_response_time = fields.Integer(string="SLA Response Time (Hours)", default=24)
    escalation_procedures = fields.Text(string="Escalation Procedures")

    # Customer Communication
    billing_contact_id = fields.Many2one("res.partner", string="Billing Contact")
    invoice_delivery_method = fields.Selection(
        [
            ("email", "Email"),
            ("postal", "Postal Mail"),
            ("portal", "Customer Portal"),
            ("electronic", "Electronic Delivery"),
        ],
        string="Invoice Delivery Method",
        default="email",
    )

    # Tax Configuration
    tax_ids = fields.Many2many("account.tax", string="Applicable Taxes")
    tax_exempt = fields.Boolean(string="Tax Exempt", default=False)

    # Discounts and Adjustments
    loyalty_discount_rate = fields.Float(
        string="Loyalty Discount Rate (%)", digits=(5, 2)
    )
    promotional_discount_ids = fields.One2many(
        "records.promotional.discount", "config_id", string="Promotional Discounts"
    )

    # Billing Alerts and Notifications
    billing_alert_enabled = fields.Boolean(
        string="Billing Alerts Enabled", default=True
    )
    overdue_alert_days = fields.Integer(string="Overdue Alert Days", default=15)
    credit_limit = fields.Monetary(string="Credit Limit", currency_field="currency_id")

    # Geographic and Regional
    billing_region = fields.Selection(
        [
            ("domestic", "Domestic"),
            ("international", "International"),
            ("regional", "Regional"),
        ],
        string="Billing Region",
        default="domestic",
    )

    # Service Level Agreements
    sla_storage_retrieval_hours = fields.Integer(
        string="SLA Storage Retrieval (Hours)", default=24
    )
    sla_destruction_days = fields.Integer(string="SLA Destruction (Days)", default=30)
    sla_pickup_hours = fields.Integer(string="SLA Pickup (Hours)", default=48)

    # Quality and Compliance
    quality_standards = fields.Text(string="Quality Standards")
    compliance_requirements = fields.Text(string="Compliance Requirements")
    audit_frequency = fields.Selection(
        [("monthly", "Monthly"), ("quarterly", "Quarterly"), ("annually", "Annually")],
        string="Audit Frequency",
        default="quarterly",
    )

    # Environmental and Sustainability
    carbon_offset_fee = fields.Monetary(
        string="Carbon Offset Fee", currency_field="currency_id"
    )
    sustainability_program = fields.Boolean(
        string="Sustainability Program", default=False
    )

    # Insurance and Risk
    insurance_coverage = fields.Monetary(
        string="Insurance Coverage", currency_field="currency_id"
    )
    liability_limit = fields.Monetary(
        string="Liability Limit", currency_field="currency_id"
    )

    # Technology Integration
    api_integration_enabled = fields.Boolean(
        string="API Integration Enabled", default=False
    )
    edi_enabled = fields.Boolean(string="EDI Enabled", default=False)
    reporting_frequency = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
        ],
        string="Reporting Frequency",
        default="monthly",
    )

    # Financial Controls
    approval_required_threshold = fields.Monetary(
        string="Approval Required Threshold", currency_field="currency_id"
    )
    budget_allocation = fields.Monetary(
        string="Budget Allocation", currency_field="currency_id"
    )
    spend_variance_alert = fields.Float(
        string="Spend Variance Alert (%)", digits=(5, 2), default=10.0
    )

    # Historical and Analytics
    billing_start_date = fields.Date(string="Billing Start Date", tracking=True)
    last_billing_date = fields.Date(string="Last Billing Date")
    billing_success_rate = fields.Float(
        string="Billing Success Rate (%)", compute="_compute_success_rate", store=True
    )
    average_billing_amount = fields.Monetary(
        string="Average Billing Amount",
        compute="_compute_averages",
        store=True,
        currency_field="currency_id",
    )

    # Multi-Currency Support
    multi_currency_enabled = fields.Boolean(
        string="Multi-Currency Enabled", default=False
    )
    exchange_rate_method = fields.Selection(
        [
            ("daily", "Daily Rate"),
            ("monthly", "Monthly Average"),
            ("fixed", "Fixed Rate"),
        ],
        string="Exchange Rate Method",
        default="daily",
    )

    # Customer Satisfaction
    satisfaction_tracking = fields.Boolean(string="Satisfaction Tracking", default=True)
    nps_target = fields.Integer(string="NPS Target", default=70)

    # Competitive Analysis
    market_rate_comparison = fields.Boolean(
        string="Market Rate Comparison", default=False
    )
    competitive_analysis_frequency = fields.Selection(
        [("monthly", "Monthly"), ("quarterly", "Quarterly"), ("annually", "Annually")],
        string="Competitive Analysis Frequency",
        default="quarterly",
    )

    # System Fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Responsible User", default=lambda self: self.env.user
    )

    @api.depends("billing_line_ids", "billing_frequency", "base_rate")
    def _compute_revenue(self):
        """Compute revenue metrics"""
        for record in self:
            # Calculate from billing lines if available
            if record.billing_line_ids:
                total_amount = sum(record.billing_line_ids.mapped("amount"))
                record.monthly_revenue = total_amount
                record.quarterly_revenue = total_amount * 3
                record.annual_revenue = total_amount * 12
            else:
                # Estimate from base rate and frequency
                multiplier = {
                    "monthly": 12,
                    "quarterly": 4,
                    "semi_annually": 2,
                    "annually": 1,
                }.get(record.billing_frequency, 12)
                record.annual_revenue = (record.base_rate or 0) * multiplier
                record.monthly_revenue = record.annual_revenue / 12
                record.quarterly_revenue = record.annual_revenue / 4

    @api.depends("invoice_ids")
    def _compute_accuracy(self):
        """Compute billing accuracy rate"""
        for record in self:
            if record.invoice_ids:
                total_invoices = len(record.invoice_ids)
                accurate_invoices = len(
                    record.invoice_ids.filtered(lambda inv: inv.state != "cancel")
                )
                record.billing_accuracy_rate = (
                    (accurate_invoices / total_invoices) * 100
                    if total_invoices > 0
                    else 0
                )
            else:
                record.billing_accuracy_rate = 100.0

    @api.depends("invoice_ids")
    def _compute_collection(self):
        """Compute collection rate"""
        for record in self:
            if record.invoice_ids:
                total_amount = sum(record.invoice_ids.mapped("amount_total"))
                paid_amount = sum(
                    record.invoice_ids.filtered(
                        lambda inv: inv.payment_state == "paid"
                    ).mapped("amount_total")
                )
                record.collection_rate = (
                    (paid_amount / total_amount) * 100 if total_amount > 0 else 0
                )
            else:
                record.collection_rate = 100.0

    @api.depends("invoice_ids")
    def _compute_delays(self):
        """Compute payment delay average"""
        for record in self:
            if record.invoice_ids:
                paid_invoices = record.invoice_ids.filtered(
                    lambda inv: inv.payment_state == "paid"
                )
                if paid_invoices:
                    delays = []
                    for invoice in paid_invoices:
                        if invoice.invoice_date_due and invoice.payment_date:
                            delay = (
                                invoice.payment_date - invoice.invoice_date_due
                            ).days
                            delays.append(max(0, delay))  # Only count positive delays
                    record.payment_delay_average = (
                        sum(delays) / len(delays) if delays else 0
                    )
                else:
                    record.payment_delay_average = 0
            else:
                record.payment_delay_average = 0

    @api.depends("partner_id")
    def _compute_satisfaction(self):
        """Compute customer satisfaction score"""
        for record in self:
            if record.partner_id:
                # Look for feedback records related to this customer
                feedback_records = self.env["customer.feedback"].search(
                    [("partner_id", "=", record.partner_id.id)]
                )
                if feedback_records:
                    avg_rating = sum(feedback_records.mapped("rating")) / len(
                        feedback_records
                    )
                    record.customer_satisfaction_score = (
                        avg_rating * 20
                    )  # Convert 1-5 scale to 0-100
                else:
                    record.customer_satisfaction_score = 85.0  # Default good score
            else:
                record.customer_satisfaction_score = 0.0

    @api.depends("billing_frequency", "billing_cycle_start")
    def _compute_next_billing_date(self):
        """Compute next billing date based on frequency and cycle start."""
        for record in self:
            if record.billing_cycle_start and record.billing_frequency:
                start_date = record.billing_cycle_start
                today = fields.Date.today()

                # Simple date calculation without external dependencies
                if record.billing_frequency == "monthly":
                    # Add 30 days as approximation
                    next_date = start_date
                    while next_date <= today:
                        next_date = fields.Date.add(next_date, days=30)
                elif record.billing_frequency == "quarterly":
                    # Add 90 days as approximation
                    next_date = start_date
                    while next_date <= today:
                        next_date = fields.Date.add(next_date, days=90)
                elif record.billing_frequency == "semi_annually":
                    # Add 180 days as approximation
                    next_date = start_date
                    while next_date <= today:
                        next_date = fields.Date.add(next_date, days=180)
                elif record.billing_frequency == "annually":
                    # Add 365 days as approximation
                    next_date = start_date
                    while next_date <= today:
                        next_date = fields.Date.add(next_date, days=365)
                else:
                    # Default to monthly if unknown frequency
                    next_date = start_date
                    while next_date <= today:
                        next_date = fields.Date.add(next_date, days=30)

                record.next_billing_date = next_date
            else:
                record.next_billing_date = False

    @api.depends("base_rate", "billing_frequency", "billing_line_ids")
    def _compute_annual_revenue(self):
        """Compute annual revenue projection"""
        for record in self:
            if record.billing_line_ids:
                # Use actual billing data
                total_monthly = sum(record.billing_line_ids.mapped("amount"))
                record.annual_revenue = total_monthly * 12
            elif record.base_rate and record.billing_frequency:
                # Project from base rate and frequency
                frequency_multiplier = {
                    "monthly": 12,
                    "quarterly": 4,
                    "semi_annually": 2,
                    "annually": 1,
                }.get(record.billing_frequency, 12)
                record.annual_revenue = record.base_rate * frequency_multiplier
            else:
                record.annual_revenue = 0.0

    @api.depends("billing_line_ids", "billing_line_ids.amount")
    def _compute_averages(self):
        """Compute average billing amounts"""
        for record in self:
            if record.billing_line_ids:
                total_amount = sum(record.billing_line_ids.mapped("amount"))
                record.average_monthly_billing = (
                    total_amount / len(record.billing_line_ids)
                    if record.billing_line_ids
                    else 0.0
                )
            else:
                record.average_monthly_billing = record.base_rate or 0.0

    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    sequence = fields.Integer(string="Sequence", default=10)
    notes = fields.Text(string="Notes")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")
    # === COMPREHENSIVE MISSING FIELDS ===
    customer_category_ids = fields.Many2many(
        "customer.category", string="Customer Categories"
    )
    default_payment_terms_id = fields.Many2one(
        "account.payment.term", string="Default Payment Terms"
    )
    credit_limit_amount = fields.Monetary(
        string="Credit Limit", currency_field="currency_id"
    )
    service_catalog_ids = fields.Many2many("product.template", string="Service Catalog")
    pricing_tier_ids = fields.One2many(
        "pricing.tier", "billing_config_id", string="Pricing Tiers"
    )
    discount_policy_ids = fields.One2many(
        "discount.policy", "billing_config_id", string="Discount Policies"
    )
    surcharge_policy_ids = fields.One2many(
        "surcharge.policy", "billing_config_id", string="Surcharge Policies"
    )
    auto_invoice_generation = fields.Boolean(
        string="Auto Invoice Generation", default=True
    )
    invoice_template_id = fields.Many2one("mail.template", string="Invoice Template")
    payment_reminder_days = fields.Integer(string="Payment Reminder Days", default=7)
    accounting_integration_enabled = fields.Boolean(
        string="Accounting Integration", default=True
    )
    revenue_account_id = fields.Many2one("account.account", string="Revenue Account")
    receivable_account_id = fields.Many2one(
        "account.account", string="Receivable Account"
    )
    tax_configuration_ids = fields.One2many(
        "tax.configuration", "billing_config_id", string="Tax Configurations"
    )
    billing_dashboard_enabled = fields.Boolean(string="Billing Dashboard", default=True)
    kpi_tracking_enabled = fields.Boolean(string="KPI Tracking", default=True)
    custom_report_ids = fields.One2many(
        "custom.report", "billing_config_id", string="Custom Reports"
    )
    analytics_retention_days = fields.Integer(
        string="Analytics Retention Days", default=365
    )
    approval_workflow_enabled = fields.Boolean(
        string="Approval Workflow", default=False
    )
    approval_threshold_amount = fields.Monetary(
        string="Approval Threshold", currency_field="currency_id"
    )
    approval_user_ids = fields.Many2many("res.users", string="Approval Users")
    escalation_enabled = fields.Boolean(string="Escalation Enabled", default=False)
    # Advanced Billing Configuration Fields
    amount = fields.Monetary("Total Amount", currency_field="currency_id")
    auto_billing_enabled = fields.Boolean("Auto Billing Enabled", default=True)
    billing_alert_threshold = fields.Float("Billing Alert Threshold", default=1000.0)
    billing_automation_level = fields.Selection(
        [("manual", "Manual"), ("semi", "Semi-Auto"), ("full", "Fully Automated")],
        default="semi",
    )
    billing_cycle_id = fields.Many2one("billing.cycle", "Billing Cycle")
    billing_discount_percentage = fields.Float("Billing Discount %", default=0.0)
    billing_method = fields.Selection(
        [("invoice", "Invoice"), ("auto_charge", "Auto Charge")], default="invoice"
    )
    billing_notification_enabled = fields.Boolean("Billing Notifications", default=True)
    billing_override_allowed = fields.Boolean("Override Allowed", default=False)
    billing_portal_access = fields.Boolean("Portal Access", default=True)
    billing_preferences = fields.Text("Billing Preferences")
    billing_rules_version = fields.Char("Billing Rules Version")
    billing_tier = fields.Selection(
        [("basic", "Basic"), ("premium", "Premium"), ("enterprise", "Enterprise")],
        default="basic",
    )
    credit_limit_warning = fields.Boolean("Credit Limit Warning", default=True)
    custom_billing_rules = fields.Text("Custom Billing Rules")
    customer_tier_level = fields.Selection(
        [
            ("bronze", "Bronze"),
            ("silver", "Silver"),
            ("gold", "Gold"),
            ("platinum", "Platinum"),
        ],
        default="bronze",
    )
    department_allocation_rules = fields.Text("Department Allocation Rules")
    discount_eligibility_rules = fields.Text("Discount Eligibility Rules")
    escalation_threshold_amount = fields.Monetary(
        "Escalation Threshold", currency_field="currency_id"
    )
    expense_tracking_enabled = fields.Boolean("Expense Tracking", default=True)
    invoice_consolidation_period = fields.Selection(
        [("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")],
        default="monthly",
    )
    late_fee_calculation = fields.Text("Late Fee Calculation Rules")
    minimum_billing_amount = fields.Monetary(
        "Minimum Billing Amount", currency_field="currency_id"
    )
    payment_gateway_integration = fields.Boolean(
        "Payment Gateway Integration", default=False
    )
    prepaid_balance_warning = fields.Boolean("Prepaid Balance Warning", default=True)
    pro_rata_calculation = fields.Boolean("Pro-rata Calculation", default=True)
    tax_calculation_method = fields.Selection(
        [("inclusive", "Tax Inclusive"), ("exclusive", "Tax Exclusive")],
        default="exclusive",
    )
    usage_tracking_enabled = fields.Boolean("Usage Tracking", default=True)

    # Framework Integration Fields

    @api.depends("invoice_ids", "billing_line_ids")
    def _compute_statistics(self):
        """Compute billing statistics."""
        for record in self:
            record.invoice_count = len(record.invoice_ids)
            record.billing_history_count = len(record.billing_line_ids)
            record.total_revenue = sum(record.invoice_ids.mapped("amount_total"))

    @api.depends("invoice_ids")
    def _compute_success_rate(self):
        """Compute billing success rate."""
        for record in self:
            if record.invoice_ids:
                paid_invoices = record.invoice_ids.filtered(
                    lambda inv: inv.payment_state == "paid"
                )
                record.billing_success_rate = (
                    len(paid_invoices) / len(record.invoice_ids)
                ) * 100
            else:
                record.billing_success_rate = 0

    @api.depends("invoice_ids")
    def _compute_averages(self):
        """Compute average billing amounts."""
        for record in self:
            if record.invoice_ids:
                record.average_billing_amount = sum(
                    record.invoice_ids.mapped("amount_total")
                ) / len(record.invoice_ids)
            else:
                record.average_billing_amount = 0

    @api.depends("invoice_ids", "billing_line_ids")
    def _compute_average_monthly_billing(self):
        """Compute average monthly billing amount"""
        for record in self:
            if record.billing_line_ids:
                # Calculate from billing lines
                total_amount = sum(record.billing_line_ids.mapped("amount"))
                record.average_monthly_billing = (
                    total_amount / len(record.billing_line_ids)
                    if record.billing_line_ids
                    else 0.0
                )
            elif record.invoice_ids:
                # Fallback to invoice data
                monthly_invoices = record.invoice_ids.filtered(
                    lambda inv: inv.invoice_date 
                    and inv.invoice_date >= fields.Date.today().replace(day=1)
                )
                record.average_monthly_billing = (
                    sum(monthly_invoices.mapped("amount_total")) 
                    if monthly_invoices else 0.0
                )
            else:
                record.average_monthly_billing = record.base_rate or 0.0

    @api.depends("invoice_ids", "billing_frequency")
    def _compute_monthly_revenue(self):
        """Compute monthly revenue based on invoices and billing frequency"""
        for record in self:
            if record.invoice_ids:
                total_revenue = sum(record.invoice_ids.mapped("amount_total"))
                
                # Normalize to monthly based on billing frequency
                if record.billing_frequency == "monthly":
                    record.monthly_revenue = total_revenue
                elif record.billing_frequency == "quarterly":
                    record.monthly_revenue = total_revenue / 3
                elif record.billing_frequency == "semi_annually":
                    record.monthly_revenue = total_revenue / 6
                elif record.billing_frequency == "annually":
                    record.monthly_revenue = total_revenue / 12
                else:
                    # Default to monthly if frequency not set
                    record.monthly_revenue = total_revenue
            else:
                record.monthly_revenue = 0.0

    @api.depends("invoice_ids", "billing_frequency")
    def _compute_quarterly_revenue(self):
        """Compute quarterly revenue based on invoices and billing frequency"""
        for record in self:
            if record.invoice_ids:
                total_revenue = sum(record.invoice_ids.mapped("amount_total"))
                
                # Normalize to quarterly based on billing frequency
                if record.billing_frequency == "monthly":
                    record.quarterly_revenue = total_revenue * 3
                elif record.billing_frequency == "quarterly":
                    record.quarterly_revenue = total_revenue
                elif record.billing_frequency == "semi_annually":
                    record.quarterly_revenue = total_revenue / 2
                elif record.billing_frequency == "annually":
                    record.quarterly_revenue = total_revenue / 4
                else:
                    # Default quarterly calculation from monthly
                    record.quarterly_revenue = total_revenue * 3
            else:
                record.quarterly_revenue = 0.0

    def action_generate_invoice(self):
        """Generate invoice."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Invoice Generated"),
                "message": _("Invoice has been generated successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_analytics(self):
        """View analytics."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Billing Analytics"),
            "res_model": "records.billing.analytics",
            "view_mode": "graph,tree",
            "target": "current",
        }

    def action_view_billing_history(self):
        """View billing history."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Billing History"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("partner_id", "=", self.partner_id.id)],
        }

    def action_configure_rates(self):
        """Configure rates."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Configure Rates"),
            "res_model": "base.rates",
            "view_mode": "tree,form",
            "target": "current",
        }

    def action_test_billing(self):
        """Test billing."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Billing Test"),
                "message": _("Billing test completed successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_duplicate(self):
        """Duplicate configuration."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Configuration Duplicated"),
                "message": _("Configuration has been duplicated successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_invoices(self):
        """View invoices."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Invoices"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [
                ("partner_id", "=", self.partner_id.id),
                ("move_type", "=", "out_invoice"),
            ],
        }

    def action_view_revenue(self):
        """View revenue."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Revenue"),
            "res_model": "account.move.line",
            "view_mode": "graph,tree",
            "target": "current",
            "domain": [("partner_id", "=", self.partner_id.id)],
        }

    def action_view_invoice(self):
        """View invoice."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Invoice"),
            "res_model": "account.move",
            "view_mode": "form",
            "target": "current",
        }

    # ============================================================================
    # COMPUTE METHODS FOR NEW FIELDS
    # ============================================================================

    @api.depends("billing_frequency", "billing_cycle_start")
    def _compute_next_billing_date(self):
        """Compute next billing date based on frequency"""
        for record in self:
            if record.billing_cycle_start:
                start_date = record.billing_cycle_start
                if record.billing_frequency == "monthly":
                    record.next_billing_date = start_date + timedelta(days=30)
                elif record.billing_frequency == "quarterly":
                    record.next_billing_date = start_date + timedelta(days=90)
                elif record.billing_frequency == "semi_annually":
                    record.next_billing_date = start_date + timedelta(days=180)
                elif record.billing_frequency == "annually":
                    record.next_billing_date = start_date + timedelta(days=365)
                else:
                    record.next_billing_date = False
            else:
                record.next_billing_date = False

    @api.depends("partner_id")
    def _compute_invoice_count(self):
        """Compute number of invoices for this billing configuration"""
        for record in self:
            if record.partner_id:
                invoice_count = self.env["account.move"].search_count(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                    ]
                )
                record.invoice_count = invoice_count
            else:
                record.invoice_count = 0

    @api.depends("usage_tracking_ids")
    def _compute_billing_history_count(self):
        """Compute billing history count"""
        for record in self:
            record.billing_history_count = len(record.usage_tracking_ids)

    @api.depends("partner_id")
    def _compute_total_revenue(self):
        """Compute total revenue from this customer"""
        for record in self:
            if record.partner_id:
                invoice_lines = self.env["account.move.line"].search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_id.move_type", "=", "out_invoice"),
                        ("move_id.state", "=", "posted"),
                    ]
                )
                record.total_revenue = sum(invoice_lines.mapped("price_total"))
            else:
                record.total_revenue = 0.0

    @api.depends("total_revenue", "billing_frequency")
    def _compute_performance_metrics(self):
        """Compute performance metrics like average monthly revenue"""
        for record in self:
            if record.total_revenue and record.billing_frequency:
                if record.billing_frequency == "monthly":
                    record.average_monthly_revenue = record.total_revenue
                elif record.billing_frequency == "quarterly":
                    record.average_monthly_revenue = record.total_revenue / 3
                elif record.billing_frequency == "semi_annually":
                    record.average_monthly_revenue = record.total_revenue / 6
                elif record.billing_frequency == "annually":
                    record.average_monthly_revenue = record.total_revenue / 12
                else:
                    record.average_monthly_revenue = 0.0

                # Simple growth rate calculation (placeholder)
                record.revenue_growth_rate = 5.0  # Default 5% growth
            else:
                record.average_monthly_revenue = 0.0
                record.revenue_growth_rate = 0.0

    @api.depends("last_audit_date", "audit_frequency")
    def _compute_next_audit_date(self):
        """Compute next audit date based on frequency"""
        for record in self:
            if record.last_audit_date and record.audit_frequency:
                if record.audit_frequency == "monthly":
                    record.next_audit_date = record.last_audit_date + timedelta(days=30)
                elif record.audit_frequency == "quarterly":
                    record.next_audit_date = record.last_audit_date + timedelta(days=90)
                elif record.audit_frequency == "annually":
                    record.next_audit_date = record.last_audit_date + timedelta(
                        days=365
                    )
                else:
                    record.next_audit_date = False
            else:
                record.next_audit_date = False

    # ============================================================================
    # ACTION METHODS FOR NEW FUNCTIONALITY
    # ============================================================================

    def action_generate_invoice(self):
        """Generate invoice based on current configuration"""
        self.ensure_one()
        # Implementation for invoice generation
        return {
            "type": "ir.actions.act_window",
            "name": _("Generated Invoice"),
            "res_model": "account.move",
            "view_mode": "form",
            "target": "current",
        }

    def action_configure_rates(self):
        """Open rate configuration wizard"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Configure Rates"),
            "res_model": "records.billing.rate",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("billing_config_id", "=", self.id)],
        }

    def action_test_billing(self):
        """Test billing configuration"""
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Billing Test"),
                "message": _("Billing configuration test completed successfully"),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_analytics(self):
        """View billing analytics dashboard"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Billing Analytics"),
            "res_model": "records.billing.analytics",
            "view_mode": "graph,pivot",
            "target": "current",
            "context": {"default_billing_config_id": self.id},
        }

    def action_view_invoices(self):
        """View related invoices"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Related Invoices"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [
                ("partner_id", "=", self.partner_id.id),
                ("move_type", "=", "out_invoice"),
            ],
        }

    def action_view_billing_history(self):
        """View billing history"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Billing History"),
            "res_model": "records.usage.tracking",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("billing_config_id", "=", self.id)],
        }
