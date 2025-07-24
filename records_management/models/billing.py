# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Billing(models.Model):
    _name = 'records.billing'
    _description = 'General Billing Model'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'invoice_date desc'

    # Phase 1: Explicit Activity Field (1 field)
    activity_ids = fields.One2many('mail.activity', compute='_compute_activity_ids', string='Activities')

    name = fields.Char('Reference', required=True)
    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    department_id = fields.Many2one('records.department', 'Department')
    invoice_date = fields.Date('Invoice Date', default=fields.Date.today)
    amount_total = fields.Float('Total Amount')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    
    # Invoice integration
    invoice_id = fields.Many2one('account.move', 'Invoice', readonly=True)

    # Phase 3: Analytics & Computed Fields (7 fields)
    billing_performance_score = fields.Float(
        string='Billing Performance Score (%)',
        compute='_compute_billing_analytics',
        store=True,
        help='Overall billing performance and efficiency score'
    )
    collection_efficiency_rate = fields.Float(
        string='Collection Efficiency (%)',
        compute='_compute_billing_analytics',
        store=True,
        help='Efficiency rate of payment collection'
    )
    revenue_impact_assessment = fields.Float(
        string='Revenue Impact ($)',
        compute='_compute_billing_analytics',
        store=True,
        help='Assessment of revenue impact from this billing'
    )
    payment_cycle_duration = fields.Float(
        string='Payment Cycle (Days)',
        compute='_compute_billing_analytics',
        store=True,
        help='Expected or actual payment cycle duration'
    )
    billing_risk_indicator = fields.Char(
        string='Risk Indicator',
        compute='_compute_billing_analytics',
        store=True,
        help='Risk assessment indicator for collection'
    )
    billing_insights_summary = fields.Text(
        string='Billing Insights',
        compute='_compute_billing_analytics',
        store=True,
        help='AI-generated billing insights and recommendations'
    )
    analytics_last_update = fields.Datetime(
        string='Analytics Updated',
        compute='_compute_billing_analytics',
        store=True,
        help='Last analytics computation timestamp'
    )

    @api.depends('state', 'amount_total', 'invoice_date', 'partner_id', 'invoice_id')
    def _compute_billing_analytics(self):
        """Compute comprehensive analytics for billing records"""
        for billing in self:
            # Update timestamp
            billing.analytics_last_update = fields.Datetime.now()
            
            # Billing performance score
            performance = 50.0  # Base performance
            
            # State progression performance
            state_scores = {
                'draft': 20.0,
                'confirmed': 40.0,
                'invoiced': 70.0,
                'paid': 100.0,
                'cancelled': 0.0
            }
            performance += state_scores.get(billing.state, 20.0)
            
            # Invoice generation efficiency
            if billing.invoice_id:
                performance += 15.0
            
            # Amount impact
            if billing.amount_total > 1000:
                performance += 10.0  # High value billing
            elif billing.amount_total > 500:
                performance += 5.0   # Medium value billing
            
            billing.billing_performance_score = min(100, performance)
            
            # Collection efficiency rate
            collection = 60.0  # Base collection efficiency
            
            if billing.state == 'paid':
                collection = 100.0  # Perfect collection
            elif billing.state == 'invoiced':
                collection = 80.0   # Good progress
            elif billing.state == 'confirmed':
                collection = 60.0   # On track
            elif billing.state == 'cancelled':
                collection = 0.0    # No collection
            
            billing.collection_efficiency_rate = collection
            
            # Revenue impact assessment
            impact = billing.amount_total or 0.0
            
            # Apply state modifier
            if billing.state == 'paid':
                impact *= 1.0  # Full impact
            elif billing.state == 'invoiced':
                impact *= 0.9  # High probability
            elif billing.state == 'confirmed':
                impact *= 0.8  # Good probability
            elif billing.state == 'draft':
                impact *= 0.6  # Moderate probability
            else:
                impact *= 0.0  # No impact
            
            billing.revenue_impact_assessment = impact
            
            # Payment cycle duration
            if billing.state == 'paid' and billing.invoice_date:
                # For paid bills, calculate actual cycle (simulated)
                billing.payment_cycle_duration = 30.0  # Standard 30 days
            elif billing.state in ['invoiced', 'confirmed']:
                # Estimate based on customer and amount
                if billing.amount_total > 1000:
                    billing.payment_cycle_duration = 45.0  # Longer for high amounts
                else:
                    billing.payment_cycle_duration = 30.0  # Standard cycle
            else:
                billing.payment_cycle_duration = 0.0
            
            # Billing risk indicator
            if billing.state == 'cancelled':
                billing.billing_risk_indicator = '🚨 Cancelled - No Revenue'
            elif billing.state == 'paid':
                billing.billing_risk_indicator = '✅ Collected Successfully'
            elif billing.amount_total > 2000:
                billing.billing_risk_indicator = '⚠️ High Value - Monitor Closely'
            elif billing.payment_cycle_duration > 40:
                billing.billing_risk_indicator = '📅 Extended Cycle - Follow Up'
            else:
                billing.billing_risk_indicator = '📊 Standard Risk Level'
            
            # Billing insights summary
            insights = []
            
            if billing.billing_performance_score > 85:
                insights.append("✅ High-performing billing record")
            elif billing.billing_performance_score < 60:
                insights.append("⚠️ Below target performance - review process")
            
            if billing.state == 'draft' and billing.invoice_date:
                insights.append("📋 Ready for confirmation - advance to next stage")
            
            if billing.amount_total > 1500:
                insights.append("💰 High-value billing - priority collection tracking")
            
            if billing.collection_efficiency_rate == 100:
                insights.append("🎯 Perfect collection - excellent performance")
            
            if billing.payment_cycle_duration > 45:
                insights.append("⏰ Extended payment cycle - consider follow-up")
            
            if billing.state == 'invoiced' and not billing.invoice_id:
                insights.append("🔄 Invoice generation pending")
            
            if billing.department_id:
                insights.append("🏢 Department-specific billing - targeted service")
            
            if not insights:
                insights.append("📈 Standard billing processing")
            
            billing.billing_insights_summary = "\n".join(insights)

    def action_generate_invoice(self):
        """Generate invoice for this billing"""
        self.ensure_one()
        if self.invoice_id:
            return self._show_existing_invoice()
        
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': self.invoice_date,
            'ref': self.name,
            'invoice_line_ids': [(0, 0, {
                'name': f'Records Management Services - {self.name}',
                'quantity': 1,
                'price_unit': self.amount_total,
            })]
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.write({
            'invoice_id': invoice.id,
            'state': 'invoiced'
        })
        
        self.message_post(body=_('Invoice generated: %s') % invoice.name)
        return self._show_existing_invoice()

    def action_view_analytics(self):
        """View analytics for billing"""
        self.ensure_one()
        return {
            'name': _('Billing Analytics'),
            'type': 'ir.actions.act_window',
            'res_model': 'billing.analytics.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_billing_id': self.id},
        }

    def action_view_billing_history(self):
        """View billing history for customer"""
        self.ensure_one()
        return {
            'name': _('Billing History: %s') % self.partner_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.billing',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'default_partner_id': self.partner_id.id},
        }

    def action_configure_rates(self):
        """Configure billing rates"""
        self.ensure_one()
        return {
            'name': _('Configure Billing Rates'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.billing.config',
            'view_mode': 'tree,form',
            'target': 'current',
        }

    def action_test_billing(self):
        """Test billing calculation"""
        self.ensure_one()
        return {
            'name': _('Test Billing Calculation'),
            'type': 'ir.actions.act_window',
            'res_model': 'billing.test.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_billing_id': self.id},
        }

    def action_duplicate(self):
        """Duplicate this billing record"""
        self.ensure_one()
        copy = self.copy({'name': f'{self.name} (Copy)', 'state': 'draft', 'invoice_id': False})
        return {
            'name': _('Billing Copy'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.billing',
            'res_id': copy.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_invoices(self):
        """View invoices for this billing"""
        self.ensure_one()
        if not self.invoice_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'No invoice generated yet.',
                    'type': 'warning',
                }
            }
        
        return {
            'name': _('Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_revenue(self):
        """View revenue analytics"""
        self.ensure_one()
        return {
            'name': _('Revenue Analytics'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'view_mode': 'graph,pivot,tree',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'group_by': ['date']},
        }

    def action_view_invoice(self):
        """View invoice (context action)"""
        invoice_id = self.env.context.get('invoice_id')
        if invoice_id:
            return {
                'name': _('Invoice'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': invoice_id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False

    def _show_existing_invoice(self):
        """Show the existing invoice"""
        return {
            'name': _('Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.billing') or _('New')
        return super().create(vals_list)

    # Compute method for activity_ids One2many field
    def _compute_activity_ids(self):
        """Compute activities for this record"""
        for record in self:
            record.activity_ids = self.env["mail.activity"].search([
                ("res_model", "=", "records.billing"),
                ("res_id", "=", record.id)
            ])
