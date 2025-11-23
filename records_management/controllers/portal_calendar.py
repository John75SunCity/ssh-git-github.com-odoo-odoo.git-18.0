# -*- coding: utf-8 -*-
"""
Portal Calendar Controller
Customer-facing calendar showing scheduled services, pickups, and deliveries
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
        ShredBin = request.env['shred.bin'].sudo()
        shred_bins = ShredBin.search([
            ('partner_id', '=', partner.commercial_partner_id.id),
            ('active', '=', True),
            ('service_frequency', '!=', False)
        ])

        for bin in shred_bins:
            # Generate recurring service dates based on frequency
            service_dates = self._generate_recurring_dates(
                bin.next_service_date or datetime.now(),
                bin.service_frequency,
                start_date,
                end_date
            )

            for service_date in service_dates:
                events.append({
                    'id': f'shred_{bin.id}_{service_date.strftime("%Y%m%d")}',
                    'title': _('Shredding Service: %s') % bin.bin_barcode,
                    'start': service_date.isoformat(),
                    'backgroundColor': '#8B0000',  # Dark red
                    'borderColor': '#8B0000',
                    'extendedProps': {
                        'type': 'shredding',
                        'frequency': bin.service_frequency,
                        'bin_id': bin.id,
                        'location': bin.location_description or 'On-site',
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
