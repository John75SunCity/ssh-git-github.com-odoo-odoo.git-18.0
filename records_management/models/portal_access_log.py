# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PortalAccessLog(models.Model):
    """Audit log for tracking admin access to customer portal accounts"""
    _name = 'portal.access.log'
    _description = 'Portal Access Audit Log'
    _order = 'access_date desc'
    _rec_name = 'display_name'
    
    admin_user_id = fields.Many2one(
        'res.users',
        string='Admin User',
        required=True,
        ondelete='restrict',
        help="Internal user who accessed the portal account"
    )
    
    portal_user_id = fields.Many2one(
        'res.users',
        string='Portal User',
        required=True,
        ondelete='cascade',
        help="Portal user account that was accessed"
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ondelete='cascade',
        help="Customer whose portal was accessed"
    )
    
    access_date = fields.Datetime(
        string='Access Date',
        required=True,
        default=fields.Datetime.now,
        help="When the portal account was accessed"
    )
    
    ip_address = fields.Char(
        string='IP Address',
        help="IP address from which the access was made"
    )
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    @api.depends('admin_user_id', 'partner_id', 'access_date')
    def _compute_display_name(self):
        for log in self:
            log.display_name = '%s accessed %s on %s' % (
                log.admin_user_id.name,
                log.partner_id.name,
                log.access_date.strftime('%Y-%m-%d %H:%M:%S') if log.access_date else ''
            )
