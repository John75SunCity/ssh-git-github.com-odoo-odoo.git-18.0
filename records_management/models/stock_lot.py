# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class StockLot(models.Model):
    _inherit = 'stock.lot'

    # Phase 1: Explicit Activity Field (1 field)
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')

    # Customer tracking for records management
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        help='Customer associated with this lot/serial number'
    )
    
    # Extensions for shredding integration (e.g., link to shredding service)
    shredding_service_id = fields.Many2one(
        'shredding.service',
        string='Shredding Service'
    )

    # Phase 3: Analytics & Computed Fields (6 fields)
    lot_utilization_efficiency = fields.Float(
        string='Utilization Efficiency (%)',
        compute='_compute_lot_analytics',
        store=True,
        help='Efficiency of lot utilization and management'
    )
    service_integration_score = fields.Float(
        string='Service Integration Score',
        compute='_compute_lot_analytics',
        store=True,
        help='Score indicating integration with shredding services'
    )
    lifecycle_stage_indicator = fields.Char(
        string='Lifecycle Stage',
        compute='_compute_lot_analytics',
        store=True,
        help='Current stage in lot lifecycle'
    )
    customer_service_rating = fields.Float(
        string='Customer Service Rating',
        compute='_compute_lot_analytics',
        store=True,
        help='Rating based on customer service delivery'
    )
    lot_insights = fields.Text(
        string='Lot Insights',
        compute='_compute_lot_analytics',
        store=True,
        help='AI-generated insights about lot management'
    )
    analytics_update_timestamp = fields.Datetime(
        string='Analytics Updated',
        compute='_compute_lot_analytics',
        store=True,
        help='Last analytics computation time'
    )

    @api.depends('customer_id', 'shredding_service_id', 'product_id', 'name')
    def _compute_lot_analytics(self):
        """Compute comprehensive analytics for stock lots"""
        for lot in self:
            # Update timestamp
            lot.analytics_update_timestamp = fields.Datetime.now()
            
            # Lot utilization efficiency
            utilization = 60.0  # Base utilization
            
            # Customer assignment efficiency
            if lot.customer_id:
                utilization += 25.0
            
            # Product integration
            if lot.product_id:
                utilization += 15.0
            
            # Naming convention efficiency
            if lot.name and len(lot.name) > 5:
                utilization += 10.0  # Good identification
            
            lot.lot_utilization_efficiency = min(100, utilization)
            
            # Service integration score
            integration = 40.0  # Base integration
            
            if lot.shredding_service_id:
                integration += 40.0  # Connected to shredding service
            
            if lot.customer_id and lot.shredding_service_id:
                integration += 20.0  # Full service integration
            
            lot.service_integration_score = min(100, integration)
            
            # Lifecycle stage indicator
            if lot.shredding_service_id:
                # Check shredding service status
                service = lot.shredding_service_id
                if service.status == 'completed':
                    lot.lifecycle_stage_indicator = '🏁 Service Completed'
                elif service.status == 'in_progress':
                    lot.lifecycle_stage_indicator = '⚡ Service In Progress'
                elif service.status == 'confirmed':
                    lot.lifecycle_stage_indicator = '📋 Service Scheduled'
                else:
                    lot.lifecycle_stage_indicator = '📝 Service Planned'
            elif lot.customer_id:
                lot.lifecycle_stage_indicator = '🏢 Customer Assigned'
            else:
                lot.lifecycle_stage_indicator = '📦 Available Stock'
            
            # Customer service rating
            service_rating = 70.0  # Base rating
            
            if lot.customer_id:
                service_rating += 20.0
            
            if lot.shredding_service_id:
                service_rating += 10.0
            
            lot.customer_service_rating = min(100, service_rating)
            
            # Lot insights
            insights = []
            
            if lot.lot_utilization_efficiency > 85:
                insights.append("✅ Highly efficient lot management")
            elif lot.lot_utilization_efficiency < 60:
                insights.append("⚠️ Low utilization - optimize assignment")
            
            if lot.service_integration_score > 80:
                insights.append("🔗 Excellent service integration")
            
            if not lot.customer_id:
                insights.append("👤 No customer assigned - allocate for service")
            
            if lot.shredding_service_id:
                insights.append("🗂️ Integrated with shredding service workflow")
            else:
                insights.append("📋 Available for service scheduling")
            
            if lot.customer_service_rating > 90:
                insights.append("🌟 Outstanding customer service setup")
            
            if 'Service Completed' in lot.lifecycle_stage_indicator:
                insights.append("🎯 Service lifecycle completed successfully")
            
            if not insights:
                insights.append("📊 Standard lot management")
            
            lot.lot_insights = "\n".join(insights)

    def action_view_customer_lots(self):
        """View all lots for this customer"""
        self.ensure_one()
        return {
            'name': _('Customer Lots'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.customer_id.id)],
            'context': {'default_customer_id': self.customer_id.id},
        }

    def action_schedule_shredding(self):
        """Schedule shredding for this lot"""
        self.ensure_one()
        return {
            'name': _('Schedule Shredding'),
            'type': 'ir.actions.act_window',
            'res_model': 'shredding.schedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lot_id': self.id},
        }

    def action_view_shredding_service(self):
        """View associated shredding service"""
        self.ensure_one()
        if self.shredding_service_id:
            return {
                'name': _('Shredding Service'),
                'type': 'ir.actions.act_window',
                'res_model': 'shredding.service',
                'res_id': self.shredding_service_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False

    def action_update_customer(self):
        """Update customer for this lot"""
        self.ensure_one()
        return {
            'name': _('Update Customer'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_print_label(self):
        """Print lot label"""
        self.ensure_one()
        return {
            'name': _('Print Lot Label'),
            'type': 'ir.actions.report',
            'report_name': 'records_management.lot_label_report',
            'report_type': 'qweb-pdf',
            'report_file': 'records_management.lot_label_report',
            'context': {'active_ids': [self.id]},
        }
