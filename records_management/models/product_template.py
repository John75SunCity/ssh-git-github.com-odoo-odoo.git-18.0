from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # ============================================================================
    # RECORDS MANAGEMENT FIELDS
    # ============================================================================
    is_records_management_product = fields.Boolean(
        string="Is a Records Management Service",
        help="Check this if the product is specifically for records management services, like storage, shredding, or retrieval."
    )

    service_type = fields.Selection(
        selection_add=[
            ('storage', 'Storage'),
            ('destruction', 'Destruction'),
            ('retrieval', 'Retrieval'),
            ('pickup', 'Pickup'),
            ('consulting', 'Consulting'),
            ('other', 'Other'),
        ],
        string='RM Service Type',
        tracking=True,
        default='other',
        ondelete={
            'storage': 'set default',
            'destruction': 'set default',
            'retrieval': 'set default',
            'pickup': 'set default',
            'consulting': 'set default',
            'other': 'set default',
        }
    )

    # --- Container Specs ---
    is_records_container = fields.Boolean(
        string="Represents a Container",
        help="Check if this product represents a physical container type for billing."
    )
    container_volume_cf = fields.Float(string="Volume (cu ft)", digits=(12, 4))
    container_weight_lbs = fields.Float(string="Avg. Weight (lbs)")

    # --- Compliance ---
    naid_compliant = fields.Boolean(string="NAID Compliant")
    hipaa_compliant = fields.Boolean(string="HIPAA Compliant")

    # --- Service Level ---
    requires_appointment = fields.Boolean(string="Requires Appointment")
    sla_response_time = fields.Float(string="SLA Response Time (Hours)")
    sla_completion_time = fields.Float(string="SLA Completion Time (Hours)")

    # --- Portal Display ---
    is_featured_service = fields.Boolean(string="Featured in Portal")
    service_description_portal = fields.Html(string="Portal Description")

    # --- Computed Fields ---
    customer_rating = fields.Float(string="Avg. Rating", compute='_compute_feedback_stats', digits=(3, 2))
    feedback_count = fields.Integer(string="Feedback Count", compute='_compute_feedback_stats')

    # Additional computed fields for view compatibility
    price_history_count = fields.Integer(
        string="Price History Count",
        compute='_compute_price_stats',
        help="Number of price history records"
    )

    can_be_expensed = fields.Boolean(
        string="Can be Expensed",
        default=True,
        help="Whether this product can be expensed"
    )

    price_margin = fields.Float(
        string="Price Margin",
        compute='_compute_price_stats',
        help="Price margin percentage"
    )

    base_cost = fields.Float(
        string="Base Cost",
        compute='_compute_price_stats',
        help="Base cost for the product"
    )

    # Additional cost breakdown fields
    labor_cost = fields.Float(
        string="Labor Cost",
        help="Labor cost component"
    )

    material_cost = fields.Float(
        string="Material Cost",
        help="Material cost component"
    )

    overhead_cost = fields.Float(
        string="Overhead Cost",
        help="Overhead cost component"
    )

    # Billing configuration fields
    billing_frequency = fields.Selection([
        ('one_time', 'One Time'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    ], string="Billing Frequency",
        default='monthly',
        help="How frequently this service is billed"
    )

    minimum_billing_period = fields.Integer(
        string="Minimum Billing Period",
        default=1,
        help="Minimum billing period in the selected frequency unit"
    )

    prorate_partial_periods = fields.Boolean(
        string="Prorate Partial Periods",
        default=True,
        help="Whether to prorate billing for partial periods"
    )

    auto_invoice = fields.Boolean(
        string="Auto Invoice",
        default=True,
        help="Automatically generate invoices for this service"
    )

    # Document storage configuration
    document_storage_included = fields.Integer(
        string="Documents Included",
        default=0,
        help="Number of documents included in base price"
    )

    max_documents_included = fields.Integer(
        string="Max Documents Included",
        default=0,
        help="Maximum number of documents that can be included"
    )

    additional_document_cost = fields.Float(
        string="Additional Document Cost",
        help="Cost per additional document beyond included amount"
    )

    # ALL ADDITIONAL FIELDS FROM VIEWS - Adding in bulk for efficiency
    additional_box_cost = fields.Float(string="Additional Box Cost", help="Cost per additional box")
    api_integration = fields.Boolean(string="API Integration", help="API integration available")
    average_sale_price = fields.Float(string="Average Sale Price", compute='_compute_sales_stats')
    box_retrieval_time = fields.Float(string="Box Retrieval Time (Hours)", default=24.0)
    box_storage_included = fields.Integer(string="Boxes Included", default=0)
    certificate_of_destruction = fields.Boolean(string="Certificate of Destruction", default=True)
    climate_controlled = fields.Boolean(string="Climate Controlled", help="Climate controlled storage")
    compliance_guarantee = fields.Boolean(string="Compliance Guarantee", default=True)
    customer_retention_rate = fields.Float(string="Customer Retention Rate", compute='_compute_customer_stats')
    customization_allowed = fields.Boolean(string="Customization Allowed", default=True)
    data_recovery_guarantee = fields.Boolean(string="Data Recovery Guarantee")
    digital_conversion_included = fields.Boolean(string="Digital Conversion Included")
    document_retrieval_time = fields.Float(string="Document Retrieval Time (Hours)", default=4.0)
    emergency_response_time = fields.Float(string="Emergency Response Time (Hours)", default=2.0)
    emergency_retrieval = fields.Boolean(string="Emergency Retrieval Available", default=True)
    external_service_id = fields.Char(string="External Service ID")
    first_sale_date = fields.Date(string="First Sale Date", compute='_compute_sales_stats')
    geographic_coverage = fields.Selection([
        ('local', 'Local'),
        ('regional', 'Regional'),
        ('national', 'National'),
        ('international', 'International')
    ], string="Geographic Coverage", default='local')
    is_template_service = fields.Boolean(string="Is Template Service")
    last_sale_date = fields.Date(string="Last Sale Date", compute='_compute_sales_stats')
    max_boxes_included = fields.Integer(string="Max Boxes Included", default=0)
    naid_compliance_level = fields.Selection([
        ('none', 'None'),
        ('basic', 'Basic'),
        ('aaa', 'AAA'),
        ('enhanced', 'Enhanced AAA')
    ], string="NAID Compliance Level", default='aaa')
    pickup_delivery_included = fields.Boolean(string="Pickup/Delivery Included", default=True)
    profit_margin = fields.Float(string="Profit Margin %", compute='_compute_price_stats')
    requires_approval = fields.Boolean(string="Requires Approval")
    sales_velocity = fields.Float(string="Sales Velocity", compute='_compute_sales_stats')
    same_day_service = fields.Boolean(string="Same Day Service Available")
    security_guarantee = fields.Boolean(string="Security Guarantee", default=True)
    shredding_included = fields.Boolean(string="Shredding Included")
    sla_terms = fields.Text(string="SLA Terms")
    standard_response_time = fields.Float(string="Standard Response Time (Hours)", default=4.0)
    sync_enabled = fields.Boolean(string="Sync Enabled", default=True)
    template_category = fields.Selection([
        ('storage', 'Storage Services'),
        ('destruction', 'Destruction Services'),
        ('retrieval', 'Retrieval Services'),
        ('consulting', 'Consulting Services'),
        ('other', 'Other Services')
    ], string="Template Category", default='storage')
    total_revenue_ytd = fields.Float(string="Total Revenue YTD", compute='_compute_sales_stats')
    total_sales_ytd = fields.Float(string="Total Sales YTD", compute='_compute_sales_stats')
    uptime_guarantee = fields.Float(string="Uptime Guarantee %", default=99.9)
    webhook_notifications = fields.Boolean(string="Webhook Notifications")
    witness_destruction = fields.Boolean(string="Witness Destruction Available")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    def _compute_feedback_stats(self):
        """Compute average customer rating and feedback count from feedback records."""
        # Initialize stats for all templates
        for template in self:
            template.feedback_count = 0
            template.customer_rating = 0.0

        if 'portal.feedback' in self.env and self.ids:
            # Efficiently read all feedback data in one go
            feedback_data = self.env['portal.feedback']._read_group(
                [('product_id.product_tmpl_id', 'in', self.ids), ('rating', '!=', False)],
                ['product_id', 'rating'],
                ['product_id']
            )

            # Map results to template IDs
            feedback_map = {}
            for item in feedback_data:
                product_tmpl_id = self.env['product.product'].browse(item['product_id'][0]).product_tmpl_id.id
                if product_tmpl_id not in feedback_map:
                    feedback_map[product_tmpl_id] = []

                # Assuming rating is a selection of strings '1', '2', '3', '4', '5'
                try:
                    feedback_map[product_tmpl_id].append(int(item['rating']))
                except (ValueError, TypeError):
                    continue # Ignore non-integer ratings

            # Assign computed values
            for template in self:
                if template.id in feedback_map:
                    ratings = feedback_map[template.id]
                    if ratings:
                        template.feedback_count = len(ratings)
                        template.customer_rating = sum(ratings) / len(ratings)

    def _compute_price_stats(self):
        """Compute price-related statistics."""
        for template in self:
            # Price history count (simplified - could be from actual price history model)
            template.price_history_count = 0

            # Price margin calculation (list_price vs standard_price)
            if template.list_price and template.standard_price:
                template.price_margin = ((template.list_price - template.standard_price) / template.list_price) * 100
            else:
                template.price_margin = 0.0

            # Base cost (using standard_price as base cost)
            template.base_cost = template.standard_price or 0.0

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('sla_response_time', 'sla_completion_time')
    def _check_sla_times(self):
        """Validate SLA time relationships."""
        for record in self:
            if record.sla_response_time and record.sla_completion_time and record.sla_response_time > record.sla_completion_time:
                raise ValidationError(_("SLA response time cannot be greater than completion time."))

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('is_records_management_product')
    def _onchange_is_records_management_product(self):
        """Set default type to 'Service' if this is a records management product."""
        if self.is_records_management_product:
            self.type = 'service'

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_availability_display(self):
        """Get human-readable availability display. (Placeholder for more complex logic)"""
        self.ensure_one()
        # This could be expanded to check resource calendars or other settings.
        return _("Available standard business hours.")

    def get_compliance_badges(self):
        """Get list of compliance certifications."""
        self.ensure_one()
        badges = []
        if self.naid_compliant:
            badges.append("NAID")
        if self.hipaa_compliant:
            badges.append("HIPAA")
        return badges

    def calculate_service_price(self, quantity=1):
        """
        Calculate service price. This is a simplified version.
        Real pricing can be complex and might involve pricelist rules.
        """
        self.ensure_one()
        # The 'list_price' field on product.template is the base sales price.
        base_price = self.list_price or 0.0
        total_price = base_price * quantity

        # A real implementation would check for pricelist rules here.
        # self.env['product.pricelist.item'].search(...)

        return total_price

    # -------------------------------------------------------------
    # Placeholder button actions from XML (safe stubs)
    # -------------------------------------------------------------
    def action_configure_pricing(self):
        self.ensure_one()
        return False

    def action_view_sales(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Orders'),
            'res_model': 'sale.order.line',
            'view_mode': 'list,form',
            'domain': [('product_id.product_tmpl_id', 'in', self.ids)],
            'target': 'current',
        }

    def action_view_pricing_history(self):
        self.ensure_one()
        return False

    def action_view_variants(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Variants'),
            'res_model': 'product.product',
            'view_mode': 'list,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'target': 'current',
        }
