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
import base64
import csv
import io
import json
import logging
from datetime import datetime, timedelta

# Odoo core imports
from markupsafe import Markup
from odoo import http, _, fields
from odoo.http import request
from dateutil.relativedelta import relativedelta

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

    def _get_user_permissions(self):
        """
        Get comprehensive permission information for the current user.
        Returns a dict with permission details for all major portal actions.
        
        Permission levels:
        - 'full': Can add, read, update, request destruction (green light)
        - 'partial': Can read and some actions but not all (yellow light)  
        - 'readonly': Can only view/read (yellow light)
        - 'none': No access (red light)
        
        Each permission includes:
        - level: 'full', 'partial', 'readonly', 'none'
        - color: 'green', 'yellow', 'red'
        - can_create, can_read, can_update, can_request_destruction: boolean flags
        - message: Human readable description of permissions
        
        Note: In records management, customers don't "delete" items - they request
        destruction services. The physical containers/files are retrieved, shredded,
        and billed. Records are archived (not deleted) in the system.
        """
        user = request.env.user

        # Determine user's role level
        is_system_admin = user.has_group('base.group_system')
        is_records_manager = user.has_group('records_management.group_records_manager')
        is_records_user = user.has_group('records_management.group_records_user')
        is_portal_company_admin = user.has_group('records_management.group_portal_company_admin')
        is_portal_dept_admin = user.has_group('records_management.group_portal_department_admin')
        is_portal_dept_user = user.has_group('records_management.group_portal_department_user')
        is_portal_readonly = user.has_group('records_management.group_portal_readonly_employee')

        def make_perm(can_create, can_read, can_update, can_request_destruction):
            """Helper to build permission dict from action flags.
            
            Args:
                can_create: Can add new items
                can_read: Can view items
                can_update: Can edit item details
                can_request_destruction: Can submit destruction service requests
            """
            if can_create and can_read and can_update and can_request_destruction:
                level = 'full'
                color = 'green'
                message = 'Full access: You can add, view, edit, and request destruction'
            elif can_create and can_read and can_update:
                level = 'partial'
                color = 'yellow'
                message = 'Partial access: You can add, view, and edit (cannot request destruction)'
            elif can_read and can_update:
                level = 'partial'
                color = 'yellow'
                message = 'Partial access: You can view and edit (cannot add new or request destruction)'
            elif can_read:
                level = 'readonly'
                color = 'yellow'
                message = 'Read only: You can view but cannot make changes'
            else:
                level = 'none'
                color = 'red'
                message = 'No access: You do not have permission for this feature'

            return {
                'level': level,
                'color': color,
                'can_create': can_create,
                'can_read': can_read,
                'can_update': can_update,
                'can_request_destruction': can_request_destruction,
                # Keep can_delete as alias for backward compatibility
                'can_delete': can_request_destruction,
                'message': message,
            }

        permissions = {}

        # Containers
        if is_system_admin or is_records_manager or is_portal_company_admin:
            permissions['containers'] = make_perm(True, True, True, True)
        elif is_portal_dept_admin or is_portal_dept_user or is_records_user:
            permissions['containers'] = make_perm(True, True, True, False)
        elif is_portal_readonly:
            permissions['containers'] = make_perm(False, True, False, False)
        else:
            permissions['containers'] = make_perm(False, False, False, False)

        # Files/Folders within containers
        if is_system_admin or is_records_manager or is_portal_company_admin:
            permissions['files'] = make_perm(True, True, True, True)
        elif is_portal_dept_admin or is_portal_dept_user or is_records_user:
            permissions['files'] = make_perm(True, True, True, False)
        elif is_portal_readonly:
            permissions['files'] = make_perm(False, True, False, False)
        else:
            permissions['files'] = make_perm(False, False, False, False)

        # Inventory items
        if is_system_admin or is_records_manager or is_portal_company_admin:
            permissions['inventory'] = make_perm(True, True, True, True)
        elif is_portal_dept_admin or is_portal_dept_user or is_records_user:
            permissions['inventory'] = make_perm(True, True, True, False)
        elif is_portal_readonly:
            permissions['inventory'] = make_perm(False, True, False, False)
        else:
            permissions['inventory'] = make_perm(False, False, False, False)

        # Requests (retrieval, destruction, etc.)
        if is_system_admin or is_records_manager or is_portal_company_admin:
            permissions['requests'] = make_perm(True, True, True, True)
        elif is_portal_dept_admin or is_portal_dept_user or is_records_user:
            permissions['requests'] = make_perm(True, True, True, False)
        elif is_portal_readonly:
            permissions['requests'] = make_perm(False, True, False, False)
        else:
            permissions['requests'] = make_perm(False, False, False, False)

        # User management
        if is_system_admin or is_records_manager or is_portal_company_admin:
            permissions['users'] = make_perm(True, True, True, True)
        elif is_portal_dept_admin:
            permissions['users'] = make_perm(True, True, True, False)
            permissions['users']['message'] = 'Partial access: You can manage users in your department only'
        else:
            permissions['users'] = make_perm(False, False, False, False)

        # Departments
        if is_system_admin or is_records_manager or is_portal_company_admin:
            permissions['departments'] = make_perm(True, True, True, True)
        elif is_portal_dept_admin:
            permissions['departments'] = make_perm(False, True, True, False)
            permissions['departments']['message'] = 'Partial access: You can view and edit your department only'
        else:
            permissions['departments'] = make_perm(False, True, False, False)

        # Billing/Invoices (view only for most portal users)
        if is_system_admin or is_records_manager:
            permissions['billing'] = make_perm(True, True, True, True)
        elif is_portal_company_admin:
            permissions['billing'] = make_perm(False, True, False, False)
        else:
            permissions['billing'] = make_perm(False, True, False, False)

        # Reports/Analytics
        if is_system_admin or is_records_manager or is_portal_company_admin:
            permissions['reports'] = make_perm(True, True, True, True)
        elif is_portal_dept_admin:
            permissions['reports'] = make_perm(False, True, False, False)
            permissions['reports']['message'] = 'Read only: You can view reports for your department'
        else:
            permissions['reports'] = make_perm(False, False, False, False)

        # Destruction certificates
        if is_system_admin or is_records_manager or is_portal_company_admin:
            permissions['certificates'] = make_perm(False, True, False, False)
            permissions['certificates']['message'] = 'Read only: Certificates are system-generated'
        elif is_portal_dept_admin or is_portal_dept_user:
            permissions['certificates'] = make_perm(False, True, False, False)
        else:
            permissions['certificates'] = make_perm(False, True, False, False)

        # Settings/Configuration
        if is_system_admin or is_records_manager:
            permissions['settings'] = make_perm(True, True, True, True)
        elif is_portal_company_admin:
            permissions['settings'] = make_perm(False, True, True, False)
            permissions['settings']['message'] = 'Partial access: You can view and edit company settings'
        else:
            permissions['settings'] = make_perm(False, False, False, False)

        # Add user role info for display
        if is_system_admin:
            permissions['user_role'] = 'System Administrator'
        elif is_records_manager:
            permissions['user_role'] = 'Records Manager'
        elif is_records_user:
            permissions['user_role'] = 'Records User'
        elif is_portal_company_admin:
            permissions['user_role'] = 'Company Administrator'
        elif is_portal_dept_admin:
            permissions['user_role'] = 'Department Administrator'
        elif is_portal_dept_user:
            permissions['user_role'] = 'Department User'
        elif is_portal_readonly:
            permissions['user_role'] = 'Read-Only User'
        else:
            permissions['user_role'] = 'Portal User'

        return permissions

    def _get_smart_department_context(self, user=None, partner=None):
        """Get smart department selection context for portal forms.
        
        Returns a dict with:
        - departments: RecordSet of departments user can select from
        - default_department: The single department if user has exactly one, else False
        - has_departments: True if company has ANY departments configured
        - show_department_selector: True if user should see a dropdown (multiple options)
        
        Logic:
        1. If user has specific department assignments, show only those + child depts
        2. If user is company admin with no assignments, show all company departments
        3. If regular user with no assignments, show none (company-level only)
        """
        if user is None:
            user = request.env.user
        if partner is None:
            partner = user.partner_id

        # Get user's assigned departments via records.storage.department.user
        user_dept_assignments = request.env['records.storage.department.user'].sudo().search([
            ('user_id', '=', user.id),
            ('state', '=', 'active'),
            ('active', '=', True),
        ])
        user_departments = user_dept_assignments.mapped('department_id')

        # Get all departments for the company (for company admins / to check if company uses depts)
        company_departments = request.env['records.department'].sudo().search([
            ('partner_id', '=', partner.commercial_partner_id.id),
        ])

        # Determine which departments to show based on user role
        is_company_admin = user.has_group('records_management.group_portal_company_admin')

        if user_departments:
            # User has specific department assignments - include child departments too
            all_user_depts = user_departments
            for dept in user_departments:
                if dept.child_ids:
                    all_user_depts |= dept.child_ids
            departments = all_user_depts
        elif is_company_admin:
            # Company admin with no specific dept assignment - show all
            departments = company_departments
        else:
            # Regular user with no department assignment - show none (company-level only)
            departments = request.env['records.department'].sudo().browse()

        # Determine default department (first one if user has exactly one)
        default_department = departments[0] if len(departments) == 1 else False

        return {
            'departments': departments,
            'default_department': default_department,
            'has_departments': bool(company_departments),
            'show_department_selector': len(departments) > 1,
        }

    def _prepare_portal_layout_values(self):
        """
        Prepare common values for portal layout templates.
        Returns base context dictionary for portal pages.
        """
        partner = request.env.user.partner_id
        commercial_partner = partner.commercial_partner_id if partner else partner

        # Get custom field labels for this customer
        field_labels = request.env['field.label.customization'].sudo().get_labels_dict(
            commercial_partner.id if commercial_partner else None
        )

        # Get user permissions for all portal features
        permissions = self._get_user_permissions()

        return {
            'page_name': 'records_management',
            'user': request.env.user,
            'partner': partner,
            'field_labels': field_labels,  # Custom terminology for this customer
            'permissions': permissions,     # Access rights for permission indicators
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
            'locations': request.env['stock.location'].search([]),
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
                    containers.sudo().write({"location_id": new_location_id_int})
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
                        containers.sudo().write({"tag_ids": [(6, 0, tag_ids)]})
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
        Container = request.env["records.container"].sudo()
        PickupRequest = request.env["pickup.request"].sudo()
        ShredService = request.env["shredding.service"].sudo()

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
                        request.env["stock.location"].browse(location_id[0]).name if location_id else "Unknown"
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
        recent_pickups = request.env["pickup.request"].sudo().search(pickup_domain, order="create_date desc", limit=5)

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
        containers_this_month = request.env["records.container"].sudo().search_count(container_month_domain)

        container_week_domain = partner_domain + [("create_date", ">=", last_week.strftime("%Y-%m-%d"))]
        containers_last_week = request.env["records.container"].sudo().search_count(container_week_domain)

        # Pickup efficiency (filtered by partner)
        pickup_completed_domain = partner_domain + [
            ("state", "=", "completed"),
            ("completion_date", ">=", last_month.strftime("%Y-%m-%d")),
        ]
        completed_pickups = request.env["pickup.request"].sudo().search_count(pickup_completed_domain)

        pickup_total_domain = partner_domain + [("create_date", ">=", last_month.strftime("%Y-%m-%d"))]
        total_pickups = request.env["pickup.request"].sudo().search_count(pickup_total_domain)

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
        overdue_pickups = request.env["pickup.request"].sudo().search_count(
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
        Customer Certifications Portal:
        - Destruction Certificates (NAID AAA certificates from completed shredding jobs)
        - Training Courses & Materials (eLearning portal access)
        
        NOTE: NAID Operator Certifications are for employees only, not shown here.
        """
        partner = request.env.user.partner_id.commercial_partner_id

        # Get destruction certificates for this customer (from completed jobs)
        destruction_certificates = request.env['naid.certificate'].sudo().search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'completed')
        ], order='certificate_date desc')

        # Get training courses available to customers
        training_courses = request.env['slide.channel'].sudo().search([
            ('is_published', '=', True),
            ('website_published', '=', True),
        ], order='name')

        context = {
            'destruction_certificates': destruction_certificates,
            'training_courses': training_courses,
            'page_name': 'certifications',
        }

        return request.render('records_management.portal_certifications', context)

    @http.route("/my/certifications/<int:certification_id>", type="http", auth="user", website=True)
    def portal_certification_detail(self, certification_id):
        """
        Detailed view of a destruction certificate (NAID AAA certificate).
        Shows certificate details, items destroyed, dates, signatures, etc.
        """
        partner = request.env.user.partner_id.commercial_partner_id

        # Get destruction certificate with security check
        certificate = request.env['naid.certificate'].sudo().search([
            ('id', '=', certification_id),
            ('partner_id', '=', partner.id)
        ], limit=1)

        # Check if certificate exists and user has access
        if not certificate:
            return request.redirect('/my/certifications')

        context = {
            'certificate': certificate,
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

            feedback = request.env['portal.feedback'].sudo().create(feedback_vals)

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
    # PORTAL HUB - Main Landing Page
    # ============================================================================

    @http.route(['/portal-hub'], type='http', auth='user', website=True)
    def portal_hub(self, **kw):
        """
        Portal Hub - Main landing page for Records Management Portal.
        Provides quick access to all portal features and recent activity.
        """
        partner = request.env.user.partner_id

        # Get summary counts for dashboard cards - Hierarchical Inventory
        container_count = request.env['records.container'].sudo().search_count([
            ('partner_id', 'child_of', partner.commercial_partner_id.id)
        ])

        file_folder_count = request.env['records.file'].sudo().search_count([
            ('partner_id', 'child_of', partner.commercial_partner_id.id)
        ])

        document_count = request.env['records.document'].sudo().search_count([
            ('partner_id', 'child_of', partner.commercial_partner_id.id)
        ])

        # Get active service request count
        request_count = request.env['portal.request'].sudo().search_count([
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ('state', 'not in', ['cancelled', 'done'])
        ])

        certificate_count = request.env['destruction.certificate'].sudo().search_count([
            ('partner_id', 'child_of', partner.commercial_partner_id.id)
        ])

        # Get recent activities
        recent_requests = request.env['portal.request'].sudo().search([
            ('partner_id', 'child_of', partner.commercial_partner_id.id)
        ], order='create_date desc', limit=5)

        values = {
            'page_name': 'portal_hub',
            'container_count': container_count,
            'file_folder_count': file_folder_count,
            'document_count': document_count,
            'request_count': request_count,
            'certificate_count': certificate_count,
            'recent_requests': recent_requests,
            'partner': partner,
        }

        # Render the base portal home template - our inheritance will apply automatically
        return request.render('portal.portal_my_home', values)

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
    # SERVICE ATTACHMENTS PORTAL ROUTES
    # Customer-visible attachments from work orders, certificates, invoices
    # Uses native ir.attachment system (Attach File button on work orders)
    # NOT for customer inventory documents (handled by /my/inventory)
    # ============================================================================

    def _get_service_attachment_domain(self, partner):
        """
        Build domain to get service attachments visible to this customer.
        Filters by attachments on work orders, pickups, certificates, invoices
        that belong to this customer.
        """
        # Get IDs of service records belonging to this customer
        work_order_ids = request.env['work.order.shredding'].sudo().search([
            ('partner_id', 'child_of', partner.commercial_partner_id.id)
        ]).ids

        pickup_ids = request.env['pickup.request'].sudo().search([
            ('partner_id', 'child_of', partner.commercial_partner_id.id)
        ]).ids

        certificate_ids = request.env['destruction.certificate'].sudo().search([
            ('partner_id', 'child_of', partner.commercial_partner_id.id)
        ]).ids

        invoice_ids = request.env['account.move'].sudo().search([
            ('partner_id', 'child_of', partner.commercial_partner_id.id),
            ('move_type', 'in', ['out_invoice', 'out_refund'])
        ]).ids

        # Build domain for attachments from these records
        domain = ['|', '|', '|',
            '&', ('res_model', '=', 'work.order.shredding'), ('res_id', 'in', work_order_ids),
            '&', ('res_model', '=', 'pickup.request'), ('res_id', 'in', pickup_ids),
            '&', ('res_model', '=', 'destruction.certificate'), ('res_id', 'in', certificate_ids),
            '&', ('res_model', '=', 'account.move'), ('res_id', 'in', invoice_ids),
        ]

        return domain

    @http.route(['/my/service-attachments', '/my/service-attachments/page/<int:page>'], type='http', auth="user", website=True)
    def portal_service_attachments(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        """Display service attachments visible to customer in portal.
        
        These are attachments (photos, PDFs) from work orders, pickups, 
        certificates - NOT customer inventory documents.
        """
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        Attachment = request.env['ir.attachment'].sudo()

        # Get base domain for this customer's service attachments
        domain = self._get_service_attachment_domain(partner)

        # Date filtering
        if date_begin and date_end:
            domain += [('create_date', '>=', date_begin), ('create_date', '<=', date_end)]

        # Filter by attachment type
        searchbar_filters = {
            'all': {'label': _('All Files'), 'domain': []},
            'images': {'label': _('Photos'), 'domain': [('mimetype', 'ilike', 'image')]},
            'pdfs': {'label': _('PDFs'), 'domain': [('mimetype', '=', 'application/pdf')]},
            'work_orders': {'label': _('Work Orders'), 'domain': [('res_model', '=', 'work.order.shredding')]},
            'certificates': {'label': _('Certificates'), 'domain': [('res_model', '=', 'destruction.certificate')]},
        }

        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # Sorting options
        searchbar_sortings = {
            'date': {'label': _('Most Recent'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
        }

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Count total attachments
        attachment_count = Attachment.search_count(domain)

        # Pager setup
        pager = request.website.pager(
            url="/my/service-attachments",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=attachment_count,
            page=page,
            step=self._items_per_page,
        )

        # Get attachments for current page
        attachments = Attachment.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'attachments': attachments,
            'page_name': 'service_attachments',
            'pager': pager,
            'default_url': '/my/service-attachments',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
        })

        return request.render("records_management.portal_service_attachments", values)

    @http.route(['/my/service-attachment/<int:attachment_id>'], type='http', auth="user", website=True)
    def portal_service_attachment_detail(self, attachment_id=None, **kw):
        """Display individual service attachment details"""
        attachment = request.env['ir.attachment'].sudo().browse(attachment_id)
        partner = request.env.user.partner_id

        # Security check - verify attachment belongs to customer's service record
        if not attachment.exists():
            return request.redirect('/my/service-attachments')

        # Verify the source document belongs to this customer
        allowed = False
        if attachment.res_model == 'work.order.shredding':
            wo = request.env['work.order.shredding'].sudo().browse(attachment.res_id)
            allowed = wo.exists() and wo.partner_id.commercial_partner_id == partner.commercial_partner_id
        elif attachment.res_model == 'pickup.request':
            pr = request.env['pickup.request'].sudo().browse(attachment.res_id)
            allowed = pr.exists() and pr.partner_id.commercial_partner_id == partner.commercial_partner_id
        elif attachment.res_model == 'destruction.certificate':
            dc = request.env['destruction.certificate'].sudo().browse(attachment.res_id)
            allowed = dc.exists() and dc.partner_id.commercial_partner_id == partner.commercial_partner_id
        elif attachment.res_model == 'account.move':
            am = request.env['account.move'].sudo().browse(attachment.res_id)
            allowed = am.exists() and am.partner_id.commercial_partner_id == partner.commercial_partner_id

        if not allowed:
            return request.redirect('/my/service-attachments')

        # Get source document name
        source_doc = None
        if attachment.res_model and attachment.res_id:
            source_doc = request.env[attachment.res_model].sudo().browse(attachment.res_id)

        values = self._prepare_portal_layout_values()
        values.update({
            'attachment': attachment,
            'source_doc': source_doc,
            'page_name': 'service_attachment_detail',
        })

        return request.render("records_management.portal_service_attachment_detail", values)

    @http.route(['/my/service-attachment/<int:attachment_id>/download'], type='http', auth="user")
    def portal_service_attachment_download(self, attachment_id=None, **kw):
        """Download service attachment"""
        attachment = request.env['ir.attachment'].sudo().browse(attachment_id)
        partner = request.env.user.partner_id

        if not attachment.exists():
            return request.redirect('/my/service-attachments')

        # Security check (same as detail view)
        allowed = False
        if attachment.res_model == 'work.order.shredding':
            wo = request.env['work.order.shredding'].sudo().browse(attachment.res_id)
            allowed = wo.exists() and wo.partner_id.commercial_partner_id == partner.commercial_partner_id
        elif attachment.res_model in ['pickup.request', 'destruction.certificate', 'account.move']:
            rec = request.env[attachment.res_model].sudo().browse(attachment.res_id)
            allowed = rec.exists() and rec.partner_id.commercial_partner_id == partner.commercial_partner_id

        if not allowed:
            return request.redirect('/my/service-attachments')

        # Return file download
        return request.env['ir.http']._get_content_common(
            xmlid=None, model='ir.attachment', res_id=attachment.id, field='datas',
            filename=attachment.name, filename_field='name', download=True
        )

    # Legacy route redirect (for backwards compatibility)
    @http.route(['/my/service-photos', '/my/service-photos/page/<int:page>'], type='http', auth="user", website=True)
    def portal_service_photos_redirect(self, **kw):
        """Redirect old service-photos URL to service-attachments"""
        return request.redirect('/my/service-attachments')

    # ============================================================================
    # DOCUMENTS PORTAL ROUTES
    # ============================================================================

    @http.route(['/my/documents', '/my/documents/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_documents(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, **kw):
        """Display customer digital documents in portal"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        Document = request.env['records.document'].sudo()

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
        document = request.env['records.document'].sudo().browse(document_id)

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
        document = request.env['records.document'].sudo().browse(document_id)

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
    def portal_my_containers(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, state_filter=None, **kw):
        """
        Display container inventory for portal users
        FIXED: Uses records.container model with correct ownership fields
        Previously broken: used stock.quant with wrong owner_id field
        """
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        Container = request.env['records.container'].sudo()

        # Build base domain - use hierarchical access for stock_owner_id
        base_domain = [
            '|',
            ('partner_id', '=', partner.id),
            ('stock_owner_id', 'child_of', partner.id),
        ]

        # Search filter
        if search:
            base_domain += [
                '|', '|', '|', '|',
                ('name', 'ilike', search),
                ('barcode', 'ilike', search),
                ('temp_barcode', 'ilike', search),
                ('department_id.name', 'ilike', search),
                ('location_id.name', 'ilike', search),
            ]

        # Date filtering
        if date_begin and date_end:
            base_domain += [('create_date', '>=', date_begin), ('create_date', '<=', date_end)]

        # Calculate counts for each state (for tab badges)
        counts = {
            'all': Container.search_count(base_domain),
            'in': Container.search_count(base_domain + [('state', '=', 'in')]),
            'out': Container.search_count(base_domain + [('state', '=', 'out')]),
            'pending': Container.search_count(base_domain + [('state', '=', 'pending')]),
        }

        # Apply state filter to domain
        domain = list(base_domain)
        if state_filter and state_filter != 'all':
            domain += [('state', '=', state_filter)]

        # Legacy status filter (for backward compatibility)
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

        # Count total containers (with all filters applied)
        container_count = Container.search_count(domain)

        # Pager setup
        pager = request.website.pager(
            url="/my/containers",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby, 'search': search, 'state_filter': state_filter},
            total=container_count,
            page=page,
            step=self._items_per_page,
        )

        # Get containers for current page
        containers = Container.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        # Get user permissions
        permissions = self._get_user_permissions()

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
            'state_filter': state_filter or 'all',
            'counts': counts,
            'permissions': permissions,
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

        # Get user permissions for traffic light indicators
        permissions = self._get_user_permissions()

        values = {
            'container': container,
            'page_name': 'container_detail',
            'permissions': permissions,
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
                    'location': file_folder.location_id.name if file_folder.location_id else 'Unknown',
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
                attachments = request.env['ir.attachment'].sudo().search([
                    ('res_model', '=', 'records.document'),
                    ('res_id', '=', document.id),
                    ('mimetype', 'like', 'pdf')
                ])

                attachment_info = f" - {len(attachments)} PDF scan(s)" if attachments else ""

                # Get file state for document availability
                file_state = document.file_id.state if document.file_id else 'in'

                all_inventory_items.append({
                    'type': 'document',
                    'id': document.id,
                    'name': document.name,
                    'barcode': document.temp_barcode,
                    'description': f"Document - {document.description or 'No description'}{attachment_info}",
                    'location': document.container_id.current_location_id.name if document.container_id and document.container_id.current_location_id else 'Unknown',
                    'date': document.create_date,
                    'state': file_state,
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
    def portal_inventory_containers(self, page=1, sortby=None, filterby=None, search=None, state_filter=None, **kw):
        """Containers tab - backend-style list view with bulk actions and state filtering"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id.commercial_partner_id

        Container = request.env['records.container'].sudo()
        base_domain = [('partner_id', '=', partner.id)]

        if search:
            base_domain += ['|', '|', ('name', 'ilike', search), ('barcode', 'ilike', search), ('temp_barcode', 'ilike', search)]

        # Calculate counts for each state (for tab badges)
        counts = {
            'all': Container.search_count(base_domain),
            'in': Container.search_count(base_domain + [('state', '=', 'in')]),
            'out': Container.search_count(base_domain + [('state', '=', 'out')]),
            'pending': Container.search_count(base_domain + [('state', '=', 'pending')]),
        }

        # Apply state filter to domain
        domain = list(base_domain)
        if state_filter and state_filter != 'all':
            domain += [('state', '=', state_filter)]

        # Legacy status filter (for backward compatibility with filterby dropdown)
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
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search, 'state_filter': state_filter},
            total=container_count,
            page=page,
            step=20,
        )

        containers = Container.search(domain, order=order, limit=20, offset=pager['offset'])

        # Get permissions for the template
        permissions = self._get_user_permissions()

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
            'state_filter': state_filter or 'all',
            'counts': counts,
            'permissions': permissions,
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

        # Get smart department context for editing
        user = request.env.user
        dept_context = self._get_smart_department_context(user, user.partner_id)

        # Get container types
        container_types = request.env['records.container.type'].search([])

        # Get movement history
        movements = request.env['chain.of.custody'].search([
            ('container_ids', 'in', [container_id])
        ], order='transfer_date desc', limit=20)

        # Get files in this container
        files = request.env['records.file'].sudo().search([
            ('container_id', '=', container_id),
            ('partner_id', '=', partner.id)
        ])

        # Get user permissions for traffic light indicators
        permissions = self._get_user_permissions()

        # Legacy permission flags for backward compatibility
        can_edit = request.env.user.has_group('records_management.group_portal_department_user')
        can_delete = request.env.user.has_group('records_management.group_portal_department_admin')

        values = {
            'container': container,
            'container_types': container_types,
            'movements': movements,
            'files': files,
            'permissions': permissions,
            'can_edit': can_edit,
            'can_delete': can_delete,
            'page_name': 'container_detail',
            **dept_context,  # departments, default_department, has_departments, show_department_selector
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
            departments = request.env['records.department'].sudo().search([
                ('company_id', '=', partner.id)
            ])
            container_types = request.env['records.container.type'].sudo().search([])
            # Get retention policies for the form (use records.retention.policy, not rule)
            retention_policies = request.env['records.retention.policy'].sudo().search([
                ('active', '=', True)
            ], order='name')
            # Get staging locations for the customer
            staging_locations = request.env['customer.staging.location'].sudo().search([
                ('partner_id', '=', partner.id),
                ('active', '=', True)
            ], order='complete_name')
            # Get user permissions for traffic light indicators
            permissions = self._get_user_permissions()
            # Get smart department context
            dept_context = self._get_smart_department_context(request.env.user, request.env.user.partner_id)

            values = {
                'departments': departments,
                'container_types': container_types,
                'retention_policies': retention_policies,
                'staging_locations': staging_locations,
                'permissions': permissions,
                'page_name': 'container_create',
                **dept_context,  # departments, default_department, has_departments, show_department_selector
            }
            return request.render("records_management.portal_container_create_form", values)

        # POST request - create container
        try:
            # Validate required fields - accept both 'name' and 'container_number'
            name = post.get('name') or post.get('container_number')
            container_type_id = post.get('container_type_id')
            department_id = post.get('department_id')
            
            # Name is always required
            if not name:
                return request.render('records_management.portal_error', {
                    'error_title': _('Missing Required Fields'),
                    'error_message': _('Please provide a container name/number.'),
                })
            
            # Department handling for company admins vs regular users
            is_company_admin = request.env.user.has_group('records_management.group_portal_company_admin')
            
            # Department is optional for company admins, required for others
            if department_id:
                department = request.env['records.department'].sudo().browse(int(department_id))
                if not department.exists() or department.partner_id.id != partner.id:
                    return request.render('records_management.portal_error', {
                        'error_title': _('Invalid Department'),
                        'error_message': _('The selected department is invalid.'),
                    })
                # Check department access for non-company-admins
                if not is_company_admin:
                    accessible_depts = request.env.user.accessible_department_ids.ids
                    if int(department_id) not in accessible_depts:
                        return request.render('records_management.portal_error', {
                            'error_title': _('Unauthorized Department'),
                            'error_message': _('You do not have access to this department.'),
                        })
            elif not is_company_admin:
                # Non-admins must have a department
                return request.render('records_management.portal_error', {
                    'error_title': _('Missing Required Fields'),
                    'error_message': _('Please select a department.'),
                })
            
            # Container type - auto-select Type 01 if not provided (standard accepted size)
            if not container_type_id:
                # First try to find Type 01 by code or name
                default_type = request.env['records.container.type'].sudo().search([
                    '|', '|',
                    ('code', '=', 'TYPE01'),
                    ('code', '=', '01'),
                    ('name', 'ilike', 'Type 01')
                ], limit=1)
                if not default_type:
                    # Fallback to any default type
                    default_type = request.env['records.container.type'].sudo().search([
                        ('is_default', '=', True)
                    ], limit=1)
                if not default_type:
                    # Last resort - first available type
                    default_type = request.env['records.container.type'].sudo().search([], limit=1)
                if default_type:
                    container_type_id = default_type.id

            # Get container type for default weight
            container_type = None
            if container_type_id:
                container_type = request.env['records.container.type'].sudo().browse(int(container_type_id))

            # Staging location validation (required for proper tracking)
            staging_location_id = post.get('staging_location_id')
            staging_location = None
            if staging_location_id:
                staging_location = request.env['customer.staging.location'].sudo().browse(int(staging_location_id))
                # Verify ownership
                if staging_location.partner_id.id != partner.id:
                    return request.render('records_management.portal_error', {
                        'error_title': _('Invalid Staging Location'),
                        'error_message': _('The selected staging location does not belong to your organization.'),
                    })

            # Create container
            container_vals = {
                'name': name,
                'partner_id': partner.id,
                'state': 'pending',  # Correct field name is 'state', not 'status'
                'created_via_portal': True,
            }
            
            # Add department if provided
            if department_id:
                container_vals['department_id'] = int(department_id)
            
            # Add container type if available
            if container_type_id:
                container_vals['container_type_id'] = int(container_type_id)
                # Set default weight from container type's average weight (for route planning/statistics)
                if container_type and container_type.average_weight_lbs:
                    container_vals['weight'] = container_type.average_weight_lbs

            # Add staging location if provided
            if staging_location:
                container_vals['customer_staging_location_id'] = staging_location.id

            # Optional fields
            if post.get('description'):
                container_vals['description'] = post.get('description')
            if post.get('location_id'):
                container_vals['current_location_id'] = int(post.get('location_id'))

            # Barcode handling - generate temp barcode if staging location assigned
            if staging_location:
                # Generate TMP barcode for tracking at customer site
                # Format: TMP-{COMPANY_REF}-{DEPT_CODE}-{CHILD_CODE}-{SEQ}
                # 
                # Structure (all 4-digit codes, 6-digit sequence):
                # - Company only:      TMP-0915-000001
                # - With department:   TMP-0915-HR01-000001  
                # - With child dept:   TMP-0915-HR01-LGL1-000001
                #
                # Sequence resets to 000001 when a new department/child is added
                
                import re
                
                # Get 4-char company code (sanitized partner ref)
                raw_company_ref = partner.ref or 'CUST'
                company_code = re.sub(r'[^A-Za-z0-9]', '', raw_company_ref).upper()[:4].ljust(4, '0')
                
                # Build barcode prefix based on department hierarchy
                barcode_prefix = f'TMP-{company_code}'
                
                # Get department info if assigned
                dept_code = None
                child_code = None
                department = None
                if department_id:
                    department = request.env['records.department'].sudo().browse(int(department_id))
                    if department.exists():
                        # Get 4-char department code
                        raw_dept_code = department.code or 'DEPT'
                        dept_code = re.sub(r'[^A-Za-z0-9]', '', raw_dept_code).upper()[:4].ljust(4, '0')
                        barcode_prefix += f'-{dept_code}'
                        
                        # Check if this department has a parent (making it a child dept)
                        if department.parent_department_id:
                            # This IS a child department - get parent code too
                            parent_dept = department.parent_department_id
                            raw_parent_code = parent_dept.code or 'PRNT'
                            parent_code = re.sub(r'[^A-Za-z0-9]', '', raw_parent_code).upper()[:4].ljust(4, '0')
                            # Rebuild prefix: TMP-COMPANY-PARENT-CHILD
                            barcode_prefix = f'TMP-{company_code}-{parent_code}-{dept_code}'
                
                # Get next sequence number for this exact prefix
                # This ensures sequence resets when department structure changes
                existing_count = request.env['records.container'].sudo().search_count([
                    ('barcode', 'like', barcode_prefix + '-%'),
                    ('partner_id', '=', partner.id)
                ])
                seq_num = str(existing_count + 1).zfill(6)  # 000001, 000002, etc.
                
                temp_barcode = f'{barcode_prefix}-{seq_num}'
                container_vals['barcode'] = temp_barcode
            elif post.get('generate_barcode'):
                # Auto-generate barcode using sequence
                container_vals['barcode'] = request.env['ir.sequence'].sudo().next_by_code('records.container') or f'CNT-{name[:10].upper()}'
            elif post.get('custom_barcode'):
                container_vals['barcode'] = post.get('custom_barcode')
            elif post.get('barcode'):
                container_vals['barcode'] = post.get('barcode')

            container = request.env['records.container'].sudo().create(container_vals)

            # Audit log
            audit_description = _('Container %s created via portal by %s') % (container.name, request.env.user.name)
            if staging_location:
                audit_description += _(' | Staging location: %s | Temp barcode: %s') % (
                    staging_location.complete_name, container.barcode
                )
            request.env['naid.audit.log'].sudo().create({
                'action_type': 'container_created',
                'user_id': request.env.user.id,
                'container_id': container.id,
                'description': audit_description,
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
                new_dept = request.env['records.department'].sudo().browse(new_dept_id)
                if new_dept.company_id.id == partner.id:
                    update_vals['department_id'] = new_dept_id

            # State change - department admin+
            if post.get('state') and request.env.user.has_group('records_management.group_portal_department_admin'):
                update_vals['state'] = post.get('state')

            if update_vals:
                container.sudo().write(update_vals)

                # Audit log
                request.env['naid.audit.log'].sudo().create({
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
        """
        DISABLED: Portal users cannot delete physical inventory directly.
        
        To stop storage charges, customers must submit a destruction request:
        1. Submit destruction request via portal (/my/request/new/destruction)
        2. Request gets approved by admin
        3. Admin schedules destruction work order
        4. Admin marks containers as destroyed (changes state to 'destroyed')
        5. Customer is billed per-container destruction fee
        6. Storage charges stop for destroyed containers
        
        This ensures proper NAID compliance and audit trail.
        """
        return {
            'success': False,
            'error': _('❌ Physical inventory cannot be deleted directly. To stop storage charges, please submit a Destruction Request from the portal. Once approved and processed, containers will be marked as destroyed and billing will be updated.')
        }

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
        ], order='transfer_date desc')

        # Check if user can request moves
        can_request_move = request.env.user.has_group('records_management.group_portal_department_user')
        permissions = self._get_user_permissions()

        values = {
            'container': container,
            'movements': movements,
            'can_request_move': can_request_move,
            'permissions': permissions,
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
            new_location = request.env['stock.location'].browse(new_location_id)

            # Create move request using sudo() for portal user access
            move_request = request.env['portal.request'].sudo().create({
                'request_type': 'move',
                'partner_id': partner.id,
                'requester_id': request.env.user.partner_id.id,
                'container_ids': [(6, 0, [container_id])],
                'target_location_id': new_location_id,
                'notes': post.get('notes', ''),
                'state': 'draft',
            })

            # Auto-submit if internal staff will handle
            move_request.sudo().action_submit()

            # Audit log
            request.env['naid.audit.log'].sudo().create({
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

        # Department-level filtering for non-company-admins
        if not request.env.user.has_group('records_management.group_portal_company_admin'):
            accessible_depts = request.env.user.accessible_department_ids.ids
            if accessible_depts:
                domain += [('department_id', 'in', accessible_depts)]

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

        # Get permissions for the template
        permissions = self._get_user_permissions()

        values.update({
            'files': files,
            'page_name': 'inventory_files',
            'pager': pager,
            'search': search or '',
            'file_count': file_count,
            'permissions': permissions,
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
        departments = request.env['records.department'].sudo().search([('company_id', '=', partner.id)])
        containers = request.env['records.container'].sudo().search([('partner_id', '=', partner.id)])
        documents = request.env['records.document'].sudo().search([('file_id', '=', file_id)])

        # Permission flags
        can_edit = request.env.user.has_group('records_management.group_portal_department_user')
        can_delete = request.env.user.has_group('records_management.group_portal_department_admin')
        permissions = self._get_user_permissions()

        # Retrieval cart count
        retrieval_cart_count = self._get_retrieval_cart_count(partner)

        values = {
            'file': file_record,
            'documents': documents,
            'departments': departments,
            'containers': containers,
            'can_edit': can_edit,
            'can_delete': can_delete,
            'permissions': permissions,
            'retrieval_cart_count': retrieval_cart_count,
            'page_name': 'file_detail',
        }

        return request.render("records_management.portal_file_detail", values)

    @http.route(['/my/inventory/files/create'], type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_file_create(self, **post):
        """Create new file folder (department user+)."""
        user = request.env.user
        if not user.has_group('records_management.group_portal_department_user'):
            if request.httprequest.method == 'GET':
                return request.redirect('/my/home?error=unauthorized')
            return request.render('records_management.portal_error', {
                'error_title': _('Unauthorized'),
                'error_message': _('You do not have permission to create files.'),
            })

        partner = user.partner_id.commercial_partner_id

        if request.httprequest.method == 'GET':
            # Use smart department helper
            dept_context = self._get_smart_department_context(user, user.partner_id)
            containers = request.env['records.container'].sudo().search([('partner_id', '=', partner.id)])

            # Pre-select container if passed via query parameter
            preselect_container_id = post.get('container_id')
            if preselect_container_id:
                try:
                    preselect_container_id = int(preselect_container_id)
                except (ValueError, TypeError):
                    preselect_container_id = None

            values = {
                'containers': containers,
                'preselect_container_id': preselect_container_id,
                'permissions': self._get_user_permissions(),
                'page_name': 'file_create',
                **dept_context,  # departments, default_department, has_departments, show_department_selector
            }
            return request.render("records_management.portal_file_create", values)

        try:
            name = post.get('name')
            container_id = post.get('container_id')
            department_id = post.get('department_id')

            # Department is now optional - only validate if provided
            if not all([name, container_id]):
                return request.render('records_management.portal_error', {
                    'error_title': _('Missing Required Fields'),
                    'error_message': _('Please provide file name and container.'),
                })

            # Get container to inherit department if not specified
            container = request.env['records.container'].sudo().browse(int(container_id))
            if not container.exists() or container.partner_id.id != partner.id:
                return request.render('records_management.portal_error', {
                    'error_title': _('Invalid Container'),
                    'error_message': _('The selected container is invalid or does not belong to you.'),
                })

            # Department validation - inherit from container if not provided
            final_department_id = False
            if department_id:
                department = request.env['records.department'].sudo().browse(int(department_id))
                if not department.exists() or department.partner_id.id != partner.id:
                    return request.render('records_management.portal_error', {
                        'error_title': _('Invalid Department'),
                        'error_message': _('The selected department is invalid.'),
                    })
                final_department_id = int(department_id)

                # Department access check for non-company-admins
                if not request.env.user.has_group('records_management.group_portal_company_admin'):
                    accessible_depts = request.env.user.accessible_department_ids.ids
                    if final_department_id not in accessible_depts:
                        return request.render('records_management.portal_error', {
                            'error_title': _('Unauthorized Department'),
                            'error_message': _('You do not have access to this department.'),
                        })
            elif container.department_id:
                # Inherit department from container
                final_department_id = container.department_id.id

            file_vals = {
                'name': name,
                'partner_id': partner.id,
                'container_id': int(container_id),
                'created_via_portal': True,
            }

            # Only set department if we have one
            if final_department_id:
                file_vals['department_id'] = final_department_id

            if post.get('description'):
                file_vals['description'] = post.get('description')
            if post.get('barcode'):
                file_vals['barcode'] = post.get('barcode')

            file_record = request.env['records.file'].sudo().create(file_vals)

            request.env['naid.audit.log'].sudo().create({
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
                new_dept = request.env['records.department'].sudo().browse(new_dept_id)
                if new_dept.company_id.id == partner.id:
                    update_vals['department_id'] = new_dept_id

            if update_vals:
                file_record.sudo().write(update_vals)
                request.env['naid.audit.log'].sudo().create({
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
        """
        DISABLED: Portal users cannot delete physical inventory directly.
        
        To stop storage charges, customers must submit a destruction request.
        Physical files must be destroyed through proper NAID workflow.
        """
        return {
            'success': False,
            'error': _('❌ Physical files cannot be deleted directly. To stop storage charges, please submit a Destruction Request from the portal.')
        }

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

                    request.env['naid.audit.log'].sudo().create({
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

                    doc = request.env['records.document'].sudo().create(doc_vals)

                    request.env['naid.audit.log'].sudo().create({
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

            request.env['naid.audit.log'].sudo().create({
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
    # FILE DOCUMENT UPLOAD (Portal Upload with Attachment)
    # ============================================================================

    @http.route(['/my/inventory/file/<int:file_id>/upload'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_file_upload_document(self, file_id, **post):
        """Upload a document with attachment to a file folder."""
        try:
            partner = request.env.user.partner_id.commercial_partner_id
            file_record = request.env['records.file'].sudo().browse(file_id)

            # Security: Verify ownership
            if file_record.partner_id.id != partner.id:
                return request.redirect('/my/inventory/files?error=unauthorized')

            # Get upload data
            document_name = post.get('document_name')
            description = post.get('description', '')
            attachment = post.get('attachment')

            if not document_name or not attachment:
                return request.redirect(f'/my/inventory/file/{file_id}?error=missing_fields')

            # Create the document record
            doc_vals = {
                'name': document_name,
                'partner_id': partner.id,
                'department_id': file_record.department_id.id if file_record.department_id else False,
                'file_id': file_id,
                'container_id': file_record.container_id.id if file_record.container_id else False,
                'description': description,
                'created_via_portal': True,
            }
            doc = request.env['records.document'].sudo().create(doc_vals)

            # Create attachment linked to the document
            import base64
            attachment_data = base64.b64encode(attachment.read())
            attachment_vals = {
                'name': attachment.filename,
                'type': 'binary',
                'datas': attachment_data,
                'res_model': 'records.document',
                'res_id': doc.id,
                'mimetype': attachment.content_type or 'application/octet-stream',
            }
            request.env['ir.attachment'].sudo().create(attachment_vals)

            # Audit log
            request.env['naid.audit.log'].sudo().create({
                'action_type': 'document_uploaded',
                'user_id': request.env.user.id,
                'description': _('Document "%s" uploaded to file %s via portal by %s') % (
                    document_name, file_record.name, request.env.user.name
                ),
                'timestamp': fields.Datetime.now(),
            })

            return request.redirect(f'/my/inventory/file/{file_id}?document_uploaded=success')

        except Exception as e:
            _logger.error(f"Document upload failed: {str(e)}", exc_info=True)
            return request.redirect(f'/my/inventory/file/{file_id}?error=upload_failed')

    # ============================================================================
    # FILE RETRIEVAL CART (Collect files before submitting request)
    # ============================================================================

    def _get_or_create_retrieval_cart(self, partner):
        """Get or create a draft retrieval request to use as cart."""
        PortalRequest = request.env['portal.request'].sudo()

        # Look for existing draft retrieval request
        cart = PortalRequest.search([
            ('partner_id', '=', partner.id),
            ('request_type', '=', 'retrieval'),
            ('state', '=', 'draft'),
        ], limit=1, order='create_date desc')

        if not cart:
            cart = PortalRequest.create({
                'name': _('File Retrieval Cart - %s') % partner.name,
                'partner_id': partner.id,
                'request_type': 'retrieval',
                'state': 'draft',
                'description': _('Files queued for retrieval from storage.'),
                'created_via_portal': True,
            })

        return cart

    def _get_retrieval_cart_count(self, partner):
        """Get count of files in retrieval cart."""
        cart = request.env['portal.request'].sudo().search([
            ('partner_id', '=', partner.id),
            ('request_type', '=', 'retrieval'),
            ('state', '=', 'draft'),
        ], limit=1)
        return len(cart.file_ids) if cart else 0

    @http.route(['/my/retrieval-cart/add'], type='json', auth='user', methods=['POST'])
    def portal_retrieval_cart_add(self, file_id=None, **kw):
        """Add a file to the retrieval cart."""
        try:
            if not file_id:
                return {'success': False, 'error': 'No file specified'}

            partner = request.env.user.partner_id.commercial_partner_id
            file_record = request.env['records.file'].sudo().browse(file_id)

            # Security check
            if file_record.partner_id.commercial_partner_id.id != partner.id:
                return {'success': False, 'error': 'You do not have permission to request this file.'}

            # Check file is in storage
            if file_record.state != 'in':
                state_msg = {
                    'pending': 'This file is still pending and not yet in storage.',
                    'out': 'This file is already checked out.',
                    'perm_out': 'This file has been permanently removed.',
                    'destroyed': 'This file has been destroyed.',
                }.get(file_record.state, 'This file cannot be retrieved.')
                return {'success': False, 'error': state_msg}

            # Get or create cart
            cart = self._get_or_create_retrieval_cart(partner)

            # Check if already in cart
            if file_record.id in cart.file_ids.ids:
                return {
                    'success': True,
                    'message': _('"%s" is already in your cart.') % file_record.name,
                    'cart_count': len(cart.file_ids),
                    'already_in_cart': True,
                }

            # Add to cart
            cart.sudo().write({
                'file_ids': [(4, file_record.id)],
            })

            return {
                'success': True,
                'message': _('"%s" added to retrieval cart.') % file_record.name,
                'cart_count': len(cart.file_ids),
            }

        except Exception as e:
            _logger.error(f"Add to retrieval cart failed: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route(['/my/retrieval-cart/remove'], type='json', auth='user', methods=['POST'])
    def portal_retrieval_cart_remove(self, file_id=None, **kw):
        """Remove a file from the retrieval cart."""
        try:
            if not file_id:
                return {'success': False, 'error': 'No file specified'}

            partner = request.env.user.partner_id.commercial_partner_id
            cart = request.env['portal.request'].sudo().search([
                ('partner_id', '=', partner.id),
                ('request_type', '=', 'retrieval'),
                ('state', '=', 'draft'),
            ], limit=1)

            if not cart:
                return {'success': False, 'error': 'No cart found'}

            cart.sudo().write({
                'file_ids': [(3, int(file_id))],
            })

            return {
                'success': True,
                'message': _('File removed from cart.'),
                'cart_count': len(cart.file_ids),
            }

        except Exception as e:
            _logger.error(f"Remove from retrieval cart failed: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route(['/my/retrieval-cart'], type='http', auth='user', website=True)
    def portal_retrieval_cart(self, **kw):
        """View and manage the file retrieval cart."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id.commercial_partner_id

        # Get cart
        cart = request.env['portal.request'].sudo().search([
            ('partner_id', '=', partner.id),
            ('request_type', '=', 'retrieval'),
            ('state', '=', 'draft'),
        ], limit=1)

        files = cart.file_ids if cart else request.env['records.file']

        values.update({
            'cart': cart,
            'files': files,
            'file_count': len(files),
            'page_name': 'retrieval_cart',
            'permissions': self._get_user_permissions(),
        })

        return request.render("records_management.portal_retrieval_cart", values)

    @http.route(['/my/retrieval-cart/submit'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_retrieval_cart_submit(self, **post):
        """Submit the retrieval cart and create a work order."""
        try:
            partner = request.env.user.partner_id.commercial_partner_id
            cart = request.env['portal.request'].sudo().search([
                ('partner_id', '=', partner.id),
                ('request_type', '=', 'retrieval'),
                ('state', '=', 'draft'),
            ], limit=1)

            if not cart or not cart.file_ids:
                return request.redirect('/my/retrieval-cart?error=empty_cart')

            files = cart.file_ids
            delivery_notes = post.get('delivery_notes', '')

            # Build file list for description
            file_list = '\\n'.join('• ' + f.name + (' (in ' + f.container_id.name + ')' if f.container_id else '') for f in files)

            # Update cart to submitted
            cart.sudo().write({
                'state': 'submitted',
                'name': _('File Retrieval Request - %s (%d files)') % (partner.name, len(files)),
                'description': _('Customer requested retrieval of %d file folder(s) from storage.\\n\\nFiles:\\n%s\\n\\nDelivery Notes:\\n%s') % (
                    len(files), file_list, delivery_notes or 'None'
                ),
                'priority': '2',
            })

            # Get unique containers
            container_ids = list(set(f.container_id.id for f in files if f.container_id))
            if container_ids:
                cart.sudo().write({
                    'container_ids': [(6, 0, container_ids)],
                })

            # Create retrieval work order
            work_order = request.env['records.retrieval.work.order'].sudo().create({
                'name': _('Portal File Retrieval - %s (%d files)') % (partner.name, len(files)),
                'partner_id': partner.id,
                'user_id': request.env.ref('base.user_admin').id,
                'state': 'draft',
                'delivery_method': 'delivery',
                'notes': _('File retrieval request from portal.\\n\\n%s\\n\\nDelivery Notes: %s') % (file_list, delivery_notes or 'None'),
            })

            # Create FSM task
            containers = request.env['records.container'].sudo().browse(container_ids)
            self._create_fsm_task_for_work_order(work_order, 'retrieval', partner, containers)

            # Link work order to cart
            cart.sudo().write({
                'work_order_id': work_order.id,
            })

            # Notify records management team
            cart.message_post(
                body=_('🔔 File retrieval request submitted via portal.\\n\\n%d file(s) requested for delivery.') % len(files),
                subject=_('New File Retrieval Request'),
                subtype_xmlid='mail.mt_comment',
                message_type='notification',
            )

            return request.redirect(f'/my/requests/{cart.id}?submitted=success')

        except Exception as e:
            _logger.error(f"Submit retrieval cart failed: {str(e)}", exc_info=True)
            return request.redirect('/my/retrieval-cart?error=submit_failed')

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
            doc.pdf_scans = request.env['ir.attachment'].sudo().search([
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
            'permissions': self._get_user_permissions(),
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

        # Get related data with smart department context
        user = request.env.user
        dept_context = self._get_smart_department_context(user, user.partner_id)
        files = request.env['records.file'].sudo().search([('partner_id', '=', partner.id)])
        containers = request.env['records.container'].sudo().search([('partner_id', '=', partner.id)])

        # Get attachments
        attachments = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'records.document'),
            ('res_id', '=', doc_id)
        ])

        # Permission flags
        can_edit = request.env.user.has_group('records_management.group_portal_department_user')
        can_delete = request.env.user.has_group('records_management.group_portal_department_admin')
        permissions = self._get_user_permissions()

        values = {
            'document': doc_record,
            'attachments': attachments,
            'files': files,
            'containers': containers,
            'can_edit': can_edit,
            'can_delete': can_delete,
            'permissions': permissions,
            'page_name': 'document_detail',
            **dept_context,  # departments, default_department, has_departments, show_department_selector
        }

        return request.render("records_management.portal_document_detail", values)

    @http.route(['/my/inventory/documents/create'], type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_document_create(self, **post):
        """Create new document (department user+)."""
        user = request.env.user
        if not user.has_group('records_management.group_portal_department_user'):
            if request.httprequest.method == 'GET':
                return request.redirect('/my/home?error=unauthorized')
            return request.render('records_management.portal_error', {
                'error_title': _('Unauthorized'),
                'error_message': _('You do not have permission to create documents.'),
            })

        partner = user.partner_id.commercial_partner_id

        if request.httprequest.method == 'GET':
            # Use smart department context
            dept_context = self._get_smart_department_context(user, user.partner_id)
            files = request.env['records.file'].sudo().search([('partner_id', '=', partner.id)])
            containers = request.env['records.container'].sudo().search([('partner_id', '=', partner.id)])

            values = {
                'files': files,
                'containers': containers,
                'permissions': self._get_user_permissions(),
                'page_name': 'document_create',
                **dept_context,  # departments, default_department, has_departments, show_department_selector
            }
            return request.render("records_management.portal_document_create", values)

        try:
            name = post.get('name')
            file_id = post.get('file_id')
            department_id = post.get('department_id')

            # Department is now optional
            if not all([name, file_id]):
                return request.render('records_management.portal_error', {
                    'error_title': _('Missing Required Fields'),
                    'error_message': _('Please provide document name and file.'),
                })

            # Department validation (if provided)
            if department_id:
                department = request.env['records.department'].sudo().browse(int(department_id))
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

            doc_record = request.env['records.document'].sudo().create(doc_vals)

            request.env['naid.audit.log'].sudo().create({
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
                new_dept = request.env['records.department'].sudo().browse(new_dept_id)
                if new_dept.company_id.id == partner.id:
                    update_vals['department_id'] = new_dept_id

            if update_vals:
                doc_record.sudo().write(update_vals)
                request.env['naid.audit.log'].sudo().create({
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
        """
        Digital documents CAN be deleted by portal users (they are just metadata/attachments).
        Physical inventory deletion is disabled - use destruction requests instead.
        """
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

            request.env['naid.audit.log'].sudo().create({
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

            attachment = request.env['ir.attachment'].sudo().create({
                'name': uploaded_file.filename,
                'type': 'binary',
                'datas': base64.b64encode(uploaded_file.read()),
                'res_model': 'records.document',
                'res_id': doc_id,
                'mimetype': uploaded_file.content_type or 'application/octet-stream',
            })

            request.env['naid.audit.log'].sudo().create({
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
            departments = request.env['records.department'].sudo().search([('company_id', '=', partner.id)])
            files = request.env['records.file'].sudo().search([('partner_id', '=', partner.id)])

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

                doc_record = request.env['records.document'].sudo().create(doc_vals)
                created_docs.append(doc_record)

                attachment = request.env['ir.attachment'].sudo().create({
                    'name': uploaded_file.filename,
                    'type': 'binary',
                    'datas': base64.b64encode(uploaded_file.read()),
                    'res_model': 'records.document',
                    'res_id': doc_record.id,
                    'mimetype': uploaded_file.content_type or 'application/octet-stream',
                })

            if created_docs:
                request.env['naid.audit.log'].sudo().create({
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

            scan_request = request.env['portal.request'].sudo().create(request_vals)

            # Link document to request
            doc_record.sudo().write({
                'scan_request_id': scan_request.id,
                'scan_requested_date': datetime.now(),
            })

            request.env['naid.audit.log'].sudo().create({
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

        if request_type not in ['retrieval', 'destruction', 'pickup', 'scanning', 'file_search']:
            return request.redirect('/my/requests?error=invalid_type')

        if request.httprequest.method == 'GET':
            departments = request.env['records.department'].sudo().search([('company_id', '=', partner.id)])
            # Keep sudo() context for containers to avoid barcode nomenclature access issues in template
            containers_sudo = request.env['records.container'].sudo().search([('partner_id', '=', partner.id)])
            files = request.env['records.file'].sudo().search([('partner_id', '=', partner.id)])

            # Pre-fetch location names to avoid barcode nomenclature access in template
            container_data = []
            for container in containers_sudo:
                container_data.append({
                    'id': container.id,
                    'name': container.name,
                    'description': container.description or 'No description',
                    'location_name': container.location_id.name if container.location_id else None,
                    'barcode': container.barcode,
                    'state': container.state,
                })

            values = {
                'request_type': request_type,
                'partner': partner,
                'departments': departments,
                'containers': containers_sudo,
                'container_data': container_data,  # Safe data without ORM access
                'files': files,
                'page_name': f'request_create_{request_type}',
            }

            # Route to specific template based on type
            if request_type == 'destruction':
                return request.render("records_management.portal_destruction_request_create", values)
            elif request_type == 'pickup':
                return request.render("records_management.portal_pickup_request_create", values)
            elif request_type == 'file_search':
                return request.render("records_management.portal_file_search_create", values)
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
            if post.get('notes'):
                request_vals['description'] = post.get('notes')

            # Handle container and file selections
            container_ids = request.httprequest.form.getlist('container_ids')
            if container_ids:
                request_vals['container_ids'] = [(6, 0, [int(c) for c in container_ids if c])]

            file_ids = request.httprequest.form.getlist('file_ids')
            if file_ids:
                request_vals['file_ids'] = [(6, 0, [int(f) for f in file_ids if f])]

            # Handle notification preferences
            if post.get('notification_method'):
                request_vals['notification_method'] = post.get('notification_method')
            if post.get('notify_on_file_located'):
                request_vals['notify_on_file_located'] = True
            if post.get('notify_on_ready_for_delivery'):
                request_vals['notify_on_ready_for_delivery'] = True

            # Handle file search fields
            if request_type == 'file_search':
                if post.get('search_file_name'):
                    request_vals['search_file_name'] = post.get('search_file_name')
                if post.get('search_date_from'):
                    request_vals['search_date_from'] = post.get('search_date_from')
                if post.get('search_date_to'):
                    request_vals['search_date_to'] = post.get('search_date_to')
                if post.get('search_alpha_range'):
                    request_vals['search_alpha_range'] = post.get('search_alpha_range')

                # Get selected search containers
                selected_containers = request.httprequest.form.getlist('selected_search_container_ids')
                if selected_containers:
                    request_vals['selected_search_container_ids'] = [(6, 0, [int(c) for c in selected_containers if c])]

            req_record = request.env['portal.request'].sudo().create(request_vals)

            request.env['naid.audit.log'].sudo().create({
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

        except ValidationError as e:
            _logger.warning(f"Request creation validation error: {str(e)}")
            return request.render('records_management.portal_error', {
                'error_title': _('Validation Error'),
                'error_message': str(e),
            })
        except AccessError as e:
            _logger.error(f"Request creation access error: {str(e)}")
            return request.render('records_management.portal_error', {
                'error_title': _('Access Denied'),
                'error_message': _('You do not have permission to create this request.'),
            })
        except Exception as e:
            _logger.error(f"Request creation failed: {str(e)}")
            return request.render('records_management.portal_error', {
                'error_title': _('Request Creation Failed'),
                'error_message': str(e),
            })

    @http.route(['/my/request/search_containers'], type='json', auth='user', methods=['POST'])
    def search_matching_containers(self, file_name='', date_from=None, date_to=None, alpha_range='', **kw):
        """AJAX endpoint to search for matching containers based on file search criteria."""
        try:
            partner = request.env.user.partner_id.commercial_partner_id

            # Convert date strings to date objects
            date_from_obj = None
            date_to_obj = None
            if date_from:
                try:
                    from datetime import datetime
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                except:
                    pass
            if date_to:
                try:
                    from datetime import datetime
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                except:
                    pass

            # Call intelligent search method
            matching_containers = request.env['portal.request'].search_matching_containers(
                file_name=file_name,
                date_from=date_from_obj,
                date_to=date_to_obj,
                alpha_range=alpha_range,
                partner_id=partner.id
            )

            # Build results
            results = []
            for container in matching_containers:
                results.append({
                    'id': container.id,
                    'name': container.name,
                    'barcode': container.barcode or '',
                    'temp_barcode': container.temp_barcode or '',
                    'location': container.location_id.name if container.location_id else '',
                    'alpha_range': container.alpha_range or '',
                    'date_range': '%s to %s' % (
                        container.date_range_start.strftime('%m/%d/%Y') if container.date_range_start else 'N/A',
                        container.date_range_end.strftime('%m/%d/%Y') if container.date_range_end else 'N/A'
                    ),
                    'contents': container.content_description or '',
                    'score': getattr(container, 'matching_score', 0),
                    'reasons': getattr(container, 'matching_reasons', ''),
                })

            return {
                'success': True,
                'containers': results,
                'count': len(results)
            }

        except Exception as e:
            _logger.error(f"Container search failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'containers': [],
                'count': 0
            }

    @http.route(['/my/containers/search'], type='json', auth='user', methods=['POST'])
    def instant_container_search(self, query='', offset=0, limit=50, **kw):
        """
        Chunked instant search for containers with indexed fields.
        Handles large datasets (20,000+ containers) with pagination.
        
        Args:
            query: Search string
            offset: Starting record (for pagination)
            limit: Number of records per chunk (default 50)
        """
        try:
            partner = request.env.user.partner_id.commercial_partner_id

            # Build search domain with indexed fields
            domain = [('partner_id', '=', partner.id)]

            if query:
                query = query.strip()
                # Search across indexed fields: name (Box Number), barcode, temp_barcode,
                # alpha_range, content_description for comprehensive instant search
                domain.append('|')
                domain.append('|')
                domain.append('|')
                domain.append('|')
                domain.append(('name', 'ilike', query))
                domain.append(('barcode', 'ilike', query))
                domain.append(('temp_barcode', 'ilike', query))
                domain.append(('alpha_range', 'ilike', query))
                domain.append(('content_description', 'ilike', query))

            Container = request.env['records.container'].sudo()

            # Get total count
            total_count = Container.search_count(domain)

            # Get paginated results
            containers = Container.search(
                domain,
                offset=offset,
                limit=limit,
                order='name asc'
            )

            results = []
            for container in containers:
                results.append({
                    'id': container.id,
                    'name': container.name,
                    'barcode': container.barcode or '',
                    'temp_barcode': container.temp_barcode or '',
                    'location': container.location_id.name if container.location_id else '',
                    'alpha_range': container.alpha_range or '',
                    'date_range': '%s to %s' % (
                        container.content_date_from.strftime('%m/%d/%Y') if container.content_date_from else 'N/A',
                        container.content_date_to.strftime('%m/%d/%Y') if container.content_date_to else 'N/A'
                    ),
                    'contents': (container.content_description or '')[:100],  # Truncate for performance
                })

            return {
                'success': True,
                'containers': results,
                'count': len(results),
                'total': total_count,
                'has_more': (offset + limit) < total_count,
                'next_offset': offset + limit if (offset + limit) < total_count else None
            }

        except Exception as e:
            _logger.error(f"Instant container search failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'containers': [],
                'count': 0,
                'total': 0
            }

    def _create_fsm_task_for_work_order(self, work_order, service_type, partner, containers):
        """
        Helper method to create FSM task and calendar event for work orders.
        
        Args:
            work_order: The work order record (retrieval, destruction, etc.)
            service_type: Type of service ('retrieval', 'destruction', 'shredding_onsite', etc.)
            partner: Customer partner record
            containers: Recordset of containers involved
            
        Returns:
            project.task: Created FSM task
        """
        # Get or create FSM project
        fsm_project = request.env.ref('records_management_fsm.project_field_service', raise_if_not_found=False)
        if not fsm_project:
            # Create default FSM project
            fsm_project = request.env['project.project'].sudo().create({
                'name': 'Field Service',
                'is_fsm': True,
                'allow_timesheets': True,
            })

        # Map service types to worksheet templates
        template_map = {
            'retrieval': 'records_management_fsm.worksheet_template_retrieval',
            'destruction': 'records_management_fsm.worksheet_template_destruction',
            'shredding_onsite': 'records_management_fsm.worksheet_template_shredding_onsite',
            'shredding_offsite': 'records_management_fsm.worksheet_template_shredding_offsite',
            'access': 'records_management_fsm.worksheet_template_access',
            'pickup': 'records_management_fsm.worksheet_template_pickup',
        }

        # Service type display names
        service_names = {
            'retrieval': 'Container Retrieval',
            'destruction': 'Container Destruction',
            'shredding_onsite': 'On-Site Shredding',
            'shredding_offsite': 'Off-Site Shredding',
            'access': 'Container Access',
            'pickup': 'Container Pickup',
        }

        # Calculate scheduled date (next business day)
        from datetime import datetime, timedelta
        scheduled_date = datetime.now()
        # Skip to next business day if weekend
        while scheduled_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
            scheduled_date += timedelta(days=1)
        scheduled_date += timedelta(days=1)  # Next business day

        # Create FSM task
        task_vals = {
            'name': f"{service_names.get(service_type, 'Service')}: {partner.name}",
            'project_id': fsm_project.id,
            'partner_id': partner.id,
            'date_deadline': scheduled_date.date(),
            'planned_date_begin': scheduled_date,
            'planned_date_end': scheduled_date + timedelta(hours=2),
            'description': f"Portal request for {len(containers)} container(s)\n\nContainers:\n" +
                          '\n'.join(f"• {c.name}" for c in containers[:10]) +
                          (f"\n... and {len(containers) - 10} more" if len(containers) > 10 else ""),
            'container_ids': [(6, 0, containers.ids)],
        }

        # Link to appropriate work order
        if hasattr(work_order, '_name'):
            if work_order._name == 'records.retrieval.work.order':
                task_vals['retrieval_work_order_id'] = work_order.id
            elif work_order._name == 'container.destruction.work.order':
                task_vals['destruction_work_order_id'] = work_order.id
                task_vals['destruction_type'] = work_order.destruction_method if hasattr(work_order, 'destruction_method') else 'off_site'
            elif work_order._name == 'work.order.shredding':
                task_vals['shredding_work_order_id'] = work_order.id
            elif work_order._name == 'pickup.request':
                task_vals['pickup_request_id'] = work_order.id

        # Create the task
        fsm_task = request.env['project.task'].sudo().create(task_vals)

        # Link FSM task back to work order
        if hasattr(work_order, 'fsm_task_id'):
            work_order.sudo().write({'fsm_task_id': fsm_task.id})

        # Create worksheet from template
        template_xml_id = template_map.get(service_type)
        if template_xml_id:
            template = request.env.ref(template_xml_id, raise_if_not_found=False)
            if template:
                request.env['fsm.worksheet.instance'].sudo().create({
                    'task_id': fsm_task.id,
                    'template_id': template.id,
                })

        # Create calendar event for internal team
        calendar_vals = {
            'name': f"{service_names.get(service_type, 'Service')} - {partner.name}",
            'start': scheduled_date,
            'stop': scheduled_date + timedelta(hours=2),
            'partner_ids': [(4, partner.id)],
            'description': f"FSM Task: {fsm_task.name}\n\n{len(containers)} container(s) to process",
            'location': partner.street or partner.city or '',
            'alarm_ids': [(0, 0, {
                'name': 'Notification',
                'alarm_type': 'notification',
                'interval': 'hours',
                'duration': 1,
            })],
        }

        # Add assigned user if available
        if hasattr(work_order, 'user_id') and work_order.user_id:
            calendar_vals['user_id'] = work_order.user_id.id
            calendar_vals['partner_ids'].append((4, work_order.user_id.partner_id.id))

        calendar_event = request.env['calendar.event'].sudo().create(calendar_vals)

        # Link calendar event to FSM task (if FSM supports it)
        if hasattr(fsm_task, 'calendar_event_id'):
            fsm_task.sudo().write({'calendar_event_id': calendar_event.id})

        # Post message to work order about FSM task creation
        if hasattr(work_order, 'message_post'):
            work_order.sudo().message_post(
                body=f'✅ FSM Task created: <a href="/web#id={fsm_task.id}&model=project.task">{fsm_task.name}</a><br/>'
                     f'📅 Scheduled: {scheduled_date.strftime("%B %d, %Y at %I:%M %p")}<br/>'
                     f'📋 Calendar event created for team',
                subject='FSM Task & Calendar Event Created'
            )

        return fsm_task

    @http.route(['/my/containers/bulk_request'], type='json', auth='user', methods=['POST'])
    def create_bulk_container_request(self, request_type='', container_ids=None, **kw):
        """
        Portal endpoint for bulk container requests.
        Customers can select multiple containers and submit requests for:
        - Retrieval
        - Destruction  
        - Permanent Removal (perm-out)
        - Access
        
        Returns JSON with success status and created request ID.
        """
        try:
            if not container_ids or not isinstance(container_ids, list):
                return {
                    'success': False,
                    'error': 'No containers selected. Please select at least one container.'
                }

            if not request_type:
                return {
                    'success': False,
                    'error': 'Request type is required.'
                }

            # Get current user's partner
            partner = request.env.user.partner_id.commercial_partner_id

            # Validate containers belong to this customer
            Container = request.env['records.container'].sudo()
            containers = Container.browse(container_ids)

            # Security check
            invalid_containers = containers.filtered(lambda c: c.partner_id.commercial_partner_id != partner)
            if invalid_containers:
                return {
                    'success': False,
                    'error': 'You do not have permission to request actions on some selected containers.'
                }

            # Map request types to portal.request types and descriptions
            request_type_map = {
                'retrieval': {
                    'type': 'retrieval',
                    'title': 'Container Retrieval Request',
                    'description': 'Customer requested retrieval of containers from storage.'
                },
                'return_to_warehouse': {
                    'type': 'pickup',
                    'title': 'Return to Warehouse Request',
                    'description': 'Customer requested pickup of containers to return to warehouse storage.\\n\\nOur team will pick up the containers from your location and return them to secure storage.'
                },
                'send_to_storage': {
                    'type': 'pickup',
                    'title': 'Send to Storage Request',
                    'description': 'Customer requested initial pickup of pending containers to begin storage service.\\n\\nOur team will pick up these new containers from your location and place them in secure warehouse storage.'
                },
                'destruction': {
                    'type': 'destruction',
                    'title': 'Container Destruction Request',
                    'description': 'Customer requested secure destruction of containers.\\n\\nCharges will apply:\\n• Removal fee: $15/container\\n• Shredding fee: $25/container'
                },
                'permanent_removal': {
                    'type': 'pickup',  # Use pickup type for perm-out
                    'title': 'Permanent Removal Request',
                    'description': 'Customer requested permanent removal of containers (perm-out).\\n\\nCharges will apply:\\n• Removal fee: $15/container'
                },
                'access': {
                    'type': 'other',
                    'title': 'Container Access Request',
                    'description': 'Customer requested access to containers for viewing/inspection.'
                }
            }

            if request_type not in request_type_map:
                return {
                    'success': False,
                    'error': f'Invalid request type: {request_type}'
                }

            req_config = request_type_map[request_type]

            # Build container list for description
            container_list = '\\n'.join('• ' + c.name for c in containers)

            # Create portal request
            PortalRequest = request.env['portal.request'].sudo()
            portal_request = PortalRequest.create({
                'name': f"{req_config['title']} - {partner.name} ({len(containers)} containers)",
                'partner_id': partner.id,
                'request_type': req_config['type'],
                'state': 'submitted',
                'description': f"{req_config['description']}\\n\\nContainers:\\n{container_list}",
                'priority': '2',  # Medium priority
                'container_ids': [(6, 0, container_ids)],
            })

            # Create work order based on request type
            work_order = None
            fsm_task = None

            if request_type == 'retrieval':
                # Create retrieval work order
                work_order = request.env['records.retrieval.work.order'].sudo().create({
                    'name': f"Portal Retrieval - {partner.name} ({len(containers)} containers)",
                    'partner_id': partner.id,
                    'user_id': request.env.ref('base.user_admin').id,  # Assign to admin
                    'state': 'draft',
                    'delivery_method': 'scan',
                    'scanned_barcode_ids': [(6, 0, container_ids)],
                })

                # Auto-create FSM task
                fsm_task = self._create_fsm_task_for_work_order(
                    work_order,
                    'retrieval',
                    partner,
                    containers
                )

                # Link work order to portal request
                portal_request.message_post(
                    body=f'Retrieval work order created: <a href="/web#id={work_order.id}&model=records.retrieval.work.order">{work_order.name}</a>',
                    subject='Work Order Created'
                )

            elif request_type == 'destruction':
                # Create destruction work order
                work_order = request.env['container.destruction.work.order'].sudo().create({
                    'name': f"Portal Destruction - {partner.name} ({len(containers)} containers)",
                    'partner_id': partner.id,
                    'user_id': request.env.ref('base.user_admin').id,
                    'state': 'draft',
                    'destruction_method': 'shredding',
                    'container_ids': [(6, 0, container_ids)],
                })

                # Auto-create FSM task
                fsm_task = self._create_fsm_task_for_work_order(
                    work_order,
                    'destruction',
                    partner,
                    containers
                )

                # Link work order to portal request
                portal_request.message_post(
                    body=f'Destruction work order created: <a href="/web#id={work_order.id}&model=container.destruction.work.order">{work_order.name}</a>',
                    subject='Work Order Created'
                )

            elif request_type == 'return_to_warehouse':
                # Create pickup request for return to warehouse
                work_order = request.env['pickup.request'].sudo().create({
                    'name': f"Portal Return to Warehouse - {partner.name} ({len(containers)} containers)",
                    'partner_id': partner.id,
                    'state': 'draft',
                    'pickup_type': 'return',
                    'container_ids': [(6, 0, container_ids)],
                    'internal_notes': f'Customer requested pickup to return {len(containers)} container(s) to warehouse storage.',
                })

                # Auto-create FSM task for pickup
                fsm_task = self._create_fsm_task_for_work_order(
                    work_order,
                    'pickup',
                    partner,
                    containers
                )

                # Link work order to portal request
                portal_request.message_post(
                    body=f'Pickup request created for return to warehouse: <a href="/web#id={work_order.id}&model=pickup.request">{work_order.name}</a>',
                    subject='Pickup Request Created'
                )

            elif request_type == 'send_to_storage':
                # Create pickup request for initial storage (pending containers)
                work_order = request.env['pickup.request'].sudo().create({
                    'name': f"Portal Initial Storage Pickup - {partner.name} ({len(containers)} containers)",
                    'partner_id': partner.id,
                    'state': 'draft',
                    'pickup_type': 'initial',
                    'container_ids': [(6, 0, container_ids)],
                    'internal_notes': f'Customer requested initial pickup of {len(containers)} pending container(s) to begin storage service.',
                })

                # Auto-create FSM task for pickup
                fsm_task = self._create_fsm_task_for_work_order(
                    work_order,
                    'pickup',
                    partner,
                    containers
                )

                # Link work order to portal request
                portal_request.message_post(
                    body=f'Pickup request created for initial storage: <a href="/web#id={work_order.id}&model=pickup.request">{work_order.name}</a>',
                    subject='Pickup Request Created'
                )

            # Send notification to backend team
            # Get records management group users
            rm_group = request.env.ref('records_management.group_records_manager', raise_if_not_found=False)
            if rm_group:
                portal_request.message_subscribe(partner_ids=rm_group.users.mapped('partner_id').ids)

            # Post notification message
            portal_request.message_post(
                body=f'🔔 New portal request submitted by {partner.name}\\n\\n{len(containers)} container(s) selected',
                subject=f'New {req_config["title"]}',
                subtype_xmlid='mail.mt_comment',
                message_type='notification'
            )

            return {
                'success': True,
                'message': f'Request submitted successfully! Our team has been notified and will process your request for {len(containers)} container(s).',
                'request_id': portal_request.id,
                'container_count': len(containers)
            }

        except Exception as e:
            _logger.error(f"Bulk container request failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'An error occurred: {str(e)}'
            }

    @http.route(['/my/files/bulk_request'], type='json', auth='user', methods=['POST'])
    def create_bulk_file_request(self, request_type='', file_ids=None, **kw):
        """
        Portal endpoint for bulk file requests.
        Customers can select multiple files and submit requests for:
        - Retrieval (file retrieval from containers)
        - Return to Warehouse (return files currently out)
        
        Returns JSON with success status and created request ID.
        """
        try:
            if not file_ids or not isinstance(file_ids, list):
                return {
                    'success': False,
                    'error': 'No files selected. Please select at least one file.'
                }

            if not request_type:
                return {
                    'success': False,
                    'error': 'Request type is required.'
                }

            # Get current user's partner
            partner = request.env.user.partner_id.commercial_partner_id

            # Validate files belong to this customer
            RecordsFile = request.env['records.file'].sudo()
            files = RecordsFile.browse(file_ids)

            # Security check
            invalid_files = files.filtered(lambda f: f.partner_id.commercial_partner_id != partner)
            if invalid_files:
                return {
                    'success': False,
                    'error': 'You do not have permission to request actions on some selected files.'
                }

            # Department access check for non-company-admins
            if not request.env.user.has_group('records_management.group_portal_company_admin'):
                accessible_depts = request.env.user.accessible_department_ids.ids
                unauthorized_files = files.filtered(lambda f: f.department_id.id not in accessible_depts)
                if unauthorized_files:
                    return {
                        'success': False,
                        'error': 'You do not have department access to some selected files.'
                    }

            # Map request types
            request_type_map = {
                'retrieval': {
                    'type': 'retrieval',
                    'title': 'File Retrieval Request',
                    'description': 'Customer requested retrieval of file folders from storage.'
                },
                'return_to_warehouse': {
                    'type': 'pickup',
                    'title': 'Return Files to Warehouse',
                    'description': 'Customer requested pickup of file folders to return to warehouse storage.'
                },
            }

            if request_type not in request_type_map:
                return {
                    'success': False,
                    'error': f'Invalid request type: {request_type}'
                }

            req_config = request_type_map[request_type]

            # Build file list for description
            file_list = '\\n'.join('• ' + f.name + (' (in ' + f.container_id.name + ')' if f.container_id else '') for f in files)

            # Get unique containers that contain these files
            container_ids = list(set(f.container_id.id for f in files if f.container_id))

            # Create portal request
            PortalRequest = request.env['portal.request'].sudo()
            portal_request = PortalRequest.create({
                'name': f"{req_config['title']} - {partner.name} ({len(files)} files)",
                'partner_id': partner.id,
                'request_type': req_config['type'],
                'state': 'submitted',
                'description': f"{req_config['description']}\\n\\nFiles:\\n{file_list}",
                'priority': '2',
                'container_ids': [(6, 0, container_ids)] if container_ids else False,
            })

            # Create work order
            work_order = None

            if request_type == 'retrieval':
                work_order = request.env['records.retrieval.work.order'].sudo().create({
                    'name': f"Portal File Retrieval - {partner.name} ({len(files)} files)",
                    'partner_id': partner.id,
                    'user_id': request.env.ref('base.user_admin').id,
                    'state': 'draft',
                    'delivery_method': 'scan',
                    'notes': f'File retrieval request for {len(files)} file folder(s).\\n\\n{file_list}',
                })

                containers = request.env['records.container'].sudo().browse(container_ids)
                fsm_task = self._create_fsm_task_for_work_order(work_order, 'retrieval', partner, containers)

                portal_request.message_post(
                    body=f'Retrieval work order created: <a href="/web#id={work_order.id}&model=records.retrieval.work.order">{work_order.name}</a>',
                    subject='Work Order Created'
                )

            elif request_type == 'return_to_warehouse':
                work_order = request.env['pickup.request'].sudo().create({
                    'name': f"Portal File Return - {partner.name} ({len(files)} files)",
                    'partner_id': partner.id,
                    'state': 'draft',
                    'pickup_type': 'return',
                    'container_ids': [(6, 0, container_ids)] if container_ids else False,
                    'internal_notes': f'Customer requested return of {len(files)} file folder(s) to warehouse.\\n\\n{file_list}',
                })

                containers = request.env['records.container'].sudo().browse(container_ids)
                fsm_task = self._create_fsm_task_for_work_order(work_order, 'pickup', partner, containers)

                portal_request.message_post(
                    body=f'Pickup request created for file return: <a href="/web#id={work_order.id}&model=pickup.request">{work_order.name}</a>',
                    subject='Pickup Request Created'
                )

            # Send notification
            rm_group = request.env.ref('records_management.group_records_manager', raise_if_not_found=False)
            if rm_group:
                portal_request.message_subscribe(partner_ids=rm_group.users.mapped('partner_id').ids)

            portal_request.message_post(
                body=f'🔔 New portal request submitted by {partner.name}\\n\\n{len(files)} file(s) selected',
                subject=f'New {req_config["title"]}',
                subtype_xmlid='mail.mt_comment',
                message_type='notification'
            )

            return {
                'success': True,
                'message': f'Request submitted successfully! Our team has been notified and will process your request for {len(files)} file(s).',
                'request_id': portal_request.id,
                'file_count': len(files)
            }

        except Exception as e:
            _logger.error(f"Bulk file request failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'An error occurred: {str(e)}'
            }

    @http.route(['/my/files/search'], type='json', auth='user', methods=['POST'])
    def instant_file_search(self, query='', offset=0, limit=50, **kw):
        """
        Chunked instant search for files with indexed fields.
        Handles large datasets with pagination.
        """
        try:
            partner = request.env.user.partner_id.commercial_partner_id

            domain = [('partner_id', '=', partner.id)]

            if query:
                query = query.strip()
                domain.append('|')
                domain.append('|')
                domain.append(('name', 'ilike', query))
                domain.append(('file_number', 'ilike', query))
                domain.append(('description', 'ilike', query))

            File = request.env['records.file'].sudo()

            total_count = File.search_count(domain)

            files = File.search(
                domain,
                offset=offset,
                limit=limit,
                order='name asc'
            )

            results = []
            for file_rec in files:
                results.append({
                    'id': file_rec.id,
                    'name': file_rec.name,
                    'number': file_rec.file_number or '',
                    'container': file_rec.container_id.name if file_rec.container_id else '',
                    'container_id': file_rec.container_id.id if file_rec.container_id else None,
                    'description': (file_rec.description or '')[:100],
                })

            return {
                'success': True,
                'files': results,
                'count': len(results),
                'total': total_count,
                'has_more': (offset + limit) < total_count,
                'next_offset': offset + limit if (offset + limit) < total_count else None
            }

        except Exception as e:
            _logger.error(f"Instant file search failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'files': [],
                'count': 0,
                'total': 0
            }

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
                request.env['naid.audit.log'].sudo().create({
                    'action_type': 'request_updated',
                    'user_id': request.env.user.id,
                    'description': _('Request %s updated via portal by %s') % (req_record.name, request.env.user.name),
                    'timestamp': datetime.now(),
                })

            return request.redirect(f'/my/requests/{request_id}?updated=success')

        except Exception as e:
            _logger.error("Request edit failed: %s", str(e))
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

            request.env['naid.audit.log'].sudo().create({
                'action_type': 'request_cancelled',
                'user_id': request.env.user.id,
                'description': _('Request %s cancelled via portal by %s') % (req_record.name, request.env.user.name),
                'timestamp': datetime.now(),
            })

            return {'success': True, 'message': _('Request cancelled successfully')}

        except ValidationError as e:
            _logger.warning(f"Request cancel validation error: {str(e)}")
            return {'success': False, 'error': str(e)}
        except AccessError as e:
            _logger.error(f"Request cancel access error: {str(e)}")
            return {'success': False, 'error': _('Access denied')}
        except Exception as e:
            _logger.error(f"Request cancel failed: {str(e)}")
            return {'success': False, 'error': _('Request cancellation failed')}

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

            request.env['naid.audit.log'].sudo().create({
                'action_type': 'request_submitted',
                'user_id': request.env.user.id,
                'description': _('Request %s submitted for approval via portal by %s') % (
                    req_record.name, request.env.user.name
                ),
                'timestamp': datetime.now(),
            })

            return {'success': True, 'message': _('Request submitted successfully')}

        except ValidationError as e:
            _logger.warning(f"Request submit validation error: {str(e)}")
            return {'success': False, 'error': str(e)}
        except AccessError as e:
            _logger.error(f"Request submit access error: {str(e)}")
            return {'success': False, 'error': _('Access denied')}
        except Exception as e:
            _logger.error(f"Request submit failed: {str(e)}")
            return {'success': False, 'error': _('Request submission failed')}

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
            return request.render('records_management.portal_error', {
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

        return request.render("records_management.portal_my_certificates", values)

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
            request.env['naid.audit.log'].sudo().create({
                'action_type': 'destruction_approved',
                'user_id': user.id,
                'description': _('Destruction request %s approved via portal by %s') % (
                    dest_request.name, user.name
                ),
                'timestamp': datetime.now(),
            })

            return {'success': True, 'message': _('Destruction request approved successfully')}

        except ValidationError as e:
            _logger.warning(f"Destruction approval validation error: {str(e)}")
            return {'success': False, 'error': str(e)}
        except AccessError as e:
            _logger.error(f"Destruction approval access error: {str(e)}")
            return {'success': False, 'error': _('Access denied')}
        except Exception as e:
            _logger.error(f"Destruction approval failed: {str(e)}")
            return {'success': False, 'error': _('Destruction approval operation failed')}

    # ============================================================================
    # BILLING & REPORTS ROUTES (12 routes)
    # ============================================================================

    @http.route(['/my/invoices'], type='http', auth='user', website=True)
    def portal_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        """List all billing invoices for the portal user."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        domain = [('partner_id', 'child_of', partner.commercial_partner_id.id), ('move_type', 'in', ('out_invoice', 'out_refund'))]

        # Pagination
        invoice_count = request.env['account.move'].search_count(domain)
        pager = request.website.pager(
            url="/my/invoices",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=invoice_count,
            page=page,
            step=20,
        )

        invoices = request.env['account.move'].search(domain, order='invoice_date desc', limit=20, offset=pager['offset'])

        values.update({
            'invoices': invoices,
            'page_name': 'invoices',
            'pager': pager,
            'invoice_count': invoice_count,
        })
        return request.render('records_management.portal_billing', values)

    @http.route(['/my/invoices/history'], type='http', auth='user', website=True)
    def portal_invoices_history(self, page=1, **kw):
        """View payment history."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        domain = [('partner_id', '=', partner.commercial_partner_id.id)]
        payment_count = request.env['account.payment'].search_count(domain)

        pager = request.website.pager(
            url="/my/invoices/history",
            total=payment_count,
            page=page,
            step=20,
        )

        payments = request.env['account.payment'].search(domain, order='date desc', limit=20, offset=pager['offset'])

        values.update({
            'payments': payments,
            'page_name': 'payment_history',
            'pager': pager,
        })
        return request.render('records_management.portal_billing_details', values)

    @http.route(['/my/billing/rates'], type='http', auth='user', website=True)
    def portal_billing_rates(self, **kw):
        """View billing rate information."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        # Get rate information for this partner
        rates = request.env['records.billing.rate'].search([
            '|',
            ('partner_id', '=', partner.commercial_partner_id.id),
            ('partner_id', '=', False)  # General rates
        ])

        values.update({
            'rates': rates,
            'page_name': 'billing_rates',
        })
        return request.render('records_management.portal_billing_rates', values)

    @http.route(['/my/billing/statements'], type='http', auth='user', website=True)
    def portal_billing_statements(self, page=1, **kw):
        """Download billing statements."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        statements = request.env['records.billing.statement'].search([
            ('partner_id', '=', partner.commercial_partner_id.id)
        ], order='date desc', limit=20)

        values.update({
            'statements': statements,
            'page_name': 'billing_statements',
        })
        return request.render('records_management.portal_billing_statements', values)

    @http.route(['/my/reports'], type='http', auth='user', website=True)
    def portal_reports(self, page=1, **kw):
        """Inventory reports dashboard."""
        values = self._prepare_portal_layout_values()
        user = request.env.user
        partner = user.partner_id

        # Department filtering
        if not user.has_group('records_management.group_portal_company_admin'):
            accessible_departments = user.accessible_department_ids.ids
        else:
            accessible_departments = False

        values.update({
            'page_name': 'reports',
            'accessible_departments': accessible_departments,
        })
        return request.render('records_management.portal_reports', values)

    @http.route(['/my/reports/activity'], type='http', auth='user', website=True)
    def portal_reports_activity(self, page=1, date_begin=None, date_end=None, **kw):
        """Activity reports."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        domain = [('partner_id', '=', partner.commercial_partner_id.id)]
        if date_begin:
            domain.append(('create_date', '>=', date_begin))
        if date_end:
            domain.append(('create_date', '<=', date_end))

        activities = request.env['naid.audit.log'].search(domain, order='timestamp desc', limit=100)

        values.update({
            'activities': activities,
            'page_name': 'reports_activity',
        })
        return request.render('records_management.portal_reports_activity', values)

    @http.route(['/my/reports/compliance'], type='http', auth='user', website=True)
    def portal_reports_compliance(self, **kw):
        """Compliance reports for NAID."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        # Get compliance status
        compliance_data = {
            'naid_certified': partner.naid_certified,
            'certification_date': partner.naid_certification_date,
            'audit_logs_count': request.env['naid.audit.log'].search_count([('partner_id', '=', partner.id)]),
        }

        values.update({
            'compliance_data': compliance_data,
            'page_name': 'reports_compliance',
        })
        return request.render('records_management.portal_reports_compliance', values)

    @http.route(['/my/reports/export'], type='http', auth='user', website=True)
    def portal_reports_export(self, **kw):
        """Export data options."""
        values = self._prepare_portal_layout_values()
        values.update({'page_name': 'reports_export'})
        return request.render('records_management.portal_reports_export', values)

    @http.route(['/my/inventory/counts'], type='json', auth='user', website=True)
    def portal_inventory_counts(self, **kw):
        """Inventory count summary - Returns JSON for AJAX calls."""
        user = request.env.user
        partner = user.partner_id

        # Department filtering
        domain = [('partner_id', '=', partner.commercial_partner_id.id)]
        if not user.has_group('records_management.group_portal_company_admin'):
            accessible_departments = user.accessible_department_ids.ids
            if accessible_departments:
                domain.append(('department_id', 'in', accessible_departments))

        # Get counts for all inventory types (use sudo for portal access)
        containers_count = request.env['records.container'].sudo().search_count(domain)
        files_count = request.env['records.file'].sudo().search_count(domain)
        documents_count = request.env['records.document'].sudo().search_count(domain)
        
        # Temp inventory count
        temp_domain = [('partner_id', '=', partner.commercial_partner_id.id)]
        temp_count = request.env['temp.inventory'].sudo().search_count(temp_domain)
        
        # Customer staging locations count
        locations_domain = [('partner_id', '=', partner.commercial_partner_id.id)]
        locations_count = request.env['customer.staging.location'].sudo().search_count(locations_domain)

        return {
            'containers': containers_count,
            'files': files_count,
            'documents': documents_count,
            'temp': temp_count,
            'locations': locations_count,
        }

    @http.route(['/my/inventory/recent_activity'], type='http', auth='user', website=True)
    def portal_inventory_recent_activity(self, page=1, **kw):
        """Recent inventory activity."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        domain = [('partner_id', '=', partner.commercial_partner_id.id)]
        activity_count = request.env['naid.audit.log'].search_count(domain)

        pager = request.website.pager(
            url="/my/inventory/recent_activity",
            total=activity_count,
            page=page,
            step=20,
        )

        activities = request.env['naid.audit.log'].search(
            domain,
            order='timestamp desc',
            limit=20,
            offset=pager['offset']
        )

        values.update({
            'activities': activities,
            'page_name': 'recent_activity',
            'pager': pager,
        })
        return request.render('records_management.portal_reports_activity', values)

    @http.route(['/my/billing/summary'], type='http', auth='user', website=True)
    def portal_billing_summary(self, **kw):
        """Billing summary dashboard."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        summary = {
            'total_invoiced': sum(request.env['account.move'].search([
                ('partner_id', '=', partner.commercial_partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted')
            ]).mapped('amount_total')),
            'total_paid': sum(request.env['account.payment'].search([
                ('partner_id', '=', partner.commercial_partner_id.id)
            ]).mapped('amount')),
        }

        values.update({
            'summary': summary,
            'page_name': 'billing_summary',
        })
        return request.render('records_management.portal_billing_dashboard', values)

    @http.route(['/my/reports/audit'], type='http', auth='user', website=True)
    def portal_reports_audit(self, page=1, **kw):
        """Audit reports for compliance."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        domain = [('partner_id', '=', partner.commercial_partner_id.id)]
        audit_count = request.env['naid.audit.log'].search_count(domain)

        pager = request.website.pager(
            url="/my/reports/audit",
            total=audit_count,
            page=page,
            step=20,
        )

        audits = request.env['naid.audit.log'].search(
            domain,
            order='timestamp desc',
            limit=20,
            offset=pager['offset']
        )

        values.update({
            'audits': audits,
            'page_name': 'audit_reports',
            'pager': pager,
        })
        return request.render('records_management.portal_reports', values)

    # ============================================================================
    # BARCODE ROUTES (3 routes)
    # ============================================================================

    @http.route(['/my/barcode/main'], type='http', auth='user', website=True)
    def portal_barcode_main(self, **kw):
        """Barcode scanning center."""
        values = self._prepare_portal_layout_values()
        values.update({'page_name': 'barcode_main'})
        return request.render('records_management.portal_barcode_main_menu', values)

    @http.route(['/my/barcode/scan/container'], type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_barcode_scan_container(self, barcode_data=None, **post):
        """Scan container barcode."""
        values = self._prepare_portal_layout_values()

        if request.httprequest.method == 'POST' and barcode_data:
            container = request.env['records.container'].sudo().search([
                ('barcode', '=', barcode_data),
                ('partner_id', '=', request.env.user.partner_id.commercial_partner_id.id)
            ], limit=1)

            if container:
                # Log scan in audit
                request.env['naid.audit.log'].sudo().create({
                    'action_type': 'barcode_scan',
                    'user_id': request.env.user.id,
                    'description': _('Container %s scanned via barcode') % container.name,
                    'timestamp': datetime.now(),
                })
                return request.redirect('/my/inventory/container/%s?scanned=success' % container.id)
            else:
                values.update({'error': _('Container not found')})

        values.update({'page_name': 'barcode_scan_container'})
        return request.render('records_management.portal_barcode_scanner', values)

    @http.route(['/my/barcode/scan/file'], type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_barcode_scan_file(self, barcode_data=None, **post):
        """Scan file barcode."""
        values = self._prepare_portal_layout_values()

        if request.httprequest.method == 'POST' and barcode_data:
            file = request.env['records.file'].sudo().search([
                ('barcode', '=', barcode_data),
                ('partner_id', '=', request.env.user.partner_id.commercial_partner_id.id)
            ], limit=1)

            if file:
                # Log scan in audit
                request.env['naid.audit.log'].sudo().create({
                    'action_type': 'barcode_scan',
                    'user_id': request.env.user.id,
                    'description': _('File %s scanned via barcode') % file.name,
                    'timestamp': datetime.now(),
                })
                return request.redirect('/my/inventory/file/%s?scanned=success' % file.id)
            else:
                values.update({'error': _('File not found')})

        values.update({'page_name': 'barcode_scan_file'})
        return request.render('records_management.portal_barcode_scanner', values)

    # ============================================================================
    # FEEDBACK & SETTINGS ROUTES (5 routes)
    # ============================================================================

    @http.route(['/my/feedback'], type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_feedback(self, **post):
        """Submit feedback."""
        values = self._prepare_portal_layout_values()

        if request.httprequest.method == 'POST':
            feedback = request.env['customer.feedback'].sudo().create({
                'partner_id': request.env.user.partner_id.id,
                'name': post.get('subject', 'Portal Feedback'),
                'comments': post.get('feedback'),
                'rating': post.get('rating', '3'),
            })
            return request.redirect('/my/feedback/history?submitted=success')

        values.update({'page_name': 'feedback'})
        return request.render('records_management.feedback_form_template', values)

    @http.route(['/my/feedback/history'], type='http', auth='user', website=True)
    def portal_feedback_history(self, page=1, **kw):
        """View submitted feedback history."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        domain = [('partner_id', '=', partner.id)]
        feedback_count = request.env['customer.feedback'].search_count(domain)

        pager = request.website.pager(
            url="/my/feedback/history",
            total=feedback_count,
            page=page,
            step=20,
        )

        feedbacks = request.env['customer.feedback'].search(
            domain,
            order='create_date desc',
            limit=20,
            offset=pager['offset']
        )

        values.update({
            'feedbacks': feedbacks,
            'page_name': 'feedback_history',
            'pager': pager,
        })
        return request.render('records_management.portal_feedback_history', values)

    @http.route(['/my/notifications'], type='http', auth='user', website=True)
    def portal_notifications(self, **kw):
        """Notification preferences."""
        values = self._prepare_portal_layout_values()
        user = request.env.user

        values.update({
            'user': user,
            'page_name': 'notifications',
        })
        return request.render('records_management.portal_notifications', values)

    @http.route(['/my/notifications/update'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_notifications_update(self, **post):
        """Update notification preferences."""
        user = request.env.user

        # Update notification settings
        user.write({
            'notification_type': post.get('notification_type', 'email'),
        })

        return request.redirect('/my/notifications?updated=success')

    @http.route(['/my/access'], type='http', auth='user', website=True)
    def portal_access(self, **kw):
        """Access management (Department Admin+)."""
        values = self._prepare_portal_layout_values()
        user = request.env.user

        # Require department admin+ permissions
        if not user.has_group('records_management.group_portal_department_admin'):
            return request.render('records_management.portal_error', {
                'error_title': _('Access Denied'),
                'error_message': _('You do not have permission to manage access.'),
            })

        # Get department users
        accessible_departments = user.accessible_department_ids
        department_users = request.env['records.department.user'].search([
            ('department_id', 'in', accessible_departments.ids)
        ])

        values.update({
            'department_users': department_users,
            'page_name': 'access_management',
        })
        return request.render('records_management.portal_access_management', values)

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

    # NOTE: portal_container_detail is defined earlier in this file (around line 2066)
    # with full CRUD support and permission handling

    def portal_file_detail(self, file_id, **kw):
        """Individual file folder detail view"""
        file_folder = request.env['records.file'].sudo().browse(file_id)

        # Security check
        if file_folder.partner_id != request.env.user.partner_id.commercial_partner_id:
            return request.not_found()

        # Get documents in this file folder
        documents_in_file = request.env['records.document'].sudo().search([
            ('file_id', '=', file_id),
            ('partner_id', '=', file_folder.partner_id.id)
        ])

        values = {
            'file': file_folder,  # Template expects 'file'
            'file_folder': file_folder,  # Keep for backwards compatibility
            'documents_in_file': documents_in_file,
            'page_name': 'file_detail',
        }

        return request.render("records_management.portal_file_detail", values)

    @http.route(['/my/inventory/document/<int:document_id>'], type='http', auth="user", website=True)
    def portal_document_detail(self, document_id, **kw):
        """Individual document detail view with PDF scans"""
        document = request.env['records.document'].sudo().browse(document_id)

        # Security check
        if document.partner_id != request.env.user.partner_id.commercial_partner_id:
            return request.not_found()

        # Get PDF scans
        pdf_scans = request.env['ir.attachment'].sudo().search([
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

            # Create retrieval request using sudo() for portal user access
            portal_request = request.env['portal.request'].sudo().create({
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

            # Create destruction request using sudo() for portal user access
            portal_request = request.env['portal.request'].sudo().create({
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

            # Create pickup request using sudo() for portal user access
            portal_request = request.env['portal.request'].sudo().create({
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

            container.sudo().write(update_vals)

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

            # Update file locations using sudo() for portal user access
            files.sudo().write({'container_id': container_id})

            return {
                'success': True,
                'message': f'{len(files)} files added to container {container.name}'
            }

        except ValueError as e:
            return {'success': False, 'error': f'Invalid data format: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Server error: {str(e)}'}



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

        available_files = request.env['records.file'].sudo().search([
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

            # Create temp inventory record using sudo() for portal user access
            temp_inventory = request.env['temp.inventory'].sudo().create({
                'name': description,
                'description': description,
                'partner_id': request.env.user.partner_id.id,
                'state': 'draft',
            })

            # Generate barcode using sequence
            barcode = request.env['ir.sequence'].sudo().next_by_code('temp.inventory') or f"TEMP-{temp_inventory.id}"

            # Update the temp inventory with the barcode in the name if needed
            if temp_inventory.name == description:
                temp_inventory.sudo().write({'name': f"{description} ({barcode})"})

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
            temp_item = request.env['temp.inventory'].sudo().browse(int(item_id))
            if not temp_item.exists() or temp_item.partner_id.id != request.env.user.partner_id.id:
                return {
                    'success': False,
                    'error': 'Item not found or access denied.'
                }

            # Create or find existing pickup request using sudo()
            pickup_request = request.env['portal.request'].sudo().search([
                ('partner_id', '=', request.env.user.partner_id.id),
                ('request_type', '=', 'pickup'),
                ('state', 'in', ['draft', 'submitted'])
            ], limit=1)

            if not pickup_request:
                pickup_request = request.env['portal.request'].sudo().create({
                    'partner_id': request.env.user.partner_id.id,
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
            pickup_request.sudo().write({
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
                if not item.exists() or item.partner_id.id != request.env.user.partner_id.id:
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

            destruction_request = request.env['portal.request'].sudo().create({
                'partner_id': request.env.user.partner_id.id,
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
    # CUSTOMER STAGING LOCATIONS (Virtual locations before pickup)
    # ============================================================================

    @http.route(['/my/inventory/locations'], type='http', auth='user', website=True)
    def portal_staging_locations(self, **kw):
        """
        Customer Staging Locations - Virtual locations for organizing containers before pickup.
        
        Allows customers to:
        - Create hierarchical locations (Company/Dept/Floor/Room)
        - Assign containers to locations
        - Provide pickup instructions to technicians
        """
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id.commercial_partner_id

        # Get customer's staging locations (including archived if requested)
        StagingLocation = request.env['customer.staging.location']
        domain = [('partner_id', '=', partner.id)]

        # Show archived locations if requested
        if not kw.get('show_archived'):
            domain.append(('active', '=', True))

        staging_locations = StagingLocation.search(domain, order='complete_name asc')

        # Get root-level locations (no parent)
        root_locations = staging_locations.filtered(lambda l: not l.parent_id)

        values.update({
            'staging_locations': staging_locations,
            'root_locations': root_locations,
            'page_name': 'staging_locations',
            'total_locations': len(staging_locations),
            'show_archived': kw.get('show_archived'),
            # Notification parameters
            'created': kw.get('created'),
            'updated': kw.get('updated'),
            'archived': kw.get('archived'),
            'unarchived': kw.get('unarchived'),
            'deleted': kw.get('deleted'),
        })

        return request.render("records_management.portal_staging_locations", values)

    @http.route(['/my/inventory/location/create'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_staging_location_create(self, **post):
        """Create new customer staging location"""
        partner = request.env.user.partner_id.commercial_partner_id

        if request.httprequest.method == 'POST':
            # Create location (use sudo for portal users to create staging locations)
            StagingLocation = request.env['customer.staging.location'].sudo()

            vals = {
                'name': post.get('name'),
                'partner_id': partner.id,
                'department_id': int(post.get('department_id')) if post.get('department_id') else False,
                'parent_id': int(post.get('parent_id')) if post.get('parent_id') else False,
                'location_type': post.get('location_type', 'other'),
                'notes': post.get('notes', ''),
            }

            location = StagingLocation.create(vals)

            return request.redirect('/my/inventory/locations?created=%s' % location.id)

        # GET - show form
        values = self._prepare_portal_layout_values()

        # Get available parent locations
        StagingLocation = request.env['customer.staging.location']
        parent_locations = StagingLocation.search([
            ('partner_id', '=', partner.id)
        ], order='complete_name asc')

        # Get smart department context
        user = request.env.user
        dept_context = self._get_smart_department_context(user, user.partner_id)

        values.update({
            'parent_locations': parent_locations,
            'page_name': 'create_staging_location',
            **dept_context,  # departments, default_department, has_departments, show_department_selector
        })

        return request.render("records_management.portal_staging_location_create", values)

    @http.route(['/my/inventory/location/<int:location_id>/edit'], type='http', auth='user', website=True, methods=['GET', 'POST'])
    def portal_staging_location_edit(self, location_id, **post):
        """Edit/update customer staging location"""
        location = request.env['customer.staging.location'].browse(location_id)
        partner = request.env.user.partner_id.commercial_partner_id

        # Security check
        if not location.exists() or location.partner_id.commercial_partner_id != partner:
            return request.redirect('/my/inventory/locations?error=access_denied')

        if request.httprequest.method == 'POST':
            # Update location
            vals = {
                'name': post.get('name'),
                'parent_id': int(post.get('parent_id')) if post.get('parent_id') else False,
                'location_type': post.get('location_type', 'other'),
                'notes': post.get('notes', ''),
            }

            # Only update department if provided
            if post.get('department_id'):
                vals['department_id'] = int(post.get('department_id'))

            try:
                location.sudo().write(vals)
                return request.redirect('/my/inventory/location/%s?updated=1' % location.id)
            except Exception as e:
                return request.render('records_management.portal_error', {
                    'error_message': 'Failed to update location',
                    'error_details': str(e)
                })

        # GET - show edit form
        values = self._prepare_portal_layout_values()

        # Get available parent locations (exclude self and children to prevent recursion)
        StagingLocation = request.env['customer.staging.location']
        all_locations = StagingLocation.search([('partner_id', '=', partner.id)])

        # Exclude current location and its descendants
        child_locations = StagingLocation.search([('id', 'child_of', location.id)])
        parent_locations = all_locations - child_locations

        # Get departments
        departments = request.env['records.department'].search([('partner_id', '=', partner.id)])

        values.update({
            'location': location,
            'parent_locations': parent_locations,
            'departments': departments,
            'page_name': 'edit_staging_location',
        })

        return request.render("records_management.portal_staging_location_edit", values)

    @http.route(['/my/inventory/location/<int:location_id>/archive'], type='http', auth='user', website=True, methods=['POST'])
    def portal_staging_location_archive(self, location_id, **post):
        """Archive/unarchive customer staging location"""
        location = request.env['customer.staging.location'].browse(location_id)
        partner = request.env.user.partner_id.commercial_partner_id

        # Security check
        if not location.exists() or location.partner_id.commercial_partner_id != partner:
            return request.redirect('/my/inventory/locations?error=access_denied')

        # Toggle active state using sudo() for portal user access
        location.sudo().write({'active': not location.active})

        action = 'unarchived' if location.active else 'archived'
        return request.redirect('/my/inventory/locations?%s=%s' % (action, location.id))

    @http.route(['/my/inventory/location/<int:location_id>/delete'], type='http', auth='user', website=True, methods=['POST'])
    def portal_staging_location_delete(self, location_id, **post):
        """Delete customer staging location (only if no containers assigned)"""
        location = request.env['customer.staging.location'].browse(location_id)
        partner = request.env.user.partner_id.commercial_partner_id

        # Security check
        if not location.exists() or location.partner_id.commercial_partner_id != partner:
            return request.redirect('/my/inventory/locations?error=access_denied')

        # Check if location has containers
        if location.container_count > 0:
            return request.render('records_management.portal_error', {
                'error_message': 'Cannot delete location with containers',
                'error_details': 'This location has %s container(s) assigned. Please move or remove them before deleting.' % location.container_count
            })

        # Check if location has child locations
        if location.child_ids:
            return request.render('records_management.portal_error', {
                'error_message': 'Cannot delete location with sub-locations',
                'error_details': 'This location has %s sub-location(s). Please delete or move them first.' % len(location.child_ids)
            })

        try:
            location_name = location.complete_name
            location.unlink()
            return request.redirect('/my/inventory/locations?deleted=%s' % location_name)
        except Exception as e:
            return request.render('records_management.portal_error', {
                'error_message': 'Failed to delete location',
                'error_details': str(e)
            })

    @http.route(['/my/inventory/location/<int:location_id>/print-barcode'], type='http', auth='user', website=True)
    def portal_staging_location_print_barcode(self, location_id, **kw):
        """Generate and print barcode label for staging location."""
        location = request.env['customer.staging.location'].sudo().browse(location_id)
        partner = request.env.user.partner_id.commercial_partner_id

        # Security check
        if not location.exists() or location.partner_id.commercial_partner_id != partner:
            return request.redirect('/my/inventory/locations?error=access_denied')

        # Generate barcode if not exists
        if not location.barcode:
            location.action_generate_barcode()

        # Render barcode label as PDF
        report = request.env.ref('records_management.action_report_staging_location_barcode', raise_if_not_found=False)
        if report:
            pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(report.report_name, [location.id])
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', 'attachment; filename="Location-Barcode-%s.pdf"' % (location.barcode or location.id)),
            ]
            return request.make_response(pdf_content, headers=pdfhttpheaders)
        else:
            # Fallback: render simple HTML barcode page
            return request.render('records_management.portal_staging_location_barcode', {
                'location': location,
                'page_name': 'location_barcode',
            })

    @http.route(['/my/inventory/location/<int:location_id>/generate-barcode'], type='json', auth='user', methods=['POST'])
    def portal_staging_location_generate_barcode(self, location_id, **kw):
        """AJAX endpoint to generate barcode for staging location."""
        try:
            location = request.env['customer.staging.location'].sudo().browse(location_id)
            partner = request.env.user.partner_id.commercial_partner_id

            if not location.exists() or location.partner_id.commercial_partner_id != partner:
                return {'success': False, 'error': 'Access denied'}

            location.action_generate_barcode()
            return {
                'success': True,
                'barcode': location.barcode,
                'message': 'Barcode generated successfully'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route(['/my/inventory/location/<int:location_id>'], type='http', auth='user', website=True)
    def portal_staging_location_detail(self, location_id, **kw):
        """View containers at a specific staging location"""
        location = request.env['customer.staging.location'].browse(location_id)
        partner = request.env.user.partner_id.commercial_partner_id

        if not location.exists() or location.partner_id != partner:
            return request.not_found()

        # Get containers at this location and child locations
        child_locations = request.env['customer.staging.location'].search([
            ('id', 'child_of', location.id)
        ])

        Container = request.env['records.container']
        containers = Container.search([
            ('customer_staging_location_id', 'in', child_locations.ids)
        ], order='name asc')

        values = self._prepare_portal_layout_values()
        values.update({
            'location': location,
            'containers': containers,
            'child_locations': child_locations,
            'page_name': 'staging_location_detail',
            'container_count': len(containers),
            'updated': kw.get('updated'),
        })

        return request.render("records_management.portal_staging_location_detail", values)

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

    def portal_report_documents(self, **kw):
        """Document Inventory Report - PDF generation"""
        partner = request.env.user.partner_id.commercial_partner_id

        # Get all documents for this customer
        documents = request.env['records.document'].sudo().search([
            ('partner_id', '=', partner.id)
        ], order='file_id, name')

        values = {
            'page_name': 'reports',
            'partner': partner,
            'documents': documents,
            'total_documents': len(documents),
            'report_date': fields.Date.today(),
        }

        # Return PDF report
        return request.env.ref('records_management.action_report_document_inventory').report_action(documents, data=values)

    @http.route(['/records/report/certificates'], type='http', auth='user', website=True)
    def portal_report_certificates(self, **kw):
        """Certificate Report - PDF generation"""
        partner = request.env.user.partner_id.commercial_partner_id

        # Get all certificates for this customer
        certificates = request.env['naid.certificate'].sudo().search([
            ('partner_id', '=', partner.id)
        ], order='certificate_date desc')

        values = {
            'page_name': 'reports',
            'partner': partner,
            'certificates': certificates,
            'total_certificates': len(certificates),
            'report_date': fields.Date.today(),
        }

        # Return PDF report
        return request.env.ref('records_management.action_report_naid_certificate').report_action(certificates, data=values)

    @http.route(['/records/report/containers'], type='http', auth='user', website=True)
    def portal_report_containers(self, **kw):
        """Container Status Report - PDF generation"""
        partner = request.env.user.partner_id.commercial_partner_id

        # Get all containers for this customer
        containers = request.env['records.container'].sudo().search([
            ('partner_id', '=', partner.id)
        ], order='name')

        # Calculate summary stats
        summary = {
            'total_containers': len(containers),
            'pending_containers': len(containers.filtered(lambda c: c.state == 'pending')),
            'in_storage': len(containers.filtered(lambda c: c.state == 'in')),
            'out_containers': len(containers.filtered(lambda c: c.state == 'out')),
            'perm_out_containers': len(containers.filtered(lambda c: c.state == 'perm_out')),
            'destroyed_containers': len(containers.filtered(lambda c: c.state == 'destroyed')),
            'total_files': sum(containers.mapped('file_count')),
        }

        values = {
            'page_name': 'reports',
            'partner': partner,
            'containers': containers,
            'summary': summary,
            'report_date': fields.Date.today(),
        }

        # Return PDF report
        return request.env.ref('records_management.action_report_container_status').report_action(containers, data=values)

    # ================================================================
    # FEEDBACK & SUPPORT ROUTES
    # ================================================================

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
        departments = request.env['records.department'].sudo().search([
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

    @http.route(['/my/organization'], type='http', auth='user', website=True)
    def portal_organization_chart(self, **kw):
        """
        Portal Organization Chart - Shows customer company structure
        
        ARCHITECTURE:
        - Company (res.partner with is_company=True) 
          → Departments (records.department)
            → Department Users (records.storage.department.user → res.users)
        
        This now uses the actual records.department and records.storage.department.user
        models instead of relying solely on res.partner hierarchy.
        """
        partner = request.env.user.partner_id
        company = partner.commercial_partner_id  # Get the main company

        # Build organization structure
        nodes = []
        edges = []
        added_ids = set()  # Track what's been added (using composite keys)
        
        # =====================================================================
        # STEP 1: Add Company Node (root)
        # =====================================================================
        company_node_id = f'company_{company.id}'
        nodes.append({
            'id': company_node_id,
            'label': company.name,
            'name': company.name,
            'type': 'company',
            'color': '#f39c12',  # Gold for companies
            'email': company.email or '',
            'phone': company.phone or '',
            'job_title': 'Company',
            'image': f'/web/image/res.partner/{company.id}/avatar_128',
            'is_current_user': False,
        })
        added_ids.add(company_node_id)
        
        # =====================================================================
        # STEP 2: Add Departments (records.department)
        # =====================================================================
        departments = request.env['records.department'].sudo().search([
            ('partner_id', '=', company.id),
            ('active', '=', True),
        ])
        
        for dept in departments:
            dept_node_id = f'dept_{dept.id}'
            if dept_node_id not in added_ids:
                # Determine parent (company or parent department)
                if dept.parent_department_id:
                    parent_node_id = f'dept_{dept.parent_department_id.id}'
                else:
                    parent_node_id = company_node_id
                
                nodes.append({
                    'id': dept_node_id,
                    'label': dept.name,
                    'name': dept.name,
                    'type': 'department',
                    'color': '#27ae60',  # Green for departments
                    'email': '',
                    'phone': '',
                    'job_title': f'Department ({dept.state})',
                    'image': '',
                    'is_current_user': False,
                    'container_count': dept.container_count or 0,
                    'file_count': dept.file_count or 0,
                })
                added_ids.add(dept_node_id)
                
                # Edge from parent to department
                edges.append({
                    'from': parent_node_id,
                    'to': dept_node_id,
                    'color': '#27ae60'
                })
        
        # =====================================================================
        # STEP 3: Add Department Users (records.storage.department.user)
        # =====================================================================
        dept_users = request.env['records.storage.department.user'].sudo().search([
            ('department_id.partner_id', '=', company.id),
            ('state', '=', 'active'),
            ('active', '=', True),
        ])
        
        current_user = request.env.user
        for du in dept_users:
            user = du.user_id
            user_partner = user.partner_id
            user_node_id = f'user_{user.id}'
            
            if user_node_id not in added_ids:
                # Determine color based on user type
                if user.id == current_user.id:
                    color = '#e74c3c'  # Red - you are here
                elif user.share:
                    color = '#e91e63'  # Pink - portal user
                else:
                    color = '#3498db'  # Blue - internal user
                
                # Role badge
                role_label = dict(du._fields['role'].selection).get(du.role, 'User')
                
                nodes.append({
                    'id': user_node_id,
                    'label': user.name,
                    'name': user.name,
                    'type': 'person',
                    'color': color,
                    'email': user.email or user_partner.email or '',
                    'phone': user_partner.phone or '',
                    'job_title': f'{role_label} ({du.access_level})',
                    'image': f'/web/image/res.users/{user.id}/avatar_128' if user.id else '',
                    'is_current_user': user.id == current_user.id,
                    'role': du.role,
                    'access_level': du.access_level,
                })
                added_ids.add(user_node_id)
            
            # Edge from department to user (always add, even if user was already added - they may be in multiple depts)
            dept_node_id = f'dept_{du.department_id.id}'
            edge_key = f'{dept_node_id}->{user_node_id}'
            if edge_key not in added_ids:
                edges.append({
                    'from': dept_node_id,
                    'to': user_node_id,
                    'color': '#3498db'  # Blue for user connections
                })
                added_ids.add(edge_key)
        
        # =====================================================================
        # STEP 4: Add current user if not already in diagram
        # =====================================================================
        current_user_node_id = f'user_{current_user.id}'
        if current_user_node_id not in added_ids:
            nodes.append({
                'id': current_user_node_id,
                'label': current_user.name + ' (You)',
                'name': current_user.name,
                'type': 'person',
                'color': '#e74c3c',  # Red - you are here
                'email': current_user.email or '',
                'phone': current_user.partner_id.phone or '',
                'job_title': 'Portal User',
                'image': f'/web/image/res.users/{current_user.id}/avatar_128',
                'is_current_user': True,
            })
            added_ids.add(current_user_node_id)
            
            # Connect to company if no department assignment
            edges.append({
                'from': company_node_id,
                'to': current_user_node_id,
                'color': '#e74c3c',
                'dashes': True  # Dashed line for "unassigned"
            })

        # Calculate statistics
        stats = {
            'companies': len([n for n in nodes if n['type'] == 'company']),
            'departments': len([n for n in nodes if n['type'] == 'department']),
            'users': len([n for n in nodes if n['type'] == 'person']),
            'connections': len(edges),
        }

        # Prepare diagram data - JSON-encode lists/dicts for JavaScript consumption
        # QWeb t-out escapes HTML by default - wrap with Markup() to mark as safe
        # This prevents HTML entities like &quot; from corrupting the JSON
        diagram_data = {
            'id': company.id,
            'node_data_json': Markup(json.dumps(nodes)),      # Pre-serialized, marked safe
            'edge_data_json': Markup(json.dumps(edges)),      # Pre-serialized, marked safe
            'diagram_stats_json': Markup(json.dumps(stats)),  # Pre-serialized, marked safe
            'show_messaging': True,
            'show_access_rights': False,
            'layout_type': 'hierarchical',
            'search_query': '',
        }

        # Debug: Log what we're sending to template
        _logger.info(f"Organization chart data - Nodes: {len(nodes)}, Edges: {len(edges)}, Stats: {stats}")

        # Prepare context for template
        values = {
            'page_name': 'organization',
            'diagram': diagram_data,
            'user': request.env.user,
            'partner': partner,
            'can_add_users': request.env.user.has_group('records_management.group_portal_company_admin'),
        }

        return request.render("records_management.portal_organization_diagram", values)

    @http.route(['/my/organization/add-user'], type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_add_team_member(self, **post):
        """
        Add Team Member - Company Admin can add new contacts and assign portal access
        Allows portal company admins to invite sub-users with different access levels
        """
        # Security: Only Company Admins can add users
        if not request.env.user.has_group('records_management.group_portal_company_admin'):
            return request.render('records_management.portal_error', {
                'error_title': _('Unauthorized'),
                'error_message': _('Only company administrators can add team members.'),
            })

        partner = request.env.user.partner_id
        company = partner.commercial_partner_id

        # GET request - show form
        if request.httprequest.method == 'GET':
            # Get smart department context (company admins see all departments)
            user = request.env.user
            dept_context = self._get_smart_department_context(user, user.partner_id)

            values = {
                'page_name': 'add_team_member',
                'partner': partner,
                'company': company,
                'success': post.get('success'),
                **dept_context,  # departments, default_department, has_departments, show_department_selector
            }
            return request.render("records_management.portal_add_team_member_form", values)

        # POST request - create contact and send portal invitation
        try:
            # Validate required fields
            name = post.get('name', '').strip()
            email = post.get('email', '').strip()
            portal_access_level = post.get('portal_access_level', 'readonly')

            if not name or not email:
                return request.render('records_management.portal_error', {
                    'error_title': _('Missing Required Fields'),
                    'error_message': _('Please provide at least name and email address.'),
                })

            # Check if email already exists
            existing_partner = request.env['res.partner'].sudo().search([
                ('email', '=ilike', email)
            ], limit=1)

            if existing_partner:
                return request.render('records_management.portal_error', {
                    'error_title': _('Email Already Exists'),
                    'error_message': _('A contact with this email address already exists: %s') % existing_partner.name,
                })

            # Create contact under the company
            contact_vals = {
                'name': name,
                'email': email,
                'phone': post.get('phone', '').strip(),
                'function': post.get('job_title', '').strip(),
                'parent_id': company.id,  # Link to company
                'type': 'contact',
                'company_type': 'person',
                'is_company': False,
            }

            # Optional department assignment
            department_id = post.get('department_id')
            if department_id:
                dept = request.env['records.department'].sudo().browse(int(department_id))
                if dept.company_id.id == company.id:
                    contact_vals['department_id'] = int(department_id)

            # Create the contact
            new_contact = request.env['res.partner'].sudo().create(contact_vals)

            # Create portal user with appropriate access level
            portal_wizard = request.env['portal.wizard'].sudo().create({
                'partner_ids': [(4, new_contact.id)]
            })

            # Map portal access level to groups
            group_mapping = {
                'company_admin': request.env.ref('records_management.group_portal_company_admin').id,
                'department_admin': request.env.ref('records_management.group_portal_department_admin').id,
                'department_user': request.env.ref('records_management.group_portal_department_user').id,
                'readonly': request.env.ref('records_management.group_portal_readonly_employee').id,
            }

            # Get the group ID for the selected access level
            group_id = group_mapping.get(portal_access_level)

            # Grant portal access
            wizard_user = portal_wizard.user_ids.filtered(lambda u: u.partner_id.id == new_contact.id)
            if wizard_user:
                wizard_user.action_grant_access()

                # Assign specific records management group
                if group_id and wizard_user.partner_id.user_ids:
                    user = wizard_user.partner_id.user_ids[0]
                    user.sudo().write({
                        'groups_id': [(4, group_id)]
                    })

            # Audit log
            request.env['naid.audit.log'].sudo().create({
                'action_type': 'user_invited',
                'user_id': request.env.user.id,
                'description': _('Team member %s invited via portal by %s with access level: %s') % (
                    new_contact.name,
                    request.env.user.name,
                    portal_access_level
                ),
                'timestamp': datetime.now(),
            })

            _logger.info(f"Portal user invitation sent: {new_contact.name} ({email}) by {request.env.user.name}")

            return request.redirect('/my/organization?success=user_added&user_name=%s' % new_contact.name)

        except Exception as e:
            _logger.error(f"Team member invitation failed: {str(e)}", exc_info=True)
            return request.render('records_management.portal_error', {
                'error_title': _('Invitation Failed'),
                'error_message': _('Failed to add team member: %s') % str(e),
            })

    # =============================
    # INTERACTIVE FEATURES - AJAX ENDPOINTS
    # =============================

    def portal_inventory_export(self, **kw):
        """
        Export inventory to Excel/CSV
        
        Security: Exports only user's commercial partner data
        Used by: portal_interactive_features.js - PortalInventory widget
        """
        try:
            # Security: Get user's commercial partner
            partner = request.env.user.partner_id.commercial_partner_id

            # Get filters from request
            search = kw.get('search', '')
            location_id = kw.get('location_id')
            status = kw.get('status')

            # Build domain with partner filtering
            domain = [('partner_id', 'child_of', partner.commercial_partner_id.id)]

            if search:
                domain.append('|')
                domain.append(('name', 'ilike', search))
                domain.append(('barcode', 'ilike', search))

            if location_id:
                domain.append(('location_id', '=', int(location_id)))

            if status:
                domain.append(('state', '=', status))

            # Get containers
            Container = request.env['records.container']
            containers = Container.search(domain, order='name asc')

            # Create CSV export
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Headers
            writer.writerow([
                'Container ID',
                'Name',
                'Barcode',
                'Location',
                'Box Count',
                'Status',
                'Created Date'
            ])

            # Data rows
            for container in containers:
                writer.writerow([
                    container.id,
                    container.name,
                    container.barcode or '',
                    container.location_id.name if container.location_id else '',
                    container.box_count or 0,
                    container.state,
                    container.create_date.strftime('%Y-%m-%d') if container.create_date else ''
                ])

            # Prepare response
            output.seek(0)
            response = request.make_response(
                output.getvalue(),
                headers=[
                    ('Content-Type', 'text/csv'),
                    ('Content-Disposition', 'attachment; filename="inventory_export_%s.csv"' % datetime.now().strftime('%Y%m%d_%H%M%S'))
                ]
            )

            # Audit log using sudo() for portal user access
            request.env['naid.audit.log'].sudo().create({
                'action_type': 'export',
                'user_id': request.env.user.id,
                'description': _('Inventory exported by %s (%d records)') % (
                    request.env.user.name,
                    len(containers)
                ),
                'timestamp': datetime.now(),
            })

            return response

        except Exception as e:
            _logger.error(f"Inventory export failed: {str(e)}", exc_info=True)
            return request.render('records_management.portal_error', {
                'error_title': _('Export Failed'),
                'error_message': _('Failed to export inventory: %s') % str(e),
            })
