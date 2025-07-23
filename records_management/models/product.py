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
