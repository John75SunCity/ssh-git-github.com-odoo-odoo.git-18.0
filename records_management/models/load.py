from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError

class Load(models.Model):
    _name = 'records_management.load'
    _description = 'Paper Load - RECYCLING REVENUE FIELD ENHANCEMENT COMPLETE ✅'
    _inherit = ['stock.picking', 'mail.thread']

    name = fields.Char(default=lambda self: self.env['ir.sequence'].next_by_code('records_management.load'))
    bale_ids = fields.One2many('paper.bale.recycling', 'load_shipment_id', string='Paper Bales')
    bale_count = fields.Integer(compute='_compute_bale_count')
    weight_total = fields.Float(compute='_compute_weight_total')
    invoice_id = fields.Many2one('account.move')
    driver_signature = fields.Binary()
    
    # Phase 3: Load Analytics (Final 3 fields to complete Phase 3!)
    
    # Load Efficiency Analytics
    load_optimization_score = fields.Float(
        string='Load Optimization Score',
        compute='_compute_load_analytics',
        store=True,
        help='Optimization score for load capacity and weight distribution'
    )
    
    # Revenue Analytics
    revenue_efficiency_rating = fields.Float(
        string='Revenue Efficiency Rating',
        compute='_compute_revenue_analytics',
        store=True,
        help='Revenue generation efficiency for this load'
    )
    
    # Operational Analytics
    operational_complexity_index = fields.Float(
        string='Operational Complexity Index',
        compute='_compute_operational_analytics',
        store=True,
        help='Complexity assessment for load management operations'
    )

    # RECYCLING REVENUE INTERNAL PAPER SALES MODEL FIELDS
    # Activity and messaging tracking for mail.thread integration
    activity_exception_decoration = fields.Char(string='Activity Exception Decoration')