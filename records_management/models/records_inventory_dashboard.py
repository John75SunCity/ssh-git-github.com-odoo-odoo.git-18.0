from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class RecordsInventoryDashboard(models.Model):
    _name = 'records.inventory.dashboard'
    _description = 'Records Inventory Dashboard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    dashboard_type = fields.Selection()
    refresh_interval = fields.Integer()
    auto_refresh = fields.Boolean()
    location_ids = fields.Many2many()
    customer_ids = fields.Many2many()
    department_id = fields.Many2one()
    date_range = fields.Selection()
    date_from = fields.Date()
    date_to = fields.Date()
    show_container_summary = fields.Boolean()
    show_location_utilization = fields.Boolean()
    show_customer_distribution = fields.Boolean()
    show_recent_activity = fields.Boolean()
    show_financial_metrics = fields.Boolean()
    show_alerts = fields.Boolean()
    total_containers = fields.Integer()
    active_containers = fields.Integer()
    total_volume_cf = fields.Float()
    total_customers = fields.Integer()
    total_locations = fields.Integer()
    average_utilization = fields.Float()
    type01_count = fields.Integer()
    type02_count = fields.Integer()
    type03_count = fields.Integer()
    type04_count = fields.Integer()
    type06_count = fields.Integer()
    recent_pickups = fields.Integer()
    recent_deliveries = fields.Integer()
    pending_requests = fields.Integer()
    recent_movements = fields.Integer()
    monthly_revenue = fields.Monetary()
    total_billed_amount = fields.Monetary()
    average_monthly_revenue = fields.Monetary()
    currency_id = fields.Many2one()
    alert_count = fields.Integer()
    critical_alerts = fields.Integer()
    capacity_warnings = fields.Integer()
    state = fields.Selection()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    months_back = fields.Date()
    today = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_container_metrics(self):
            """Compute container-related metrics"""
            for dashboard in self:
                domain = dashboard._get_container_domain()

                containers = self.env['records.container').search(domain]
                dashboard.total_containers = len(containers)
                dashboard.active_containers = len(containers.filtered('active'))
                dashboard.total_volume_cf = sum(containers.mapped('volume_cf') or [0.0])


    def _compute_customer_metrics(self):
            """Compute customer-related metrics"""
            for dashboard in self:
                domain = dashboard._get_container_domain()

                containers = self.env['records.container'].search(domain)
                dashboard.total_customers = len(containers.mapped('partner_id'))


    def _compute_location_metrics(self):
            """Compute location-related metrics"""
            for dashboard in self:
                if dashboard.location_ids:
                    locations = dashboard.location_ids
                else:
                    locations = self.env['records.location'].search([)]
                        ('company_id', '=', dashboard.company_id.id)


                dashboard.total_locations = len(locations)

                # Calculate average utilization
                utilizations = locations.mapped('utilization_percentage')
                if utilizations:
                    dashboard.average_utilization = sum(utilizations) / len(utilizations)
                else:
                    dashboard.average_utilization = 0.0


    def _compute_container_type_breakdown(self):
            """Compute container type breakdown"""
            for dashboard in self:
                domain = dashboard._get_container_domain()

                containers = self.env['records.container'].search(domain)

                dashboard.type01_count = len(containers.filtered(lambda c: c.container_type == 'type_01'))
                dashboard.type02_count = len(containers.filtered(lambda c: c.container_type == 'type_02'))
                dashboard.type03_count = len(containers.filtered(lambda c: c.container_type == 'type_03'))
                dashboard.type04_count = len(containers.filtered(lambda c: c.container_type == 'type_04'))
                dashboard.type06_count = len(containers.filtered(lambda c: c.container_type == 'type_06'))


    def _compute_activity_metrics(self):
            """Compute recent activity metrics"""
            for dashboard in self:
                date_from, date_to = dashboard._get_date_range()

                # Recent pickup requests
                pickup_domain = []
                    ('create_date', '>=', date_from),
                    ('create_date', '<=', date_to),
                    ('company_id', '=', dashboard.company_id.id)

                dashboard.recent_pickups = self.env['pickup.request'].search_count(pickup_domain)

                # Recent deliveries (could be linked to different model)
                delivery_domain = []
                    ('create_date', '>=', date_from),
                    ('create_date', '<=', date_to),
                    ('company_id', '=', dashboard.company_id.id)

                dashboard.recent_deliveries = self.env['records.delivery'].search_count(delivery_domain)

                # Pending requests
                dashboard.pending_requests = self.env['portal.request'].search_count([)]
                    ('state', 'in', ['draft', 'submitted']),
                    ('company_id', '=', dashboard.company_id.id)


                # Recent movements
                movement_domain = []
                    ('create_date', '>=', date_from),
                    ('create_date', '<=', date_to),
                    ('company_id', '=', dashboard.company_id.id)

                dashboard.recent_movements = self.env['records.container.movement'].search_count(movement_domain)


    def _compute_financial_metrics(self):
            """Compute financial metrics"""
            for dashboard in self:
                if not dashboard.show_financial_metrics:
                    dashboard.monthly_revenue = 0.0
                    dashboard.total_billed_amount = 0.0
                    dashboard.average_monthly_revenue = 0.0
                    continue

                date_from, date_to = dashboard._get_date_range()

                # Calculate revenue metrics based on billing records
                billing_domain = []
                    ('billing_date', '>=', date_from),
                    ('billing_date', '<=', date_to),
                    ('company_id', '=', dashboard.company_id.id),
                    ('state', '=', 'confirmed')


                billing_records = self.env['records.billing'].search(billing_domain)
                dashboard.monthly_revenue = sum(billing_records.mapped('total_amount'))

                # Total billed amount (all time)
                all_billing = self.env['records.billing'].search([)]
                    ('company_id', '=', dashboard.company_id.id),
                    ('state', '=', 'confirmed')

                dashboard.total_billed_amount = sum(all_billing.mapped('total_amount'))

                # Average monthly revenue (last 12 months)

    def _compute_alerts(self):
            """Compute alert counts"""
            for dashboard in self:
                # Location capacity warnings
                locations = self.env['records.location'].search([)]
                    ('company_id', '=', dashboard.company_id.id),
                    ('utilization_percentage', '>=', 90)

                dashboard.capacity_warnings = len(locations)

                # Critical alerts (near capacity or expired certificates)
                critical_count = 0

                # Near capacity locations (95%+)
                critical_locations = locations.filtered(lambda l: l.utilization_percentage >= 95)
                critical_count += len(critical_locations)

                # Expired or expiring certificates
                expired_certs = self.env['naid.certificate'].search([)]
                    ('expiration_date', '<=', fields.Date.today() + timedelta(days=30)),
                    ('state', '=', 'active'),
                    ('company_id', '=', dashboard.company_id.id)

                critical_count += len(expired_certs)

                dashboard.critical_alerts = critical_count
                dashboard.alert_count = dashboard.capacity_warnings + critical_count

        # ============================================================================
            # HELPER METHODS
        # ============================================================================

    def _get_container_domain(self):
            """Build domain for container queries based on dashboard filters""":
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


    def get_container_type_distribution(self):
            """Get container type distribution for charts""":
            self.ensure_one()
            return {}
                'TYPE 1 (Standard)': self.type01_count,
                'TYPE 2 (Legal/Banker)': self.type02_count,
                'TYPE 3 (Map)': self.type03_count,
                'TYPE 4 (Odd Size/Temp)': self.type04_count,
                'TYPE 6 (Pathology)': self.type06_count,



    def get_location_utilization_data(self):
            """Get location utilization data for charts""":
            self.ensure_one()

            if self.location_ids:
                locations = self.location_ids
            else:
                locations = self.env['records.location'].search([)]
                    ('company_id', '=', self.company_id.id),
                    ('active', '=', True)


            return [{]}
                'name': loc.name,
                'utilization': loc.utilization_percentage,
                'capacity': loc.storage_capacity,
                'current': loc.current_utilization,


    def get_top_customers_data(self):
            """Get top customers by container count"""
            self.ensure_one()
            domain = self._get_container_domain()

            containers = self.env['records.container'].search(domain)
            customer_counts = {}

            for container in containers:
                customer = container.partner_id
                if customer:
                    if customer.id not in customer_counts:
                        customer_counts[customer.id] = {}
                            'name': customer.name,
                            'count': 0,
                            'volume': 0.0

                    customer_counts[customer.id]['count'] += 1
                    customer_counts[customer.id]['volume'] += container.volume_cf or 0.0

            # Sort by count and return top 10
            sorted_customers = sorted()
                customer_counts.values(),
                key=lambda x: x['count'],
                reverse=True

            return sorted_customers[:10]

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_refresh_dashboard(self):
            """Manually refresh dashboard data"""
            self.ensure_one()
            # Force recomputation of all computed fields
            fields_to_recompute = []
                '_compute_container_metrics',
                '_compute_customer_metrics',
                '_compute_location_metrics',
                '_compute_container_type_breakdown',
                '_compute_activity_metrics',
                '_compute_financial_metrics',
                '_compute_alerts'


            for method_name in fields_to_recompute:
                if hasattr(self, method_name):
                    getattr(self, method_name)()

            return {}
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {}
                    'message': _('Dashboard refreshed successfully'),
                    'type': 'success'




    def action_export_data(self):
            """Export dashboard data to Excel"""
            self.ensure_one()

            return {}
                'type': 'ir.actions.report',
                'report_name': 'records_management.dashboard_export_report',
                'report_type': 'xlsx',
                'data': {}
                    'dashboard_id': self.id,
                    'include_charts': True,
                    'include_details': True

                'context': self.env.context



    def action_view_containers(self):
            """View containers in list view with dashboard filters applied"""
            self.ensure_one()
            domain = self._get_container_domain()

            return {}
                'type': 'ir.actions.act_window',
                'name': _('Containers'),
                'res_model': 'records.container',
                'view_mode': 'tree,form',
                'domain': domain,
                'context': {'default_company_id': self.company_id.id}



    def action_view_locations(self):
            """View locations with utilization details"""
            self.ensure_one()
            domain = [('company_id', '=', self.company_id.id)]

            if self.location_ids:
                domain.append(('id', 'in', self.location_ids.ids))

            return {}
                'type': 'ir.actions.act_window',
                'name': _('Locations'),
                'res_model': 'records.location',
                'view_mode': 'tree,form',
                'domain': domain,
                'context': {'default_company_id': self.company_id.id}



    def action_view_customers(self):
            """View customers with storage details"""
            self.ensure_one()
            domain = [('is_company', '=', True)]

            if self.customer_ids:
                domain.append(('id', 'in', self.customer_ids.ids))

            return {}
                'type': 'ir.actions.act_window',
                'name': _('Customers'),
                'res_model': 'res.partner',
                'view_mode': 'tree,form',
                'domain': domain,
                'context': {'default_company_id': self.company_id.id}



    def action_view_recent_activity(self):
            """View recent activity records"""
            self.ensure_one()
            date_from, date_to = self._get_date_range()

            return {}
                'type': 'ir.actions.act_window',
                'name': _('Recent Activity'),
                'res_model': 'records.container.movement',
                'view_mode': 'tree,form',
                'domain': []
                    ('create_date', '>=', date_from),
                    ('create_date', '<=', date_to),
                    ('company_id', '=', self.company_id.id)

                'context': {'default_company_id': self.company_id.id}



    def action_view_alerts(self):
            """View system alerts and warnings"""
            self.ensure_one()

            # For now, redirect to locations near capacity
            return {}
                'type': 'ir.actions.act_window',
                'name': _('System Alerts'),
                'res_model': 'records.location',
                'view_mode': 'tree,form',
                'domain': []
                    ('company_id', '=', self.company_id.id),
                    ('utilization_percentage', '>=', 90)

                'context': {'default_company_id': self.company_id.id}



    def action_activate_dashboard(self):
            """Activate dashboard"""
            for record in self:
                record.write({'state': 'active'})
                record.message_post(body=_("Dashboard activated"))


    def action_deactivate_dashboard(self):
            """Deactivate dashboard"""
            for record in self:
                record.write({'state': 'inactive'})
                record.message_post(body=_("Dashboard deactivated"))

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_date_range(self):
            """Validate custom date range"""
            for record in self:
                if record.date_range == 'custom':
                    if not record.date_from or not record.date_to:
                        raise ValidationError(_("Please specify both start and end dates for custom range")):
                    if record.date_from > record.date_to:
                        raise ValidationError(_("Start date must be before end date"))


    def _check_refresh_interval(self):
            """Validate refresh interval"""
            for record in self:
                if record.refresh_interval < 1 or record.refresh_interval > 60:
                    raise ValidationError(_("Refresh interval must be between 1 and 60 minutes"))

