# -*- coding: utf-8 -*-
"""
Partner Bin Key Management - Simple Key Tracking
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PartnerBinKey(models.Model):
    """
    Partner Bin Key Management
    Simple tracking of who has which generic physical keys
    """
    
    _name = 'partner.bin.key'
    _description = 'Partner Bin Key Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = "name"
    
    # ==========================================
    # CORE IDENTIFICATION FIELDS
    # ==========================================
    name = fields.Char(string='Key ID', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Responsible User', 
                             default=lambda self: self.env.user, tracking=True)

    # ==========================================
    # KEY ASSIGNMENT
    # ==========================================
    partner_id = fields.Many2one('res.partner', string='Customer', 
                                required=True, tracking=True,
                                domain=[('is_company', '=', True)])
    assigned_to_contact = fields.Many2one('res.partner', string='Assigned To',
                                         domain=[('is_company', '=', False)], tracking=True)
    
    # ==========================================
    # BASIC STATUS
    # ==========================================
    state = fields.Selection([
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('lost', 'Lost'),
        ('returned', 'Returned')
    ], string='Status', default='available', tracking=True, required=True)
    
    # ==========================================
    # TRACKING DATES
    # ==========================================
    assignment_date = fields.Date(string='Assignment Date', tracking=True)
    return_date = fields.Date(string='Return Date', tracking=True)
    
    # ==========================================
    # NOTES
    # ==========================================
    notes = fields.Text(string='Notes', tracking=True)
    
    # ==========================================
    # WORKFLOW ACTION METHODS
    # ==========================================
    def action_assign_key(self):
        """Assign key to contact"""
        self.ensure_one()
        if self.state != 'available':
            raise UserError(_('Only available keys can be assigned'))
        
        if not self.assigned_to_contact:
            raise UserError(_('Contact must be specified for assignment'))
        
        self.write({
            'state': 'assigned',
            'assignment_date': fields.Date.today()
        })
        
        self.message_post(body=_('Key assigned to %s') % self.assigned_to_contact.name)
    
    def action_return_key(self):
        """Return key"""
        self.ensure_one()
        if self.state != 'assigned':
            raise UserError(_('Only assigned keys can be returned'))
        
        self.write({
            'state': 'returned',
            'return_date': fields.Date.today()
        })
        
        self.message_post(body=_('Key returned by %s') % self.assigned_to_contact.name)
    
    def action_report_lost(self):
        """Report key as lost"""
        self.ensure_one()
        self.write({'state': 'lost'})
        self.message_post(body=_('Key reported as lost'))
    
    def action_make_available(self):
        """Make key available again"""
        self.ensure_one()
        self.write({
            'state': 'available',
            'assigned_to_contact': False,
            'assignment_date': False,
            'return_date': False
        })
        self.message_post(body=_('Key made available'))
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence number if needed"""
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('partner.bin.key') or _('New Key')
        return super().create(vals_list)
