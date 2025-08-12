# -*- coding: utf-8 -*-
"""
Customer Portal Integration for Work Orders

This module provides customer portal integration for all work order types,
allowing customers to:
- View work order status and progress
- Track real-time updates and notifications
- Access work order documents and reports
- Submit feedback and confirmations
- Manage work order preferences

Integration Features:
- Unified portal dashboard for all work order types
- Real-time status updates and notifications
- Document access and download capabilities
- Customer feedback and rating system
- Mobile-responsive interface for field access

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.osv.expression import OR


class WorkOrderPortal(CustomerPortal):
    """Customer portal integration for work orders"""

    def _prepare_home_portal_values(self, counters):
        """Add work order counts to portal home"""
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        if 'work_order_count' in counters:
            # Count all work orders for the customer
            domain = [('partner_id', '=', partner.id), ('portal_visible', '=', True)]
            
            work_order_count = 0
            # Count each work order type
            for model in ['container.retrieval.work.order', 'file.retrieval.work.order',
                         'scan.retrieval.work.order', 'container.destruction.work.order',
                         'container.access.work.order']:
                try:
                    work_order_count += request.env[model].search_count(domain)
                except AccessError:
                    pass

            values['work_order_count'] = work_order_count

        if 'coordinator_count' in counters:
            coordinator_count = request.env['work.order.coordinator'].search_count([
                ('partner_id', '=', partner.id),
                ('customer_visible', '=', True)
            ])
            values['coordinator_count'] = coordinator_count

        return values

    @http.route(['/my/work_orders', '/my/work_orders/page/<int:page>'], type='http', 
                auth="user", website=True)
    def portal_my_work_orders(self, page=1, date_begin=None, date_end=None,
                              sortby=None, filterby=None, search=None, search_in='all', **kw):
        """Display customer work orders in portal"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        # Domain for all work orders
        domain = [('partner_id', '=', partner.id), ('portal_visible', '=', True)]

        # Search and filter logic
        searchbar_sortings = {
            'date': {'label': _('Date'), 'order': 'scheduled_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
            'priority': {'label': _('Priority'), 'order': 'priority desc'},
        }

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'active': {'label': _('Active'), 'domain': [('state', 'not in', ['completed', 'cancelled'])]},
            'completed': {'label': _('Completed'), 'domain': [('state', 'in', ['completed', 'done'])]},
        }

        # Default sort order
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # Apply filters
        if filterby:
            domain += searchbar_filters[filterby]['domain']

        # Date filters
        if date_begin and date_end:
            domain += [('scheduled_date', '>=', date_begin), ('scheduled_date', '<=', date_end)]

        # Collect all work orders from different models
        all_work_orders = []
        
        work_order_models = {
            'container.retrieval.work.order': _('Container Retrieval'),
            'file.retrieval.work.order': _('File Retrieval'),
            'scan.retrieval.work.order': _('Scan Retrieval'),
            'container.destruction.work.order': _('Container Destruction'),
            'container.access.work.order': _('Container Access'),
        }

        for model_name, type_label in work_order_models.items():
            try:
                orders = request.env[model_name].search(domain, order=order)
                for order in orders:
                    all_work_orders.append({
                        'record': order,
                        'type': type_label,
                        'model': model_name,
                        'url': f'/my/work_order/{model_name}/{order.id}',
                    })
            except AccessError:
                pass

        # Apply search
        if search and search_in:
            search_domain = []
            if search_in in ('all', 'name'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('all', 'description'):
                search_domain = OR([search_domain, [('description', 'ilike', search)]])
            
            # Filter work orders by search
            filtered_orders = []
            for wo in all_work_orders:
                if search.lower() in wo['record'].name.lower() or \
                   (wo['record'].description and search.lower() in wo['record'].description.lower()):
                    filtered_orders.append(wo)
            all_work_orders = filtered_orders

        # Sort work orders
        if sortby == 'date':
            all_work_orders.sort(key=lambda x: x['record'].scheduled_date or x['record'].create_date, reverse=True)
        elif sortby == 'name':
            all_work_orders.sort(key=lambda x: x['record'].name)
        elif sortby == 'priority':
            all_work_orders.sort(key=lambda x: int(x['record'].priority or 0), reverse=True)

        # Pagination
        total = len(all_work_orders)
        pager = portal_pager(
            url="/my/work_orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 
                     'filterby': filterby, 'search': search, 'search_in': search_in},
            total=total,
            page=page,
            step=20
        )

        # Get work orders for current page
        start = (page - 1) * 20
        end = start + 20
        work_orders = all_work_orders[start:end]

        values.update({
            'work_orders': work_orders,
            'page_name': 'work_orders',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'sortby': sortby,
            'filterby': filterby,
            'search': search,
            'search_in': search_in,
        })

        return request.render("records_management.portal_my_work_orders", values)

    @http.route(['/my/work_order/<string:model>/<int:order_id>'], type='http',
                auth="user", website=True)
    def portal_work_order_detail(self, model, order_id, access_token=None, **kw):
        """Display individual work order details"""
        try:
            work_order = self._document_check_access(model, order_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # Get work order type label
        type_labels = {
            'container.retrieval.work.order': _('Container Retrieval'),
            'file.retrieval.work.order': _('File Retrieval'),
            'scan.retrieval.work.order': _('Scan Retrieval'),
            'container.destruction.work.order': _('Container Destruction'),
            'container.access.work.order': _('Container Access'),
        }

        values = {
            'work_order': work_order,
            'work_order_type': type_labels.get(model, _('Work Order')),
            'page_name': 'work_order_detail',
        }

        # Add model-specific information
        if model == 'container.retrieval.work.order':
            values.update({
                'show_containers': True,
                'show_delivery_info': True,
            })
        elif model == 'file.retrieval.work.order':
            values.update({
                'show_files': True,
                'show_pickup_info': True,
            })
        elif model == 'scan.retrieval.work.order':
            values.update({
                'show_scan_specs': True,
                'show_digital_delivery': True,
            })

        return request.render("records_management.portal_work_order_detail", values)

    @http.route(['/my/coordinators', '/my/coordinators/page/<int:page>'], type='http',
                auth="user", website=True)
    def portal_my_coordinators(self, page=1, date_begin=None, date_end=None,
                              sortby=None, **kw):
        """Display work order coordinators in portal"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        
        domain = [('partner_id', '=', partner.id), ('customer_visible', '=', True)]

        # Date filters
        if date_begin and date_end:
            domain += [('scheduled_date', '>=', date_begin), ('scheduled_date', '<=', date_end)]

        # Sort order
        order = 'scheduled_date desc'
        if sortby == 'name':
            order = 'name'
        elif sortby == 'progress':
            order = 'coordination_progress desc'

        coordinators = request.env['work.order.coordinator'].search(domain, order=order)

        # Pagination
        pager = portal_pager(
            url="/my/coordinators",
            total=len(coordinators),
            page=page,
            step=20
        )

        coordinators = coordinators[(page-1)*20:page*20]

        values.update({
            'coordinators': coordinators,
            'page_name': 'coordinators',
            'pager': pager,
        })

        return request.render("records_management.portal_my_coordinators", values)

    def _document_check_access(self, model_name, document_id, access_token=None):
        """Check access to work order document"""
        document = request.env[model_name].browse([document_id])
        document_sudo = document.sudo().exists()
        
        if not document_sudo:
            raise MissingError(_("This document does not exist."))
        
        # Check if user has access
        try:
            document.check_access_rights('read')
            document.check_access_rule('read')
        except AccessError:
            if not access_token or not document_sudo.access_token or \
               not document_sudo._portal_ensure_token() == access_token:
                raise
        
        return document_sudo
