# -*- coding: utf-8 -*-
"""
Portal Calendar Controller
Customer-facing calendar showing scheduled services, pickups, and deliveries
Also includes the Work Order Coordinator view for company/department admins
"""

import logging
from datetime import datetime, timedelta
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)


class PortalCalendarController(CustomerPortal):
    """
    Portal controller for customer service calendar.
    Shows scheduled:
    - Shredding services (weekly, monthly, etc.)
    - Container pickups
    - Document/file retrievals
    - Delivery appointments
    """

    # ============================================================================
    # WORK ORDER COORDINATOR (Unified View)
    # ============================================================================
    @http.route(['/my/coordinators', '/my/coordinators/page/<int:page>'], type='http', auth='user', website=True)
    def portal_coordinators(self, page=1, sortby='scheduled_date', filterby='all', search=None, **kw):
        """
        Display unified work order coordinator view for company/department admins.
        Shows all active and pending work orders across all types in kanban/list view.
        """
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id.commercial_partner_id
        
        # Build domain - filter by customer
        domain = [('partner_id', '=', partner.id)]
        
        # Department filtering for non-company admins
        if not request.env.user.has_group('records_management.group_portal_company_admin'):
            accessible_depts = request.env.user.accessible_department_ids.ids
            if accessible_depts:
                # Filter by accessible departments if we have department field
                pass  # unified.work.order may not have department_id
        
        # Status filters
        if filterby == 'pending':
            domain += [('state', 'in', ['draft', 'confirmed', 'authorized', 'assigned'])]
        elif filterby == 'scheduled':
            domain += [('state', '=', 'scheduled')]
        elif filterby == 'in_progress':
            domain += [('state', '=', 'in_progress')]
        elif filterby == 'completed':
            domain += [('state', 'in', ['completed', 'verified', 'certified'])]
        elif filterby == 'active':
            domain += [('state', 'not in', ['completed', 'verified', 'certified', 'invoiced', 'cancelled'])]
        
        # Search
        if search:
            domain += ['|', '|', ('name', 'ilike', search), ('display_name', 'ilike', search), ('work_order_type', 'ilike', search)]
        
        # Sort options
        sort_mapping = {
            'scheduled_date': 'scheduled_date desc',
            'priority': 'priority desc, scheduled_date desc',
            'state': 'state, scheduled_date desc',
            'type': 'work_order_type, scheduled_date desc',
        }
        order = sort_mapping.get(sortby, 'scheduled_date desc')
        
        UnifiedWO = request.env['unified.work.order'].sudo()
        
        # Pagination
        step = 20
        offset = (page - 1) * step
        
        work_order_count = UnifiedWO.search_count(domain)
        pager = request.website.pager(
            url="/my/coordinators",
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search},
            total=work_order_count,
            page=page,
            step=step,
        )
        
        work_orders = UnifiedWO.search(domain, order=order, limit=step, offset=offset)
        
        # Group by state for kanban
        state_groups = {}
        for wo in UnifiedWO.search(domain):
            state = wo.state or 'draft'
            if state not in state_groups:
                state_groups[state] = []
            state_groups[state].append(wo)
        
        values.update({
            'work_orders': work_orders,
            'work_order_count': work_order_count,
            'pager': pager,
            'page_name': 'coordinators',
            'sortby': sortby,
            'filterby': filterby,
            'search': search or '',
            'state_groups': state_groups,
            'filter_options': [
                ('all', 'All Work Orders'),
                ('active', 'Active (Not Completed)'),
                ('pending', 'Pending Approval'),
                ('scheduled', 'Scheduled'),
                ('in_progress', 'In Progress'),
                ('completed', 'Completed'),
            ],
            'sort_options': [
                ('scheduled_date', 'Scheduled Date'),
                ('priority', 'Priority'),
                ('state', 'Status'),
                ('type', 'Work Order Type'),
            ],
        })
        
        return request.render("records_management.portal_coordinators_template", values)

    @http.route(['/my/coordinators/<int:work_order_id>'], type='http', auth='user', website=True)
    def portal_coordinator_detail(self, work_order_id, **kw):
        """
        View details of a specific work order from the coordinator view.
        Redirects to the appropriate detail page based on work order type.
        """
        UnifiedWO = request.env['unified.work.order'].sudo()
        work_order = UnifiedWO.browse(work_order_id)
        
        if not work_order.exists():
            return request.redirect('/my/coordinators')
        
        # Check access
        partner = request.env.user.partner_id.commercial_partner_id
        if work_order.partner_id.id != partner.id:
            return request.redirect('/my/coordinators')
        
        # Redirect to appropriate detail view based on type
        redirect_map = {
            'retrieval': '/my/retrievals/',
            'shredding': '/my/shredding/',
            'pickup': '/my/pickups/',
            'container_destruction': '/my/destruction/',
        }
        
        base_url = redirect_map.get(work_order.work_order_type, '/my/work-orders/')
        return request.redirect(f'{base_url}{work_order.source_id}')

    @http.route(['/my/calendar'], type='http', auth='user', website=True)
    def portal_my_calendar(self, **kw):
        """
        Display customer's scheduled services in a calendar view.
        """
        partner = request.env.user.partner_id

        values = {
            'page_name': 'calendar',
            'partner': partner,
        }

        return request.render("records_management.portal_calendar_view", values)

    @http.route(['/my/calendar/events'], type='json', auth='user')
    def portal_calendar_events(self, start=None, end=None, **kw):
        """
        JSON endpoint to fetch calendar events for FullCalendar.js
        
        Returns events in FullCalendar format:
        {
            'id': unique_id,
            'title': event_title,
            'start': iso_datetime,
            'end': iso_datetime (optional),
            'backgroundColor': color,
            'borderColor': color,
            'url': detail_url (optional),
            'extendedProps': {...}
        }
        """
        partner = request.env.user.partner_id
        events = []

        # Parse date range (FullCalendar sends ISO strings)
        if start:
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        else:
            start_date = datetime.now() - timedelta(days=30)

        if end:
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
        else:
            end_date = datetime.now() + timedelta(days=90)

        # ============================================================================
        # 1. SHREDDING SERVICES (Recurring bin services)
        # ============================================================================
        ShredBin = request.env['shredding.service.bin'].sudo()
        shred_bins = ShredBin.search([
            ('current_customer_id', '=', partner.commercial_partner_id.id),
            ('status', '=', 'in_service')
        ])

        for bin in shred_bins:
            # Use next_service_date from shredding.service.bin
            if bin.next_service_date:
                events.append({
                    'id': f'shred_{bin.id}',
                    'title': _('Shredding Service: %s') % bin.barcode,
                    'start': bin.next_service_date.isoformat(),
                    'backgroundColor': '#8B0000',  # Dark red
                    'borderColor': '#8B0000',
                    'extendedProps': {
                        'type': 'shredding',
                        'bin_size': bin.bin_size,
                        'bin_id': bin.id,
                        'location': bin.current_department_id.name if bin.current_department_id else 'On-site',
                    }
                })

        # ============================================================================
        # 2. FIELD SERVICE TASKS (Pickups, Retrievals, Deliveries)
        # ============================================================================
        Task = request.env['project.task'].sudo()

        # Search for FSM tasks related to this customer
        task_domain = [
            ('partner_id', '=', partner.commercial_partner_id.id),
            '|',
            ('scheduled_start_time', '>=', start_date),
            ('date_deadline', '>=', start_date.date()),
        ]

        tasks = Task.search(task_domain)

        for task in tasks:
            # Determine event date (prefer scheduled_start_time, fallback to date_deadline)
            event_start = task.scheduled_start_time or datetime.combine(
                task.date_deadline or datetime.now().date(),
                datetime.min.time()
            )

            event_end = task.scheduled_end_time or (event_start + timedelta(hours=2))

            # Color code by work order type
            color_map = {
                'pickup': '#007bff',      # Blue
                'retrieval': '#28a745',   # Green
                'destruction': '#dc3545', # Red
                'delivery': '#ffc107',    # Yellow
                'internal': '#6c757d',    # Gray
            }

            task_type = task.work_order_type or 'other'
            color = color_map.get(task_type, '#17a2b8')  # Teal default

            # Build detail URL
            detail_url = f'/my/tasks/{task.id}' if task.portal_show else None

            events.append({
                'id': f'task_{task.id}',
                'title': task.name,
                'start': event_start.isoformat(),
                'end': event_end.isoformat() if event_end else None,
                'backgroundColor': color,
                'borderColor': color,
                'url': detail_url,
                'extendedProps': {
                    'type': 'service',
                    'work_order_type': task_type,
                    'task_id': task.id,
                    'stage': task.stage_id.name if task.stage_id else 'Scheduled',
                }
            })

        # ============================================================================
        # 3. PORTAL REQUESTS (Pending pickups, destructions)
        # ============================================================================
        PortalRequest = request.env['portal.request'].sudo()

        portal_requests = PortalRequest.search([
            ('partner_id', '=', partner.commercial_partner_id.id),
            ('state', 'in', ['draft', 'submitted', 'approved']),
            ('requested_date', '!=', False),
            ('requested_date', '>=', start_date.date()),
            ('requested_date', '<=', end_date.date()),
        ])

        for req in portal_requests:
            req_date = datetime.combine(req.requested_date, datetime.min.time())

            # Color by request type
            req_color = '#6610f2' if req.request_type == 'destruction' else '#fd7e14'  # Purple or Orange

            events.append({
                'id': f'request_{req.id}',
                'title': _('%s Request') % req.request_type.capitalize(),
                'start': req_date.isoformat(),
                'backgroundColor': req_color,
                'borderColor': req_color,
                'url': f'/my/requests/{req.id}',
                'extendedProps': {
                    'type': 'request',
                    'request_type': req.request_type,
                    'request_id': req.id,
                    'state': req.state,
                }
            })

        # ============================================================================
        # 4. CONTAINER RETRIEVALS (Scheduled document access)
        # ============================================================================
        RetrievalOrder = request.env['records.retrieval.order'].sudo()

        retrievals = RetrievalOrder.search([
            ('partner_id', '=', partner.commercial_partner_id.id),
            ('state', 'not in', ['cancelled', 'delivered']),
            ('scheduled_date', '>=', start_date),
            ('scheduled_date', '<=', end_date),
        ])

        for retrieval in retrievals:
            events.append({
                'id': f'retrieval_{retrieval.id}',
                'title': _('Document Retrieval: %s') % retrieval.name,
                'start': retrieval.scheduled_date.isoformat(),
                'backgroundColor': '#20c997',  # Teal
                'borderColor': '#20c997',
                'url': f'/my/retrievals/{retrieval.id}' if hasattr(retrieval, 'portal_url') else None,
                'extendedProps': {
                    'type': 'retrieval',
                    'retrieval_id': retrieval.id,
                    'state': retrieval.state,
                }
            })

        return events

    def _generate_recurring_dates(self, start_date, frequency, range_start, range_end):
        """
        Generate recurring service dates based on frequency.
        
        Args:
            start_date: First service date
            frequency: 'weekly', 'biweekly', 'monthly', 'quarterly'
            range_start: Calendar view start
            range_end: Calendar view end
            
        Returns:
            List of datetime objects
        """
        if not start_date or not frequency:
            return []

        dates = []
        current = start_date

        # Frequency intervals
        intervals = {
            'weekly': timedelta(days=7),
            'biweekly': timedelta(days=14),
            'monthly': timedelta(days=30),  # Approximate
            'quarterly': timedelta(days=90),
        }

        interval = intervals.get(frequency, timedelta(days=7))

        # Generate dates within range
        while current <= range_end:
            if current >= range_start:
                dates.append(current)
            current += interval

            # Safety limit: max 100 occurrences
            if len(dates) > 100:
                break

        return dates
