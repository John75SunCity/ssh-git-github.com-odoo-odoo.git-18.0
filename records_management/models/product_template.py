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

    service_type = fields.Selection([
        ('storage', 'Storage'),
        ('destruction', 'Destruction'),
        ('retrieval', 'Retrieval'),
        ('pickup', 'Pickup'),
        ('consulting', 'Consulting'),
        ('other', 'Other'),
    ], string='RM Service Type', tracking=True)

    # --- Container Specs ---
    is_records_container = fields.Boolean(
        string="Represents a Container",
        help="Check if this product represents a physical container type for billing."
    )
    container_volume_cf = fields.Float(string="Volume (cu ft)", digits=(12, 4))
    container_weight_lbs = fields.Float(string="Avg. Weight (lbs)")

    # --- Compliance ---
    naid_compliant = fields.Boolean(string="NAID Compliant", tracking=True)
    hipaa_compliant = fields.Boolean(string="HIPAA Compliant", tracking=True)

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

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    def _compute_feedback_stats(self):
        """Compute average customer rating and feedback count from feedback records."""
        feedback_data = {}
        if 'portal.feedback' in self.env:
            # Using read_group is much more efficient than searching and looping in Python
            feedback_data_result = self.env['portal.feedback']._read_group(
                [('product_id.product_tmpl_id', 'in', self.ids), ('rating', '!=', False)],
                ['product_id', 'rating'],
                ['product_id']
            )
            for data in feedback_data_result:
                product_tmpl_id = self.env['product.product'].browse(data['product_id'][0]).product_tmpl_id.id
                ratings = self.env['portal.feedback'].search(data['__domain']).mapped('rating')
                numeric_ratings = [int(r) for r in ratings if r.isdigit()]
                if numeric_ratings:
                    feedback_data[product_tmpl_id] = {
                        'count': len(numeric_ratings),
                        'avg': sum(numeric_ratings) / len(numeric_ratings)
                    }

        for template in self:
            stats = feedback_data.get(template.id, {'count': 0, 'avg': 0.0})
            template.feedback_count = stats['count']
            template.customer_rating = stats['avg']

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

