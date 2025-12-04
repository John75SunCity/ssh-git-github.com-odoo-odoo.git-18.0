# -*- coding: utf-8 -*-
"""
Portal Additional Features Controller
Provides routes for Mobile, E-learning, and Compliance features
"""

from odoo import http, fields, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalFeaturesController(CustomerPortal):
    """
    Controller for additional portal features:
    - Mobile interface
    - E-learning/Training
    - Compliance/Audit
    """

    # ============================================================================
    # MOBILE INTERFACE ROUTES
    # ============================================================================

    @http.route(['/my/mobile'], type='http', auth="user", website=True)
    def portal_mobile_dashboard(self, **kw):
        """Mobile-optimized dashboard"""
        values = self._prepare_portal_layout_values()
        
        partner = request.env.user.partner_id
        
        # Get summary counts for mobile dashboard
        Container = request.env['records.container'].sudo()
        Request = request.env['portal.request'].sudo()
        
        values.update({
            'container_count': Container.search_count([('partner_id', '=', partner.id)]),
            'pending_requests': Request.search_count([
                ('partner_id', '=', partner.id),
                ('state', 'in', ['draft', 'submitted', 'in_progress'])
            ]),
            'page_name': 'mobile',
        })
        
        return request.render('records_management.portal_mobile_template', values)

    @http.route(['/my/mobile/inventory'], type='http', auth="user", website=True)
    def portal_mobile_inventory(self, **kw):
        """Mobile inventory browser"""
        values = self._prepare_portal_layout_values()
        
        partner = request.env.user.partner_id
        Container = request.env['records.container'].sudo()
        
        containers = Container.search([
            ('partner_id', '=', partner.id)
        ], limit=50, order='write_date desc')
        
        values.update({
            'containers': containers,
            'page_name': 'mobile_inventory',
        })
        
        return request.render('records_management.portal_mobile_inventory_browser', values)

    @http.route(['/my/mobile/settings'], type='http', auth="user", website=True)
    def portal_mobile_settings(self, **kw):
        """Mobile settings page"""
        values = self._prepare_portal_layout_values()
        
        values.update({
            'page_name': 'mobile_settings',
        })
        
        return request.render('records_management.portal_mobile_settings', values)

    @http.route(['/my/mobile/export'], type='http', auth="user", website=True)
    def portal_mobile_export(self, **kw):
        """Mobile export interface"""
        values = self._prepare_portal_layout_values()
        
        values.update({
            'page_name': 'mobile_export',
        })
        
        return request.render('records_management.portal_mobile_export', values)

    @http.route(['/my/mobile/work-order/create'], type='http', auth="user", website=True)
    def portal_mobile_work_order_create(self, **kw):
        """Mobile work order creation"""
        values = self._prepare_portal_layout_values()
        
        partner = request.env.user.partner_id
        Container = request.env['records.container'].sudo()
        
        values.update({
            'containers': Container.search([('partner_id', '=', partner.id)], limit=100),
            'page_name': 'mobile_work_order',
        })
        
        return request.render('records_management.portal_mobile_work_order_create', values)

    # ============================================================================
    # E-LEARNING / TRAINING ROUTES
    # ============================================================================

    @http.route(['/my/training'], type='http', auth="user", website=True)
    def portal_training_dashboard(self, **kw):
        """Training courses dashboard"""
        values = self._prepare_portal_layout_values()
        
        # Get training courses if model exists
        ElearningCourse = request.env.get('elearning.course')
        courses = []
        
        if ElearningCourse:
            courses = ElearningCourse.sudo().search([
                ('active', '=', True),
                ('is_published', '=', True)
            ])
        
        values.update({
            'courses': courses,
            'page_name': 'training',
        })
        
        return request.render('records_management.portal_elearning_courses', values)

    @http.route(['/my/training/course/<int:course_id>'], type='http', auth="user", website=True)
    def portal_training_course(self, course_id, **kw):
        """Training course detail"""
        values = self._prepare_portal_layout_values()
        
        ElearningCourse = request.env.get('elearning.course')
        course = None
        
        if ElearningCourse:
            course = ElearningCourse.sudo().browse(course_id)
        
        values.update({
            'course': course,
            'page_name': 'training_course',
        })
        
        return request.render('records_management.portal_elearning_course', values)

    @http.route(['/my/training/progress'], type='http', auth="user", website=True)
    def portal_training_progress(self, **kw):
        """User's training progress"""
        values = self._prepare_portal_layout_values()
        
        values.update({
            'page_name': 'training_progress',
        })
        
        return request.render('records_management.portal_elearning_progress', values)

    @http.route(['/my/training/certificates'], type='http', auth="user", website=True)
    def portal_training_certificates(self, **kw):
        """User's training certificates"""
        values = self._prepare_portal_layout_values()
        
        values.update({
            'page_name': 'training_certificates',
        })
        
        return request.render('records_management.portal_training_certificates', values)

    # ============================================================================
    # COMPLIANCE / AUDIT ROUTES
    # ============================================================================

    @http.route(['/my/compliance'], type='http', auth="user", website=True)
    def portal_compliance_dashboard(self, **kw):
        """Compliance status dashboard"""
        values = self._prepare_portal_layout_values()
        
        partner = request.env.user.partner_id
        
        # Get compliance-related data
        NaidCertificate = request.env['naid.certificate'].sudo()
        ChainOfCustody = request.env['chain.of.custody'].sudo()
        
        certificates = NaidCertificate.search([
            ('partner_id', '=', partner.id)
        ], limit=10, order='create_date desc')
        
        custody_records = ChainOfCustody.search([
            ('partner_id', '=', partner.id)
        ], limit=20, order='create_date desc')
        
        values.update({
            'certificates': certificates,
            'custody_records': custody_records,
            'page_name': 'compliance',
        })
        
        return request.render('records_management.portal_compliance_status', values)

    @http.route(['/my/compliance/audit-logs'], type='http', auth="user", website=True)
    def portal_audit_logs(self, **kw):
        """Audit logs for customer"""
        values = self._prepare_portal_layout_values()
        
        partner = request.env.user.partner_id
        
        # Get audit logs
        NaidAuditLog = request.env['naid.audit.log'].sudo()
        
        logs = NaidAuditLog.search([
            ('partner_id', '=', partner.id)
        ], limit=50, order='create_date desc')
        
        values.update({
            'audit_logs': logs,
            'page_name': 'audit_logs',
        })
        
        return request.render('records_management.portal_audit_logs', values)

    @http.route(['/my/compliance/custody-log'], type='http', auth="user", website=True)
    def portal_custody_log(self, **kw):
        """Chain of custody log"""
        values = self._prepare_portal_layout_values()
        
        partner = request.env.user.partner_id
        
        ChainOfCustody = request.env['chain.of.custody'].sudo()
        
        custody_records = ChainOfCustody.search([
            ('partner_id', '=', partner.id)
        ], limit=100, order='create_date desc')
        
        values.update({
            'custody_records': custody_records,
            'page_name': 'custody_log',
        })
        
        return request.render('records_management.portal_custody_log', values)

    # ============================================================================
    # PROFILE / SETTINGS ROUTES
    # ============================================================================

    @http.route(['/my/profile'], type='http', auth="user", website=True)
    def portal_profile(self, **kw):
        """User profile page"""
        values = self._prepare_portal_layout_values()
        
        values.update({
            'page_name': 'profile',
        })
        
        return request.render('records_management.portal_profile', values)

    @http.route(['/my/settings'], type='http', auth="user", website=True)
    def portal_settings(self, **kw):
        """User settings page"""
        values = self._prepare_portal_layout_values()
        
        values.update({
            'page_name': 'settings',
        })
        
        return request.render('records_management.portal_settings', values)

    @http.route(['/my/search'], type='http', auth="user", website=True)
    def portal_search_results(self, q='', **kw):
        """Global search results"""
        values = self._prepare_portal_layout_values()
        
        partner = request.env.user.partner_id
        results = []
        
        if q and len(q) >= 3:
            # Search containers
            Container = request.env['records.container'].sudo()
            containers = Container.search([
                ('partner_id', '=', partner.id),
                '|', '|',
                ('name', 'ilike', q),
                ('barcode', 'ilike', q),
                ('description', 'ilike', q)
            ], limit=20)
            
            for c in containers:
                results.append({
                    'type': 'container',
                    'name': c.name,
                    'description': c.description or '',
                    'url': '/my/containers/%s' % c.id,
                })
            
            # Search documents
            Document = request.env['records.document'].sudo()
            documents = Document.search([
                ('partner_id', '=', partner.id),
                '|',
                ('name', 'ilike', q),
                ('barcode', 'ilike', q)
            ], limit=20)
            
            for d in documents:
                results.append({
                    'type': 'document',
                    'name': d.name,
                    'description': d.document_type_id.name if d.document_type_id else '',
                    'url': '/my/documents/%s' % d.id,
                })
        
        values.update({
            'query': q,
            'results': results,
            'page_name': 'search',
        })
        
        return request.render('records_management.portal_search_results', values)

    # ============================================================================
    # SUPPORT ROUTES
    # ============================================================================

    @http.route(['/my/support'], type='http', auth="user", website=True)
    def portal_support_tickets(self, **kw):
        """Support tickets list"""
        values = self._prepare_portal_layout_values()
        
        values.update({
            'page_name': 'support',
        })
        
        return request.render('records_management.portal_support_tickets', values)
