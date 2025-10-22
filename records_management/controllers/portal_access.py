# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError
from odoo.addons.web.controllers.home import Home
import werkzeug


class PortalAccessController(http.Controller):
    
    @http.route(['/portal/access/<string:token>'], type='http', auth='user', website=True)
    def portal_access_login(self, token, **kwargs):
        """
        Secure portal access endpoint using token authentication
        Admin users can access customer portal accounts via this route
        """
        # Verify current user has permission
        if not request.env.user.can_access_portal_accounts:
            return request.render('records_management.portal_access_denied', {
                'error': _("You are not authorized to access customer portal accounts.")
            })
        
        # Find and validate token
        access_token = request.env['portal.access.token'].sudo().search([
            ('token', '=', token)
        ], limit=1)
        
        if not access_token or not access_token.is_valid():
            return request.render('records_management.portal_access_denied', {
                'error': _("Invalid or expired access token. Please generate a new one.")
            })
        
        # Mark token as used
        access_token.sudo().write({
            'used': True,
            'used_date': http.request.env['ir.qweb.field.datetime'].now()
        })
        
        # Get target portal user
        portal_user = access_token.user_id
        
        # Log the access for audit trail
        request.env['portal.access.log'].sudo().create({
            'admin_user_id': request.env.user.id,
            'portal_user_id': portal_user.id,
            'partner_id': portal_user.partner_id.id,
            'access_date': http.request.env['ir.qweb.field.datetime'].now(),
            'ip_address': request.httprequest.remote_addr,
        })
        
        # Switch to portal user session
        request.session.uid = portal_user.id
        request.session.login = portal_user.login
        request.session.session_token = portal_user._compute_session_token(request.session.sid)
        
        # Store original admin user ID in session for easy switch back
        request.session['original_admin_uid'] = request.env.user.id
        
        # Redirect to portal home
        return werkzeug.utils.redirect('/my/home')
    
    @http.route(['/portal/switch_back'], type='http', auth='user', website=True)
    def portal_switch_back_to_admin(self, **kwargs):
        """
        Switch back from portal user to original admin account
        """
        original_uid = request.session.get('original_admin_uid')
        
        if not original_uid:
            return werkzeug.utils.redirect('/web')
        
        # Get original admin user
        admin_user = request.env['res.users'].sudo().browse(original_uid)
        
        if not admin_user.exists():
            return werkzeug.utils.redirect('/web')
        
        # Switch back to admin
        request.session.uid = admin_user.id
        request.session.login = admin_user.login
        request.session.session_token = admin_user._compute_session_token(request.session.sid)
        
        # Clear original admin UID
        request.session.pop('original_admin_uid', None)
        
        # Redirect to backend
        return werkzeug.utils.redirect('/web')


class PortalAccessLog(http.Controller):
    """Audit log for portal account access"""
    _name = 'portal.access.log'
    _description = 'Portal Access Log'
    _order = 'access_date desc'
    
    admin_user_id = http.request.env['res.users']
    portal_user_id = http.request.env['res.users']
    partner_id = http.request.env['res.partner']
    access_date = http.request.env['ir.qweb.field.datetime']
    ip_address = http.request.env['ir.qweb.field']
