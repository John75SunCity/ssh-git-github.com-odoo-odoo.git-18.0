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
Version: 19.0.0.1
License: LGPL-3
"""

# Standard library imports

# Odoo core imports
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.osv.expression import OR

# Odoo addons imports
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class WorkOrderPortal(CustomerPortal):
    """Customer portal integration for work orders"""

    def _prepare_home_portal_values(self, counters):
        """Add work order counts to portal home"""
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        # Global portal gating: if disabled via configurator, suppress counts
        config_enabled = request.env['rm.module.configurator'].sudo().get_config_parameter('work_orders_portal_enabled', True)
        if not config_enabled:
            if 'work_order_count' in counters:
                values['work_order_count'] = 0
            return values

        if 'work_order_count' in counters:
            # Count all work orders for the customer
            domain = [('partner_id', '=', partner.id), ('portal_visible', '=', True)]

            work_order_count = 0
            # Count each work order type
            # Only include currently supported unified or active work order models
            for model in [
                'records.retrieval.order',  # unified retrieval order model
                'container.destruction.work.order',
                'container.access.work.order'
            ]:
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

        # Respect global portal toggle: if disabled, render page with no results (avoids controller removal complexity)
        config_enabled = request.env['rm.module.configurator'].sudo().get_config_parameter('work_orders_portal_enabled', True)
        if not config_enabled:
            values.update({
                'work_orders': [],
                'page_name': 'work_orders',
                'pager': portal_pager(url='/my/work_orders', total=0, page=page, step=20),
                'searchbar_sortings': {},
                'searchbar_filters': {},
                'searchbar_inputs': {},
                'sortby': None,
                'filterby': None,
                'search': None,
                'search_in': None,
                'default_url': '/my/work_orders',
            })
            return request.render("records_management.portal_my_work_orders", values)

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
            'records.retrieval.order': _('Records Retrieval'),
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
                        'url': '/my/work_order/%s/%s' % (model_name, order.id),
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
                record_name = wo['record'].name or ''
                record_description = wo['record'].description or ''
                if search.lower() in record_name.lower() or \
                   search.lower() in record_description.lower():
                    filtered_orders.append(wo)
            all_work_orders = filtered_orders

        # Sort work orders
        if sortby == 'date':
            all_work_orders.sort(
                key=lambda x: x['record'].scheduled_date or x['record'].create_date,
                reverse=True
            )
        elif sortby == 'name':
            all_work_orders.sort(key=lambda x: x['record'].name or '')
        elif sortby == 'priority':
            all_work_orders.sort(key=lambda x: int(x['record'].priority or 0), reverse=True)

        # Pagination
        total = len(all_work_orders)
        url_args = {
            'date_begin': date_begin,
            'date_end': date_end,
            'sortby': sortby,
            'filterby': filterby,
            'search': search,
            'search_in': search_in
        }

        pager = portal_pager(
            url="/my/work_orders",
            url_args=url_args,
            total=total,
            page=page,
            step=20
        )

        # Get work orders for current page
        start = (page - 1) * 20
        end = start + 20
        work_orders = all_work_orders[start:end]

        # Provide the context variables expected by the generic portal searchbar template.
        # Without these, the base template may attempt to concatenate None (default_url) with strings
        # producing a TypeError in QWeb (observed portal.portal_searchbar crash).
        values.update({
            'work_orders': work_orders,
            'page_name': 'work_orders',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': self._prepare_work_order_searchbar_inputs(),  # expected by portal searchbar
            'sortby': sortby,
            'filterby': filterby,
            'search': search,
            'search_in': search_in,
            # Explicit default_url so portal.portal_searchbar can safely build links
            'default_url': '/my/work_orders',
        })

        return request.render("records_management.portal_my_work_orders", values)

    @http.route(['/my/work_order/<string:model>/<int:order_id>'], type='http',
                auth="user", website=True)
    def portal_work_order_detail(self, model, order_id, access_token=None, **kw):
        """Display individual work order details"""
        try:
            work_order = self._check_work_order_access(model, order_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # Get work order type label
        type_labels = {
            'records.retrieval.order': _('Records Retrieval'),
            'container.destruction.work.order': _('Container Destruction'),
            'container.access.work.order': _('Container Access'),
        }

        values = {
            'work_order': work_order,
            'work_order_type': type_labels.get(model, _('Work Order')),
            'page_name': 'work_order_detail',
        }

        # Add model-specific information
        if model == 'records.retrieval.order':
            values.update({
                'show_retrieval_lines': True,
                'show_delivery_info': True,
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

    def _check_work_order_access(self, model_name, document_id, access_token=None):
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

    # ============================================================================
    # PORTAL INTEGRATION METHODS
    # ============================================================================
    def _prepare_work_order_searchbar_inputs(self):
        """Prepare search inputs for work orders in the portal"""
        return {
            'all': {'input': 'all', 'label': _('Search in All')},
            'name': {'input': 'name', 'label': _('Search in Reference')},
            'description': {'input': 'description', 'label': _('Search in Description')},
        }

    def _get_work_order_groupby_mapping(self):
        """Get groupby options for work orders"""
        return {
            'none': _('None'),
            'type': _('Work Order Type'),
            'state': _('Status'),
            'priority': _('Priority'),
            'assigned_technician': _('Assigned Technician'),
        }

    def _prepare_work_order_domain(self, partner_id, search=None, search_in=None,
                                  filterby=None, date_begin=None, date_end=None):
        """Prepare domain for work order search"""
        domain = [
            ('partner_id', '=', partner_id),
            ('portal_visible', '=', True)
        ]

        # Apply date filters
        if date_begin and date_end:
            domain += [
                ('scheduled_date', '>=', date_begin),
                ('scheduled_date', '<=', date_end)
            ]

        # Apply status filters
        if filterby == 'active':
            domain += [('state', 'not in', ['completed', 'cancelled'])]
        elif filterby == 'completed':
            domain += [('state', 'in', ['completed', 'done'])]

        return domain

    # ============================================================================
    # NOTIFICATION METHODS
    # ============================================================================
    def _send_work_order_notification(self, work_order, message_type='update'):
        """Send notification about work order updates"""
        if not work_order.partner_id:
            return False

        template_mapping = {
            'update': 'records_management.work_order_status_update_template',
            'completion': 'records_management.work_order_completion_template',
            'delay': 'records_management.work_order_delay_template',
        }

        template = request.env.ref(template_mapping.get(message_type), False)
        if template:
            template.send_mail(work_order.id, force_send=True)
            return True
        return False

    def _create_portal_activity(self, work_order, activity_type='follow_up'):
        """Create portal activity for work order"""
        activity_types = {
            'follow_up': request.env.ref('mail.mail_activity_data_todo'),
            'call': request.env.ref('mail.mail_activity_data_call'),
            'meeting': request.env.ref('mail.mail_activity_data_meeting'),
        }

        activity_type_id = activity_types.get(activity_type)
        if not activity_type_id:
            return False

        values = {
            "activity_type_id": activity_type_id.id,
            "res_id": work_order.id,
            "res_model_id": request.env["ir.model"]._get(work_order._name).id,
            "user_id": work_order.user_id.id or request.env.user.id,
            "summary": _(
                "Follow up on work order: %s",
                work_order.name,
            ),
            "note": _("Customer portal activity for work order follow-up"),
        }

        return request.env['mail.activity'].create(values)

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def _format_work_order_data(self, work_order, model_name):
        """Format work order data for portal display"""
        return {
            'id': work_order.id,
            'name': work_order.name or _('Draft'),
            'display_name': work_order.display_name,
            'state': work_order.state,
            'priority': work_order.priority or '1',
            'scheduled_date': work_order.scheduled_date,
            'completion_date': getattr(work_order, 'completion_date', None),
            'assigned_technician': getattr(work_order, 'assigned_technician', None),
            'description': work_order.description or '',
            'partner_id': work_order.partner_id,
            'company_id': work_order.company_id,
            'portal_url': '/my/work_order/%s/%s' % (model_name, work_order.id),
            'access_token': getattr(work_order, 'access_token', ''),
        }

    def _get_work_order_status_badge(self, state):
        """Get Bootstrap badge class for work order status"""
        status_mapping = {
            'draft': 'secondary',
            'confirmed': 'primary',
            'in_progress': 'warning',
            'completed': 'success',
            'cancelled': 'danger',
            'on_hold': 'info',
        }
        return status_mapping.get(state, 'secondary')

    def _get_work_order_priority_label(self, priority):
        """Get human-readable priority label"""
        priority_mapping = {
            '0': _('Low'),
            '1': _('Normal'),
            '2': _('High'),
            '3': _('Urgent'),
        }
        return priority_mapping.get(str(priority), _('Normal'))

    # ============================================================================
    # EXPORT AND DOWNLOAD METHODS
    # ============================================================================
    @http.route(['/my/work_order/<string:model>/<int:order_id>/download'],
                type='http', auth="user", website=True)
    def portal_work_order_download(self, model, order_id, access_token=None, **kw):
        """Download work order documents"""
        try:
            work_order = self._check_work_order_access(model, order_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # Generate work order report
        report = request.env.ref('records_management.work_order_report')
        if report:
            # Correct signature: _render_qweb_pdf(report_ref, res_ids, data=None)
            pdf_content, content_type = request.env['ir.actions.report']._render_qweb_pdf(
                report.report_name, [work_order.id]
            )
            pdf_name = _("Work_Order_%s.pdf") % work_order.name

            return request.make_response(
                pdf_content,
                headers=[
                    ('Content-Type', content_type),
                    ('Content-Disposition', 'attachment; filename=%s' % pdf_name)
                ]
            )

        return request.redirect('/my/work_orders')

    def _get_work_order_attachments(self, work_order):
        """Get attachments for work order"""
        return request.env['ir.attachment'].search([
            ('res_model', '=', work_order._name),
            ('res_id', '=', work_order.id)
        ])
