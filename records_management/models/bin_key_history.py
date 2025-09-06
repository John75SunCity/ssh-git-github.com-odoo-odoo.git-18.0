# -*- coding: utf-8 -*-
"""
Bin Key History Module

Logs all significant events related to the lifecycle of a bin access key,
providing a complete audit trail for NAID compliance.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _

class BinKeyHistory(models.Model):
    """
    Stores historical records of events for each bin key.
    """
    _name = 'bin.key.history'
    _description = 'Bin Key Assignment History'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'event_date desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION & RELATIONSHIPS
    # ============================================================================
    name = fields.Char(
        string='History Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    key_id = fields.Many2one(
        'bin.key',
        string='Key',
        required=True,
        ondelete='cascade',
        index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='key_id.company_id',
        store=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Assigned User',  # Disambiguated from mail.activity's activity_user_id "Responsible User"
        required=True,
        default=lambda self: self.env.user
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Assigned Customer',
        help="The customer to whom the key was assigned at the time of the event."
    )

    # ============================================================================
    # EVENT DETAILS
    # ============================================================================
    event_date = fields.Datetime(
        string='Event Date',
        required=True,
        default=fields.Datetime.now
    )
    event_type = fields.Selection([
        ('create', 'Created'),
        ('assign', 'Assigned'),
        ('return', 'Returned'),
        ('lost', 'Marked as Lost'),
        ('retire', 'Retired'),
        ('update', 'Updated')
    ], string='Event Type', required=True)
    notes = fields.Text(string='Notes')

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides the create method to assign a sequence number for the record name.
        This ensures each history entry has a unique, sequential reference.
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('bin.key.history') or _('New')
        return super().create(vals_list)
