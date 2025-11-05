# -*- coding: utf-8 -*-
"""
Bin Access Key Management Module

Manages the lifecycle of physical keys used to access secure shredding bins.
This includes assignment, return, loss tracking, and history logging, ensuring
a secure chain of custody for bin access.

Author: Records Management System
Version: 18.0.0.2.29
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

# Note: Translation warnings during module loading are expected
# for constraint definitions - this is non-blocking behavior


class BinKey(models.Model):
    _name = 'bin.key'
    _description = 'Bin Access Key'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE IDENTIFICATION & WORKFLOW
    # ============================================================================
    name = fields.Char(
        string='Key Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: "New"
    )
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('lost', 'Lost'),
        ('retired', 'Retired')
    ], string='Status', default='available', required=True, tracking=True, copy=False)

    # ============================================================================
    # KEY DETAILS
    # ============================================================================
    key_code = fields.Char(string='Key Code', required=True, copy=False, tracking=True)
    key_type = fields.Selection([
        ('master', 'Master'),
        ('standard', 'Standard'),
        ('temporary', 'Temporary')
    ], string='Key Type', default='standard', required=True)
    description = fields.Text(string='Description')
    physical_key_id = fields.Many2one(
        'bin.key',
        string='Physical Parent Key',
        help="If this is a derivative/duplicate, link to the original physical key",
        tracking=True
    )

    # ============================================================================
    # ASSIGNMENT & VALIDITY
    # ============================================================================
    partner_id = fields.Many2one(comodel_name='res.partner', string='Assigned Customer', tracking=True)
    key_holder_id = fields.Many2one(
        'res.partner',
        string='Current Key Holder',
        help="Person or customer currently responsible for the key",
        tracking=True
    )
    issue_date = fields.Date(string='Issue Date', tracking=True)
    return_date = fields.Date(string='Expected Return Date', tracking=True)
    actual_return_date = fields.Date(string='Actual Return Date', readonly=True)

    # ============================================================================
    # FINANCIALS
    # ============================================================================
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', comodel_name='res.currency')
    replacement_fee = fields.Monetary(string="Replacement Fee", currency_field="currency_id")

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    bin_ids = fields.Many2many(
        'shred.bin',
        'bin_key_shred_bin_rel',
        'key_id', 'bin_id',
        string='Associated Bins'
    )
    history_ids = fields.One2many('bin.key.history', 'key_id', string='Assignment History')
    replacement_of_id = fields.Many2one(comodel_name='bin.key', string='Replacement For', readonly=True)
    replaced_by_id = fields.Many2one(comodel_name='bin.key', string='Replaced By', readonly=True)

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('key_code_company_uniq', 'unique(key_code, company_id)', 'The key code must be unique per company.'),
    ]

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'key_code')
    def _compute_display_name(self):
        """Computes a descriptive name for the key."""
        for key in self:
            key.display_name = f"{key.name} ({key.key_code or ''})"

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_assign_key(self):
        """Opens a wizard to assign the key."""
        self.ensure_one()
        if self.state != 'available':
            raise UserError(_("Only available keys can be assigned."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Assign Key'),
            'res_model': 'bin.key.assignment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_key_id': self.id}
        }

    def action_return_key(self):
        """Marks the key as returned and available."""
        self.ensure_one()
        if self.state != 'assigned':
            raise UserError(_("Only assigned keys can be returned."))
        self.write({
            'state': 'available',
            'partner_id': False,
            'actual_return_date': fields.Date.today()
        })
        self._create_history_entry('return')
        self.message_post(body=_("Key returned and marked as available."))

    def action_mark_lost(self):
        """Marks the key as lost and opens the replacement wizard."""
        self.ensure_one()
        self.state = 'lost'
        self._create_history_entry('lost')
        self.message_post(body=_("Key marked as lost."))
        # Optionally, open a wizard to create a replacement and invoice for the fee
        return {
            'type': 'ir.actions.act_window',
            'name': _('Replace Lost Key'),
            'res_model': 'bin.key.replacement.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lost_key_id': self.id}
        }

    def action_retire_key(self):
        """Retires the key permanently."""
        self.ensure_one()
        self.write({'state': 'retired', 'active': False})
        self._create_history_entry('retire')
        self.message_post(body=_("Key has been retired."))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _create_history_entry(self, event_type, notes=None):
        """Creates a history record for a key event."""
        self.ensure_one()
        self.env['bin.key.history'].create({
            'key_id': self.id,
            'event_type': event_type,
            'partner_id': self.partner_id.id,
            'event_date': fields.Datetime.now(),
            'notes': notes,
        })

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Assign a sequence number on creation and log history."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('bin.key') or _('New')
        keys = super().create(vals_list)
        for key in keys:
            key._create_history_entry('create')
        return keys

    def write(self, vals):
        """Log significant changes to the history."""
        res = super().write(vals)
        if 'state' in vals and vals['state'] == 'assigned':
            for key in self:
                key._create_history_entry('assign')
        return res
