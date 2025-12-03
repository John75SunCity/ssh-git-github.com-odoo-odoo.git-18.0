# -*- coding: utf-8 -*-
"""
Records Management Dashboard Controller

Provides web interface for Records Management dashboard with comprehensive
analytics, real-time data, and mobile-responsive interface.

Author: Records Management System
Version: 18.0.0.2.29
License: LGPL-3
"""

# Standard library imports
import json
import logging
from types import SimpleNamespace
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Odoo core imports
from odoo import Command, http, fields, _, models
from odoo.http import request
from odoo.exceptions import AccessError, UserError, ValidationError

# Odoo addons imports
from odoo.addons.portal.controllers.portal import CustomerPortal


_logger = logging.getLogger(__name__)


PORTAL_CARD_METADATA = [
    {
        'key': 'inventory',
        'menu_xml_id': 'records_management.portal_menu_records_inventory',
        'icon_class': 'fa fa-cubes text-primary fa-2x',
        'description': 'View and manage your stored containers and documents',
        'fallback_name': 'My Inventory',
        'default_url': '/my/containers',
        'type': 'button_group',
        'badge_value_key': 'container_count',
        'badge_label': 'Containers',
        'badge_empty': 'No containers yet',
        'buttons': [
            {
                'menu_xml_id': 'records_management.portal_menu_records_inventory',
                'label': 'View Inventory',
                'classes': 'btn btn-sm btn-primary',
                'icon_class': 'fa fa-list',
                'fallback_url': '/my/containers',
            },
            {
                'menu_xml_id': 'records_management.portal_menu_records_inventory',
                'label': 'Add Container',
                'classes': 'btn btn-sm btn-outline-success',
                'icon_class': 'fa fa-plus',
                'fallback_url': '/my/inventory/containers/add',
            },
            {
                'menu_xml_id': 'records_management.portal_menu_records_inventory',
                'label': 'Add File',
                'classes': 'btn btn-sm btn-outline-info',
                'icon_class': 'fa fa-folder-plus',
                'fallback_url': '/my/inventory/files/add',
            },
            {
                'menu_xml_id': 'records_management.portal_menu_records_inventory',
                'label': 'Add Document',
                'classes': 'btn btn-sm btn-outline-warning',
                'icon_class': 'fa fa-file-plus',
                'fallback_url': '/my/inventory/documents/add',
            },
        ],
    },
    {
        'key': 'service_requests',
        'menu_xml_id': 'records_management.portal_menu_requests',
        'icon_class': 'fa fa-clipboard-list text-warning fa-2x',
        'description': 'Submit and track pickup, destruction, and service requests',
        'fallback_name': 'Service Requests',
        'default_url': '/my/requests',
        'type': 'button_group',
        'buttons': [
            {
                'menu_xml_id': 'records_management.portal_submenu_request_pickup',
                'classes': 'btn btn-sm btn-outline-primary',
                'label': 'Request Pickup',
                'icon_class': 'fa fa-truck',
                'fallback_url': '/my/request/new/pickup',
            },
            {
                'menu_xml_id': 'records_management.portal_submenu_request_destruction',
                'classes': 'btn btn-sm btn-outline-danger',
                'label': 'Request Destruction',
                'icon_class': 'fa fa-fire',
                'fallback_url': '/my/request/new/destruction',
            },
            {
                'menu_xml_id': 'records_management.portal_menu_requests',
                'classes': 'btn btn-sm btn-outline-success',
                'label': 'View All Requests',
                'icon_class': 'fa fa-list',
                'fallback_url': '/my/requests',
            },
        ],
    },
    {
        'key': 'documents',
        'menu_xml_id': 'records_management.portal_menu_documents',
        'icon_class': 'fa fa-file-text text-info fa-2x',
        'description': 'Access your documents, invoices, and destruction certificates',
        'fallback_name': 'Documents',
        'default_url': '/my/documents',
        'type': 'button_group',
        'buttons': [
            {
                'menu_xml_id': 'records_management.portal_menu_documents',
                'classes': 'btn btn-sm btn-outline-info',
                'label': 'My Documents',
                'icon_class': 'fa fa-file',
                'fallback_url': '/my/documents',
            },
            {
                'menu_xml_id': 'records_management.portal_menu_certificates',
                'classes': 'btn btn-sm btn-outline-danger',
                'label': 'Certificates',
                'icon_class': 'fa fa-certificate',
                'fallback_url': '/my/certificates',
            },
            {
                'menu_xml_id': 'records_management.portal_menu_invoices',
                'classes': 'btn btn-sm btn-outline-success',
                'label': 'Invoices',
                'icon_class': 'fa fa-dollar',
                'fallback_url': '/my/invoices',
            },
        ],
    },
    {
        'key': 'shredding',
        'menu_xml_id': 'records_management.portal_menu_shredding',
        'icon_class': 'fa fa-recycle text-danger fa-2x',
        'description': 'Manage shredding bins, request destruction, and download certificates',
        'fallback_name': 'Shredding & Destruction',
        'default_url': '/my/shredding',
        'type': 'button_group',
        'buttons': [
            {
                'menu_xml_id': 'records_management.portal_menu_shredding',
                'classes': 'btn btn-sm btn-outline-danger',
                'label': 'Shredding Dashboard',
                'icon_class': 'fa fa-dashboard',
                'fallback_url': '/my/shredding',
            },
            {
                'menu_xml_id': 'records_management.portal_menu_shredding',
                'classes': 'btn btn-sm btn-outline-primary',
                'label': 'Request Shredding',
                'icon_class': 'fa fa-fire',
                'fallback_url': '/my/shredding/request/new',
            },
            {
                'menu_xml_id': 'records_management.portal_menu_shredding',
                'classes': 'btn btn-sm btn-outline-success',
                'label': 'Certificates',
                'icon_class': 'fa fa-certificate',
                'fallback_url': '/my/shredding/certificates',
            },
        ],
    },
    {
        'key': 'help',
        'menu_xml_id': 'records_management.portal_menu_help',
        'icon_class': 'fa fa-question-circle text-secondary fa-2x',
        'description': 'Get help, provide feedback, or contact support',
        'fallback_name': 'Help & Support',
        'default_url': '/contactus',
        'type': 'button_group',
        'buttons': [
            {
                'menu_xml_id': 'records_management.portal_submenu_tour',
                'classes': 'btn btn-sm btn-outline-info',
                'label': 'Take Portal Tour',
                'icon_class': 'fa fa-graduation-cap',
                'fallback_url': '/portal/tour',
            },
            {
                'menu_xml_id': 'records_management.portal_submenu_feedback',
                'classes': 'btn btn-sm btn-outline-warning',
                'label': 'Provide Feedback',
                'icon_class': 'fa fa-comment',
                'fallback_url': '/portal/feedback',
            },
            {
                'menu_xml_id': 'records_management.portal_menu_help',
                'classes': 'btn btn-sm btn-outline-secondary',
                'label': 'Help Center',
                'icon_class': 'fa fa-book',
                'fallback_url': '/portal/help',
            },
        ],
    },
]


class RecordsManagementController(http.Controller):
    """
    Records Management Dashboard Controller

    Provides comprehensive dashboard interface for Records Management operations
    including container tracking, document analytics, and location management.
    """

    @http.route(['/records/dashboard', '/records/dashboard/<string:view_type>'],
                type='http', auth='user', website=True)
    def records_dashboard(self, view_type='overview', **kw):
        """
        Main Records Management dashboard with multiple view types

        Args:
            view_type (str): Dashboard view type (overview, containers, documents, locations)
        """
        try:
            # Validate user access
            if not request.env.user.has_group('records_management.group_records_user'):
                raise AccessError(_('You do not have access to Records Management'))

            # Get dashboard configuration from RM Module Configurator
            configurator = self._get_dashboard_configuration()

            # Base data collection with security filtering
            base_domain = self._get_security_domain()

            # Get core data efficiently
            dashboard_data = self._prepare_dashboard_data(base_domain, view_type, configurator)

            # Add analytics and KPI data
            dashboard_data.update(self._get_dashboard_analytics(base_domain))

            # Add real-time notifications
            dashboard_data.update(self._get_dashboard_notifications())

            # Template selection based on view type
            template_map = {
                'overview': 'records_management.dashboard_overview',
                'containers': 'records_management.dashboard_containers',
                'documents': 'records_management.dashboard_documents',
                'locations': 'records_management.dashboard_locations',
                'analytics': 'records_management.dashboard_analytics',
            }

            template = template_map.get(view_type, 'records_management.dashboard_overview')

            return request.render(template, dashboard_data)

        except AccessError:
            return request.redirect('/web/login?redirect=/records/dashboard')
        except Exception as e:
            # Lint conflict workaround: keep multi-arg variant + suppression hint
            return request.render(
                "records_management.dashboard_error", {"error_message": _("Dashboard loading failed: %s", str(e))}  # no-translation-lint
            )

    # Updated for Odoo 18: type="jsonrpc" not supported -> use 'json'
    @http.route(['/records/api/dashboard_data'], type='json', auth='user')
    def get_dashboard_data_json(self, filters=None, **kw):
        """
        AJAX endpoint for real-time dashboard data updates

        Returns:
            dict: JSON data for dashboard widgets
        """
        try:
            # Security validation
            if not request.env.user.has_group('records_management.group_records_user'):
                return {'error': _('Access denied')}

            # Apply filters
            domain = self._get_security_domain()
            if filters:
                domain += self._parse_dashboard_filters(filters)

            # Get real-time data
            data = {
                'containers_count': request.env['records.container'].search_count(domain),
                'documents_count': request.env['records.document'].search_count(domain),
                'active_pickups': self._get_active_pickups_count(domain),
                'pending_destruction': self._get_pending_destruction_count(domain),
                'capacity_utilization': self._calculate_capacity_utilization(domain),
                'revenue_this_month': self._calculate_monthly_revenue(domain),
                'naid_compliance_score': self._calculate_naid_compliance_score(domain),
                'recent_activities': self._get_recent_activities(domain, limit=10),
                'alerts': self._get_system_alerts(),
                'last_updated': datetime.now().isoformat(),
            }

            return data

        except Exception as e:
            return {"error": _("Failed to load dashboard data: %s", str(e))}  # no-translation-lint

    @http.route(['/records/container/<int:container_id>'], type='http', auth='user', website=True)
    def container_detail(self, container_id, **kw):
        """
        Individual container detail page

        Args:
            container_id (int): Container record ID
        """
        try:
            container = request.env['records.container'].browse(container_id)

            if not container.exists():
                raise UserError(_('Container not found'))

            # Check access permissions
            container.check_access_rights('read')
            container.check_access_rule('read')

            # Get related data
            container_data = {
                'container': container,
                'documents': container.document_ids,
                'movements': container.movement_ids.sorted('create_date', reverse=True),
                'audit_logs': self._get_container_audit_logs(container),
                'destruction_records': container.destruction_ids,
                'billing_history': self._get_container_billing_history(container),
                'qr_code_url': self._generate_container_qr_code(container),
            }

            return request.render('records_management.container_detail', container_data)

        except (AccessError, UserError) as e:
            return request.render('records_management.error_page', {
                'error_title': _('Container Access Error'),
                'error_message': str(e)
            })

    @http.route(['/records/location/<int:location_id>'], type='http', auth='user', website=True)
    def location_detail(self, location_id, **kw):
        """
        Location detail page with capacity and utilization data

        Args:
            location_id (int): Location record ID
        """
        try:
            location = request.env['stock.location'].browse(location_id)

            if not location.exists():
                raise UserError(_('Location not found'))

            # Security check
            location.check_access_rights('read')
            location.check_access_rule('read')

            # Calculate location metrics
            location_data = {
                'location': location,
                'containers': location.container_ids,
                'capacity_used': self._calculate_location_capacity_used(location),
                'capacity_available': self._calculate_location_capacity_available(location),
                'utilization_percentage': self._calculate_location_utilization(location),
                'container_types_breakdown': self._get_location_container_breakdown(location),
                'recent_movements': self._get_location_recent_movements(location),
                'access_history': self._get_location_access_history(location),
            }

            return request.render('records_management.location_detail', location_data)

        except (AccessError, UserError) as e:
            return request.render('records_management.error_page', {
                'error_title': _('Location Access Error'),
                'error_message': str(e)
            })

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _get_dashboard_configuration(self):
        """Get dashboard configuration from RM Module Configurator"""
        configurator = request.env['rm.module.configurator'].search([
            ('company_id', 'in', [request.env.company.id, False])
        ])

        config = {}
        for conf in configurator:
            config[conf.config_key] = {
                'boolean_value': conf.boolean_value,
                'text_value': conf.text_value,
                'integer_value': conf.integer_value,
            }

        return config

    def _get_security_domain(self):
        """Get security domain based on user permissions and department access"""
        domain = []

        # Company filter
        domain.append(('company_id', '=', request.env.company.id))

        # Department-based access control
        user = request.env.user
        if user.records_department_ids:
            department_partners = user.records_department_ids.mapped('partner_ids')
            if department_partners:
                domain.append(('partner_id', 'in', department_partners.ids))

        return domain

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

    def _prepare_dashboard_data(self, domain, view_type, configurator):
        """Prepare core dashboard data efficiently"""
        # Get configurable visibility settings
        show_containers = configurator.get('show_dashboard_containers', {}).get('boolean_value', True)
        show_documents = configurator.get('show_dashboard_documents', {}).get('boolean_value', True)
        show_locations = configurator.get('show_dashboard_locations', {}).get('boolean_value', True)

        data = {
            'view_type': view_type,
            'user': request.env.user,
            'company': request.env.company,
            'current_datetime': datetime.now(),
            'page_title': self._get_dashboard_title(view_type),
        }

        # Load data based on configuration and view type
        if show_containers and view_type in ['overview', 'containers']:
            data['containers'] = request.env['records.container'].search(
                domain + [('active', '=', True)],
                limit=100,
                order='create_date desc'
            )
            data['containers_count'] = request.env['records.container'].search_count(domain)

        if show_documents and view_type in ['overview', 'documents']:
            data['documents'] = request.env['records.document'].search(
                domain + [('active', '=', True)],
                limit=100,
                order='create_date desc'
            )
            data['documents_count'] = request.env['records.document'].search_count(domain)

        if show_locations and view_type in ['overview', 'locations']:
            data['locations'] = request.env['stock.location'].search(
                domain + [('active', '=', True)],
                order='name'
            )
            data['locations_count'] = request.env['stock.location'].search_count(domain)

        return data

    def _get_dashboard_analytics(self, domain):
        """Get analytical data for dashboard KPIs"""
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        return {
            'kpis': {
                'containers_added_this_week': self._count_records_in_period(
                    'records.container', domain, week_start
                ),
                'containers_added_this_month': self._count_records_in_period(
                    'records.container', domain, month_start
                ),
                'documents_processed_today': self._count_records_in_period(
                    'records.document', domain, today
                ),
                'pending_pickup_requests': request.env['pickup.request'].search_count(
                    domain + [('state', '=', 'confirmed')]
                ),
                'active_destruction_orders': request.env['shredding.service'].search_count(
                    domain + [('state', 'in', ['confirmed', 'in_progress'])]
                ),
            },
            'trends': self._get_dashboard_trends(domain),
        }

    def _get_dashboard_notifications(self):
        """Get system notifications and alerts"""
        notifications = []

        # Check for overdue pickups
        overdue_pickups = request.env['pickup.request'].search_count([
            ('pickup_date', '<', datetime.now().date()),
            ('state', 'in', ['confirmed', 'in_progress'])
        ])

        if overdue_pickups > 0:
            notifications.append(
                {
                    "type": "warning",
                    "message": _("%d pickup requests are overdue") % overdue_pickups,
                    "action_url": "/records/pickup_requests?filter=overdue",
                }
            )

        # Check for capacity alerts
        locations_near_capacity = self._get_locations_near_capacity()
        if locations_near_capacity:
            notifications.append(
                {
                    "type": "info",
                    "message": _("%d locations are near capacity") % len(locations_near_capacity),
                    "action_url": "/records/locations?filter=near_capacity",
                }
            )

        return {'notifications': notifications}

    def _get_dashboard_title(self, view_type):
        """Get localized dashboard title"""
        titles = {
            'overview': _('Records Management Dashboard'),
            'containers': _('Container Management'),
            'documents': _('Document Management'),
            'locations': _('Location Management'),
            'analytics': _('Analytics & Reports'),
        }
        return titles.get(view_type, _('Records Management'))

    def _count_records_in_period(self, model_name, base_domain, start_date):
        """Count records created in a specific period"""
        if isinstance(start_date, datetime):
            start_datetime = start_date
        else:
            start_datetime = datetime.combine(start_date, datetime.min.time())

        domain = base_domain + [('create_date', '>=', start_datetime)]
        return request.env[model_name].search_count(domain)

    def _get_dashboard_trends(self, domain):
        """Calculate trends for dashboard display"""
        # This would include more sophisticated trend analysis
        return {
            'container_growth_rate': 0.0,  # Placeholder
            'document_processing_rate': 0.0,  # Placeholder
            'revenue_trend': 'up',  # Placeholder
        }

    def _get_locations_near_capacity(self, threshold=90):
        """Get locations that are near capacity threshold"""
        locations = request.env['stock.location'].search([('active', '=', True)])
        near_capacity = []

        for location in locations:
            utilization = self._calculate_location_utilization(location)
            if utilization >= threshold:
                near_capacity.append(location)

        return near_capacity

    def _calculate_location_utilization(self, location):
        """Calculate location utilization percentage"""
        if not location.max_capacity or location.max_capacity <= 0:
            return 0.0

        current_usage = sum(location.container_ids.mapped('volume'))
        return (current_usage / location.max_capacity) * 100

    def _get_active_pickups_count(self, domain):
        """Get count of active pickup requests"""
        return request.env['pickup.request'].search_count(
            domain + [('state', 'in', ['confirmed', 'in_progress'])]
        )

    def _get_pending_destruction_count(self, domain):
        """Get count of pending destruction orders"""
        return request.env['shredding.service'].search_count(
            domain + [('state', '=', 'confirmed')]
        )

    def _calculate_capacity_utilization(self, domain):
        """Calculate overall capacity utilization across all locations"""
        locations = request.env['stock.location'].search(domain + [('active', '=', True)])

        total_capacity = sum(locations.mapped('max_capacity'))
        if total_capacity <= 0:
            return 0.0

        total_used = 0.0
        for location in locations:
            total_used += sum(location.container_ids.mapped('volume'))

        return (total_used / total_capacity) * 100

    def _calculate_monthly_revenue(self, domain):
        """Calculate revenue for current month"""
        month_start = datetime.now().replace(day=1)

        # This would integrate with billing system
        # Placeholder implementation
        return 0.0

    def _calculate_naid_compliance_score(self, domain):
        """Calculate NAID compliance score"""
        # This would analyze audit logs and compliance records
        # Placeholder implementation
        return 95.5

    def _get_recent_activities(self, domain, limit=10):
        """Get recent system activities"""
        activities = []

        # Get recent container movements
        movements = request.env['records.container.movement'].search(
            domain + [('active', '=', True)],
            limit=limit,
            order='create_date desc'
        )

        for movement in movements:
            activities.append(
                {
                    "type": "movement",
                    "description": _("Container %s moved to %s")
                    % (movement.container_id.name, movement.location_id.name),
                    "datetime": movement.create_date,
                    "user": movement.create_uid.name,
                }
            )

        return activities

    def _get_system_alerts(self):
        """Get system-wide alerts"""
        alerts = []

        # System health checks would go here
        # Placeholder implementation

        return alerts

    def _parse_dashboard_filters(self, filters):
        """Parse dashboard filters into search domain"""
        domain = []

        if filters.get('date_from'):
            domain.append(('create_date', '>=', filters['date_from']))

        if filters.get('date_to'):
            domain.append(('create_date', '<=', filters['date_to']))

        if filters.get('partner_id'):
            domain.append(('partner_id', '=', int(filters['partner_id'])))

        return domain

    # ============================================================================
    # CONTAINER DETAIL HELPER METHODS
    # ============================================================================

    def _get_container_audit_logs(self, container):
        """Get audit logs for specific container"""
        # Prevent NewId warning: only search if container is saved
        if not container or not container.id or isinstance(container.id, models.NewId):
            return request.env['naid.audit.log']
        return request.env['naid.audit.log'].search([
            ('container_id', 'in', container.ids)
        ], order='create_date desc', limit=20)

    def _get_container_billing_history(self, container):
        """Get billing history for container"""
        # This would integrate with billing system
        return []

    def _generate_container_qr_code(self, container):
        """Generate QR code URL for container"""
        return '/records/container/%s/qr' % container.id

    # ============================================================================
    # LOCATION DETAIL HELPER METHODS
    # ============================================================================

    def _calculate_location_capacity_used(self, location):
        """Calculate used capacity for location"""
        return sum(location.container_ids.mapped('volume'))

    def _calculate_location_capacity_available(self, location):
        """Calculate available capacity for location"""
        used = self._calculate_location_capacity_used(location)
        return max(0, (location.max_capacity or 0) - used)

    def _get_location_container_breakdown(self, location):
        """Get container type breakdown for location"""
        containers = location.container_ids
        breakdown = {}

        for container in containers:
            container_type = container.container_type or 'unknown'
            if container_type not in breakdown:
                breakdown[container_type] = {'count': 0, 'volume': 0.0}

            breakdown[container_type]['count'] += 1
            breakdown[container_type]['volume'] += container.volume or 0.0

        return breakdown

    def _get_location_recent_movements(self, location, limit=10):
        """Get recent movements for location"""
        return request.env['records.container.movement'].search([
            ('location_id', '=', location.id)
        ], order='create_date desc', limit=limit)

    def _get_location_access_history(self, location, limit=10):
        """Get access history for location"""
        return request.env['bin.key.history'].search([
            ('location_id', '=', location.id)
        ], order='create_date desc', limit=limit)


class RecordsManagementPortal(CustomerPortal):
    """
    Portal integration for Records Management

    Extends customer portal with Records Management specific functionality
    """

    def _get_smart_department_context(self, user=None, partner=None):
        """Get smart department selection context for portal forms.
        
        Returns a dict with:
        - departments: RecordSet of departments user can select from
        - default_department: The single department if user has exactly one, else False
        - has_departments: True if company has ANY departments configured
        - show_department_selector: True if user should see a dropdown (multiple options)
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
        
        # Get all departments for the company
        company_departments = request.env['records.department'].sudo().search([
            ('partner_id', '=', partner.commercial_partner_id.id),
        ])
        
        # Determine which departments to show based on user role
        is_company_admin = user.has_group('records_management.group_portal_company_admin')
        
        if user_departments:
            # User has specific department assignments - include child departments too
            all_user_depts = user_departments
            for dept in user_departments:
                all_user_depts |= dept.child_ids
            departments = all_user_depts
        elif is_company_admin:
            # Company admin sees all departments
            departments = company_departments
        else:
            # Regular user with no assignments - no department selection
            departments = request.env['records.department'].sudo().browse()
        
        # Determine default and selector visibility
        has_departments = bool(company_departments)
        show_department_selector = len(departments) > 1
        default_department = departments[0] if len(departments) == 1 else False
        
        return {
            'departments': departments,
            'default_department': default_department,
            'has_departments': has_departments,
            'show_department_selector': show_department_selector,
        }

    def _collect_records_management_portal_metrics(self, base_values=None):
        """Collect counters and dashboard metadata used on portal landing."""
        partner = request.env.user.partner_id
        commercial_partner = partner.commercial_partner_id

        metrics = dict(base_values or {})

        container_domain = ['|', ('partner_id', '=', partner.id), ('stock_owner_id', '=', partner.id)]
        metrics['container_count'] = request.env['records.container'].sudo().search_count(container_domain)

        if metrics.get('pickup_request_count') is None:
            domain = [('partner_id', '=', partner.id)]
            metrics['pickup_request_count'] = request.env['pickup.request'].search_count(domain)

        work_order_domain = [('partner_id', '=', partner.id), ('portal_visible', '=', True)]
        work_order_count = 0
        for model in ['records.retrieval.order', 'container.destruction.work.order', 'container.access.work.order']:
            try:
                work_order_count += request.env[model].search_count(work_order_domain)
            except Exception:
                continue
        metrics['work_order_count'] = work_order_count

        # coordinator_count removed - work.order.coordinator model was deleted
        # Use Dispatch Center (unified.work.order) for consolidated work order management
        metrics['coordinator_count'] = 0

        # Certificates and invoices are surfaced on the portal dashboard cards
        try:
            certificate_domain = [('partner_id', '=', partner.id)]
            metrics['certificate_count'] = request.env['destruction.certificate'].sudo().search_count(certificate_domain)
        except Exception:
            metrics['certificate_count'] = 0

        try:
            invoice_domain = [
                ('partner_id', '=', partner.id),
                ('move_type', '=', 'out_invoice'),
            ]
            metrics['invoice_count'] = request.env['account.move'].sudo().search_count(invoice_domain)
        except Exception:
            metrics['invoice_count'] = 0

        try:
            allowed_partners = commercial_partner.child_ids.ids + [commercial_partner.id]
            request_domain = [('partner_id', 'in', allowed_partners)]
            metrics['service_request_count'] = request.env['portal.request'].sudo().search_count(request_domain)
        except Exception:
            metrics['service_request_count'] = 0

        metrics['portal_dashboard_cards'] = self._build_portal_dashboard_cards(metrics)
        return metrics

    def _prepare_home_portal_values(self, counters):
        """Add Records Management counters to portal home"""
        values = super()._prepare_home_portal_values(counters)
        metrics = self._collect_records_management_portal_metrics(values)
        values.update(metrics)
        return values

    def _resolve_menu_info(self, xml_id, fallback_name, fallback_url):
        menu = request.env.ref(xml_id, raise_if_not_found=False)
        base_url = request.httprequest.host_url.rstrip('/') if request.httprequest else ''

        def _ensure_absolute(url):
            if not url:
                return ''
            if url.startswith('http://') or url.startswith('https://'):
                return url
            if base_url:
                normalized = url if url.startswith('/') else f'/{url}'
                return f"{base_url}{normalized}"
            return url

        if menu:
            return {
                'name': menu.name,
                'url': _ensure_absolute(menu.url or fallback_url),
            }
        return {
            'name': fallback_name,
            'url': _ensure_absolute(fallback_url),
        }

    def _build_portal_dashboard_cards(self, values):
        cards = []
        for config in PORTAL_CARD_METADATA:
            fallback_name = _(config.get('fallback_name', 'Portal Link'))
            menu_info = self._resolve_menu_info(
                config['menu_xml_id'],
                fallback_name,
                config.get('default_url', '/my/home'),
            )

            card = {
                'key': config['key'],
                'title': menu_info['name'],
                'icon_class': config.get('icon_class'),
                'description': _(config['description']),
                'type': config.get('type', 'summary'),
            }

            badge_value_key = config.get('badge_value_key')
            if badge_value_key:
                badge_value = values.get(badge_value_key, 0)
                card['badge'] = {
                    'value': badge_value,
                    'label': _(config.get('badge_label', 'Items')),
                    'empty_label': _(config.get('badge_empty', 'No records yet')),
                }

            buttons = []
            for button in config.get('buttons', []):
                button_menu = self._resolve_menu_info(
                    button['menu_xml_id'],
                    _(button.get('label', 'Portal Link')),
                    button.get('fallback_url', '/my/home'),
                )
                buttons.append({
                    'url': button_menu['url'],
                    'label': _(button.get('label', button_menu['name'])),
                    'classes': button.get('classes', 'btn btn-sm btn-primary'),
                    'icon_class': button.get('icon_class'),
                })
            card['buttons'] = buttons

            cards.append(card)
        return cards

    @http.route('/records_management/portal/dashboard_cards', type='json', auth='user', website=True)
    def portal_dashboard_cards_endpoint(self):
        """Return assembled dashboard cards for portals that need runtime bootstrap."""
        metrics = self._collect_records_management_portal_metrics()
        cards = metrics.get('portal_dashboard_cards', [])
        response_payload = {
            'cards': cards,
            'counts': {
                key: metrics[key]
                for key in [
                    'container_count',
                    'pickup_request_count',
                    'work_order_count',
                    'coordinator_count',
                    'certificate_count',
                    'invoice_count',
                    'service_request_count',
                ]
                if key in metrics
            },
        }
        return response_payload

    # NOTE: Route disabled to avoid conflict with portal.py - use portal.py version instead
    # @http.route(['/my/containers', '/my/containers/page/<int:page>'],
    #             type='http', auth='user', website=True)
    def portal_my_containers_disabled(self, page=1, sortby=None, filterby=None, search=None, **kw):
        """Customer portal container listing"""
        partner = request.env.user.partner_id
        domain = [('partner_id', '=', partner.id), ('active', '=', True)]

        # Status filter options
        searchbar_filters = {
            'all': {'label': _('All Containers'), 'domain': []},
            'active': {'label': _('Active'), 'domain': [('state', '=', 'active')]},
            'in_storage': {'label': _('In Storage'), 'domain': [('state', '=', 'in_storage')]},
            'in_transit': {'label': _('In Transit'), 'domain': [('state', '=', 'in_transit')]},
            'pending': {'label': _('Pending Pickup'), 'domain': [('state', '=', 'pending_pickup')]},
            'destroyed': {'label': _('Destroyed'), 'domain': [('state', '=', 'destroyed')]},
        }

        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # Sorting options
        searchbar_sortings = {
            'name': {'label': _('Name'), 'order': 'name'},
            'date': {'label': _('Date Created'), 'order': 'create_date desc'},
            'location': {'label': _('Location'), 'order': 'location_id'},
        }

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Search
        if search:
            domain += [('name', 'ilike', search)]

        # Get containers
        containers = request.env['records.container'].search(domain, order=order)

        values = {
            'containers': containers,
            'page_name': 'container',
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
            'search': search or '',
            'container_count': len(containers),
            'default_url': '/my/containers',
        }

        return request.render('records_management.portal_my_containers', values)

    @http.route(['/my/containers/new'], type='http', auth='user', website=True)
    def portal_container_create_form(self, error=None, **kw):
        """Portal form to create a new container (Quick Add style)"""
        partner = request.env.user.partner_id
        user = request.env.user

        # Use smart department helper for consistent behavior across portal
        dept_context = self._get_smart_department_context(user, partner)

        # Build permissions dict expected by template
        # Check user groups to determine permission level
        is_company_admin = user.has_group('records_management.group_portal_company_admin')
        is_dept_admin = user.has_group('records_management.group_portal_department_admin')
        is_dept_user = user.has_group('records_management.group_portal_department_user')
        is_readonly = user.has_group('records_management.group_portal_readonly_employee')

        # Determine user role name
        if is_company_admin:
            user_role = 'Company Admin'
            can_create = True
        elif is_dept_admin:
            user_role = 'Department Admin'
            can_create = True
        elif is_dept_user:
            user_role = 'Department User'
            can_create = True
        elif is_readonly:
            user_role = 'Read-Only'
            can_create = False
        else:
            user_role = 'Portal User'
            can_create = True  # Default portal users can create

        permissions = {
            'user_role': user_role,
            'containers': {
                'can_create': can_create,
                'can_read': True,
                'can_update': not is_readonly,
            },
        }

        values = {
            'page_name': 'container_create',
            'partner': partner,
            'permissions': permissions,
            'error': error,
            **dept_context,  # departments, default_department, has_departments, show_department_selector
        }
        return request.render('records_management.portal_container_create_form', values)

    @http.route(['/my/containers/create'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_container_create(self, **post):
        """Handle portal container creation with Quick Add Wizard logic
        
        Permission is handled by ACL:
        - Portal Company Admin: Full CRUD
        - Portal Dept Admin: Read, Write, Create  
        - Portal Dept User: Read, Write, Create
        - Portal Read-Only: Read only
        """
        partner = request.env.user.partner_id

        try:
            # Try to create - ACL will enforce permissions automatically
            # If user doesn't have create rights, Odoo will raise AccessError

            # Get default temp location
            temp_location = request.env['stock.location'].search([
                ('name', 'ilike', 'temp'),
                ('usage', '=', 'internal')
            ], limit=1)

            if not temp_location:
                # Create or get temp location
                temp_location = request.env['stock.location'].sudo().search([
                    ('complete_name', '=', 'WH/Stock/Temporary Receiving')
                ], limit=1)

            # Calculate destruction date based on retention period
            retention = post.get('retention_period', '7')
            destruction_date = False
            if retention and retention != 'permanent':
                try:
                    years = int(retention) if retention != 'custom' else int(post.get('custom_retention_years', 7))
                    from dateutil.relativedelta import relativedelta
                    destruction_date = fields.Date.today() + relativedelta(years=years)
                except:
                    pass

            # Build contents label (range or description)
            contents_label = ''
            contents_type = post.get('contents_type', 'alphabetical')

            if contents_type == 'custom':
                contents_label = post.get('contents_description', '')
            else:
                range_start = post.get('range_start', '')
                range_end = post.get('range_end', '')
                if range_start and range_end:
                    contents_label = f"{range_start} - {range_end}"

            # Create container with Quick Add logic
            container_vals = {
                'partner_id': partner.commercial_partner_id.id,
                'stock_owner_id': partner.commercial_partner_id.id,  # Stock owner = customer
                'department_id': int(post.get('department_id')) if post.get('department_id') else False,
                'location_id': temp_location.id if temp_location else False,
                'description': contents_label,
                'destruction_date': destruction_date,
            }

            # Generate temp barcode (same logic as wizard)
            container_number = post.get('container_number', '').strip()
            partner_abbr = partner.commercial_partner_id.name[:4].upper() if partner.commercial_partner_id else 'TEMP'
            date_str = fields.Date.today().strftime('%Y%m%d')
            temp_barcode = f"TEMP-{partner_abbr}-{date_str}-{container_number}"

            container_vals['temp_barcode'] = temp_barcode
            container_vals['name'] = f"{partner_abbr}-{container_number}"

            # Create container - Odoo ACL automatically enforces permissions
            container = request.env['records.container'].create(container_vals)

            return request.redirect('/my/containers?created=%s' % container.id)

        except AccessError:
            # User doesn't have create permission (Read-Only Employee group)
            return request.redirect('/my/containers/new?error=no_permission')
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error("Portal container creation error: %s", str(e))
            return request.redirect('/my/containers/new?error=%s' % str(e))

    # ============================================================================
    # PORTAL DOCUMENT RETRIEVAL
    # ============================================================================
    @http.route(['/my/document-retrieval', '/my/document-retrieval/page/<int:page>'], type='http', auth='user', website=True)
    def portal_document_retrieval(self, page=1, **kw):  # pylint: disable=unused-argument
        """Render the unified document retrieval portal page."""
        values = self._prepare_portal_layout_values()
        partner = self._get_portal_partner()

        base_rates, customer_rates, has_custom_rates = self._get_retrieval_rates(partner)

        container_domain = [('partner_id', '=', partner.id), ('active', '=', True)]
        document_domain = [('partner_id', '=', partner.id), ('active', '=', True)]

        containers = request.env['records.container'].search(container_domain, order='create_date desc', limit=100)
        documents = request.env['records.document'].search(document_domain, order='create_date desc', limit=100)

        work_orders = request.env['records.retrieval.order'].search([
            ('partner_id', '=', partner.id),
            ('portal_visible', '=', True)
        ], order='request_date desc', limit=10)

        values.update({
            'page_name': 'document_retrieval',
            'default_url': '/my/document-retrieval',
            'containers': containers,
            'documents': documents,
            'work_orders': work_orders,
            'base_rates': base_rates,
            'customer_rates': customer_rates,
            'has_custom_rates': has_custom_rates,
            'json': json,
            'error_message': kw.get('error') or kw.get('error_message'),
        })

        return request.render('records_management.portal_document_retrieval', values)

    @http.route(['/my/document-retrieval/create'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_document_retrieval_create(self, **post):
        """Handle creation of a document retrieval work order from the portal."""
        partner = self._get_portal_partner()

        try:
            items_payload = self._parse_retrieval_items(post.get('items'))
            if not items_payload:
                raise UserError(_('Please add at least one item to retrieve.'))

            delivery_instructions = self._build_delivery_instructions(post)
            scheduled_date = self._parse_delivery_date(post.get('delivery_date'))

            line_commands = []
            for index, item in enumerate(items_payload, start=1):
                description = item['description']
                file_name = description or _('Portal Retrieval Item %s') % index
                line_vals = {
                    'file_name': file_name,
                    'file_description': description,
                    'barcode': item['barcode'],
                    'item_type': self._map_portal_item_type(item['type']),
                    'partner_id': partner.id,
                    'notes': description,
                }
                if item['container_id']:
                    line_vals['container_id'] = item['container_id']
                if item['document_id']:
                    line_vals['file_reference'] = _('Document ID %s') % item['document_id']
                line_commands.append(Command.create(line_vals))

            order_vals = {
                'partner_id': partner.id,
                'priority': self._map_portal_priority(post.get('priority')),
                'request_description': (post.get('retrieval_notes') or '').strip(),
                'delivery_instructions': delivery_instructions,
                'scheduled_date': scheduled_date,
                'delivery_method': 'physical',
                'line_ids': line_commands,
            }

            order = request.env['records.retrieval.order'].create(order_vals)

            return request.redirect('/my/document-retrieval/%s' % order.id)

        except (UserError, ValidationError) as e:
            return self.portal_document_retrieval(error=str(e))
        except Exception as e:  # pragma: no cover - defensive portal handling
            _logger.exception('Portal retrieval order creation failed')
            fallback = _('We could not submit your retrieval request. Please contact support if the issue persists.')
            return self.portal_document_retrieval(error=fallback)

    @http.route(['/my/document-retrieval/<int:order_id>'], type='http', auth='user', website=True)
    def portal_document_retrieval_detail(self, order_id, **kw):  # pylint: disable=unused-argument
        """Display portal detail view for a retrieval order."""
        partner = self._get_portal_partner()
        order = request.env['records.retrieval.order'].sudo().browse(order_id)

        if not order or not order.exists() or order.partner_id.commercial_partner_id.id != partner.id or not order.portal_visible:
            return request.redirect('/my/document-retrieval')

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'document_retrieval',
            'work_order': order,
        })

        return request.render('records_management.portal_document_retrieval_detail', values)

    @http.route(['/my/document-retrieval/calculate-price'], type='json', auth='user', website=True, csrf=False)
    def portal_document_retrieval_calculate_price(self, **kwargs):  # pylint: disable=unused-argument
        """Return pricing preview for portal calculator."""
        partner = self._get_portal_partner()
        params = request.jsonrequest.get('params', {}) if request.jsonrequest else {}
        priority_key = params.get('priority', 'standard')
        try:
            item_count = int(params.get('item_count', 1) or 1)
        except (TypeError, ValueError):
            item_count = 1
        item_count = max(item_count, 1)

        base_rates, customer_rates, has_custom_rates = self._get_retrieval_rates(partner)
        pricing = self._compute_retrieval_pricing(priority_key, item_count, base_rates, customer_rates, has_custom_rates)

        return pricing

    # ------------------------------------------------------------------
    # Helper methods (portal document retrieval)
    # ------------------------------------------------------------------
    def _get_portal_partner(self):
        partner = request.env.user.partner_id
        return partner.commercial_partner_id or partner

    def _get_retrieval_rates(self, partner):
        base_rate = request.env['base.rate'].sudo().search([
            ('company_id', '=', request.env.company.id),
            ('active', '=', True)
        ], order='effective_date desc', limit=1)

        base_rates = SimpleNamespace(
            base_retrieval_rate=float(base_rate.document_retrieval_rate or 0.0) if base_rate else 0.0,
            base_delivery_rate=float(base_rate.delivery_rate or 0.0) if base_rate else 0.0,
            rush_end_of_day_item=0.0,
            rush_4_hours_item=0.0,
            emergency_1_hour_item=0.0,
            weekend_item=0.0,
            holiday_item=0.0,
        )

        customer_rates = SimpleNamespace(
            custom_retrieval_rate=0.0,
            custom_delivery_rate=0.0,
        )

        negotiated_rate = request.env['customer.negotiated.rate'].sudo().search([
            ('partner_id', '=', partner.id),
            ('active', '=', True),
            ('state', 'in', ['approved', 'active'])
        ], order='priority asc, effective_date desc', limit=1)

        if negotiated_rate:
            if negotiated_rate.per_document_rate:
                customer_rates.custom_retrieval_rate = float(negotiated_rate.per_document_rate)
            if negotiated_rate.per_service_rate:
                customer_rates.custom_delivery_rate = float(negotiated_rate.per_service_rate)

        has_custom_rates = bool(customer_rates.custom_retrieval_rate or customer_rates.custom_delivery_rate)
        return base_rates, customer_rates, has_custom_rates

    def _compute_retrieval_pricing(self, priority_key, item_count, base_rates, customer_rates, has_custom_rates):
        retrieval_rate = customer_rates.custom_retrieval_rate if has_custom_rates and customer_rates.custom_retrieval_rate else base_rates.base_retrieval_rate
        delivery_rate = customer_rates.custom_delivery_rate if has_custom_rates and customer_rates.custom_delivery_rate else base_rates.base_delivery_rate

        retrieval_rate = retrieval_rate or 0.0
        delivery_rate = delivery_rate or 0.0

        base_retrieval_cost = float(retrieval_rate) * item_count
        base_delivery_cost = float(delivery_rate)

        priority_map = {
            'rush_eod': base_rates.rush_end_of_day_item,
            'rush_4h': base_rates.rush_4_hours_item,
            'emergency_1h': base_rates.emergency_1_hour_item,
            'weekend': base_rates.weekend_item,
            'holiday': base_rates.holiday_item,
        }

        priority_surcharge = float(priority_map.get(priority_key, 0.0))
        priority_item_cost = priority_surcharge * item_count
        priority_order_cost = priority_surcharge

        total_cost = base_retrieval_cost + base_delivery_cost + priority_item_cost + priority_order_cost

        return {
            'base_retrieval_cost': base_retrieval_cost,
            'base_delivery_cost': base_delivery_cost,
            'priority_item_cost': priority_item_cost,
            'priority_order_cost': priority_order_cost,
            'total_cost': total_cost,
            'has_custom_rates': has_custom_rates,
        }

    def _map_portal_priority(self, priority_key):
        mapping = {
            'rush_eod': '2',
            'rush_4h': '2',
            'emergency_1h': '3',
            'weekend': '2',
            'holiday': '3',
            'standard': '1',
        }
        return mapping.get(priority_key, '1')

    def _map_portal_item_type(self, item_type):
        mapping = {
            'container': 'container',
            'document': 'file',
            'file': 'file',
        }
        return mapping.get(item_type, 'other')

    def _parse_retrieval_items(self, items_json):
        if not items_json:
            return []
        try:
            payload = json.loads(items_json)
        except (TypeError, ValueError):
            return []
        if not isinstance(payload, list):
            return []

        def _safe_int(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return False

        sanitized = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            sanitized.append({
                'type': (item.get('type') or 'file').strip(),
                'container_id': _safe_int(item.get('container_id')),
                'document_id': _safe_int(item.get('document_id')),
                'barcode': (item.get('barcode') or '').strip(),
                'description': (item.get('description') or '').strip(),
            })
        return sanitized

    def _parse_delivery_date(self, delivery_date_str):
        if not delivery_date_str:
            return False
        try:
            delivery_date = fields.Date.to_date(delivery_date_str)
        except AttributeError:  # pragma: no cover - fallback for older APIs
            try:
                delivery_date = fields.Date.from_string(delivery_date_str)
            except Exception:
                return False
        except Exception:  # pragma: no cover - best effort parsing
            return False
        dt_value = datetime.combine(delivery_date, datetime.min.time())
        return fields.Datetime.to_string(dt_value)

    def _build_delivery_instructions(self, post):
        parts = []
        contact = (post.get('delivery_contact') or '').strip()
        phone = (post.get('delivery_phone') or '').strip()
        address = (post.get('delivery_address') or '').strip()
        if contact:
            parts.append(_('Contact: %s') % contact)
        if phone:
            parts.append(_('Phone: %s') % phone)
        if address:
            parts.append(_('Address: %s') % address)
        notes = (post.get('retrieval_notes') or '').strip()
        if notes:
            parts.append(_('Notes: %s') % notes)
        return '\n'.join(parts)

    # ============================================================================
    # PORTAL SERVICE REQUESTS
    # ============================================================================
    @http.route(['/my/requests', '/my/requests/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_requests(self, page=1, search=None, sortby=None, **kw):
        """Portal service requests list view"""
        values = self._prepare_portal_layout_values()
        PortalRequest = request.env['portal.request']

        # Search domain - filter by commercial partner
        partner = request.env.user.partner_id
        domain = [
            ('partner_id', 'in', partner.commercial_partner_id.child_ids.ids + [partner.commercial_partner_id.id])
        ]

        # Add search filter
        if search:
            domain += [
                '|', '|',
                ('name', 'ilike', search),
                ('description', 'ilike', search),
                ('request_type', 'ilike', search)
            ]

        # Sorting
        sort_order = {
            'date': 'create_date desc',
            'name': 'name',
            'type': 'request_type',
            'status': 'state',
        }
        order = sort_order.get(sortby, 'create_date desc')

        # Count total requests
        total_count = PortalRequest.search_count(domain)

        # Pagination
        items_per_page = 20
        total_pages = (total_count + items_per_page - 1) // items_per_page
        offset = (page - 1) * items_per_page

        # Get requests
        requests = PortalRequest.search(domain, order=order, limit=items_per_page, offset=offset)

        # Pagination info
        has_prev = page > 1
        has_next = page < total_pages

        values.update({
            'requests': requests,
            'total_count': total_count,
            'page_name': 'my_requests',
            'default_url': '/my/requests',
            'search_term': search,
            'sortby': sortby,
            'current_page': page,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_page': page - 1,
            'next_page': page + 1,
        })

        return request.render('records_management.my_requests_template', values)

    @http.route(['/my/requests/<int:request_id>'], type='http', auth='user', website=True)
    def portal_request_detail(self, request_id, **kw):
        """Portal service request detail view"""
        try:
            customer_request = request.env['portal.request'].browse(request_id)

            # Security check - ensure user can access this request
            partner = request.env.user.partner_id
            allowed_partners = partner.commercial_partner_id.child_ids.ids + [partner.commercial_partner_id.id]

            if customer_request.partner_id.id not in allowed_partners:
                return request.redirect('/my/requests')

            values = {
                'customer_request': customer_request,
                'page_name': 'request_detail',
            }

            return request.render('records_management.my_request_detail_template', values)

        except Exception:
            return request.redirect('/my/requests')

    @http.route(['/my/requests/<int:request_id>/cancel'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_request_cancel(self, request_id, **kw):
        """Cancel a service request"""
        try:
            customer_request = request.env['portal.request'].browse(request_id)

            # Security check
            partner = request.env.user.partner_id
            allowed_partners = partner.commercial_partner_id.child_ids.ids + [partner.commercial_partner_id.id]

            if customer_request.partner_id.id not in allowed_partners:
                return request.redirect('/my/requests')

            # Cancel the request
            if customer_request.state in ['draft', 'submitted']:
                customer_request.action_cancel()

            return request.redirect('/my/requests/%s' % request_id)

        except Exception:
            return request.redirect('/my/requests')

    @http.route(['/my/request/new/pickup'], type='http', auth='user', website=True)
    def portal_pickup_request_form(self, **kw):
        """Display pickup request creation form"""
        values = self._prepare_portal_layout_values()
        user = request.env.user
        partner = user.partner_id

        # Use smart department helper for consistent behavior across portal
        dept_context = self._get_smart_department_context(user, partner)
        
        values.update({
            'partner': partner,
            'page_name': 'new_pickup_request',
            'error': kw.get('error'),
            **dept_context,  # departments, default_department, has_departments, show_department_selector
        })

        return request.render('records_management.portal_pickup_request_create', values)

    @http.route(['/my/request/new/pickup/submit'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_pickup_request_create(self, **kw):
        """Create a new pickup request from portal"""
        # Check permissions - all portal users except read-only can create pickup requests
        user = request.env.user
        can_create_pickup = (
            user.has_group("records_management.group_records_user") or
            user.has_group("records_management.group_records_manager") or
            user.has_group("records_management.group_portal_company_admin") or
            user.has_group("records_management.group_portal_department_admin") or
            user.has_group("records_management.group_portal_department_user")
        )
        
        if not can_create_pickup:
            return request.redirect('/my/request/new/pickup?error=insufficient_permissions')

        try:
            partner = request.env.user.partner_id

            # Prepare pickup request values
            vals = {
                'partner_id': partner.commercial_partner_id.id,
                'company_id': int(kw.get('company_id')) if kw.get('company_id') else partner.commercial_partner_id.id,
                'department_id': int(kw.get('department_id')) if kw.get('department_id') else False,
                'contact_name': kw.get('contact_name', partner.name),
                'contact_phone': kw.get('contact_phone', partner.phone),
                'contact_email': kw.get('contact_email', partner.email),
                'pickup_address': kw.get('pickup_address'),
                'preferred_pickup_date': kw.get('preferred_pickup_date'),
                'service_type': kw.get('service_type', 'standard'),
                'estimated_volume': float(kw.get('estimated_volume', 0)) if kw.get('estimated_volume') else 0,
                'estimated_weight': float(kw.get('estimated_weight', 0)) if kw.get('estimated_weight') else 0,
                'special_instructions': kw.get('special_instructions'),
                'description': kw.get('description'),
            }

            # Create pickup request (ACL will enforce permissions)
            pickup_request = request.env['pickup.request'].create(vals)

            # Submit the request
            pickup_request.action_submit()

            return request.redirect('/my/requests?pickup_created=%s' % pickup_request.id)

        except AccessError:
            return request.redirect('/my/request/new/pickup?error=no_permission')
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error("Portal pickup request creation error: %s", str(e))
            return request.redirect('/my/request/new/pickup?error=%s' % str(e))

    @http.route(['/my/request/new/destruction'], type='http', auth='user', website=True)
    def portal_destruction_request_form(self, **kw):
        """Display destruction request creation form"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        # Get user's containers for selection
        containers = request.env['records.container'].search([
            ('partner_id', '=', partner.commercial_partner_id.id)
        ])

        values.update({
            'partner': partner,
            'containers': containers,
            'page_name': 'new_destruction_request',
            'error': kw.get('error'),
        })

        return request.render('records_management.portal_destruction_request_create', values)

    @http.route(['/my/request/new/destruction/submit'], type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_destruction_request_create(self, **kw):
        """Create a new destruction request from portal"""
        # Check permissions - all portal users except read-only can create destruction requests
        user = request.env.user
        can_create_destruction = (
            user.has_group("records_management.group_records_user") or
            user.has_group("records_management.group_records_manager") or
            user.has_group("records_management.group_portal_company_admin") or
            user.has_group("records_management.group_portal_department_admin") or
            user.has_group("records_management.group_portal_department_user")
        )
        
        if not can_create_destruction:
            return request.redirect('/my/request/new/destruction?error=insufficient_permissions')

        try:
            partner = request.env.user.partner_id

            # Prepare destruction request values
            vals = {
                'partner_id': partner.commercial_partner_id.id,
                'destruction_method': kw.get('destruction_method', 'shredding'),
                'notes': kw.get('notes'),
                'naid_compliant': True,  # Always NAID compliant for portal requests
            }

            # Create destruction request (ACL will enforce permissions)
            destruction_request = request.env['records.destruction'].create(vals)

            # If container IDs provided, create destruction items
            container_ids = request.httprequest.form.getlist('container_ids')
            if container_ids:
                for container_id in container_ids:
                    request.env['destruction.item'].create({
                        'destruction_id': destruction_request.id,
                        'container_id': int(container_id),
                    })

            # Schedule the destruction
            destruction_request.action_schedule()

            return request.redirect('/my/requests?destruction_created=%s' % destruction_request.id)

        except AccessError:
            return request.redirect('/my/request/new/destruction?error=no_permission')
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error("Portal destruction request creation error: %s", str(e))
            return request.redirect('/my/request/new/destruction?error=%s' % str(e))
