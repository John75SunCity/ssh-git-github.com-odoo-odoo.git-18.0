# -*- coding: utf-8 -*-
"""
Product Template Extension for Records Management

This module extends the product.template model to integrate Records Management
container specifications, service offerings, and billing configurations.
Supports the actual business container types used in operations.

Key Features:
- Container type specifications (TYPE 01-06) with actual business dimensions
- Service product definitions for shredding, storage, and retrieval
- Integration with Records Management billing system
- NAID compliance tracking for destruction services

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
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
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # CONTAINER SPECIFICATIONS
    # ============================================================================
    is_records_container = fields.Boolean(
        string="Records Container",
        default=False,
        help="Whether this product is a records management container",
    )
    container_type = fields.Selection(
        [
            ("type_01", "TYPE 01: Standard Box (1.2 CF)"),
            ("type_02", "TYPE 02: Legal/Banker Box (2.4 CF)"),
            ("type_03", "TYPE 03: Map Box (0.875 CF)"),
            ("type_04", "TYPE 04: Odd Size/Temp Box (5.0 CF)"),
            ("type_06", "TYPE 06: Pathology Box (0.042 CF)"),
        ],
        string="Container Type",
        help="Business container type specification",
    )
    container_volume_cf = fields.Float(
        string="Container Volume (Cubic Feet)",
        digits=(12, 3),
        help="Container volume in cubic feet for capacity planning",
    )
    container_weight_lbs = fields.Float(
        string="Container Weight (lbs)",
        help="Average container weight in pounds",
    )
    container_dimensions = fields.Char(
        string="Container Dimensions",
        help="Physical dimensions of the container",
    )

    # ============================================================================
    # SERVICE CONFIGURATION
    # ============================================================================
    is_template_service = fields.Boolean(
        string="Template Service",
        default=False,
        help="Whether this is a records management service template",
    )
    is_featured_service = fields.Boolean(
        string="Featured Service",
        default=False,
        help="Whether this service is featured in customer portal",
    )
    template_category = fields.Selection(
        [
            ("storage", "Document Storage"),
            ("retrieval", "Document Retrieval"),
            ("destruction", "Secure Destruction"),
            ("digital", "Digital Services"),
            ("compliance", "Compliance Services"),
            ("consultation", "Consultation Services"),
        ],
        string="Template Category",
        help="Category of records management service",
    )

    # ============================================================================
    # EXTERNAL INTEGRATION
    # ============================================================================
    external_service_id = fields.Char(
        string="External Service ID", help="External system service identifier"
    )
    sync_enabled = fields.Boolean(
        string="Sync Enabled",
        default=True,
        help="Enable synchronization with external systems",
    )
    api_integration = fields.Boolean(
        string="API Integration",
        default=False,
        help="Enable API integration for this service",
    )
    webhook_notifications = fields.Boolean(
        string="Webhook Notifications",
        default=False,
        help="Enable webhook notifications for service events",
    )

    # ============================================================================
    # SERVICE SPECIFICATIONS
    # ============================================================================
    service_duration = fields.Float(
        string="Service Duration (hours)",
        help="Expected duration for service completion",
    )
    service_frequency = fields.Selection(
        [
            ("one_time", "One Time"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annual", "Annual"),
            ("on_demand", "On Demand"),
        ],
        string="Service Frequency",
        default="one_time",
        help="How frequently this service is typically required",
    )
    requires_appointment = fields.Boolean(
        string="Requires Appointment",
        default=False,
        help="Whether service requires scheduled appointment",
    )
    advance_notice_days = fields.Integer(
        string="Advance Notice (days)",
        default=1,
        help="Days of advance notice required for scheduling",
    )
    service_location = fields.Selection(
        [("onsite", "On-Site"), ("offsite", "Off-Site"), ("both", "Both")],
        string="Service Location",
        default="offsite",
        help="Where service can be performed",
    )

    # ============================================================================
    # COMPLIANCE & SECURITY
    # ============================================================================
    naid_compliant = fields.Boolean(
        string="NAID Compliant",
        default=False,
        help="Service meets NAID compliance standards",
    )
    hipaa_compliant = fields.Boolean(
        string="HIPAA Compliant",
        default=False,
        help="Service meets HIPAA compliance requirements",
    )
    sox_compliant = fields.Boolean(
        string="SOX Compliant",
        default=False,
        help="Service meets SOX compliance requirements",
    )
    iso_compliant = fields.Boolean(
        string="ISO Compliant",
        default=False,
        help="Service meets ISO compliance standards",
    )
    security_clearance_required = fields.Boolean(
        string="Security Clearance Required",
        default=False,
        help="Service requires security clearance",
    )
    encryption_level = fields.Selection(
        [
            ("none", "No Encryption"),
            ("basic", "Basic Encryption"),
            ("advanced", "Advanced Encryption"),
            ("military", "Military Grade"),
        ],
        string="Encryption Level",
        default="basic",
        help="Level of encryption provided",
    )

    # ============================================================================
    # CAPACITY & RESOURCE MANAGEMENT
    # ============================================================================
    max_concurrent_jobs = fields.Integer(
        string="Max Concurrent Jobs",
        default=1,
        help="Maximum number of concurrent jobs for this service",
    )
    staff_required = fields.Integer(
        string="Staff Required", default=1, help="Number of staff members required"
    )
    equipment_required = fields.Text(
        string="Equipment Required", help="Description of equipment needed for service"
    )
    vehicle_required = fields.Boolean(
        string="Vehicle Required", default=False, help="Service requires vehicle"
    )
    service_radius_miles = fields.Integer(
        string="Service Radius (miles)", help="Maximum service radius in miles"
    )

    # ============================================================================
    # PRICING & BILLING
    # ============================================================================
    pricing_model = fields.Selection(
        [
            ("fixed", "Fixed Price"),
            ("hourly", "Hourly Rate"),
            ("per_item", "Per Item"),
            ("per_box", "Per Box"),
            ("subscription", "Subscription"),
            ("volume", "Volume Discount"),
        ],
        string="Pricing Model",
        default="fixed",
        help="How this service is priced",
    )
    minimum_charge = fields.Float(
        string="Minimum Charge", help="Minimum charge for service"
    )
    setup_fee = fields.Float(string="Setup Fee", help="One-time setup fee")
    bulk_discount_threshold = fields.Integer(
        string="Bulk Discount Threshold", help="Minimum quantity for bulk discount"
    )
    bulk_discount_rate = fields.Float(
        string="Bulk Discount Rate (%)", help="Percentage discount for bulk orders"
    )
    subscription_period = fields.Selection(
        [("monthly", "Monthly"), ("quarterly", "Quarterly"), ("annual", "Annual")],
        string="Subscription Period",
        help="Billing period for subscription services",
    )

    # ============================================================================
    # SCHEDULING & AVAILABILITY
    # ============================================================================
    availability_monday = fields.Boolean(string="Available Monday", default=True)
    availability_tuesday = fields.Boolean(string="Available Tuesday", default=True)
    availability_wednesday = fields.Boolean(string="Available Wednesday", default=True)
    availability_thursday = fields.Boolean(string="Available Thursday", default=True)
    availability_friday = fields.Boolean(string="Available Friday", default=True)
    availability_saturday = fields.Boolean(string="Available Saturday", default=False)
    availability_sunday = fields.Boolean(string="Available Sunday", default=False)
    service_hours_start = fields.Float(
        string="Service Hours Start",
        default=8.0,
        help="Service start time (24-hour format)",
    )
    service_hours_end = fields.Float(
        string="Service Hours End",
        default=17.0,
        help="Service end time (24-hour format)",
    )
    emergency_service = fields.Boolean(
        string="Emergency Service Available",
        default=False,
        help="Service available for emergencies",
    )
    after_hours_available = fields.Boolean(
        string="After Hours Available",
        default=False,
        help="Service available after regular hours",
    )

    # ============================================================================
    # SLA & PERFORMANCE
    # ============================================================================
    sla_response_time = fields.Float(
        string="SLA Response Time (hours)", help="Service Level Agreement response time"
    )
    sla_completion_time = fields.Float(
        string="SLA Completion Time (hours)",
        help="Service Level Agreement completion time",
    )
    quality_standard = fields.Selection(
        [
            ("basic", "Basic Quality"),
            ("premium", "Premium Quality"),
            ("enterprise", "Enterprise Quality"),
        ],
        string="Quality Standard",
        default="basic",
        help="Quality standard for service delivery",
    )
    performance_guarantee = fields.Boolean(
        string="Performance Guarantee",
        default=False,
        help="Service comes with performance guarantee",
    )

    # ============================================================================
    # CUSTOMER EXPERIENCE
    # ============================================================================
    customer_rating = fields.Float(
        string="Customer Rating",
        compute="_compute_customer_rating",
        store=True,
        help="Average customer rating from feedback",
    )
    feedback_count = fields.Integer(
        string="Feedback Count",
        compute="_compute_feedback_count",
        help="Total number of customer feedback records",
    )
    popular_service = fields.Boolean(
        string="Popular Service",
        compute="_compute_popular_service",
        store=True,
        help="Service is marked as popular based on usage",
    )
    service_description_portal = fields.Html(
        string="Portal Description", help="Description shown to customers in portal"
    )
    service_benefits = fields.Html(
        string="Service Benefits", help="Benefits and features of this service"
    )

    detailed_type = fields.Selection([("consu", "Consumable"), ("service", "Service"), ("product", "Storable Product")], string="Product Type")
    list_price = fields.Float(string="Sales Price", digits="Product Price")
    standard_price = fields.Float(string="Cost", digits="Product Price")
    categ_id = fields.Many2one("product.category", string="Product Category")
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure")
    uom_po_id = fields.Many2one("uom.uom", string="Purchase Unit of Measure")
    sale_ok = fields.Boolean(string="Can be Sold", default=True)
    purchase_ok = fields.Boolean(string="Can be Purchased", default=True)
    naid_compliance_level = fields.Selection([("aaa", "NAID AAA"), ("aa", "NAID AA"), ("a", "NAID A")], string="NAID Compliance")
    service_type = fields.Selection([("storage", "Storage"), ("retrieval", "Retrieval"), ("destruction", "Destruction"), ("scanning", "Scanning")], string="Service Type")
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    # ============================================================================
    # SPECIALIZED CONFIGURATION FIELDS
    # ============================================================================
    additional_box_cost = fields.Monetary(string='Additional Box Cost', currency_field='currency_id', help='Cost for additional boxes beyond included amount')
    additional_document_cost = fields.Monetary(string='Additional Document Cost', currency_field='currency_id', help='Cost for additional documents beyond included amount')
    auto_invoice = fields.Boolean(string='Auto Invoice', help='Automatically generate invoices for this service')
    average_sale_price = fields.Monetary(string='Average Sale Price', currency_field='currency_id', compute='_compute_average_sale_price')
    base_cost = fields.Monetary(string='Base Cost', currency_field='currency_id', help='Base cost before markups')
    billing_frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annually', 'Annually'), ('per_use', 'Per Use')], string='Billing Frequency')
    box_retrieval_time = fields.Float(string='Box Retrieval Time (Hours)', digits=(6, 2), help='Standard time to retrieve a box')
    box_storage_included = fields.Integer(string='Boxes Included', help='Number of boxes included in base price')
    can_be_expensed = fields.Boolean(string='Can Be Expensed', help='Whether this service can be expensed')
    certificate_of_destruction = fields.Boolean(string='Certificate of Destruction', help='Includes certificate of destruction')
    climate_controlled = fields.Boolean(string='Climate Controlled', help='Climate controlled storage')
    compliance_guarantee = fields.Boolean(string='Compliance Guarantee', help='Guaranteed compliance with regulations')
    customer_retention_rate = fields.Float(string='Customer Retention Rate (%)', digits=(5, 2), help='Rate of customer retention for this service')
    customization_allowed = fields.Boolean(string='Customization Allowed', help='Service can be customized')
    data_recovery_guarantee = fields.Boolean(string='Data Recovery Guarantee', help='Guaranteed data recovery if needed')
    digital_conversion_included = fields.Boolean(string='Digital Conversion Included', help='Includes digital scanning')
    document_retrieval_time = fields.Float(string='Document Retrieval Time (Hours)', digits=(6, 2), help='Standard time to retrieve a document')
    document_storage_included = fields.Integer(string='Documents Included', help='Number of documents included in base price')
    emergency_response_time = fields.Float(string='Emergency Response Time (Hours)', digits=(6, 2), help='Guaranteed emergency response time')
    emergency_retrieval = fields.Boolean(string='Emergency Retrieval', help='24/7 emergency retrieval available')
    first_sale_date = fields.Date(string='First Sale Date', help='First time this service was sold')
    geographic_coverage = fields.Char(string='Geographic Coverage', help='Geographic areas covered')
    labor_cost = fields.Monetary(string='Labor Cost', currency_field='currency_id', help='Labor component of cost')
    last_sale_date = fields.Date(string='Last Sale Date', help='Most recent sale of this service')
    material_cost = fields.Monetary(string='Material Cost', currency_field='currency_id', help='Material component of cost')
    max_boxes_included = fields.Integer(string='Max Boxes Included', help='Maximum number of boxes included')
    max_documents_included = fields.Integer(string='Max Documents Included', help='Maximum number of documents included')
    minimum_billing_period = fields.Integer(string='Minimum Billing Period (Months)', help='Minimum commitment period')
    overhead_cost = fields.Monetary(string='Overhead Cost', currency_field='currency_id', help='Overhead component of cost')
    pickup_delivery_included = fields.Boolean(string='Pickup/Delivery Included', help='Includes pickup and delivery service')
    price_history_count = fields.Integer(string='Price Changes Count', compute='_compute_price_history_count')
    price_margin = fields.Float(string='Price Margin (%)', digits=(5, 2), help='Profit margin percentage')
    profit_margin = fields.Float(string='Profit Margin (%)', digits=(5, 2), help='Calculated profit margin')
    prorate_partial_periods = fields.Boolean(string='Prorate Partial Periods', help='Prorate billing for partial periods')
    sales_count = fields.Integer(string='Sales Count', compute='_compute_sales_count')
    sales_velocity = fields.Float(string='Sales Velocity', digits=(8, 2), help='Rate of sales over time')
    same_day_service = fields.Boolean(string='Same Day Service', help='Same day service available')
    security_guarantee = fields.Boolean(string='Security Guarantee', help='Security guarantee provided')
    shredding_included = fields.Boolean(string='Shredding Included', help='Secure shredding included')
    sla_terms = fields.Text(string='SLA Terms', help='Service level agreement terms')
    standard_response_time = fields.Float(string='Standard Response Time (Hours)', digits=(6, 2), help='Standard response time for requests')
    total_revenue_ytd = fields.Monetary(string='Total Revenue YTD', currency_field='currency_id', compute='_compute_total_revenue_ytd')
    total_sales_ytd = fields.Integer(string='Total Sales YTD', compute='_compute_total_sales_ytd')
    uptime_guarantee = fields.Float(string='Uptime Guarantee (%)', digits=(5, 2), help='Guaranteed uptime percentage')
    witness_destruction = fields.Boolean(string='Witness Destruction', help='Customer can witness destruction')

    @api.depends("product_template_id")
    def _compute_customer_rating(self):
        """Compute average customer rating from feedback records"""
        for record in self:
            if hasattr(self.env, "customer.feedback"):
                feedback_records = self.env["customer.feedback"].search(
                    [("product_template_id", "=", record.id), ("rating", ">", "0")]
                )
                if feedback_records:
                    total_rating = sum(
                        int(feedback.rating)
                        for feedback in feedback_records
                        if feedback.rating and feedback.rating.isdigit()
                    )
                    record.customer_rating = total_rating / len(feedback_records)
                else:
                    record.customer_rating = 0.0
            else:
                record.customer_rating = 0.0

    @api.depends("product_template_id")
    def _compute_feedback_count(self):
        """Compute total feedback count"""
        for record in self:
            if hasattr(self.env, "customer.feedback"):
                record.feedback_count = self.env["customer.feedback"].search_count(
                    [("product_template_id", "=", record.id)]
                )
            else:
                record.feedback_count = 0

    @api.depends("customer_rating", "feedback_count")
    def _compute_popular_service(self):
        """Determine if service is popular based on rating and feedback"""
        for record in self:
            record.popular_service = (
                record.customer_rating >= 4.0 and record.feedback_count >= 10
            )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("advance_notice_days", "staff_required")
    def _check_positive_values(self):
        """Validate positive values for certain fields"""
        for record in self:
            if record.advance_notice_days and record.advance_notice_days < 0:
                raise ValidationError(_("Advance notice days must be non-negative."))
            if record.staff_required and record.staff_required < 1:
                raise ValidationError(_("Staff required must be at least 1."))

    @api.constrains("sla_response_time", "sla_completion_time")
    def _check_sla_times(self):
        """Validate SLA time relationships"""
        for record in self:
            if (
                record.sla_response_time
                and record.sla_completion_time
                and record.sla_response_time > record.sla_completion_time
            ):
                raise ValidationError(
                    _("SLA response time cannot be greater than completion time.")
                )

    @api.constrains("service_radius_miles")
    def _check_service_radius(self):
        """Validate service radius"""
        for record in self:
            if record.service_radius_miles and record.service_radius_miles <= 0:
                raise ValidationError(_("Service radius must be positive."))

    @api.constrains("service_hours_start", "service_hours_end")
    def _check_service_hours(self):
        """Validate service hours"""
        for record in self:
            if record.service_hours_start >= record.service_hours_end:
                raise ValidationError(_("Service start time must be before end time."))

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange("container_type")
    def _onchange_container_type(self):
        """Set container specifications based on container type"""
        container_specs = {
            "type_01": {"volume": 1.2, "weight": 35, "dimensions": '12" x 15" x 10"'},
            "type_02": {"volume": 2.4, "weight": 65, "dimensions": '24" x 15" x 10"'},
            "type_03": {"volume": 0.875, "weight": 35, "dimensions": '42" x 6" x 6"'},
            "type_04": {"volume": 5.0, "weight": 75, "dimensions": "Variable"},
            "type_06": {"volume": 0.042, "weight": 40, "dimensions": '12" x 6" x 10"'},
        }
        
        if self.container_type and self.container_type in container_specs:
            specs = container_specs[self.container_type]
            self.container_volume_cf = specs["volume"]
            self.container_weight_lbs = specs["weight"]
            self.container_dimensions = specs["dimensions"]
            self.is_records_container = True

    @api.onchange("template_category")
    def _onchange_template_category(self):
        """Set default values based on template category"""
        if self.template_category == "destruction":
            self.naid_compliant = True
            self.security_clearance_required = True
            self.encryption_level = "advanced"
        elif self.template_category == "compliance":
            self.hipaa_compliant = True
            self.sox_compliant = True
            self.iso_compliant = True

    @api.onchange("pricing_model")
    def _onchange_pricing_model(self):
        """Set default values based on pricing model"""
        if self.pricing_model == "subscription":
            self.subscription_period = "monthly"
        elif self.pricing_model == "volume":
            self.bulk_discount_threshold = self.bulk_discount_threshold or 10
            self.bulk_discount_rate = self.bulk_discount_rate or 5.0

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model
    def get_services_by_category(self, category):
        """Get services by template category"""
        return self.search(
            [
                ("is_template_service", "=", True),
                ("template_category", "=", category),
                ("active", "=", True),
            ]
        )

    def get_availability_display(self):
        """Get human-readable availability display"""
        self.ensure_one()
        available_days = []
        days = [
            ("Monday", self.availability_monday),
            ("Tuesday", self.availability_tuesday),
            ("Wednesday", self.availability_wednesday),
            ("Thursday", self.availability_thursday),
            ("Friday", self.availability_friday),
            ("Saturday", self.availability_saturday),
            ("Sunday", self.availability_sunday),
        ]

        for day_name, available in days:
            if available:
                available_days.append(day_name)

        if len(available_days) == 7:
            return "Available daily"
        elif (
            len(available_days) == 5
            and not self.availability_saturday
            and not self.availability_sunday
        ):
            return "Available weekdays"
        elif len(available_days) == 0:
            return "No availability set"
        else:
            return f"Available: {', '.join(available_days)}"

    def get_compliance_badges(self):
        """Get list of compliance certifications"""
        self.ensure_one()
        badges = []
        if self.naid_compliant:
            badges.append("NAID")
        if self.hipaa_compliant:
            badges.append("HIPAA")
        if self.sox_compliant:
            badges.append("SOX")
        if self.iso_compliant:
            badges.append("ISO")
        return badges

    def calculate_service_price(self, quantity=1, duration=None):
        """Calculate service price based on pricing model"""
        self.ensure_one()
        base_price = self.list_price or 0.0

        if self.pricing_model == "fixed":
            total_price = base_price
        elif self.pricing_model == "hourly":
            hours = duration or self.service_duration or 1.0
            total_price = base_price * hours
        elif self.pricing_model in ["per_item", "per_box"]:
            total_price = base_price * quantity
            # Apply bulk discount if applicable
            if (
                self.bulk_discount_threshold
                and quantity >= self.bulk_discount_threshold
                and self.bulk_discount_rate
            ):
                discount = total_price * (self.bulk_discount_rate / 100)
                total_price -= discount
        else:
            total_price = base_price

        # Add setup fee if applicable
        if self.setup_fee:
            total_price += self.setup_fee

        # Apply minimum charge
        if self.minimum_charge:
            total_price = max(total_price, self.minimum_charge)

        return total_price
