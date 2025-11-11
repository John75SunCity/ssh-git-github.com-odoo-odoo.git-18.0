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
import json
import logging
from datetime import datetime, timedelta

# Odoo core imports
from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class RecordsManagementController(http.Controller):
    """
    Main controller for Records Management dashboard and administrative operations.
    Provides comprehensive business intelligence and operational control interface.
    """

    # Portal pagination configuration
    _items_per_page = 20

    # ============================================================================
    # COMMON HELPER METHODS
    # ============================================================================

    def _prepare_portal_layout_values(self):
        """
        Prepare common values for portal layout templates.
        Returns base context dictionary for portal pages.
        """
        return {
            'page_name': 'records_management',
            'user': request.env.user,
            'partner': request.env.user.partner_id,
        }

    # ============================================================================
    # DASHBOARD ROUTES
    # ============================================================================

    @http.route("/records/dashboard", type="http", auth="user", website=True)
    def records_dashboard(self):
        """
        Enhanced dashboard with comprehensive business intelligence.
        Provides real-time operational metrics and performance indicators.
        """
        if not request.env.user.has_group("records_management.group_records_user"):
            return request.redirect("/web/login?redirect=/records/dashboard")

        # Get comprehensive dashboard data (now filtered by user partner)
        dashboard_data = self._get_dashboard_data()

        # Get recent activities
        recent_activities = self._get_recent_activities()

        # Get performance metrics
        performance_metrics = self._get_performance_metrics()

        # Get alerts and notifications
        system_alerts = self._get_system_alerts()

        # Get refresh interval from system parameters or use default
        refresh_interval = int(request.env['ir.config_parameter'].sudo().get_param(
            'records_management.dashboard_refresh_interval', 300
        ))

        context = {
            'dashboard_data': dashboard_data,
            'recent_activities': recent_activities,
            'performance_metrics': performance_metrics,
            'system_alerts': system_alerts,
            'user_permissions': self._get_user_dashboard_permissions(),
            'refresh_interval': refresh_interval,
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
            elif data_type == 'metrics':
                return {
                    'success': True,
                    'data': self._get_performance_metrics()
                }
            elif data_type == 'activities':
                return {
                    'success': True,
                    'data': self._get_recent_activities()
                }
            else:
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
        if not request.env.user.has_group("records_management.group_records_manager"):
            return request.redirect("/records/dashboard")

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

        if partner_id and partner_id.isdigit():  # Added check to avoid int(None)
            domain.append(('partner_id', '=', int(partner_id)))
        if location_id and location_id.isdigit():  # Added check to avoid int(None)
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

        # The context dictionary provides the following keys to the template:
        # - containers: recordset of filtered containers
        # - summary_stats: dict with total/average/count breakdowns
        # - filters: dict of applied filter values
        # - customers: recordset of all company partners
        # - locations: recordset of all locations
        return request.render('records_management.container_summary_report', context)

    # ============================================================================
    # CONTAINER MANAGEMENT ROUTES
    # ============================================================================

    @http.route("/records/containers/list", type="json", auth="user", methods=["POST"])
    def list_containers_with_barcodes(self, **post):
        """Return lightweight container list including temporary & physical barcode state.

        Accepts optional filters: partner_id, limit, offset, search (matches name, barcode, temp_barcode).
        This endpoint is designed for modern Owl portal components needing real-time barcode visibility.
        """
        if not request.env.user.has_group("records_management.group_records_user") and not request.env.user.has_group("records_management.group_portal_company_admin"):
            return {"success": False, "error": "Insufficient permissions"}

        try:
            Container = request.env['records.container']
            domain = []

            partner_id = post.get('partner_id')
            if partner_id and str(partner_id).isdigit():
                domain.append(('partner_id', '=', int(partner_id)))

            search_term = (post.get('search') or '').strip()
            if search_term:
                # Perform name_search style expansion for barcode fields
                search_domain = ['|', '|', ('name', 'ilike', search_term), ('barcode', 'ilike', search_term), ('temp_barcode', 'ilike', search_term)]
                if domain:
                    domain = ['&'] + domain + [search_domain]
                else:
                    domain = search_domain

            limit = int(post.get('limit') or 40)
            offset = int(post.get('offset') or 0)

            containers = Container.search(domain, limit=limit, offset=offset, order='create_date desc')
            total_count = Container.search_count(domain if isinstance(domain, list) else [])

            result = []
            for c in containers:
                result.append({
                    'id': c.id,
                    'name': c.name,
                    'partner': c.partner_id.name,
                    'location': c.location_id.name,
                    'container_type': c.container_type_id.name,
                    'state': c.state,
                    'temp_barcode': c.temp_barcode,
                    'barcode': c.barcode,
                    'barcode_assigned': bool(c.barcode),
                    'create_date': c.create_date and c.create_date.strftime('%Y-%m-%d') or '',
                })

            return {
                'success': True,
                'containers': result,
                'total': total_count,
                'limit': limit,
                'offset': offset,
            }
        except Exception as e:
            _logger.error("Error listing containers with barcodes: %s", e)
            return {"success": False, "error": "Failed to load containers"}

    @http.route("/records/containers/bulk-update", type="json", auth="user", methods=["POST"])
    def action_bulk_container_update(self, **post):
        """
        Bulk update operations for containers.
        Supports location changes, status updates, and batch processing.
        """
        if not request.env.user.has_group("records_management.group_records_user"):
            return {'success': False, 'error': 'Insufficient permissions'}

        try:
            container_ids = post.get('container_ids', [])
            action_type = post.get('action_type')
            values = post.get('values', {})

            if not container_ids:
                return {'success': False, 'error': 'No containers selected'}

            containers = request.env["records.container"].browse(container_ids)

            # Validate user can access these containers
            for container in containers:
                if not container.can_user_access():
                    return {"success": False, "error": f"Access denied for container {container.name}"}

            updated_count = 0

            if action_type == 'change_location':
                new_location_id = values.get('location_id')
                if new_location_id:
                    try:
                        new_location_id_int = int(new_location_id)
                    except (TypeError, ValueError):
                        return {'success': False, 'error': 'Invalid location_id provided'}
                    containers.write({"location_id": new_location_id_int})
                    updated_count = len(containers)

                    # Create movement records for audit trail
                    for container in containers:
                        self._create_movement_record(container, new_location_id_int)

            elif action_type == "add_tags":  # Removed unnecessary "update_status" placeholder
                tag_ids = values.get('tag_ids', [])
                if tag_ids:
                    # Ensure tag_ids is a list of integers
                    if not isinstance(tag_ids, list):
                        tag_ids = [tag_ids]
                    tag_ids = [int(t) for t in tag_ids if str(t).isdigit()]
                    if tag_ids:
                        containers.write({"tag_ids": [(6, 0, tag_ids)]})
                        updated_count = len(containers)

            # Create NAID audit log
            self._create_audit_log(
                "bulk_container_update", f"Bulk {action_type} performed on {updated_count} containers"
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
        if not request.env.user.has_group("records_management.group_records_user"):
            return request.redirect("/web/login")

        # Build domain based on filters
        domain = []
        partner_id = get.get("partner_id")
        location_id = get.get("location_id")
        if partner_id and partner_id.isdigit():  # Added check to avoid int(None)
            domain.append(("partner_id", "=", int(partner_id)))
        if location_id and location_id.isdigit():  # Added check to avoid int(None)
            domain.append(("location_id", "=", int(location_id)))

        containers = request.env['records.container'].search(domain)

        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")

        # Write header
        writer.writerow([
            'Container Number', 'Customer', 'Location', 'Container Type',
            'Volume (CF)', 'Weight (lbs)', 'Status', 'Created Date'
        ])

        # Write data rows
        from odoo.fields import Datetime as OdooDatetime

        for container in containers:
            # Normalize create_date to string if not already a datetime
            create_date_str = ""
            if container.create_date:
                if isinstance(container.create_date, datetime):
                    create_date_str = container.create_date.strftime("%Y-%m-%d")
                else:
                    # Try Odoo's from_string first, then fallback to common formats
                    date_val = None
                    try:
                        date_val = OdooDatetime.from_string(str(container.create_date))
                    except Exception:
                        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S%z"):
                            try:
                                date_val = datetime.strptime(str(container.create_date), fmt)
                                break
                            except Exception:
                                continue
                    if date_val:
                        create_date_str = date_val.strftime("%Y-%m-%d")
                    else:
                        create_date_str = str(container.create_date)
            writer.writerow(
                [
                    container.name or "",
                    container.partner_id.name or "",
                    container.location_id.name or "",
                    container.container_type or "",
                    container.volume or 0,
                    container.weight or 0,
                    container.state or "",
                    create_date_str,
                ]
            )
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
        existing_container = request.env["records.container"].search(
            [("name", "=", container_number), ("partner_id", "=", int(customer_id))], limit=1
        )

        if existing_container:
            # Generate suggestions
            suggestions = self._generate_container_number_suggestions(
                container_number, customer_id
            )

            return {
                "success": True,
                "available": False,
                "existing_container": existing_container.name,
                "suggestions": suggestions,
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
        if not request.env.user.has_group("records_management.group_records_manager"):
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
        Container = request.env["records.container"]
        PickupRequest = request.env["pickup.request"]
        ShredService = request.env["shredding.service"]

        # Determine if user is a portal user (customer) - exclude sensitive data like location capacity
        is_portal_user = not request.env.user.has_group("records_management.group_records_manager")
        user_partner_id = request.env.user.partner_id.id

        # Base domain for filtering by user partner (for portal users)
        partner_domain = [("partner_id", "=", user_partner_id)] if is_portal_user else []

        # Get current company containers (filtered by partner for portal users)
        company_domain = [('company_id', '=', request.env.company.id)]
        full_domain = company_domain + partner_domain + [("active", "=", True)]

        # Container statistics (filtered)
        total_containers = Container.search_count(full_domain)
        containers_by_type = Container.read_group(full_domain, ["container_type"], ["container_type"])

        # Active requests (filtered by partner for portal users)
        pickup_domain = partner_domain + [("state", "in", ["draft", "confirmed"])]
        pending_pickups = PickupRequest.search_count(pickup_domain)

        # Recent destruction services (filtered by partner for portal users)
        shred_domain = partner_domain + [
            ("completion_date", ">=", (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        ]
        recent_destructions = ShredService.search_count(shred_domain)

        # Calculate total volume (filtered)
        container_data = Container.search_read(full_domain, ["volume", "location_id"])

        # Initialize variables for calculation
        total_volume = 0
        location_utilization = {}  # Only populate for non-portal users

        for container in container_data:
            total_volume += container["volume"] or 0
            # Exclude location utilization for portal users to prevent capacity exposure
            if not is_portal_user:
                location_id = container.get("location_id")
                if location_id:
                    location_name = (
                        request.env["records.location"].browse(location_id[0]).name if location_id else "Unknown"
                    )
                    if location_name not in location_utilization:
                        location_utilization[location_name] = {"volume": 0, "count": 0}
                    location_utilization[location_name]["volume"] += container["volume"] or 0
                    location_utilization[location_name]["count"] += 1

        # Efficiently count unique active customers (filtered for portal users - should be 1 or 0)
        customer_domain = partner_domain + [("active", "=", True)]
        active_customers_group = Container.read_group(customer_domain, ["partner_id"], ["partner_id"])
        active_customers_count = (
            len(active_customers_group) if not is_portal_user else (1 if active_customers_group else 0)
        )

        return {
            "total_containers": total_containers,
            "containers_by_type": {
                (item["container_type"] or "Unknown"): item["__count"] for item in containers_by_type
            },
            "total_volume_cf": round(total_volume, 2),
            "pending_pickups": pending_pickups,
            "recent_destructions": recent_destructions,
            "location_utilization": location_utilization,  # Empty for portal users
            "active_customers": active_customers_count,
        }

    def _get_recent_activities(self, limit=10):
        """Get recent system activities for dashboard display."""
        activities = []

        # Determine if user is a portal user and get their partner
        is_portal_user = not request.env.user.has_group("records_management.group_records_manager")
        user_partner_id = request.env.user.partner_id.id
        partner_domain = [("partner_id", "=", user_partner_id)] if is_portal_user else []

        # Recent container creations (filtered by partner)
        container_domain = partner_domain + [
            ("create_date", ">=", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
        ]
        recent_containers = request.env["records.container"].search(container_domain, order="create_date desc", limit=5)

        for container in recent_containers:
            activities.append({
                'type': 'container_created',
                'description': f'New container {container.name} added for {container.partner_id.name}',
                'timestamp': container.create_date,
                'icon': 'fa-box',
                'color': 'success'
            })

        # Recent pickup requests (filtered by partner)
        pickup_domain = partner_domain + [
            ("create_date", ">=", (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
        ]
        recent_pickups = request.env["pickup.request"].search(pickup_domain, order="create_date desc", limit=5)

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

        # Determine if user is a portal user and get their partner
        is_portal_user = not request.env.user.has_group("records_management.group_records_manager")
        user_partner_id = request.env.user.partner_id.id
        partner_domain = [("partner_id", "=", user_partner_id)] if is_portal_user else []

        # Container growth metrics (filtered by partner)
        container_month_domain = partner_domain + [("create_date", ">=", last_month.strftime("%Y-%m-%d"))]
        containers_this_month = request.env["records.container"].search_count(container_month_domain)

        container_week_domain = partner_domain + [("create_date", ">=", last_week.strftime("%Y-%m-%d"))]
        containers_last_week = request.env["records.container"].search_count(container_week_domain)

        # Pickup efficiency (filtered by partner)
        pickup_completed_domain = partner_domain + [
            ("state", "=", "completed"),
            ("completion_date", ">=", last_month.strftime("%Y-%m-%d")),
        ]
        completed_pickups = request.env["pickup.request"].search_count(pickup_completed_domain)

        pickup_total_domain = partner_domain + [("create_date", ">=", last_month.strftime("%Y-%m-%d"))]
        total_pickups = request.env["pickup.request"].search_count(pickup_total_domain)

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
        overdue_pickups = request.env["pickup.request"].search_count(
            [
                ("state", "in", ["confirmed", "in_progress"]),
                ("scheduled_date", "<", datetime.now().strftime("%Y-%m-%d")),
            ]
        )

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
            "can_view_analytics": user.has_group("records_management.group_records_manager"),
            "can_bulk_update": user.has_group("records_management.group_records_user"),
            "can_export_data": user.has_group("records_management.group_records_user"),
            "can_manage_system": user.has_group("records_management.group_records_manager"),
            "can_view_billing": user.has_group("records_management.group_records_manager"),
        }

    def _calculate_container_summary(self, containers):
        """Calculate summary statistics for container report."""
        if not containers:
            return {}

        total_containers = len(containers)
        total_volume = float(sum(c.volume or 0 for c in containers))
        total_weight = float(sum(c.weight or 0 for c in containers))

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
        request.env["records.container.movement"].sudo().create(
            {
                "container_id": container.id,
                "from_location_id": container.location_id.id if container.location_id else False,
                "to_location_id": new_location_id,
                "movement_date": datetime.now(),
                "moved_by": request.env.user.id,
                "movement_type": "location_change",
            }
        )

    def _create_audit_log(self, action_type, description):
        """Create NAID audit log entry."""
        ip_address = getattr(getattr(request, "httprequest", None), "remote_addr", None)
        request.env["naid.audit.log"].sudo().create(
            {
                "action_type": action_type,
                "description": description,
                "user_id": request.env.user.id,
                "timestamp": datetime.now(),
                "ip_address": ip_address,
            }
        )

    def _generate_container_number_suggestions(self, base_number, customer_id):
        """Generate alternative container number suggestions."""
        suggestions = []

        # Try with suffix patterns
        suffixes = ['-A', '-B', '-C', '-1', '-2', '-3']

        for suffix in suffixes:
            suggested_number = base_number + suffix
            exists = request.env["records.container"].search(
                [("name", "=", suggested_number), ("partner_id", "=", int(customer_id))], limit=1
            )

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
        recent_logs = request.env["naid.audit.log"].search_count(
            [("timestamp", ">=", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"))]
        )

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
        total = request.env["records.container"].search_read([("active", "=", True)], ["volume"])
        return round(sum(c["volume"] or 0 for c in total), 2)

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

    # ============================================================================
    # NAID CERTIFICATION ROUTES
    # ============================================================================

    @http.route(
        "/my/certificates/<int:cert_id>", type="http", auth="user", website=True
    )
    def portal_certificate_detail(self, cert_id, **kwargs):
        """
        Portal detail page for a NAID Certificate of Destruction.
        Ensures the logged-in user's partner owns the certificate.
        """
        Certificate = request.env["naid.certificate"].sudo()
        cert = Certificate.browse(cert_id)

        # Validate existence and ownership (partner-based)
        if not cert or not cert.exists():
            return request.redirect("/my")

        user_partner = request.env.user.partner_id
        if cert.partner_id.id != user_partner.id:
            # Prevent access if certificate is not owned by this portal user
            return request.redirect("/my")

        # Minimal context for portal detail
        context = {
            "certificate": cert,
            "page_name": "certificate_detail",
        }
        return request.render(
            "records_management.portal_certificate_detail", context
        )

    @http.route(
        "/my/certificates/<int:cert_id>/download",
        type="http",
        auth="user",
        website=True,
        methods=["GET"],
    )
    def portal_certificate_download(self, cert_id, **get):
        """
        Secure download for a NAID Certificate PDF for portal users.
        Verifies ownership and returns the generated PDF via QWeb report.
        """
        Certificate = request.env["naid.certificate"].sudo()
        cert = Certificate.browse(cert_id)

        # Validate existence
        if not cert or not cert.exists():
            return request.redirect("/my")

        # Ownership check
        user_partner = request.env.user.partner_id
        if cert.partner_id.id != user_partner.id:
            return request.redirect("/my")

        # Optionally require issued/sent state for downloads
        if cert.state not in ("issued", "sent"):
            # Fallback: try to generate on the fly if data missing but allowed
            try:
                if not cert.certificate_data:
                    cert.action_issue_certificate()
            except Exception:
                return request.redirect("/my")

        # Use the report to render PDF content
        report = request.env.ref(
            "records_management.action_report_naid_certificate", raise_if_not_found=False
        )
        if not report:
            return request.redirect("/my")

        # Defensive fix: sanitize report fields if migration stored lists/tuples
        try:
            fixes = {}
            if isinstance(getattr(report, "report_name", None), (list, tuple)):
                rn = report.report_name
                fixes["report_name"] = rn[0] if rn else ""
            elif report.report_name is not None and not isinstance(report.report_name, str):
                fixes["report_name"] = str(report.report_name)

            if isinstance(getattr(report, "report_file", None), (list, tuple)):
                rf = report.report_file
                fixes["report_file"] = rf[0] if rf else ""
            elif report.report_file is not None and not isinstance(report.report_file, str):
                fixes["report_file"] = str(report.report_file)

            if fixes:
                report.write(fixes)
        except Exception:
            # Non-blocking; rendering attempt will surface issues if any remain
            pass

        # Use global model method with explicit report reference to avoid list-as-report_ref bugs
        pdf_tuple = request.env['ir.actions.report']._render_qweb_pdf(report.report_name, [cert.id])
        pdf_content = pdf_tuple[0] if isinstance(pdf_tuple, tuple) else pdf_tuple
        pdf_bytes = pdf_content if isinstance(pdf_content, (bytes, bytearray)) else bytes(pdf_content or b"")

        filename = (cert.certificate_filename or ("CoD-%s.pdf" % (cert.certificate_number or cert.id))).replace(" ", "_")
        headers = [
            ("Content-Type", "application/pdf"),
            ("Content-Disposition", f"attachment; filename={filename}"),
        ]
        return request.make_response(pdf_bytes, headers=headers)

    @http.route("/my/certifications", type="http", auth="user", website=True)
    def portal_certifications(self):
        """
        Portal page for customers to view technician certifications.
        Shows NAID operator certifications with training status.
        """
        # Get all active NAID operator certifications
        certifications = request.env['naid.operator.certification'].search([
            ('active', '=', True)
        ], order='certification_date desc')

        # Get training courses for reference
        training_courses = request.env['slide.channel'].search([
            ('is_published', '=', True)
        ])

        context = {
            'certifications': certifications,
            'training_courses': training_courses,
            'page_name': 'certifications',
        }

        return request.render('records_management.portal_certifications', context)

    @http.route("/my/certifications/<int:certification_id>", type="http", auth="user", website=True)
    def portal_certification_detail(self, certification_id):
        """
        Detailed view of a specific certification.
        """
        certification = request.env['naid.operator.certification'].browse(certification_id)

        # Check if certification exists and user has access
        if not certification.exists():
            return request.redirect('/my/certifications')

        context = {
            'certification': certification,
            'page_name': 'certification_detail',
        }

        return request.render('records_management.portal_certification_detail', context)

    # ============================================================================
    # FEEDBACK ROUTES
    # ============================================================================

    @http.route("/my/feedback/quick", type="http", auth="user", methods=["POST"], website=True)
    def submit_quick_feedback(self, **post):
        """
        Handle quick feedback form submission from portal.
        Creates a portal feedback record with proper validation.
        """
        try:
            # Validate required fields
            feedback_type = post.get('feedback_type')
            feedback_content = post.get('feedback_content')
            priority = post.get('priority', 'medium')

            if not feedback_type or not feedback_content:
                return request.redirect('/my?error=missing_fields')

            # Create feedback record
            feedback_vals = {
                'partner_id': request.env.user.partner_id.id,
                'feedback_type': feedback_type,
                'description': feedback_content,
                'priority': priority,
                'state': 'new',
                'active': True,
                'company_id': request.env.company.id,
            }

            # Add contact preference if provided
            if post.get('contact_back'):
                feedback_vals['contact_back'] = True

            feedback = request.env['portal.feedback'].create(feedback_vals)

            # Create audit log for NAID compliance
            self._create_audit_log(
                "portal_feedback_submitted",
                f"Quick feedback submitted by {request.env.user.partner_id.name}"
            )

            # Send success message
            return request.redirect('/my?success=feedback_submitted')

        except Exception as e:
            _logger.error("Quick feedback submission error: %s", e)
            return request.redirect('/my?error=feedback_failed')

    # ============================================================================
    # CERTIFICATES PORTAL ROUTES
    # ============================================================================

    @http.route(['/my/certificates', '/my/certificates/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_certificates(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        """Display customer destruction certificates in portal"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        Certificate = request.env['destruction.certificate']

        domain = [
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
        ]

        # Date filtering
        if date_begin and date_end:
            domain += [('date', '>=', date_begin), ('date', '<=', date_end)]

        # Sorting options
        searchbar_sortings = {
            'date': {'label': 'Date', 'order': 'date desc'},
            'name': {'label': 'Certificate Number', 'order': 'name'},
            'state': {'label': 'Status', 'order': 'state'},
        }

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Count total certificates
        certificate_count = Certificate.search_count(domain)

        # Pager setup
        pager = request.website.pager(
            url="/my/certificates",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=certificate_count,
            page=page,
            step=self._items_per_page,
        )

        # Get certificates for current page
        certificates = Certificate.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'certificates': certificates,
            'page_name': 'certificates',
            'pager': pager,
            'default_url': '/my/certificates',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })

        return request.render("records_management.portal_my_certificates", values)

    @http.route(['/my/certificate/<int:certificate_id>'], type='http', auth="user", website=True)
    def portal_my_certificate(self, certificate_id=None, **kw):
        """Display individual certificate details"""
        certificate = request.env['destruction.certificate'].browse(certificate_id)

        # Security check
        if not certificate.exists() or certificate.partner_id.commercial_partner_id != request.env.user.partner_id.commercial_partner_id:
            return request.redirect('/my/certificates')

        values = {
            'certificate': certificate,
            'page_name': 'certificate_detail',
        }

        return request.render("records_management.portal_certificate_detail", values)

    @http.route(['/my/certificate/<int:certificate_id>/download'], type='http', auth="user")
    def portal_certificate_download(self, certificate_id=None, **kw):
        """Download certificate PDF"""
        certificate = request.env['destruction.certificate'].browse(certificate_id)

        # Security check
        if not certificate.exists() or certificate.partner_id.commercial_partner_id != request.env.user.partner_id.commercial_partner_id:
            return request.redirect('/my/certificates')

        # Generate PDF report
        pdf = request.env.ref('records_management.action_report_destruction_certificate').sudo()._render_qweb_pdf([certificate.id])[0]

        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', f'attachment; filename="Certificate-{certificate.name}.pdf"'),
        ]

        return request.make_response(pdf, headers=pdfhttpheaders)

    # ============================================================================
    # DOCUMENTS PORTAL ROUTES
    # ============================================================================

    @http.route(['/my/documents', '/my/documents/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_documents(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, **kw):
        """Display customer digital documents in portal"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        Document = request.env['records.document']

        domain = [
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
        ]

        # Search filter
        if search:
            domain += ['|', ('name', 'ilike', search), ('description', 'ilike', search)]

        # Date filtering
        if date_begin and date_end:
            domain += [('create_date', '>=', date_begin), ('create_date', '<=', date_end)]

        # Status filter
        searchbar_filters = {
            'all': {'label': 'All', 'domain': []},
            'active': {'label': 'Active', 'domain': [('active', '=', True)]},
            'flagged': {'label': 'Flagged', 'domain': [('permanently_flagged', '=', True)]},
        }

        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # Sorting options
        searchbar_sortings = {
            'date': {'label': 'Date', 'order': 'create_date desc'},
            'name': {'label': 'Name', 'order': 'name'},
            'type': {'label': 'Type', 'order': 'document_type_id'},
        }

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Count total documents
        document_count = Document.search_count(domain)

        # Pager setup
        pager = request.website.pager(
            url="/my/documents",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'search': search},
            total=document_count,
            page=page,
            step=self._items_per_page,
        )

        # Get documents for current page
        documents = Document.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'documents': documents,
            'page_name': 'documents',
            'pager': pager,
            'default_url': '/my/documents',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
            'search': search or '',
        })

        return request.render("records_management.portal_my_documents", values)

    @http.route(['/my/document/<int:document_id>'], type='http', auth="user", website=True)
    def portal_my_document(self, document_id=None, **kw):
        """Display individual document details"""
        document = request.env['records.document'].browse(document_id)

        # Security check
        if not document.exists() or document.partner_id.commercial_partner_id != request.env.user.partner_id.commercial_partner_id:
            return request.redirect('/my/documents')

        values = {
            'document': document,
            'page_name': 'document_detail',
        }

        return request.render("records_management.portal_document_detail", values)

    @http.route(['/my/document/<int:document_id>/download'], type='http', auth="user")
    def portal_document_download(self, document_id=None, **kw):
        """Download document attachment"""
        document = request.env['records.document'].browse(document_id)

        # Security check
        if not document.exists() or document.partner_id.commercial_partner_id != request.env.user.partner_id.commercial_partner_id:
            return request.redirect('/my/documents')

        # Get attachment if exists
        if document.attachment_id:
            return request.redirect(f'/web/content/{document.attachment_id.id}?download=true')
        else:
            return request.redirect('/my/documents?error=no_attachment')

    # ============================================================================
    # CONTAINER INVENTORY PORTAL ROUTES (FIXED - USES CORRECT MODEL & FIELDS)
    # ============================================================================

    @http.route(['/my/containers', '/my/containers/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_containers(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, **kw):
        """
        Display container inventory for portal users
        FIXED: Uses records.container model with correct ownership fields
        Previously broken: used stock.quant with wrong owner_id field
        """
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        Container = request.env['records.container']

        # Build domain - use hierarchical access for stock_owner_id
        # Users can see containers where:
        # - partner_id matches their company (direct ownership)
        # - OR stock_owner_id is themselves or any child department (hierarchical ownership)
        domain = [
            '|',
            ('partner_id', '=', partner.id),
            ('stock_owner_id', 'child_of', partner.id),
        ]

        # Search filter
        if search:
            domain += [
                '|', '|', '|', '|',
                ('name', 'ilike', search),
                ('barcode', 'ilike', search),
                ('temp_barcode', 'ilike', search),
                ('department_id.name', 'ilike', search),
                ('location_id.name', 'ilike', search),
            ]

        # Date filtering
        if date_begin and date_end:
            domain += [('create_date', '>=', date_begin), ('create_date', '<=', date_end)]

        # Status filter
        searchbar_filters = {
            'all': {'label': 'All Containers', 'domain': []},
            'active': {'label': 'Active', 'domain': [('state', '=', 'active')]},
            'in_storage': {'label': 'In Storage', 'domain': [('state', '=', 'in_storage')]},
            'in_transit': {'label': 'In Transit', 'domain': [('state', '=', 'in_transit')]},
            'pending': {'label': 'Pending Pickup', 'domain': [('state', '=', 'pending_pickup')]},
            'destroyed': {'label': 'Destroyed', 'domain': [('state', '=', 'destroyed')]},
        }

        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # Sorting options
        searchbar_sortings = {
            'date': {'label': 'Recent First', 'order': 'write_date desc'},
            'name': {'label': 'Container Name', 'order': 'name'},
            'barcode': {'label': 'Barcode', 'order': 'barcode'},
            'location': {'label': 'Location', 'order': 'location_id'},
            'state': {'label': 'Status', 'order': 'state'},
        }

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Count total containers
        container_count = Container.search_count(domain)

        # Pager setup
        pager = request.website.pager(
            url="/my/containers",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'search': search},
            total=container_count,
            page=page,
            step=self._items_per_page,
        )

        # Get containers for current page
        containers = Container.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'containers': containers,
            'page_name': 'containers',
            'pager': pager,
            'default_url': '/my/containers',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
            'search': search or '',
            'container_count': container_count,
        })

        return request.render("records_management.portal_my_containers", values)

    @http.route(['/my/container/<int:container_id>'], type='http', auth="user", website=True)
    def portal_my_container(self, container_id=None, **kw):
        """Display individual container details"""
        container = request.env['records.container'].browse(container_id)
        partner = request.env.user.partner_id

        # Security check - verify ownership via partner_id OR hierarchical stock_owner_id
        # Check if container would be visible under the same domain as portal_my_containers
        visible_containers = request.env['records.container'].search([
            ('id', '=', container_id),
            '|',
            ('partner_id', '=', partner.id),
            ('stock_owner_id', 'child_of', partner.id),
        ])
        has_access = container.exists() and bool(visible_containers)

        if not has_access:
            return request.redirect('/my/containers')

        values = {
            'container': container,
            'page_name': 'container_detail',
        }

        return request.render("records_management.portal_container_detail", values)

    @http.route(['/my/inventory'], type='http', auth="user", website=True)
    def portal_my_inventory(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, inventory_type=None, **kw):
        """
        Display comprehensive inventory for portal users including:
        - Records containers (boxes)
        - File folders within containers
        - Individual documents
        - Temp inventory items
        - PDF scans/attachments
        """
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        commercial_partner = partner.commercial_partner_id

        # Initialize inventory collections
        all_inventory_items = []
        total_count = 0

        # Search term for filtering across all inventory types
        search_term = search or ''

        # Inventory type filter
        inventory_type_filters = {
            'all': {'label': 'All Inventory', 'types': ['containers', 'files', 'documents', 'temp']},
            'containers': {'label': 'Containers/Boxes', 'types': ['containers']},
            'files': {'label': 'File Folders', 'types': ['files']},
            'documents': {'label': 'Documents', 'types': ['documents']},
            'temp': {'label': 'Temp Inventory', 'types': ['temp']},
        }

        if not inventory_type:
            inventory_type = 'all'

        active_types = inventory_type_filters[inventory_type]['types']

        # 1. CONTAINERS/BOXES
        if 'containers' in active_types:
            Container = request.env['records.container']
            container_domain = [('partner_id', '=', commercial_partner.id)]

            if search_term:
                container_domain += ['|', '|', ('name', 'ilike', search_term),
                                   ('barcode', 'ilike', search_term),
                                   ('temp_barcode', 'ilike', search_term)]

            containers = Container.search(container_domain, order='create_date desc')

            for container in containers:
                all_inventory_items.append({
                    'type': 'container',
                    'id': container.id,
                    'name': container.name,
                    'barcode': container.barcode or container.temp_barcode,
                    'description': f"Container - {container.state.title() if container.state else 'Active'}",
                    'location': container.current_location_id.name if container.current_location_id else 'Unknown',
                    'date': container.create_date,
                    'state': container.state or 'active',
                    'model': 'records.container',
                    'icon': 'fa-archive',
                    'color': 'primary'
                })

        # 2. FILE FOLDERS
        if 'files' in active_types:
            FileFolder = request.env['records.file']
            file_domain = [('partner_id', '=', commercial_partner.id)]

            if search_term:
                file_domain += ['|', '|', ('name', 'ilike', search_term),
                              ('barcode', 'ilike', search_term),
                              ('description', 'ilike', search_term)]

            file_folders = FileFolder.search(file_domain, order='create_date desc')

            for file_folder in file_folders:
                all_inventory_items.append({
                    'type': 'file',
                    'id': file_folder.id,
                    'name': file_folder.name,
                    'barcode': file_folder.barcode,
                    'description': f"File Folder - {file_folder.description or 'No description'}",
                    'location': file_folder.current_location_id.name if file_folder.current_location_id else 'Unknown',
                    'date': file_folder.create_date,
                    'state': file_folder.state or 'active',
                    'model': 'records.file',
                    'icon': 'fa-folder',
                    'color': 'info'
                })

        # 3. DOCUMENTS (including PDF scans)
        if 'documents' in active_types:
            Document = request.env['records.document']
            doc_domain = [('partner_id', '=', commercial_partner.id)]

            if search_term:
                doc_domain += ['|', '|', ('name', 'ilike', search_term),
                              ('temp_barcode', 'ilike', search_term),
                              ('description', 'ilike', search_term)]

            documents = Document.search(doc_domain, order='create_date desc')

            for document in documents:
                # Check if document has PDF attachments/scans
                attachments = request.env['ir.attachment'].search([
                    ('res_model', '=', 'records.document'),
                    ('res_id', '=', document.id),
                    ('mimetype', 'like', 'pdf')
                ])

                attachment_info = f" - {len(attachments)} PDF scan(s)" if attachments else ""

                all_inventory_items.append({
                    'type': 'document',
                    'id': document.id,
                    'name': document.name,
                    'barcode': document.temp_barcode,
                    'description': f"Document - {document.description or 'No description'}{attachment_info}",
                    'location': document.container_id.current_location_id.name if document.container_id and document.container_id.current_location_id else 'Unknown',
                    'date': document.create_date,
                    'state': document.state or 'active',
                    'model': 'records.document',
                    'icon': 'fa-file-text',
                    'color': 'success',
                    'has_pdf': bool(attachments),
                    'pdf_count': len(attachments)
                })

        # 4. TEMP INVENTORY
        if 'temp' in active_types:
            TempInventory = request.env['temp.inventory']
            temp_domain = [('partner_id', '=', partner.id)]

            if search_term:
                temp_domain += ['|', ('name', 'ilike', search_term), ('description', 'ilike', search_term)]

            temp_inventory = TempInventory.search(temp_domain, order='date_created desc')

            for temp_item in temp_inventory:
                all_inventory_items.append({
                    'type': 'temp',
                    'id': temp_item.id,
                    'name': temp_item.name,
                    'barcode': temp_item.temp_barcode or '',
                    'description': f"Temp Item - {temp_item.description or 'No description'}",
                    'location': 'Temporary',
                    'date': temp_item.date_created,
                    'state': temp_item.state or 'draft',
                    'model': 'temp.inventory',
                    'icon': 'fa-clock-o',
                    'color': 'warning'
                })

        # Sort all inventory items
        sortby_options = {
            'date': lambda x: x['date'],
            'name': lambda x: x['name'].lower(),
            'type': lambda x: x['type'],
            'state': lambda x: x['state']
        }

        if not sortby:
            sortby = 'date'

        reverse_sort = sortby == 'date'  # Most recent first for dates
        all_inventory_items.sort(key=sortby_options.get(sortby, sortby_options['date']), reverse=reverse_sort)

        # Apply pagination
        total_count = len(all_inventory_items)
        items_per_page = self._items_per_page
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        inventory_records = all_inventory_items[start_index:end_index]

        # Pager setup
        pager = request.website.pager(
            url="/my/inventory",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'search': search, 'inventory_type': inventory_type},
            total=total_count,
            page=page,
            step=items_per_page,
        )

        # Sorting options
        searchbar_sortings = {
            'date': {'label': 'Recent First', 'order': 'date desc'},
            'name': {'label': 'Name A-Z', 'order': 'name asc'},
            'type': {'label': 'Type', 'order': 'type asc'},
            'state': {'label': 'Status', 'order': 'state asc'},
        }

        values.update({
            'inventory_records': inventory_records,
            'page_name': 'inventory',
            'pager': pager,
            'default_url': '/my/inventory',
            'searchbar_sortings': searchbar_sortings,
            'inventory_type_filters': inventory_type_filters,
            'sortby': sortby,
            'inventory_type': inventory_type,
            'search': search_term,
            'inventory_count': total_count,
            'commercial_partner': commercial_partner,
        })

        return request.render("records_management.portal_my_inventory", values)

    # ============================================================================
    # INVENTORY TAB ROUTES (Backend-style list/detail views)
    # ============================================================================

    @http.route(['/my/inventory/containers'], type='http', auth="user", website=True)
    def portal_inventory_containers(self, page=1, sortby=None, filterby=None, search=None, **kw):
        """Containers tab - backend-style list view with bulk actions"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id.commercial_partner_id

        Container = request.env['records.container']
        domain = [('partner_id', '=', partner.id)]

        if search:
            domain += ['|', '|', ('name', 'ilike', search), ('barcode', 'ilike', search), ('temp_barcode', 'ilike', search)]

        # Filtering options
        searchbar_filters = {
            'all': {'label': 'All Containers', 'domain': []},
            'active': {'label': 'Active', 'domain': [('state', '=', 'active')]},
            'storage': {'label': 'In Storage', 'domain': [('state', '=', 'in_storage')]},
            'transit': {'label': 'In Transit', 'domain': [('state', '=', 'in_transit')]},
        }

        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # Sorting options
        searchbar_sortings = {
            'name': {'label': 'Name', 'order': 'name'},
            'date': {'label': 'Date Created', 'order': 'create_date desc'},
            'location': {'label': 'Location', 'order': 'current_location_id'},
        }

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Get containers
        container_count = Container.search_count(domain)
        pager = request.website.pager(
            url="/my/inventory/containers",
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search},
            total=container_count,
            page=page,
            step=20,
        )

        containers = Container.search(domain, order=order, limit=20, offset=pager['offset'])

        values.update({
            'containers': containers,
            'page_name': 'inventory_containers',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
            'search': search or '',
            'container_count': container_count,
        })

        return request.render("records_management.portal_inventory_containers", values)

    @http.route(['/my/inventory/files'], type='http', auth="user", website=True)
    def portal_inventory_files(self, page=1, sortby=None, filterby=None, search=None, **kw):
        """File folders tab - backend-style list view"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id.commercial_partner_id

        RecordsFile = request.env['records.file']
        domain = [('partner_id', '=', partner.id)]

        if search:
            domain += ['|', '|', ('name', 'ilike', search), ('barcode', 'ilike', search), ('description', 'ilike', search)]

        # Get files
        file_count = RecordsFile.search_count(domain)
        pager = request.website.pager(
            url="/my/inventory/files",
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search},
            total=file_count,
            page=page,
            step=20,
        )

        files = RecordsFile.search(domain, order='create_date desc', limit=20, offset=pager['offset'])

        values.update({
            'files': files,
            'page_name': 'inventory_files',
            'pager': pager,
            'search': search or '',
            'file_count': file_count,
        })

        return request.render("records_management.portal_inventory_files", values)

    @http.route(['/my/inventory/documents'], type='http', auth="user", website=True)
    def portal_inventory_documents(self, page=1, sortby=None, filterby=None, search=None, **kw):
        """Documents tab - backend-style list view with PDF scan info"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id.commercial_partner_id

        Document = request.env['records.document']
        domain = [('partner_id', '=', partner.id)]

        if search:
            domain += ['|', '|', ('name', 'ilike', search), ('temp_barcode', 'ilike', search), ('description', 'ilike', search)]

        # Get documents
        doc_count = Document.search_count(domain)
        pager = request.website.pager(
            url="/my/inventory/documents",
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search},
            total=doc_count,
            page=page,
            step=20,
        )

        documents = Document.search(domain, order='create_date desc', limit=20, offset=pager['offset'])

        # Get PDF scan info for each document
        for doc in documents:
            doc.pdf_scans = request.env['ir.attachment'].search([
                ('res_model', '=', 'records.document'),
                ('res_id', '=', doc.id),
                ('mimetype', 'like', 'pdf')
            ])

        values.update({
            'documents': documents,
            'page_name': 'inventory_documents',
            'pager': pager,
            'search': search or '',
            'doc_count': doc_count,
        })

        return request.render("records_management.portal_inventory_documents", values)

    @http.route(['/my/inventory/temp'], type='http', auth="user", website=True)
    def portal_inventory_temp(self, page=1, sortby=None, filterby=None, search=None, **kw):
        """Temp inventory tab - backend-style list view"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        TempInventory = request.env['temp.inventory']
        domain = [('partner_id', '=', partner.id)]

        if search:
            domain += ['|', ('name', 'ilike', search), ('description', 'ilike', search)]

        # Get temp inventory
        temp_count = TempInventory.search_count(domain)
        pager = request.website.pager(
            url="/my/inventory/temp",
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search},
            total=temp_count,
            page=page,
            step=20,
        )

        temp_items = TempInventory.search(domain, order='date_created desc', limit=20, offset=pager['offset'])

        values.update({
            'temp_items': temp_items,
            'page_name': 'inventory_temp',
            'pager': pager,
            'search': search or '',
            'temp_count': temp_count,
        })

        return request.render("records_management.portal_inventory_temp", values)

    # ============================================================================
    # INDIVIDUAL ITEM DETAIL ROUTES
    # ============================================================================

    @http.route(['/my/inventory/container/<int:container_id>'], type='http', auth="user", website=True)
    def portal_container_detail(self, container_id, **kw):
        """Individual container detail view with management options"""
        container = request.env['records.container'].browse(container_id)

        # Security check
        if container.partner_id != request.env.user.partner_id.commercial_partner_id:
            return request.not_found()

        # Get files in this container
        files_in_container = request.env['records.file'].search([
            ('container_id', '=', container_id),
            ('partner_id', '=', container.partner_id.id)
        ])

        values = {
            'container': container,
            'files_in_container': files_in_container,
            'page_name': 'container_detail',
        }

        return request.render("records_management.portal_container_detail", values)

    @http.route(['/my/inventory/file/<int:file_id>'], type='http', auth="user", website=True)
    def portal_file_detail(self, file_id, **kw):
        """Individual file folder detail view"""
        file_folder = request.env['records.file'].browse(file_id)

        # Security check
        if file_folder.partner_id != request.env.user.partner_id.commercial_partner_id:
            return request.not_found()

        # Get documents in this file folder
        documents_in_file = request.env['records.document'].search([
            ('file_folder_id', '=', file_id),
            ('partner_id', '=', file_folder.partner_id.id)
        ])

        values = {
            'file_folder': file_folder,
            'documents_in_file': documents_in_file,
            'page_name': 'file_detail',
        }

        return request.render("records_management.portal_file_detail", values)

    @http.route(['/my/inventory/document/<int:document_id>'], type='http', auth="user", website=True)
    def portal_document_detail(self, document_id, **kw):
        """Individual document detail view with PDF scans"""
        document = request.env['records.document'].browse(document_id)

        # Security check
        if document.partner_id != request.env.user.partner_id.commercial_partner_id:
            return request.not_found()

        # Get PDF scans
        pdf_scans = request.env['ir.attachment'].search([
            ('res_model', '=', 'records.document'),
            ('res_id', '=', document_id),
            ('mimetype', 'like', 'pdf')
        ])

        values = {
            'document': document,
            'pdf_scans': pdf_scans,
            'page_name': 'document_detail',
        }

        return request.render("records_management.portal_document_detail", values)

    # ============================================================================
    # BULK ACTION ROUTES
    # ============================================================================

    @http.route(['/my/inventory/bulk/retrieve'], type='json', auth='user', methods=['POST'])
    def portal_bulk_retrieve(self, **post):
        """Request retrieval for selected items"""
        if not (request.env.user.has_group('records_management.group_portal_company_admin') or
                request.env.user.has_group('records_management.group_portal_department_admin') or
                request.env.user.has_group('records_management.group_portal_department_user')):
            return {'success': False, 'error': 'Insufficient permissions'}

        try:
            item_ids = post.get('item_ids', [])
            item_type = post.get('item_type')  # 'container', 'file', 'document'

            # Create retrieval request
            portal_request = request.env['portal.request'].create({
                'partner_id': request.env.user.partner_id.commercial_partner_id.id,
                'request_type': 'retrieval',
                'retrieval_items': json.dumps({
                    'type': item_type,
                    'ids': item_ids,
                    'action': 'retrieve'
                }),
                'notes': post.get('notes', ''),
                'state': 'draft'
            })

            return {
                'success': True,
                'message': f'Retrieval request created for {len(item_ids)} items',
                'request_id': portal_request.id
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route(['/my/inventory/bulk/destroy'], type='json', auth='user', methods=['POST'])
    def portal_bulk_destroy(self, **post):
        """Request destruction for selected items"""
        if not (request.env.user.has_group('records_management.group_portal_company_admin') or
                request.env.user.has_group('records_management.group_portal_department_admin') or
                request.env.user.has_group('records_management.group_portal_department_user')):
            return {'success': False, 'error': 'Insufficient permissions'}

        try:
            item_ids = post.get('item_ids', [])
            item_type = post.get('item_type')

            # Create destruction request
            portal_request = request.env['portal.request'].create({
                'partner_id': request.env.user.partner_id.commercial_partner_id.id,
                'request_type': 'destruction',
                'retrieval_items': json.dumps({
                    'type': item_type,
                    'ids': item_ids,
                    'action': 'destroy',
                    'method': post.get('destruction_method', 'shredding')
                }),
                'notes': post.get('notes', ''),
                'state': 'draft'
            })

            return {
                'success': True,
                'message': f'Destruction request created for {len(item_ids)} items',
                'request_id': portal_request.id
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route(['/my/inventory/bulk/pickup'], type='json', auth='user', methods=['POST'])
    def portal_bulk_pickup(self, **post):
        """Schedule pickup for items at customer location"""
        if not (request.env.user.has_group('records_management.group_portal_company_admin') or
                request.env.user.has_group('records_management.group_portal_department_admin') or
                request.env.user.has_group('records_management.group_portal_department_user')):
            return {'success': False, 'error': 'Insufficient permissions'}

        try:
            item_ids = post.get('item_ids', [])
            item_type = post.get('item_type')

            # Create pickup request
            portal_request = request.env['portal.request'].create({
                'partner_id': request.env.user.partner_id.commercial_partner_id.id,
                'request_type': 'pickup',
                'retrieval_items': json.dumps({
                    'type': item_type,
                    'ids': item_ids,
                    'action': 'pickup'
                }),
                'notes': post.get('notes', ''),
                'pickup_date': post.get('pickup_date'),
                'state': 'draft'
            })

            return {
                'success': True,
                'message': f'Pickup request created for {len(item_ids)} items',
                'request_id': portal_request.id
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============================================================================
    # ITEM MANAGEMENT ROUTES
    # ============================================================================

    @http.route(['/my/inventory/container/<int:container_id>/update'], type='json', auth='user', methods=['POST'])
    def portal_update_container(self, container_id, **post):
        """Update container information"""
        try:
            container = request.env['records.container'].browse(container_id)

            # Security check
            if container.partner_id != request.env.user.partner_id.commercial_partner_id:
                return {'success': False, 'error': 'Access denied'}

            # Update allowed fields
            update_vals = {}
            if 'sequence_range' in post:
                update_vals['sequence_range'] = post['sequence_range']
            if 'notes' in post:
                update_vals['notes'] = post['notes']

            container.write(update_vals)

            return {'success': True, 'message': 'Container updated successfully'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route(['/my/inventory/file/add_to_container'], type='json', auth='user', methods=['POST'])
    def portal_add_file_to_container(self, **post):
        """Add selected files to a container"""
        try:
            file_ids = post.get('file_ids', [])
            container_id = post.get('container_id')

            files = request.env['records.file'].browse(file_ids)
            container = request.env['records.container'].browse(container_id)

            # Security check
            partner = request.env.user.partner_id.commercial_partner_id
            if container.partner_id != partner or any(f.partner_id != partner for f in files):
                return {'success': False, 'error': 'Access denied'}

            # Update file locations
            files.write({'container_id': container_id})

            return {
                'success': True,
                'message': f'{len(files)} files added to container {container.name}'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ============================================================================
    # OVERVIEW TAB DATA ROUTES
    # ============================================================================

    @http.route(['/my/inventory/counts'], type='http', auth='user', website=True)
    def portal_inventory_counts(self, **kw):
        """Get inventory counts for overview dashboard"""
        partner = request.env.user.partner_id.commercial_partner_id

        counts = {
            'containers': request.env['records.container'].search_count([('partner_id', '=', partner.id)]),
            'files': request.env['records.file'].search_count([('partner_id', '=', partner.id)]),
            'documents': request.env['records.document'].search_count([('partner_id', '=', partner.id)]),
            'temp': request.env['temp.inventory'].search_count([('partner_id', '=', request.env.user.partner_id.id)]),
        }

        return request.make_response(
            json.dumps(counts),
            headers=[('Content-Type', 'application/json')]
        )

    @http.route(['/my/inventory/recent_activity'], type='http', auth='user', website=True)
    def portal_recent_activity(self, **kw):
        """Get recent activity for overview dashboard"""
        partner = request.env.user.partner_id.commercial_partner_id

        # Get recent containers
        recent_containers = request.env['records.container'].search([
            ('partner_id', '=', partner.id)
        ], order='create_date desc', limit=5)

        # Get recent requests
        recent_requests = request.env['portal.request'].search([
            ('partner_id', '=', partner.id)
        ], order='create_date desc', limit=5)

        activity_html = '<ul class="list-unstyled">'

        for container in recent_containers:
            activity_html += f'''
            <li class="mb-2">
                <i class="fa fa-archive text-primary"></i>
                <strong>Container:</strong> {container.name}
                <small class="text-muted">- Created {container.create_date.strftime('%Y-%m-%d')}</small>
            </li>
            '''

        for req in recent_requests:
            activity_html += f'''
            <li class="mb-2">
                <i class="fa fa-paper-plane text-info"></i>
                <strong>Request:</strong> {req.request_type.title()}
                <small class="text-muted">- {req.create_date.strftime('%Y-%m-%d')}</small>
            </li>
            '''

        if not recent_containers and not recent_requests:
            activity_html += '<li class="text-muted">No recent activity</li>'

        activity_html += '</ul>'

        response_data = {'html': activity_html}

        return request.make_response(
            json.dumps(response_data),
            headers=[('Content-Type', 'application/json')]
        )

    @http.route(['/my/inventory/files/available'], type='http', auth='user', website=True)
    def portal_available_files(self, **kw):
        """Get files not assigned to any container"""
        partner = request.env.user.partner_id.commercial_partner_id

        available_files = request.env['records.file'].search([
            ('partner_id', '=', partner.id),
            ('container_id', '=', False)  # Not in any container
        ])

        files_data = []
        for file_folder in available_files:
            files_data.append({
                'id': file_folder.id,
                'name': file_folder.name,
                'barcode': file_folder.barcode or '',
                'description': file_folder.description or ''
            })

        response_data = {'files': files_data}

        return request.make_response(
            json.dumps(response_data),
            headers=[('Content-Type', 'application/json')]
        )

    # ============================================================================
    # BARCODE GENERATION ROUTES
    # ============================================================================

    @http.route(['/records_management/portal/generate_container_barcode'], type='json', auth='user', website=True)
    def generate_container_barcode(self, **kw):
        """Generate barcode for records.container using ir.sequence"""
        try:
            Container = request.env['records.container']
            # Use your container sequence
            barcode_value = request.env['ir.sequence'].next_by_code('records.container.barcode')

            container = Container.create({
                'name': _('Container %s') % barcode_value,
                'barcode': barcode_value,
                'partner_id': request.env.user.partner_id.id,
            })

            return {
                'success': True,
                'barcode': {
                    'id': container.id,
                    'name': container.barcode,
                    'barcode_type': 'container',
                    'barcode_format': 'code128',
                    'sequence_code': 'records.container.barcode',
                    'state': container.state,
                    'barcode_image': container.barcode_image,
                }
            }
        except Exception as e:
            _logger.exception("Container barcode generation failed")
            return {'success': False, 'error': str(e)}

    @http.route(['/records_management/portal/generate_file_barcode'], type='json', auth='user', website=True)
    def generate_file_barcode(self, **kw):
        """Generate barcode for records.file using ir.sequence"""
        try:
            File = request.env['records.file']
            barcode_value = request.env['ir.sequence'].next_by_code('records.file.barcode')

            file_record = File.create({
                'name': _('File %s') % barcode_value,
                'barcode': barcode_value,
                'partner_id': request.env.user.partner_id.id,
            })

            return {
                'success': True,
                'barcode': {
                    'id': file_record.id,
                    'name': file_record.barcode,
                    'barcode_type': 'file',
                    'barcode_format': 'code128',
                    'sequence_code': 'records.file.barcode',
                    'state': file_record.state,
                    'barcode_image': file_record.barcode_image,
                }
            }
        except Exception as e:
            _logger.exception("File barcode generation failed")
            return {'success': False, 'error': str(e)}

    @http.route(['/records_management/portal/generate_temp_barcode'], type='json', auth='user', website=True)
    def generate_temp_barcode(self, **kw):
        """Generate temporary barcode using ir.sequence"""
        try:
            TempBarcode = request.env['records.temp.barcode']
            barcode_value = request.env['ir.sequence'].next_by_code('records.temp.barcode')

            temp_barcode = TempBarcode.create({
                'name': barcode_value,
                'barcode': barcode_value,
                'partner_id': request.env.user.partner_id.id,
                'expiry_date': fields.Date.today() + relativedelta(days=30),
            })

            return {
                'success': True,
                'barcode': {
                    'id': temp_barcode.id,
                    'name': temp_barcode.barcode,
                    'barcode_type': 'temp',
                    'barcode_format': 'code128',
                    'sequence_code': 'records.temp.barcode',
                    'state': 'active',
                    'barcode_image': temp_barcode.barcode_image,
                }
            }
        except Exception as e:
            _logger.exception("Temp barcode generation failed")
            return {'success': False, 'error': str(e)}

    # ============================================================================
    # PORTAL INVENTORY MANAGEMENT ROUTES
    # ============================================================================

    @http.route('/my/inventory/add_temp', type='json', auth='user', methods=['POST'])
    def add_temp_inventory(self, **post):
        """
        Add temporary inventory item for portal users.
        Requires appropriate portal permissions.
        """
        # Check user permissions
        user = request.env.user
        if not (user.has_group('records_management.group_portal_company_admin') or
                user.has_group('records_management.group_portal_department_admin') or
                user.has_group('records_management.group_portal_department_user')):
            return {
                'success': False,
                'error': 'Insufficient permissions. You need admin or department user access to add inventory.'
            }

        try:
            item_type = post.get('type', '').strip()
            description = post.get('description', '').strip()

            if not item_type or not description:
                return {
                    'success': False,
                    'error': 'Type and description are required.'
                }

            # Create temp inventory record
            temp_inventory = request.env['temp.inventory'].create({
                'name': description,
                'description': description,
                'partner_id': user.partner_id.id,
                'state': 'draft',
            })

            # Generate barcode using sequence
            barcode = request.env['ir.sequence'].next_by_code('temp.inventory') or f"TEMP-{temp_inventory.id}"

            # Update the temp inventory with the barcode in the name if needed
            if temp_inventory.name == description:
                temp_inventory.write({'name': f"{description} ({barcode})"})

            # Create audit log
            self._create_audit_log(
                "temp_inventory_created",
                f"Temp inventory created by portal user: {description}"
            )

            return {
                'success': True,
                'barcode': barcode,
                'temp_inventory_id': temp_inventory.id,
                'message': f'Temporary inventory "{description}" created successfully with barcode {barcode}.'
            }

        except Exception as e:
            _logger.error("Add temp inventory error: %s", e)
            return {
                'success': False,
                'error': 'Failed to create temporary inventory. Please try again.'
            }

    @http.route('/my/inventory/add_to_pickup', type='json', auth='user', methods=['POST'])
    def add_to_pickup(self, **post):
        """
        Add inventory item to pickup request.
        Requires appropriate portal permissions.
        """
        # Check user permissions
        user = request.env.user
        if not (user.has_group('records_management.group_portal_company_admin') or
                user.has_group('records_management.group_portal_department_admin') or
                user.has_group('records_management.group_portal_department_user')):
            return {
                'success': False,
                'error': 'Insufficient permissions. You need admin or department user access to request pickup.'
            }

        try:
            item_id = post.get('item_id')
            if not item_id:
                return {
                    'success': False,
                    'error': 'Item ID is required.'
                }

            # Get the temp inventory item
            temp_item = request.env['temp.inventory'].browse(int(item_id))
            if not temp_item.exists() or temp_item.partner_id.id != user.partner_id.id:
                return {
                    'success': False,
                    'error': 'Item not found or access denied.'
                }

            # Create or find existing pickup request
            pickup_request = request.env['portal.request'].search([
                ('partner_id', '=', user.partner_id.id),
                ('request_type', '=', 'pickup'),
                ('state', 'in', ['draft', 'submitted'])
            ], limit=1)

            if not pickup_request:
                pickup_request = request.env['portal.request'].create({
                    'partner_id': user.partner_id.id,
                    'request_type': 'pickup',
                    'state': 'draft',
                    'description': f'Pickup request for temp inventory items',
                    'retrieval_items': json.dumps([]),
                })

            # Add item to pickup request - update retrieval_items JSON
            existing_items = json.loads(pickup_request.retrieval_items or '[]')
            existing_items.append({
                'type': 'temp_inventory',
                'id': temp_item.id,
                'name': temp_item.name,
                'description': temp_item.description or '',
            })
            pickup_request.write({
                'retrieval_items': json.dumps(existing_items)
            })

            # Create audit log
            self._create_audit_log(
                "temp_inventory_added_to_pickup",
                f"Temp inventory {temp_item.name} added to pickup request by portal user"
            )

            return {
                'success': True,
                'pickup_request_id': pickup_request.id,
                'message': f'Item "{temp_item.name}" added to pickup request.'
            }

        except Exception as e:
            _logger.error("Add to pickup error: %s", e)
            return {
                'success': False,
                'error': 'Failed to add item to pickup request. Please try again.'
            }

    @http.route('/my/inventory/request_destruction', type='json', auth='user', methods=['POST'])
    def request_destruction(self, **post):
        """
        Request destruction for selected inventory items.
        Requires appropriate portal permissions.
        """
        # Check user permissions
        user = request.env.user
        if not (user.has_group('records_management.group_portal_company_admin') or
                user.has_group('records_management.group_portal_department_admin') or
                user.has_group('records_management.group_portal_department_user')):
            return {
                'success': False,
                'error': 'Insufficient permissions. You need admin or department user access to request destruction.'
            }

        try:
            item_ids = post.get('item_ids', [])
            if not item_ids:
                return {
                    'success': False,
                    'error': 'No items selected for destruction.'
                }

            # Get temp inventory items
            temp_items = request.env['temp.inventory'].browse(item_ids)
            # Verify ownership
            for item in temp_items:
                if not item.exists() or item.partner_id.id != user.partner_id.id:
                    return {
                        'success': False,
                        'error': 'Access denied for one or more selected items.'
                    }

            # Create destruction request with temp inventory data in retrieval_items
            items_data = []
            for item in temp_items:
                items_data.append({
                    'type': 'temp_inventory',
                    'id': item.id,
                    'name': item.name,
                    'description': item.description or '',
                })

            destruction_request = request.env['portal.request'].create({
                'partner_id': user.partner_id.id,
                'request_type': 'destruction',
                'state': 'draft',
                'description': f'Destruction request for {len(temp_items)} items',
                'retrieval_items': json.dumps(items_data)
            })

            # Create audit log
            self._create_audit_log(
                "destruction_request_created",
                f"Destruction request created by portal user for {len(temp_items)} items"
            )

            return {
                'success': True,
                'destruction_request_id': destruction_request.id,
                'message': f'Destruction request created for {len(temp_items)} items.'
            }

        except Exception as e:
            _logger.error("Request destruction error: %s", e)
            return {
                'success': False,
                'error': 'Failed to create destruction request. Please try again.'
            }

    # ============================================================================
    # DOCUMENT RETRIEVAL PORTAL ROUTES
    # ============================================================================

    @http.route(['/my/document-retrieval'], type='http', auth='user', website=True)
    def portal_document_retrieval(self, **kw):
        """Document retrieval request form for portal users"""
        partner = request.env.user.partner_id

        # Get containers owned by the user's company (stock_owner filter)
        containers = request.env['records.container'].sudo().search([
            ('stock_owner', '=', partner.id)
        ])

        # Get documents from those containers
        documents = request.env['records.document'].sudo().search([
            ('container_id', 'in', containers.ids)
        ])

        # Prepare options for frontend
        container_options = [(c.id, c.name) for c in containers]
        document_options = [(d.id, d.name) for d in documents]

        values = {
            'page_name': 'document_retrieval',
            'containers': containers,
            'documents': documents,
            'container_options': json.dumps(container_options),
            'document_options': json.dumps(document_options),
        }
        return request.render('records_management.portal_document_retrieval_template', values)

    @http.route(['/my/document-retrieval/calculate-price'], type='json', auth='user')
    def calculate_retrieval_price(self, priority='standard', item_count=1, **kw):
        """Calculate pricing for document retrieval request"""
        # Get pricing configuration
        config = request.env['rm.module.configurator'].sudo().search([], limit=1)

        base_retrieval = config.retrieval_base_cost or 25.0
        base_delivery = config.delivery_base_cost or 15.0
        priority_multiplier = 1.5 if priority == 'urgent' else 1.0

        pricing = {
            'base_retrieval_cost': base_retrieval,
            'priority_item_cost': (base_retrieval * priority_multiplier - base_retrieval) * item_count,
            'base_delivery_cost': base_delivery,
            'priority_order_cost': (base_delivery * priority_multiplier - base_delivery),
            'total_cost': (base_retrieval + base_delivery) * priority_multiplier * item_count,
            'has_custom_rates': False
        }

        return pricing

    @http.route(['/my/document-retrieval/submit'], type='http', auth='user', methods=['POST'], csrf=True, website=True)
    def submit_retrieval_request(self, **post):
        """Submit a document retrieval request"""
        partner = request.env.user.partner_id

        # Parse items data
        items_data = json.loads(post.get('items_data', '[]'))

        # Create portal request
        request_vals = {
            'partner_id': partner.id,
            'request_type': 'retrieval',
            'priority': post.get('priority', 'standard'),
            'description': post.get('notes', ''),
            'retrieval_items': json.dumps(items_data),
        }

        new_request = request.env['portal.request'].sudo().create(request_vals)

        # Redirect to request confirmation page
        return request.redirect('/my/requests/%s' % new_request.id)
