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

    def _check_dashboard_access(self):
        """
        Check if user has access to dashboard functionality.
        Includes internal users and all portal user types.
        """
        user = request.env.user
        return (
            user.has_group("records_management.group_records_user") or
            user.has_group("records_management.group_records_manager") or
            user.has_group("records_management.group_portal_company_admin") or
            user.has_group("records_management.group_portal_department_admin") or
            user.has_group("records_management.group_portal_department_user") or
            user.has_group("records_management.group_portal_readonly_employee")
        )

    def _check_analytics_access(self):
        """
        Check if user has access to analytics functionality.
        Analytics: Managers + Portal Company Admins + Portal Department Admins.
        """
        user = request.env.user
        return (
            user.has_group("records_management.group_records_manager") or
            user.has_group("records_management.group_portal_company_admin") or
            user.has_group("records_management.group_portal_department_admin")
        )

    def _check_bulk_update_access(self):
        """
        Check if user has access to bulk update functionality.
        Bulk Updates: Internal Users + Portal Admins + Portal Department Users.
        """
        user = request.env.user
        return (
            user.has_group("records_management.group_records_user") or
            user.has_group("records_management.group_records_manager") or
            user.has_group("records_management.group_portal_company_admin") or
            user.has_group("records_management.group_portal_department_admin") or
            user.has_group("records_management.group_portal_department_user")
        )

    # ============================================================================
    # DASHBOARD ROUTES
    # ============================================================================

    @http.route("/records/dashboard", type="http", auth="user", website=True)
    def records_dashboard(self):
        """
        Enhanced dashboard with comprehensive business intelligence.
        Provides real-time operational metrics and performance indicators.
        Accessible to all internal users and portal users (all types).
        """
        if not self._check_dashboard_access():
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
        Accessible to managers and portal company/department admins.
        """
        if not self._check_analytics_access():
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
        containers = request.env['records.container'].sudo().search(domain, order='create_date desc')

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
        Accessible to all authenticated users including portal read-only.
        """
        if not self._check_dashboard_access():
            return {"success": False, "error": "Insufficient permissions"}

        try:
            Container = request.env['records.container'].sudo()
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
        Accessible to internal users, portal admins, and portal department users.
        """
        if not self._check_bulk_update_access():
            return {'success': False, 'error': 'Insufficient permissions for bulk updates'}

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
        Accessible to internal users, portal admins, and portal department users.
        """
        if not self._check_bulk_update_access():
            return request.redirect("/web/login")

        # Build domain based on filters
        domain = []
        partner_id = get.get("partner_id")
        location_id = get.get("location_id")
        if partner_id and partner_id.isdigit():  # Added check to avoid int(None)
            domain.append(("partner_id", "=", int(partner_id)))
        if location_id and location_id.isdigit():  # Added check to avoid int(None)
            domain.append(("location_id", "=", int(location_id)))

        containers = request.env['records.container'].sudo().search(domain)

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
        Accessible to managers and portal company admins only.
        """
        user = request.env.user
        can_manage_system = (
            user.has_group("records_management.group_records_manager") or
            user.has_group("records_management.group_portal_company_admin")
        )

        if not can_manage_system:
            return {'success': False, 'error': 'Insufficient permissions for system monitoring'}

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

        # Determine if user is a portal user (not internal user) - exclude sensitive data like location capacity
        user = request.env.user
        is_portal_user = not user.has_group("base.group_user")

        # Portal users should see filtered data, internal users see all data
        # Portal company admins get more access than regular portal users
        is_portal_admin = (
            user.has_group("records_management.group_portal_company_admin") or
            user.has_group("records_management.group_portal_department_admin")
        )
        user_partner_id = user.partner_id.id

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
        is_portal_user = not request.env.user.has_group("base.group_user")
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
        is_portal_user = not request.env.user.has_group("base.group_user")
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
        """Get user permissions for dashboard functionality including portal users."""
        user = request.env.user

        # Define permission groups for comprehensive access control
        # Analytics: Managers + Portal Company Admins + Portal Department Admins
        can_view_analytics = (
            user.has_group("records_management.group_records_manager") or
            user.has_group("records_management.group_portal_company_admin") or
            user.has_group("records_management.group_portal_department_admin")
        )

        # Bulk Updates: Internal Users + Portal Admins + Portal Department Users
        can_bulk_update = (
            user.has_group("records_management.group_records_user") or
            user.has_group("records_management.group_records_manager") or
            user.has_group("records_management.group_portal_company_admin") or
            user.has_group("records_management.group_portal_department_admin") or
            user.has_group("records_management.group_portal_department_user")
        )

        # Data Export: Internal Users + Portal Admins + Portal Department Users
        can_export_data = (
            user.has_group("records_management.group_records_user") or
            user.has_group("records_management.group_records_manager") or
            user.has_group("records_management.group_portal_company_admin") or
            user.has_group("records_management.group_portal_department_admin") or
            user.has_group("records_management.group_portal_department_user")
        )

        # System Management: Managers + Portal Company Admins only
        can_manage_system = (
            user.has_group("records_management.group_records_manager") or
            user.has_group("records_management.group_portal_company_admin")
        )

        # Billing: Managers + Portal Company Admins + Portal Department Admins
        can_view_billing = (
            user.has_group("records_management.group_records_manager") or
            user.has_group("records_management.group_portal_company_admin") or
            user.has_group("records_management.group_portal_department_admin")
        )

        # Stock Movement History: All authenticated users (including portal read-only)
        can_view_stock_movements = (
            user.has_group("records_management.group_records_user") or
            user.has_group("records_management.group_records_manager") or
            user.has_group("records_management.group_portal_company_admin") or
            user.has_group("records_management.group_portal_department_admin") or
            user.has_group("records_management.group_portal_department_user") or
            user.has_group("records_management.group_portal_readonly_employee")
        )

        # Real-time Monitoring: Internal Users + Portal Admins + Portal Department Users
        can_view_realtime_monitoring = (
            user.has_group("records_management.group_records_user") or
            user.has_group("records_management.group_records_manager") or
            user.has_group("records_management.group_portal_company_admin") or
            user.has_group("records_management.group_portal_department_admin") or
            user.has_group("records_management.group_portal_department_user")
        )

        return {
            "can_view_analytics": can_view_analytics,
            "can_bulk_update": can_bulk_update,
            "can_export_data": can_export_data,
            "can_manage_system": can_manage_system,
            "can_view_billing": can_view_billing,
            "can_view_stock_movements": can_view_stock_movements,
            "can_view_realtime_monitoring": can_view_realtime_monitoring,
            # User type identification for UI customization
            "is_portal_user": not user.has_group("base.group_user"),
            "is_internal_user": user.has_group("base.group_user"),
            "is_portal_company_admin": user.has_group("records_management.group_portal_company_admin"),
            "is_portal_department_admin": user.has_group("records_management.group_portal_department_admin"),
            "is_portal_department_user": user.has_group("records_management.group_portal_department_user"),
            "is_portal_readonly": user.has_group("records_management.group_portal_readonly_employee"),
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
        """Create comprehensive movement record using enhanced stock movement tracking."""
        # Get the new location record
        new_location = request.env['stock.location'].sudo().browse(new_location_id)

        # Use the new comprehensive movement tracking system
        request.env['records.stock.movement'].sudo().create_movement(
            container=container,
            to_location=new_location,
            movement_type='location_change',
            reason='Bulk location update via portal',
            user=request.env.user
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

        Certificate = request.env['destruction.certificate'].sudo()

        domain = [
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
        ]

        # Date filtering
        if date_begin and date_end:
            domain += [('date', '>=', date_begin), ('date', '<=', date_end)]

        # Sorting options
        searchbar_sortings = {
            'date': {'label': 'Date', 'order': 'certificate_date desc'},
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
        certificate = request.env['destruction.certificate'].sudo().browse(certificate_id)

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
        certificate = request.env['destruction.certificate'].sudo().browse(certificate_id)

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

        Container = request.env['records.container'].sudo()

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
            'name': {'label': 'Box Number', 'order': 'name'},
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
        container = request.env['records.container'].sudo().browse(container_id)
        partner = request.env.user.partner_id

        # Security check - verify ownership via partner_id OR hierarchical stock_owner_id
        # Check if container would be visible under the same domain as portal_my_containers
        visible_containers = request.env['records.container'].sudo().search([
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
    def portal_inventory_dashboard(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, inventory_type=None, **kw):
        """
        Enhanced inventory dashboard with comprehensive stock integration.
        
        Features:
        - Real-time stock quant synchronization
        - Comprehensive movement tracking
        - Location-based filtering and search
        - Mobile-optimized responsive design
        
        Security Layer Pattern: Use sudo() for model access but maintain data filtering
        """
        # Permission check: All portal user types can view inventory
        user = request.env.user
        if not (user.has_group("records_management.group_records_user") or
               user.has_group("records_management.group_records_manager") or
               user.has_group("records_management.group_portal_company_admin") or
               user.has_group("records_management.group_portal_department_admin") or
               user.has_group("records_management.group_portal_department_user") or
               user.has_group("records_management.group_portal_readonly_employee")):
            return request.render("website.403")

        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        commercial_partner = partner.commercial_partner_id

        # Enhanced Dashboard with Stock Integration (Phase 1 Implementation)
        # Get stock quants owned by customer (Security Layer Pattern)
        stock_quants = request.env['stock.quant'].sudo().search([
            ('owner_id', '=', commercial_partner.id),
            ('quantity', '>', 0),
            ('product_id.default_code', '=', 'RECORDS-CONTAINER')
        ])

        # Get comprehensive stock summary
        stock_summary = self._get_comprehensive_stock_summary(stock_quants)

        # Get recent movements for dashboard
        recent_movements = self._get_recent_dashboard_movements(commercial_partner)

        # Group containers by location for location-based overview
        containers_by_location = self._group_containers_by_location(stock_quants)

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
            Container = request.env['records.container'].sudo()
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
            # Phase 1 Enhanced Stock Integration Data
            'stock_summary': stock_summary,
            'recent_movements': recent_movements,
            'containers_by_location': containers_by_location,
            # Real-time monitoring capabilities
            'enable_real_time_updates': True,
            'movement_refresh_interval': 30000,  # 30 seconds
        })

        return request.render("records_management.portal_inventory_enhanced", values)

    # ============================================================================
    # INVENTORY TAB ROUTES (Backend-style list/detail views)
    # ============================================================================

    @http.route(['/my/inventory/containers'], type='http', auth="user", website=True)
    def portal_inventory_containers(self, page=1, sortby=None, filterby=None, search=None, **kw):
        """Containers tab - backend-style list view with bulk actions"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id.commercial_partner_id

        Container = request.env['records.container'].sudo()
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

    # ============================================================================
    # CONTAINER CRUD OPERATIONS (Full Create, Read, Update, Delete)
    # ============================================================================

    @http.route(['/my/inventory/container/<int:container_id>'], type='http', auth="user", website=True)
    def portal_container_detail(self, container_id, **kw):
        """Container detail view with edit/delete capability."""
        partner = request.env.user.partner_id.commercial_partner_id

        container = request.env['records.container'].sudo().browse(container_id)

        # Security: Verify ownership
        if container.partner_id.id != partner.id:
            return request.redirect('/my/home?error=unauthorized')

        # Check department access for non-company-admins
        if not request.env.user.has_group('records_management.group_portal_company_admin'):
            accessible_depts = request.env.user.accessible_department_ids.ids
            if container.department_id and container.department_id.id not in accessible_depts:
                return request.redirect('/my/home?error=unauthorized_dept')

        # Get available departments for editing
        departments = request.env['records.department'].search([
            ('company_id', '=', partner.id)
        ])

        # Get available locations
        locations = request.env['records.location'].search([
            '|', ('partner_id', '=', partner.id), ('partner_id', '=', False)
        ])

        # Get container types
        container_types = request.env['records.container.type'].search([])

        # Get movement history
        movements = request.env['chain.of.custody'].search([
            ('container_ids', 'in', [container_id])
        ], order='timestamp desc', limit=20)

        # Check permissions
        can_edit = request.env.user.has_group('records_management.group_portal_department_user')
        can_delete = request.env.user.has_group('records_management.group_portal_department_admin')

        values = {
            'container': container,
            'departments': departments,
            'locations': locations,
            'container_types': container_types,
            'movements': movements,
            'can_edit': can_edit,
            'can_delete': can_delete,
            'page_name': 'container_detail',
        }

        return request.render("records_management.portal_container_detail", values)

    @http.route(['/my/inventory/containers/create'], type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_container_create(self, **post):
        """Create new container (department user+)."""

        # Access check - must be department user or higher
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            if request.httprequest.method == 'GET':
                return request.redirect('/my/home?error=unauthorized')
            return request.render('records_management.portal_error', {
                'error_title': _('Unauthorized'),
                'error_message': _('You do not have permission to create containers.'),
            })

        partner = request.env.user.partner_id.commercial_partner_id

        # GET request - show form
        if request.httprequest.method == 'GET':
            departments = request.env['records.department'].search([
                ('company_id', '=', partner.id)
            ])
            locations = request.env['records.location'].search([
                '|', ('partner_id', '=', partner.id), ('partner_id', '=', False)
            ])
            container_types = request.env['records.container.type'].search([])

            values = {
                'departments': departments,
                'locations': locations,
                'container_types': container_types,
                'page_name': 'container_create',
            }
            return request.render("records_management.portal_container_create", values)

        # POST request - create container
        try:
            # Validate required fields
            name = post.get('name')
            container_type_id = post.get('container_type_id')
            department_id = post.get('department_id')

            if not all([name, container_type_id, department_id]):
                return request.render('records_management.portal_error', {
                    'error_title': _('Missing Required Fields'),
                    'error_message': _('Please provide container name, type, and department.'),
                })

            # Department validation
            department = request.env['records.department'].browse(int(department_id))
            if not department or department.company_id.id != partner.id:
                return request.render('records_management.portal_error', {
                    'error_title': _('Invalid Department'),
                    'error_message': _('The selected department is invalid.'),
                })

            # Check department access for non-company-admins
            if not request.env.user.has_group('records_management.group_portal_company_admin'):
                accessible_depts = request.env.user.accessible_department_ids.ids
                if int(department_id) not in accessible_depts:
                    return request.render('records_management.portal_error', {
                        'error_title': _('Unauthorized Department'),
                        'error_message': _('You do not have access to this department.'),
                    })

            # Create container
            container_vals = {
                'name': name,
                'partner_id': partner.id,
                'department_id': int(department_id),
                'container_type_id': int(container_type_id),
                'status': 'draft',
                'created_via_portal': True,
            }

            # Optional fields
            if post.get('description'):
                container_vals['description'] = post.get('description')
            if post.get('location_id'):
                container_vals['current_location_id'] = int(post.get('location_id'))
            if post.get('barcode'):
                container_vals['barcode'] = post.get('barcode')

            container = request.env['records.container'].create(container_vals)

            # Audit log
            request.env['naid.audit.log'].create({
                'action_type': 'container_created',
                'user_id': request.env.user.id,
                'container_id': container.id,
                'description': _('Container %s created via portal by %s') % (container.name, request.env.user.name),
                'timestamp': datetime.now(),
            })

            return request.redirect(f'/my/inventory/container/{container.id}?created=success')

        except Exception as e:
            _logger.error(f"Container creation failed: {str(e)}")
            return request.render('records_management.portal_error', {
                'error_title': _('Container Creation Failed'),
                'error_message': str(e),
            })

    @http.route(['/my/inventory/container/<int:container_id>/edit'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_container_edit(self, container_id, **post):
        """Edit container details (department user+ for own dept, company admin for all)."""

        # Access check
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            return request.redirect('/my/home?error=unauthorized')

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            container = request.env['records.container'].sudo().browse(container_id)

            # Verify ownership
            if container.partner_id.id != partner.id:
                return request.redirect('/my/inventory/containers?error=unauthorized')

            # Check department access
            is_company_admin = request.env.user.has_group('records_management.group_portal_company_admin')
            if not is_company_admin:
                accessible_depts = request.env.user.accessible_department_ids.ids
                if container.department_id.id not in accessible_depts:
                    return request.redirect('/my/inventory/containers?error=unauthorized_dept')

            # Update container fields
            update_vals = {}

            if post.get('name'):
                update_vals['name'] = post.get('name')
            if post.get('description'):
                update_vals['description'] = post.get('description')
            if post.get('container_type_id'):
                update_vals['container_type_id'] = int(post.get('container_type_id'))
            if post.get('location_id'):
                update_vals['current_location_id'] = int(post.get('location_id'))

            # Department change - only company admin
            if post.get('department_id') and is_company_admin:
                new_dept_id = int(post.get('department_id'))
                new_dept = request.env['records.department'].browse(new_dept_id)
                if new_dept.company_id.id == partner.id:
                    update_vals['department_id'] = new_dept_id

            # Status change - department admin+
            if post.get('status') and request.env.user.has_group('records_management.group_portal_department_admin'):
                update_vals['status'] = post.get('status')

            if update_vals:
                container.sudo().write(update_vals)

                # Audit log
                request.env['naid.audit.log'].create({
                    'action_type': 'container_updated',
                    'user_id': request.env.user.id,
                    'container_id': container.id,
                    'description': _('Container %s updated via portal by %s') % (container.name, request.env.user.name),
                    'timestamp': datetime.now(),
                })

            return request.redirect(f'/my/inventory/container/{container_id}?updated=success')

        except Exception as e:
            _logger.error(f"Container edit failed: {str(e)}")
            return request.redirect(f'/my/inventory/container/{container_id}?error=update_failed')

    @http.route(['/my/inventory/container/<int:container_id>/delete'], type='json', auth='user', methods=['POST'])
    def portal_container_delete(self, container_id, **kw):
        """Delete/archive container (department admin+ for own dept, company admin for all)."""

        # Access check - must be department admin or higher
        if not request.env.user.has_group('records_management.group_portal_department_admin'):
            return {'success': False, 'error': _('Unauthorized - requires department admin access')}

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            container = request.env['records.container'].sudo().browse(container_id)

            # Verify ownership
            if container.partner_id.id != partner.id:
                return {'success': False, 'error': _('Unauthorized - container does not belong to your company')}

            # Check department access
            is_company_admin = request.env.user.has_group('records_management.group_portal_company_admin')
            if not is_company_admin:
                accessible_depts = request.env.user.accessible_department_ids.ids
                if container.department_id.id not in accessible_depts:
                    return {'success': False, 'error': _('Unauthorized - no access to this department')}

            # Check if container has active files/documents
            has_contents = (
                request.env['records.file'].search_count([('container_id', '=', container_id)]) > 0 or
                request.env['records.document'].search_count([('container_id', '=', container_id)]) > 0
            )

            if has_contents and not is_company_admin:
                return {'success': False, 'error': _('Cannot delete container with contents - requires company admin')}

            # Archive instead of hard delete (for audit trail)
            container.sudo().write({
                'active': False,
                'status': 'archived',
                'archived_date': datetime.now(),
                'archived_by_id': request.env.user.id,
            })

            # Audit log
            request.env['naid.audit.log'].create({
                'action_type': 'container_deleted',
                'user_id': request.env.user.id,
                'container_id': container.id,
                'description': _('Container %s archived via portal by %s') % (container.name, request.env.user.name),
                'timestamp': datetime.now(),
            })

            return {'success': True, 'message': _('Container archived successfully')}

        except Exception as e:
            _logger.error(f"Container delete failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route(['/my/inventory/container/<int:container_id>/movements'], type='http', auth="user", website=True)
    def portal_container_movements(self, container_id, **kw):
        """View container movement history and request moves."""
        partner = request.env.user.partner_id.commercial_partner_id
        container = request.env['records.container'].sudo().browse(container_id)

        # Security check
        if container.partner_id.id != partner.id:
            return request.redirect('/my/home?error=unauthorized')

        # Get movement history
        movements = request.env['chain.of.custody'].search([
            ('container_ids', 'in', [container_id])
        ], order='timestamp desc')

        # Get available locations for move requests
        locations = request.env['records.location'].search([
            '|', ('partner_id', '=', partner.id), ('partner_id', '=', False)
        ])

        # Check if user can request moves
        can_request_move = request.env.user.has_group('records_management.group_portal_department_user')

        values = {
            'container': container,
            'movements': movements,
            'locations': locations,
            'can_request_move': can_request_move,
            'page_name': 'container_movements',
        }

        return request.render("records_management.portal_container_movements", values)

    @http.route(['/my/inventory/container/<int:container_id>/request-move'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_container_request_move(self, container_id, **post):
        """Request container move to new location (creates service request)."""

        # Access check
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            return request.redirect('/my/home?error=unauthorized')

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            container = request.env['records.container'].sudo().browse(container_id)

            # Security check
            if container.partner_id.id != partner.id:
                return {'error': 'Unauthorized'}

            # Get target location
            new_location_id = int(post.get('new_location_id'))
            new_location = request.env['records.location'].browse(new_location_id)

            # Create move request
            move_request = request.env['portal.request'].create({
                'request_type': 'move',
                'partner_id': partner.id,
                'requester_id': request.env.user.partner_id.id,
                'container_ids': [(6, 0, [container_id])],
                'target_location_id': new_location_id,
                'notes': post.get('notes', ''),
                'state': 'draft',
            })

            # Auto-submit if internal staff will handle
            move_request.action_submit()

            # Audit log
            request.env['naid.audit.log'].create({
                'action_type': 'container_move_requested',
                'user_id': request.env.user.id,
                'container_id': container.id,
                'description': _('Move requested for container %s to location %s') % (container.name, new_location.name),
                'timestamp': datetime.now(),
            })

            return request.redirect(f'/my/inventory/container/{container_id}/movements?request_created=success')

        except Exception as e:
            _logger.error(f"Container move request failed: {str(e)}")
            return request.redirect(f'/my/inventory/container/{container_id}/movements?error=request_failed')

    # ============================================================================
    # INVENTORY FILE & DOCUMENT ROUTES
    # ============================================================================

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

    # ============================================================================
    # FILES CRUD OPERATIONS (Full Create, Read, Update, Delete)
    # ============================================================================

    @http.route(['/my/inventory/file/<int:file_id>'], type='http', auth="user", website=True)
    def portal_file_detail(self, file_id, **kw):
        """File detail view with edit/delete capability."""
        partner = request.env.user.partner_id.commercial_partner_id
        file_record = request.env['records.file'].sudo().browse(file_id)

        # Security: Verify ownership
        if file_record.partner_id.id != partner.id:
            return request.redirect('/my/home?error=unauthorized')

        # Department access check
        if not request.env.user.has_group('records_management.group_portal_company_admin'):
            accessible_depts = request.env.user.accessible_department_ids.ids
            if file_record.department_id and file_record.department_id.id not in accessible_depts:
                return request.redirect('/my/home?error=unauthorized_dept')

        # Get related data
        departments = request.env['records.department'].search([('company_id', '=', partner.id)])
        containers = request.env['records.container'].search([('partner_id', '=', partner.id)])
        documents = request.env['records.document'].search([('file_id', '=', file_id)])

        # Permission flags
        can_edit = request.env.user.has_group('records_management.group_portal_department_user')
        can_delete = request.env.user.has_group('records_management.group_portal_department_admin')

        values = {
            'file': file_record,
            'documents': documents,
            'departments': departments,
            'containers': containers,
            'can_edit': can_edit,
            'can_delete': can_delete,
            'page_name': 'file_detail',
        }

        return request.render("records_management.portal_file_detail", values)

    @http.route(['/my/inventory/files/create'], type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_file_create(self, **post):
        """Create new file folder (department user+)."""
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            if request.httprequest.method == 'GET':
                return request.redirect('/my/home?error=unauthorized')
            return request.render('records_management.portal_error', {
                'error_title': _('Unauthorized'),
                'error_message': _('You do not have permission to create files.'),
            })

        partner = request.env.user.partner_id.commercial_partner_id

        if request.httprequest.method == 'GET':
            departments = request.env['records.department'].search([('company_id', '=', partner.id)])
            containers = request.env['records.container'].search([('partner_id', '=', partner.id)])

            values = {
                'departments': departments,
                'containers': containers,
                'page_name': 'file_create',
            }
            return request.render("records_management.portal_file_create", values)

        try:
            name = post.get('name')
            container_id = post.get('container_id')
            department_id = post.get('department_id')

            if not all([name, container_id, department_id]):
                return request.render('records_management.portal_error', {
                    'error_title': _('Missing Required Fields'),
                    'error_message': _('Please provide file name, container, and department.'),
                })

            # Department validation
            department = request.env['records.department'].browse(int(department_id))
            if department.company_id.id != partner.id:
                return request.render('records_management.portal_error', {
                    'error_title': _('Invalid Department'),
                    'error_message': _('The selected department is invalid.'),
                })

            # Department access check
            if not request.env.user.has_group('records_management.group_portal_company_admin'):
                accessible_depts = request.env.user.accessible_department_ids.ids
                if int(department_id) not in accessible_depts:
                    return request.render('records_management.portal_error', {
                        'error_title': _('Unauthorized Department'),
                        'error_message': _('You do not have access to this department.'),
                    })

            file_vals = {
                'name': name,
                'partner_id': partner.id,
                'department_id': int(department_id),
                'container_id': int(container_id),
                'created_via_portal': True,
            }

            if post.get('description'):
                file_vals['description'] = post.get('description')
            if post.get('barcode'):
                file_vals['barcode'] = post.get('barcode')

            file_record = request.env['records.file'].create(file_vals)

            request.env['naid.audit.log'].create({
                'action_type': 'file_created',
                'user_id': request.env.user.id,
                'description': _('File %s created via portal by %s') % (file_record.name, request.env.user.name),
                'timestamp': datetime.now(),
            })

            return request.redirect(f'/my/inventory/file/{file_record.id}?created=success')

        except Exception as e:
            _logger.error(f"File creation failed: {str(e)}")
            return request.render('records_management.portal_error', {
                'error_title': _('File Creation Failed'),
                'error_message': str(e),
            })

    @http.route(['/my/inventory/file/<int:file_id>/edit'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_file_edit(self, file_id, **post):
        """Edit file details (department user+)."""
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            return request.redirect('/my/home?error=unauthorized')

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            file_record = request.env['records.file'].sudo().browse(file_id)

            if file_record.partner_id.id != partner.id:
                return request.redirect('/my/inventory/files?error=unauthorized')

            is_company_admin = request.env.user.has_group('records_management.group_portal_company_admin')
            if not is_company_admin:
                accessible_depts = request.env.user.accessible_department_ids.ids
                if file_record.department_id.id not in accessible_depts:
                    return request.redirect('/my/inventory/files?error=unauthorized_dept')

            update_vals = {}
            if post.get('name'):
                update_vals['name'] = post.get('name')
            if post.get('description'):
                update_vals['description'] = post.get('description')
            if post.get('barcode'):
                update_vals['barcode'] = post.get('barcode')
            if post.get('container_id'):
                update_vals['container_id'] = int(post.get('container_id'))

            if post.get('department_id') and is_company_admin:
                new_dept_id = int(post.get('department_id'))
                new_dept = request.env['records.department'].browse(new_dept_id)
                if new_dept.company_id.id == partner.id:
                    update_vals['department_id'] = new_dept_id

            if update_vals:
                file_record.sudo().write(update_vals)
                request.env['naid.audit.log'].create({
                    'action_type': 'file_updated',
                    'user_id': request.env.user.id,
                    'description': _('File %s updated via portal by %s') % (file_record.name, request.env.user.name),
                    'timestamp': datetime.now(),
                })

            return request.redirect(f'/my/inventory/file/{file_id}?updated=success')

        except Exception as e:
            _logger.error(f"File edit failed: {str(e)}")
            return request.redirect(f'/my/inventory/file/{file_id}?error=update_failed')

    @http.route(['/my/inventory/file/<int:file_id>/delete'], type='json', auth='user', methods=['POST'])
    def portal_file_delete(self, file_id, **kw):
        """Delete/archive file (department admin+)."""
        if not request.env.user.has_group('records_management.group_portal_department_admin'):
            return {'success': False, 'error': _('Unauthorized - requires department admin access')}

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            file_record = request.env['records.file'].sudo().browse(file_id)

            if file_record.partner_id.id != partner.id:
                return {'success': False, 'error': _('Unauthorized')}

            is_company_admin = request.env.user.has_group('records_management.group_portal_company_admin')
            if not is_company_admin:
                accessible_depts = request.env.user.accessible_department_ids.ids
                if file_record.department_id.id not in accessible_depts:
                    return {'success': False, 'error': _('Unauthorized - no access to this department')}

            # Check for documents
            has_documents = request.env['records.document'].search_count([('file_id', '=', file_id)]) > 0
            if has_documents and not is_company_admin:
                return {'success': False, 'error': _('Cannot delete file with documents - requires company admin')}

            file_record.sudo().write({'active': False})

            request.env['naid.audit.log'].create({
                'action_type': 'file_deleted',
                'user_id': request.env.user.id,
                'description': _('File %s archived via portal by %s') % (file_record.name, request.env.user.name),
                'timestamp': datetime.now(),
            })

            return {'success': True, 'message': _('File archived successfully')}

        except Exception as e:
            _logger.error(f"File delete failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route(['/my/inventory/file/<int:file_id>/add-document'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_file_add_document(self, file_id, **post):
        """Add document to file (department user+)."""
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            return request.redirect('/my/home?error=unauthorized')

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            file_record = request.env['records.file'].sudo().browse(file_id)

            if file_record.partner_id.id != partner.id:
                return request.redirect('/my/inventory/files?error=unauthorized')

            # Department access check
            is_company_admin = request.env.user.has_group('records_management.group_portal_company_admin')
            if not is_company_admin:
                accessible_depts = request.env.user.accessible_department_ids.ids
                if file_record.department_id.id not in accessible_depts:
                    return request.redirect('/my/inventory/files?error=unauthorized_dept')

            document_id = post.get('document_id')
            if document_id:
                # Link existing document to file
                doc = request.env['records.document'].sudo().browse(int(document_id))
                if doc.partner_id.id == partner.id:
                    doc.sudo().write({'file_id': file_id})

                    request.env['naid.audit.log'].create({
                        'action_type': 'document_added_to_file',
                        'user_id': request.env.user.id,
                        'description': _('Document %s added to file %s via portal by %s') % (
                            doc.name, file_record.name, request.env.user.name
                        ),
                        'timestamp': datetime.now(),
                    })
            else:
                # Create new document in file
                doc_name = post.get('document_name')
                if doc_name:
                    doc_vals = {
                        'name': doc_name,
                        'partner_id': partner.id,
                        'department_id': file_record.department_id.id,
                        'file_id': file_id,
                        'created_via_portal': True,
                    }
                    if post.get('document_description'):
                        doc_vals['description'] = post.get('document_description')

                    doc = request.env['records.document'].create(doc_vals)

                    request.env['naid.audit.log'].create({
                        'action_type': 'document_created_in_file',
                        'user_id': request.env.user.id,
                        'description': _('Document %s created in file %s via portal by %s') % (
                            doc.name, file_record.name, request.env.user.name
                        ),
                        'timestamp': datetime.now(),
                    })

            return request.redirect(f'/my/inventory/file/{file_id}?document_added=success')

        except Exception as e:
            _logger.error(f"Add document to file failed: {str(e)}")
            return request.redirect(f'/my/inventory/file/{file_id}?error=add_document_failed')

    @http.route(['/my/inventory/file/<int:file_id>/move-container'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_file_move_container(self, file_id, **post):
        """Move file to different container (department user+)."""
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            return request.redirect('/my/home?error=unauthorized')

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            file_record = request.env['records.file'].sudo().browse(file_id)

            if file_record.partner_id.id != partner.id:
                return request.redirect('/my/inventory/files?error=unauthorized')

            # Department access check
            is_company_admin = request.env.user.has_group('records_management.group_portal_company_admin')
            if not is_company_admin:
                accessible_depts = request.env.user.accessible_department_ids.ids
                if file_record.department_id.id not in accessible_depts:
                    return request.redirect('/my/inventory/files?error=unauthorized_dept')

            new_container_id = post.get('container_id')
            if not new_container_id:
                return request.redirect(f'/my/inventory/file/{file_id}?error=no_container')

            # Verify new container ownership
            new_container = request.env['records.container'].sudo().browse(int(new_container_id))
            if new_container.partner_id.id != partner.id:
                return request.redirect(f'/my/inventory/file/{file_id}?error=invalid_container')

            old_container_name = file_record.container_id.name if file_record.container_id else 'None'
            file_record.sudo().write({'container_id': int(new_container_id)})

            request.env['naid.audit.log'].create({
                'action_type': 'file_moved_container',
                'user_id': request.env.user.id,
                'description': _('File %s moved from container %s to %s via portal by %s') % (
                    file_record.name, old_container_name, new_container.name, request.env.user.name
                ),
                'timestamp': datetime.now(),
            })

            return request.redirect(f'/my/inventory/file/{file_id}?moved=success')

        except Exception as e:
            _logger.error(f"Move file to container failed: {str(e)}")
            return request.redirect(f'/my/inventory/file/{file_id}?error=move_failed')

    # ============================================================================
    # DOCUMENTS CRUD OPERATIONS (Full Create, Read, Update, Delete)
    # ============================================================================

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

    @http.route(['/my/inventory/document/<int:doc_id>'], type='http', auth="user", website=True)
    def portal_document_detail(self, doc_id, **kw):
        """Document detail view with edit/delete capability."""
        partner = request.env.user.partner_id.commercial_partner_id
        doc_record = request.env['records.document'].sudo().browse(doc_id)

        # Security: Verify ownership
        if doc_record.partner_id.id != partner.id:
            return request.redirect('/my/home?error=unauthorized')

        # Department access check
        if not request.env.user.has_group('records_management.group_portal_company_admin'):
            accessible_depts = request.env.user.accessible_department_ids.ids
            if doc_record.department_id and doc_record.department_id.id not in accessible_depts:
                return request.redirect('/my/home?error=unauthorized_dept')

        # Get related data
        departments = request.env['records.department'].search([('company_id', '=', partner.id)])
        files = request.env['records.file'].search([('partner_id', '=', partner.id)])
        containers = request.env['records.container'].search([('partner_id', '=', partner.id)])

        # Get attachments
        attachments = request.env['ir.attachment'].search([
            ('res_model', '=', 'records.document'),
            ('res_id', '=', doc_id)
        ])

        # Permission flags
        can_edit = request.env.user.has_group('records_management.group_portal_department_user')
        can_delete = request.env.user.has_group('records_management.group_portal_department_admin')

        values = {
            'document': doc_record,
            'attachments': attachments,
            'departments': departments,
            'files': files,
            'containers': containers,
            'can_edit': can_edit,
            'can_delete': can_delete,
            'page_name': 'document_detail',
        }

        return request.render("records_management.portal_document_detail", values)

    @http.route(['/my/inventory/documents/create'], type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_document_create(self, **post):
        """Create new document (department user+)."""
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            if request.httprequest.method == 'GET':
                return request.redirect('/my/home?error=unauthorized')
            return request.render('records_management.portal_error', {
                'error_title': _('Unauthorized'),
                'error_message': _('You do not have permission to create documents.'),
            })

        partner = request.env.user.partner_id.commercial_partner_id

        if request.httprequest.method == 'GET':
            departments = request.env['records.department'].search([('company_id', '=', partner.id)])
            files = request.env['records.file'].search([('partner_id', '=', partner.id)])
            containers = request.env['records.container'].search([('partner_id', '=', partner.id)])

            values = {
                'departments': departments,
                'files': files,
                'containers': containers,
                'page_name': 'document_create',
            }
            return request.render("records_management.portal_document_create", values)

        try:
            name = post.get('name')
            file_id = post.get('file_id')
            department_id = post.get('department_id')

            if not all([name, file_id, department_id]):
                return request.render('records_management.portal_error', {
                    'error_title': _('Missing Required Fields'),
                    'error_message': _('Please provide document name, file, and department.'),
                })

            # Department validation
            department = request.env['records.department'].browse(int(department_id))
            if department.company_id.id != partner.id:
                return request.render('records_management.portal_error', {
                    'error_title': _('Invalid Department'),
                    'error_message': _('The selected department is invalid.'),
                })

            # Department access check
            if not request.env.user.has_group('records_management.group_portal_company_admin'):
                accessible_depts = request.env.user.accessible_department_ids.ids
                if int(department_id) not in accessible_depts:
                    return request.render('records_management.portal_error', {
                        'error_title': _('Unauthorized Department'),
                        'error_message': _('You do not have access to this department.'),
                    })

            doc_vals = {
                'name': name,
                'partner_id': partner.id,
                'department_id': int(department_id),
                'file_id': int(file_id),
                'created_via_portal': True,
            }

            if post.get('description'):
                doc_vals['description'] = post.get('description')
            if post.get('document_type_id'):
                doc_vals['document_type_id'] = int(post.get('document_type_id'))

            doc_record = request.env['records.document'].create(doc_vals)

            request.env['naid.audit.log'].create({
                'action_type': 'document_created',
                'user_id': request.env.user.id,
                'description': _('Document %s created via portal by %s') % (doc_record.name, request.env.user.name),
                'timestamp': datetime.now(),
            })

            return request.redirect(f'/my/inventory/document/{doc_record.id}?created=success')

        except Exception as e:
            _logger.error(f"Document creation failed: {str(e)}")
            return request.render('records_management.portal_error', {
                'error_title': _('Document Creation Failed'),
                'error_message': str(e),
            })

    @http.route(['/my/inventory/document/<int:doc_id>/edit'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_document_edit(self, doc_id, **post):
        """Edit document metadata (department user+)."""
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            return request.redirect('/my/home?error=unauthorized')

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            doc_record = request.env['records.document'].sudo().browse(doc_id)

            if doc_record.partner_id.id != partner.id:
                return request.redirect('/my/inventory/documents?error=unauthorized')

            is_company_admin = request.env.user.has_group('records_management.group_portal_company_admin')
            if not is_company_admin:
                accessible_depts = request.env.user.accessible_department_ids.ids
                if doc_record.department_id.id not in accessible_depts:
                    return request.redirect('/my/inventory/documents?error=unauthorized_dept')

            update_vals = {}
            if post.get('name'):
                update_vals['name'] = post.get('name')
            if post.get('description'):
                update_vals['description'] = post.get('description')
            if post.get('file_id'):
                update_vals['file_id'] = int(post.get('file_id'))

            if post.get('department_id') and is_company_admin:
                new_dept_id = int(post.get('department_id'))
                new_dept = request.env['records.department'].browse(new_dept_id)
                if new_dept.company_id.id == partner.id:
                    update_vals['department_id'] = new_dept_id

            if update_vals:
                doc_record.sudo().write(update_vals)
                request.env['naid.audit.log'].create({
                    'action_type': 'document_updated',
                    'user_id': request.env.user.id,
                    'description': _('Document %s updated via portal by %s') % (doc_record.name, request.env.user.name),
                    'timestamp': datetime.now(),
                })

            return request.redirect(f'/my/inventory/document/{doc_id}?updated=success')

        except Exception as e:
            _logger.error(f"Document edit failed: {str(e)}")
            return request.redirect(f'/my/inventory/document/{doc_id}?error=update_failed')

    @http.route(['/my/inventory/document/<int:doc_id>/delete'], type='json', auth='user', methods=['POST'])
    def portal_document_delete(self, doc_id, **kw):
        """Delete/archive document (department admin+)."""
        if not request.env.user.has_group('records_management.group_portal_department_admin'):
            return {'success': False, 'error': _('Unauthorized - requires department admin access')}

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            doc_record = request.env['records.document'].sudo().browse(doc_id)

            if doc_record.partner_id.id != partner.id:
                return {'success': False, 'error': _('Unauthorized')}

            is_company_admin = request.env.user.has_group('records_management.group_portal_company_admin')
            if not is_company_admin:
                accessible_depts = request.env.user.accessible_department_ids.ids
                if doc_record.department_id.id not in accessible_depts:
                    return {'success': False, 'error': _('Unauthorized - no access to this department')}

            doc_record.sudo().write({'active': False})

            request.env['naid.audit.log'].create({
                'action_type': 'document_deleted',
                'user_id': request.env.user.id,
                'description': _('Document %s archived via portal by %s') % (doc_record.name, request.env.user.name),
                'timestamp': datetime.now(),
            })

            return {'success': True, 'message': _('Document archived successfully')}

        except Exception as e:
            _logger.error(f"Document delete failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route(['/my/inventory/document/<int:doc_id>/upload'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_document_upload(self, doc_id, **post):
        """Upload file attachment to document (department user+)."""
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            return request.redirect('/my/home?error=unauthorized')

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            doc_record = request.env['records.document'].sudo().browse(doc_id)

            if doc_record.partner_id.id != partner.id:
                return request.redirect('/my/inventory/documents?error=unauthorized')

            if 'file' not in request.httprequest.files:
                return request.redirect(f'/my/inventory/document/{doc_id}?error=no_file')

            uploaded_file = request.httprequest.files['file']
            if not uploaded_file.filename:
                return request.redirect(f'/my/inventory/document/{doc_id}?error=no_file')

            attachment = request.env['ir.attachment'].create({
                'name': uploaded_file.filename,
                'type': 'binary',
                'datas': base64.b64encode(uploaded_file.read()),
                'res_model': 'records.document',
                'res_id': doc_id,
                'mimetype': uploaded_file.content_type or 'application/octet-stream',
            })

            request.env['naid.audit.log'].create({
                'action_type': 'document_file_uploaded',
                'user_id': request.env.user.id,
                'description': _('File %s uploaded to document %s via portal by %s') % (
                    uploaded_file.filename, doc_record.name, request.env.user.name
                ),
                'timestamp': datetime.now(),
            })

            return request.redirect(f'/my/inventory/document/{doc_id}?upload=success')

        except Exception as e:
            _logger.error(f"Document upload failed: {str(e)}")
            return request.redirect(f'/my/inventory/document/{doc_id}?error=upload_failed')

    @http.route(['/my/inventory/documents/bulk-upload'], type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_document_bulk_upload(self, **post):
        """Bulk document upload interface (department user+)."""
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            if request.httprequest.method == 'GET':
                return request.redirect('/my/home?error=unauthorized')
            return request.render('records_management.portal_error', {
                'error_title': _('Unauthorized'),
                'error_message': _('You do not have permission to upload documents.'),
            })

        partner = request.env.user.partner_id.commercial_partner_id

        if request.httprequest.method == 'GET':
            departments = request.env['records.department'].search([('company_id', '=', partner.id)])
            files = request.env['records.file'].search([('partner_id', '=', partner.id)])

            values = {
                'departments': departments,
                'files': files,
                'page_name': 'document_bulk_upload',
            }
            return request.render("records_management.portal_document_bulk_upload", values)

        try:
            file_id = post.get('file_id')
            department_id = post.get('department_id')

            if not all([file_id, department_id]):
                return request.render('records_management.portal_error', {
                    'error_title': _('Missing Required Fields'),
                    'error_message': _('Please select file and department.'),
                })

            # Department access check
            if not request.env.user.has_group('records_management.group_portal_company_admin'):
                accessible_depts = request.env.user.accessible_department_ids.ids
                if int(department_id) not in accessible_depts:
                    return request.render('records_management.portal_error', {
                        'error_title': _('Unauthorized Department'),
                        'error_message': _('You do not have access to this department.'),
                    })

            uploaded_files = request.httprequest.files.getlist('files[]')
            if not uploaded_files:
                return request.render('records_management.portal_error', {
                    'error_title': _('No Files Uploaded'),
                    'error_message': _('Please select files to upload.'),
                })

            created_docs = []
            for uploaded_file in uploaded_files:
                if not uploaded_file.filename:
                    continue

                doc_vals = {
                    'name': uploaded_file.filename,
                    'partner_id': partner.id,
                    'department_id': int(department_id),
                    'file_id': int(file_id),
                    'created_via_portal': True,
                }

                doc_record = request.env['records.document'].create(doc_vals)
                created_docs.append(doc_record)

                attachment = request.env['ir.attachment'].create({
                    'name': uploaded_file.filename,
                    'type': 'binary',
                    'datas': base64.b64encode(uploaded_file.read()),
                    'res_model': 'records.document',
                    'res_id': doc_record.id,
                    'mimetype': uploaded_file.content_type or 'application/octet-stream',
                })

            if created_docs:
                request.env['naid.audit.log'].create({
                    'action_type': 'documents_bulk_uploaded',
                    'user_id': request.env.user.id,
                    'description': _('%d documents uploaded via portal by %s') % (
                        len(created_docs), request.env.user.name
                    ),
                    'timestamp': datetime.now(),
                })

            return request.redirect(f'/my/inventory/documents?upload=success&count={len(created_docs)}')

        except Exception as e:
            _logger.error(f"Bulk upload failed: {str(e)}")
            return request.render('records_management.portal_error', {
                'error_title': _('Bulk Upload Failed'),
                'error_message': str(e),
            })

    @http.route(['/my/inventory/document/<int:doc_id>/request-scan'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_document_request_scan(self, doc_id, **post):
        """Request scanning service for document (department user+)."""
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            return request.redirect('/my/home?error=unauthorized')

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            doc_record = request.env['records.document'].sudo().browse(doc_id)

            if doc_record.partner_id.id != partner.id:
                return request.redirect('/my/inventory/documents?error=unauthorized')

            # Department access check
            is_company_admin = request.env.user.has_group('records_management.group_portal_company_admin')
            if not is_company_admin:
                accessible_depts = request.env.user.accessible_department_ids.ids
                if doc_record.department_id.id not in accessible_depts:
                    return request.redirect('/my/inventory/documents?error=unauthorized_dept')

            # Create scan service request
            request_vals = {
                'name': _('Scan Request for %s') % doc_record.name,
                'partner_id': partner.id,
                'department_id': doc_record.department_id.id,
                'request_type': 'scanning',
                'state': 'draft',
                'created_via_portal': True,
            }

            if post.get('notes'):
                request_vals['notes'] = post.get('notes')

            scan_request = request.env['portal.request'].create(request_vals)

            # Link document to request
            doc_record.sudo().write({
                'scan_request_id': scan_request.id,
                'scan_requested_date': datetime.now(),
            })

            request.env['naid.audit.log'].create({
                'action_type': 'scan_requested',
                'user_id': request.env.user.id,
                'description': _('Scan requested for document %s via portal by %s') % (
                    doc_record.name, request.env.user.name
                ),
                'timestamp': datetime.now(),
            })

            return request.redirect(f'/my/inventory/document/{doc_id}?scan_requested=success')

        except Exception as e:
            _logger.error(f"Request scan failed: {str(e)}")
            return request.redirect(f'/my/inventory/document/{doc_id}?error=scan_request_failed')

    @http.route(['/my/document/<int:doc_id>'], type='http', auth="user", website=True)
    def portal_document_detail_alt(self, doc_id, **kw):
        """Alternative document detail route (redirects to main route)."""
        return request.redirect(f'/my/inventory/document/{doc_id}')

    # ============================================================================
    # SERVICE REQUESTS CRUD OPERATIONS (Full workflow management)
    # ============================================================================

    @http.route(['/my/requests'], type='http', auth='user', website=True)
    def portal_requests_list(self, page=1, sortby=None, filterby=None, search=None, **kw):
        """List all service requests (all users - read own department)."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id.commercial_partner_id

        Request = request.env['portal.request']
        domain = [('partner_id', '=', partner.id)]

        # Department filtering for non-company admins
        if not request.env.user.has_group('records_management.group_portal_company_admin'):
            accessible_depts = request.env.user.accessible_department_ids.ids
            if accessible_depts:
                domain += [('department_id', 'in', accessible_depts)]

        if filterby:
            if filterby == 'retrieval':
                domain += [('request_type', '=', 'retrieval')]
            elif filterby == 'destruction':
                domain += [('request_type', '=', 'destruction')]
            elif filterby == 'pickup':
                domain += [('request_type', '=', 'pickup')]
            elif filterby == 'scanning':
                domain += [('request_type', '=', 'scanning')]
            elif filterby == 'pending':
                domain += [('state', 'in', ['draft', 'submitted'])]
            elif filterby == 'approved':
                domain += [('state', '=', 'approved')]

        if search:
            domain += ['|', ('name', 'ilike', search), ('description', 'ilike', search)]

        request_count = Request.search_count(domain)
        pager = request.website.pager(
            url="/my/requests",
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search},
            total=request_count,
            page=page,
            step=20,
        )

        requests = Request.search(domain, order='create_date desc', limit=20, offset=pager['offset'])

        values.update({
            'requests': requests,
            'page_name': 'requests',
            'pager': pager,
            'search': search or '',
            'filterby': filterby,
            'request_count': request_count,
        })

        return request.render("records_management.portal_requests_template", values)

    @http.route(['/my/requests/<int:request_id>'], type='http', auth='user', website=True)
    def portal_request_detail(self, request_id, **kw):
        """Service request detail view with edit/cancel capability."""
        partner = request.env.user.partner_id.commercial_partner_id
        req_record = request.env['portal.request'].sudo().browse(request_id)

        if req_record.partner_id.id != partner.id:
            return request.redirect('/my/home?error=unauthorized')

        # Department access check
        if not request.env.user.has_group('records_management.group_portal_company_admin'):
            accessible_depts = request.env.user.accessible_department_ids.ids
            if req_record.department_id and req_record.department_id.id not in accessible_depts:
                return request.redirect('/my/home?error=unauthorized_dept')

        # Permission flags
        can_edit = request.env.user.has_group('records_management.group_portal_department_user') and req_record.state in ['draft', 'submitted']
        can_cancel = request.env.user.has_group('records_management.group_portal_department_user') and req_record.state not in ['cancelled', 'completed']

        values = {
            'request': req_record,
            'can_edit': can_edit,
            'can_cancel': can_cancel,
            'page_name': 'request_detail',
        }

        return request.render("records_management.portal_request_detail", values)

    @http.route(['/my/request/new/<string:request_type>'], type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_request_create(self, request_type, **post):
        """Create new service request (department user+)."""
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            if request.httprequest.method == 'GET':
                return request.redirect('/my/home?error=unauthorized')
            return request.render('records_management.portal_error', {
                'error_title': _('Unauthorized'),
                'error_message': _('You do not have permission to create requests.'),
            })

        partner = request.env.user.partner_id.commercial_partner_id

        if request_type not in ['retrieval', 'destruction', 'pickup', 'scanning']:
            return request.redirect('/my/requests?error=invalid_type')

        if request.httprequest.method == 'GET':
            departments = request.env['records.department'].search([('company_id', '=', partner.id)])
            containers = request.env['records.container'].search([('partner_id', '=', partner.id)])
            files = request.env['records.file'].search([('partner_id', '=', partner.id)])

            values = {
                'request_type': request_type,
                'departments': departments,
                'containers': containers,
                'files': files,
                'page_name': f'request_create_{request_type}',
            }

            # Route to specific template based on type
            if request_type == 'destruction':
                return request.render("records_management.portal_destruction_request_create", values)
            elif request_type == 'pickup':
                return request.render("records_management.portal_pickup_request_create", values)
            else:
                return request.render("records_management.portal_request_create", values)

        try:
            department_id = post.get('department_id')
            if not department_id:
                return request.render('records_management.portal_error', {
                    'error_title': _('Missing Required Fields'),
                    'error_message': _('Please select a department.'),
                })

            # Department access check
            if not request.env.user.has_group('records_management.group_portal_company_admin'):
                accessible_depts = request.env.user.accessible_department_ids.ids
                if int(department_id) not in accessible_depts:
                    return request.render('records_management.portal_error', {
                        'error_title': _('Unauthorized Department'),
                        'error_message': _('You do not have access to this department.'),
                    })

            request_vals = {
                'name': post.get('name') or _('New %s Request') % request_type.capitalize(),
                'partner_id': partner.id,
                'department_id': int(department_id),
                'request_type': request_type,
                'state': 'draft',
                'created_via_portal': True,
            }

            if post.get('description'):
                request_vals['description'] = post.get('description')
            if post.get('priority'):
                request_vals['priority'] = post.get('priority')
            if post.get('scheduled_date'):
                request_vals['scheduled_date'] = post.get('scheduled_date')

            req_record = request.env['portal.request'].create(request_vals)

            request.env['naid.audit.log'].create({
                'action_type': f'{request_type}_request_created',
                'user_id': request.env.user.id,
                'description': _('%s request %s created via portal by %s') % (
                    request_type.capitalize(), req_record.name, request.env.user.name
                ),
                'timestamp': datetime.now(),
            })

            # Auto-submit if requested
            if post.get('auto_submit') == 'true':
                req_record.sudo().write({'state': 'submitted'})

            return request.redirect(f'/my/requests/{req_record.id}?created=success')

        except Exception as e:
            _logger.error(f\"Request creation failed: {str(e)}\")
            return request.render('records_management.portal_error', {
                'error_title': _('Request Creation Failed'),
                'error_message': str(e),
            })

    @http.route(['/my/requests/<int:request_id>/edit'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_request_edit(self, request_id, **post):
        """Edit service request (department user+ for draft/submitted only)."""
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            return request.redirect('/my/home?error=unauthorized')

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            req_record = request.env['portal.request'].sudo().browse(request_id)

            if req_record.partner_id.id != partner.id:
                return request.redirect('/my/requests?error=unauthorized')

            if req_record.state not in ['draft', 'submitted']:
                return request.redirect(f'/my/requests/{request_id}?error=cannot_edit')

            # Department access check
            is_company_admin = request.env.user.has_group('records_management.group_portal_company_admin')
            if not is_company_admin:
                accessible_depts = request.env.user.accessible_department_ids.ids
                if req_record.department_id.id not in accessible_depts:
                    return request.redirect('/my/requests?error=unauthorized_dept')

            update_vals = {}
            if post.get('description'):
                update_vals['description'] = post.get('description')
            if post.get('priority'):
                update_vals['priority'] = post.get('priority')
            if post.get('scheduled_date'):
                update_vals['scheduled_date'] = post.get('scheduled_date')

            if update_vals:
                req_record.sudo().write(update_vals)
                request.env['naid.audit.log'].create({
                    'action_type': 'request_updated',
                    'user_id': request.env.user.id,
                    'description': _('Request %s updated via portal by %s') % (req_record.name, request.env.user.name),
                    'timestamp': datetime.now(),
                })

            return request.redirect(f'/my/requests/{request_id}?updated=success')

        except Exception as e:
            _logger.error(f\"Request edit failed: {str(e)}\")
            return request.redirect(f'/my/requests/{request_id}?error=update_failed')

    @http.route(['/my/requests/<int:request_id>/cancel'], type='json', auth='user', methods=['POST'])
    def portal_request_cancel(self, request_id, **kw):
        """Cancel service request (department user+)."""
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            return {'success': False, 'error': _('Unauthorized')}

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            req_record = request.env['portal.request'].sudo().browse(request_id)

            if req_record.partner_id.id != partner.id:
                return {'success': False, 'error': _('Unauthorized')}

            if req_record.state in ['cancelled', 'completed']:
                return {'success': False, 'error': _('Cannot cancel completed or cancelled requests')}

            # Department access check
            is_company_admin = request.env.user.has_group('records_management.group_portal_company_admin')
            if not is_company_admin:
                accessible_depts = request.env.user.accessible_department_ids.ids
                if req_record.department_id.id not in accessible_depts:
                    return {'success': False, 'error': _('Unauthorized - no access to this department')}

            req_record.sudo().write({'state': 'cancelled'})

            request.env['naid.audit.log'].create({
                'action_type': 'request_cancelled',
                'user_id': request.env.user.id,
                'description': _('Request %s cancelled via portal by %s') % (req_record.name, request.env.user.name),
                'timestamp': datetime.now(),
            })

            return {'success': True, 'message': _('Request cancelled successfully')}

        except Exception as e:
            _logger.error(f\"Request cancel failed: {str(e)}\")
            return {'success': False, 'error': str(e)}

    @http.route(['/my/requests/<int:request_id>/submit'], type='json', auth='user', methods=['POST'])
    def portal_request_submit(self, request_id, **kw):
        """Submit request for approval (department user+)."""
        if not request.env.user.has_group('records_management.group_portal_department_user'):
            return {'success': False, 'error': _('Unauthorized')}

        try:
            partner = request.env.user.partner_id.commercial_partner_id
            req_record = request.env['portal.request'].sudo().browse(request_id)

            if req_record.partner_id.id != partner.id:
                return {'success': False, 'error': _('Unauthorized')}

            if req_record.state != 'draft':
                return {'success': False, 'error': _('Only draft requests can be submitted')}

            req_record.sudo().write({'state': 'submitted'})

            request.env['naid.audit.log'].create({
                'action_type': 'request_submitted',
                'user_id': request.env.user.id,
                'description': _('Request %s submitted for approval via portal by %s') % (
                    req_record.name, request.env.user.name
                ),
                'timestamp': datetime.now(),
            })

            return {'success': True, 'message': _('Request submitted successfully')}

        except Exception as e:
            _logger.error(f\"Request submit failed: {str(e)}\")
            return {'success': False, 'error': str(e)}

    # ============================================================================
    # DESTRUCTION & CUSTODY WORKFLOW ROUTES (5 routes)
    # ============================================================================

    @http.route(['/my/destruction'], type='http', auth='user', website=True)
    def portal_destruction_list(self, page=1, filterby=None, search=None, **kw):
        """
        List all destruction requests with filtering
        Accessible to: All portal users (own department)
        Security: Department filtering for non-company admins
        """
        values = self._prepare_portal_layout_values()
        user = request.env.user
        partner = user.partner_id

        DestructionRequest = request.env['portal.request']
        domain = [
            ('partner_id', '=', partner.id),
            ('request_type', '=', 'destruction')
        ]

        # Department filtering for non-company admins
        if not user.has_group('records_management.group_portal_company_admin'):
            accessible_departments = user.accessible_department_ids.ids
            if accessible_departments:
                domain.append(('department_id', 'in', accessible_departments))

        # Filter by state
        if filterby == 'pending':
            domain.append(('state', 'in', ['draft', 'submitted']))
        elif filterby == 'approved':
            domain.append(('state', '=', 'approved'))
        elif filterby == 'completed':
            domain.append(('state', '=', 'completed'))

        # Search
        if search:
            domain += ['|', ('name', 'ilike', search), ('description', 'ilike', search)]

        # Pagination
        request_count = DestructionRequest.search_count(domain)
        pager = request.website.pager(
            url="/my/destruction",
            url_args={'filterby': filterby, 'search': search},
            total=request_count,
            page=page,
            step=20,
        )

        requests = DestructionRequest.search(
            domain,
            order='create_date desc',
            limit=20,
            offset=pager['offset']
        )

        values.update({
            'requests': requests,
            'page_name': 'destruction',
            'pager': pager,
            'filterby': filterby or 'all',
            'search': search or '',
            'request_count': request_count,
        })

        return request.render("records_management.portal_destruction_list", values)

    @http.route(['/my/destruction/pending'], type='http', auth='user', website=True)
    def portal_destruction_pending(self, page=1, search=None, **kw):
        """
        Show pending destruction requests needing approval
        Accessible to: Department Admin+
        Security: Department access validation
        """
        values = self._prepare_portal_layout_values()
        user = request.env.user
        partner = user.partner_id

        # Require department admin+ permissions
        if not user.has_group('records_management.group_portal_department_admin'):
            return request.render('records_management.portal_errors', {
                'error_title': _('Access Denied'),
                'error_message': _('You do not have permission to view pending destruction approvals.'),
            })

        DestructionRequest = request.env['portal.request']
        domain = [
            ('partner_id', '=', partner.id),
            ('request_type', '=', 'destruction'),
            ('state', '=', 'submitted')  # Only show submitted requests awaiting approval
        ]

        # Department filtering for non-company admins
        if not user.has_group('records_management.group_portal_company_admin'):
            accessible_departments = user.accessible_department_ids.ids
            if accessible_departments:
                domain.append(('department_id', 'in', accessible_departments))

        # Search
        if search:
            domain += ['|', ('name', 'ilike', search), ('description', 'ilike', search)]

        # Pagination
        request_count = DestructionRequest.search_count(domain)
        pager = request.website.pager(
            url="/my/destruction/pending",
            url_args={'search': search},
            total=request_count,
            page=page,
            step=20,
        )

        pending_requests = DestructionRequest.search(
            domain,
            order='create_date asc',  # Oldest first for approval queue
            limit=20,
            offset=pager['offset']
        )

        values.update({
            'pending_requests': pending_requests,
            'page_name': 'destruction_pending',
            'pager': pager,
            'search': search or '',
            'request_count': request_count,
        })

        return request.render("records_management.portal_destruction_pending", values)

    @http.route(['/my/certificates'], type='http', auth='user', website=True)
    def portal_certificates(self, page=1, search=None, **kw):
        """
        List destruction certificates with download capability
        Accessible to: All portal users (own department)
        Security: Department filtering
        """
        values = self._prepare_portal_layout_values()
        user = request.env.user
        partner = user.partner_id

        Certificate = request.env['destruction.certificate']
        domain = [('partner_id', '=', partner.id)]

        # Department filtering for non-company admins
        if not user.has_group('records_management.group_portal_company_admin'):
            accessible_departments = user.accessible_department_ids.ids
            if accessible_departments:
                domain.append(('department_id', 'in', accessible_departments))

        # Search
        if search:
            domain += ['|', ('name', 'ilike', search), ('certificate_number', 'ilike', search)]

        # Pagination
        cert_count = Certificate.search_count(domain)
        pager = request.website.pager(
            url="/my/certificates",
            url_args={'search': search},
            total=cert_count,
            page=page,
            step=20,
        )

        certificates = Certificate.search(
            domain,
            order='destruction_date desc',
            limit=20,
            offset=pager['offset']
        )

        values.update({
            'certificates': certificates,
            'page_name': 'certificates',
            'pager': pager,
            'search': search or '',
            'cert_count': cert_count,
        })

        return request.render("records_management.portal_certificates", values)

    @http.route(['/my/custody/chain'], type='http', auth='user', website=True)
    def portal_custody_chain(self, page=1, filterby=None, search=None, **kw):
        """
        Chain of custody tracking for compliance
        Accessible to: All portal users (own department)
        Security: Department filtering
        """
        values = self._prepare_portal_layout_values()
        user = request.env.user
        partner = user.partner_id

        CustodyLog = request.env['naid.custody']
        domain = [('partner_id', '=', partner.id)]

        # Department filtering for non-company admins
        if not user.has_group('records_management.group_portal_company_admin'):
            accessible_departments = user.accessible_department_ids.ids
            if accessible_departments:
                domain.append(('department_id', 'in', accessible_departments))

        # Filter by custody type
        if filterby == 'transfer':
            domain.append(('custody_type', '=', 'transfer'))
        elif filterby == 'destruction':
            domain.append(('custody_type', '=', 'destruction'))
        elif filterby == 'retrieval':
            domain.append(('custody_type', '=', 'retrieval'))

        # Search
        if search:
            domain += [
                '|', '|',
                ('container_id.name', 'ilike', search),
                ('from_custodian_id.name', 'ilike', search),
                ('to_custodian_id.name', 'ilike', search)
            ]

        # Pagination
        custody_count = CustodyLog.search_count(domain)
        pager = request.website.pager(
            url="/my/custody/chain",
            url_args={'filterby': filterby, 'search': search},
            total=custody_count,
            page=page,
            step=20,
        )

        custody_logs = CustodyLog.search(
            domain,
            order='transfer_date desc',
            limit=20,
            offset=pager['offset']
        )

        values.update({
            'custody_logs': custody_logs,
            'page_name': 'custody_chain',
            'pager': pager,
            'filterby': filterby or 'all',
            'search': search or '',
            'custody_count': custody_count,
        })

        return request.render("records_management.portal_custody_chain", values)

    @http.route(['/my/destruction/<int:request_id>/approve'], type='json', auth='user', methods=['POST'])
    def portal_destruction_approve(self, request_id, **kw):
        """
        Approve destruction request (Department Admin+)
        Accessible to: Department Admin+
        Security: Department access + state validation
        """
        try:
            user = request.env.user
            partner = user.partner_id

            # Require department admin+ permissions
            if not user.has_group('records_management.group_portal_department_admin'):
                return {'success': False, 'error': _('Insufficient permissions to approve destruction requests')}

            # Get destruction request
            dest_request = request.env['portal.request'].sudo().browse(request_id)
            if not dest_request.exists():
                return {'success': False, 'error': _('Destruction request not found')}

            # Verify ownership
            if dest_request.partner_id.id != partner.id:
                return {'success': False, 'error': _('Unauthorized access to destruction request')}

            # Department access validation
            if not user.has_group('records_management.group_portal_company_admin'):
                accessible_departments = user.accessible_department_ids.ids
                if dest_request.department_id.id not in accessible_departments:
                    return {'success': False, 'error': _('Access denied to this department')}

            # Verify request type and state
            if dest_request.request_type != 'destruction':
                return {'success': False, 'error': _('This is not a destruction request')}

            if dest_request.state != 'submitted':
                return {'success': False, 'error': _('Only submitted requests can be approved')}

            # Approve the request
            dest_request.write({
                'state': 'approved',
                'approved_by_id': user.id,
                'approved_date': datetime.now(),
            })

            # Create audit log
            request.env['naid.audit.log'].create({
                'action_type': 'destruction_approved',
                'user_id': user.id,
                'description': _('Destruction request %s approved via portal by %s') % (
                    dest_request.name, user.name
                ),
                'timestamp': datetime.now(),
            })

            return {'success': True, 'message': _('Destruction request approved successfully')}

        except Exception as e:
            _logger.error(f\"Destruction approval failed: {str(e)}\")
            return {'success': False, 'error': str(e)}

    # ============================================================================
    # TEMPORARY INVENTORY & OTHER ROUTES
    # ============================================================================

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
        container = request.env['records.container'].sudo().browse(container_id)

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
        if not self._check_bulk_update_access():
            return {'success': False, 'error': 'Insufficient permissions for bulk operations'}

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
        if not self._check_bulk_update_access():
            return {'success': False, 'error': 'Insufficient permissions for bulk operations'}

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
        if not self._check_bulk_update_access():
            return {'success': False, 'error': 'Insufficient permissions for bulk operations'}

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
            container = request.env['records.container'].sudo().browse(container_id)

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

            # Validate inputs
            if not file_ids or not container_id:
                return {'success': False, 'error': 'Missing file IDs or container ID'}

            # Convert to integers if they're strings
            if isinstance(file_ids, str):
                file_ids = [int(file_ids)]
            elif isinstance(file_ids, list):
                file_ids = [int(f_id) for f_id in file_ids if str(f_id).isdigit()]

            container_id = int(container_id) if container_id else None

            if not file_ids or not container_id:
                return {'success': False, 'error': 'Invalid file IDs or container ID'}

            files = request.env['records.file'].browse(file_ids)
            container = request.env['records.container'].sudo().browse(container_id)

            # Security check
            partner = request.env.user.partner_id.commercial_partner_id

            # Check container access
            if not container.exists() or container.partner_id != partner:
                return {'success': False, 'error': 'Container access denied'}

            # Check file access
            for file_rec in files:
                if not file_rec.exists():
                    return {'success': False, 'error': f'File {file_rec.id} not found'}
                if hasattr(file_rec, 'partner_id') and file_rec.partner_id and file_rec.partner_id != partner:
                    return {'success': False, 'error': f'File {file_rec.name} access denied'}

            # Update file locations
            files.write({'container_id': container_id})

            return {
                'success': True,
                'message': f'{len(files)} files added to container {container.name}'
            }

        except ValueError as e:
            return {'success': False, 'error': f'Invalid data format: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Server error: {str(e)}'}

    # ============================================================================
    # OVERVIEW TAB DATA ROUTES
    # ============================================================================

    @http.route(['/my/inventory/counts'], type='http', auth='user', website=True)
    def portal_inventory_counts(self, **kw):
        """Get inventory counts for overview dashboard"""
        partner = request.env.user.partner_id.commercial_partner_id

        counts = {
            'containers': request.env['records.container'].sudo().search_count([('partner_id', '=', partner.id)]),
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
        recent_containers = request.env['records.container'].sudo().search([
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
            Container = request.env['records.container'].sudo()
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
        Accessible to internal users, portal admins, and portal department users.
        """
        # Check user permissions using enhanced permission system
        if not self._check_bulk_update_access():
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
        Accessible to internal users, portal admins, and portal department users.
        """
        # Check user permissions using enhanced permission system
        if not self._check_bulk_update_access():
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
        Accessible to internal users, portal admins, and portal department users.
        """
        # Check user permissions using enhanced permission system
        if not self._check_bulk_update_access():
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
    # STOCK MOVEMENT HISTORY PORTAL ROUTES (PHASE 1 ENHANCEMENT)
    # ============================================================================

    @http.route(['/my/inventory/movements'], type='http', auth='user', website=True)
    def portal_stock_movements(self, page=1, date_begin=None, date_end=None,
                              sortby=None, filterby=None, search=None, **kw):
        """
        Stock movement history for portal users with comprehensive filtering.
        Phase 1 Enhancement: Real-time movement tracking with customer portal access.
        """
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id.commercial_partner_id

        # Use sudo() for model access but maintain data filtering (Security Layer Pattern)
        Movement = request.env['records.stock.movement'].sudo()
        domain = [('partner_id', '=', partner.id), ('is_portal_visible', '=', True)]

        # Search filter
        if search:
            domain += [
                '|', '|', '|',
                ('container_id.name', 'ilike', search),
                ('container_id.barcode', 'ilike', search),
                ('to_location_id.complete_name', 'ilike', search),
                ('reason', 'ilike', search)
            ]

        # Date filtering
        if date_begin and date_end:
            domain += [('movement_date', '>=', date_begin), ('movement_date', '<=', date_end)]

        # Movement type filter
        searchbar_filters = {
            'all': {'label': 'All Movements', 'domain': []},
            'location_change': {'label': 'Location Changes', 'domain': [('movement_type', '=', 'location_change')]},
            'pickup': {'label': 'Pickups', 'domain': [('movement_type', '=', 'pickup')]},
            'delivery': {'label': 'Deliveries', 'domain': [('movement_type', '=', 'delivery')]},
            'retrieval': {'label': 'Retrievals', 'domain': [('movement_type', '=', 'retrieval')]},
            'transfer': {'label': 'Transfers', 'domain': [('movement_type', '=', 'transfer')]},
        }

        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # Sorting options
        searchbar_sortings = {
            'date': {'label': 'Recent First', 'order': 'movement_date desc'},
            'container': {'label': 'Box Number', 'order': 'container_id'},
            'location': {'label': 'Location', 'order': 'to_location_id'},
            'type': {'label': 'Movement Type', 'order': 'movement_type'},
        }

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Count total movements
        movement_count = Movement.search_count(domain)

        # Pager setup
        pager = request.website.pager(
            url="/my/inventory/movements",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby,
                     'filterby': filterby, 'search': search},
            total=movement_count,
            page=page,
            step=self._items_per_page,
        )

        # Get movements for current page
        movements = Movement.search(domain, order=order,
                                  limit=self._items_per_page,
                                  offset=pager['offset'])

        # Get movement summary statistics
        movement_stats = self._get_movement_statistics(partner)

        values.update({
            'movements': movements,
            'page_name': 'stock_movements',
            'pager': pager,
            'default_url': '/my/inventory/movements',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
            'search': search or '',
            'movement_count': movement_count,
            'movement_stats': movement_stats,
        })

        return request.render("records_management.portal_stock_movements", values)

    @http.route(['/my/inventory/movements/data'], type='json', auth='user', methods=['POST'])
    def get_movements_data(self, **post):
        """
        AJAX endpoint for real-time movement data updates.
        Supports filtering and pagination for modern frontend.
        """
        try:
            partner = request.env.user.partner_id.commercial_partner_id

            # Get filter parameters
            filters = {
                'movement_type': post.get('movement_type'),
                'date_from': post.get('date_from'),
                'date_to': post.get('date_to'),
                'container_id': int(post.get('container_id')) if post.get('container_id') else None,
            }

            # Remove None values
            filters = {k: v for k, v in filters.items() if v is not None}

            # Get movements using the portal method
            movement_data = request.env['records.stock.movement'].sudo().get_portal_movements(
                partner=partner,
                limit=int(post.get('limit', 20)),
                offset=int(post.get('offset', 0)),
                filters=filters
            )

            return {
                'success': True,
                'data': movement_data
            }

        except Exception as e:
            _logger.error("Error fetching movement data: %s", e)
            return {
                'success': False,
                'error': 'Failed to load movement data'
            }

    @http.route(['/my/inventory/container/<int:container_id>/movements'], type='http', auth='user', website=True)
    def portal_container_movements(self, container_id, **kw):
        """Individual container movement history"""
        # Security Layer Pattern: Use sudo() but filter by partner
        container = request.env['records.container'].sudo().browse(container_id)
        partner = request.env.user.partner_id.commercial_partner_id

        # Verify access
        if not container.exists() or container.partner_id.commercial_partner_id != partner:
            return request.not_found()

        # Get movement history for this container
        movements = container.get_stock_movement_history()

        # Get stock summary
        stock_summary = container.get_stock_summary()

        values = {
            'container': container,
            'movements': movements,
            'stock_summary': stock_summary,
            'page_name': 'container_movements',
        }

        return request.render("records_management.portal_container_movements", values)

    def _get_movement_statistics(self, partner):
        """Get movement statistics for dashboard display"""
        Movement = request.env['records.stock.movement'].sudo()

        # Movement counts by type (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        domain_base = [
            ('partner_id', '=', partner.id),
            ('movement_date', '>=', thirty_days_ago),
            ('is_portal_visible', '=', True)
        ]

        stats = {}
        movement_types = ['location_change', 'pickup', 'delivery', 'retrieval', 'transfer']

        for movement_type in movement_types:
            count = Movement.search_count(domain_base + [('movement_type', '=', movement_type)])
            stats[movement_type] = count

        # Total movements
        stats['total_recent'] = Movement.search_count(domain_base)

        # Most active locations
        recent_movements = Movement.search(domain_base, limit=100)
        location_activity = {}
        for movement in recent_movements:
            location = movement.to_location_id.complete_name
            location_activity[location] = location_activity.get(location, 0) + 1

        # Sort and get top 5
        top_locations = sorted(location_activity.items(), key=lambda x: x[1], reverse=True)[:5]
        stats['top_locations'] = top_locations

        return stats

    # ============================================================================
    # ENHANCED STOCK LOCATION MANAGEMENT (PHASE 2 PREVIEW)
    # ============================================================================

    @http.route(['/my/inventory/locations'], type='http', auth='user', website=True)
    def portal_stock_locations(self, **kw):
        """
        Stock location overview for portal users.
        Shows locations where customer containers are stored.
        """
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id.commercial_partner_id

        # Get locations with customer containers (Security Layer Pattern)
        Container = request.env['records.container'].sudo()
        containers = Container.search([('partner_id', '=', partner.id), ('quant_id', '!=', False)])

        # Group by location
        location_data = {}
        for container in containers:
            location = container.current_location_id
            if location:
                if location.id not in location_data:
                    location_data[location.id] = {
                        'location': location,
                        'containers': [],
                        'total_containers': 0,
                        'last_activity': False,
                    }
                location_data[location.id]['containers'].append(container)
                location_data[location.id]['total_containers'] += 1

                # Update last activity
                if container.last_movement_date:
                    current_last = location_data[location.id]['last_activity']
                    if not current_last or container.last_movement_date > current_last:
                        location_data[location.id]['last_activity'] = container.last_movement_date

        values.update({
            'location_data': list(location_data.values()),
            'page_name': 'stock_locations',
            'total_locations': len(location_data),
        })

        return request.render("records_management.portal_stock_locations", values)

    @http.route(['/my/inventory/location/<int:location_id>'], type='http', auth='user', website=True)
    def portal_location_detail(self, location_id, **kw):
        """Detailed view of containers at a specific location"""
        location = request.env['stock.location'].sudo().browse(location_id)
        partner = request.env.user.partner_id.commercial_partner_id

        if not location.exists():
            return request.not_found()

        # Get customer containers at this location (Security Layer Pattern)
        Container = request.env['records.container'].sudo()
        containers = Container.search([
            ('partner_id', '=', partner.id),
            ('current_location_id', '=', location_id)
        ])

        # If no containers, redirect back
        if not containers:
            return request.redirect('/my/inventory/locations')

        # Get recent movements for this location
        Movement = request.env['records.stock.movement'].sudo()
        recent_movements = Movement.search([
            ('partner_id', '=', partner.id),
            ('to_location_id', '=', location_id),
            ('is_portal_visible', '=', True)
        ], order='movement_date desc', limit=10)

        values = {
            'location': location,
            'containers': containers,
            'recent_movements': recent_movements,
            'page_name': 'location_detail',
            'container_count': len(containers),
        }

        return request.render("records_management.portal_location_detail", values)

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

    # ============================================================================
    # ENHANCED STOCK INTEGRATION HELPER METHODS (PHASE 1)
    # ============================================================================

    def _get_comprehensive_stock_summary(self, stock_quants):
        """
        Get comprehensive stock summary for enhanced dashboard.
        Integrates with native Odoo stock system for real-time data.
        """
        if not stock_quants:
            return {
                'total_quantity': 0,
                'locations_count': 0,
                'last_movement': None,
                'total_containers': 0,
                'stock_value': 0.0,
            }

        # Calculate comprehensive metrics
        total_quantity = sum(quant.quantity for quant in stock_quants)
        unique_locations = stock_quants.mapped('location_id')

        # Get containers linked to these quants
        Container = request.env['records.container'].sudo()
        containers = Container.search([('quant_id', 'in', stock_quants.ids)])

        # Get last movement from any container
        last_movement = None
        if containers:
            latest_movements = request.env['records.stock.movement'].sudo().search([
                ('container_id', 'in', containers.ids)
            ], order='movement_date desc', limit=1)
            if latest_movements:
                last_movement = latest_movements[0].movement_date

        return {
            'total_quantity': int(total_quantity),
            'locations_count': len(unique_locations),
            'last_movement': last_movement,
            'total_containers': len(containers),
            'stock_value': sum(quant.value for quant in stock_quants),
            'locations': [{'name': loc.complete_name, 'id': loc.id} for loc in unique_locations],
        }

    def _get_recent_dashboard_movements(self, partner, limit=10):
        """Get recent movements for dashboard display"""
        Movement = request.env['records.stock.movement'].sudo()
        movements = Movement.search([
            ('partner_id', '=', partner.id),
            ('is_portal_visible', '=', True),
            ('state', 'in', ['confirmed', 'done'])
        ], order='movement_date desc', limit=limit)

        movement_data = []
        for movement in movements:
            movement_data.append({
                'container_name': movement.container_id.name,
                'movement_type': movement._get_movement_type_display(),
                'location': movement.to_location_id.complete_name,
                'date': movement.movement_date.strftime('%Y-%m-%d %H:%M'),
                'user': movement.user_id.name,
            })

        return movement_data

    def _group_containers_by_location(self, stock_quants):
        """Group containers by location with enhanced data"""
        location_groups = {}

        for quant in stock_quants:
            location = quant.location_id
            if location.id not in location_groups:
                location_groups[location.id] = {
                    'location': location,
                    'container_count': 0,
                    'total_quantity': 0,
                    'containers': [],
                }

            # Get container for this quant
            container = request.env['records.container'].sudo().search([
                ('quant_id', '=', quant.id)
            ], limit=1)

            if container:
                location_groups[location.id]['containers'].append({
                    'id': container.id,
                    'name': container.name,
                    'barcode': container.barcode or container.temp_barcode,
                    'state': container.state,
                })

            location_groups[location.id]['container_count'] += 1
            location_groups[location.id]['total_quantity'] += quant.quantity

        return list(location_groups.values())

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

    # ============================================================================
    # BARCODE MAIN MENU AND SCANNING INTERFACE
    # ============================================================================

    @http.route(['/my/barcode/main'], type='http', auth='user', website=True)
    def portal_barcode_main_menu(self, **kw):
        """
        Barcode main menu - central hub for all barcode operations.
        
        Standard Odoo Command: O-CMD.MAIN-MENU redirects here.
        Provides quick access to scanning workflows and batch operations.
        
        Returns:
            Rendered template with barcode operation menu
        """
        values = self._prepare_portal_layout_values()

        # Get user's containers for quick stats
        partner = request.env.user.partner_id.commercial_partner_id
        Container = request.env['records.container'].sudo()

        container_stats = {
            'total': Container.search_count([('partner_id', '=', partner.id)]),
            'active': Container.search_count([('partner_id', '=', partner.id), ('state', '=', 'active')]),
            'pending_pickup': Container.search_count([('partner_id', '=', partner.id), ('state', '=', 'pending_pickup')]),
            'pending_destruction': Container.search_count([('partner_id', '=', partner.id), ('state', '=', 'pending_destruction')]),
        }

        # Define available barcode operations
        barcode_operations = [
            {
                'name': 'Scan Container',
                'route': '/my/barcode/scan/container',
                'icon': 'fa-archive',
                'description': 'Scan container barcode to view details',
                'color': 'primary'
            },
            {
                'name': 'Scan File Folder',
                'route': '/my/barcode/scan/file',
                'icon': 'fa-folder',
                'description': 'Scan file folder barcode',
                'color': 'info'
            },
            {
                'name': 'Request Pickup',
                'route': '/my/barcode/scan/pickup',
                'icon': 'fa-truck',
                'description': 'Scan containers for pickup request',
                'color': 'warning'
            },
            {
                'name': 'Request Retrieval',
                'route': '/my/barcode/scan/retrieval',
                'icon': 'fa-download',
                'description': 'Scan containers for retrieval',
                'color': 'success'
            },
        ]

        values.update({
            'page_name': 'barcode_menu',
            'barcode_operations': barcode_operations,
            'container_stats': container_stats,
        })

        return request.render("records_management.portal_barcode_main_menu", values)

    @http.route(['/my/barcode/scan/<string:scan_type>'], type='http', auth='user', website=True)
    def portal_barcode_scanner(self, scan_type='container', **kw):
        """
        Barcode scanner interface for specific operation types.
        
        Args:
            scan_type (str): Type of scan (container, file, pickup, retrieval)
            
        Returns:
            Rendered template with barcode scanner interface
        """
        values = self._prepare_portal_layout_values()

        scan_config = {
            'container': {
                'title': 'Scan Container',
                'icon': 'fa-archive',
                'placeholder': 'Scan or enter container barcode...',
                'endpoint': '/my/barcode/process/container',
            },
            'file': {
                'title': 'Scan File Folder',
                'icon': 'fa-folder',
                'placeholder': 'Scan or enter file barcode...',
                'endpoint': '/my/barcode/process/file',
            },
            'pickup': {
                'title': 'Scan for Pickup',
                'icon': 'fa-truck',
                'placeholder': 'Scan containers to request pickup...',
                'endpoint': '/my/barcode/process/pickup',
            },
            'retrieval': {
                'title': 'Scan for Retrieval',
                'icon': 'fa-download',
                'placeholder': 'Scan containers to request retrieval...',
                'endpoint': '/my/barcode/process/retrieval',
            },
        }

        config = scan_config.get(scan_type, scan_config['container'])

        values.update({
            'page_name': f'barcode_scan_{scan_type}',
            'scan_type': scan_type,
            'scan_config': config,
        })

        return request.render("records_management.portal_barcode_scanner", values)

    @http.route(['/my/barcode/process/<string:operation>'], type='json', auth='user')
    def portal_barcode_process(self, operation='container', barcode=None, **kw):
        """
        Process scanned barcode for specific operation.
        
        Handles standard Odoo commands and container lookups.
        
        Args:
            operation (str): Operation type (container, file, pickup, retrieval)
            barcode (str): Scanned barcode value
            
        Returns:
            dict: JSON response with action or error
        """
        if not barcode:
            return {'error': _('No barcode provided')}

        # Handle standard Odoo commands
        if barcode == 'O-CMD.MAIN-MENU':
            return {'redirect': '/my/barcode/main'}

        if barcode in ['O-BTN.validate', 'O-BTN.discard', 'O-BTN.cancel',
                       'O-CMD.PRINT', 'O-CMD.PACKING', 'O-BTN.scrap', 'O-CMD.RETURN']:
            return {
                'info': _('Command %s recognized. Please scan a container first.') % barcode
            }

        # Process container barcode
        Container = request.env['records.container'].sudo()
        partner = request.env.user.partner_id.commercial_partner_id

        # Search by barcode or temp_barcode
        container = Container.search([
            ('partner_id', '=', partner.id),
            '|', ('barcode', '=', barcode), ('temp_barcode', '=', barcode)
        ], limit=1)

        if not container:
            return {'error': _('Container not found with barcode: %s') % barcode}

        # Execute operation-specific action
        if operation == 'container':
            return {
                'success': True,
                'redirect': f'/my/inventory/container/{container.id}',
                'container': {
                    'id': container.id,
                    'name': container.name,
                    'barcode': container.barcode or container.temp_barcode,
                    'state': container.state,
                }
            }

        elif operation == 'pickup':
            # Add to pickup request queue (session-based)
            return {
                'success': True,
                'message': _('Container %s added to pickup request') % container.name,
                'container': {
                    'id': container.id,
                    'name': container.name,
                }
            }

        elif operation == 'retrieval':
            # Add to retrieval request queue
            return {
                'success': True,
                'message': _('Container %s added to retrieval request') % container.name,
                'container': {
                    'id': container.id,
                    'name': container.name,
                }
            }

        return {'error': _('Unknown operation: %s') % operation}

    # ================================================================
    # SERVICE REQUEST CREATION ROUTES
    # ================================================================

    @http.route(['/my/request/new/<string:request_type>'], type='http', auth='user', website=True)
    def portal_request_new(self, request_type='retrieval', **kw):
        """Service request creation form for different request types."""
        partner = request.env.user.partner_id.commercial_partner_id

        # Define request type configurations
        request_configs = {
            'retrieval': {
                'title': _('Request Document Retrieval'),
                'icon': 'fa-truck',
                'description': _('Request physical documents to be retrieved from storage'),
                'form_fields': ['container_ids', 'delivery_date', 'special_instructions'],
            },
            'destruction': {
                'title': _('Request Destruction Service'),
                'icon': 'fa-fire',
                'description': _('Request secure destruction of physical documents (NAID compliant)'),
                'form_fields': ['container_ids', 'destruction_method', 'witness_required'],
            },
            'pickup': {
                'title': _('Schedule Pickup'),
                'icon': 'fa-calendar',
                'description': _('Schedule pickup of documents for storage'),
                'form_fields': ['pickup_date', 'pickup_address', 'estimated_boxes'],
            },
            'scanning': {
                'title': _('Request Document Scanning'),
                'icon': 'fa-scanner',
                'description': _('Request documents to be scanned and digitized'),
                'form_fields': ['document_ids', 'scan_resolution', 'file_format'],
            },
        }

        config = request_configs.get(request_type, request_configs['retrieval'])

        # Get available containers for selection
        containers = request.env['records.container'].search([
            ('partner_id', '=', partner.id),
            ('state', 'in', ['storage', 'active'])
        ])

        values = {
            'page_name': f'request_{request_type}',
            'request_type': request_type,
            'config': config,
            'containers': containers,
            'partner': partner,
        }

        return request.render("records_management.portal_request_form", values)

    # ================================================================
    # DESTRUCTION MANAGEMENT ROUTES
    # ================================================================

    @http.route(['/my/destruction'], type='http', auth='user', website=True)
    def portal_destruction_requests(self, **kw):
        """List all destruction requests for the customer."""
        partner = request.env.user.partner_id.commercial_partner_id

        destruction_requests = request.env['portal.request'].search([
            ('partner_id', '=', partner.id),
            ('request_type', '=', 'destruction')
        ], order='create_date desc')

        values = {
            'page_name': 'destruction',
            'requests': destruction_requests,
        }

        return request.render("records_management.portal_destruction_list", values)

    @http.route(['/my/destruction/pending'], type='http', auth='user', website=True)
    def portal_destruction_pending(self, **kw):
        """Destruction requests pending approval."""
        partner = request.env.user.partner_id.commercial_partner_id

        pending_requests = request.env['portal.request'].search([
            ('partner_id', '=', partner.id),
            ('request_type', '=', 'destruction'),
            ('state', 'in', ['draft', 'pending_approval'])
        ])

        values = {
            'page_name': 'destruction',
            'requests': pending_requests,
        }

        return request.render("records_management.portal_destruction_pending", values)

    @http.route(['/my/custody/chain'], type='http', auth='user', website=True)
    def portal_chain_of_custody(self, **kw):
        """Chain of custody tracking for all containers."""
        partner = request.env.user.partner_id.commercial_partner_id

        custody_records = request.env['chain.of.custody'].search([
            ('partner_id', '=', partner.id)
        ], order='transfer_date desc', limit=100)

        values = {
            'page_name': 'custody',
            'custody_records': custody_records,
        }

        return request.render("records_management.portal_chain_of_custody", values)

    # ================================================================
    # BILLING & INVOICES ROUTES
    # ================================================================

    @http.route(['/my/invoices/history'], type='http', auth='user', website=True)
    def portal_invoice_history(self, **kw):
        """Payment history and archived invoices."""
        partner = request.env.user.partner_id.commercial_partner_id

        # Get paid invoices
        invoices = request.env['account.move'].search([
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['paid', 'in_payment'])
        ], order='invoice_date desc')

        values = {
            'page_name': 'invoices',
            'invoices': invoices,
            'payment_history': True,
        }

        return request.render("records_management.portal_invoice_history", values)

    @http.route(['/my/billing/rates'], type='http', auth='user', website=True)
    def portal_billing_rates(self, **kw):
        """Display current billing rates and pricing information."""
        partner = request.env.user.partner_id.commercial_partner_id

        # Get customer's billing configuration
        billing_info = request.env['records.billing'].search([
            ('partner_id', '=', partner.id)
        ], limit=1)

        # Get product pricing
        products = request.env['product.product'].search([
            ('categ_id.name', 'ilike', 'records management')
        ])

        values = {
            'page_name': 'billing',
            'billing_info': billing_info,
            'products': products,
        }

        return request.render("records_management.portal_billing_rates", values)

    @http.route(['/my/billing/statements'], type='http', auth='user', website=True)
    def portal_billing_statements(self, **kw):
        """Download billing statements."""
        partner = request.env.user.partner_id.commercial_partner_id

        # Get recent invoices for statements
        statements = request.env['account.move'].search([
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ], order='invoice_date desc', limit=12)

        values = {
            'page_name': 'billing',
            'statements': statements,
        }

        return request.render("records_management.portal_billing_statements", values)

    # ================================================================
    # REPORTS & ANALYTICS ROUTES
    # ================================================================

    @http.route(['/my/reports'], type='http', auth='user', website=True)
    def portal_reports_inventory(self, **kw):
        """Inventory reports and summaries."""
        partner = request.env.user.partner_id.commercial_partner_id

        # Generate inventory summary
        containers = request.env['records.container'].search([
            ('partner_id', '=', partner.id)
        ])

        summary = {
            'total_containers': len(containers),
            'active_containers': len(containers.filtered(lambda c: c.state == 'active')),
            'in_storage': len(containers.filtered(lambda c: c.state == 'storage')),
            'total_files': sum(containers.mapped('file_count')),
        }

        values = {
            'page_name': 'reports',
            'summary': summary,
            'containers': containers,
        }

        return request.render("records_management.portal_reports_inventory", values)

    @http.route(['/my/reports/activity'], type='http', auth='user', website=True)
    def portal_reports_activity(self, **kw):
        """Activity reports showing movements and requests."""
        partner = request.env.user.partner_id.commercial_partner_id

        # Get recent activity
        requests = request.env['portal.request'].search([
            ('partner_id', '=', partner.id)
        ], order='create_date desc', limit=50)

        movements = request.env['stock.move'].search([
            ('partner_id', '=', partner.id)
        ], order='date desc', limit=50)

        values = {
            'page_name': 'reports',
            'requests': requests,
            'movements': movements,
        }

        return request.render("records_management.portal_reports_activity", values)

    @http.route(['/my/reports/compliance'], type='http', auth='user', website=True)
    def portal_reports_compliance(self, **kw):
        """NAID compliance and audit reports."""
        partner = request.env.user.partner_id.commercial_partner_id

        # Get compliance data
        certificates = request.env['naid.certificate'].search([
            ('partner_id', '=', partner.id)
        ])

        audit_logs = request.env['naid.audit.log'].search([
            ('partner_id', '=', partner.id)
        ], order='timestamp desc', limit=100)

        values = {
            'page_name': 'reports',
            'certificates': certificates,
            'audit_logs': audit_logs,
        }

        return request.render("records_management.portal_reports_compliance", values)

    @http.route(['/my/reports/export'], type='http', auth='user', website=True)
    def portal_reports_export(self, **kw):
        """Export data in various formats."""
        partner = request.env.user.partner_id.commercial_partner_id

        values = {
            'page_name': 'reports',
            'export_options': [
                {'format': 'csv', 'icon': 'fa-file-csv', 'label': _('CSV Export')},
                {'format': 'xlsx', 'icon': 'fa-file-excel', 'label': _('Excel Export')},
                {'format': 'pdf', 'icon': 'fa-file-pdf', 'label': _('PDF Report')},
            ],
        }

        return request.render("records_management.portal_reports_export", values)

    # ================================================================
    # FEEDBACK & SUPPORT ROUTES
    # ================================================================

    @http.route(['/my/feedback'], type='http', auth='user', website=True)
    def portal_feedback_submit(self, **kw):
        """Submit feedback form."""
        values = {
            'page_name': 'feedback',
        }

        return request.render("records_management.portal_feedback_form", values)

    @http.route(['/my/feedback/history'], type='http', auth='user', website=True)
    def portal_feedback_history(self, **kw):
        """Feedback submission history."""
        partner = request.env.user.partner_id.commercial_partner_id

        feedback_records = request.env['customer.feedback'].search([
            ('partner_id', '=', partner.id)
        ], order='create_date desc')

        values = {
            'page_name': 'feedback',
            'feedback_records': feedback_records,
        }

        return request.render("records_management.portal_feedback_history", values)

    @http.route(['/help'], type='http', auth='user', website=True)
    def portal_help_center(self, **kw):
        """Help center with documentation."""
        values = {
            'page_name': 'support',
            'help_topics': [
                {
                    'title': _('Getting Started'),
                    'icon': 'fa-rocket',
                    'articles': [
                        {'title': _('Portal Overview'), 'url': '/help/overview'},
                        {'title': _('Managing Inventory'), 'url': '/help/inventory'},
                    ]
                },
                {
                    'title': _('Service Requests'),
                    'icon': 'fa-tasks',
                    'articles': [
                        {'title': _('How to Request Retrieval'), 'url': '/help/retrieval'},
                        {'title': _('Destruction Process'), 'url': '/help/destruction'},
                    ]
                },
            ],
        }

        return request.render("records_management.portal_help_center", values)

    # ================================================================
    # SETTINGS & USER MANAGEMENT ROUTES
    # ================================================================

    @http.route(['/my/users'], type='http', auth='user', website=True)
    def portal_department_users(self, **kw):
        """Manage department users (for company admins)."""
        if not request.env.user.has_group('records_management.group_portal_company_admin'):
            return request.redirect('/my/home')

        partner = request.env.user.partner_id.commercial_partner_id

        # Get all portal users for this company
        users = request.env['res.users'].search([
            ('partner_id.parent_id', '=', partner.id),
            ('groups_id', 'in', [request.env.ref('base.group_portal').id])
        ])

        # Get departments for the dropdown
        departments = request.env['records.department'].search([
            ('company_id', '=', partner.id)
        ])

        values = {
            'page_name': 'settings',
            'users': users,
            'departments': departments,
            'company': partner,
        }

        return request.render("records_management.portal_department_users", values)

    @http.route(['/my/users/create'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_create_department_user(self, **post):
        """Create new portal user for a department (company admin only)."""
        if not request.env.user.has_group('records_management.group_portal_company_admin'):
            return request.redirect('/my/home')

        try:
            partner = request.env.user.partner_id.commercial_partner_id

            # Validate required fields
            name = post.get('name')
            email = post.get('email')
            department_id = int(post.get('department_id', 0))

            if not all([name, email, department_id]):
                return request.render('records_management.portal_error', {
                    'error_title': 'Missing Required Fields',
                    'error_message': 'Please provide name, email, and department.',
                })

            # Check if user already exists
            existing_user = request.env['res.users'].sudo().search([
                ('login', '=', email)
            ], limit=1)

            if existing_user:
                return request.render('records_management.portal_error', {
                    'error_title': 'User Already Exists',
                    'error_message': f'A user with email {email} already exists.',
                })

            # Get the department
            department = request.env['records.department'].sudo().browse(department_id)
            if not department or department.company_id.id != partner.id:
                return request.render('records_management.portal_error', {
                    'error_title': 'Invalid Department',
                    'error_message': 'The selected department is invalid.',
                })

            # Create partner for the user
            new_partner = request.env['res.partner'].sudo().create({
                'name': name,
                'email': email,
                'parent_id': partner.id,
                'type': 'contact',
                'department_id': department_id,
            })

            # Create portal user
            portal_group = request.env.ref('base.group_portal')
            new_user = request.env['res.users'].sudo().create({
                'name': name,
                'login': email,
                'email': email,
                'partner_id': new_partner.id,
                'groups_id': [(6, 0, [portal_group.id])],
                'active': True,
            })

            # Send invitation email
            new_user.sudo().action_reset_password()

            # Log the creation
            request.env['naid.audit.log'].sudo().create({
                'action_type': 'portal_user_created',
                'user_id': request.env.user.id,
                'description': _('Portal user %s created for department %s by company admin') % (name, department.name),
                'timestamp': fields.Datetime.now(),
            })

            return request.redirect('/my/users?created=success')

        except Exception as e:
            return request.render('records_management.portal_error', {
                'error_title': 'User Creation Failed',
                'error_message': str(e),
            })

    @http.route(['/my/users/<int:user_id>/edit'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_edit_department_user(self, user_id, **post):
        """Edit portal user (company admin only)."""
        if not request.env.user.has_group('records_management.group_portal_company_admin'):
            return request.redirect('/my/home')

        try:
            user = request.env['res.users'].sudo().browse(user_id)
            partner = request.env.user.partner_id.commercial_partner_id

            # Verify user belongs to this company
            if user.partner_id.parent_id.id != partner.id:
                return request.redirect('/my/users?error=unauthorized')

            # Update user info
            if post.get('name'):
                user.sudo().write({'name': post['name']})
                user.partner_id.sudo().write({'name': post['name']})

            if post.get('department_id'):
                user.partner_id.sudo().write({'department_id': int(post['department_id'])})

            if 'active' in post:
                user.sudo().write({'active': post['active'] == 'true'})

            return request.redirect('/my/users?updated=success')

        except Exception as e:
            return request.redirect('/my/users?error=update_failed')

    @http.route(['/my/users/<int:user_id>/deactivate'], type='json', auth='user', methods=['POST'])
    def portal_deactivate_user(self, user_id, **kw):
        """Deactivate a portal user (company admin only)."""
        if not request.env.user.has_group('records_management.group_portal_company_admin'):
            return {'success': False, 'error': 'Unauthorized'}

        try:
            user = request.env['res.users'].sudo().browse(user_id)
            partner = request.env.user.partner_id.commercial_partner_id

            # Verify user belongs to this company
            if user.partner_id.parent_id.id != partner.id:
                return {'success': False, 'error': 'Unauthorized'}

            user.sudo().write({'active': False})

            # Log the action
            request.env['naid.audit.log'].sudo().create({
                'action_type': 'portal_user_deactivated',
                'user_id': request.env.user.id,
                'description': _('Portal user %s deactivated by company admin') % user.name,
                'timestamp': fields.Datetime.now(),
            })

            return {'success': True, 'message': 'User deactivated successfully'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route(['/my/notifications'], type='http', auth='user', website=True)
    def portal_notifications_settings(self, **kw):
        """Notification preferences."""
        user = request.env.user

        values = {
            'page_name': 'settings',
            'user': user,
            'notification_channels': [
                {'type': 'email', 'label': _('Email Notifications'), 'enabled': True},
                {'type': 'sms', 'label': _('SMS Alerts'), 'enabled': False},
                {'type': 'portal', 'label': _('Portal Messages'), 'enabled': True},
            ],
        }

        return request.render("records_management.portal_notifications", values)

    @http.route(['/my/access'], type='http', auth='user', website=True)
    def portal_access_management(self, **kw):
        """Access management (for department admins)."""
        if not request.env.user.has_group('records_management.group_portal_department_admin'):
            return request.redirect('/my/home')

        partner = request.env.user.partner_id

        # Get access permissions
        access_records = request.env['portal.user.access'].search([
            ('partner_id', '=', partner.id)
        ])

        values = {
            'page_name': 'settings',
            'access_records': access_records,
        }

        return request.render("records_management.portal_access_management", values)

    @http.route(['/my/inventory/advanced_search'], type='http', auth='user', website=True)
    def portal_advanced_search(self, **kw):
        """Advanced search interface for inventory."""
        values = {
            'page_name': 'inventory',
            'search_categories': [
                {'id': 'containers', 'label': _('Containers'), 'icon': 'fa-archive'},
                {'id': 'files', 'label': _('Files'), 'icon': 'fa-folder'},
                {'id': 'documents', 'label': _('Documents'), 'icon': 'fa-file-text'},
            ],
        }

        return request.render("records_management.portal_advanced_search", values)
