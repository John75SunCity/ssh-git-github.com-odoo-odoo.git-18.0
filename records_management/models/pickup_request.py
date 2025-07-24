# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
from odoo import models, fields, api

class PickupRequest(models.Model):
    """Model for pickup requests with workflow enhancements."""
    _name = 'pickup.request'
    _description = 'Pickup Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Name',
        required=True,
        default='New'
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True
    )
    box_id = fields.Many2one(
        'records.box',
        string='Related Box',
        help='Box associated with this pickup request'
    )
    request_date = fields.Date(
        string='Request Date',
        default=fields.Date.context_today,
        required=True
    )
    request_item_ids = fields.One2many('pickup.request.item', 'request_id', string='Request Items')
        'pickup.request.item',
        'pickup_id',
        string='Request Items'
    )
    notes = fields.Text(string='Notes')
    
    # Phase 2: Audit & Compliance Fields (12 fields)
    audit_required = fields.Boolean(
        string='Audit Required',
        default=False
    )
    compliance_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review')
    ], string='Compliance Status', default='pending')
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Risk Level', default='low')
    regulatory_requirement = fields.Text(string='Regulatory Requirement')
    approval_required = fields.Boolean(
        string='Approval Required',
        default=False
    )
    approved_by = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Datetime(string='Approval Date')
    security_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string='Security Level', default='internal')
    chain_of_custody = fields.Text(string='Chain of Custody')
    pickup_authorization = fields.Char(string='Pickup Authorization')
    transport_requirements = fields.Text(string='Transport Requirements')
    compliance_notes = fields.Text(string='Compliance Notes')
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        digits=(16, 2)
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot',
        domain="[('product_id', '=', product_id)]"
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='draft', string='Status')
    scheduled_date = fields.Date(string='Scheduled Date')
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse'
    )
    driver_id = fields.Many2one(
        'res.partner',
        string='Driver',
        domain="[('is_company', '=', False)]"
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehicle'
    )
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High')
    ], default='0', string='Priority')

    # Phase 3: Analytics & Computed Fields (9 fields)
    pickup_efficiency_score = fields.Float(
        string='Pickup Efficiency Score (%)',
        compute='_compute_pickup_analytics',
        store=True,
        help='Overall efficiency score for pickup operations'
    )
    fulfillment_time_hours = fields.Float(
        string='Fulfillment Time (Hours)',
        compute='_compute_pickup_analytics',
        store=True,
        help='Time from request to completion'
    )
    route_optimization_score = fields.Float(
        string='Route Optimization Score',
        compute='_compute_pickup_analytics',
        store=True,
        help='Route efficiency and optimization rating'
    )
    cost_per_pickup = fields.Float(
        string='Cost per Pickup ($)',
        compute='_compute_pickup_analytics',
        store=True,
        help='Estimated cost for this pickup operation'
    )
    customer_satisfaction_rating = fields.Float(
        string='Customer Satisfaction Rating',
        compute='_compute_pickup_analytics',
        store=True,
        help='Predicted customer satisfaction score'
    )
    operational_complexity = fields.Float(
        string='Operational Complexity (1-10)',
        compute='_compute_pickup_analytics',
        store=True,
        help='Complexity assessment for this pickup'
    )
    resource_utilization = fields.Float(
        string='Resource Utilization (%)',
        compute='_compute_pickup_analytics',
        store=True,
        help='Efficiency of resource allocation'
    )
    pickup_performance_insights = fields.Text(
        string='Performance Insights',
        compute='_compute_pickup_analytics',
        store=True,
        help='AI-generated operational insights'
    )
    analytics_timestamp = fields.Datetime(
        string='Analytics Updated',
        compute='_compute_pickup_analytics',
        store=True,
        help='Last analytics computation time'
    )
    signature = fields.Binary(string='Signature')
    signed_by = fields.Many2one('res.users', string='Signed By')
    signature_date = fields.Datetime(string='Signature Date')
    completion_date = fields.Date(string='Completion Date')

    @api.depends('state', 'priority', 'request_date', 'scheduled_date', 'completion_date', 
                 'quantity', 'security_level', 'risk_level', 'compliance_status')
    def _compute_pickup_analytics(self):
        """Compute comprehensive analytics for pickup requests"""
        for pickup in self:
            # Update timestamp
            pickup.analytics_timestamp = fields.Datetime.now()
            
            # Pickup efficiency score
            efficiency_factors = []
            
            # State progression efficiency
            if pickup.state == 'completed':
                efficiency_factors.append(100)
            elif pickup.state == 'scheduled':
                efficiency_factors.append(80)
            elif pickup.state == 'confirmed':
                efficiency_factors.append(60)
            else:
                efficiency_factors.append(40)
            
            # Priority handling efficiency
            if pickup.priority == '1':  # High priority
                if pickup.state in ['scheduled', 'completed']:
                    efficiency_factors.append(95)
                else:
                    efficiency_factors.append(70)
            else:
                efficiency_factors.append(85)
            
            # Compliance efficiency
            if pickup.compliance_status == 'approved':
                efficiency_factors.append(90)
            elif pickup.compliance_status == 'under_review':
                efficiency_factors.append(70)
            else:
                efficiency_factors.append(50)
            
            pickup.pickup_efficiency_score = sum(efficiency_factors) / len(efficiency_factors)
            
            # Fulfillment time calculation
            if pickup.completion_date and pickup.request_date:
                time_diff = (pickup.completion_date - pickup.request_date).days
                pickup.fulfillment_time_hours = time_diff * 24  # Convert to hours
            elif pickup.scheduled_date and pickup.request_date:
                time_diff = (pickup.scheduled_date - pickup.request_date).days
                pickup.fulfillment_time_hours = time_diff * 24
            else:
                pickup.fulfillment_time_hours = 0.0
            
            # Route optimization score (simulated based on factors)
            route_score = 70.0  # Base score
            
            if pickup.warehouse_id:
                route_score += 15.0  # Warehouse assignment helps
            if pickup.driver_id:
                route_score += 10.0  # Driver assignment helps
            if pickup.vehicle_id:
                route_score += 5.0   # Vehicle assignment helps
            
            pickup.route_optimization_score = min(100, route_score)
            
            # Cost per pickup estimation
            base_cost = 25.0  # Base pickup cost
            
            # Quantity factor
            if pickup.quantity > 50:
                base_cost += pickup.quantity * 0.5
            elif pickup.quantity > 20:
                base_cost += pickup.quantity * 0.3
            else:
                base_cost += pickup.quantity * 0.2
            
            # Security level factor
            security_costs = {
                'public': 0,
                'internal': 5,
                'confidential': 15,
                'restricted': 30
            }
            base_cost += security_costs.get(pickup.security_level, 0)
            
            pickup.cost_per_pickup = base_cost
            
            # Customer satisfaction rating
            satisfaction = 75.0  # Base satisfaction
            
            if pickup.state == 'completed':
                satisfaction += 15.0
            elif pickup.state == 'cancelled':
                satisfaction -= 30.0
            
            if pickup.priority == '1' and pickup.state in ['scheduled', 'completed']:
                satisfaction += 10.0
            
            if pickup.fulfillment_time_hours <= 48:  # Within 2 days
                satisfaction += 10.0
            elif pickup.fulfillment_time_hours > 168:  # More than a week
                satisfaction -= 15.0
            
            pickup.customer_satisfaction_rating = min(100, max(0, satisfaction))
            
            # Operational complexity assessment
            complexity = 3.0  # Base complexity
            
            # Security level complexity
            security_complexity = {
                'public': 0,
                'internal': 1,
                'confidential': 2,
                'restricted': 3
            }
            complexity += security_complexity.get(pickup.security_level, 0)
            
            # Risk level complexity
            risk_complexity = {
                'low': 0,
                'medium': 1,
                'high': 2,
                'critical': 3
            }
            complexity += risk_complexity.get(pickup.risk_level, 0)
            
            # Quantity complexity
            if pickup.quantity > 100:
                complexity += 1
            
            pickup.operational_complexity = min(10, complexity)
            
            # Resource utilization calculation
            utilization = 60.0  # Base utilization
            
            if pickup.driver_id and pickup.vehicle_id:
                utilization += 25.0
            elif pickup.driver_id or pickup.vehicle_id:
                utilization += 15.0
            
            if pickup.warehouse_id:
                utilization += 10.0
            
            pickup.resource_utilization = min(100, utilization)
            
            # Performance insights
            insights = []
            
            if pickup.pickup_efficiency_score > 85:
                insights.append("✅ High efficiency pickup operation")
            elif pickup.pickup_efficiency_score < 65:
                insights.append("⚠️ Below target efficiency - process review needed")
            
            if pickup.fulfillment_time_hours > 120:  # More than 5 days
                insights.append("⏰ Extended fulfillment time - expedite processing")
            
            if pickup.cost_per_pickup > 100:
                insights.append("💰 High cost pickup - optimize resource allocation")
            
            if pickup.operational_complexity > 7:
                insights.append("🔧 Complex operation - additional oversight required")
            
            if pickup.customer_satisfaction_rating > 90:
                insights.append("😊 Excellent customer satisfaction metrics")
            
            if pickup.resource_utilization < 60:
                insights.append("📊 Low resource utilization - optimize assignments")
            
            if not insights:
                insights.append("📈 Standard operation within normal parameters")
            
            pickup.pickup_performance_insights = "\n".join(insights)

    @api.model_create_multi
    def create(self, vals_list: List[dict]) -> 'PickupRequest':
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                sequence = self.env['ir.sequence'].next_by_code(
                    'pickup.request'
                )
                vals['name'] = sequence or 'New'
        return super().create(vals_list)

    def action_confirm(self) -> bool:
        return self.write({'state': 'confirmed'})

    def action_schedule(self) -> bool:
        if not self.scheduled_date:
            self.scheduled_date = fields.Date.context_today(self)
        return self.write({'state': 'scheduled'})

    def action_complete(self) -> bool:
        self.completion_date = fields.Date.context_today(self)
        return self.write({'state': 'completed'})

    def action_cancel(self) -> bool:
        return self.write({'state': 'cancelled'})

    def action_view_items(self):
        """View pickup request items"""
        self.ensure_one()
        return {
            'name': _('Pickup Items'),
            'type': 'ir.actions.act_window',
            'res_model': 'pickup.request.item',
            'view_mode': 'tree,form',
            'domain': [('pickup_request_id', '=', self.id)],
            'context': {'default_pickup_request_id': self.id},
        }

    def action_reschedule(self):
        """Reschedule pickup request"""
        self.ensure_one()
        return {
            'name': _('Reschedule Pickup'),
            'type': 'ir.actions.act_window',
            'res_model': 'pickup.reschedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_pickup_id': self.id},
        }

    def action_assign_driver(self):
        """Assign driver to pickup request"""
        self.ensure_one()
        return {
            'name': _('Assign Driver'),
            'type': 'ir.actions.act_window',
            'res_model': 'pickup.driver.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_pickup_id': self.id},
        }

    def action_print_route(self):
        """Print pickup route"""
        self.ensure_one()
        return {
            'name': _('Print Route'),
            'type': 'ir.actions.report',
            'report_name': 'records_management.pickup_route_report',
            'report_type': 'qweb-pdf',
            'report_file': 'records_management.pickup_route_report',
            'context': {'active_ids': [self.id]},
        }

    def action_send_notification(self):
        """Send pickup notification"""
        self.ensure_one()
        return {
            'name': _('Send Notification'),
            'type': 'ir.actions.act_window',
            'res_model': 'pickup.notification.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_pickup_id': self.id},
        }

    @api.onchange('customer_id')
    def _onchange_customer_id(self) -> None:
        """
        Update domain for driver and vehicle based on customer
        for better UI.
        """
        return {
            'domain': {
                'driver_id': [('parent_id', '=', self.customer_id.id)]
            }
        }
