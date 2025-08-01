# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BinKeyHistory(models.Model):
    _name = 'bin.key.history'
    _description = 'Bin Key History'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_created desc'
    _rec_name = 'action_type'

    # Basic Information
    action_type = fields.Selection([
        ('created', 'Key Created'),
        ('assigned', 'Key Assigned'),
        ('revoked', 'Key Revoked'),
        ('renewed', 'Key Renewed'),
        ('suspended', 'Key Suspended'),
        ('reactivated', 'Key Reactivated')
    ], string='Action Type', required=True, tracking=True)

    # Related Partner Bin Key (the inverse field that was missing)
    partner_bin_key_id = fields.Many2one(
        'partner.bin.key', 
        string='Partner Bin Key', 
        required=True, 
        ondelete='cascade',
        tracking=True
    )

    # User who performed the action
    user_id = fields.Many2one(
        'res.users', 
        string='User', 
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )

    # Timestamps
    date_created = fields.Datetime(
        string='Date Created', 
        default=fields.Datetime.now,
        required=True
    )

    # Additional details
    notes = fields.Text(string='Notes')
    old_value = fields.Char(string='Old Value')
    new_value = fields.Char(string='New Value')

    # Company
    company_id = fields.Many2one(
        'res.company', 
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    # Control fields
    active = fields.Boolean(default=True)

    # Computed fields
    display_name = fields.Char(
        string='Display Name', 
        compute='_compute_display_name', 
        store=True
    )

    @api.depends('action_type', 'date_created', 'partner_bin_key_id')
    def _compute_display_name(self):
        """Compute display name for history records."""
        for record in self:
            if record.action_type and record.date_created:
                action_display = dict(record._fields['action_type'].selection).get(record.action_type, '')
                date_str = record.date_created.strftime('%Y-%m-%d %H:%M')
                record.display_name = f"{action_display} - {date_str}"
            else:
                record.display_name = _('New History Entry')
