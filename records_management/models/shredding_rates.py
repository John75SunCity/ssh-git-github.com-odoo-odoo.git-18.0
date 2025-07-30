# -*- coding: utf-8 -*-
"""
Comprehensive Rate Management System
Base rates, customer-specific rates, and rate calculation engine
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class BaseRates(models.Model):
    """
    Base Rates - Default pricing for all services
    These are the standard rates that apply to customers unless they have negotiated rates
    """

    _name = "base.rates"
    _description = "Base Service Rates"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "service_category, name"

    # Core identification
    name = fields.Char(string="Rate Name", required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(default=True)

    # Service categorization
    service_category = fields.Selection(
        [
            ("records", "Records Management"),
            ("shredding", "Shredding Services"),
            ("container", "Container Storage"),
            ("pickup", "Pickup & Delivery"),
            ("scanning", "Document Scanning"),
            ("special", "Special Services"),
        ],
        string="Service Category",
        required=True,
        tracking=True,
    )

    service_type = fields.Selection(
        [
            # Records Management
            ("monthly_storage", "Monthly Storage Fee"),
            ("retrieval", "Document Retrieval"),
            ("refile", "Document Refiling"),
            ("permanent_withdrawal", "Permanent Withdrawal"),
            # Shredding Services
            ("onsite_shredding", "On-site Shredding"),
            ("offsite_shredding", "Off-site Shredding"),
            ("hard_drive_destruction", "Hard Drive Destruction"),
            ("certificate_fee", "Destruction Certificate"),
            # Container Types
            ("standard_container", "Standard Container"),
            ("map_container", "Map Container"),
            ("oversize_container", "Oversize Container"),
            ("specialty_container", "Specialty Container"),
            # Pickup & Delivery
            ("scheduled_pickup", "Scheduled Pickup"),
            ("emergency_pickup", "Emergency Pickup"),
            ("delivery_fee", "Delivery Fee"),
            # Scanning Services
            ("document_scanning", "Document Scanning"),
            ("index_creation", "Index Creation"),
            # Special Services
            ("consultation", "Consultation Services"),
            ("training", "Training Services"),
            ("custom_service", "Custom Service"),
        ],
        string="Service Type",
        required=True,
        tracking=True,
    )

    # Pricing structure
    rate_structure = fields.Selection(
        [
            ("per_unit", "Per Unit"),
            ("per_pound", "Per Pound"),
            ("per_hour", "Per Hour"),
            ("per_container", "Per Container"),
            ("per_page", "Per Page"),
            ("flat_fee", "Flat Fee"),
        ],
        string="Rate Structure",
        required=True,
        tracking=True,
    )

    base_rate = fields.Float(
        string="Base Rate ($)",
        required=True,
        tracking=True,
        help="Base rate amount in dollars",
    )
    minimum_charge = fields.Float(
        string="Minimum Charge ($)",
        tracking=True,
        help="Minimum charge for this service",
    )

    # Effective dates
    effective_date = fields.Date(
        string="Effective Date", default=fields.Date.today, required=True, tracking=True
    )
    expiration_date = fields.Date(string="Expiration Date", tracking=True)

    # Rate management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("superseded", "Superseded"),
            ("expired", "Expired"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Additional details
    description = fields.Text(string="Description")
    notes = fields.Text(string="Internal Notes")

    # Computed fields
    customer_count = fields.Integer(
        string="Customers Using Base Rate", compute="_compute_customer_count"
    )
    negotiated_rate_count = fields.Integer(
        string="Customers with Negotiated Rates",
        compute="_compute_negotiated_rate_count",
    )

    @api.depends("service_category", "service_type")
    def _compute_customer_count(self):
        """Count customers using base rates for this service"""
        for record in self:
            # Count customers without negotiated rates for this service
            customer_rates = self.env["customer.rate.profile"].search(
                [
                    ("service_category", "=", record.service_category),
                    ("service_type", "=", record.service_type),
                    ("active", "=", True),
                ]
            )
            negotiated_customers = customer_rates.mapped("partner_id.id")

            total_customers = self.env["res.partner"].search_count(
                [("customer_rank", ">", 0), ("id", "not in", negotiated_customers)]
            )
            record.customer_count = total_customers

    @api.depends("service_category", "service_type")
    def _compute_negotiated_rate_count(self):
        """Count customers with negotiated rates for this service"""
        for record in self:
            record.negotiated_rate_count = self.env[
                "customer.rate.profile"
            ].search_count(
                [
                    ("service_category", "=", record.service_category),
                    ("service_type", "=", record.service_type),
                    ("active", "=", True),
                ]
            )

    def action_activate(self):
        """Activate this rate and supersede previous active rates"""
        self.ensure_one()
        if self.state != "draft":
            raise ValidationError(_("Only draft rates can be activated"))

        # Supersede existing active rates for the same service
        existing_active = self.search(
            [
                ("service_category", "=", self.service_category),
                ("service_type", "=", self.service_type),
                ("state", "=", "active"),
                ("id", "!=", self.id),
            ]
        )
        existing_active.write({"state": "superseded"})

        self.write({"state": "active"})
        self.message_post(body=_("Rate activated and previous rates superseded"))

    def action_expire(self):
        """Expire this rate"""
        self.ensure_one()
        self.write({"state": "expired", "expiration_date": fields.Date.today()})
        self.message_post(body=_("Rate expired"))

    @api.model
    def get_active_rate(self, service_category, service_type):
        """Get the currently active base rate for a service"""
        return self.search(
            [
                ("service_category", "=", service_category),
                ("service_type", "=", service_type),
                ("state", "=", "active"),
                ("effective_date", "<=", fields.Date.today()),
                "|",
                ("expiration_date", "=", False),
                ("expiration_date", ">=", fields.Date.today()),
            ],
            limit=1,
        )


class CustomerRateProfileExtension(models.Model):
    """
    Extension for Customer Rate Profiles - Add shredding-specific fields
    This extends the base customer.rate.profile model with additional functionality
    """

    _inherit = "customer.rate.profile"

    # Service matching (matches base rates)
    service_category = fields.Selection(
        [
            ("records", "Records Management"),
            ("shredding", "Shredding Services"),
            ("container", "Container Storage"),
            ("pickup", "Pickup & Delivery"),
            ("scanning", "Document Scanning"),
            ("special", "Special Services"),
        ],
        string="Service Category",
        required=True,
        tracking=True,
    )

    service_type = fields.Selection(
        [
            # Records Management
            ("monthly_storage", "Monthly Storage Fee"),
            ("retrieval", "Document Retrieval"),
            ("refile", "Document Refiling"),
            ("permanent_withdrawal", "Permanent Withdrawal"),
            # Shredding Services
            ("onsite_shredding", "On-site Shredding"),
            ("offsite_shredding", "Off-site Shredding"),
            ("hard_drive_destruction", "Hard Drive Destruction"),
            ("certificate_fee", "Destruction Certificate"),
            # Container Types
            ("standard_container", "Standard Container"),
            ("map_container", "Map Container"),
            ("oversize_container", "Oversize Container"),
            ("specialty_container", "Specialty Container"),
            # Pickup & Delivery
            ("scheduled_pickup", "Scheduled Pickup"),
            ("emergency_pickup", "Emergency Pickup"),
            ("delivery_fee", "Delivery Fee"),
            # Scanning Services
            ("document_scanning", "Document Scanning"),
            ("index_creation", "Index Creation"),
            # Special Services
            ("consultation", "Consultation Services"),
            ("training", "Training Services"),
            ("custom_service", "Custom Service"),
        ],
        string="Service Type",
        required=True,
        tracking=True,
    )

    # Base rate reference
    base_rate_id = fields.Many2one(
        "base.rates",
        string="Base Rate",
        domain="[('service_category', '=', service_category), ('service_type', '=', service_type), ('state', '=', 'active')]",
        tracking=True,
    )
    base_rate_amount = fields.Float(
        string="Base Rate Amount", related="base_rate_id.base_rate", readonly=True
    )

    # Rate adjustment methods
    adjustment_method = fields.Selection(
        [
            ("percentage_discount", "Percentage Discount"),
            ("percentage_markup", "Percentage Markup"),
            ("fixed_discount", "Fixed Dollar Discount"),
            ("fixed_markup", "Fixed Dollar Markup"),
            ("fixed_rate", "Fixed Rate Override"),
        ],
        string="Adjustment Method",
        required=True,
        tracking=True,
    )

    adjustment_value = fields.Float(
        string="Adjustment Value",
        required=True,
        tracking=True,
        help="Percentage (without % sign) or dollar amount depending on adjustment method",
    )

    # Calculated rate
    negotiated_rate = fields.Float(
        string="Negotiated Rate ($)",
        compute="_compute_negotiated_rate",
        store=True,
        tracking=True,
    )
    rate_difference = fields.Float(
        string="Difference from Base ($)",
        compute="_compute_rate_difference",
        store=True,
    )
    savings_percentage = fields.Float(
        string="Savings %", compute="_compute_savings_percentage", store=True
    )

    # Effective dates and contract info
    effective_date = fields.Date(
        string="Effective Date", default=fields.Date.today, required=True, tracking=True
    )
    expiration_date = fields.Date(string="Expiration Date", tracking=True)
    contract_reference = fields.Char(string="Contract Reference", tracking=True)

    # Rate management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("expired", "Expired"),
            ("superseded", "Superseded"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Additional details
    notes = fields.Text(string="Negotiation Notes")
    approved_by = fields.Many2one("res.users", string="Approved By", tracking=True)
    approval_date = fields.Date(string="Approval Date", tracking=True)

    @api.depends("partner_id", "service_category", "service_type", "profile_type")
    def _compute_name(self):
        """Generate profile name - Extended version with service details"""
        for record in self:
            if record.partner_id:
                name_parts = [record.partner_id.name]

                # Add profile type if available
                if hasattr(record, "profile_type") and record.profile_type:
                    name_parts.append(record.profile_type.title())

                # Add service details if available
                if record.service_category and record.service_type:
                    service_name = dict(record._fields["service_type"].selection).get(
                        record.service_type, record.service_type
                    )
                    name_parts.append(service_name)

                record.name = " - ".join(name_parts)
            else:
                record.name = "New Rate Profile"

    @api.depends("base_rate_amount", "adjustment_method", "adjustment_value")
    def _compute_negotiated_rate(self):
        """Calculate negotiated rate based on adjustment method"""
        for record in self:
            if not record.base_rate_amount:
                record.negotiated_rate = 0.0
                continue

            base = record.base_rate_amount
            adjustment = record.adjustment_value

            if record.adjustment_method == "percentage_discount":
                record.negotiated_rate = base * (1 - adjustment / 100)
            elif record.adjustment_method == "percentage_markup":
                record.negotiated_rate = base * (1 + adjustment / 100)
            elif record.adjustment_method == "fixed_discount":
                record.negotiated_rate = max(0, base - adjustment)
            elif record.adjustment_method == "fixed_markup":
                record.negotiated_rate = base + adjustment
            elif record.adjustment_method == "fixed_rate":
                record.negotiated_rate = adjustment
            else:
                record.negotiated_rate = base

    @api.depends("base_rate_amount", "negotiated_rate")
    def _compute_rate_difference(self):
        """Calculate difference from base rate"""
        for record in self:
            record.rate_difference = record.negotiated_rate - record.base_rate_amount

    @api.depends("base_rate_amount", "negotiated_rate")
    def _compute_savings_percentage(self):
        """Calculate savings percentage"""
        for record in self:
            if record.base_rate_amount:
                record.savings_percentage = (
                    (record.base_rate_amount - record.negotiated_rate)
                    / record.base_rate_amount
                ) * 100
            else:
                record.savings_percentage = 0.0

    def action_activate(self):
        """Activate this rate profile"""
        self.ensure_one()
        if self.state != "draft":
            raise ValidationError(_("Only draft rate profiles can be activated"))

        if not self.approved_by:
            raise ValidationError(_("Rate profile must be approved before activation"))

        # Supersede existing active profiles for same customer/service
        existing = self.search(
            [
                ("partner_id", "=", self.partner_id.id),
                ("service_category", "=", self.service_category),
                ("service_type", "=", self.service_type),
                ("state", "=", "active"),
                ("id", "!=", self.id),
            ]
        )
        existing.write({"state": "superseded"})

        self.write({"state": "active"})
        self.message_post(body=_("Rate profile activated"))

    def action_approve(self):
        """Approve this rate profile"""
        self.ensure_one()
        self.write(
            {"approved_by": self.env.user.id, "approval_date": fields.Date.today()}
        )
        self.message_post(body=_("Rate profile approved by %s") % self.env.user.name)

    @api.model
    def get_customer_rate(self, partner_id, service_category, service_type):
        """Get the customer's rate for a specific service (negotiated or base)"""
        # First check for active negotiated rate
        negotiated_rate = self.search(
            [
                ("partner_id", "=", partner_id),
                ("service_category", "=", service_category),
                ("service_type", "=", service_type),
                ("state", "=", "active"),
                ("effective_date", "<=", fields.Date.today()),
                "|",
                ("expiration_date", "=", False),
                ("expiration_date", ">=", fields.Date.today()),
            ],
            limit=1,
        )

        if negotiated_rate:
            return negotiated_rate.negotiated_rate, "negotiated"

        # Fall back to base rate
        base_rate = self.env["base.rates"].get_active_rate(
            service_category, service_type
        )
        if base_rate:
            return base_rate.base_rate, "base"

        return 0.0, "none"

    @api.constrains("adjustment_value")
    def _check_adjustment_value(self):
        """Validate adjustment values"""
        for record in self:
            if record.adjustment_method in ["percentage_discount", "percentage_markup"]:
                if record.adjustment_value < 0 or record.adjustment_value > 100:
                    raise ValidationError(
                        _("Percentage values must be between 0 and 100")
                    )
            elif record.adjustment_method in [
                "fixed_discount",
                "fixed_markup",
                "fixed_rate",
            ]:
                if record.adjustment_value < 0:
                    raise ValidationError(_("Rate values cannot be negative"))


class RateAnalysis(models.TransientModel):
    """
    Rate Analysis Wizard - Compare base rates vs negotiated rates
    """

    _name = "rate.analysis.wizard"
    _description = "Rate Analysis and Comparison"

    # Analysis parameters
    service_category = fields.Selection(
        [
            ("records", "Records Management"),
            ("shredding", "Shredding Services"),
            ("container", "Container Storage"),
            ("pickup", "Pickup & Delivery"),
            ("scanning", "Document Scanning"),
            ("special", "Special Services"),
        ],
        string="Service Category",
    )

    customer_filter = fields.Selection(
        [
            ("all", "All Customers"),
            ("base_rates", "Customers Using Base Rates"),
            ("negotiated_rates", "Customers with Negotiated Rates"),
            ("specific_customer", "Specific Customer"),
        ],
        string="Customer Filter",
        default="all",
    )

    specific_customer_id = fields.Many2one(
        "res.partner", string="Specific Customer", domain=[("customer_rank", ">", 0)]
    )

    def action_generate_analysis(self):
        """Generate comprehensive rate analysis"""
        self.ensure_one()

        # This would generate a detailed report showing:
        # - Base rates vs negotiated rates
        # - Savings by customer
        # - Rate distribution analysis
        # - Revenue impact analysis

        return {
            "type": "ir.actions.act_window",
            "name": "Rate Analysis Report",
            "res_model": "rate.analysis.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_analysis_complete": True},
        }


class RevenueForecaster(models.TransientModel):
    """
    Revenue Forecasting & Rate Impact Analysis Tool
    Analyze potential revenue changes from rate adjustments
    """

    _name = "revenue.forecaster"
    _description = "Revenue Forecasting & Rate Impact Analysis"

    # Forecasting parameters
    name = fields.Char(string="Forecast Name", compute="_compute_name", store=True)
    forecast_period = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annual", "Semi-Annual"),
            ("annual", "Annual"),
            ("custom", "Custom Period"),
        ],
        string="Forecast Period",
        default="annual",
        required=True,
    )

    # Custom period dates
    custom_start_date = fields.Date(string="Custom Start Date")
    custom_end_date = fields.Date(string="Custom End Date")

    # Rate adjustment scenarios
    scenario_type = fields.Selection(
        [
            ("global_increase", "Global Rate Increase"),
            ("global_decrease", "Global Rate Decrease"),
            ("category_specific", "Category-Specific Adjustment"),
            ("customer_specific", "Customer-Specific Adjustment"),
            ("competitive_analysis", "Competitive Positioning"),
            ("what_if", "What-If Scenario"),
        ],
        string="Scenario Type",
        default="global_increase",
        required=True,
    )

    # Global adjustment parameters
    global_adjustment_type = fields.Selection(
        [("percentage", "Percentage Change"), ("fixed_amount", "Fixed Dollar Amount")],
        string="Adjustment Type",
        default="percentage",
    )

    global_adjustment_value = fields.Float(
        string="Adjustment Value", help="Percentage (without % sign) or dollar amount"
    )

    # Category-specific adjustments
    service_category = fields.Selection(
        [
            ("records", "Records Management"),
            ("shredding", "Shredding Services"),
            ("container", "Container Storage"),
            ("pickup", "Pickup & Delivery"),
            ("scanning", "Document Scanning"),
            ("special", "Special Services"),
        ],
        string="Target Service Category",
    )

    category_adjustment_value = fields.Float(string="Category Adjustment Value")

    # Customer filters
    customer_segment = fields.Selection(
        [
            ("all", "All Customers"),
            ("high_volume", "High Volume (>100 containers)"),
            ("medium_volume", "Medium Volume (20-100 containers)"),
            ("low_volume", "Low Volume (<20 containers)"),
            ("negotiated_rates", "Customers with Negotiated Rates"),
            ("base_rates", "Customers on Base Rates"),
            ("specific_customers", "Selected Customers"),
        ],
        string="Customer Segment",
        default="all",
    )

    specific_customer_ids = fields.Many2many(
        "res.partner", string="Specific Customers", domain=[("customer_rank", ">", 0)]
    )

    # Market analysis parameters
    market_growth_rate = fields.Float(
        string="Expected Market Growth (%)",
        default=3.0,
        help="Annual market growth percentage",
    )
    inflation_rate = fields.Float(
        string="Inflation Rate (%)", default=2.5, help="Expected inflation rate"
    )
    customer_retention_rate = fields.Float(
        string="Customer Retention Rate (%)",
        default=95.0,
        help="Expected customer retention rate with new rates",
    )

    # Competitive positioning
    competitor_rate_factor = fields.Float(
        string="Competitor Rate Factor",
        default=1.0,
        help="Multiplier vs competitor rates (1.0 = same, 1.1 = 10% higher)",
    )

    # Results (computed after analysis)
    current_monthly_revenue = fields.Float(
        string="Current Monthly Revenue ($)", readonly=True
    )
    projected_monthly_revenue = fields.Float(
        string="Projected Monthly Revenue ($)", readonly=True
    )
    revenue_difference = fields.Float(
        string="Monthly Revenue Change ($)", readonly=True
    )
    revenue_percentage_change = fields.Float(string="Revenue Change (%)", readonly=True)

    annual_revenue_impact = fields.Float(
        string="Annual Revenue Impact ($)", readonly=True
    )
    customer_impact_count = fields.Integer(string="Customers Affected", readonly=True)
    risk_assessment = fields.Selection(
        [
            ("low", "Low Risk"),
            ("medium", "Medium Risk"),
            ("high", "High Risk"),
            ("very_high", "Very High Risk"),
        ],
        string="Risk Assessment",
        readonly=True,
    )

    # Detailed analysis results
    forecast_line_ids = fields.One2many(
        "revenue.forecast.line",
        "forecast_id",
        string="Detailed Forecast Lines",
        readonly=True,
    )

    # Analysis status
    analysis_complete = fields.Boolean(string="Analysis Complete", default=False)
    analysis_date = fields.Datetime(string="Analysis Date", readonly=True)

    @api.depends("scenario_type", "forecast_period")
    def _compute_name(self):
        """Generate forecast name"""
        for record in self:
            scenario_name = dict(record._fields["scenario_type"].selection).get(
                record.scenario_type, "Forecast"
            )
            period_name = dict(record._fields["forecast_period"].selection).get(
                record.forecast_period, "Analysis"
            )
            record.name = f"{scenario_name} - {period_name}"

    def action_run_forecast(self):
        """Run the revenue forecast analysis"""
        self.ensure_one()

        # Clear previous results
        self.forecast_line_ids.unlink()

        # Get current revenue baseline
        self._calculate_current_revenue()

        # Run scenario analysis
        if self.scenario_type == "global_increase":
            self._analyze_global_increase()
        elif self.scenario_type == "global_decrease":
            self._analyze_global_decrease()
        elif self.scenario_type == "category_specific":
            self._analyze_category_specific()
        elif self.scenario_type == "customer_specific":
            self._analyze_customer_specific()
        elif self.scenario_type == "competitive_analysis":
            self._analyze_competitive_positioning()
        elif self.scenario_type == "what_if":
            self._analyze_what_if_scenario()

        # Calculate risk assessment
        self._calculate_risk_assessment()

        # Mark analysis as complete
        self.write({"analysis_complete": True, "analysis_date": fields.Datetime.now()})

        return self._show_results()

    def _calculate_current_revenue(self):
        """Calculate current monthly revenue baseline"""
        # This would analyze current billing to establish baseline
        # For now, we'll simulate with sample data

        # Get all active customers and their current rates
        customers = self._get_target_customers()
        total_monthly = 0.0

        for customer in customers:
            # Calculate customer's monthly spend based on current rates
            customer_monthly = self._calculate_customer_monthly_revenue(customer)
            total_monthly += customer_monthly

        self.current_monthly_revenue = total_monthly
        self.customer_impact_count = len(customers)

    def _get_target_customers(self):
        """Get customers affected by this scenario"""
        domain = [("customer_rank", ">", 0)]

        if self.customer_segment == "high_volume":
            # Customers with >100 containers
            domain.append(("container_count", ">", 100))
        elif self.customer_segment == "medium_volume":
            domain.extend(
                [("container_count", ">=", 20), ("container_count", "<=", 100)]
            )
        elif self.customer_segment == "low_volume":
            domain.append(("container_count", "<", 20))
        elif self.customer_segment == "specific_customers":
            domain.append(("id", "in", self.specific_customer_ids.ids))
        elif self.customer_segment == "negotiated_rates":
            # Customers with active negotiated rates
            negotiated_customers = (
                self.env["customer.rate.profile"]
                .search([("state", "=", "active")])
                .mapped("partner_id.id")
            )
            domain.append(("id", "in", negotiated_customers))
        elif self.customer_segment == "base_rates":
            # Customers without negotiated rates
            negotiated_customers = (
                self.env["customer.rate.profile"]
                .search([("state", "=", "active")])
                .mapped("partner_id.id")
            )
            domain.append(("id", "not in", negotiated_customers))

        return self.env["res.partner"].search(domain)

    def _calculate_customer_monthly_revenue(self, customer):
        """Calculate a customer's current monthly revenue"""
        # This would analyze actual billing data
        # For simulation, we'll use container count and average rates

        container_count = getattr(
            customer, "container_count", 50
        )  # Default 50 containers

        # Get customer's rates or base rates
        storage_rate, rate_type = self.env["customer.rate.profile"].get_customer_rate(
            customer.id, "container", "standard_container"
        )

        if not storage_rate:
            storage_rate = 0.32  # Default $0.32/month per container

        return container_count * storage_rate

    def _analyze_global_increase(self):
        """Analyze global rate increase scenario"""
        customers = self._get_target_customers()
        total_new_revenue = 0.0

        for customer in customers:
            current_monthly = self._calculate_customer_monthly_revenue(customer)

            if self.global_adjustment_type == "percentage":
                new_monthly = current_monthly * (1 + self.global_adjustment_value / 100)
            else:
                new_monthly = current_monthly + self.global_adjustment_value

            # Apply retention rate
            retention_factor = self.customer_retention_rate / 100
            adjusted_revenue = new_monthly * retention_factor

            total_new_revenue += adjusted_revenue

            # Create detailed forecast line
            self._create_forecast_line(customer, current_monthly, adjusted_revenue)

        self.projected_monthly_revenue = total_new_revenue
        self._calculate_revenue_changes()

    def _analyze_global_decrease(self):
        """Analyze global rate decrease scenario"""
        customers = self._get_target_customers()
        total_new_revenue = 0.0

        for customer in customers:
            current_monthly = self._calculate_customer_monthly_revenue(customer)

            if self.global_adjustment_type == "percentage":
                new_monthly = current_monthly * (1 - self.global_adjustment_value / 100)
            else:
                new_monthly = max(0, current_monthly - self.global_adjustment_value)

            # Rate decreases might improve retention and attract new business
            growth_factor = 1 + (self.market_growth_rate / 100 / 12)  # Monthly growth
            adjusted_revenue = new_monthly * growth_factor

            total_new_revenue += adjusted_revenue

            self._create_forecast_line(customer, current_monthly, adjusted_revenue)

        self.projected_monthly_revenue = total_new_revenue
        self._calculate_revenue_changes()

    def _analyze_category_specific(self):
        """Analyze category-specific rate changes"""
        customers = self._get_target_customers()
        total_new_revenue = 0.0

        for customer in customers:
            current_monthly = self._calculate_customer_monthly_revenue(customer)

            # Only adjust rates for the specific service category
            if self.service_category:
                category_revenue = (
                    current_monthly * 0.3
                )  # Assume 30% from this category
                other_revenue = current_monthly * 0.7

                adjusted_category_revenue = category_revenue * (
                    1 + self.category_adjustment_value / 100
                )
                new_monthly = adjusted_category_revenue + other_revenue
            else:
                new_monthly = current_monthly

            total_new_revenue += new_monthly
            self._create_forecast_line(customer, current_monthly, new_monthly)

        self.projected_monthly_revenue = total_new_revenue
        self._calculate_revenue_changes()

    def _analyze_customer_specific(self):
        """Analyze customer-specific rate changes"""
        customers = self._get_target_customers()
        total_new_revenue = 0.0

        for customer in customers:
            current_monthly = self._calculate_customer_monthly_revenue(customer)

            # Apply different adjustments based on customer segment
            if customer.id in self.specific_customer_ids.ids:
                adjustment = self.global_adjustment_value
                new_monthly = current_monthly * (1 + adjustment / 100)
            else:
                new_monthly = current_monthly

            total_new_revenue += new_monthly
            self._create_forecast_line(customer, current_monthly, new_monthly)

        self.projected_monthly_revenue = total_new_revenue
        self._calculate_revenue_changes()

    def _analyze_competitive_positioning(self):
        """Analyze competitive positioning scenario"""
        customers = self._get_target_customers()
        total_new_revenue = 0.0

        # Market research: competitor rates
        competitor_base_rate = 0.30  # Example competitor rate
        our_target_rate = competitor_base_rate * self.competitor_rate_factor

        for customer in customers:
            current_monthly = self._calculate_customer_monthly_revenue(customer)
            container_count = getattr(customer, "container_count", 50)

            new_monthly = container_count * our_target_rate

            # Apply market dynamics
            if self.competitor_rate_factor > 1.1:  # 10% higher than competitors
                retention_impact = 0.95  # 5% customer loss risk
            elif self.competitor_rate_factor < 0.9:  # 10% lower than competitors
                retention_impact = 1.05  # 5% customer gain potential
            else:
                retention_impact = 1.0

            adjusted_revenue = new_monthly * retention_impact
            total_new_revenue += adjusted_revenue

            self._create_forecast_line(customer, current_monthly, adjusted_revenue)

        self.projected_monthly_revenue = total_new_revenue
        self._calculate_revenue_changes()

    def _analyze_what_if_scenario(self):
        """Analyze custom what-if scenario"""
        # This allows for complex custom scenarios
        self._analyze_global_increase()  # Default to global increase logic

    def _calculate_revenue_changes(self):
        """Calculate revenue change metrics"""
        self.revenue_difference = (
            self.projected_monthly_revenue - self.current_monthly_revenue
        )

        if self.current_monthly_revenue:
            self.revenue_percentage_change = (
                self.revenue_difference / self.current_monthly_revenue
            ) * 100
        else:
            self.revenue_percentage_change = 0.0

        # Calculate annual impact
        if self.forecast_period == "monthly":
            annual_multiplier = 12
        elif self.forecast_period == "quarterly":
            annual_multiplier = 4
        elif self.forecast_period == "semi_annual":
            annual_multiplier = 2
        else:
            annual_multiplier = 1

        self.annual_revenue_impact = self.revenue_difference * annual_multiplier

    def _calculate_risk_assessment(self):
        """Calculate risk assessment based on various factors"""
        risk_score = 0

        # Rate change magnitude
        if abs(self.revenue_percentage_change) > 20:
            risk_score += 3
        elif abs(self.revenue_percentage_change) > 10:
            risk_score += 2
        elif abs(self.revenue_percentage_change) > 5:
            risk_score += 1

        # Customer retention risk
        if self.customer_retention_rate < 90:
            risk_score += 3
        elif self.customer_retention_rate < 95:
            risk_score += 2
        elif self.customer_retention_rate < 98:
            risk_score += 1

        # Competitive positioning risk
        if self.competitor_rate_factor > 1.2:
            risk_score += 3
        elif self.competitor_rate_factor > 1.1:
            risk_score += 2
        elif self.competitor_rate_factor > 1.05:
            risk_score += 1

        # Set risk assessment
        if risk_score >= 7:
            self.risk_assessment = "very_high"
        elif risk_score >= 5:
            self.risk_assessment = "high"
        elif risk_score >= 3:
            self.risk_assessment = "medium"
        else:
            self.risk_assessment = "low"

    def _create_forecast_line(self, customer, current_revenue, projected_revenue):
        """Create detailed forecast line for a customer"""
        self.env["revenue.forecast.line"].create(
            {
                "forecast_id": self.id,
                "partner_id": customer.id,
                "current_monthly_revenue": current_revenue,
                "projected_monthly_revenue": projected_revenue,
                "revenue_change": projected_revenue - current_revenue,
                "revenue_change_percentage": (
                    ((projected_revenue - current_revenue) / current_revenue * 100)
                    if current_revenue
                    else 0
                ),
            }
        )

    def _show_results(self):
        """Show forecast results"""
        return {
            "type": "ir.actions.act_window",
            "name": "Revenue Forecast Results",
            "res_model": "revenue.forecaster",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": {"default_analysis_complete": True},
        }

    def action_export_forecast(self):
        """Export forecast to Excel"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model={self._name}&id={self.id}&field=forecast_file&download=true&filename=revenue_forecast.xlsx",
            "target": "self",
        }

    def action_apply_scenario(self):
        """Apply this scenario to actual rates (with confirmation)"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Apply Rate Changes",
            "res_model": "rate.change.confirmation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_forecast_id": self.id,
                "default_revenue_impact": self.annual_revenue_impact,
                "default_customer_count": self.customer_impact_count,
            },
        }


class RevenueForecastLine(models.TransientModel):
    """
    Detailed forecast line for individual customers
    """

    _name = "revenue.forecast.line"
    _description = "Revenue Forecast Line"
    _order = "revenue_change desc"

    forecast_id = fields.Many2one(
        "revenue.forecaster", string="Forecast", required=True, ondelete="cascade"
    )
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)

    current_monthly_revenue = fields.Float(string="Current Monthly Revenue ($)")
    projected_monthly_revenue = fields.Float(string="Projected Monthly Revenue ($)")
    revenue_change = fields.Float(string="Revenue Change ($)")
    revenue_change_percentage = fields.Float(string="Change (%)")

    # Customer details
    container_count = fields.Integer(
        string="Container Count", related="partner_id.container_count", readonly=True
    )
    customer_segment = fields.Char(
        string="Customer Segment", compute="_compute_customer_segment"
    )
    risk_level = fields.Selection(
        [("low", "Low Risk"), ("medium", "Medium Risk"), ("high", "High Risk")],
        string="Retention Risk",
        compute="_compute_risk_level",
    )

    @api.depends("partner_id")
    def _compute_customer_segment(self):
        """Determine customer segment"""
        for record in self:
            container_count = record.container_count or 0
            if container_count > 100:
                record.customer_segment = "High Volume"
            elif container_count >= 20:
                record.customer_segment = "Medium Volume"
            else:
                record.customer_segment = "Low Volume"

    @api.depends("revenue_change_percentage")
    def _compute_risk_level(self):
        """Assess customer retention risk"""
        for record in self:
            if record.revenue_change_percentage > 15:
                record.risk_level = "high"
            elif record.revenue_change_percentage > 7:
                record.risk_level = "medium"
            else:
                record.risk_level = "low"


# Legacy compatibility models (maintain existing XML references)
class ShreddingBaseRates(models.Model):
    """Legacy model - redirects to base.rates with shredding category"""

    _name = "shredding.base.rates"
    _description = "Shredding Base Rates (Legacy)"
    _inherit = "base.rates"

    # Legacy fields for backward compatibility with existing views
    external_per_bin_rate = fields.Float(string="External Per Bin Rate", default=0.0)
    external_service_call_rate = fields.Float(
        string="External Service Call Rate", default=0.0
    )
    managed_retrieval_rate = fields.Float(string="Managed Retrieval Rate", default=0.0)
    managed_shredding_rate = fields.Float(string="Managed Shredding Rate", default=0.0)
    managed_service_call_rate = fields.Float(
        string="Managed Service Call Rate", default=0.0
    )
    managed_permanent_removal_rate = fields.Float(
        string="Managed Permanent Removal Rate", default=0.0
    )

    # Customization flags
    use_custom_external_rates = fields.Boolean(
        string="Use Custom External Rates", default=False
    )
    use_custom_managed_rates = fields.Boolean(
        string="Use Custom Managed Rates", default=False
    )

    # Discount options
    discount_percentage = fields.Float(string="Discount Percentage", default=0.0)

    # Validity period
    effective_date = fields.Date(string="Effective Date", default=fields.Date.today)
    expiry_date = fields.Date(string="Expiry Date")

    # Pricing type
    type = fields.Selection(
        [
            ("external", "External Shredding"),
            ("managed", "Managed Shredding"),
            ("mixed", "Mixed Services"),
        ],
        string="Rate Type",
        default="external",
    )

    def create(self, vals):
        """Override to set service category to shredding"""
        vals["service_category"] = "shredding"
        return super().create(vals)


class ShreddingCustomerRates(models.Model):
    """Legacy model - redirects to customer.rate.profile with shredding category"""

    _name = "shredding.customer.rates"
    _description = "Shredding Customer Rates (Legacy)"
    _inherit = "customer.rate.profile"

    def create(self, vals):
        """Override to set service category to shredding"""
        vals["service_category"] = "shredding"
        return super().create(vals)
