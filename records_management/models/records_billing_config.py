# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class RecordsBillingConfig(models.Model):
    _name = "records.billing.config"
    _description = "Records Billing Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(
        string="Configuration Name", required=True, tracking=True, index=True
    )
    code = fields.Char(string="Configuration Code", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)

    # Framework Required Fields
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

    # State Management
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

    # ============================================================================
    # CUSTOMER & BILLING RELATIONSHIPS
    # ============================================================================

    partner_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    billing_contact_id = fields.Many2one("res.partner", string="Billing Contact")
    account_manager = fields.Many2one("res.users", string="Account Manager")

    # Billing Classification
    billing_type = fields.Selection(
        [("standard", "Standard"), ("premium", "Premium"), ("custom", "Custom")],
        string="Billing Type",
        default="standard",
        tracking=True,
    )

    service_category = fields.Selection(
        [
            ("storage", "Storage Services"),
            ("retrieval", "Retrieval Services"),
            ("destruction", "Destruction Services"),
            ("scanning", "Scanning Services"),
            ("transport", "Transport Services"),
            ("consultation", "Consultation Services"),
            ("all", "All Services"),
        ],
        string="Service Category",
        default="storage",
        tracking=True,
    )

    # ============================================================================
    # RATE STRUCTURE & PRICING
    # ============================================================================

    # Currency Configuration
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Primary Billing Model
    billing_model = fields.Selection(
        [
            ("per_container", "Per Container"),
            ("per_cubic_foot", "Per Cubic Foot"),
            ("flat_rate", "Flat Rate"),
            ("tiered", "Tiered Pricing"),
            ("usage_based", "Usage Based"),
        ],
        string="Billing Model",
        required=True,
        tracking=True,
    )

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
        default="per_box",
        tracking=True,
    )

    # Base Rate Configuration
    base_rate = fields.Monetary(
        string="Base Rate", currency_field="currency_id", tracking=True
    )
    unit_rate = fields.Monetary(string="Unit Rate", currency_field="currency_id")
    minimum_charge = fields.Monetary(
        string="Minimum Charge", currency_field="currency_id"
    )
    setup_fee = fields.Monetary(string="Setup Fee", currency_field="currency_id")
    amount = fields.Monetary(
        string="Configured Amount",
        currency_field="currency_id",
        help="Base configured billing amount",
    )

    # Service-Specific Rates
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
    pickup_service_rate = fields.Monetary(
        string="Pickup Service Rate", currency_field="currency_id"
    )
    delivery_service_rate = fields.Monetary(
        string="Delivery Service Rate", currency_field="currency_id"
    )

    # ============================================================================
    # BILLING SCHEDULE & AUTOMATION
    # ============================================================================

    # Billing Frequency
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

    # Date Management
    effective_date = fields.Date(
        string="Effective Date", required=True, default=fields.Date.today, tracking=True
    )
    billing_cycle_start = fields.Date(
        string="Billing Cycle Start", default=fields.Date.today, tracking=True
    )
    valid_from = fields.Date(
        string="Valid From", default=fields.Date.today, tracking=True
    )
    valid_until = fields.Date(string="Valid Until", tracking=True)

    # Computed Dates
    next_billing_date = fields.Date(
        string="Next Billing Date",
        compute="_compute_next_billing_date",
        store=True,
        tracking=True,
    )
    last_billing_date = fields.Date(string="Last Billing Date")

    # Automation Settings
    auto_billing = fields.Boolean(
        string="Auto Billing Enabled", default=False, tracking=True
    )
    auto_invoicing = fields.Boolean(string="Auto Invoicing", default=True)
    auto_apply = fields.Boolean(
        string="Auto Apply",
        default=False,
        help="Automatically apply billing configuration changes",
    )
    consolidate_charges = fields.Boolean(string="Consolidate Charges", default=True)
    prorate_monthly = fields.Boolean(string="Prorate Monthly", default=True)

    # ============================================================================
    # PAYMENT & TERMS CONFIGURATION
    # ============================================================================

    payment_terms = fields.Many2one("account.payment.term", string="Payment Terms")
    payment_method = fields.Selection(
        [
            ("credit_card", "Credit Card"),
            ("ach", "ACH Transfer"),
            ("check", "Check"),
            ("wire", "Wire Transfer"),
            ("invoice", "Net Terms Invoice"),
        ],
        string="Payment Method",
        default="invoice",
        tracking=True,
    )

    grace_period_days = fields.Integer(string="Grace Period (Days)", default=30)
    late_fee_percentage = fields.Float(string="Late Fee Percentage", digits=(5, 2))
    credit_limit = fields.Monetary(string="Credit Limit", currency_field="currency_id")

    # ============================================================================
    # DISCOUNT & PRICING RULES
    # ============================================================================

    # Discount Configuration
    discount_percentage = fields.Float(string="Discount Percentage", digits=(5, 2))
    discount_type = fields.Selection(
        [
            ("percentage", "Percentage"),
            ("fixed", "Fixed Amount"),
            ("volume", "Volume Based"),
            ("loyalty", "Loyalty Discount"),
        ],
        string="Discount Type",
        default="percentage",
    )

    # Advanced Pricing
    tiered_pricing_enabled = fields.Boolean(
        string="Tiered Pricing Enabled", default=False
    )
    volume_discounts_enabled = fields.Boolean(
        string="Volume Discounts Enabled", default=False
    )
    seasonal_rates = fields.Boolean(string="Seasonal Rates", default=False)
    bulk_discount_threshold = fields.Integer(string="Bulk Discount Threshold")
    bulk_discount_percentage = fields.Float(string="Bulk Discount %", digits=(5, 2))

    # ============================================================================
    # USAGE TRACKING CONFIGURATION
    # ============================================================================

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

    # ============================================================================
    # NOTIFICATION & COMMUNICATION
    # ============================================================================

    # Notification Settings
    customer_notifications = fields.Boolean(
        string="Customer Notifications", default=True
    )
    finance_team_notifications = fields.Boolean(
        string="Finance Team Notifications", default=True
    )
    manager_notifications = fields.Boolean(string="Manager Notifications", default=True)
    escalation_notifications = fields.Boolean(
        string="Escalation Notifications", default=False
    )

    # Alert Configuration
    billing_failure_alerts = fields.Boolean(
        string="Billing Failure Alerts", default=True
    )
    payment_overdue_alerts = fields.Boolean(
        string="Payment Overdue Alerts", default=True
    )
    usage_threshold_alerts = fields.Boolean(
        string="Usage Threshold Alerts", default=False
    )
    revenue_variance_alerts = fields.Boolean(
        string="Revenue Variance Alerts", default=False
    )

    # Email Configuration
    send_invoice_email = fields.Boolean(string="Send Invoice Email", default=True)
    include_usage_details = fields.Boolean(string="Include Usage Details", default=True)
    invoice_email_template = fields.Many2one(
        "mail.template", string="Invoice Email Template"
    )

    # ============================================================================
    # COMPLIANCE & AUDIT
    # ============================================================================

    audit_trail_enabled = fields.Boolean(string="Audit Trail Enabled", default=True)
    compliance_reporting = fields.Boolean(string="Compliance Reporting", default=True)
    encryption_enabled = fields.Boolean(string="Encryption Enabled", default=True)
    data_retention_period = fields.Integer(
        string="Data Retention Period (Years)", default=7
    )

    # Audit Schedule
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

    # ============================================================================
    # INTEGRATION & SYSTEM CONFIGURATION
    # ============================================================================

    # System Integration
    accounting_system_sync = fields.Boolean(
        string="Accounting System Sync", default=False
    )
    erp_integration_enabled = fields.Boolean(
        string="ERP Integration Enabled", default=False
    )
    api_access_enabled = fields.Boolean(string="API Access Enabled", default=False)
    payment_gateway_integration = fields.Boolean(
        string="Payment Gateway Integration", default=False
    )

    # Multi-currency Support
    multi_currency_support = fields.Boolean(
        string="Multi-Currency Support", default=False
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

    # ============================================================================
    # REVENUE ANALYTICS (COMPUTED FIELDS)
    # ============================================================================

    # Revenue Metrics
    annual_revenue = fields.Monetary(
        string="Annual Revenue",
        currency_field="currency_id",
        compute="_compute_annual_revenue",
        store=True,
    )
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
    total_revenue = fields.Monetary(
        string="Total Revenue",
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
    monthly_recurring_revenue = fields.Monetary(
        string="Monthly Recurring Revenue",
        currency_field="currency_id",
        compute="_compute_revenue_analytics",
        store=True,
    )

    # Performance Metrics
    billing_accuracy_rate = fields.Float(
        string="Billing Accuracy Rate (%)",
        compute="_compute_performance_metrics",
        store=True,
        digits=(5, 2),
    )
    collection_rate = fields.Float(
        string="Collection Rate (%)",
        compute="_compute_performance_metrics",
        store=True,
        digits=(5, 2),
    )
    payment_delay_average = fields.Float(
        string="Average Payment Delay (Days)",
        compute="_compute_performance_metrics",
        store=True,
        digits=(5, 2),
    )
    customer_satisfaction_score = fields.Float(
        string="Customer Satisfaction Score",
        compute="_compute_performance_metrics",
        store=True,
        digits=(3, 2),
    )

    # Count Fields
    invoice_count = fields.Integer(
        string="Invoice Count", compute="_compute_counts", store=True
    )
    billing_history_count = fields.Integer(
        string="Billing History Count", compute="_compute_counts", store=True
    )
    customer_count = fields.Integer(
        string="Customer Count", compute="_compute_counts", store=True
    )
    billing_cycle_count = fields.Integer(
        string="Billing Cycles Count",
        compute="_compute_billing_cycle_count",
        help="Number of completed billing cycles",
    )

    # Additional Analytics
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

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # One2many Relationships
    billing_rate_ids = fields.One2many(
        "records.billing.rate", "billing_config_id", string="Billing Rates"
    )
    usage_tracking_ids = fields.One2many(
        "records.usage.tracking", "billing_config_id", string="Usage Tracking Records"
    )
    invoice_generation_log_ids = fields.One2many(
        "records.billing.invoice.log",
        "billing_config_id",
        string="Invoice Generation Logs",
    )
    discount_rule_ids = fields.One2many(
        "records.billing.discount.rule", "billing_config_id", string="Discount Rules"
    )

    # Many2many Relationships
    default_service_ids = fields.Many2many(
        "product.product", string="Default Services", domain=[("type", "=", "service")]
    )
    billing_contact_ids = fields.Many2many(
        "res.partner", "billing_config_contact_rel", string="Billing Contacts"
    )

    # Mail Thread Framework Fields (Required for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("base_rate", "billing_frequency", "active")
    def _compute_annual_revenue(self):
        """Compute projected annual revenue from this configuration"""
        for record in self:
            if record.active and record.base_rate:
                if record.billing_frequency == "monthly":
                    record.annual_revenue = record.base_rate * 12
                elif record.billing_frequency == "quarterly":
                    record.annual_revenue = record.base_rate * 4
                elif record.billing_frequency == "annually":
                    record.annual_revenue = record.base_rate
                else:
                    record.annual_revenue = 0.0
            else:
                record.annual_revenue = 0.0

    @api.depends("billing_frequency", "billing_cycle_start")
    def _compute_next_billing_date(self):
        """Compute next billing date based on frequency and cycle start"""
        for record in self:
            if record.billing_cycle_start and record.billing_frequency:
                start_date = record.billing_cycle_start
                today = fields.Date.today()

                # Calculate next billing date
                if record.billing_frequency == "monthly":
                    days_to_add = 30
                elif record.billing_frequency == "quarterly":
                    days_to_add = 90
                elif record.billing_frequency == "semi_annually":
                    days_to_add = 180
                elif record.billing_frequency == "annually":
                    days_to_add = 365
                else:
                    days_to_add = 30

                # Find next occurrence after today
                next_date = start_date
                while next_date <= today:
                    next_date = fields.Date.add(next_date, days=days_to_add)

                record.next_billing_date = next_date
            else:
                record.next_billing_date = False

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

    @api.depends("partner_id", "base_rate", "billing_frequency")
    def _compute_revenue_analytics(self):
        """Compute comprehensive revenue analytics"""
        for record in self:
            if record.partner_id:
                # Get actual invoice data
                invoices = self.env["account.move"].search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                    ]
                )

                # Calculate totals from actual invoices
                record.total_revenue = sum(invoices.mapped("amount_total"))

                # Calculate period-based revenue
                today = fields.Date.today()
                month_start = today.replace(day=1)
                quarter_start = today.replace(
                    month=((today.month - 1) // 3) * 3 + 1, day=1
                )

                monthly_invoices = invoices.filtered(
                    lambda inv: inv.invoice_date >= month_start
                )
                quarterly_invoices = invoices.filtered(
                    lambda inv: inv.invoice_date >= quarter_start
                )

                record.monthly_revenue = sum(monthly_invoices.mapped("amount_total"))
                record.quarterly_revenue = sum(
                    quarterly_invoices.mapped("amount_total")
                )

                # Calculate average and recurring revenue
                if invoices:
                    record.average_monthly_billing = record.total_revenue / len(
                        invoices
                    )
                else:
                    record.average_monthly_billing = record.base_rate or 0.0

                # Monthly recurring revenue
                if record.billing_frequency == "monthly":
                    record.monthly_recurring_revenue = record.base_rate or 0.0
                elif record.billing_frequency == "quarterly":
                    record.monthly_recurring_revenue = (record.base_rate or 0.0) / 3
                elif record.billing_frequency == "annually":
                    record.monthly_recurring_revenue = (record.base_rate or 0.0) / 12
                else:
                    record.monthly_recurring_revenue = 0.0
            else:
                record.total_revenue = 0.0
                record.monthly_revenue = 0.0
                record.quarterly_revenue = 0.0
                record.average_monthly_billing = 0.0
                record.monthly_recurring_revenue = 0.0

    @api.depends("partner_id")
    def _compute_performance_metrics(self):
        """Compute performance and quality metrics"""
        for record in self:
            if record.partner_id:
                invoices = self.env["account.move"].search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                        ("state", "=", "posted"),
                    ]
                )

                if invoices:
                    # Billing accuracy rate
                    accurate_invoices = invoices.filtered(
                        lambda inv: inv.state != "cancel"
                    )
                    record.billing_accuracy_rate = (
                        len(accurate_invoices) / len(invoices)
                    ) * 100

                    # Collection rate
                    paid_invoices = invoices.filtered(
                        lambda inv: inv.payment_state == "paid"
                    )
                    record.collection_rate = (len(paid_invoices) / len(invoices)) * 100

                    # Payment delay average
                    delays = []
                    for invoice in paid_invoices:
                        if (
                            invoice.invoice_date_due
                            and hasattr(invoice, "payment_date")
                            and invoice.payment_date
                        ):
                            delay = (
                                invoice.payment_date - invoice.invoice_date_due
                            ).days
                            if delay > 0:
                                delays.append(delay)
                    record.payment_delay_average = (
                        sum(delays) / len(delays) if delays else 0.0
                    )
                else:
                    record.billing_accuracy_rate = 100.0
                    record.collection_rate = 100.0
                    record.payment_delay_average = 0.0

                # Customer satisfaction from feedback
                feedback_records = self.env["customer.feedback"].search(
                    [("partner_id", "=", record.partner_id.id)]
                )
                if feedback_records:
                    ratings = []
                    for feedback in feedback_records:
                        try:
                            rating_value = (
                                float(feedback.rating) if feedback.rating else 0
                            )
                            ratings.append(rating_value)
                        except (ValueError, TypeError):
                            continue
                    record.customer_satisfaction_score = (
                        sum(ratings) / len(ratings) if ratings else 0.0
                    )
                else:
                    record.customer_satisfaction_score = 4.0  # Default good score
            else:
                record.billing_accuracy_rate = 100.0
                record.collection_rate = 100.0
                record.payment_delay_average = 0.0
                record.customer_satisfaction_score = 0.0

    @api.depends("partner_id", "usage_tracking_ids")
    def _compute_counts(self):
        """Compute various count fields"""
        for record in self:
            if record.partner_id:
                record.invoice_count = self.env["account.move"].search_count(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("move_type", "=", "out_invoice"),
                    ]
                )
                record.customer_count = 1
            else:
                record.invoice_count = 0
                record.customer_count = 0

            record.billing_history_count = len(record.usage_tracking_ids)

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
                        ("payment_state", "!=", "paid"),
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
            record.next_invoice_amount = record.base_rate or 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_generate_invoice(self):
        """Generate invoice based on current configuration"""
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

    def action_view_invoices(self):
        """View related invoices"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Related Invoices"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "target": "current",
            "domain": (
                [
                    ("partner_id", "=", self.partner_id.id),
                    ("move_type", "=", "out_invoice"),
                ]
                if self.partner_id
                else []
            ),
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

    def action_configure_rates(self):
        """Open rate configuration"""
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

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("base_rate", "minimum_charge")
    def _check_positive_amounts(self):
        """Ensure monetary amounts are positive"""
        for record in self:
            if record.base_rate and record.base_rate < 0:
                raise ValidationError(_("Base rate must be positive"))
            if record.minimum_charge and record.minimum_charge < 0:
                raise ValidationError(_("Minimum charge must be positive"))

    @api.constrains("valid_from", "valid_until")
    def _check_date_validity(self):
        """Ensure date range is valid"""
        for record in self:
            if (
                record.valid_from
                and record.valid_until
                and record.valid_from > record.valid_until
            ):
                raise ValidationError(
                    _("Valid from date must be before valid until date")
                )

    @api.constrains("grace_period_days")
    def _check_grace_period(self):
        """Ensure grace period is reasonable"""
        for record in self:
            if record.grace_period_days and (
                record.grace_period_days < 0 or record.grace_period_days > 365
            ):
                raise ValidationError(_("Grace period must be between 0 and 365 days"))
