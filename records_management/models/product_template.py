# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # ============================================================================
    # RECORDS MANAGEMENT SERVICE FIELDS
    # ============================================================================
    # Service Configuration
    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    ),
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string="Active", default=True),
    is_template_service = fields.Boolean(string="Template Service", default=False)
    is_featured_service = fields.Boolean(string="Featured Service", default=False),
    template_category = fields.Selection(
        [
            ("storage", "Document Storage"),
            ("retrieval", "Document Retrieval"),
            ("destruction", "Secure Destruction"),
            ("digital", "Digital Services"),
            ("compliance", "Compliance Services"),
            ("consultation", "Consultation Services"),
        ]),
        string="Template Category",
    )

    # External Integration
    )
    external_service_id = fields.Char(string="External Service ID"),
    sync_enabled = fields.Boolean(string="Sync Enabled", default=True)
    api_integration = fields.Boolean(string="API Integration", default=False),
    webhook_notifications = fields.Boolean(
        string="Webhook Notifications", default=False
    )

    # ============================================================================
    # SERVICE SPECIFICATIONS
    # ============================================================================
    # Service Details
    )
    service_duration = fields.Float(string="Service Duration (hours)")
    service_frequency = fields.Selection(
        [
            ("one_time", "One Time"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annual", "Annual"),
            ("on_demand", "On Demand"),
        ]),
        string="Service Frequency",
        default="one_time",
    )

    )

    requires_appointment = fields.Boolean(string="Requires Appointment", default=False),
    advance_notice_days = fields.Integer(string="Advance Notice (days)", default=1)
    service_location = fields.Selection(
        [("onsite", "On-Site"), ("offsite", "Off-Site"), ("both", "Both")],
        string="Service Location",
        default="offsite",
    )

    # ============================================================================
    # COMPLIANCE & SECURITY
    # ============================================================================
    )
    naid_compliant = fields.Boolean(string="NAID Compliant", default=False),
    hipaa_compliant = fields.Boolean(string="HIPAA Compliant", default=False)
    sox_compliant = fields.Boolean(string="SOX Compliant", default=False),
    iso_certified = fields.Boolean(string="ISO Certified", default=False)

    security_clearance_required = fields.Boolean(
        string="Security Clearance Required", default=False
    )
    )
    background_check_required = fields.Boolean(
        string="Background Check Required", default=False
    ),
    certificate_of_destruction = fields.Boolean(
        string="Certificate of Destruction", default=False
    )
    )
    audit_trail_provided = fields.Boolean(string="Audit Trail Provided", default=True)

    # ============================================================================
    # CAPACITY & RESOURCES
    # ============================================================================
    max_capacity_per_service = fields.Integer(string="Max Capacity per Service"),
    resource_requirements = fields.Text(string="Resource Requirements")
    equipment_needed = fields.Char(string="Equipment Needed"),
    staff_required = fields.Integer(string="Staff Required", default=1)

    # Geographical service area
    service_radius_miles = fields.Float(string="Service Radius (miles)")
    available_regions = fields.Char(string="Available Regions"),
    restricted_areas = fields.Text(string="Restricted Areas")

    # ============================================================================
    # PRICING & BILLING
    # ============================================================================
    list_price = fields.Monetary(
        string="Sales Price", default=0.0, currency_field="currency_id"
    ),
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )

    pricing_model = fields.Selection(
        [
            ("fixed", "Fixed Price"),
            ("volume", "Volume Based"),
            ("time", "Time Based"),
            ("subscription", "Subscription"),
        ]),
        string="Pricing Model",
        default="fixed",
    )

    )

    minimum_service_charge = fields.Monetary(string="Minimum Service Charge"),
    setup_fee = fields.Monetary(string="Setup Fee")
    rush_order_surcharge = fields.Float(string="Rush Order Surcharge (%)")
    bulk_discount_threshold = fields.Integer(string="Bulk Discount Threshold"),
    bulk_discount_rate = fields.Float(string="Bulk Discount Rate (%)")

    # ============================================================================
    # SCHEDULING & AVAILABILITY
    # ============================================================================
    availability_monday = fields.Boolean(string="Monday", default=True),
    availability_tuesday = fields.Boolean(string="Tuesday", default=True)
    availability_wednesday = fields.Boolean(string="Wednesday", default=True),
    availability_thursday = fields.Boolean(string="Thursday", default=True)
    availability_friday = fields.Boolean(string="Friday", default=True),
    availability_saturday = fields.Boolean(string="Saturday", default=False)
    availability_sunday = fields.Boolean(string="Sunday", default=False),
    service_hours_start = fields.Float(string="Service Hours Start", default=8.0)
    service_hours_end = fields.Float(string="Service Hours End", default=17.0),
    emergency_service_available = fields.Boolean(
        string="Emergency Service Available", default=False
    )

    # ============================================================================
    # QUALITY & PERFORMANCE
    # ============================================================================
    )
    sla_response_time = fields.Float(string="SLA Response Time (hours)", default=24.0)
    sla_completion_time = fields.Float(
        string="SLA Completion Time (hours)", default=72.0
    )
    )
    quality_metrics = fields.Text(string="Quality Metrics"),
    performance_benchmarks = fields.Text(string="Performance Benchmarks")

    # Customer satisfaction tracking
    customer_rating = fields.Float(
        string="Customer Rating", compute="_compute_customer_rating"
    ),
    total_reviews = fields.Integer(
        string="Total Reviews", compute="_compute_total_reviews"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("message_ids")
    def _compute_customer_rating(self):
        """Compute average customer rating from feedback records"""
        for record in self:
            # Get customer feedback records related to this product template
            feedback_records = self.env["customer.feedback"].search(
                [("product_template_id", "=", record.id), ("rating", ">", 0)]
            )

            if feedback_records:
                total_rating = sum(
                    int(feedback.rating) for feedback in feedback_records
                )
                record.customer_rating = total_rating / len(feedback_records)
            else:
                record.customer_rating = 0.0

    @api.depends("message_ids")
    def _compute_total_reviews(self):
        """Compute total number of customer reviews for this service"""
        for record in self:
            # Count customer feedback records related to this product template
            feedback_count = self.env["customer.feedback"].search_count(
                [("product_template_id", "=", record.id)]
            )
            record.total_reviews = feedback_count

    @api.depends(
        "availability_monday",
        "availability_tuesday",
        "availability_wednesday",
        "availability_thursday",
        "availability_friday",
        "availability_saturday",
        "availability_sunday",)
    def _compute_weekly_availability(self):
        for record in self:
            days = [
                record.availability_monday,
                record.availability_tuesday,
                record.availability_wednesday,
                record.availability_thursday,
                record.availability_friday,
                record.availability_saturday,
                record.availability_sunday,
            ]
            record.weekly_availability_days = sum(days)

    weekly_availability_days = fields.Integer(
        compute="_compute_weekly_availability", string="Weekly Availability (days)"
    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_service_requests(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Service Requests",
            "res_model": "portal.request",
            "view_mode": "tree,form",
            "domain": [("request_type", "=", self.template_category)],
            "context": {"default_request_type": self.template_category},
        }

    def action_create_service_package(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Create Service Package",
            "res_model": "records.service.package",
            "view_mode": "form",
            "target": "new",
            "context": {"default_primary_service_id": self.id},
        }

    def action_duplicate_template(self):
        self.ensure_one()
        return self.copy({"name": f"{self.name} (Copy)"})

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def is_service_available(self, requested_date=None):
        """Check if service is available on requested date"""
        if not requested_date:
            return True

        # Check day of week availability
        weekday = requested_date.weekday()  # 0=Monday, 6=Sunday
        availability_fields = [
            self.availability_monday,
            self.availability_tuesday,
            self.availability_wednesday,
            self.availability_thursday,
            self.availability_friday,
            self.availability_saturday,
            self.availability_sunday,
        ]

        return bool(availability_fields[weekday])

    def calculate_service_price(self, quantity=1, rush_order=False):
        """Calculate service price based on quantity and options"""
        base_price = self.list_price

        # Apply bulk discount
        if quantity >= self.bulk_discount_threshold and self.bulk_discount_rate:
            base_price *= max(0, 1 - self.bulk_discount_rate / 100)

        # Apply rush order surcharge, ensuring negative surcharges are not allowed
        rush_surcharge = (
            self.rush_order_surcharge
            if self.rush_order_surcharge and self.rush_order_surcharge > 0
            else 0
        )
        if rush_order and rush_surcharge:
            base_price *= 1 + rush_surcharge / 100

        # Apply minimum service charge
        min_charge = (
            self.minimum_service_charge
            if self.minimum_service_charge is not None
            else 0
        )
        total_price = max(base_price * quantity, min_charge)

        return total_price + (self.setup_fee or 0)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("service_hours_start", "service_hours_end")
    def _check_service_hours(self):
        for record in self:
            if record.service_hours_start >= record.service_hours_end:
                raise ValidationError(_("Service start time must be before end time."))
    @api.constrains("bulk_discount_rate", "rush_order_surcharge")
    def _check_percentage_values(self):
        for record in self:
            if record.bulk_discount_rate and (
                record.bulk_discount_rate < 0 or record.bulk_discount_rate > 100
            ):
                raise ValidationError(
                    _("Bulk discount rate must be between 0 and 100.")
                )
            if record.rush_order_surcharge and record.rush_order_surcharge < 0:
                raise ValidationError(_("Rush order surcharge cannot be negative.")))
