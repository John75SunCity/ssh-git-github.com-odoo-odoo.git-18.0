# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # ============================================================================
    # RECORDS MANAGEMENT SERVICE FIELDS - PHASE 8 CONTINUATION
    # ============================================================================

    # === SERVICE CONFIGURATION FIELDS ===
    is_template_service = fields.Boolean(
        string="Template Service",
        default=False,
        help="Indicates if this is a template service product",
    )
    is_featured_service = fields.Boolean(
        string="Featured Service",
        default=False,
        help="Mark this service as featured in catalogs",
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
        help="Category of the service template",
    )

    external_service_id = fields.Char(
        string="External Service ID",
        help="ID used in external systems for this service",
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

    # === BILLING AND PRICING FIELDS ===
    billing_frequency = fields.Selection(
        [
            ("one_time", "One Time"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annually", "Annually"),
            ("per_use", "Per Use"),
        ],
        string="Billing Frequency",
        default="monthly",
    )

    minimum_billing_period = fields.Integer(
        string="Minimum Billing Period (months)",
        default=1,
        help="Minimum billing period in months",
    )
    prorate_partial_periods = fields.Boolean(
        string="Prorate Partial Periods",
        default=True,
        help="Prorate charges for partial billing periods",
    )
    auto_invoice = fields.Boolean(
        string="Auto Invoice",
        default=True,
        help="Automatically generate invoices for this service",
    )
    requires_approval = fields.Boolean(
        string="Requires Approval",
        default=False,
        help="Service requires approval before activation",
    )
    can_be_expensed = fields.Boolean(
        string="Can be Expensed",
        default=True,
        help="Service can be expensed by customers",
    )

    # === COST BREAKDOWN FIELDS ===
    base_cost = fields.Float(string="Base Cost", help="Base cost for the service")
    labor_cost = fields.Float(string="Labor Cost", help="Labor cost component")
    material_cost = fields.Float(string="Material Cost", help="Material cost component")
    overhead_cost = fields.Float(string="Overhead Cost", help="Overhead cost component")
    price_margin = fields.Float(
        string="Price Margin (%)",
        compute="_compute_price_margin",
        store=True,
        help="Profit margin percentage",
    )
    profit_margin = fields.Float(
        string="Profit Margin",
        compute="_compute_profit_margin",
        store=True,
        help="Calculated profit margin",
    )
    profit = fields.Float(
        string="Profit",
        compute="_compute_profit",
        store=True,
        help="Calculated profit amount",
    )
    revenue = fields.Float(
        string="Revenue",
        compute="_compute_revenue",
        store=True,
        help="Total revenue for this product",
    )

    # === CAPACITY AND LIMITS FIELDS ===
    max_boxes_included = fields.Integer(
        string="Max Boxes Included",
        default=0,
        help="Maximum number of boxes included in base service",
    )
    max_documents_included = fields.Integer(
        string="Max Documents Included",
        default=0,
        help="Maximum number of documents included in base service",
    )
    additional_box_cost = fields.Float(
        string="Additional Box Cost",
        help="Cost per additional box beyond included limit",
    )
    additional_document_cost = fields.Float(
        string="Additional Document Cost",
        help="Cost per additional document beyond included limit",
    )
    min_quantity = fields.Float(
        string="Minimum Quantity",
        default=1.0,
        help="Minimum quantity that can be ordered",
    )
    box_storage_included = fields.Boolean(
        string="Box Storage Included",
        default=True,
        help="Box storage is included in this service",
    )
    document_storage_included = fields.Boolean(
        string="Document Storage Included",
        default=True,
        help="Document storage is included in this service",
    )

    # === SERVICE LEVEL FIELDS ===
    standard_response_time = fields.Float(
        string="Standard Response Time (hours)",
        default=24.0,
        help="Standard response time in hours",
    )
    emergency_response_time = fields.Float(
        string="Emergency Response Time (hours)",
        default=2.0,
        help="Emergency response time in hours",
    )
    box_retrieval_time = fields.Float(
        string="Box Retrieval Time (hours)",
        default=4.0,
        help="Standard box retrieval time in hours",
    )
    document_retrieval_time = fields.Float(
        string="Document Retrieval Time (hours)",
        default=2.0,
        help="Standard document retrieval time in hours",
    )
    same_day_service = fields.Boolean(
        string="Same Day Service Available",
        default=False,
        help="Same day service is available",
    )
    emergency_retrieval = fields.Boolean(
        string="Emergency Retrieval Available",
        default=True,
        help="Emergency retrieval service is available",
    )
    pickup_delivery_included = fields.Boolean(
        string="Pickup/Delivery Included",
        default=True,
        help="Pickup and delivery service is included",
    )

    # === COMPLIANCE AND SECURITY FIELDS ===
    naid_compliance_level = fields.Selection(
        [
            ("aaa", "NAID AAA"),
            ("aa", "NAID AA"),
            ("a", "NAID A"),
            ("none", "Not NAID Certified"),
        ],
        string="NAID Compliance Level",
        default="aaa",
    )

    compliance_guarantee = fields.Boolean(
        string="Compliance Guarantee",
        default=True,
        help="Service includes compliance guarantee",
    )
    security_guarantee = fields.Boolean(
        string="Security Guarantee",
        default=True,
        help="Service includes security guarantee",
    )
    certificate_of_destruction = fields.Boolean(
        string="Certificate of Destruction",
        default=True,
        help="Certificate of destruction is provided",
    )
    witness_destruction = fields.Boolean(
        string="Witness Destruction Available",
        default=True,
        help="Witness destruction service is available",
    )
    climate_controlled = fields.Boolean(
        string="Climate Controlled Storage",
        default=True,
        help="Storage facility is climate controlled",
    )
    data_recovery_guarantee = fields.Boolean(
        string="Data Recovery Guarantee",
        default=False,
        help="Data recovery guarantee is provided",
    )
    uptime_guarantee = fields.Float(
        string="Uptime Guarantee (%)",
        default=99.9,
        help="Service uptime guarantee percentage",
    )

    # === DIGITAL SERVICES FIELDS ===
    digital_conversion_included = fields.Boolean(
        string="Digital Conversion Included",
        default=False,
        help="Digital conversion service is included",
    )
    shredding_included = fields.Boolean(
        string="Shredding Included", default=False, help="Shredding service is included"
    )
    customization_allowed = fields.Boolean(
        string="Customization Allowed",
        default=True,
        help="Service can be customized for specific customer needs",
    )

    # === BUSINESS METRICS FIELDS ===
    sales_count = fields.Integer(
        string="Sales Count",
        compute="_compute_sales_metrics",
        store=True,
        help="Total number of sales for this product",
    )
    customer_count = fields.Integer(
        string="Customer Count",
        compute="_compute_customer_metrics",
        store=True,
        help="Number of unique customers who purchased this product",
    )
    average_sale_price = fields.Float(
        string="Average Sale Price",
        compute="_compute_sales_metrics",
        store=True,
        help="Average sale price across all sales",
    )
    total_revenue_ytd = fields.Float(
        string="Total Revenue YTD",
        compute="_compute_revenue_metrics",
        store=True,
        help="Total revenue year to date",
    )
    total_sales_ytd = fields.Integer(
        string="Total Sales YTD",
        compute="_compute_revenue_metrics",
        store=True,
        help="Total sales count year to date",
    )
    sales_velocity = fields.Float(
        string="Sales Velocity",
        compute="_compute_sales_velocity",
        store=True,
        help="Average sales per month",
    )
    customer_retention_rate = fields.Float(
        string="Customer Retention Rate (%)",
        compute="_compute_retention_rate",
        store=True,
        help="Customer retention rate percentage",
    )
    avg_deal_size = fields.Float(
        string="Average Deal Size",
        compute="_compute_deal_metrics",
        store=True,
        help="Average deal size for this product",
    )

    # === DATE TRACKING FIELDS ===
    first_sale_date = fields.Date(
        string="First Sale Date", help="Date of the first sale of this product"
    )
    last_sale_date = fields.Date(
        string="Last Sale Date", help="Date of the most recent sale"
    )
    effective_date = fields.Date(
        string="Effective Date",
        default=fields.Date.today,
        help="Date when this product becomes effective",
    )
    expiry_date = fields.Date(
        string="Expiry Date", help="Date when this product expires or is discontinued"
    )

    # === ADDITIONAL SERVICE FIELDS ===
    geographic_coverage = fields.Text(
        string="Geographic Coverage",
        help="Geographic areas where this service is available",
    )
    sla_terms = fields.Text(
        string="SLA Terms", help="Service Level Agreement terms and conditions"
    )
    discount_percentage = fields.Float(
        string="Default Discount %",
        default=0.0,
        help="Default discount percentage for this product",
    )
    period = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annually", "Annually"),
        ],
        string="Service Period",
        default="monthly",
    )

    # === RELATIONAL FIELDS ===
    pricing_rule_ids = fields.One2many(
        "product.pricing.rule", "product_tmpl_id", string="Pricing Rules"
    )
    sales_analytics_ids = fields.One2many(
        "product.sales.analytics", "product_tmpl_id", string="Sales Analytics"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("list_price", "standard_price")
    def _compute_price_margin(self):
        """Compute price margin percentage"""
        for record in self:
            if record.list_price and record.standard_price:
                record.price_margin = (
                    (record.list_price - record.standard_price) / record.list_price
                ) * 100
            else:
                record.price_margin = 0.0

    @api.depends("list_price", "standard_price")
    def _compute_profit_margin(self):
        """Compute profit margin"""
        for record in self:
            if record.list_price and record.standard_price:
                record.profit_margin = record.list_price - record.standard_price
            else:
                record.profit_margin = 0.0

    @api.depends("profit_margin", "sales_count")
    def _compute_profit(self):
        """Compute total profit"""
        for record in self:
            record.profit = record.profit_margin * record.sales_count

    @api.depends("list_price", "sales_count")
    def _compute_revenue(self):
        """Compute total revenue"""
        for record in self:
            record.revenue = record.list_price * record.sales_count

    @api.depends("product_variant_ids.sale_order_line_ids")
    def _compute_sales_metrics(self):
        """Compute sales count and average sale price"""
        for record in self:
            sale_lines = record.product_variant_ids.mapped("sale_order_line_ids")
            confirmed_lines = sale_lines.filtered(
                lambda l: l.order_id.state in ["sale", "done"]
            )

            record.sales_count = len(confirmed_lines)
            if confirmed_lines:
                record.average_sale_price = sum(
                    confirmed_lines.mapped("price_unit")
                ) / len(confirmed_lines)
            else:
                record.average_sale_price = 0.0

    @api.depends("product_variant_ids.sale_order_line_ids")
    def _compute_customer_metrics(self):
        """Compute customer count"""
        for record in self:
            sale_lines = record.product_variant_ids.mapped("sale_order_line_ids")
            confirmed_lines = sale_lines.filtered(
                lambda l: l.order_id.state in ["sale", "done"]
            )

            customers = confirmed_lines.mapped("order_id.partner_id")
            record.customer_count = len(customers)

    @api.depends("product_variant_ids.sale_order_line_ids")
    def _compute_revenue_metrics(self):
        """Compute YTD revenue and sales metrics"""
        current_year = fields.Date.today().year
        for record in self:
            sale_lines = record.product_variant_ids.mapped("sale_order_line_ids")
            ytd_lines = sale_lines.filtered(
                lambda l: l.order_id.state in ["sale", "done"]
                and l.order_id.date_order.year == current_year
            )

            record.total_sales_ytd = len(ytd_lines)
            record.total_revenue_ytd = sum(ytd_lines.mapped("price_subtotal"))

    @api.depends("sales_count", "first_sale_date")
    def _compute_sales_velocity(self):
        """Compute sales velocity (sales per month)"""
        for record in self:
            if record.first_sale_date and record.sales_count:
                months_active = (
                    fields.Date.today() - record.first_sale_date
                ).days / 30.0
                if months_active > 0:
                    record.sales_velocity = record.sales_count / months_active
                else:
                    record.sales_velocity = 0.0
            else:
                record.sales_velocity = 0.0

    @api.depends("customer_count")
    def _compute_retention_rate(self):
        """Compute customer retention rate"""
        for record in self:
            # Simplified calculation - could be enhanced with actual repeat purchase data
            if record.customer_count > 0:
                record.customer_retention_rate = 85.0  # Default retention rate
            else:
                record.customer_retention_rate = 0.0

    @api.depends("total_revenue_ytd", "total_sales_ytd")
    def _compute_deal_metrics(self):
        """Compute average deal size"""
        for record in self:
            if record.total_sales_ytd > 0:
                record.avg_deal_size = record.total_revenue_ytd / record.total_sales_ytd
            else:
                record.avg_deal_size = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_view_sales(self):
        """View sales for product."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Sales"),
            "res_model": "sale.order.line",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_template_id", "=", self.id)],
        }

    def action_configure_pricing(self):
        """Configure pricing for product."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Configure Pricing"),
            "res_model": "product.pricelist.item",
            "view_mode": "tree,form",
            "target": "current",
            "context": {"default_product_tmpl_id": self.id},
        }

    def action_configure_variants(self):
        """Configure product variants."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Configure Variants"),
            "res_model": "product.product",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_tmpl_id", "=", self.id)],
        }

    def action_pricing_rules(self):
        """View pricing rules."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Pricing Rules"),
            "res_model": "product.pricelist.item",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_tmpl_id", "=", self.id)],
        }

    def action_duplicate(self):
        """Duplicate product."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Product Duplicated"),
                "message": _("Product has been duplicated successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_update_costs(self):
        """Update product costs."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Costs Updated"),
                "message": _("Product costs have been updated."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_variants(self):
        """View product variants."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Product Variants"),
            "res_model": "product.product",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_tmpl_id", "=", self.id)],
        }

    def action_view_pricing_history(self):
        """View pricing history."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Pricing History"),
            "res_model": "product.price.history",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_template_id", "=", self.id)],
        }
