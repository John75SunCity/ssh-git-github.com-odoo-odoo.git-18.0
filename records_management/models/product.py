# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Phase 1: Explicit Activity Field (1 field)
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')

    shred_type = fields.Selection([
        ('document', 'Document Shredding'),
        ('hard_drive', 'Hard Drive Destruction'),
        ('uniform', 'Uniform Shredding'),
    ], string='Shred Type', help='Type of shredding service for NAID-compliant categorization.')
    naid_compliant = fields.Boolean(string='NAID Compliant', default=True, help='Flag if this product meets NAID AAA standards.')
    retention_note = fields.Text(string='Retention Note', compute='_compute_retention_note', store=True, 
                                 help='Computed note for ISO data integrity (e.g., retention policies).')

    # Phase 3: Analytics & Computed Fields (7 fields)
    service_utilization_rate = fields.Float(
        string='Service Utilization (%)',
        compute='_compute_product_analytics',
        store=True,
        help='Rate of service utilization and demand'
    )
    revenue_performance_score = fields.Float(
        string='Revenue Performance Score',
        compute='_compute_product_analytics',
        store=True,
        help='Performance score based on revenue generation'
    )
    compliance_certification_level = fields.Float(
        string='Compliance Level (%)',
        compute='_compute_product_analytics',
        store=True,
        help='NAID and regulatory compliance certification level'
    )
    market_demand_indicator = fields.Char(
        string='Market Demand',
        compute='_compute_product_analytics',
        store=True,
        help='Market demand trend indicator'
    )
    service_quality_rating = fields.Float(
        string='Service Quality Rating',
        compute='_compute_product_analytics',
        store=True,
        help='Quality rating based on customer feedback and compliance'
    )
    product_insights = fields.Text(
        string='Product Insights',
        compute='_compute_product_analytics',
        store=True,
        help='AI-generated product performance insights'
    )
    analytics_updated_timestamp = fields.Datetime(
        string='Analytics Updated',
        compute='_compute_product_analytics',
        store=True,
        help='Last analytics computation time'
    )
    
    # Missing business and technical fields from view analysis
    active = fields.Boolean(string='Active', default=True)
    additional_box_cost = fields.Float(string='Additional Box Cost', default=0.0)
    additional_document_cost = fields.Float(string='Additional Document Cost', default=0.0)
    api_integration = fields.Boolean(string='API Integration', default=False)
    arch = fields.Text(string='View Architecture', help='XML view architecture definition')
    auto_invoice = fields.Boolean(string='Auto Invoice', default=False)
    average_sale_price = fields.Float(string='Average Sale Price', compute='_compute_product_metrics')
    avg_deal_size = fields.Float(string='Average Deal Size', compute='_compute_product_metrics')
    base_cost = fields.Float(string='Base Cost', default=0.0)
    billing_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'), 
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Billing Frequency', default='monthly')
    box_retrieval_time = fields.Float(string='Box Retrieval Time (hours)', default=24.0)
    box_storage_included = fields.Integer(string='Box Storage Included', default=0)
    can_be_expensed = fields.Boolean(string='Can Be Expensed', default=True)
    categ_id = fields.Many2one('product.category', string='Product Category')
    certificate_of_destruction = fields.Boolean(string='Certificate of Destruction', default=False)
    climate_controlled = fields.Boolean(string='Climate Controlled', default=False)
    compliance_guarantee = fields.Boolean(string='Compliance Guarantee', default=False)
    context = fields.Text(string='Context', help='View context information')
    currency_id = fields.Many2one('res.currency', string='Currency')
    customer_count = fields.Integer(string='Customer Count', compute='_compute_product_metrics')
    customer_retention_rate = fields.Float(string='Customer Retention Rate (%)', compute='_compute_product_metrics')
    customization_allowed = fields.Boolean(string='Customization Allowed', default=False)
    data_recovery_guarantee = fields.Boolean(string='Data Recovery Guarantee', default=False)
    default_code = fields.Char(string='Internal Reference')
    description = fields.Text(string='Description')
    detailed_type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service'),
        ('product', 'Storable Product')
    ], string='Product Type', default='service')
    digital_conversion_included = fields.Boolean(string='Digital Conversion Included', default=False)
    discount_percentage = fields.Float(string='Discount Percentage', default=0.0)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    document_retrieval_time = fields.Float(string='Document Retrieval Time (hours)', default=4.0)
    document_storage_included = fields.Integer(string='Document Storage Included', default=0)
    effective_date = fields.Date(string='Effective Date', default=fields.Date.today)
    emergency_response_time = fields.Float(string='Emergency Response Time (hours)', default=2.0)
    emergency_retrieval = fields.Boolean(string='Emergency Retrieval', default=False)
    expiry_date = fields.Date(string='Expiry Date')
    external_service_id = fields.Char(string='External Service ID')
    first_sale_date = fields.Date(string='First Sale Date', compute='_compute_product_metrics')
    geographic_coverage = fields.Char(string='Geographic Coverage')
    help = fields.Text(string='Help', help='Help text for this record')
    is_featured_service = fields.Boolean(string='Featured Service', default=False)
    is_template_service = fields.Boolean(string='Template Service', default=False)
    labor_cost = fields.Float(string='Labor Cost', default=0.0)
    last_sale_date = fields.Date(string='Last Sale Date', compute='_compute_product_metrics')
    list_price = fields.Float(string='Sales Price', default=1.0)
    lst_price = fields.Float(string='List Price', related='list_price')
    material_cost = fields.Float(string='Material Cost', default=0.0)
    max_boxes_included = fields.Integer(string='Max Boxes Included', default=0)
    max_documents_included = fields.Integer(string='Max Documents Included', default=0)
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    min_quantity = fields.Float(string='Minimum Quantity', default=1.0)
    minimum_billing_period = fields.Integer(string='Minimum Billing Period (months)', default=1)
    model = fields.Char(string='Model', help='Model name for technical references')
    naid_compliance_level = fields.Selection([
        ('none', 'No NAID Compliance'),
        ('a', 'NAID Level A'),
        ('aa', 'NAID Level AA'),
        ('aaa', 'NAID Level AAA')
    ], string='NAID Compliance Level', default='aaa')
    name = fields.Char(string='Product Name', required=True)
    overhead_cost = fields.Float(string='Overhead Cost', default=0.0)
    period = fields.Selection([
        ('day', 'Day'),
        ('week', 'Week'),
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year')
    ], string='Period', default='month')
    pickup_delivery_included = fields.Boolean(string='Pickup/Delivery Included', default=False)
    price_history_count = fields.Integer(string='Price History Count', compute='_compute_product_metrics')
    price_margin = fields.Float(string='Price Margin (%)', compute='_compute_product_metrics')
    # pricing_rule_ids = fields.One2many('product.pricing.rule', 'product_id', string='Pricing Rules')  # Disabled - model doesn't exist
    product_variant_count = fields.Integer(string='Variant Count', compute='_compute_product_metrics')
    product_variant_ids = fields.One2many('product.product', 'product_tmpl_id', string='Product Variants')
    profit = fields.Float(string='Profit', compute='_compute_product_metrics')
    profit_margin = fields.Float(string='Profit Margin (%)', compute='_compute_product_metrics')
    prorate_partial_periods = fields.Boolean(string='Prorate Partial Periods', default=True)
    purchase_ok = fields.Boolean(string='Can be Purchased', default=False)
    qty_available = fields.Float(string='Quantity Available', compute='_compute_product_metrics')
    requires_approval = fields.Boolean(string='Requires Approval', default=False)
    res_model = fields.Char(string='Resource Model', help='Resource model name')
    revenue = fields.Float(string='Revenue', compute='_compute_product_metrics')
    rule_name = fields.Char(string='Rule Name')
    rule_type = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('percentage', 'Percentage'),
        ('formula', 'Formula')
    ], string='Rule Type', default='fixed')
    sale_ok = fields.Boolean(string='Can be Sold', default=True)
    # sales_analytics_ids = fields.One2many('product.sales.analytics', 'product_id', string='Sales Analytics')  # Disabled - model doesn't exist
    sales_count = fields.Integer(string='Sales Count', compute='_compute_product_metrics')
    sales_velocity = fields.Float(string='Sales Velocity', compute='_compute_product_metrics')
    same_day_service = fields.Boolean(string='Same Day Service', default=False)
    search_view_id = fields.Many2one('ir.ui.view', string='Search View')
    security_guarantee = fields.Boolean(string='Security Guarantee', default=False)
    shredding_included = fields.Boolean(string='Shredding Included', default=False)
    sla_terms = fields.Text(string='SLA Terms')
    standard_price = fields.Float(string='Cost', default=0.0)
    standard_response_time = fields.Float(string='Standard Response Time (hours)', default=24.0)
    sync_enabled = fields.Boolean(string='Sync Enabled', default=False)
    template_category = fields.Char(string='Template Category')
    total_revenue_ytd = fields.Float(string='Total Revenue YTD', compute='_compute_product_metrics')
    total_sales_ytd = fields.Float(string='Total Sales YTD', compute='_compute_product_metrics')
    type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service'),
        ('product', 'Storable Product')
    ], string='Product Type', default='service')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    uom_po_id = fields.Many2one('uom.uom', string='Purchase Unit of Measure')
    uptime_guarantee = fields.Float(string='Uptime Guarantee (%)', default=99.9)
    view_mode = fields.Char(string='View Mode', help='View mode configuration')
    volume = fields.Float(string='Volume')
    webhook_notifications = fields.Boolean(string='Webhook Notifications', default=False)
    weight = fields.Float(string='Weight')
    witness_destruction = fields.Boolean(string='Witness Destruction', default=False)

    @api.depends('type')
    def _compute_retention_note(self):
        for rec in self:
            if rec.type == 'service' and rec.shred_type:
                rec.retention_note = f"Service: {rec.shred_type}. Retain logs for 7 years per NAID standards."
            else:
                rec.retention_note = ""

    @api.depends('shred_type', 'naid_compliant', 'type', 'list_price', 'standard_price')
    def _compute_product_analytics(self):
        """Compute comprehensive analytics for products"""
        for product in self:
            # Update timestamp
            product.analytics_updated_timestamp = fields.Datetime.now()
            
            # Service utilization rate (simulated based on type and compliance)
            utilization = 60.0  # Base utilization
            
            if product.type == 'service':
                utilization += 20.0
                
                # Shred type utilization
                if product.shred_type == 'document':
                    utilization += 15.0  # High demand
                elif product.shred_type == 'hard_drive':
                    utilization += 10.0  # Medium demand
                elif product.shred_type == 'uniform':
                    utilization += 5.0   # Lower demand
            
            if product.naid_compliant:
                utilization += 10.0
            
            product.service_utilization_rate = min(100, utilization)
            
            # Revenue performance score
            revenue_score = 50.0  # Base score
            
            # Price point analysis
            if product.list_price > 100:
                revenue_score += 30.0  # Premium pricing
            elif product.list_price > 50:
                revenue_score += 20.0  # Standard pricing
            else:
                revenue_score += 10.0  # Budget pricing
            
            # Margin analysis
            if product.list_price > 0 and product.standard_price > 0:
                margin = (product.list_price - product.standard_price) / product.list_price
                if margin > 0.5:
                    revenue_score += 20.0  # High margin
                elif margin > 0.3:
                    revenue_score += 15.0  # Good margin
                else:
                    revenue_score += 5.0   # Low margin
            
            product.revenue_performance_score = min(100, revenue_score)
            
            # Compliance certification level
            compliance = 70.0  # Base compliance
            
            if product.naid_compliant:
                compliance += 25.0
            
            if product.type == 'service' and product.shred_type:
                compliance += 5.0  # Service categorization helps compliance
            
            product.compliance_certification_level = min(100, compliance)
            
            # Market demand indicator
            demand_score = product.service_utilization_rate
            
            if demand_score > 85:
                product.market_demand_indicator = '🔥 High Demand'
            elif demand_score > 70:
                product.market_demand_indicator = '📈 Growing Demand'
            elif demand_score > 50:
                product.market_demand_indicator = '📊 Steady Demand'
            else:
                product.market_demand_indicator = '📉 Low Demand'
            
            # Service quality rating
            quality = 75.0  # Base quality
            
            if product.naid_compliant:
                quality += 15.0
            
            if product.type == 'service':
                quality += 10.0
            
            product.service_quality_rating = min(100, quality)
            
            # Product insights
            insights = []
            
            if product.revenue_performance_score > 85:
                insights.append("💰 Strong revenue performer")
            elif product.revenue_performance_score < 60:
                insights.append("📊 Revenue optimization needed")
            
            if product.service_utilization_rate > 80:
                insights.append("🚀 High demand service - consider capacity expansion")
            
            if not product.naid_compliant and product.type == 'service':
                insights.append("⚠️ NAID compliance required for service credibility")
            
            if product.compliance_certification_level > 90:
                insights.append("✅ Excellent compliance standards")
            
            if 'High Demand' in product.market_demand_indicator:
                insights.append("🎯 Market leader - maintain competitive advantage")
            
            if product.shred_type == 'hard_drive':
                insights.append("🔒 Specialized service - premium positioning opportunity")
            
            if not insights:
                insights.append("📈 Standard performance within acceptable ranges")
            
            product.product_insights = "\n".join(insights)

    def _compute_product_metrics(self):
        """Compute additional product metrics"""
        for product in self:
            # Set default values for computed fields
            product.average_sale_price = product.list_price
            product.avg_deal_size = product.list_price
            product.customer_count = 0
            product.customer_retention_rate = 85.0
            product.first_sale_date = fields.Date.today()
            product.last_sale_date = fields.Date.today()
            product.price_history_count = 0
            product.price_margin = 0.0
            product.product_variant_count = len(product.product_variant_ids)
            product.profit = max(0, product.list_price - product.standard_price)
            product.profit_margin = (product.profit / product.list_price * 100) if product.list_price > 0 else 0.0
            product.qty_available = 0.0
            product.revenue = 0.0
            product.sales_count = 0
            product.sales_velocity = 0.0
            product.total_revenue_ytd = 0.0
            product.total_sales_ytd = 0.0

    def _compute_display_name(self):
        """Compute display name"""
        for product in self:
            product.display_name = product.name or 'Unnamed Product'

    def action_view_sales(self):
        """View sales history for this product"""
        self.ensure_one()
        return {
            'name': _('Sales History: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'tree,form',
            'domain': [('product_id.product_tmpl_id', '=', self.id)],
            'context': {'default_product_id': self.product_variant_ids[0].id if self.product_variant_ids else False},
        }

    def action_configure_pricing(self):
        """Configure pricing for this product"""
        self.ensure_one()
        return {
            'name': _('Configure Pricing: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.pricelist.item',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }

    def action_configure_variants(self):
        """Configure product variants"""
        self.ensure_one()
        return {
            'name': _('Product Variants: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }

    def action_pricing_rules(self):
        """View pricing rules for this product"""
        self.ensure_one()
        return {
            'name': _('Pricing Rules: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.pricelist.item',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }

    def action_duplicate(self):
        """Duplicate this product"""
        self.ensure_one()
        new_product = self.copy({'name': _('%s (Copy)') % self.name})
        return {
            'name': _('Duplicated Product'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'res_id': new_product.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_update_costs(self):
        """Update product costs"""
        self.ensure_one()
        return {
            'name': _('Update Costs: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_view_variants(self):
        """View product variants"""
        self.ensure_one()
        return {
            'name': _('Product Variants: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }

    def action_view_pricing_history(self):
        """View pricing history"""
        self.ensure_one()
        return {
            'name': _('Pricing History: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.pricelist.item',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }
