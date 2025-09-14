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
