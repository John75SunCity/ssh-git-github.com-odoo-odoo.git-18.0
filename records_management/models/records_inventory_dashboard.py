from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsInventoryDashboard(models.Model):
    _name = 'records.inventory.dashboard'
    _description = 'Records Inventory Dashboard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'create_date desc'

    # ============================================================================
    # CONFIGURATION FIELDS
    # ============================================================================
    name = fields.Char(string="Dashboard Name", required=True, default="Inventory Dashboard")
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one(comodel_name='res.users', string='User', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('inactive', 'Inactive')], default='draft')

    # Filters
    location_ids = fields.Many2many('stock.location', 'records_inventory_dashboard_location_rel', 'dashboard_id', 'location_id', string="Locations")
    customer_ids = fields.Many2many('res.partner', 'records_inventory_dashboard_customer_rel', 'dashboard_id', 'partner_id', string="Customers", domain="[('is_company', '=', True)]")
    department_id = fields.Many2one(comodel_name='records.department', string="Department")
    date_range = fields.Selection([
        ('last_7_days', 'Last 7 Days'),
        ('last_30_days', 'Last 30 Days'),
        ('last_90_days', 'Last 90 Days'),
        ('custom', 'Custom Range'),
    ], string="Date Range", default='last_30_days')
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")

    # Display Options
    show_container_summary = fields.Boolean(string="Show Container Summary", default=True)
    show_location_utilization = fields.Boolean(string="Show Location Utilization", default=True)
    show_customer_distribution = fields.Boolean(string="Show Customer Distribution", default=True)
    show_recent_activity = fields.Boolean(string="Show Recent Activity", default=True)
    show_financial_metrics = fields.Boolean(string="Show Financial Metrics", default=False)
    show_alerts = fields.Boolean(string="Show Alerts", default=True)

    # ============================================================================
    # COMPUTED METRICS
    # ============================================================================
    # Container Metrics
    total_containers = fields.Integer(string="Total Containers", compute='_compute_all_metrics')
    active_containers = fields.Integer(string="Active Containers", compute='_compute_all_metrics')
    total_volume_cf = fields.Float(string="Total Volume (cu ft)", compute='_compute_all_metrics')

    # Customer & Location Metrics
    total_customers = fields.Integer(string="Total Customers", compute='_compute_all_metrics')
    total_locations = fields.Integer(string="Total Locations", compute='_compute_all_metrics')
    average_utilization = fields.Float(string="Avg. Location Utilization (%)", compute='_compute_all_metrics')

    # Container Type Breakdown
    type01_count = fields.Integer(string="Type 01 Count", compute='_compute_all_metrics')
    type02_count = fields.Integer(string="Type 02 Count", compute='_compute_all_metrics')
    type03_count = fields.Integer(string="Type 03 Count", compute='_compute_all_metrics')
    type04_count = fields.Integer(string="Type 04 Count", compute='_compute_all_metrics')
    type06_count = fields.Integer(string="Type 06 Count", compute='_compute_all_metrics')

    # Activity Metrics
    recent_pickups = fields.Integer(string="Recent Pickups", compute='_compute_all_metrics')
    recent_deliveries = fields.Integer(string="Recent Deliveries", compute='_compute_all_metrics')
    pending_requests = fields.Integer(string="Pending Requests", compute='_compute_all_metrics')
    recent_movements = fields.Integer(string="Recent Movements", compute='_compute_all_metrics')

    # Financial Metrics
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True, comodel_name='res.currency')
    monthly_revenue = fields.Monetary(string="Revenue in Period", compute='_compute_all_metrics', currency_field='currency_id')
    total_billed_amount = fields.Monetary(string="Total Billed (All Time, currency_field='currency_id')", compute='_compute_all_metrics')

    # Alert Metrics
    alert_count = fields.Integer(string="Total Alerts", compute='_compute_all_metrics')
    critical_alerts = fields.Integer(string="Critical Alerts", compute='_compute_all_metrics')
    capacity_warnings = fields.Integer(string="Capacity Warnings", compute='_compute_all_metrics')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('location_ids', 'customer_ids', 'department_id', 'date_range', 'date_from', 'date_to', 'show_financial_metrics')
    def _compute_all_metrics(self):
        for dashboard in self:
            container_domain = dashboard._get_container_domain()
            containers = self.env['records.container'].search(container_domain)
            date_from, date_to = dashboard._get_date_range()

            # Container Metrics
            dashboard.total_containers = len(containers)
            dashboard.active_containers = len(containers.filtered('active'))
            dashboard.total_volume_cf = sum(containers.mapped('volume_cf'))

            # Customer Metrics
            dashboard.total_customers = len(containers.mapped('partner_id'))

            # Location Metrics
            locations = dashboard.location_ids or self.env['stock.location'].search([('company_id', '=', dashboard.company_id.id)])
            dashboard.total_locations = len(locations)
            utilizations = locations.mapped('utilization_percentage')
            dashboard.average_utilization = sum(utilizations) / len(utilizations) if utilizations else 0.0

            # Container Type Breakdown
            dashboard.type01_count = len(containers.filtered(lambda c: c.container_type_id.code == 'TYPE_01'))
            dashboard.type02_count = len(containers.filtered(lambda c: c.container_type_id.code == 'TYPE_02'))
            dashboard.type03_count = len(containers.filtered(lambda c: c.container_type_id.code == 'TYPE_03'))
            dashboard.type04_count = len(containers.filtered(lambda c: c.container_type_id.code == 'TYPE_04'))
            dashboard.type06_count = len(containers.filtered(lambda c: c.container_type_id.code == 'TYPE_06'))

            # Activity Metrics
            activity_domain = [('create_date', '>=', date_from), ('create_date', '<=', date_to), ('company_id', '=', dashboard.company_id.id)]
            dashboard.recent_pickups = self.env['records.pickup.request'].search_count(activity_domain)
            dashboard.recent_deliveries = self.env['records.delivery.request'].search_count(activity_domain)
            dashboard.pending_requests = self.env['portal.request'].search_count([('state', 'in', ['draft', 'submitted']), ('company_id', '=', dashboard.company_id.id)])
            dashboard.recent_movements = self.env['records.container.movement'].search_count(activity_domain)

            # Financial Metrics
            if dashboard.show_financial_metrics:
                billing_domain = [('billing_date', '>=', date_from), ('billing_date', '<=', date_to), ('company_id', '=', dashboard.company_id.id), ('state', '=', 'confirmed')]
                billing_records = self.env['records.billing'].search(billing_domain)
                dashboard.monthly_revenue = sum(billing_records.mapped('total_amount'))
                all_billing = self.env['records.billing'].search([('company_id', '=', dashboard.company_id.id), ('state', '=', 'confirmed')])
                dashboard.total_billed_amount = sum(all_billing.mapped('total_amount'))
            else:
                dashboard.monthly_revenue = 0.0
                dashboard.total_billed_amount = 0.0

            # Alert Metrics
            capacity_locations = self.env['stock.location'].search([('company_id', '=', dashboard.company_id.id), ('utilization_percentage', '>=', 90)])
            dashboard.capacity_warnings = len(capacity_locations)
            critical_count = len(capacity_locations.filtered(lambda l: l.utilization_percentage >= 95))
            dashboard.critical_alerts = critical_count
            dashboard.alert_count = dashboard.capacity_warnings

    # ============================================================================
    # HELPER & DATA-FETCHING METHODS
    # ============================================================================
    def _get_container_domain(self):
        self.ensure_one()
        domain = [('company_id', '=', self.company_id.id)]
        if self.location_ids:
            domain.append(('location_id', 'in', self.location_ids.ids))
        if self.customer_ids:
            domain.append(('partner_id', 'in', self.customer_ids.ids))
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        return domain

    def _get_date_range(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        if self.date_range == 'custom':
            return self.date_from or today, self.date_to or today
        elif self.date_range == 'last_7_days':
            return today - timedelta(days=7), today
        elif self.date_range == 'last_90_days':
            return today - timedelta(days=90), today
        # Default to last 30 days
        return today - timedelta(days=30), today

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_refresh_dashboard(self):
        self.ensure_one()
        self._compute_all_metrics()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Success"),
                'message': _('Dashboard refreshed successfully.'),
                'type': 'success',
            }
        }

    def action_activate_dashboard(self):
        self.ensure_one()
        self.write({'state': 'active'})
        self.message_post(body=_("Dashboard activated"))

    def action_deactivate_dashboard(self):
        self.ensure_one()
        self.write({'state': 'inactive'})
        self.message_post(body=_("Dashboard deactivated"))

    def action_view_containers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Filtered Containers'),
            'res_model': 'records.container',
            'view_mode': 'list,form,kanban',
            'domain': self._get_container_domain(),
            'context': {'default_company_id': self.company_id.id}
        }

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('date_range', 'date_from', 'date_to')
    def _check_date_range(self):
        for record in self:
            if record.date_range == 'custom':
                if not record.date_from or not record.date_to:
                    raise ValidationError(_("Please specify both start and end dates for a custom range."))
                if record.date_from > record.date_to:
                    raise ValidationError(_("Start date must be before or the same as the end date."))
