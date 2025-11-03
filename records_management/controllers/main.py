# -*- coding: utf-8 -*-
"""
Records Management Dashboard Controller

Provides web interface for Records Management dashboard with comprehensive
analytics, real-time data, and mobile-responsive interface.

Author: Records Management System
Version: 19.0.0.1
License: LGPL-3
"""

# Standard library imports
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Odoo core imports
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import AccessError, UserError

# Odoo addons imports
from odoo.addons.portal.controllers.portal import CustomerPortal


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
            location = request.env['records.location'].browse(location_id)

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
            data['locations'] = request.env['records.location'].search(
                domain + [('active', '=', True)],
                order='name'
            )
            data['locations_count'] = request.env['records.location'].search_count(domain)

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
        locations = request.env['records.location'].search([('active', '=', True)])
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
        locations = request.env['records.location'].search(domain + [('active', '=', True)])

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

    def _prepare_home_portal_values(self, counters):
        """Add Records Management counters to portal home"""
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        if 'container_count' in counters:
            domain = [('partner_id', '=', partner.id)]
            values['container_count'] = request.env['records.container'].search_count(domain)

        if 'pickup_request_count' in counters:
            domain = [('partner_id', '=', partner.id)]
            values['pickup_request_count'] = request.env['pickup.request'].search_count(domain)

        # Add work order counts from WorkOrderPortal functionality
        if 'work_order_count' in counters:
            domain = [('partner_id', '=', partner.id), ('portal_visible', '=', True)]
            work_order_count = 0
            for model in ['records.retrieval.order', 'container.destruction.work.order', 'container.access.work.order']:
                try:
                    work_order_count += request.env[model].search_count(domain)
                except Exception:
                    pass
            values['work_order_count'] = work_order_count

        if 'coordinator_count' in counters:
            domain = [('partner_id', '=', partner.id), ('customer_visible', '=', True)]
            try:
                values['coordinator_count'] = request.env['work.order.coordinator'].search_count(domain)
            except Exception:
                values['coordinator_count'] = 0

        return values

    @http.route(['/my/containers', '/my/containers/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_containers(self, page=1, sortby=None, filterby=None, search=None, **kw):
        """Customer portal container listing"""
        partner = request.env.user.partner_id
        domain = [('partner_id', '=', partner.id), ('active', '=', True)]

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
            'sortby': sortby,
            'search': search,
        }

        return request.render('records_management.portal_my_containers', values)

    @http.route(['/my/containers/new'], type='http', auth='user', website=True)
    def portal_container_create_form(self, error=None, **kw):
        """Portal form to create a new container (Quick Add style)"""
        partner = request.env.user.partner_id
        
        # Get departments for this customer
        departments = request.env['records.department'].search([
            ('partner_id', '=', partner.commercial_partner_id.id),
            ('active', '=', True)
        ])
        
        values = {
            'page_name': 'container_create',
            'departments': departments,
            'partner': partner,
            'error': error,
        }
        return request.render('records_management.portal_container_create_form', values)

    @http.route(['/my/containers/create'], type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_container_create(self, **post):
        """Handle portal container creation with Quick Add Wizard logic"""
        partner = request.env.user.partner_id
        
        # Check if user has create permission
        user_assignment = request.env['records.storage.department.user'].search([
            ('user_id', '=', request.env.user.id),
            ('state', '=', 'active'),
            ('can_create_records', '=', True)
        ], limit=1)
        
        if not user_assignment:
            return request.redirect('/my/containers/new?error=no_permission')
        
        try:
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
            
            # Create container
            container = request.env['records.container'].create(container_vals)
            
            return request.redirect('/my/containers?created=%s' % container.id)
            
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error("Portal container creation error: %s", str(e))
            return request.redirect('/my/containers/new?error=%s' % str(e))
