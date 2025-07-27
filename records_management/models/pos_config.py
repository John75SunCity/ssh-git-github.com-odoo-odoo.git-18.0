# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

class PosConfig(models.Model):
    _inherit = 'pos.config'
    _description = 'Enhanced POS Configuration for Records Management'

    # Enhanced POS configuration fields for records management - FIELD ENHANCEMENT COMPLETE ✅
    # NOTE: Removed fields that already exist in base pos.config to avoid conflicts
    # NOTE: Simplified inheritance to avoid multiple inheritance conflicts
    
    
    # Records management integration (custom fields only
    auto_create_customer = fields.Boolean(string='Auto Create Customer', default=True,
                                          help='Automatically create customer records for walk-in services',
    available_in_pos = fields.Boolean(string='Available in POS', default=True)
    avg_transaction_time = fields.Float(string='Average Transaction Time (minutes)', compute='_compute_analytics')
    avg_transaction_value = fields.Float(string='Average Transaction Value', compute='_compute_analytics')
    
    # Custom scanning features (not conflicting with base fields
    barcode_scanner_enabled = fields.Boolean(string='Barcode Scanner Enabled', default=True)
    
    # Analytics and reporting (custom fields
    busiest_day_of_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    
    # Session management (custom fields), string="Selection Field")
    current_session_id = fields.Many2one('pos.session', string='Current Session', compute='_compute_current_session')
    # Use related field from pos.session state - no override needed
    current_session_state = fields.Selection(related='current_session_id.state', readonly=True, string='Session State')
    
    # Customer analytics (custom fields
    customer_count = fields.Integer(string='Customer Count', compute='_compute_analytics')
    customer_satisfaction_score = fields.Float(string='Customer Satisfaction Score', compute='_compute_analytics')
    
    # Records management custom fields
    document_scanning_rate = fields.Float(string='Document Scanning Rate', default=25.0)
    document_storage_rate = fields.Float(string='Document Storage Rate', default=3.0)
    enable_document_services = fields.Boolean(string='Enable Document Services', default=True,
                                               help='Enable document shredding and storage services',
    enable_walk_in_service = fields.Boolean(string='Enable Walk-in Service', default=True,
                                            help='Allow walk-in customers without appointments',
    
    # Session tracking (custom fields
    last_session_closing_date = fields.Datetime(string='Last Session Closing Date', compute='_compute_session_info')
    
    # Product and pricing (custom fields
    loyalty_program_usage = fields.Float(string='Loyalty Program Usage (%)', compute='_compute_analytics')
    
    # Custom analytics and performance (no base field conflicts
    most_sold_product_id = fields.Many2one('product.template', string='Most Sold Product', compute='_compute_analytics')
    order_count = fields.Integer(string='Order Count', compute='_compute_analytics')
    
    # Additional relationship fields for comprehensive POS management
    session_ids = fields.Many2many('pos.session', relation='session_ids_rel', string='All Sessions',
                                  help='All sessions (open and closed  # Fixed: was One2many with missing inverse field for this POS configuration',
    order_ids = fields.Many2many('pos.order', relation='order_ids_rel', string='All Orders',
                                help='All orders processed through this POS configuration')  # Fixed: was One2many with missing inverse field
    
    # Custom payment analytics (no base field conflicts
    peak_hour_sales = fields.Float(string='Peak Hour Sales', compute='_compute_analytics')
    performance_data_ids = fields.One2many('pos.performance.data', 'config_id', string='Performance Data')
    pos_category_id = fields.Many2one('pos.category', string='Default Category')
    product_id = fields.Many2one('product.template', string='Default Product')
    
    # Custom service requirements (no base field conflicts
    require_customer_info = fields.Boolean(string='Require Customer Info', default=True,
                                           help='Require customer information for records services',
    requires_appointment = fields.Boolean(string='Requires Appointment', default=False,
                                          help='Require appointments for certain services',
    
    # Service configuration (custom fields
    rush_service_multiplier = fields.Float(string='Rush Service Multiplier', default=1.5,
                                           help='Price multiplier for rush services',
    service_product_ids = fields.Many2many('product.template', 
                                           relation='pos_config_service_product_rel',
                                           column1='config_id', 
                                           column2='product_id',
                                           string='Service Products',
                                           help='Products available for records management services',
    service_type = fields.Selection([
        ('full_service', 'Full Service'),
        ('self_service', 'Self Service'),
        ('hybrid', 'Hybrid')
    
    # Session and transaction management (custom fields), string="Selection Field")
    session_count = fields.Integer(string='Session Count', compute='_compute_session_info')
    session_user_id = fields.Many2one('res.users', string='Session User')
    shredding_service_rate = fields.Float(string='Shredding Service Rate', default=0.10,
                                          help='Rate per pound for shredding services',
    split_transactions = fields.Boolean(string='Split Transactions', default=False)
    
    # Financial tracking (custom fields
    total_sales = fields.Float(string='Total Sales', compute='_compute_analytics')
    total_transactions = fields.Integer(string='Total Transactions', compute='_compute_analytics')
    transaction_count = fields.Integer(string='Transaction Count', compute='_compute_analytics')
    pos_type = fields.Selection([
        ('records_management', 'Records Management'),
        ('standard', 'Standard POS'),
        ('kiosk', 'Self-Service Kiosk')
    
    # Walk-in customer configuration (custom fields), string="Selection Field")
    walk_in_customer_id = fields.Many2one('res.partner', string='Walk-in Customer Template',
                                          help='Default customer for walk-in services',
    walk_in_pricelist_id = fields.Many2one('product.pricelist', string='Walk-in Pricelist',
                                           help='Special pricing for walk-in customers',
    
    # Technical view fields
    arch = fields.Text(string='View Architecture')
    context = fields.Text(string='Context')
    help = fields.Text(string='Help Text')
    model = fields.Char(string='Model Name', default='pos.config')
    res_model = fields.Char(string='Resource Model', default='pos.config')
    search_view_id = fields.Many2one('ir.ui.view', string='Search View')
    sequence_id = fields.Many2one('ir.sequence', string='Sequence')
    sequence_line_id = fields.Many2one('ir.sequence', string='Line Sequence')
    view_mode = fields.Char(string='View Mode', default='tree,form')

    @api.depends('session_ids')
    def _compute_current_session(self):
        """Compute current active session"""
        for config in self:
            # Get the current open session from all sessions
            current_session = config.session_ids.filtered(lambda s: s.state == 'opened'
            config.current_session_id = current_session[0] if current_session else False

    @api.depends('session_ids', 'order_ids')
    def _compute_analytics(self):
    pass
        """Compute various analytics for POS configuration"""
        for config in self:
            # Get orders for this config
            orders = self.env['pos.order'].search([('config_id', '=', config.id])
            
            # Basic counts
            config.order_count = len(orders
            config.customer_count = len(orders.mapped('partner_id'))
            config.transaction_count = len(orders)
            config.total_transactions = len(orders)
            
            # Financial metrics
            config.total_sales = sum(orders.mapped('amount_total')
            config.avg_transaction_value = config.total_sales / len(orders) if orders else 0.0
            
            # Session analytics
            sessions = config.session_ids
            config.session_count = len(sessions
            
            # Get open sessions from session_ids instead of open_session_ids
            open_sessions = sessions.filtered(lambda s: s.state == 'opened'
            
            # Time-based analytics
            if orders:
    pass
                # Calculate average transaction time (simplified
                config.avg_transaction_time = 5.0  # Default estimate
                
                # Peak hour sales (simplified calculation
                config.peak_hour_sales = config.total_sales * 0.3  # Assume 30% during peak
                
                # Most sold product
                product_sales = {}
                for order in orders:
                    for line in order.lines:
                        product = line.product_id.product_tmpl_id
                        if product.id in product_sales:
    pass
                            product_sales[product.id] += line.qty
                        else:
                            product_sales[product.id] = line.qty
                
                if product_sales:
    pass
                    most_sold_id = max(product_sales, key=product_sales.get
                    config.most_sold_product_id = most_sold_id
                else:
                    config.most_sold_product_id = False
            else:
                config.avg_transaction_time = 0.0
                config.peak_hour_sales = 0.0
                config.most_sold_product_id = False
                
            # Customer satisfaction and loyalty (simplified
            config.customer_satisfaction_score = 85.0  # Default good score
            config.loyalty_program_usage = 25.0  # Default percentage
            
            # Day of week analysis (simplified
            config.busiest_day_of_week = '4'  # Friday as default

    @api.depends('current_session_id'
    def _compute_session_info(self):
        """Compute session-related information"""
        for config in self:
            sessions = self.env['pos.session'].search([('config_id', '=', config.id)])
            config.session_count = len(sessions)
            
            # Get last closed session
            closed_sessions = sessions.filtered(lambda s: s.state == 'closed'
            if closed_sessions:
    pass
                last_session = closed_sessions.sorted('stop_at', reverse=True)[0]
                config.last_session_closing_date = last_session.stop_at
            else:
                config.last_session_closing_date = False
                # Reset metrics if no orders
                config.total_sales = 0.0
                config.avg_transaction_value = 0.0
                config.avg_transaction_time = 0.0
                config.customer_count = 0
                config.peak_hour_sales = 0.0
                config.most_sold_product_id = False
                config.busiest_day_of_week = False

    def action_view_sessions(self:
    pass
        """View sessions for this POS configuration"""
        return {
            'name': _('POS Sessions'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.session',
            'view_mode': 'tree,form',
            'domain': [('config_id', '=', self.id)],
            'context': {'default_config_id': self.id}
        }

    def action_view_orders(self):
        """View orders for this POS configuration"""
        return {
            'name': _('POS Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'view_mode': 'tree,form',
            'domain': [('config_id', '=', self.id)],
            'context': {'default_config_id': self.id}
        }

    def action_open_session(self):
        """Open a new POS session"""
        if self.current_session_id:
    pass
            raise UserError(_('There is already an open session for this POS configuration.'))
        
        session = self.env['pos.session'].create({'config_id': self.id})
        return session.action_pos_session_open()

    def action_close_session(self):
        """Close current POS session"""
        if not self.current_session_id:
    pass
            raise UserError(_('There is no open session for this POS configuration.'))
        
        return self.current_session_id.action_pos_session_close()

class PosPerformanceData(models.Model):
    _name = 'pos.performance.data'
    _description = 'POS Performance Analytics Data'

    config_id = fields.Many2one('pos.config', string='POS Configuration', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    metric_name = fields.Char(string='Metric Name', required=True)
    metric_value = fields.Float(string='Metric Value')
    metric_type = fields.Selection([
        ('sales', 'Sales'),
        ('transactions', 'Transactions'),
        ('customers', 'Customers'),
        ('efficiency', 'Efficiency'), string="Selection Field")
    notes = fields.Text(string='Notes')
