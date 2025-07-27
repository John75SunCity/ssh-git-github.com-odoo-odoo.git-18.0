# -*- coding: utf-8 -*-
"""
Records Management Bale System - Simple Internal Operations
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class RecordsManagementBale(models.Model):
    """
    Records Management Bale System
    Simple internal tracking of shredded paper waste baling
    """

    _name = "records.management.bale"
    _description = "Records Management Bale"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "creation_date desc, name"
    _rec_name = "name"

    # ==========================================
    # CORE IDENTIFICATION FIELDS
    # ==========================================
    name = fields.Char(string="Bale Number", required=True, tracking=True,
                      default=lambda self: _('New'), copy=False)
    notes = fields.Text(string="Notes")
    company_id = fields.Many2one('res.company', string='Company',
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Bale Operator',
                             default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True)

    # ==========================================
    # BASIC BALE INFO
    # ==========================================
    creation_date = fields.Date(string='Bale Date', 
                               default=fields.Date.today, required=True, tracking=True)
    
    # Weight measurements - just the basics
    estimated_weight = fields.Float(string='Estimated Weight (lbs)', tracking=True)
    actual_weight = fields.Float(string='Actual Weight (lbs)', tracking=True)

    # ==========================================
    # SIMPLE STATUS WORKFLOW
    # ==========================================
    state = fields.Selection([
        ('baling', 'Baling'),
        ('completed', 'Completed'),
        ('shipped', 'Shipped')
    ], string='Status', default='baling', tracking=True, required=True)

    # ==========================================
    # STORAGE LOCATION
    # ==========================================
    storage_location_id = fields.Many2one('records.location', string='Storage Location', tracking=True)

    # ==========================================
    # WORKFLOW ACTION METHODS
    # ==========================================
    def action_complete_baling(self):
        """Complete baling process"""
        self.ensure_one()
        if self.state != 'baling':
            raise UserError(_('Only baling status can be completed'))
        
        if not self.actual_weight:
            raise UserError(_('Actual weight must be recorded'))
        
        self.write({'state': 'completed'})
        self.message_post(body=_('Baling completed'))

    def action_ship_bale(self):
        """Ship bale for recycling"""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_('Only completed bales can be shipped'))
        
        self.write({'state': 'shipped'})
        self.message_post(body=_('Bale shipped for recycling'))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence number"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.management.bale') or _('New')
        return super().create(vals_list)

    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    @api.constrains('estimated_weight', 'actual_weight')
    def _check_weights(self):
        """Validate weight constraints"""
        for record in self:
            if record.estimated_weight and record.estimated_weight < 0:
                raise ValidationError(_('Estimated weight cannot be negative'))
            if record.actual_weight and record.actual_weight < 0:
                raise ValidationError(_('Actual weight cannot be negative'))