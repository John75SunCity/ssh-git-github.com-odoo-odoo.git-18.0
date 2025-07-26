# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta

class RecordsBillingConfig(models.Model):
    """Configuration for records management billing"""
    _name = 'records.billing.config'
    _description = 'Records Billing Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Configuration Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    
    # Billing cycles
    billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    
    # Billing day
    billing_day = fields.Integer(string='Billing Day of Month', default=1, 
                                help='Day of the month when billing is generated')
    
    # Auto-billing settings
    auto_generate_invoices = fields.Boolean(string='Auto Generate Invoices', default=True, tracking=True)
    auto_send_invoices = fields.Boolean(string='Auto Send Invoices', default=False, tracking=True)
    
    # Default terms
    default_payment_terms = fields.Many2one('account.payment.term', string='Default Payment Terms')
    
    # Late fee settings
    apply_late_fees = fields.Boolean(string='Apply Late Fees', default=False, tracking=True)
    late_fee_percentage = fields.Float(string='Late Fee Percentage', default=0.0)
    late_fee_grace_days = fields.Integer(string='Grace Period (Days)', default=0)
    
    # Additional Billing Configuration Fields
    accounting_system_sync = fields.Boolean(string='Accounting System Sync', default=False)
    annual_revenue = fields.Float(string='Annual Revenue', compute='_compute_annual_revenue')
    audit_trail_enabled = fields.Boolean(string='Audit Trail Enabled', default=True)
    auto_apply = fields.Boolean(string='Auto Apply Rules', default=True)
    auto_billing = fields.Boolean(string='Auto Billing Enabled', default=True)
    average_monthly_billing = fields.Float(string='Average Monthly Billing', compute='_compute_average_monthly_billing')
    base_rate = fields.Float(string='Base Rate')
    billable = fields.Boolean(string='Billable', default=True)
    billing_accuracy_rate = fields.Float(string='Billing Accuracy Rate (%)', default=100.0)
    billing_cycle_start = fields.Date(string='Billing Cycle Start Date')
    billing_failure_alerts = fields.Boolean(string='Billing Failure Alerts', default=True)
    billing_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    billing_history_count = fields.Integer(string='Billing History Count', compute='_compute_billing_history_count')
    billing_model = fields.Selection([
        ('subscription', 'Subscription'),
        ('usage', 'Usage Based'),
        ('hybrid', 'Hybrid'),
        ('project', 'Project Based')
    billing_rate_ids = fields.One2many('records.billing.rate', 'config_id', string='Billing Rates')
    
    # Notification Settings
    cc_accounting = fields.Boolean(string='CC Accounting Team', default=True)
    collection_rate = fields.Float(string='Collection Rate (%)', default=95.0)
    compliance_reporting = fields.Boolean(string='Compliance Reporting', default=True)
    consolidate_charges = fields.Boolean(string='Consolidate Charges', default=False)
    cost_amount = fields.Float(string='Cost Amount')
    customer_count = fields.Integer(string='Customer Count', compute='_compute_customer_count')
    customer_notifications = fields.Boolean(string='Customer Notifications', default=True)
    customer_satisfaction_score = fields.Float(string='Customer Satisfaction Score', default=0.0)
    data_retention_period = fields.Integer(string='Data Retention Period (Years)', default=7)
    
    # Discount and Pricing Rules
    discount_rule_ids = fields.One2many('records.billing.discount.rule', 'config_id', string='Discount Rules')
    discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('tiered', 'Tiered'),
        ('volume', 'Volume Based')
    discount_value = fields.Float(string='Discount Value')
    effective_date = fields.Date(string='Effective Date', default=fields.Date.today)
    encryption_enabled = fields.Boolean(string='Encryption Enabled', default=True)
    escalation_notifications = fields.Boolean(string='Escalation Notifications', default=True)
    
    # Finance and Management
    finance_team_notifications = fields.Boolean(string='Finance Team Notifications', default=True)
    generation_date = fields.Datetime(string='Last Generation Date')
    grace_period_days = fields.Integer(string='Grace Period Days', default=30)
    include_usage_details = fields.Boolean(string='Include Usage Details', default=True)
    invoice_count = fields.Integer(string='Invoice Count', compute='_compute_invoice_count')
    invoice_email_template = fields.Many2one('mail.template', string='Invoice Email Template')
    invoice_generation_log_ids = fields.One2many('records.billing.generation.log', 'config_id', string='Generation Logs')
    invoice_number = fields.Char(string='Last Invoice Number')
    invoice_status = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    invoice_template = fields.Many2one('account.move', string='Invoice Template')
    last_invoice_date = fields.Date(string='Last Invoice Date')
    
    # Manager and Payment Settings
    manager_notifications = fields.Boolean(string='Manager Notifications', default=True)
    minimum_charge = fields.Float(string='Minimum Charge')
    minimum_threshold = fields.Float(string='Minimum Threshold')
    monthly_revenue = fields.Float(string='Monthly Revenue', compute='_compute_monthly_revenue')
    multi_currency_support = fields.Boolean(string='Multi Currency Support', default=False)
    next_billing_date = fields.Date(string='Next Billing Date', compute='_compute_next_billing_date')
    payment_delay_average = fields.Float(string='Average Payment Delay (Days)')
    payment_gateway_integration = fields.Boolean(string='Payment Gateway Integration', default=False)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
        ('ach', 'ACH'),
        ('wire', 'Wire Transfer')
    payment_overdue_alerts = fields.Boolean(string='Payment Overdue Alerts', default=True)
    payment_terms = fields.Many2one('account.payment.term', string='Default Payment Terms')
    
    # Period and Time Management
    period = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    period_end = fields.Date(string='Current Period End')
    period_start = fields.Date(string='Current Period Start')
    profit_margin = fields.Float(string='Target Profit Margin (%)')
    prorate_monthly = fields.Boolean(string='Prorate Monthly Charges', default=True)
    quarterly_revenue = fields.Float(string='Quarterly Revenue', compute='_compute_quarterly_revenue')
    
    # Rate and Revenue Management
    rate_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('variable', 'Variable'),
        ('tiered', 'Tiered'),
        ('custom', 'Custom')
    rate_unit = fields.Selection([
        ('box', 'Per Box'),
        ('cubic_foot', 'Per Cubic Foot'),
        ('hour', 'Per Hour'),
        ('project', 'Per Project')
    reminder_schedule = fields.Text(string='Reminder Schedule')
    revenue_amount = fields.Float(string='Revenue Amount')
    revenue_analytics_ids = fields.One2many('records.billing.revenue.analytics', 'config_id', string='Revenue Analytics')
    revenue_variance_alerts = fields.Boolean(string='Revenue Variance Alerts', default=True)
    rule_name = fields.Char(string='Primary Rule Name')
    
    # Email and Communication Settings
    send_invoice_email = fields.Boolean(string='Send Invoice Email', default=True)
    service_category = fields.Selection([
        ('storage', 'Storage'),
        ('destruction', 'Destruction'),
        ('retrieval', 'Retrieval'),
        ('scanning', 'Scanning'),
        ('consultation', 'Consultation')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended')
    
    # Tax and Financial Calculation
    tax_calculation_method = fields.Selection([
        ('inclusive', 'Tax Inclusive'),
        ('exclusive', 'Tax Exclusive'),
        ('exempt', 'Tax Exempt')
    tier_threshold = fields.Float(string='Tier Threshold')
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost')
    total_revenue = fields.Float(string='Total Revenue', compute='_compute_total_revenue')
    
    # Tracking and Usage Monitoring
    track_access_frequency = fields.Boolean(string='Track Access Frequency', default=True)
    track_box_storage = fields.Boolean(string='Track Box Storage', default=True)
    track_destruction_services = fields.Boolean(string='Track Destruction Services', default=True)
    track_digital_services = fields.Boolean(string='Track Digital Services', default=True)
    track_document_count = fields.Boolean(string='Track Document Count', default=True)
    track_pickup_delivery = fields.Boolean(string='Track Pickup/Delivery', default=True)
    track_retrieval_requests = fields.Boolean(string='Track Retrieval Requests', default=True)
    track_special_handling = fields.Boolean(string='Track Special Handling', default=True)
    tracking_date = fields.Date(string='Last Tracking Date')
    
    # Unit and Usage Configuration
    unit_of_measure = fields.Many2one('uom.uom', string='Unit of Measure')
    unit_rate = fields.Float(string='Unit Rate')
    usage_threshold_alerts = fields.Boolean(string='Usage Threshold Alerts', default=True)
    usage_tracking_ids = fields.One2many('records.billing.usage.tracking', 'config_id', string='Usage Tracking')
    valid_until = fields.Date(string='Valid Until')
    
    # Compute Methods for Billing Configuration
    @api.depends('revenue_analytics_ids')
    def _compute_annual_revenue(self):
        for config in self:
            # Calculate based on analytics or estimates
            config.annual_revenue = config.monthly_revenue * 12 if config.monthly_revenue else 0.0
    
    @api.depends('monthly_revenue')
    def _compute_average_monthly_billing(self):
        for config in self:
            # For now, use monthly revenue as baseline
            config.average_monthly_billing = config.monthly_revenue or 0.0
    
    def _compute_billing_history_count(self):
        for config in self:
            config.billing_history_count = len(config.invoice_generation_log_ids)
    
    def _compute_customer_count(self):
        for config in self:
            # Count customers using this config (placeholder logic)
            config.customer_count = 0
    
    def _compute_invoice_count(self):
        for config in self:
            config.invoice_count = len(config.invoice_generation_log_ids)
    
    @api.depends('period', 'period_start')
    def _compute_next_billing_date(self):
        for config in self:
            if config.period_start:
                if config.period == 'monthly':
                    config.next_billing_date = config.period_start + relativedelta(months=1)
                elif config.period == 'quarterly':
                    config.next_billing_date = config.period_start + relativedelta(months=3)
                elif config.period == 'annually':
                    config.next_billing_date = config.period_start + relativedelta(years=1)
                else:
                    config.next_billing_date = config.period_start
            else:
                config.next_billing_date = False
    
    @api.depends('revenue_analytics_ids')
    def _compute_monthly_revenue(self):
        for config in self:
            config.monthly_revenue = sum(config.revenue_analytics_ids.mapped('monthly_amount'))
    
    @api.depends('monthly_revenue')
    def _compute_quarterly_revenue(self):
        for config in self:
            config.quarterly_revenue = config.monthly_revenue * 3
    
    def _compute_total_cost(self):
        for config in self:
            config.total_cost = config.cost_amount or 0.0
    
    @api.depends('revenue_analytics_ids')
    def _compute_total_revenue(self):
        for config in self:
            config.total_revenue = sum(config.revenue_analytics_ids.mapped('total_amount'))

# Additional Related Models for One2many relationships
class RecordsBillingRate(models.Model):
    _name = 'records.billing.rate'
    _description = 'Records Billing Rate'
    
    config_id = fields.Many2one('records.billing.config', string='Configuration', required=True, ondelete='cascade')
    service_type = fields.Selection([
        ('storage', 'Storage'),
        ('destruction', 'Destruction'),
        ('retrieval', 'Retrieval'),
        ('scanning', 'Scanning')
    rate = fields.Float(string='Rate', required=True)
    unit = fields.Char(string='Unit')

class RecordsBillingDiscountRule(models.Model):
    _name = 'records.billing.discount.rule'
    _description = 'Records Billing Discount Rule'
    
    discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount')
    min_threshold = fields.Float(string='Minimum Threshold')

class RecordsBillingGenerationLog(models.Model):
    _name = 'records.billing.generation.log'
    _description = 'Records Billing Generation Log'
    
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial')
    total_amount = fields.Float(string='Total Amount')
    error_message = fields.Text(string='Error Message')

class RecordsBillingRevenueAnalytics(models.Model):
    _name = 'records.billing.revenue.analytics'
    _description = 'Records Billing Revenue Analytics'
    
    period_date = fields.Date(string='Period Date', required=True)
    monthly_amount = fields.Float(string='Monthly Amount')
    service_count = fields.Integer(string='Service Count')

class RecordsBillingUsageTracking(models.Model):
    _name = 'records.billing.usage.tracking'
    _description = 'Records Billing Usage Tracking'
    
        ('retrieval', 'Retrieval'),
        ('scanning', 'Scanning')
    usage_count = fields.Integer(string='Usage Count')
    usage_amount = fields.Float(string='Usage Amount')
    customer_id = fields.Many2one('res.partner', string='Customer')
    

class RecordsBillingPeriod(models.Model):
    """Billing periods for records management"""
    _name = 'records.billing.period'
    _description = 'Records Billing Period'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc'

    billing_config_id = fields.Many2one('records.billing.config', string='Billing Configuration', required=True)
    
    # Period dates
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', required=True, tracking=True)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    
    # Billing lines
    billing_line_ids = fields.One2many('records.billing.line', 'billing_period_id', string='Billing Lines')
    
    # Totals
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    
    @api.depends('billing_line_ids.amount')
    def _compute_totals(self):
        for period in self:
            period.total_amount = sum(period.billing_line_ids.mapped('amount'))

class RecordsBillingLine(models.Model):
    """Individual billing line items - Enhanced for dual billing model"""
    _name = 'records.billing.line'
    _description = 'Records Billing Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    billing_period_id = fields.Many2one('records.billing.period', string='Billing Period', ondelete='cascade')
    advanced_billing_period_id = fields.Many2one('records.advanced.billing.period', string='Advanced Billing Period', ondelete='cascade')
    department_id = fields.Many2one('records.department', string='Department', tracking=True)
    
    # Line type for advanced billing
    line_type = fields.Selection([
        ('storage', 'Storage'),
        ('service', 'Service')
    
    # Service details
        ('retrieval', 'Retrieval'),
        ('destruction', 'Destruction'),
        ('scanning', 'Scanning'),
        ('delivery', 'Delivery'),
        ('other', 'Other')
    
    description = fields.Text(string='Description', required=True)
    
    # Quantities and pricing
    quantity = fields.Float(string='Quantity', default=1.0, tracking=True)
    unit_price = fields.Monetary(string='Unit Price', tracking=True)
    amount = fields.Monetary(string='Amount', compute='_compute_amount', store=True, tracking=True)
    
    # Period information for storage billing
    period_start_date = fields.Date(string='Period Start Date', tracking=True)
    period_end_date = fields.Date(string='Period End Date', tracking=True)
    
    # Service completion date for service billing
    service_date = fields.Date(string='Service Date', tracking=True,
                              help="Date when service was completed (for arrears billing)")
    
    # References to source records
    box_id = fields.Many2one('records.box', string='Related Box')
    service_request_id = fields.Many2one('records.service.request', string='Related Service Request')
    retrieval_work_order_id = fields.Many2one('document.retrieval.work.order', string='Retrieval Work Order')
    shredding_work_order_id = fields.Many2one('work.order.shredding', string='Shredding Work Order')
    
    # Billing direction indicator
    billing_direction = fields.Selection([
        ('advance', 'In Advance'),
        ('arrears', 'In Arrears')
    
    @api.depends('quantity', 'unit_price')
    def _compute_amount(self):
        for line in self:
            line.amount = line.quantity * line.unit_price
    
    @api.depends('line_type', 'service_type')
    def _compute_billing_direction(self):
        for line in self:
            if line.line_type == 'storage' or line.service_type == 'storage':
                # Storage is typically billed in advance
                line.billing_direction = 'advance'
            else:
                # Services are typically billed in arrears
                line.billing_direction = 'arrears'

class RecordsServicePricing(models.Model):
    """Service pricing configuration"""
    _name = 'records.service.pricing'
    _description = 'Records Service Pricing'
    _inherit = ['mail.thread', 'mail.activity.mixin']

        ('retrieval', 'Retrieval'),
        ('destruction', 'Destruction'),
        ('scanning', 'Scanning'),
        ('delivery', 'Delivery'),
        ('other', 'Other')
    
    # Pricing model
    pricing_model = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('tiered', 'Tiered Pricing'),
        ('volume', 'Volume Based')
    
    # Basic pricing
    base_price = fields.Monetary(string='Base Price', tracking=True)
    
    # Validity
    valid_to = fields.Date(string='Valid To', tracking=True)
    
    # Pricing breaks
    pricing_break_ids = fields.One2many('records.service.pricing.break', 'pricing_id', string='Pricing Breaks')

class RecordsServicePricingBreak(models.Model):
    """Pricing breaks for tiered pricing"""
    _name = 'records.service.pricing.break'
    _description = 'Records Service Pricing Break'

    pricing_id = fields.Many2one('records.service.pricing', string='Pricing', required=True, ondelete='cascade')
    
    # Quantity ranges
    quantity_from = fields.Float(string='Quantity From', default=0.0)
    quantity_to = fields.Float(string='Quantity To')
    
    # Pricing
    
    # Discounts
    discount_percentage = fields.Float(string='Discount %', default=0.0)

class RecordsProduct(models.Model):
    """Records management specific products"""
    _name = 'records.product'
    _description = 'Records Product'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    code = fields.Char(string='Product Code', tracking=True)
    
    # Product type
    product_type = fields.Selection([
        ('box', 'Storage Box'),
        ('service', 'Service'),
        ('material', 'Material'),
        ('equipment', 'Equipment')
    
    # Pricing
    list_price = fields.Monetary(string='List Price', tracking=True)
    cost_price = fields.Monetary(string='Cost Price', tracking=True)
    
    # Status
    
    # Related product if any
    product_id = fields.Many2one('product.product', string='Related Odoo Product')

class RecordsBillingAutomation(models.Model):
    """Automation rules for billing"""
    _name = 'records.billing.automation'
    _description = 'Records Billing Automation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    
    # Trigger conditions
    trigger_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('box_added', 'Box Added'),
        ('service_completed', 'Service Completed'),
        ('manual', 'Manual Only')
    
    # Rule configuration
        ('retrieval', 'Retrieval'),
        ('destruction', 'Destruction'),
        ('scanning', 'Scanning'),
        ('delivery', 'Delivery'),
        ('other', 'Other')
    
    # Auto-pricing
    
    # Conditions
    apply_to_all_customers = fields.Boolean(string='Apply to All Customers', default=True)
    customer_ids = fields.Many2many('res.partner', string='Specific Customers')
    
    # Execution
    last_execution = fields.Datetime(string='Last Execution', readonly=True)
    next_execution = fields.Datetime(string='Next Execution', readonly=True)
