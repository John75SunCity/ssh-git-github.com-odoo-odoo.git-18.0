from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # ============================================================================
    # FIELDS
    # ============================================================================
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    currency_id = fields.Many2one()
    is_records_container = fields.Boolean()
    container_type = fields.Selection()
    container_volume_cf = fields.Float()
    container_weight_lbs = fields.Float()
    container_dimensions = fields.Char()
    is_template_service = fields.Boolean()
    is_featured_service = fields.Boolean()
    template_category = fields.Selection()
    external_service_id = fields.Char()
    sync_enabled = fields.Boolean()
    api_integration = fields.Boolean()
    webhook_notifications = fields.Boolean()
    service_duration = fields.Float()
    service_frequency = fields.Selection()
    requires_appointment = fields.Boolean()
    advance_notice_days = fields.Integer()
    service_location = fields.Selection()
    naid_compliant = fields.Boolean()
    hipaa_compliant = fields.Boolean()
    sox_compliant = fields.Boolean()
    iso_compliant = fields.Boolean()
    security_clearance_required = fields.Boolean()
    encryption_level = fields.Selection()
    max_concurrent_jobs = fields.Integer()
    staff_required = fields.Integer()
    equipment_required = fields.Text()
    vehicle_required = fields.Boolean()
    service_radius_miles = fields.Integer()
    pricing_model = fields.Selection()
    minimum_charge = fields.Float()
    setup_fee = fields.Float(string='Setup Fee')
    bulk_discount_threshold = fields.Integer()
    bulk_discount_rate = fields.Float()
    subscription_period = fields.Selection()
    availability_monday = fields.Boolean(string='Available Monday')
    availability_tuesday = fields.Boolean(string='Available Tuesday')
    availability_wednesday = fields.Boolean(string='Available Wednesday')
    availability_thursday = fields.Boolean(string='Available Thursday')
    availability_friday = fields.Boolean(string='Available Friday')
    availability_saturday = fields.Boolean(string='Available Saturday')
    availability_sunday = fields.Boolean(string='Available Sunday')
    service_hours_start = fields.Float()
    service_hours_end = fields.Float()
    emergency_service = fields.Boolean()
    after_hours_available = fields.Boolean()
    sla_response_time = fields.Float()
    sla_completion_time = fields.Float()
    quality_standard = fields.Selection()
    performance_guarantee = fields.Boolean()
    customer_rating = fields.Float()
    feedback_count = fields.Integer()
    popular_service = fields.Boolean()
    service_description_portal = fields.Html()
    service_benefits = fields.Html()
    detailed_type = fields.Selection(string='Product Type')
    list_price = fields.Float(string='Sales Price')
    standard_price = fields.Float(string='Cost')
    categ_id = fields.Many2one('product.category')
    uom_id = fields.Many2one('uom.uom')
    uom_po_id = fields.Many2one('uom.uom')
    sale_ok = fields.Boolean(string='Can be Sold')
    purchase_ok = fields.Boolean(string='Can be Purchased')
    naid_compliance_level = fields.Selection(string='NAID Compliance')
    service_type = fields.Selection(string='Service Type')
    additional_box_cost = fields.Monetary(string='Additional Box Cost')
    additional_document_cost = fields.Monetary(string='Additional Document Cost')
    auto_invoice = fields.Boolean(string='Auto Invoice')
    average_sale_price = fields.Monetary(string='Average Sale Price')
    base_cost = fields.Monetary(string='Base Cost')
    billing_frequency = fields.Selection(string='Billing Frequency')
    box_retrieval_time = fields.Float(string='Box Retrieval Time (Hours)')
    box_storage_included = fields.Integer(string='Boxes Included')
    can_be_expensed = fields.Boolean(string='Can Be Expensed')
    certificate_of_destruction = fields.Boolean(string='Certificate of Destruction')
    climate_controlled = fields.Boolean(string='Climate Controlled')
    compliance_guarantee = fields.Boolean(string='Compliance Guarantee')
    customer_retention_rate = fields.Float(string='Customer Retention Rate (%)')
    customization_allowed = fields.Boolean(string='Customization Allowed')
    data_recovery_guarantee = fields.Boolean(string='Data Recovery Guarantee')
    digital_conversion_included = fields.Boolean(string='Digital Conversion Included')
    document_retrieval_time = fields.Float(string='Document Retrieval Time (Hours)')
    document_storage_included = fields.Integer(string='Documents Included')
    emergency_response_time = fields.Float(string='Emergency Response Time (Hours)')
    emergency_retrieval = fields.Boolean(string='Emergency Retrieval')
    first_sale_date = fields.Date(string='First Sale Date')
    geographic_coverage = fields.Char(string='Geographic Coverage')
    labor_cost = fields.Monetary(string='Labor Cost')
    last_sale_date = fields.Date(string='Last Sale Date')
    material_cost = fields.Monetary(string='Material Cost')
    max_boxes_included = fields.Integer(string='Max Boxes Included')
    max_documents_included = fields.Integer(string='Max Documents Included')
    minimum_billing_period = fields.Integer(string='Minimum Billing Period (Months)')
    overhead_cost = fields.Monetary(string='Overhead Cost')
    pickup_delivery_included = fields.Boolean(string='Pickup/Delivery Included')
    price_history_count = fields.Integer(string='Price Changes Count')
    price_margin = fields.Float(string='Price Margin (%)')
    profit_margin = fields.Float(string='Profit Margin (%)')
    prorate_partial_periods = fields.Boolean(string='Prorate Partial Periods')
    sales_count = fields.Integer(string='Sales Count')
    sales_velocity = fields.Float(string='Sales Velocity')
    same_day_service = fields.Boolean(string='Same Day Service')
    security_guarantee = fields.Boolean(string='Security Guarantee')
    shredding_included = fields.Boolean(string='Shredding Included')
    sla_terms = fields.Text(string='SLA Terms')
    standard_response_time = fields.Float(string='Standard Response Time (Hours)')
    total_revenue_ytd = fields.Monetary(string='Total Revenue YTD')
    total_sales_ytd = fields.Integer(string='Total Sales YTD')
    uptime_guarantee = fields.Float(string='Uptime Guarantee (%)')
    witness_destruction = fields.Boolean(string='Witness Destruction')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_customer_rating(self):
            """Compute average customer rating from feedback records"""
            for record in self:
                if hasattr(self.env, "customer.feedback"):
                    feedback_records = self.env["customer.feedback").search(]
                        [("product_template_id", "=", record.id), ("rating", ">", "0")]

                    if feedback_records:
                        total_rating = sum()
                            int(feedback.rating)
                            for feedback in feedback_records:
                            if feedback.rating and feedback.rating.isdigit():

                        record.customer_rating = total_rating / len(feedback_records)
                    else:
                        record.customer_rating = 0.0
                else:
                    record.customer_rating = 0.0


    def _compute_feedback_count(self):
            """Compute total feedback count"""
            for record in self:
                if hasattr(self.env, "customer.feedback"):
                    record.feedback_count = self.env["customer.feedback"].search_count()
                        [("product_template_id", "=", record.id)]

                else:
                    record.feedback_count = 0


    def _compute_popular_service(self):
            """Determine if service is popular based on rating and feedback""":
            for record in self:
                record.popular_service = ()
                    record.customer_rating >= 4.0 and record.feedback_count >= 10


        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_positive_values(self):
            """Validate positive values for certain fields""":
            for record in self:
                if record.advance_notice_days and record.advance_notice_days < 0:
                    raise ValidationError(_("Advance notice days must be non-negative."))
                if record.staff_required and record.staff_required < 1:
                    raise ValidationError(_("Staff required must be at least 1."))


    def _check_sla_times(self):
            """Validate SLA time relationships"""
            for record in self:
                if (:)
                    record.sla_response_time
                    and record.sla_completion_time
                    and record.sla_response_time > record.sla_completion_time

                    raise ValidationError()
                        _("SLA response time cannot be greater than completion time.")



    def _check_service_radius(self):
            """Validate service radius"""
            for record in self:
                if record.service_radius_miles and record.service_radius_miles <= 0:
                    raise ValidationError(_("Service radius must be positive."))


    def _check_service_hours(self):
            """Validate service hours"""
            for record in self:
                if record.service_hours_start >= record.service_hours_end:
                    raise ValidationError(_("Service start time must be before end time."))

        # ============================================================================
            # ONCHANGE METHODS
        # ============================================================================

    def _onchange_container_type(self):
            """Set container specifications based on container type"""
            container_specs = {}
                "type_01": {"volume": 1.2, "weight": 35, "dimensions": '12" x 15" x 10"'},"
                "type_02": {"volume": 2.4, "weight": 65, "dimensions": '24" x 15" x 10"'},"
                "type_03": {"volume": 0.875, "weight": 35, "dimensions": '42" x 6" x 6"'},"
                "type_04": {"volume": 5.0, "weight": 75, "dimensions": "Variable"},
                "type_06": {"volume": 0.42, "weight": 40, "dimensions": '12" x 6" x 10"'},"


            if self.container_type and self.container_type in container_specs:
                specs = container_specs[self.container_type]
                self.container_volume_cf = specs["volume"]
                self.container_weight_lbs = specs["weight"]
                self.container_dimensions = specs["dimensions"]
                self.is_records_container = True


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

    def get_services_by_category(self, category):
            """Get services by template category"""
            return self.search()
                []
                    ("is_template_service", "=", True),
                    ("template_category", "=", category),
                    ("active", "=", True),




    def get_availability_display(self):
            """Get human-readable availability display"""
            self.ensure_one()
            available_days = []
            days = []
                ("Monday", self.availability_monday),
                ("Tuesday", self.availability_tuesday),
                ("Wednesday", self.availability_wednesday),
                ("Thursday", self.availability_thursday),
                ("Friday", self.availability_friday),
                ("Saturday", self.availability_saturday),
                ("Sunday", self.availability_sunday),


            for day_name, available in days:
                if available:
                    available_days.append(day_name)

            if len(available_days) == 7:
                return "Available daily"
            elif ()
                len(available_days) == 5
                and not self.availability_saturday
                and not self.availability_sunday

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
                # Apply bulk discount if applicable:
                if (:)
                    self.bulk_discount_threshold
                    and quantity >= self.bulk_discount_threshold
                    and self.bulk_discount_rate

                    discount = total_price * (self.bulk_discount_rate / 100)
                    total_price -= discount
            else:
                total_price = base_price

            # Add setup fee if applicable:
            if self.setup_fee:
                total_price += self.setup_fee

            # Apply minimum charge
            if self.minimum_charge:
                total_price = max(total_price, self.minimum_charge)

            return total_price

