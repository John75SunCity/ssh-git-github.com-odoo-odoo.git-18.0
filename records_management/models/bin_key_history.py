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
    # VIEW SUPPORT FIELDS (introduced to satisfy existing XML references)
    # ----------------------------------------------------------------------------
    # The partner form (mobile_bin_key_wizard_views.xml) expects the following
    # fields inside the <list> of bin_key_history_ids: key_number, status,
    # issue_date, return_date, issue_location, emergency_contact.
    # These did not exist in the original model and triggered a ParseError.
    # To maintain backward compatibility with the existing design intent we
    # expose them here as related / computed mirrors of existing data.
    # ============================================================================
    key_number = fields.Char(
        string='Key Number',
        related='key_id.key_code',
        store=True,
        readonly=True,
        help="Displays the key's code/number for quick reference."
    )
    status = fields.Char(
        string='Status',
        compute='_compute_status',
        store=True,
        help="Derived textual status used purely for legacy view badge decoration."
    )
    issue_date = fields.Date(
        string='Issue Date',
        related='key_id.issue_date',
        store=True,
        readonly=True
    )
    return_date = fields.Date(
        string='Return Date',
        related='key_id.actual_return_date',
        store=True,
        readonly=True
    )
    issue_location = fields.Char(
        string='Issue Location',
        compute='_compute_issue_location',
        store=True,
        help="Location / partner context at the time of the key issue (derived)."
    )
    emergency_contact = fields.Boolean(
        string='Emergency Contact',
        related='partner_id.is_emergency_key_contact',
        store=True,
        readonly=True,
        help="Indicates whether the associated partner is flagged as an emergency key contact."
    )

    @api.depends('event_type')
    def _compute_status(self):
        """Map internal event types to legacy status labels expected by the view.

        XML decorations reference: 'issued', 'returned', 'lost', 'replaced'.
        We translate our event_type domain accordingly; unhandled types fall
        back to the raw event_type for transparency.
        """
        mapping = {
            'assign': 'issued',
            'create': 'issued',
            'return': 'returned',
            'lost': 'lost',
            'retire': 'replaced',
        }
        for record in self:
            record.status = mapping.get(record.event_type, record.event_type or '')

    @api.depends('key_id.partner_id')
    def _compute_issue_location(self):
        for record in self:
            record.issue_location = record.key_id.partner_id.display_name if record.key_id and record.key_id.partner_id else False

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
