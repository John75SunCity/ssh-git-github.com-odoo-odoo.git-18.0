# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api, _


class RecordsInventoryDashboard(models.Model):
    """Records Inventory Dashboard

    Provides real-time dashboard view of inventory metrics including:
    - Container counts by location and type
    - Customer distribution analysis
    - Capacity utilization metrics  
    - Recent activity summaries
    - Revenue and billing insights
    """
    _name = 'records.inventory.dashboard'
    _description = 'Records Inventory Dashboard'
    _rec_name = 'name'
    _order = 'create_date desc'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string='Dashboard Name',
        required=True,
        default='Inventory Dashboard',
        help='Name for this dashboard view'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,)
    user_id = fields.Many2one(
        'res.users',
        string='Owner',
        default=lambda self: self.env.user,
        required=True,
        help='Dashboard owner/creator'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this dashboard is active'
    )

    # ============================================================================
    # DASHBOARD CONFIGURATION FIELDS
    # ============================================================================
    dashboard_type = fields.Selection([
        ('overview', 'Overview Dashboard'),
        ('location', 'Location-Specific'),
        ('customer', 'Customer-Specific'),
        ('department', 'Department-Specific'),
        ('financial', 'Financial Dashboard'),
        ('operational', 'Operational Dashboard')
    ], string='Dashboard Type', default='overview', required=True,)

    refresh_interval = fields.Integer(
        string='Refresh Interval (minutes)',
        default=5,
        help='Auto-refresh interval in minutes'
    )
    auto_refresh = fields.Boolean(
        string='Auto Refresh',
        default=True,
        help='Enable automatic dashboard refresh'
    )

    # ============================================================================
    # FILTER FIELDS
    # ============================================================================
    location_ids = fields.Many2many(
        'records.location',
        string='Locations',
        help='Specific locations to include in dashboard'
    )
    customer_ids = fields.Many2many(
        'res.partner',
        string='Customers',
        domain=[('is_company', '=', True)],
        help='Specific customers to include in dashboard'
    )
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        help='Specific department filter'
    )
    date_range = fields.Selection([
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('quarter', 'This Quarter'),
        ('year', 'This Year'),
        ('custom', 'Custom Range')
    ], string='Date Range', default='month', required=True,)

    date_from = fields.Date(
        string='From Date',
        help='Start date for custom range'
    )
    date_to = fields.Date(
        string='To Date',
        help='End date for custom range'
    )

    # ============================================================================
    # DASHBOARD WIDGET CONFIGURATION
    # ============================================================================
    show_container_summary = fields.Boolean(
        string='Show Container Summary',
        default=True,
        help='Display container count and type summary'
    )
    show_location_utilization = fields.Boolean(
        string='Show Location Utilization',
        default=True,
        help='Display location capacity and utilization'
    )
    show_customer_distribution = fields.Boolean(
        string='Show Customer Distribution',
        default=True,
        help='Display customer storage distribution'
    )
    show_recent_activity = fields.Boolean(
        string='Show Recent Activity',
        default=True,
        help='Display recent container movements and activities'
    )
    show_financial_metrics = fields.Boolean(
        string='Show Financial Metrics',
        default=False,
        help='Display revenue and billing information'
    )
    show_alerts = fields.Boolean(
        string='Show Alerts',
        default=True,
        help='Display system alerts and notifications'
    )

    # ============================================================================
    # COMPUTED METRICS FIELDS
    # ============================================================================
    total_containers = fields.Integer(
        string='Total Containers',
        compute='_compute_container_metrics',
        help='Total number of containers'
    )
    active_containers = fields.Integer(
        string='Active Containers',
        compute='_compute_container_metrics',
        help='Number of active containers'
    )
    total_volume_cf = fields.Float(
        string='Total Volume (CF)',
        compute='_compute_container_metrics',
        help='Total cubic feet of containers'
    )
    total_customers = fields.Integer(
        string='Total Customers',
        compute='_compute_customer_metrics',
        help='Total number of customers'
    )
    total_locations = fields.Integer(
        string='Total Locations',
        compute='_compute_location_metrics',
        help='Total number of locations'
    )
    average_utilization = fields.Float(
        string='Average Utilization %',
        compute='_compute_location_metrics',
        help='Average location utilization percentage'
    )

    # ============================================================================
    # RECENT ACTIVITY FIELDS
    # ============================================================================
    recent_pickups = fields.Integer(
        string='Recent Pickups',
        compute='_compute_activity_metrics',
        help='Number of recent pickup requests'
    )
    recent_deliveries = fields.Integer(
        string='Recent Deliveries',
        compute='_compute_activity_metrics',
        help='Number of recent deliveries'
    )
    pending_requests = fields.Integer(
        string='Pending Requests',
        compute='_compute_activity_metrics',
        help='Number of pending service requests'
    )

    # ============================================================================
    # FINANCIAL METRICS FIELDS
    # ============================================================================
    monthly_revenue = fields.Monetary(
        string='Monthly Revenue',
        compute='_compute_financial_metrics',
        currency_field='currency_id',
        help='Revenue for current month'
    )
    total_billed_amount = fields.Monetary(
        string='Total Billed',
        compute='_compute_financial_metrics',
        currency_field='currency_id',
        help='Total amount billed'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # ============================================================================
    # ALERT FIELDS
    # ============================================================================
    alert_count = fields.Integer(
        string='Alert Count',
        compute='_compute_alerts',
        help='Number of active alerts'
    )
    critical_alerts = fields.Integer(
        string='Critical Alerts',
        compute='_compute_alerts',
        help='Number of critical alerts'
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('location_ids', 'customer_ids', 'date_from', 'date_to')
    def _compute_container_metrics(self):
        """Compute container-related metrics"""
        for dashboard in self:
            domain = dashboard._get_container_domain()
            
            containers = self.env['records.container'].search(domain)
            dashboard.total_containers = len(containers)
            dashboard.active_containers = len(containers.filtered('active'))
            dashboard.total_volume_cf = sum(containers.mapped('volume') or [0.0])

    @api.depends('location_ids', 'customer_ids')
    def _compute_customer_metrics(self):
        """Compute customer-related metrics"""
        for dashboard in self:
            domain = dashboard._get_container_domain()
            
            containers = self.env['records.container'].search(domain)
            dashboard.total_customers = len(containers.mapped('partner_id'))

    @api.depends('location_ids')
    def _compute_location_metrics(self):
        """Compute location-related metrics"""
        for dashboard in self:
            if dashboard.location_ids:
                locations = dashboard.location_ids
            else:
                locations = self.env['records.location'].search([
                    ('company_id', '=', dashboard.company_id.id)
                ])
            
            dashboard.total_locations = len(locations)
            
            # Calculate average utilization
            utilizations = locations.mapped('utilization_percentage')
            if utilizations:
                dashboard.average_utilization = sum(utilizations) / len(utilizations)
            else:
                dashboard.average_utilization = 0.0

    @api.depends('date_from', 'date_to', 'date_range')
    def _compute_activity_metrics(self):
        """Compute recent activity metrics"""
        for dashboard in self:
            date_from, date_to = dashboard._get_date_range()
            
            # Recent pickup requests
            pickup_domain = [('create_date', '>=', date_from), ('create_date', '<=', date_to)]
            dashboard.recent_pickups = self.env['pickup.request'].search_count(pickup_domain)
            
            # Recent deliveries (could be linked to different model)
            dashboard.recent_deliveries = 0  # Placeholder
            
            # Pending requests
            dashboard.pending_requests = self.env['portal.request'].search_count([
                ('state', 'in', ['draft', 'submitted'])
            ])

    @api.depends('date_from', 'date_to', 'date_range')
    def _compute_financial_metrics(self):
        """Compute financial metrics"""
        for dashboard in self:
            if not dashboard.show_financial_metrics:
                dashboard.monthly_revenue = 0.0
                dashboard.total_billed_amount = 0.0
                continue
                
            # Calculate revenue metrics (placeholder implementation)
            dashboard.monthly_revenue = 0.0  # Would integrate with billing system
            dashboard.total_billed_amount = 0.0  # Would integrate with accounting

    def _compute_alerts(self):
        """Compute alert counts"""
        for dashboard in self:
            # Placeholder implementation - would integrate with alert system
            dashboard.alert_count = 0
            dashboard.critical_alerts = 0

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _get_container_domain(self):
        """Build domain for container queries based on dashboard filters"""
        domain = [('company_id', '=', self.company_id.id)]
        
        if self.location_ids:
            domain.append(('location_id', 'in', self.location_ids.ids))
        
        if self.customer_ids:
            domain.append(('partner_id', 'in', self.customer_ids.ids))
        
        if self.department_id:
            domain.append(('partner_id.records_department_id', '=', self.department_id.id))
            
        return domain

    def _get_date_range(self):
        """Get date range based on dashboard configuration"""
        if self.date_range == 'custom':
            return self.date_from or fields.Date.today(), self.date_to or fields.Date.today()
        
        today = fields.Date.today()

    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')
        
        if self.date_range == 'today':
            return today, today
        elif self.date_range == 'week':
            # Start of week (Monday)
            start_week = today - timedelta(days=today.weekday())
            return start_week, today
        elif self.date_range == 'month':
            # Start of month
            start_month = today.replace(day=1)
            return start_month, today
        elif self.date_range == 'quarter':
            # Start of quarter
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            start_quarter = today.replace(month=quarter_start_month, day=1)
            return start_quarter, today
        elif self.date_range == 'year':
            # Start of year
            start_year = today.replace(month=1, day=1)
            return start_year, today
        
        return today, today

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_refresh_dashboard(self):
        """Manually refresh dashboard data"""
        self.ensure_one()
        # Force recomputation of all computed fields
        self._compute_container_metrics()
        self._compute_customer_metrics()
        self._compute_location_metrics()
        self._compute_activity_metrics()
        self._compute_financial_metrics()
        self._compute_alerts()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Dashboard refreshed successfully'),
                'type': 'success'
            )
        )

    def action_export_data(self):
        """Export dashboard data to Excel"""
        self.ensure_one()
        # Implementation for data export
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Export functionality coming soon'),
                'type': 'info'
            )
        )

    def action_view_containers(self):
        """View containers in list view with dashboard filters applied"""
        self.ensure_one()
        domain = self._get_container_domain()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Containers'),
            'res_model': 'records.container',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_company_id': self.company_id.id}
        )

    def action_view_locations(self):
        """View locations with utilization details"""
        self.ensure_one()
        domain = []
        if self.location_ids:
            domain = [('id', 'in', self.location_ids.ids)]
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Locations'),
            'res_model': 'records.location',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_company_id': self.company_id.id}
        )

    def action_view_customers(self):
        """View customers with storage details"""
        self.ensure_one()
        domain = [('is_company', '=', True)]
        if self.customer_ids:
            domain.append(('id', 'in', self.customer_ids.ids))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customers'),
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_company_id': self.company_id.id}
        )
