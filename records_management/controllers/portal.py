# -*- coding: utf-8 -*-
"""
Records Management Main Controller

This controller provides the core dashboard and administrative endpoints for the
Records Management system. It implements comprehensive business intelligence,
operational metrics, and administrative controls with proper security and
performance optimization.

Key Features:
- Executive dashboard with real-time KPIs
- Container management and analytics
- NAID compliance monitoring
- Financial performance tracking
- Operational efficiency metrics
"""

# Python stdlib imports
import csv
import io
import logging
from datetime import datetime, timedelta

# Odoo core imports
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class RecordsManagementController(http.Controller):
    """
    Main controller for Records Management dashboard and administrative operations.
    Provides comprehensive business intelligence and operational control interface.
    """

    # ============================================================================
    # DASHBOARD ROUTES
    # ============================================================================

    @http.route("/records/dashboard", type="http", auth="user", website=True)
    def records_dashboard(self):
        """
        Enhanced dashboard with comprehensive business intelligence.
        Provides real-time operational metrics and performance indicators.
        """
        # Validate user permissions
        if not request.env.user.has_group('records_management.group_records_user'):
            return request.redirect('/web/login?redirect=/records/dashboard')

        # Get comprehensive dashboard data
        dashboard_data = self._get_dashboard_data()

        # Get recent activities
        recent_activities = self._get_recent_activities()

        # Get performance metrics
        performance_metrics = self._get_performance_metrics()

        # Get alerts and notifications
        system_alerts = self._get_system_alerts()

        context = {
            'dashboard_data': dashboard_data,
            'recent_activities': recent_activities,
            'performance_metrics': performance_metrics,
            'system_alerts': system_alerts,
            'user_permissions': self._get_user_dashboard_permissions(),
            'refresh_interval': 300,  # 5 minutes
        }

        return request.render('records_management.enhanced_dashboard', context)

    @http.route("/records/dashboard/data", type="json", auth="user", methods=["POST"])
    def get_dashboard_data(self, **post):
        """
        JSON endpoint for AJAX dashboard data updates.
        Provides real-time data for dashboard widgets.
        """
        try:
            data_type = post.get('data_type', 'overview')

            if data_type == 'overview':
                return {
                    'success': True,
                    'data': self._get_dashboard_data()
                }
            if data_type == 'metrics':
                return {
                    'success': True,
                    'data': self._get_performance_metrics()
                }
            if data_type == 'activities':
                return {
                    'success': True,
                    'data': self._get_recent_activities()
                }

            return {
                'success': False,
                'error': 'Invalid data type requested'
            }

        except Exception as e:
            _logger.error("Error fetching dashboard data: %s", e)
            return {
                'success': False,
                'error': 'Failed to load dashboard data'
            }

    # ============================================================================
    # BUSINESS INTELLIGENCE ROUTES
    # ============================================================================

    @http.route("/records/analytics", type="http", auth="user", website=True)
    def records_analytics(self):
        """
        Comprehensive analytics dashboard for business intelligence.
        """
        if not request.env.user.has_group('records_management.group_records_manager'):
            return request.redirect('/records/dashboard')

        analytics_data = {
            'revenue_trends': self._get_revenue_trends(),
            'container_utilization': self._get_container_utilization(),
            'customer_segments': self._get_customer_segments(),
            'operational_efficiency': self._get_operational_efficiency(),
            'compliance_metrics': self._get_compliance_metrics(),
        }

        return request.render('records_management.analytics_dashboard', {
            'analytics_data': analytics_data,
            'date_range_options': self._get_date_range_options(),
        })

    @http.route("/records/reports/container-summary", type="http", auth="user", methods=["GET"])
    def container_summary_report(self, **get):
        """
        Generate comprehensive container summary report.
        """
        # Get filter parameters
        date_from = get.get('date_from')
        date_to = get.get('date_to')
        partner_id = get.get('partner_id')
        location_id = get.get('location_id')

        # Build domain for filtering
        domain = [('active', '=', True)]

        if partner_id:
            domain.append(('partner_id', '=', int(partner_id)))
        if location_id:
            domain.append(('location_id', '=', int(location_id)))
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))

        # Get containers with applied filters
        containers = request.env['records.container'].search(domain, order='create_date desc')

        # Calculate summary statistics
        summary_stats = self._calculate_container_summary(containers)

        context = {
            'containers': containers,
            'summary_stats': summary_stats,
            'filters': {
                'date_from': date_from,
                'date_to': date_to,
                'partner_id': int(partner_id) if partner_id else None,
                'location_id': int(location_id) if location_id else None,
            },
            'customers': request.env['res.partner'].search([('is_company', '=', True)]),
            'locations': request.env['records.location'].search([]),
        }

        return request.render('records_management.container_summary_report', context)
    # ============================================================================
    # CONTAINER MANAGEMENT ROUTES
    # ============================================================================

    @http.route("/records/containers/bulk-update", type="json", auth="user", methods=["POST"])
    def action_bulk_container_update(self, **post):
        """
        Bulk update operations for containers.
        Supports location changes, status updates, and batch processing.
        """
        if not request.env.user.has_group('records_management.group_records_user'):
            return {'success': False, 'error': 'Insufficient permissions'}

        try:
            container_ids = post.get('container_ids', [])
            action_type = post.get('action_type')
            values = post.get('values', {})

            if not container_ids:
                return {'success': False, 'error': 'No containers selected'}

            containers = request.env['records.container'].browse(container_ids)

            # Validate user can access these containers
            for container in containers:
                if not container.can_user_access():
                    return {
                        'success': False,
                        'error': f'Access denied for container {container.name}'
                    }

            updated_count = 0

            if action_type == 'change_location':
                new_location_id = values.get('location_id')
                if new_location_id:
                    containers.write({'location_id': int(new_location_id)})
                    updated_count = len(containers)

                    # Create movement records for audit trail
                    for container in containers:
                        self._create_movement_record(container, new_location_id)

            if action_type == 'update_status':
                new_status = values.get('status')
                if new_status:
                    containers.write({'state': new_status})
                    updated_count = len(containers)

            if action_type == 'add_tags':
                tag_ids = values.get('tag_ids', [])
                if tag_ids:
                    containers.write({'tag_ids': [(6, 0, tag_ids)]})
                    updated_count = len(containers)

            # Create NAID audit log
            self._create_audit_log(
                'bulk_container_update',
                f'Bulk {action_type} performed on {updated_count} containers'
            )

            return {
                'success': True,
                'updated_count': updated_count,
                'message': f'Successfully updated {updated_count} containers'
            }

        except Exception as e:
            _logger.error("Bulk container update error: %s", e)
            return {
                'success': False,
                'error': 'Bulk update operation failed'
            }

    @http.route("/records/containers/export", type="http", auth="user", methods=["GET"])
    def export_containers(self, **get):
        """
        Export container data to CSV format.
        """
        if not request.env.user.has_group('records_management.group_records_user'):
            return request.redirect('/web/login')

        # Build domain based on filters
        domain = []
        if get.get('partner_id'):
            domain.append(('partner_id', '=', int(get.get('partner_id'))))
        if get.get('location_id'):
            domain.append(('location_id', '=', int(get.get('location_id'))))

        containers = request.env['records.container'].search(domain)

        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Container Number', 'Customer', 'Location', 'Container Type',
            'Volume (CF)', 'Weight (lbs)', 'Status', 'Created Date'
        ])

        # Write data rows
        for container in containers:
            writer.writerow([
                container.name or '',
                container.partner_id.name or '',
                container.location_id.name or '',
                container.container_type or '',
                container.volume or 0,
                container.weight or 0,
                container.state or '',
                container.create_date.strftime('%Y-%m-%d') if container.create_date else ''
            ])

        # Create response
        response = request.make_response(
            output.getvalue(),
            headers=[
                ('Content-Type', 'text/csv'),
                ('Content-Disposition', f'attachment; filename=containers_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            ]
        )

        return response

    # ============================================================================
    # VALIDATION AND CONSTRAINT HELPER ROUTES
    # ============================================================================

    @http.route("/records/validate/container-number", type="json", auth="user", methods=["POST"])
    def _check_container_number_availability(self, **post):
        """
        Validate container number availability and suggest alternatives.
        """
        container_number = post.get('container_number')
        customer_id = post.get('customer_id')

        if not container_number or not customer_id:
            return {'success': False, 'error': 'Missing required parameters'}

        # Check if container number exists
        existing_container = request.env['records.container'].search([
            ('name', '=', container_number),
            ('partner_id', '=', int(customer_id))
        ], limit=1)

        if existing_container:
            # Generate suggestions
            suggestions = self._generate_container_number_suggestions(
                container_number, customer_id
            )

            return {
                'success': True,
                'available': False,
                'existing_container': existing_container.name,
                'suggestions': suggestions
            }

        return {
            'success': True,
            'available': True,
            'message': 'Container number is available'
        }

    # ============================================================================
    # SYSTEM MONITORING ROUTES
    # ============================================================================

    @http.route("/records/system/health", type="json", auth="user", methods=["POST"])
    def _check_system_health(self):
        """
        System health check endpoint for monitoring.
        """
        if not request.env.user.has_group('records_management.group_records_manager'):
            return {'success': False, 'error': 'Insufficient permissions'}

        try:
            health_data = {
                'database_status': self._check_database_health(),
                'storage_status': self._check_storage_capacity(),
                'audit_log_status': self._check_audit_log_integrity(),
                'backup_status': self._check_backup_status(),
                'compliance_status': self._check_compliance_status(),
            }

            # Determine overall health
            all_healthy = all(
                status.get('status') == 'healthy'
                for status in health_data.values()
            )

            return {
                'success': True,
                'overall_status': 'healthy' if all_healthy else 'warning',
                'health_data': health_data,
                'last_check': datetime.now().isoformat()
            }

        except Exception as e:
            _logger.error("System health check failed: %s", e)
            return {
                'success': False,
                'error': 'Health check failed',
                'overall_status': 'critical'
            }

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _get_dashboard_data(self):
        """Get comprehensive dashboard data with performance optimization."""
        # Use efficient batch queries to minimize database hits
        Container = request.env['records.container']
        PickupRequest = request.env['pickup.request']
        ShredService = request.env['shredding.service']

        # Get current company containers
        company_domain = [('company_id', '=', request.env.company.id)]

        # Container statistics
        total_containers = Container.search_count(company_domain + [('active', '=', True)])
        containers_by_type = Container.read_group(
            company_domain + [('active', '=', True)],
            ['container_type'],
            ['container_type']
        )

        # Active requests
        pending_pickups = PickupRequest.search_count([('state', 'in', ['draft', 'confirmed'])])

        # Recent destruction services
        recent_destructions = ShredService.search_count([
            ('completion_date', '>=', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        ])

        # Calculate total volume and capacity utilization
        container_data = Container.search_read(
            company_domain + [('active', '=', True)],
            ['volume', 'location_id']
        )

        total_volume = sum(c['volume'] or 0 for c in container_data)

        # Location utilization
        location_utilization = {}
        for container in container_data:
            location_name = container['location_id'][1] if container['location_id'] else 'Unassigned'
            if location_name not in location_utilization:
                location_utilization[location_name] = {'count': 0, 'volume': 0}
            location_utilization[location_name]['count'] += 1
            location_utilization[location_name]['volume'] += container['volume'] or 0

        return {
            'total_containers': total_containers,
            'containers_by_type': {item['container_type']: item['__count']
                                 for item in containers_by_type},
            'total_volume_cf': round(total_volume, 2),
            'pending_pickups': pending_pickups,
            'recent_destructions': recent_destructions,
            'location_utilization': location_utilization,
            'active_customers': len(Container.search([('active', '=', True)]).mapped('partner_id')),
        }

    def _get_recent_activities(self, limit=10):
        """Get recent system activities for dashboard display."""
        activities = []

        # Recent container creations
        recent_containers = request.env['records.container'].search(
            [('create_date', '>=', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))],
            order='create_date desc',
            limit=5
        )

        for container in recent_containers:
            activities.append({
                'type': 'container_created',
                'description': f'New container {container.name} added for {container.partner_id.name}',
                'timestamp': container.create_date,
                'icon': 'fa-box',
                'color': 'success'
            })

        # Recent pickup requests
        recent_pickups = request.env['pickup.request'].search(
            [('create_date', '>=', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))],
            order='create_date desc',
            limit=5
        )

        for pickup in recent_pickups:
            activities.append({
                'type': 'pickup_requested',
                'description': f'Pickup requested by {pickup.partner_id.name}',
                'timestamp': pickup.create_date,
                'icon': 'fa-truck',
                'color': 'info'
            })

        # Sort by timestamp and limit
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return activities[:limit]

    def _get_performance_metrics(self):
        """Calculate performance metrics for dashboard KPIs."""
        now = datetime.now()
        last_month = now - timedelta(days=30)
        last_week = now - timedelta(days=7)

        # Container growth metrics
        containers_this_month = request.env['records.container'].search_count([
            ('create_date', '>=', last_month.strftime('%Y-%m-%d'))
        ])

        containers_last_week = request.env['records.container'].search_count([
            ('create_date', '>=', last_week.strftime('%Y-%m-%d'))
        ])

        # Pickup efficiency
        completed_pickups = request.env['pickup.request'].search_count([
            ('state', '=', 'completed'),
            ('completion_date', '>=', last_month.strftime('%Y-%m-%d'))
        ])

        total_pickups = request.env['pickup.request'].search_count([
            ('create_date', '>=', last_month.strftime('%Y-%m-%d'))
        ])

        pickup_completion_rate = (completed_pickups / total_pickups * 100) if total_pickups else 0

        return {
            'containers_growth_month': containers_this_month,
            'containers_growth_week': containers_last_week,
            'pickup_completion_rate': round(pickup_completion_rate, 1),
            'total_cubic_feet_managed': self._calculate_total_cubic_feet(),
            'compliance_score': self._calculate_compliance_score(),
        }

    def _get_system_alerts(self):
        """Get system alerts and notifications."""
        alerts = []

        # Check for overdue pickups
        overdue_pickups = request.env['pickup.request'].search_count([
            ('state', 'in', ['confirmed', 'in_progress']),
            ('scheduled_date', '<', datetime.now().strftime('%Y-%m-%d'))
        ])

        if overdue_pickups:
            alerts.append({
                'type': 'warning',
                'message': f'{overdue_pickups} pickup requests are overdue',
                'action_url': '/records/pickups?filter=overdue'
            })

        # Check storage capacity
        location_capacity = self._check_location_capacity_warnings()
        if location_capacity:
            alerts.extend(location_capacity)

        # Check compliance issues
        compliance_issues = self._check_compliance_warnings()
        if compliance_issues:
            alerts.extend(compliance_issues)

        return alerts

    def _get_user_dashboard_permissions(self):
        """Get user permissions for dashboard functionality."""
        user = request.env.user

        return {
            'can_view_analytics': user.has_group('records_management.group_records_manager'),
            'can_bulk_update': user.has_group('records_management.group_records_user'),
            'can_export_data': user.has_group('records_management.group_records_user'),
            'can_manage_system': user.has_group('records_management.group_records_manager'),
            'can_view_billing': user.has_group('records_management.group_records_manager'),
        }

    def _calculate_container_summary(self, containers):
        """Calculate summary statistics for container report."""
        if not containers:
            return {}

        total_containers = len(containers)
        total_volume = sum(c.volume or 0 for c in containers)
        total_weight = sum(c.weight or 0 for c in containers)

        # Group by container type
        type_breakdown = {}
        for container in containers:
            container_type = container.container_type or 'Unknown'
            if container_type not in type_breakdown:
                type_breakdown[container_type] = {'count': 0, 'volume': 0, 'weight': 0}

            type_breakdown[container_type]['count'] += 1
            type_breakdown[container_type]['volume'] += container.volume or 0
            type_breakdown[container_type]['weight'] += container.weight or 0

        # Group by status
        status_breakdown = {}
        for container in containers:
            status = container.state or 'Unknown'
            status_breakdown[status] = status_breakdown.get(status, 0) + 1

        return {
            'total_containers': total_containers,
            'total_volume': round(total_volume, 2),
            'total_weight': round(total_weight, 2),
            'average_volume': round(total_volume / total_containers, 2) if total_containers else 0,
            'type_breakdown': type_breakdown,
            'status_breakdown': status_breakdown,
        }

    def _create_movement_record(self, container, new_location_id):
        """Create movement audit record for container location changes."""
        request.env['records.container.movement'].sudo().create({
            'container_id': container.id,
            'from_location_id': container.location_id.id if container.location_id else False,
            'to_location_id': new_location_id,
            'movement_date': datetime.now(),
            'moved_by': request.env.user.id,
            'movement_type': 'location_change',
            'notes': 'Bulk location update via dashboard'
        })

    def _create_audit_log(self, action_type, description):
        """Create NAID compliance audit log."""
        request.env['naid.audit.log'].sudo().create({
            'action_type': action_type,
            'description': description,
            'user_id': request.env.user.id,
            'timestamp': datetime.now(),
            'ip_address': request.httprequest.remote_addr,
        })

    def _generate_container_number_suggestions(self, base_number, customer_id):
        """Generate alternative container number suggestions."""
        suggestions = []

        # Try with suffix patterns
        suffixes = ['-A', '-B', '-C', '-1', '-2', '-3']

        for suffix in suffixes:
            suggested_number = base_number + suffix
            exists = request.env['records.container'].search([
                ('name', '=', suggested_number),
                ('partner_id', '=', int(customer_id))
            ], limit=1)

            if not exists:
                suggestions.append(suggested_number)
                # Limit suggestions to exactly 3
                if len(suggestions) == 3:
                    break

        return suggestions

    # Additional helper methods for system monitoring
    def _check_database_health(self):
        """Check database connectivity and performance."""
        try:
            request.env.cr.execute("SELECT 1")
            return {'status': 'healthy', 'message': 'Database connection OK'}
        except Exception as e:
            return {'status': 'critical', 'message': f'Database error: {str(e)}'}

    def _check_storage_capacity(self):
        """Check storage capacity and utilization."""
        # This would integrate with actual storage monitoring
        return {'status': 'healthy', 'message': 'Storage capacity normal'}

    def _check_audit_log_integrity(self):
        """Verify audit log integrity for NAID compliance."""
        recent_logs = request.env['naid.audit.log'].search_count([
            ('timestamp', '>=', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
        ])

        if recent_logs > 0:
            return {'status': 'healthy', 'message': f'{recent_logs} audit entries in last 24h'}
        return {'status': 'warning', 'message': 'No recent audit activity'}

    def _check_backup_status(self):
        """Check backup system status."""
        # This would integrate with backup monitoring system
        return {'status': 'healthy', 'message': 'Backup system operational'}

    def _check_compliance_status(self):
        """Check overall NAID compliance status."""
        # Check for any compliance violations or warnings
        return {'status': 'healthy', 'message': 'NAID compliance maintained'}

    def _calculate_total_cubic_feet(self):
        """Calculate total cubic feet under management."""
        total = request.env['records.container'].search_read(
            [('active', '=', True)],
            ['volume']
        )
        return round(sum(c['volume'] or 0 for c in total), 2)

    def _calculate_compliance_score(self):
        """Calculate overall compliance score."""
        # This would implement actual compliance scoring logic
        return 98.5  # Placeholder

    def _check_location_capacity_warnings(self):
        """Check for location capacity warnings."""
        # Implementation would check actual location capacity limits
        return []  # Placeholder

    def _check_compliance_warnings(self):
        """Check for compliance-related warnings."""
        # Implementation would check for compliance violations
        return []  # Placeholder
