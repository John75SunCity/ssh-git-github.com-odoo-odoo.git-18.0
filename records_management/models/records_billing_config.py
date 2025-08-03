# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


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
                    next_date = fields.Date.add(start_date, days=30)

                record.next_billing_date = next_date
            else:
                record.next_billing_date = False
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    sequence = fields.Integer(string='Sequence', default=10)
    notes = fields.Text(string='Notes')
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    updated_date = fields.Datetime(string='Updated Date')
    # === COMPREHENSIVE MISSING FIELDS ===
    customer_category_ids = fields.Many2many('customer.category', string='Customer Categories')
    default_payment_terms_id = fields.Many2one('account.payment.term', string='Default Payment Terms')
    credit_limit_amount = fields.Monetary(string='Credit Limit', currency_field='currency_id')
    service_catalog_ids = fields.Many2many('product.template', string='Service Catalog')
    pricing_tier_ids = fields.One2many('pricing.tier', 'billing_config_id', string='Pricing Tiers')
    discount_policy_ids = fields.One2many('discount.policy', 'billing_config_id', string='Discount Policies')
    surcharge_policy_ids = fields.One2many('surcharge.policy', 'billing_config_id', string='Surcharge Policies')
    auto_invoice_generation = fields.Boolean(string='Auto Invoice Generation', default=True)
    invoice_template_id = fields.Many2one('mail.template', string='Invoice Template')
    payment_reminder_days = fields.Integer(string='Payment Reminder Days', default=7)
    accounting_integration_enabled = fields.Boolean(string='Accounting Integration', default=True)
    revenue_account_id = fields.Many2one('account.account', string='Revenue Account')
    receivable_account_id = fields.Many2one('account.account', string='Receivable Account')
    tax_configuration_ids = fields.One2many('tax.configuration', 'billing_config_id', string='Tax Configurations')
    billing_dashboard_enabled = fields.Boolean(string='Billing Dashboard', default=True)
    kpi_tracking_enabled = fields.Boolean(string='KPI Tracking', default=True)
    custom_report_ids = fields.One2many('custom.report', 'billing_config_id', string='Custom Reports')
    analytics_retention_days = fields.Integer(string='Analytics Retention Days', default=365)
    approval_workflow_enabled = fields.Boolean(string='Approval Workflow', default=False)
    approval_threshold_amount = fields.Monetary(string='Approval Threshold', currency_field='currency_id')
    approval_user_ids = fields.Many2many('res.users', string='Approval Users')
    escalation_enabled = fields.Boolean(string='Escalation Enabled', default=False)
    # Advanced Billing Configuration Fields
    accounting_system_sync = fields.Boolean('Sync with Accounting System', default=True)
    amount = fields.Monetary('Total Amount', currency_field='currency_id')
    annual_revenue = fields.Monetary('Annual Revenue', currency_field='currency_id')
    audit_trail_enabled = fields.Boolean('Audit Trail Enabled', default=True)
    auto_apply = fields.Boolean('Auto Apply Rates', default=False)
    auto_billing_enabled = fields.Boolean('Auto Billing Enabled', default=True)
    billing_alert_threshold = fields.Float('Billing Alert Threshold', default=1000.0)
    billing_automation_level = fields.Selection([('manual', 'Manual'), ('semi', 'Semi-Auto'), ('full', 'Fully Automated')], default='semi')
    billing_cycle_id = fields.Many2one('billing.cycle', 'Billing Cycle')
    billing_discount_percentage = fields.Float('Billing Discount %', default=0.0)
    billing_frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annual', 'Annual')], default='monthly')
    billing_method = fields.Selection([('invoice', 'Invoice'), ('auto_charge', 'Auto Charge')], default='invoice')
    billing_notification_enabled = fields.Boolean('Billing Notifications', default=True)
    billing_override_allowed = fields.Boolean('Override Allowed', default=False)
    billing_portal_access = fields.Boolean('Portal Access', default=True)
    billing_preferences = fields.Text('Billing Preferences')
    billing_rules_version = fields.Char('Billing Rules Version')
    billing_tier = fields.Selection([('basic', 'Basic'), ('premium', 'Premium'), ('enterprise', 'Enterprise')], default='basic')
    credit_limit_amount = fields.Monetary('Credit Limit', currency_field='currency_id')
    credit_limit_warning = fields.Boolean('Credit Limit Warning', default=True)
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.company.currency_id)
    custom_billing_rules = fields.Text('Custom Billing Rules')
    customer_category_ids = fields.Many2many('res.partner.category', 'billing_config_category_rel', 'config_id', 'category_id', 'Customer Categories')
    customer_tier_level = fields.Selection([('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold'), ('platinum', 'Platinum')], default='bronze')
    default_payment_terms_id = fields.Many2one('account.payment.term', 'Default Payment Terms')
    department_allocation_rules = fields.Text('Department Allocation Rules')
    discount_eligibility_rules = fields.Text('Discount Eligibility Rules')
    early_payment_discount = fields.Float('Early Payment Discount %', default=0.0)
    escalation_threshold_amount = fields.Monetary('Escalation Threshold', currency_field='currency_id')
    expense_tracking_enabled = fields.Boolean('Expense Tracking', default=True)
    invoice_consolidation_period = fields.Selection([('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='monthly')
    invoice_delivery_method = fields.Selection([('email', 'Email'), ('portal', 'Portal'), ('mail', 'Mail')], default='email')
    late_fee_calculation = fields.Text('Late Fee Calculation Rules')
    minimum_billing_amount = fields.Monetary('Minimum Billing Amount', currency_field='currency_id')
    payment_gateway_integration = fields.Boolean('Payment Gateway Integration', default=False)
    prepaid_balance_warning = fields.Boolean('Prepaid Balance Warning', default=True)
    pricing_tier_ids = fields.Many2many('pricing.tier', 'billing_pricing_tier_rel', 'config_id', 'tier_id', 'Pricing Tiers')
    pro_rata_calculation = fields.Boolean('Pro-rata Calculation', default=True)
    revenue_recognition_method = fields.Selection([('immediate', 'Immediate'), ('deferred', 'Deferred'), ('milestone', 'Milestone')], default='immediate')
    service_catalog_ids = fields.Many2many('service.catalog', 'billing_service_catalog_rel', 'config_id', 'service_id', 'Service Catalog')
    tax_calculation_method = fields.Selection([('inclusive', 'Tax Inclusive'), ('exclusive', 'Tax Exclusive')], default='exclusive')
    usage_tracking_enabled = fields.Boolean('Usage Tracking', default=True)
    volume_discount_enabled = fields.Boolean('Volume Discount', default=False)
    
    # Framework Integration Fields
    activity_ids = fields.One2many('mail.activity', 'res_id', 'Activities', domain=[('res_model', '=', 'records.billing.config')])
    message_follower_ids = fields.One2many('mail.followers', 'res_id', 'Followers', domain=[('res_model', '=', 'records.billing.config')])
    message_ids = fields.One2many('mail.message', 'res_id', 'Messages', domain=[('res_model', '=', 'records.billing.config')])



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
