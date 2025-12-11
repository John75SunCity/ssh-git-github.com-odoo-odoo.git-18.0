# -*- coding: utf-8 -*-
"""
Destruction & Shredding Portal Dashboard

Comprehensive portal for all destruction and shredding services including:
- Recurring bin service management
- One-time shredding requests (boxes, bags, totes, purge)
- Certificates of destruction with full audit trail
- Service history tied to jobs, quotes, and invoices

Author: Records Management System
Version: 18.0.1.0.27
"""

from datetime import datetime, timedelta
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class DestructionPortalController(CustomerPortal):
    """Unified Destruction & Shredding Portal Dashboard"""

    def _get_destruction_dashboard_data(self, partner):
        """
        Gather all destruction-related data for the dashboard.
        
        Returns dict with:
        - bins: Active shredding service bins
        - pending_requests: Open destruction/shredding requests
        - certificates: Recent destruction certificates
        - work_orders: Recent shredding work orders
        - service_history: Completed services with invoice links
        - stats: Summary statistics
        """
        user = request.env.user

        # =====================================================================
        # 1. SHREDDING BINS (Recurring Service)
        # =====================================================================
        ShreddingBin = request.env['shredding.service.bin'].sudo()
        bins = ShreddingBin.search([
            ('current_customer_id', '=', partner.commercial_partner_id.id),
            ('active', '=', True)
        ], order='next_service_date asc')

        bins_data = []
        for bin in bins:
            bins_data.append({
                'id': bin.id,
                'barcode': bin.barcode,
                'bin_size': bin.bin_size,
                'bin_size_display': dict(bin._fields['bin_size'].selection).get(bin.bin_size, bin.bin_size),
                'location': bin.current_department_id.name if bin.current_department_id else _('Main Office'),
                'next_service_date': bin.next_service_date,
                'service_frequency': bin.service_frequency if hasattr(bin, 'service_frequency') else 'weekly',
                'last_service_date': bin.last_service_date,
                'status': 'due' if bin.next_service_date and bin.next_service_date <= datetime.now().date() else 'scheduled',
            })

        # =====================================================================
        # 2. PENDING DESTRUCTION REQUESTS
        # =====================================================================
        PortalRequest = request.env['portal.request'].sudo()
        pending_requests = PortalRequest.search([
            ('partner_id', '=', partner.commercial_partner_id.id),
            ('request_type', 'in', ['destruction', 'shredding', 'purge']),
            ('state', 'in', ['draft', 'submitted', 'approved', 'scheduled'])
        ], order='create_date desc', limit=20)

        # =====================================================================
        # 3. FSM TASKS (Scheduled Services via Odoo FSM)
        # All services are scheduled through FSM - this is the source of truth
        # =====================================================================
        FsmTask = request.env['project.task'].sudo()

        # Get all shredding/destruction FSM tasks for this customer
        fsm_domain = [
            ('partner_id', '=', partner.commercial_partner_id.id),
            ('is_fsm', '=', True),
            '|', '|', '|', '|',
            ('name', 'ilike', 'shred'),
            ('name', 'ilike', 'destruction'),
            ('service_type', 'in', ['on_site_shredding', 'off_site_shredding', 'hard_drive_destruction', 'product_destruction']),
            ('shredding_work_order_id', '!=', False),
            ('destruction_work_order_id', '!=', False)
        ]

        # Check if service_type field exists
        if 'service_type' not in FsmTask._fields:
            fsm_domain = [
                ('partner_id', '=', partner.commercial_partner_id.id),
                ('is_fsm', '=', True),
                '|', '|',
                ('name', 'ilike', 'shred'),
                ('name', 'ilike', 'destruction'),
                ('shredding_work_order_id', '!=', False),
            ]

        fsm_tasks = FsmTask.search(fsm_domain, order='date_deadline desc', limit=50)

        # Split into scheduled vs completed
        scheduled_fsm_tasks = fsm_tasks.filtered(lambda t: not t.stage_id.fold)
        completed_fsm_tasks = fsm_tasks.filtered(lambda t: t.stage_id.fold)

        # =====================================================================
        # 3b. SHREDDING WORK ORDERS (Supplemental data linked to FSM)
        # =====================================================================
        WorkOrderShredding = request.env['work.order.shredding'].sudo()
        work_orders = WorkOrderShredding.search([
            ('partner_id', '=', partner.commercial_partner_id.id)
        ], order='scheduled_date desc', limit=20)

        active_work_orders = work_orders.filtered(lambda w: w.state not in ['completed', 'verified', 'invoiced', 'cancelled'])
        completed_work_orders = work_orders.filtered(lambda w: w.state in ['completed', 'verified', 'invoiced'])

        # =====================================================================
        # 4. DESTRUCTION CERTIFICATES
        # =====================================================================
        NaidCertificate = request.env['naid.certificate'].sudo()
        certificates = NaidCertificate.search([
            ('partner_id', '=', partner.commercial_partner_id.id)
        ], order='destruction_date desc', limit=50)

        # Also check destruction.certificate model if different
        DestructionCertificate = request.env['destruction.certificate'].sudo()
        if DestructionCertificate._name != NaidCertificate._name:
            destruction_certs = DestructionCertificate.search([
                ('partner_id', '=', partner.commercial_partner_id.id)
            ], order='destruction_date desc', limit=50)
        else:
            destruction_certs = request.env['destruction.certificate'].browse()

        # Combine and format certificates
        all_certificates = []
        for cert in certificates:
            all_certificates.append({
                'id': cert.id,
                'model': 'naid.certificate',
                'certificate_number': cert.certificate_number,
                'destruction_date': cert.destruction_date,
                'issue_date': cert.issue_date,
                'state': cert.state if hasattr(cert, 'state') else 'issued',
                'fsm_task_id': cert.fsm_task_id.id if cert.fsm_task_id else None,
                'fsm_task_name': cert.fsm_task_id.name if cert.fsm_task_id else None,
                'has_pdf': True,  # Assume downloadable
            })

        for cert in destruction_certs:
            all_certificates.append({
                'id': cert.id,
                'model': 'destruction.certificate',
                'certificate_number': cert.certificate_number if hasattr(cert, 'certificate_number') else cert.name,
                'destruction_date': cert.destruction_date if hasattr(cert, 'destruction_date') else cert.date,
                'issue_date': cert.create_date,
                'state': cert.state if hasattr(cert, 'state') else 'issued',
                'has_pdf': True,
            })

        # Sort by date descending
        all_certificates.sort(key=lambda x: x['destruction_date'] or datetime.min, reverse=True)

        # =====================================================================
        # 5. SERVICE HISTORY (FSM Tasks + Work Orders with Invoice Links)
        # FSM tasks are the primary source; work orders provide extra detail
        # =====================================================================
        service_history = []
        processed_task_ids = set()  # Track which FSM tasks we've already added

        # First, add completed FSM tasks with their linked work order data
        for task in completed_fsm_tasks:
            # Find linked work order for additional details
            wo = None
            if hasattr(task, 'shredding_work_order_id') and task.shredding_work_order_id:
                wo = task.shredding_work_order_id
            else:
                # Try to find via reverse lookup
                wo = work_orders.filtered(lambda w: w.fsm_task_id.id == task.id)[:1]

            # Find linked invoice via sale order or work order
            invoice = None
            invoice_name = None
            if hasattr(task, 'sale_order_id') and task.sale_order_id:
                invoices = task.sale_order_id.invoice_ids.filtered(lambda i: i.state == 'posted')
                if invoices:
                    invoice = invoices[0]
                    invoice_name = invoice.name
            elif wo and wo.invoice_id:
                invoice = wo.invoice_id
                invoice_name = invoice.name

            # Get certificate
            certificate = None
            if wo and wo.certificate_id:
                certificate = wo.certificate_id
            elif hasattr(task, 'destruction_certificate_id') and task.destruction_certificate_id:
                certificate = task.destruction_certificate_id

            service_history.append({
                'id': task.id,
                'type': 'fsm_task',
                'model': 'project.task',
                'name': task.name,
                'date': task.date_deadline or task.create_date,
                'material_type': wo.material_type if wo else (task.material_type if hasattr(task, 'material_type') else None),
                'weight': wo.actual_weight or wo.estimated_weight if wo else (task.weight_processed if hasattr(task, 'weight_processed') else None),
                'boxes_count': wo.boxes_count if wo else None,
                'state': 'completed',
                'invoice_id': invoice.id if invoice else None,
                'invoice_name': invoice_name,
                'certificate_id': certificate.id if certificate else None,
                'certificate_number': certificate.certificate_number if certificate else None,
                'fsm_task_id': task.id,
                'work_order_id': wo.id if wo else None,
            })
            processed_task_ids.add(task.id)

        # Add any completed work orders that aren't linked to FSM tasks (legacy data)
        for wo in completed_work_orders:
            if wo.fsm_task_id and wo.fsm_task_id.id in processed_task_ids:
                continue  # Already added via FSM task

            service_history.append({
                'id': wo.id,
                'type': 'work_order',
                'model': 'work.order.shredding',
                'name': wo.name,
                'date': wo.completion_date or wo.scheduled_date,
                'material_type': wo.material_type,
                'weight': wo.actual_weight or wo.estimated_weight,
                'boxes_count': wo.boxes_count,
                'state': wo.state,
                'invoice_id': wo.invoice_id.id if wo.invoice_id else None,
                'invoice_name': wo.invoice_id.name if wo.invoice_id else None,
                'certificate_id': wo.certificate_id.id if wo.certificate_id else None,
                'certificate_number': wo.certificate_id.certificate_number if wo.certificate_id else None,
                'fsm_task_id': wo.fsm_task_id.id if wo.fsm_task_id else None,
                'work_order_id': wo.id,
            })

        # Sort service history by date
        service_history.sort(key=lambda x: x['date'] or datetime.min, reverse=True)

        # =====================================================================
        # 6. STATISTICS
        # =====================================================================
        stats = {
            'active_bins': len(bins),
            'bins_due_soon': len([b for b in bins_data if b['status'] == 'due']),
            'pending_requests': len(pending_requests),
            'scheduled_services': len(scheduled_fsm_tasks),  # FSM tasks waiting to be done
            'active_work_orders': len(active_work_orders),
            'certificates_ytd': len([c for c in all_certificates
                                    if c['destruction_date'] and
                                    c['destruction_date'].year == datetime.now().year]),
            'total_certificates': len(all_certificates),
            'completed_services_30d': len([s for s in service_history
                                          if s['date'] and
                                          s['date'] > datetime.now() - timedelta(days=30)]),
        }

        return {
            'bins': bins_data,
            'bins_records': bins,
            'pending_requests': pending_requests,
            'scheduled_fsm_tasks': scheduled_fsm_tasks,  # NEW: Scheduled FSM services
            'active_work_orders': active_work_orders,
            'completed_work_orders': completed_work_orders,
            'certificates': all_certificates[:20],  # Limit for dashboard
            'all_certificates_count': len(all_certificates),
            'service_history': service_history[:20],  # Limit for dashboard
            'stats': stats,
        }

    # =========================================================================
    # MAIN DESTRUCTION DASHBOARD
    # =========================================================================
    @http.route(['/my/shredding', '/my/shredding/dashboard'], type='http', auth='user', website=True)
    def portal_shredding_dashboard(self, tab='overview', **kw):
        """
        Main Shredding & Destruction Dashboard
        
        Tabs:
        - overview: Summary cards and quick actions
        - bins: Shredding bin service management
        - requests: One-time shredding requests
        - certificates: Destruction certificates
        - history: Service history with audit trail
        """
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        # Get all destruction data
        data = self._get_destruction_dashboard_data(partner)

        values.update({
            'page_name': 'shredding_dashboard',
            'active_tab': tab,
            **data,
            'can_request_service': True,  # Permission check could go here
            'partner': partner,
        })

        return request.render("records_management.portal_shredding_dashboard", values)

    # =========================================================================
    # BIN SERVICE ROUTES
    # =========================================================================
    @http.route(['/my/shredding/bins'], type='http', auth='user', website=True)
    def portal_shredding_bins(self, **kw):
        """List all shredding bins for this customer"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        ShreddingBin = request.env['shredding.service.bin'].sudo()
        bins = ShreddingBin.search([
            ('current_customer_id', '=', partner.commercial_partner_id.id),
            ('active', '=', True)
        ], order='next_service_date asc')

        values.update({
            'page_name': 'shredding_bins',
            'bins': bins,
            'partner': partner,
        })

        return request.render("records_management.portal_shredding_bins", values)

    @http.route(['/my/shredding/bin/<int:bin_id>'], type='http', auth='user', website=True)
    def portal_shredding_bin_detail(self, bin_id, **kw):
        """View single bin details and service history"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        ShreddingBin = request.env['shredding.service.bin'].sudo()
        bin_record = ShreddingBin.browse(bin_id)

        # Security check
        if not bin_record.exists() or bin_record.current_customer_id.id != partner.commercial_partner_id.id:
            return request.redirect('/my/shredding/bins')

        # Get service events for this bin
        service_events = []
        if hasattr(bin_record, 'service_event_ids'):
            service_events = bin_record.service_event_ids.sorted(key=lambda e: e.service_date, reverse=True)

        values.update({
            'page_name': 'shredding_bin_detail',
            'bin': bin_record,
            'service_events': service_events,
            'partner': partner,
        })

        return request.render("records_management.portal_shredding_bin_detail", values)

    @http.route(['/my/shredding/bin/<int:bin_id>/request-service'], type='http',
                auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def portal_request_bin_service(self, bin_id, **post):
        """Request extra/emergency bin service"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        ShreddingBin = request.env['shredding.service.bin'].sudo()
        bin_record = ShreddingBin.browse(bin_id)

        # Security check
        if not bin_record.exists() or bin_record.current_customer_id.id != partner.commercial_partner_id.id:
            return request.redirect('/my/shredding/bins')

        if request.httprequest.method == 'POST':
            # Create service request
            PortalRequest = request.env['portal.request'].sudo()
            new_request = PortalRequest.create({
                'partner_id': partner.commercial_partner_id.id,
                'request_type': 'shredding',
                'name': _('Extra Bin Service Request - %s') % bin_record.barcode,
                'description': post.get('notes', ''),
                'requested_date': post.get('preferred_date') or False,
                'state': 'submitted',
            })

            return request.redirect('/my/shredding/dashboard?tab=requests&success=1')

        values.update({
            'page_name': 'request_bin_service',
            'bin': bin_record,
            'partner': partner,
        })

        return request.render("records_management.portal_shredding_bins", values)

    # =========================================================================
    # SHREDDING REQUEST ROUTES
    # =========================================================================
    @http.route(['/my/shredding/request/new'], type='http', auth='user', website=True,
                methods=['GET', 'POST'], csrf=True)
    def portal_new_shredding_request(self, **post):
        """
        Create new shredding request for:
        - Boxes of documents
        - Bags of documents
        - Totes/containers
        - Purge/cleanout services
        """
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        if request.httprequest.method == 'POST':
            # Create shredding request
            PortalRequest = request.env['portal.request'].sudo()

            material_type = post.get('material_type', 'paper')
            container_type = post.get('container_type', 'boxes')
            quantity = int(post.get('quantity', 1))

            new_request = PortalRequest.create({
                'partner_id': partner.commercial_partner_id.id,
                'request_type': 'shredding',
                'name': _('Shredding Request - %s %s') % (quantity, container_type.title()),
                'description': _("Material Type: %s\nContainer Type: %s\nQuantity: %s\n\nNotes: %s") % (
                    material_type, container_type, quantity, post.get('notes', '')
                ),
                'requested_date': post.get('preferred_date') or False,
                'state': 'submitted',
            })

            return request.redirect('/my/shredding/dashboard?tab=requests&success=1')

        values.update({
            'page_name': 'new_shredding_request',
            'partner': partner,
            'material_types': [
                ('paper', _('Paper Documents')),
                ('hard_drive', _('Hard Drives / Media')),
                ('mixed_media', _('Mixed Media')),
                ('plastic_cards', _('Plastic Cards / IDs')),
            ],
            'container_types': [
                ('boxes', _('Banker Boxes')),
                ('bags', _('Shredding Bags')),
                ('totes', _('Totes / Bins')),
                ('purge', _('Purge / Cleanout')),
            ],
        })

        return request.render("records_management.portal_new_shredding_request", values)

    # =========================================================================
    # CERTIFICATE ROUTES
    # =========================================================================
    @http.route(['/my/shredding/certificates'], type='http', auth='user', website=True)
    def portal_shredding_certificates(self, page=1, search=None, **kw):
        """List all destruction certificates with filtering"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        NaidCertificate = request.env['naid.certificate'].sudo()
        domain = [('partner_id', '=', partner.commercial_partner_id.id)]

        if search:
            domain += ['|', ('name', 'ilike', search), ('certificate_number', 'ilike', search)]

        cert_count = NaidCertificate.search_count(domain)
        pager = request.website.pager(
            url="/my/shredding/certificates",
            url_args={'search': search},
            total=cert_count,
            page=page,
            step=20,
        )

        certificates = NaidCertificate.search(
            domain,
            order='destruction_date desc',
            limit=20,
            offset=pager['offset']
        )

        values.update({
            'page_name': 'shredding_certificates',
            'certificates': certificates,
            'pager': pager,
            'search': search or '',
            'cert_count': cert_count,
            'partner': partner,
        })

        return request.render("records_management.portal_shredding_certificates", values)

    @http.route(['/my/shredding/certificate/<int:cert_id>'], type='http', auth='user', website=True)
    def portal_shredding_certificate_detail(self, cert_id, **kw):
        """View certificate details with linked job/invoice"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        NaidCertificate = request.env['naid.certificate'].sudo()
        certificate = NaidCertificate.browse(cert_id)

        # Security check
        if not certificate.exists() or certificate.partner_id.id != partner.commercial_partner_id.id:
            return request.redirect('/my/shredding/certificates')

        # Get linked records
        linked_records = {
            'fsm_task': certificate.fsm_task_id if certificate.fsm_task_id else None,
            'work_order': None,
            'invoice': None,
            'quote': None,
        }

        # Find linked work order
        WorkOrderShredding = request.env['work.order.shredding'].sudo()
        linked_wo = WorkOrderShredding.search([
            ('certificate_id', '=', certificate.id)
        ], limit=1)
        if linked_wo:
            linked_records['work_order'] = linked_wo
            linked_records['invoice'] = linked_wo.invoice_id

        # If FSM task, try to get sale order/invoice
        if certificate.fsm_task_id:
            task = certificate.fsm_task_id
            if hasattr(task, 'sale_order_id') and task.sale_order_id:
                linked_records['quote'] = task.sale_order_id
                invoices = task.sale_order_id.invoice_ids.filtered(lambda i: i.state == 'posted')
                if invoices:
                    linked_records['invoice'] = invoices[0]

        values.update({
            'page_name': 'shredding_certificate_detail',
            'certificate': certificate,
            'linked_records': linked_records,
            'partner': partner,
        })

        return request.render("records_management.portal_certificate_detail", values)

    @http.route(['/my/shredding/certificate/<int:cert_id>/download'], type='http', auth='user')
    def portal_download_certificate(self, cert_id, **kw):
        """Download certificate PDF"""
        partner = request.env.user.partner_id

        NaidCertificate = request.env['naid.certificate'].sudo()
        certificate = NaidCertificate.browse(cert_id)

        # Security check
        if not certificate.exists() or certificate.partner_id.id != partner.commercial_partner_id.id:
            return request.redirect('/my/shredding/certificates')

        # Generate PDF
        try:
            pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'records_management.report_naid_certificate', [certificate.id]
            )

            filename = "Certificate_%s.pdf" % certificate.certificate_number

            return request.make_response(
                pdf_content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', 'attachment; filename="%s"' % filename),
                ]
            )
        except Exception:
            return request.redirect('/my/shredding/certificate/%s?error=pdf' % cert_id)

    # =========================================================================
    # SCHEDULED SERVICES ROUTES (FSM Tasks)
    # =========================================================================
    @http.route(['/my/shredding/scheduled'], type='http', auth='user', website=True)
    def portal_scheduled_services(self, **kw):
        """View all scheduled shredding/destruction services (FSM Tasks)"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        data = self._get_destruction_dashboard_data(partner)

        values.update({
            'page_name': 'shredding_scheduled',
            'scheduled_tasks': data.get('scheduled_fsm_tasks', []),
            'active_work_orders': data.get('active_work_orders', []),
            'partner': partner,
        })

        return request.render("records_management.portal_scheduled_services", values)

    @http.route(['/my/shredding/service/<int:task_id>'], type='http', auth='user', website=True)
    def portal_service_detail(self, task_id, **kw):
        """View details of a scheduled or completed FSM service"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        FsmTask = request.env['project.task'].sudo()
        task = FsmTask.browse(task_id)

        # Security check
        if not task.exists() or task.partner_id.id != partner.commercial_partner_id.id:
            return request.redirect('/my/shredding/scheduled')

        # Get linked work order
        work_order = None
        WorkOrderShredding = request.env['work.order.shredding'].sudo()
        if hasattr(task, 'shredding_work_order_id') and task.shredding_work_order_id:
            work_order = task.shredding_work_order_id
        else:
            work_order = WorkOrderShredding.search([('fsm_task_id', '=', task.id)], limit=1)

        # Get linked invoice/quote
        invoice = None
        quote = None
        if hasattr(task, 'sale_order_id') and task.sale_order_id:
            quote = task.sale_order_id
            invoices = quote.invoice_ids.filtered(lambda i: i.state == 'posted')
            if invoices:
                invoice = invoices[0]
        elif work_order and work_order.invoice_id:
            invoice = work_order.invoice_id

        # Get certificate
        certificate = None
        if work_order and work_order.certificate_id:
            certificate = work_order.certificate_id
        elif hasattr(task, 'destruction_certificate_id') and task.destruction_certificate_id:
            certificate = task.destruction_certificate_id

        values.update({
            'page_name': 'shredding_service_detail',
            'task': task,
            'work_order': work_order,
            'invoice': invoice,
            'quote': quote,
            'certificate': certificate,
            'partner': partner,
        })

        return request.render("records_management.portal_service_detail", values)

    # =========================================================================
    # SERVICE HISTORY ROUTES
    # =========================================================================
    @http.route(['/my/shredding/history'], type='http', auth='user', website=True)
    def portal_shredding_history(self, page=1, filterby='all', **kw):
        """View complete shredding service history"""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        data = self._get_destruction_dashboard_data(partner)

        values.update({
            'page_name': 'shredding_history',
            'service_history': data['service_history'],
            'filterby': filterby,
            'partner': partner,
        })

        return request.render("records_management.portal_shredding_history", values)
